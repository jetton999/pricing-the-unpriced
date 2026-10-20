"""Comps engine v1: rent and revenue ranges for each ground-floor use on the Greenmount frontage (Idea 1).

Run from anywhere (standard library only):   python3 team/comps/comps_engine.py
Inputs beside this script:  library/rents.csv, library/benchmarks.csv, library/operators.csv,
                            engine_inputs.json (every assumption, with its source), parcel_tax.csv
Output beside this script:  comps_ranges.json, read by team/explorer/build_explorer.py

What it computes (MODEL_CARD.md explains why each method was chosen and what was rejected):
  1. Listing route. Asking rents made triple-net equivalent, logged, pooled by corridor with empirical Bayes
     (each corridor's mean pulled toward its city's mean, more strongly the fewer rows it has), plus a shrunk
     multiplier per format. The 80% range is widened until it covers 80% of listings held out by source.
  2. Affordability route. Sales per sq ft (benchmark rows, in 2025 dollars) x the share of sales the format
     usually spends on rent - the parcel's taxes and insurance.
  3. Typical rent = a mixture of the two routes, weighted n/(n+3) toward the listings.
     Revenue = sales per sq ft x usable floor area.
     Supportable rent (what the explorer ranks with) = the lower of the listing rent and what the use can afford.
  4. Checks: held-out coverage, interval score against a naive range, a Baltimore-only check, sensitivity
     reruns, a cross-city comparison with price-level factors, and operators' figures against the ranges.

Private step (optional; its input and output never go into the repo):
  PTU_PRIVATE_OPERATOR=/secure/path/operator.json python3 team/comps/comps_engine.py
  operator.json: {"format_id": "cafe", "sales_per_sqft": ..., "year": ...}  or "annual_sales" and "sqft"
  Writes private_annex.json beside that file (or in PTU_PRIVATE_OUT). The public comps_ranges.json is
  byte-identical with or without it; test_comps_engine.py checks that.
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


def rent_rows(inp, loads=None, drop=()):
    loads = loads or inp.loads
    rr = inp.cfg['rent_rows']
    out = []
    for x in read_csv('rents.csv'):
        assert '2731 greenmount' not in (x['address'] or '').lower(), 'NDA parcel must never enter the library'
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
                        parcels=greenmount_numbers(x['address'])))
    return out


# ---------------------------------------------------------------- listing route: corridor-level empirical Bayes
def fit(data):
    """Two steps, both closed form.
    1. Format multipliers: each row's log rent minus its city mean; the mean residual per format is shrunk toward 0
       by tau_f^2 / (tau_f^2 + s^2/n_f) (method of moments).
    2. Corridor means of the format-adjusted logs, pooled toward a precision-weighted city mean with the
       DerSimonian-Laird between-corridor variance tau^2: pooled = B x city mean + (1 - B) x corridor mean,
       B = v / (v + tau^2), v = s^2 / n."""
    cities = sorted(set(d['city'] for d in data))
    cm = {c: st.mean([d['y'] for d in data if d['city'] == c]) for c in cities}
    fmts = sorted(set(d['fmt'] for d in data))
    res = {f: [d['y'] - cm[d['city']] for d in data if d['fmt'] == f] for f in fmts}
    s2r = st.pvariance([d['y'] - cm[d['city']] for d in data])
    fm = {f: st.mean(res[f]) for f in fmts}
    nf = {f: len(res[f]) for f in fmts}
    tf2 = max(0.0, st.pvariance(list(fm.values())) - st.mean([s2r / nf[f] for f in fmts])) if len(fmts) > 1 else 0.0
    fshr = {f: (tf2 / (tf2 + s2r / nf[f]) if tf2 > 0 else 0.0) for f in fmts}
    feff = {f: fshr[f] * fm[f] for f in fmts}
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


def predict(m, grp, fmt, city='baltimore'):
    """(log location, sd) of a new listing of format fmt in corridor grp; None if the format has no listings."""
    f = BORROW_A.get(fmt, fmt)
    if f not in m['feff']:
        return None
    if grp in m['post']:
        loc, pv = m['post'][grp], m['postvar'][grp]
    else:
        loc, pv = m['mu'][city], m['muvar'][city] + m['tau2']
    return loc + m['feff'][f], math.sqrt(m['s2'] + pv)


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
    return dict(n=n, sources=len(keys), nominal_hits=hits, nominal_cover=hits / n, nominal_ci95=cp, below=below, above=above,
                widen=c, honest_hits=honest, honest_cover=honest / n, honest_ci95=clopper_pearson(honest, n),
                baltimore_n=len(bal), baltimore_nominal=bal_hits_n, baltimore_widened=bal_hits_w,
                interval_score_model=is_model, interval_score_naive=is_naive, skill=1 - is_model / is_naive,
                jackknife_plus_waverly_shop=jk)


def q_emp(xs, p):
    xs = sorted(xs)
    h = (len(xs) - 1) * p
    i = int(math.floor(h))
    return xs[i] if i + 1 >= len(xs) else xs[i] + (h - i) * (xs[i + 1] - xs[i])


# ---------------------------------------------------------------- distributions (the explorer re-implements these in JS)
def cdf_ln(x, loc, s):
    return 0.0 if x <= 0 else ND.cdf((math.log(x) - loc) / s)


def q_ln(p, loc, s):
    return math.exp(loc + s * ND.inv_cdf(p))


def cdf_tp(y, mu, slo, shi):
    """Two-piece lognormal: below the median the log spread is slo, above it shi (keeps all three benchmark points)."""
    if y <= 0:
        return 0.0
    t = math.log(y) - mu
    return ND.cdf(t / (slo if t < 0 else shi))


def q_tp(p, mu, slo, shi):
    e = ND.inv_cdf(p)
    return math.exp(mu + (slo if e < 0 else shi) * e)


def bisect(cdf, p, hi):
    lo = 0.0
    while cdf(hi) < p:
        hi *= 2
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


class Dist:
    """One format at one parcel: listing route A, affordability route B, and what follows from them."""

    def __init__(self, A, Bp, eti, wA, mult=1.0):
        self.A = None if A is None else (A[0] + math.log(mult), A[1])      # (log loc, widened sd)
        self.B = None if Bp is None else dict(Bp, mu=Bp['mu'] + math.log(mult))
        self.eti, self.wA = eti, wA

    def cdfA(self, x):
        return cdf_ln(x, *self.A)

    def cdfB(self, x):   # B = share x S - eti; can be negative
        b = self.B
        return cdf_tp((x + self.eti) / b['share'], b['mu'], b['slo'], b['shi'])

    def qA(self, p):
        return q_ln(p, *self.A)

    def qB(self, p):
        b = self.B
        return b['share'] * q_tp(p, b['mu'], b['slo'], b['shi']) - self.eti

    def qS(self, p):
        b = self.B
        return q_tp(p, b['mu'], b['slo'], b['shi'])

    def typical(self, p):
        """Mixture of the two routes, weight wA on listings."""
        if self.A and not self.B:
            return self.qA(p)
        if self.B and not self.A:
            return max(0.0, self.qB(p))
        w = self.wA
        return bisect(lambda x: w * self.cdfA(x) + (1 - w) * self.cdfB(x), p, 50.0)

    def supportable(self, p):
        """max(0, min(listing rent, affordable rent)); A and B independent within one building."""
        if self.A and not self.B:
            return self.qA(p)
        if self.B and not self.A:
            return max(0.0, self.qB(p))
        F = lambda x: 1 - (1 - self.cdfA(x)) * (1 - self.cdfB(x))
        if F(0.0) >= p:
            return 0.0
        return bisect(F, p, 50.0)

    def can_pay(self, n=400):
        """P(affordable rent >= listing rent) = E over listing rents m of P(B >= m)."""
        if not (self.A and self.B):
            return None
        return sum(1 - self.cdfB(self.qA((j + 0.5) / n)) for j in range(n)) / n


# ---------------------------------------------------------------- affordability route inputs
def route_b_params(inp, sigma_default=None):
    cfg = inp.cfg['route_b']
    loc = inp.cfg['local_demand']
    z = inp.z

    def local(f):
        return loc['food']['factor'] if f in loc['food']['applies_to'] else loc['other']['factor']

    out = {}
    # the borrowed spread comes from the cafe benchmark
    cs = cfg['cafe']['sales']
    c10 = cs['p10']['v'] * inp.cpi_factor(cs['p10']['year'])
    c90 = cs['p90']['v'] * inp.cpi_factor(cs['p90']['year'])
    sig = sigma_default if sigma_default is not None else (math.log(c90) - math.log(c10)) / (2 * z)
    for f, spec in cfg.items():
        if f == 'about':
            continue
        if 'borrow' in spec:
            continue
        if spec.get('applies') is False:
            out[f] = dict(applies=False, why=spec['why'])
            continue
        lf = local(f)
        s = spec['sales']
        trail = []
        if 'single' in s:
            pt = s['single']
            k = inp.cpi_factor(pt['year'])
            p50 = pt['v'] * k * lf
            slo = shi = sig
            trail.append(dict(point='P50', v=pt['v'], year=pt['year'], cpi=k, local=lf, out=p50, rows=pt['rows'], how=pt['how']))
            spread = 'borrowed'
        else:
            pts = {}
            for key in ('p10', 'p50', 'p90'):
                pt = s[key]
                k = inp.cpi_factor(pt['year'])
                pts[key] = pt['v'] * k * lf
                trail.append(dict(point=key.upper(), v=pt['v'], year=pt['year'], cpi=k, local=lf, out=pts[key], rows=pt['rows'], how=pt['how']))
            p50 = pts['p50']
            slo = (math.log(p50) - math.log(pts['p10'])) / z
            shi = (math.log(pts['p90']) - math.log(p50)) / z
            spread = 'own'
        sh = spec['share']
        out[f] = dict(applies=True, mu=math.log(p50), slo=slo, shi=shi, share=sh['mid'], share_low=sh.get('low'), share_high=sh.get('high'),
                      share_rows=sh['rows'], share_how=sh['how'], spread=spread, trail=trail, local=lf)
    for f, spec in cfg.items():
        if isinstance(spec, dict) and 'borrow' in spec:
            out[f] = dict(out[spec['borrow']], borrowed_from=spec['borrow'], borrow_why=spec['why'])
    return out, sig


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
def build(cfg=None, private_path=None):
    inp = Inputs(cfg or load_inputs())
    rows = rent_rows(inp)
    m = fit(rows)
    ho = holdout(rows, inp)
    c = ho['widen']
    z = inp.z
    B, sig = route_b_params(inp)
    k3 = inp.cfg['combine']['prior_rows']
    per, med, other = parcel_tax(inp)
    eti_med = med + other

    names = {}
    fmts = ['cafe', 'counter', 'foodmaker', 'tavern', 'shop', 'showroom', 'bike', 'services', 'fitness', 'studio', 'venue', 'office',
            'workshop', 'community']

    def A_at(model, grp='waverly'):
        out = {}
        for f in fmts:
            pr = predict(model, grp, f)
            out[f] = None if pr is None else (pr[0], pr[1] * c)
        return out

    A_w = A_at(m)
    nrows = {f: sum(1 for d in rows if d['fmt'] == BORROW_A.get(f, f)) for f in fmts}

    def wA_of(f):
        if A_w.get(f) is None:
            return 0.0
        if not (B.get(f) or {}).get('applies'):
            return 1.0
        return nrows[f] / (nrows[f] + k3)

    def dist(f, A=None, eti=None, mult=1.0):
        Bp = B.get(f) if (B.get(f) or {}).get('applies') else None
        return Dist(A if A is not None else A_w[f], Bp, eti_med if eti is None else eti, wA_of(f), mult)

    def qs(fn):
        return [r2(fn(p)) for p in (inp.alpha / 2, 0.5, 1 - inp.alpha / 2)]

    formats = {}
    for f in fmts:
        d = dist(f)
        Bp = B.get(f) or {}
        rec = dict(n_listings=nrows[f], wA=r4(wA_of(f)),
                   A=None if d.A is None else dict(loc=r4(A_w[f][0]), sd=r4(A_w[f][1]), q=qs(d.qA)),
                   B=None if d.B is None else dict(mu=r4(Bp['mu']), slo=r4(Bp['slo']), shi=r4(Bp['shi']), share=Bp['share'],
                                                   share_low=Bp.get('share_low'), share_high=Bp.get('share_high'), share_rows=Bp['share_rows'],
                                                   share_how=Bp['share_how'], spread=Bp['spread'], local=Bp['local'],
                                                   sales_q=qs(d.qS), q=qs(lambda p: max(0.0, d.qB(p))),
                                                   trail=[dict(t, cpi=r4(t['cpi']), out=r2(t['out'])) for t in Bp['trail']]),
                   B_na=None if Bp.get('applies', False) else Bp.get('why'),
                   typical=qs(d.typical) if (d.A or d.B) else None,
                   supportable=qs(d.supportable) if (d.A or d.B) else None,
                   can_pay=r4(d.can_pay()),
                   borrowed_from=BORROW_A.get(f) or Bp.get('borrowed_from'),
                   multiplier=None if BORROW_A.get(f, f) not in m['feff'] else dict(
                       raw=r4(math.exp(m['fraw'][BORROW_A.get(f, f)])), shrunk=r4(math.exp(m['feff'][BORROW_A.get(f, f)])),
                       keep=r4(m['fshr'][BORROW_A.get(f, f)])))
        flags = []
        if nrows[f] == 0 and f not in BORROW_A:
            flags.append('no listings: the range comes from the affordability route only' if d.B else 'no listings and no sales benchmark')
        elif nrows[f] < 3:
            flags.append(f'only {nrows[f]} listing{"s" if nrows[f] != 1 else ""}: the multiplier is mostly pulled back to 1')
        if rec['borrowed_from']:
            flags.append(f'borrowed from {rec["borrowed_from"]}')
        if Bp.get('spread') == 'borrowed':
            flags.append('one sales figure: its spread is borrowed from the cafe benchmark')
        if d.A and d.B:
            impl = (math.exp(A_w[f][0]) + eti_med) / Bp['share']
            lo_s, hi_s = d.qS(inp.alpha / 2), d.qS(1 - inp.alpha / 2)
            rec['implied_sales'] = r2(impl)
            if not (lo_s <= impl <= hi_s):
                flags.append(f'the listing median implies ${impl:,.0f}/sq ft of sales, outside the benchmark range')
        # enough evidence to rank this use by money: a sales route, or at least three listings
        rec['rankable'] = bool(d.B) or nrows[f] >= 3
        if not rec['rankable']:
            flags.append('not enough evidence to rank it by money (no sales benchmark and fewer than 3 listings)')
        rec['flags'] = flags
        formats[f] = rec
    for f, why in inp.cfg['not_estimated'].items():
        formats[f] = dict(not_estimated=why)

    # parcels: own-listing exclusion and pass-through costs
    parcels = {}
    for a, v in per.items():
        parcels[a] = dict(tax=r4(v['tax']), eti=r4(v['tax'] + other))
    own = {}
    for d in rows:
        for a in d['parcels']:
            own.setdefault(a, set()).add(d['id'])
    for a, ids in sorted(own.items()):
        mi = fit([d for d in rows if d['id'] not in ids])
        Ai = A_at(mi)
        parcels.setdefault(a, dict(tax=None, eti=r4(eti_med)))
        parcels[a]['own_listings'] = sorted(ids)
        parcels[a]['A'] = {f: [r4(v[0]), r4(v[1])] for f, v in Ai.items() if v is not None}

    # examples for the JS consistency check: the parcels available now
    examples = []
    for a in ['2932', '3026', '3036', '3107', '3117', '3211']:
        pa = parcels.get(a, {})
        eti = pa.get('eti') or eti_med
        for f in ('cafe', 'shop', 'fitness', 'bike', 'venue'):
            Ao = pa.get('A', {}).get(f)
            d = dist(f, A=tuple(Ao) if Ao else None, eti=eti)
            examples.append(dict(address=a, fmt=f, typical=qs(d.typical), supportable=qs(d.supportable), can_pay=r4(d.can_pay())))

    # the trail behind the Waverly mean
    wts = row_weights(m, rows)
    used = {d['id']: d for d in rows}
    trail = sorted(({'id': i, 'w': r4(w), 'nnn': r2(used[i]['nnn']), 'fmt': used[i]['fmt'], 'grp': used[i]['grp']} for i, w in wts.items()),
                   key=lambda x: -x['w'])

    # nearest listings per format (for showing, not for the range)
    rr = inp.cfg['rent_rows']
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
                           nnn=r2(d['nnn']), sqft=d['sqft'], year=d['year'], url=d['url']) for d in top]

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

    # operators' figures against the ranges
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
        Bf = B.get(f) or {}
        inside = None
        rng = None
        if Bf.get('applies'):
            lo = q_tp(inp.alpha / 2, Bf['mu'], Bf['slo'], Bf['shi']); hi = q_tp(1 - inp.alpha / 2, Bf['mu'], Bf['slo'], Bf['shi'])
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

    # sensitivity reruns
    sens = []
    def waverly_shop_p50(rows_, model=None):
        mm = model or fit(rows_)
        return math.exp(predict(mm, 'waverly', 'shop')[0])
    sens.append(dict(what='Lease-basis loads (modified gross / gross)', setting='$2 / $4 (default)', result=f'Waverly shop listing median ${waverly_shop_p50(rows, m):.2f}'))
    for alt in inp.loads['sensitivity']:
        lo2 = dict(inp.loads); lo2.update(alt)
        sens.append(dict(what='Lease-basis loads (modified gross / gross)', setting=f'${alt["modified gross"]:.0f} / ${alt["gross"]:.0f}',
                         result=f'Waverly shop listing median ${waverly_shop_p50(rent_rows(inp, loads=lo2)):.2f}'))
    sens.append(dict(what='Drop the one in-place lease (R-004, 3217)', setting='dropped', result=f'Waverly shop listing median ${waverly_shop_p50(rent_rows(inp, drop={"R-004"})):.2f}'))
    for kk in (1, 3, 10):
        w = nrows['cafe'] / (nrows['cafe'] + kk)
        d = Dist(A_w['cafe'], B['cafe'], eti_med, w)
        sens.append(dict(what='Weight on listings, n/(n+k), cafe', setting=f'k = {kk} (weight {w:.2f})', result='typical rent P10/P50/P90 ' + ' / '.join(f'${d.typical(p):.2f}' for p in (0.1, 0.5, 0.9))))
    for sg in (0.3, 0.6):
        Bs, _ = route_b_params(inp, sigma_default=sg)
        d = Dist(None, Bs['bike'], eti_med, 0.0)
        sens.append(dict(what='Borrowed sales spread (bike)', setting=f'sigma = {sg}', result='affordable rent P10/P50/P90 ' + ' / '.join(f'${max(0, d.qB(p)):.2f}' for p in (0.1, 0.5, 0.9))))
    d = Dist(None, B['bike'], eti_med, 0.0)
    sens.append(dict(what='Borrowed sales spread (bike)', setting=f'sigma = {sig:.3f} (default, from cafe)', result='affordable rent P10/P50/P90 ' + ' / '.join(f'${max(0, d.qB(p)):.2f}' for p in (0.1, 0.5, 0.9))))
    for f in ('cafe', 'shop', 'services', 'fitness'):
        b = B[f]
        for lab in ('share_low', 'share_high'):
            if b.get(lab):
                d = Dist(None, dict(b, share=b[lab]), eti_med, 0.0)
                sens.append(dict(what=f'Share of sales spent on rent ({f})', setting=f'{b[lab]:.1%}', result=f'affordable rent median ${max(0, d.qB(0.5)):.2f}'))

    out = dict(
        version='comps engine v1',
        built_from=dict(rents=len(read_csv('rents.csv')), rows_used=len(rows), sources=ho['sources'], corridors=len(m['n']),
                        benchmarks=len(read_csv('benchmarks.csv')), operators=len(read_csv('operators.csv'))),
        interval=dict(alpha=inp.alpha, z=r4(z), widen=r4(c)),
        dollars=inp.target,
        model=dict(within_sd=r4(math.sqrt(m['s2'])), between_corridor_sd=r4(math.sqrt(m['tau2'])), between_format_sd=r4(math.sqrt(m['tf2'])),
                   city_means={k: r2(math.exp(v)) for k, v in m['mu'].items()},
                   waverly=dict(n=m['n']['waverly'], raw=r2(math.exp(m['raw']['waverly'])), pooled=r2(math.exp(m['post']['waverly'])),
                                B=r4(m['B']['waverly']), own_share=r4(1 - m['B']['waverly'])),
                   waverly_trail=trail, sigma_default=r4(sig), prior_rows=k3, eti_median=r4(eti_med), tax_median=r4(med),
                   pass_through_other=other, baltimore_p90=r2(q_emp([d['nnn'] for d in rows if d['city'] == 'baltimore'], 1 - inp.alpha / 2))),
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
                     jackknife_plus_waverly_shop=[r2(x) for x in ho['jackknife_plus_waverly_shop']]),
        sensitivity=sens,
        approval=inp.cfg['approval'],
        plan=inp.cfg['plan'],
        local_demand=inp.cfg['local_demand'],
        sources=sources_index(),
    )
    priv = None
    if private_path:
        priv = private_step(private_path, inp, B, sig, m, A_w, wA_of, eti_med, qs)
    return out, priv


def sources_index():
    """Every library row a range can cite, so the page can link a row id to its source."""
    idx = {}
    for name in ('rents.csv', 'benchmarks.csv', 'operators.csv'):
        for x in read_csv(name):
            idx[x['row_id']] = dict(t=x['source_title'][:140], u=x['source_url'], y=x['figure_year'] if 'figure_year' in x else x.get('revenue_year', ''),
                                    q=(x.get('evidence_quote') or '')[:160])
    return idx


# ---------------------------------------------------------------- private step
def private_step(path, inp, B, sig, m, A_w, wA_of, eti_med, qs):
    path = os.path.abspath(path)
    if os.path.commonpath([path, REPO]) == REPO:
        raise SystemExit('Refusing: the private operator file must live outside the repository (CUSP RCF or another secure folder).')
    with open(path, encoding='utf-8') as fh:
        op = json.load(fh)
    f = op['format_id']
    if not (B.get(f) or {}).get('applies'):
        raise SystemExit(f'No affordability route for {f}; nothing to calibrate.')
    s = op.get('sales_per_sqft') or (op['annual_sales'] / op['sqft'])
    s *= inp.cpi_factor(op.get('year', inp.target))
    b = B[f]
    k_obs = math.log(s) - b['mu']
    tau = math.sqrt(m['tau2'])
    def w_of(t, sg):
        return t * t / (t * t + sg * sg)
    runs = [('default', w_of(tau, sig))] + [(json.dumps(x), w_of(x.get('tau', tau), x.get('sigma', sig))) for x in inp.cfg['private_calibration']['sensitivity']]
    lo = q_tp(inp.alpha / 2, b['mu'], b['slo'], b['shi']); hi = q_tp(1 - inp.alpha / 2, b['mu'], b['slo'], b['shi'])
    res = dict(note='PRIVATE. Never commit, publish or quote. Built from the NDA operator file; the calibrated figures can be inverted to recover it.',
               format=f, inside_public_range=lo <= s <= hi, runs=[])
    for lab, w in runs:
        bb = dict(b, mu=b['mu'] + w * k_obs)
        d = Dist(A_w[f], bb, eti_med, wA_of(f))
        res['runs'].append(dict(setting=lab, weight=round(w, 3), shift_pct=round(100 * (math.exp(w * k_obs) - 1), 1),
                                sales=qs(d.qS), typical=qs(d.typical), supportable=qs(d.supportable)))
    return res


def main():
    priv_in = os.environ.get('PTU_PRIVATE_OPERATOR')
    out, priv = build(private_path=priv_in)
    dst = os.path.join(HERE, 'comps_ranges.json')
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    h = out['holdout']
    print(f"wrote {os.path.relpath(dst, REPO)}: {out['built_from']['rows_used']} listings in {out['built_from']['corridors']} corridors; "
          f"held-out coverage {h['nominal_hits']}/{h['n']} at the nominal 80%, widened x{out['interval']['widen']:.2f}")
    if priv is not None:
        pdir = os.environ.get('PTU_PRIVATE_OUT') or os.path.dirname(os.path.abspath(priv_in))
        if os.path.commonpath([os.path.abspath(pdir), REPO]) == REPO:
            raise SystemExit('Refusing to write the private annex inside the repository.')
        pth = os.path.join(pdir, 'private_annex.json')
        with open(pth, 'w', encoding='utf-8') as fh:
            json.dump(priv, fh, indent=1)
        print('private annex written outside the repository (contents not printed)')


if __name__ == '__main__':
    sys.exit(main())
