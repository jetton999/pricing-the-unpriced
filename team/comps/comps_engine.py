"""Comps engine v2: asking-rent ranges for ground-floor space on the Greenmount frontage, and a sales check by use (Idea 1).

Run from anywhere (standard library only):   python3 team/comps/comps_engine.py
Inputs beside this script:  library/rents.csv, library/benchmarks.csv, library/operators.csv,
                            engine_inputs.json (every assumption, with its source), parcel_tax.csv
Output beside this script:  comps_ranges.json, read by team/explorer/build_explorer.py

What it computes (MODEL_CARD.md explains why each method was chosen and what was rejected):
  1. Rent level. Listed rents made triple-net equivalent, logged, pooled by corridor with empirical Bayes
     (each corridor's mean pulled toward its city's mean, more strongly the fewer rows it has), plus a shrunk
     multiplier per use. The 80% range is widened until it covers 80% of listings held out by source.
     This is the one basis for every dollar figure. A use with no listings of its own gets the corridor's
     level with no multiplier, and says so.
  2. Sales check. For a use with a sales benchmark: sales per sq ft in up to three labelled scenarios (low, mid,
     high; 2025 dollars) x the share of sales such a business usually spends on rent - taxes and insurance = the
     rent it could pay. The check says whether the mid scenario covers the mid asking rent. It is a flag, not a
     probability, and it never changes a rent figure.
  3. Checks: held-out coverage, interval score against a naive range, a Baltimore-only check, sensitivity
     reruns, a cross-city comparison with price-level factors, and operators' figures against the scenarios.

Changed from v1 after the sponsor's review of 17 November 2026. v1 gave each use min(asking rent, affordable
rent), treating the two as independent draws. That cut the figure of every use with both kinds of evidence (cafe
by 22%, shop by 19%) and left uses with one kind uncut, so a bike shop, with one national sales figure and no
listings, came out as the highest-rent use on every available parcel. v2 has no such figure, no "chance it can
pay", no weights for combining the two, and nothing that ranks uses by money.
"""
import csv
import json
import math
import os
import re
import statistics as st
import sys
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LIBDIR = os.path.join(HERE, 'library')
ND = NormalDist()


def load_inputs(path=None):
    with open(path or os.path.join(HERE, 'engine_inputs.json'), encoding='utf-8') as fh:
        return json.load(fh)


def read_csv(name):
    with open(os.path.join(LIBDIR, name), encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def r4(x):
    return None if x is None else round(float(x), 4)


def r2(x):
    return None if x is None else round(float(x), 2)


# ---------------------------------------------------------------- inputs
class Inputs:
    def __init__(self, cfg):
        self.cfg = cfg
        self.alpha = cfg['interval']['alpha']
        self.z = ND.inv_cdf(1 - self.alpha / 2)
        self.cpi = {int(k): v for k, v in cfg['cpi']['annual'].items()}
        self.target = cfg['target_dollar_year']
        self.loads = cfg['lease_basis_loads']
        self.rules = cfg['corridors']['rules']
        self.groups = cfg['corridors']['groups']
        self.fam = {f: k for k, fs in cfg['format_families'].items() if k != 'about' for f in fs}

    def cpi_factor(self, year):
        y = int(year)
        if y not in self.cpi:
            raise KeyError(f'CPI for {y} missing from engine_inputs.json')
        return self.cpi[self.target] / self.cpi[y]

    def corridor(self, text):
        t = text.lower()
        for k, v in self.rules:
            if k in t:
                return v
        raise ValueError(f'no corridor rule matches: {text}')


GREEN = re.compile(r'(\d{4})(?:\s*-\s*(\d{4}))?\s+Greenmount', re.I)


def greenmount_numbers(address):
    """'3028-3030 Greenmount Ave' -> {'3028', '3030'}: the parcels a listing describes."""
    m = GREEN.search(address or '')
    if not m:
        return set()
    a = int(m.group(1)); b = int(m.group(2) or a)
    return {str(n) for n in range(a, b + 1, 2)} | {str(a), str(b)}


MIXED = 'mixed'   # a multi-tenant building's average rent: no single use, so it gets no use multiplier


def rent_rows(inp, loads=None, drop=(), override=None):
    loads = loads or inp.loads
    rr = inp.cfg['rent_rows']
    out = []
    for x in read_csv('rents.csv'):
        if override and x['row_id'] in override:
            x = dict(x, **override[x['row_id']])
        f = x['format_id']
        if f in rr['drop_formats'] or not x['asking_rent_usd_per_sqft_yr'] or x['row_id'] in drop:
            continue
        sf = float(x['space_sqft']) if x['space_sqft'] else None
        if sf is not None and sf < rr['min_sqft']:
            continue
        if f == 'workshop' and sf is not None and sf > rr['max_sqft_workshop']:
            continue
        r = float(x['asking_rent_usd_per_sqft_yr'])
        basis = x['rent_basis'] if x['rent_basis'] in loads else 'unknown'
        nnn = r - loads[basis]
        if nnn <= 0:
            continue
        grp = inp.corridor(x['corridor'])
        city = 'baltimore' if 'Baltimore' in x['city_state'] else 'other'
        out.append(dict(id=x['row_id'], fmt=f, grp=grp, city=city, y=math.log(nnn), nnn=nnn, rent=r, basis=x['rent_basis'],
                        sqft=sf, address=x['address'], url=x['source_url'], src=x['source_title'], year=x['figure_year'],
                        cond=x['space_condition'], corridor=x['corridor'], key=(x['source_url'] or x['row_id']).split('#')[0].rstrip('/'),
                        parcels=greenmount_numbers(x['address']), kind=(x.get('rent_kind') or 'asking').strip()))
    return out


# ---------------------------------------------------------------- rent level: corridor-level empirical Bayes
def fit(data):
    """Two steps, both closed form.
    1. Format multipliers: each row's log rent minus its city mean; the mean residual per format is shrunk toward 0
       by tau_f^2 / (tau_f^2 + s^2/n_f) (method of moments). A multi-tenant average ("mixed") gets no multiplier.
    2. Corridor means of the format-adjusted logs, pooled toward a precision-weighted city mean with the
       DerSimonian-Laird between-corridor variance tau^2: pooled = B x city mean + (1 - B) x corridor mean,
       B = v / (v + tau^2), v = s^2 / n."""
    cities = sorted(set(d['city'] for d in data))
    cm = {c: st.mean([d['y'] for d in data if d['city'] == c]) for c in cities}
    fmts = sorted(set(d['fmt'] for d in data if d['fmt'] != MIXED))
    res = {f: [d['y'] - cm[d['city']] for d in data if d['fmt'] == f] for f in fmts}
    s2r = st.pvariance([d['y'] - cm[d['city']] for d in data])
    fm = {f: st.mean(res[f]) for f in fmts}
    nf = {f: len(res[f]) for f in fmts}
    tf2 = max(0.0, st.pvariance(list(fm.values())) - st.mean([s2r / nf[f] for f in fmts])) if len(fmts) > 1 else 0.0
    fshr = {f: (tf2 / (tf2 + s2r / nf[f]) if tf2 > 0 else 0.0) for f in fmts}
    feff = {f: fshr[f] * fm[f] for f in fmts}
    feff[MIXED] = 0.0
    adj = [dict(d, ya=d['y'] - feff[d['fmt']]) for d in data]
    grps = sorted(set(d['grp'] for d in adj))
    g = {k: [d['ya'] for d in adj if d['grp'] == k] for k in grps}
    city_of = {d['grp']: d['city'] for d in adj}
    ss = sum(sum((v - st.mean(g[k])) ** 2 for v in g[k]) for k in grps)
    dof = sum(len(g[k]) - 1 for k in grps)
    s2 = ss / dof
    mean = {k: st.mean(g[k]) for k in grps}
    v = {k: s2 / len(g[k]) for k in grps}
    w = {k: 1 / v[k] for k in grps}
    mu_fe = {c: sum(w[k] * mean[k] for k in grps if city_of[k] == c) / sum(w[k] for k in grps if city_of[k] == c) for c in cities}
    Q = sum(w[k] * (mean[k] - mu_fe[city_of[k]]) ** 2 for k in grps)
    C = sum(sum(w[k] for k in grps if city_of[k] == c) - sum(w[k] ** 2 for k in grps if city_of[k] == c) / sum(w[k] for k in grps if city_of[k] == c) for c in cities)
    tau2 = max(0.0, (Q - (len(grps) - len(cities))) / C) if C > 0 else 0.0
    ws = {k: 1 / (v[k] + tau2) for k in grps}
    sws = {c: sum(ws[k] for k in grps if city_of[k] == c) for c in cities}
    mu = {c: sum(ws[k] * mean[k] for k in grps if city_of[k] == c) / sws[c] for c in cities}
    muvar = {c: 1 / sws[c] for c in cities}
    B = {k: v[k] / (v[k] + tau2) for k in grps}
    post = {k: B[k] * mu[city_of[k]] + (1 - B[k]) * mean[k] for k in grps}
    postvar = {k: (1 - B[k]) * v[k] + B[k] ** 2 * muvar[city_of[k]] for k in grps}
    return dict(feff=feff, fshr=fshr, fraw=fm, nf=nf, tf2=tf2, s2=s2, tau2=tau2, mu=mu, muvar=muvar, B=B, post=post,
                postvar=postvar, n={k: len(g[k]) for k in grps}, raw=mean, city_of=city_of, ws=ws, sws=sws, cm=cm)


BORROW_A = {'tavern': 'cafe'}


def level(m, grp, city='baltimore'):
    """(log location, variance of that location) of a corridor's rent level, before any use multiplier."""
    if grp in m['post']:
        return m['post'][grp], m['postvar'][grp]
    return m['mu'][city], m['muvar'][city] + m['tau2']


def predict(m, grp, fmt, city='baltimore'):
    """(log location, sd) of a new listing of format fmt in corridor grp; None if the format has no listings."""
    f = BORROW_A.get(fmt, fmt)
    if f not in m['feff']:
        return None
    loc, pv = level(m, grp, city)
    return loc + m['feff'][f], math.sqrt(m['s2'] + pv)


def asking(m, grp, fmt, city='baltimore'):
    """The rent level for a use: (log location, sd, basis). With the use's multiplier where it has listings (or
    borrows another use's); the corridor's level with no multiplier where it has none."""
    pr = predict(m, grp, fmt, city)
    if pr is not None:
        return pr[0], pr[1], ('borrowed from ' + BORROW_A[fmt]) if fmt in BORROW_A else 'own listings'
    loc, pv = level(m, grp, city)
    return loc, math.sqrt(m['s2'] + pv), 'corridor level'


def row_weights(m, data, grp='waverly'):
    """How much each listing contributes to the pooled corridor mean (format effects held fixed)."""
    city = m['city_of'][grp]
    Bk = m['B'][grp]
    out = {}
    for d in data:
        k = d['grp']
        wk = 0.0
        if k == grp:
            wk += (1 - Bk) / m['n'][k]
        if m['city_of'].get(k) == city:
            wk += Bk * (m['ws'][k] / m['sws'][city]) / m['n'][k]
        if wk > 0:
            out[d['id']] = wk
    return out


# ---------------------------------------------------------------- held-out checks
def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def clopper_pearson(k, n, a=0.05):
    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if f(mid):
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) < a / 2)
    upper = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) > a / 2)
    return lower, upper


def interval_score(lo, hi, y, a):
    return (hi - lo) + (2 / a) * max(0.0, lo - y) + (2 / a) * max(0.0, y - hi)


def holdout(data, inp):
    """Leave out one source at a time (two listings from the same page leave together), refit, predict."""
    z, a = inp.z, inp.alpha
    keys = sorted(set(d['key'] for d in data))
    recs = []
    for key in keys:
        train = [d for d in data if d['key'] != key]
        mi = fit(train)
        tr = sorted(d['nnn'] for d in train)
        nlo, nhi = q_emp(tr, a / 2), q_emp(tr, 1 - a / 2)
        ws_pred = predict(mi, 'waverly', 'shop')
        for d in data:
            if d['key'] != key:
                continue
            pr = predict(mi, d['grp'], d['fmt'], d['city'])
            if pr is None:
                continue
            loc, sd = pr
            recs.append(dict(id=d['id'], city=d['city'], y=d['y'], loc=loc, sd=sd, zs=(d['y'] - loc) / sd,
                             naive=(nlo, nhi), wshop=ws_pred[0]))
    n = len(recs)
    absz = sorted(abs(r['zs']) for r in recs)
    k = math.ceil((1 - a) * (n + 1))
    c = max(1.0, absz[min(k, n) - 1] / z)
    hits = sum(abs(r['zs']) <= z for r in recs)
    below = sum(r['zs'] < -z for r in recs)
    above = sum(r['zs'] > z for r in recs)
    # honest coverage of the widened range: the widening factor is recomputed without the held-out row
    honest = 0
    for i, r in enumerate(recs):
        others = sorted(abs(x['zs']) for j, x in enumerate(recs) if j != i)
        ki = math.ceil((1 - a) * n)
        ci = max(1.0, others[min(ki, n - 1) - 1] / z)
        honest += abs(r['zs']) <= ci * z
    bal = [r for r in recs if r['city'] == 'baltimore']
    bal_hits_w = sum(abs(r['zs']) <= c * z for r in bal)
    bal_hits_n = sum(abs(r['zs']) <= z for r in bal)
    is_model = st.mean(interval_score(math.exp(r['loc'] - c * z * r['sd']), math.exp(r['loc'] + c * z * r['sd']), math.exp(r['y']), a) for r in recs)
    is_naive = st.mean(interval_score(r['naive'][0], r['naive'][1], math.exp(r['y']), a) for r in recs)
    # jackknife+ range for a Waverly shop (Barber et al.): held-out residual around each held-out fit's prediction
    lo_l = sorted(r['wshop'] - abs(r['y'] - r['loc']) for r in recs)
    hi_l = sorted(r['wshop'] + abs(r['y'] - r['loc']) for r in recs)
    kj = math.ceil((1 - a) * (n + 1))
    jk = (math.exp(lo_l[n - kj]), math.exp(hi_l[kj - 1])) if kj <= n else (None, None)
    cp = clopper_pearson(hits, n)
    return dict(n=n, sources=len(keys), ids=sorted(r['id'] for r in recs), nominal_hits=hits, nominal_cover=hits / n, nominal_ci95=cp, below=below, above=above,
                widen=c, honest_hits=honest, honest_cover=honest / n, honest_ci95=clopper_pearson(honest, n),
                baltimore_n=len(bal), baltimore_nominal=bal_hits_n, baltimore_widened=bal_hits_w,
                interval_score_model=is_model, interval_score_naive=is_naive, skill=1 - is_model / is_naive,
                jackknife_plus_waverly_shop=jk)


def fit_against_corridor_levels(data, iters=200):
    """An estimator that was tried and not kept: each use's multiplier is estimated on what is left of a listing
    after its corridor's level (not after its city's mean), alternating with the corridor levels until both settle."""
    fmts = sorted(set(d['fmt'] for d in data if d['fmt'] != MIXED))
    feff = dict({f: 0.0 for f in fmts}, **{MIXED: 0.0})
    for _ in range(iters):
        m = fit([dict(d, y=d['y'] - feff[d['fmt']], fmt=MIXED) for d in data])
        res = {f: [d['y'] - feff[MIXED] - m['post'][d['grp']] for d in data if d['fmt'] == f] for f in fmts}
        nf = {f: len(res[f]) for f in fmts}
        centre = sum(sum(res[f]) for f in fmts) / sum(nf.values())       # a corridor's level is that of its average listing
        fm = {f: st.mean(res[f]) - centre for f in fmts}
        tf2 = max(0.0, st.pvariance(list(fm.values())) - st.mean([m['s2'] / nf[f] for f in fmts])) if len(fmts) > 1 else 0.0
        new = dict({f: (tf2 / (tf2 + m['s2'] / nf[f]) if tf2 > 0 else 0.0) * fm[f] for f in fmts}, **{MIXED: 0.0})
        step = max(abs(new[f] - feff[f]) for f in fmts)
        feff = new
        if step < 1e-9:
            break
    return dict(m, feff=feff)


def fit_with_a_minimum_of_listings(n_min):
    """An estimator that was tried and not kept: a use gets its own multiplier only from n_min listings up."""
    def fitter(data):
        thin = {f for f, n in fit(data)['nf'].items() if n < n_min}
        return fit([dict(d, fmt=MIXED) if d['fmt'] in thin else d for d in data])
    return fitter


def fit_without_shrinking(data):
    """An estimator that was tried and not kept: each use's multiplier is its raw average gap from its city's mean."""
    raw = dict(fit(data)['fraw'], **{MIXED: 0.0})
    return dict(fit([dict(d, y=d['y'] - raw[d['fmt']], fmt=MIXED) for d in data]), feff=raw)


def alternatives(data, inp, ids):
    """Each estimator predicts every listing from a model fitted without that listing's source, on the same listings
    (ids: the ones the engine's own held-out check predicts). A use with no multiplier in the fit gets the corridor's
    level alone, as on the page. Reported: the error of the middle figure in logs, the widening its 80% range needs,
    and the interval score of the widened range (lower is better)."""
    z, a = inp.z, inp.alpha
    keys = sorted(set(d['key'] for d in data))
    out = []
    for name, fitter in (('as built', fit),
                         ("each use's multiplier estimated against its corridor's level", fit_against_corridor_levels),
                         ('multipliers not shrunk (raw averages)', fit_without_shrinking),
                         ('a multiplier only from two listings up', fit_with_a_minimum_of_listings(2)),
                         ('a multiplier only from three listings up', fit_with_a_minimum_of_listings(3)),
                         ('no multipliers by use', fit_with_a_minimum_of_listings(10 ** 6))):
        recs = []
        for key in keys:
            mi = fitter([d for d in data if d['key'] != key])
            for d in data:
                if d['key'] == key and d['id'] in ids:
                    loc, pv = level(mi, d['grp'], d['city'])
                    recs.append((d['y'], loc + mi['feff'].get(BORROW_A.get(d['fmt'], d['fmt']), 0.0), math.sqrt(mi['s2'] + pv)))
        n = len(recs)
        absz = sorted(abs(y - loc) / sd for y, loc, sd in recs)
        c = max(1.0, absz[min(math.ceil((1 - a) * (n + 1)), n) - 1] / z)
        out.append(dict(estimator=name, rows=n, log_rmse=math.sqrt(st.mean((y - loc) ** 2 for y, loc, sd in recs)),
                        inside_plain_range=sum(abs(y - loc) <= z * sd for y, loc, sd in recs), widen=c,
                        interval_score=st.mean(interval_score(math.exp(loc - c * z * sd), math.exp(loc + c * z * sd), math.exp(y), a)
                                               for y, loc, sd in recs)))
    return out


def q_emp(xs, p):
    xs = sorted(xs)
    h = (len(xs) - 1) * p
    i = int(math.floor(h))
    return xs[i] if i + 1 >= len(xs) else xs[i] + (h - i) * (xs[i + 1] - xs[i])


# ---------------------------------------------------------------- ranges and the sales check (the explorer re-implements these in JS)
def cdf_ln(x, loc, s):
    return 0.0 if x <= 0 else ND.cdf((math.log(x) - loc) / s)


def q_ln(p, loc, s):
    return math.exp(loc + s * ND.inv_cdf(p))


SCEN = ('low', 'mid', 'high')


def afford(sales, share, eti):
    """Rent per sq ft a business could pay from its sales: sales x the share usually spent on rent - taxes and insurance."""
    return max(0.0, share * sales - eti)


def sales_check(asking_mid, afford_mid, margin):
    """A flag, not a probability: does the mid sales scenario cover the mid asking rent? Inside the margin it is
    too close to call."""
    if afford_mid >= (1 + margin) * asking_mid:
        return 'covers'
    if afford_mid <= (1 - margin) * asking_mid:
        return 'does not cover'
    return 'too close to call'


def sales_scenarios(inp):
    """Sales per sq ft by use, in 2025 dollars: three labelled scenarios where the benchmarks give three points,
    one (mid) where they give a single figure. No distribution is fitted to them."""
    cfg = inp.cfg['sales_check']['uses']
    loc = inp.cfg['local_demand']

    def local(f):
        return loc['food']['factor'] if f in loc['food']['applies_to'] else loc['other']['factor']

    out = {}
    for f, spec in cfg.items():
        if 'borrow' in spec:
            continue
        if spec.get('applies') is False:
            out[f] = dict(applies=False, why=spec['why'])
            continue
        lf = local(f)
        s = spec['sales']
        pts = {'mid': s['single']} if 'single' in s else {k: s[k] for k in SCEN}
        sales, trail = {}, []
        for key, pt in pts.items():
            k = inp.cpi_factor(pt['year'])
            sales[key] = pt['v'] * k * lf
            trail.append(dict(point=key, v=pt['v'], year=pt['year'], cpi=k, local=lf, out=sales[key], rows=pt['rows'], how=pt['how'],
                              assumed_sqft=pt.get('assumed_sqft')))
        sh = spec['share']
        out[f] = dict(applies=True, sales=sales, share=sh['mid'], share_low=sh.get('low'), share_high=sh.get('high'),
                      share_rows=sh['rows'], share_how=sh['how'], single='single' in s, trail=trail, local=lf)
    for f, spec in cfg.items():
        if isinstance(spec, dict) and 'borrow' in spec:
            out[f] = dict(out[spec['borrow']], borrowed_from=spec['borrow'], borrow_why=spec['why'])
    return out


# ---------------------------------------------------------------- parcels: taxes a tenant pays on top of NNN rent
def parcel_tax(inp):
    with open(os.path.join(HERE, 'parcel_tax.csv'), encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    per = {}
    for r in rows:
        a = float(r['struct_area_sqft'] or 0)
        if a > 0 and r['city_tax_usd']:
            per[r['address']] = dict(tax=float(r['city_tax_usd']) / a, use=r['usegroup'])
    med = st.median(v['tax'] for v in per.values() if v['use'] == 'C')
    other = inp.cfg['pass_through']['other_per_sqft']
    return per, med, other


# ---------------------------------------------------------------- build
FMTS = ['cafe', 'counter', 'foodmaker', 'tavern', 'shop', 'showroom', 'bike', 'services', 'fitness', 'studio', 'venue', 'office',
        'workshop', 'community']


def build(cfg=None):
    inp = Inputs(cfg or load_inputs())
    rows = rent_rows(inp)
    m = fit(rows)
    ho = holdout(rows, inp)
    tried = alternatives(rows, inp, set(ho.pop('ids')))
    # the comparison is on the engine's own held-out listings, so its first row must repeat the held-out check
    assert (tried[0]['rows'], tried[0]['inside_plain_range']) == (ho['n'], ho['nominal_hits']) and abs(tried[0]['widen'] - ho['widen']) < 1e-9 \
        and abs(tried[0]['interval_score'] - ho['interval_score_model']) < 1e-9, 'the comparison of estimators does not repeat the held-out check'
    c = ho['widen']
    z = inp.z
    S = sales_scenarios(inp)
    margin = inp.cfg['sales_check']['margin']
    per, med, other = parcel_tax(inp)
    eti_med = med + other
    fmts = FMTS

    def qs(loc, sd):
        return [r2(q_ln(p, loc, sd)) for p in (inp.alpha / 2, 0.5, 1 - inp.alpha / 2)]

    def ask_at(model, grp='waverly'):
        """Every use's rent level in a corridor, with the widened spread: {use: (log location, sd, basis)}."""
        return {f: (a[0], a[1] * c, a[2]) for f, a in ((f, asking(model, grp, f)) for f in fmts)}

    def space_at(model, grp='waverly'):
        """The corridor's rent level for a space, whatever goes in it: no use multiplier."""
        loc, pv = level(model, grp)
        return loc, math.sqrt(model['s2'] + pv) * c

    A_w = ask_at(m)
    space = space_at(m)
    nrows = {f: sum(1 for d in rows if d['fmt'] == BORROW_A.get(f, f)) for f in fmts}

    formats = {}
    for f in fmts:
        loc, sd, basis = A_w[f]
        Sp = S.get(f) or {}
        bf = BORROW_A.get(f, f)
        rec = dict(n_listings=nrows[f],
                   asking=dict(loc=r4(loc), sd=r4(sd), q=qs(loc, sd), basis=basis),
                   borrowed_from=BORROW_A.get(f) or Sp.get('borrowed_from'),
                   multiplier=None if bf not in m['fraw'] else dict(raw=r4(math.exp(m['fraw'][bf])), shrunk=r4(math.exp(m['feff'][bf])),
                                                                    keep=r4(m['fshr'][bf])))
        flags = []
        if basis == 'corridor level':
            flags.append("no listings for this use: the corridor's rent level is shown, with no multiplier for the use")
        elif nrows[f] < 3:
            flags.append(f'only {nrows[f]} listing{"s" if nrows[f] != 1 else ""}: thin evidence; {m["fshr"][bf]:.0%} of '
                         f"its gap from the city's mean is kept")
        if rec['borrowed_from']:
            flags.append(f'borrowed from {rec["borrowed_from"]}')
        if Sp.get('applies'):
            aff = {k: afford(v, Sp['share'], eti_med) for k, v in Sp['sales'].items()}
            rec['sales'] = dict(scenarios={k: r2(v) for k, v in Sp['sales'].items()}, afford={k: r2(v) for k, v in aff.items()},
                                share=Sp['share'], share_low=Sp.get('share_low'), share_high=Sp.get('share_high'),
                                share_rows=Sp['share_rows'], share_how=Sp['share_how'], single=Sp['single'], local=Sp['local'],
                                trail=[{k: v for k, v in dict(t, cpi=r4(t['cpi']), out=r2(t['out'])).items() if v is not None} for t in Sp['trail']])
            rec['sales_na'] = None
            rec['check'] = dict(verdict=sales_check(math.exp(loc), aff['mid'], margin), asking_mid=r2(math.exp(loc)),
                                afford_mid=r2(aff['mid']), margin=margin)
            mid_pt = next(t for t in Sp['trail'] if t['point'] == 'mid')
            if mid_pt.get('assumed_sqft'):
                # the mid figure is receipts per business divided by a floor area the team assumed: say how far the
                # verdict depends on it. receipts x share / area - taxes and insurance, set against the two margins
                receipts = mid_pt['v'] * mid_pt['assumed_sqft'] * mid_pt['cpi'] * mid_pt['local']
                covers_to = Sp['share'] * receipts / ((1 + margin) * math.exp(loc) + eti_med)
                fails_from = Sp['share'] * receipts / ((1 - margin) * math.exp(loc) + eti_med)
                rec['check'].update(assumed_sqft=mid_pt['assumed_sqft'], covers_up_to_sqft=int(round(covers_to, -1)),
                                    does_not_cover_from_sqft=int(round(fails_from, -1)))
                flags.append(f"the mid sales figure is receipts per business divided by an assumed {mid_pt['assumed_sqft']:,} sq ft: "
                             f"the check reads 'covers' up to about {round(covers_to, -1):,.0f} sq ft and 'does not cover' from "
                             f"about {round(fails_from, -1):,.0f}")
            impl = (math.exp(loc) + eti_med) / Sp['share']
            rec['implied_sales'] = r2(impl)
            if Sp['single']:
                flags.append('one sales figure: a mid scenario only')
            elif not (Sp['sales']['low'] <= impl <= Sp['sales']['high']):
                flags.append(f'the mid asking rent implies ${impl:,.0f}/sq ft of sales, outside the low-to-high scenarios')
        else:
            rec['sales'] = None
            rec['sales_na'] = Sp.get('why')
            rec['check'] = None
        rec['flags'] = flags
        formats[f] = rec
    for f, why in inp.cfg['not_estimated'].items():
        formats[f] = dict(not_estimated=why)

    # parcels: pass-through costs, and the rent level with a building's own rows left out
    parcels = {}
    for a, v in per.items():
        parcels[a] = dict(tax=r4(v['tax']), eti=r4(v['tax'] + other))
    own = {}
    for d in rows:
        for a in d['parcels']:
            own.setdefault(a, set()).add(d['id'])
    byid = {d['id']: d for d in rows}
    for a, ids in sorted(own.items()):
        mi = fit([d for d in rows if d['id'] not in ids])
        Ai = ask_at(mi)
        parcels.setdefault(a, dict(tax=None, eti=r4(eti_med)))
        parcels[a]['own_listings'] = sorted(ids)
        parcels[a]['own_rows'] = [dict(id=i, rent=byid[i]['rent'], basis=byid[i]['basis'], nnn=r2(byid[i]['nnn']), kind=byid[i]['kind'],
                                       sqft=byid[i]['sqft'], address=byid[i]['address']) for i in sorted(ids)]
        parcels[a]['A'] = {f: [r4(v[0]), r4(v[1])] for f, v in Ai.items()}
        parcels[a]['space'] = [r4(x) for x in space_at(mi)]

    # worked examples for the JS consistency check
    examples = []
    for a in ['2932', '3010', '3026', '3117', '3211', '3226']:
        pa = parcels.get(a, {})
        eti = pa.get('eti') or eti_med
        sp = pa.get('space') or [r4(space[0]), r4(space[1])]
        examples.append(dict(address=a, fmt='', asking=qs(*sp)))
        for f in ('cafe', 'shop', 'fitness', 'bike', 'venue'):
            Ao = pa.get('A', {}).get(f) or [r4(A_w[f][0]), r4(A_w[f][1])]
            Sp = S.get(f) or {}
            examples.append(dict(address=a, fmt=f, asking=qs(*Ao),
                                 afford={k: r2(afford(v, Sp['share'], eti)) for k, v in Sp['sales'].items()} if Sp.get('applies') else None))

    # the trail behind the Waverly mean
    wts = row_weights(m, rows)
    used = {d['id']: d for d in rows}
    trail = sorted(({'id': i, 'w': r4(w), 'nnn': r2(used[i]['nnn']), 'fmt': used[i]['fmt'], 'grp': used[i]['grp'], 'kind': used[i]['kind']}
                    for i, w in wts.items()), key=lambda x: -x['w'])

    # nearest listings per format (for showing, not for the range)
    nearest = {}
    for f in fmts:
        tf = BORROW_A.get(f, f)
        size = {'cafe': 1800, 'counter': 600, 'foodmaker': 2400, 'tavern': 2000, 'shop': 1000, 'showroom': 5500, 'bike': 1800, 'services': 900,
                'fitness': 3000, 'studio': 1800, 'venue': 5500, 'office': 1700, 'workshop': 1700, 'community': 3200}[f]
        def dist_k(d):
            return (1.0 * (d['grp'] != 'waverly') + 0.5 * (d['city'] != 'baltimore') + 0.5 * (inp.fam.get(d['fmt']) != inp.fam.get(tf))
                    + (abs(math.log((d['sqft'] or size) / size)) if d['sqft'] else 0.5))
        top = sorted(rows, key=lambda d: (dist_k(d), d['id']))[:6]
        nearest[f] = [dict(id=d['id'], d=r2(dist_k(d)), address=d['address'], corridor=d['corridor'], fmt=d['fmt'], rent=d['rent'], basis=d['basis'],
                           nnn=r2(d['nnn']), sqft=d['sqft'], year=d['year'], url=d['url'], kind=d['kind']) for d in top]

    # corridors side by side, with price-level factors
    rpp = inp.cfg['transfer']['rpp_2024']
    corridors = []
    for k in sorted(m['n'], key=lambda k: (m['city_of'][k] != 'baltimore', -m['n'][k], k)):
        gmeta = inp.groups[k]
        rk = rpp[gmeta['metro']]['v']
        ratio = rpp['baltimore']['v'] / rk
        corridors.append(dict(id=k, name=gmeta['name'], city=gmeta['city'], district_id=gmeta.get('district_id'), n=m['n'][k],
                              formats=sorted(set(d['fmt'] for d in rows if d['grp'] == k)),
                              raw=r2(math.exp(m['raw'][k])), pooled=r2(math.exp(m['post'][k])), B=r4(m['B'][k]),
                              rpp=rk, rpp_url=rpp[gmeta['metro']]['url'], ratio=r4(ratio), at_baltimore_prices=r2(math.exp(m['post'][k]) * ratio),
                              rows=[d['id'] for d in rows if d['grp'] == k]))
    # does the price-level factor help? predict each other-city corridor from Baltimore's mean, with and without it
    errs_with, errs_without = [], []
    for cr in corridors:
        if cr['city'] == 'Baltimore':
            continue
        target = m['raw'][cr['id']]
        base = m['mu']['baltimore']
        errs_without.append(abs(target - base))
        errs_with.append(abs(target - (base + math.log(cr['rpp'] / rpp['baltimore']['v']))))
    transfer_test = dict(n=len(errs_with), median_err_without=r4(st.median(errs_without)), median_err_with=r4(st.median(errs_with)),
                         helps=st.median(errs_with) < st.median(errs_without))

    # operators' figures against the sales scenarios
    ops = []
    om = inp.cfg['transfer']['operator_metro']
    for o in read_csv('operators.csv'):
        if not o['revenue_per_sqft_usd'] or o['figure_type'] == 'asking':
            continue
        yr = re.match(r'(?:c\.)?(\d{4})', o['revenue_year'] or '')
        if not yr:
            continue
        y = int(yr.group(1))
        metro = om.get(o['city_state'][:14].strip().rstrip(',')) or next((v for kk, v in om.items() if o['city_state'].startswith(kk)), None)
        k = inp.cpi_factor(y)
        ratio = rpp['baltimore']['v'] / rpp[metro]['v'] if metro else 1.0
        v = float(o['revenue_per_sqft_usd']) * k * ratio
        f = o['format_id']
        Sf = S.get(f) or {}
        inside = None
        rng = None
        if Sf.get('applies') and not Sf['single']:
            lo, hi = Sf['sales']['low'], Sf['sales']['high']
            inside = lo <= v <= hi
            rng = [r2(lo), r2(hi)]
        ops.append(dict(id=o['row_id'], name=o['name'], city=o['city_state'], fmt=f, model=o['operator_model'], v=float(o['revenue_per_sqft_usd']),
                        year=y, cpi=r4(k), ratio=r4(ratio), out=r2(v), lower_bound='LOWER BOUND' in (o['notes'] or ''),
                        range=rng, inside=inside, url=o['source_url']))

    # Census receipts per establishment in Baltimore (reference lines, chains included)
    census = {}
    for b in read_csv('benchmarks.csv'):
        if b['metric'] == 'revenue_per_establishment_yr' and b['geography'].startswith('Baltimore City'):
            census.setdefault(b['format_id'], []).append(dict(id=b['row_id'], v=float(b['value_mid']), naics=b['naics'], year=b['figure_year'],
                                                               what=b['evidence_quote'].split(';')[0].replace('NAICS2022=', ''), url=b['source_url']))

    # sensitivity reruns: what moves Waverly's rent level, and what moves the sales check
    sens = []

    def waverly_mid(rows_, model=None):
        return math.exp(level(model or fit(rows_), 'waverly')[0])

    sens.append(dict(what='Allowance taken off a listed rent that includes some / all of the building costs', setting='$2 / $4 (default)', result=f'Waverly rent level ${waverly_mid(rows, m):.2f}'))
    for alt in inp.loads['sensitivity']:
        lo2 = dict(inp.loads); lo2.update(alt)
        sens.append(dict(what='Allowance taken off a listed rent that includes some / all of the building costs', setting=f'${alt["modified gross"]:.0f} / ${alt["gross"]:.0f}',
                         result=f'Waverly rent level ${waverly_mid(rent_rows(inp, loads=lo2)):.2f}'))
    inplace = sorted(d['id'] for d in rows if d['kind'] == 'in place')
    sens.append(dict(what='Rents in place (' + ', '.join(inplace) + ')', setting='left out: asking rents only',
                     result=f'Waverly rent level ${waverly_mid(rent_rows(inp, drop=set(inplace))):.2f}'))
    for alt in inp.cfg['rent_rows'].get('rereads', []):
        sens.append(dict(what=alt['what'], setting=alt['setting'],
                         result=f'Waverly rent level ${waverly_mid(rent_rows(inp, override={alt["row_id"]: alt["values"]})):.2f}'))
        sens.append(dict(what=alt['what'], setting='row left out',
                         result=f'Waverly rent level ${waverly_mid(rent_rows(inp, drop={alt["row_id"]})):.2f}'))
    for f in ('cafe', 'shop', 'services', 'fitness'):
        Sp = S[f]
        for lab in ('share_low', 'share_high'):
            if Sp.get(lab):
                a = afford(Sp['sales']['mid'], Sp[lab], eti_med)
                sens.append(dict(what=f'Share of sales spent on rent ({f})', setting=f'{Sp[lab]:.1%}',
                                 result=f'could pay ${a:.2f} in the mid scenario; the check: {sales_check(math.exp(A_w[f][0]), a, margin)}'))
    for mg in inp.cfg['sales_check'].get('margin_sensitivity', []):
        ch = [f for f in fmts if formats[f].get('check') and
              sales_check(formats[f]['check']['asking_mid'], formats[f]['check']['afford_mid'], mg) != formats[f]['check']['verdict']]
        sens.append(dict(what='Margin of the sales check', setting=f'{mg:.0%} (default {margin:.0%})',
                         result=('changes the verdict for ' + ', '.join(ch)) if ch else 'no verdict changes'))

    out = dict(
        version='comps engine v2',
        built_from=dict(rents=len(read_csv('rents.csv')), rows_used=len(rows), asking=sum(1 for d in rows if d['kind'] == 'asking'),
                        in_place=len(inplace), in_place_rows=inplace, sources=ho['sources'], corridors=len(m['n']),
                        benchmarks=len(read_csv('benchmarks.csv')), operators=len(read_csv('operators.csv'))),
        interval=dict(alpha=inp.alpha, z=r4(z), widen=r4(c)),
        dollars=inp.target,
        model=dict(within_sd=r4(math.sqrt(m['s2'])), between_corridor_sd=r4(math.sqrt(m['tau2'])), between_format_sd=r4(math.sqrt(m['tf2'])),
                   city_means={k: r2(math.exp(v)) for k, v in m['mu'].items()},
                   waverly=dict(n=m['n']['waverly'], raw=r2(math.exp(m['raw']['waverly'])), pooled=r2(math.exp(m['post']['waverly'])),
                                B=r4(m['B']['waverly']), own_share=r4(1 - m['B']['waverly']),
                                asking=sum(1 for d in rows if d['grp'] == 'waverly' and d['kind'] == 'asking'),
                                in_place=sum(1 for d in rows if d['grp'] == 'waverly' and d['kind'] == 'in place')),
                   space=dict(loc=r4(space[0]), sd=r4(space[1]), q=qs(*space)),
                   waverly_trail=trail, eti_median=r4(eti_med), tax_median=r4(med), pass_through_other=other),
        formats=formats,
        parcels=parcels,
        examples=examples,
        nearest=nearest,
        corridors=corridors,
        transfer_test=transfer_test,
        operators=ops,
        census=census,
        holdout=dict({k: (r4(v) if isinstance(v, float) else v) for k, v in ho.items() if k not in ('nominal_ci95', 'honest_ci95', 'jackknife_plus_waverly_shop')},
                     nominal_ci95=[r4(x) for x in ho['nominal_ci95']], honest_ci95=[r4(x) for x in ho['honest_ci95']],
                     jackknife_plus_waverly_shop=[r2(x) for x in ho['jackknife_plus_waverly_shop']],
                     # estimators that were tried on the same held-out listings; the first row is the engine as built
                     alternatives=[dict({k: (r4(v) if isinstance(v, float) else v) for k, v in x.items()}) for x in tried]),
        sensitivity=sens,
        sales_check=dict(margin=margin, about=inp.cfg['sales_check']['about']),
        local_demand=inp.cfg['local_demand'],
        sources=sources_index(),
    )
    return out


def sources_index():
    """Every library row a range can cite, so the page can link a row id to its source."""
    idx = {}
    for name in ('rents.csv', 'benchmarks.csv', 'operators.csv'):
        for x in read_csv(name):
            idx[x['row_id']] = dict(t=x['source_title'][:140], u=x['source_url'], y=x['figure_year'] if 'figure_year' in x else x.get('revenue_year', ''),
                                    q=(x.get('evidence_quote') or '')[:160])
    return idx


def main():
    out = build()
    dst = os.path.join(HERE, 'comps_ranges.json')
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    h = out['holdout']
    print(f"wrote {os.path.relpath(dst, REPO)}: {out['built_from']['rows_used']} listings in {out['built_from']['corridors']} corridors; "
          f"held-out coverage {h['nominal_hits']}/{h['n']} at the nominal 80%, widened x{out['interval']['widen']:.2f}")


if __name__ == '__main__':
    sys.exit(main())
