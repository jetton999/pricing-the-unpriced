#!/usr/bin/env python3
"""Back-test v2: does a building's documented past add information about its use today?

    python3 team/validation/backtest.py        # writes team/validation/out/backtest_v2.json

The plan is PLAN_backtest_v2.md. It was committed four minutes before the first results, in the same working
session, so it records the rule but is not an independent pre-registration. Standard library only; about a minute.
Besides the JSON it writes out/backtest_v2.md, the full results as tables, generated so that no figure is typed by hand.

One row per parcel and use category. Outcome: the parcel has that use today. Base model: one
intercept per category ("guess the common uses"). History model: the base model plus
beta x log(1 + decades on record before the cut-off). Three data sets:

  frontage           the 69 frontage parcels, every source the extractor joins (exploratory: the
                     model was chosen on these parcels)
  frontage_sponsor   the same parcels, sponsor records only (the kind of evidence the other blocks have)
  other_blocks       Greenmount parcels outside the frontage: history from the sponsor's curated
                     records, use today coded blind from the sponsor's 2026 storefront summaries
"""
import collections
import csv
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get('REPO') or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'team', 'extractor'))
from rules import classify  # noqa: E402

csv.field_size_limit(10 ** 9)
CATS = ['food & drink', 'retail goods', 'personal services', 'automotive', 'entertainment & assembly',
        'institutional & religious', 'office', 'production & light industry']
FRONTAGE_SIDES = {'65', '67', '68', '69', '70', '71', '72'}
GENERIC = 'store building (generic)'
CUTS = (1960, 1940)
N_PERM = 10000
SEED = 20261026
# the week-1 class A rule: records that state a use (team/week1/focus_area.py)
A_SOURCES = {'polk', 'census_directory'}
A_CATEGORIES = {'directory', 'advertisement', 'commerce', 'commercial', 'construction', 'institution'}


def rd(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


# The uses today on the other blocks. PTU_OUTCOMES points the test at a re-coded file with the same columns (the
# two-coder check in team/validation/two_coder writes one); the results then go to out/backtest_v2_recoded.* and the
# files of record are left alone.
OUTCOMES = os.environ.get('PTU_OUTCOMES')


def outcome_rows():
    if OUTCOMES:
        with open(OUTCOMES, encoding='utf-8-sig', newline='') as fh:
            return list(csv.DictReader(fh))
    return rd('team', 'validation', 'outcomes_other_greenmount_2026-10.csv')


def is_admin(source):
    return source.startswith('baltimore:') or source in ('sdat_assessments', 'sdat:owner')


# ------------------------------------------------------------------ data
def frontage(sponsor_only=False):
    """Parcels, use today and decades on record for the 69 frontage parcels."""
    fa = {r['property_id']: r for r in rd('team', 'week1', 'out', 'focus_area_properties.csv')}
    gaps = rd('team', 'evidence', 'blocklot_gaps.csv')
    merged = {g['property_id']: g['current_property_id'] for g in gaps if g['current_property_id']}
    props = {k: v for k, v in fa.items() if v['block_side_id'] in FRONTAGE_SIDES and k not in merged}
    now = collections.defaultdict(set)
    for t in rd('team', 'tenants', 'current_tenants_2026-10.csv'):
        pid = merged.get(t['property_id'], t['property_id'])
        if pid in props and t['status'] == 'occupied':
            now[pid] |= {c for c in (t['business_type'] or '').split(' ; ') if c in CATS}
    ev = rd('team', 'extractor', 'out', 'evidence.csv')
    rows = []
    for e in ev:
        pid = merged.get(e['property_id'], e['property_id'])
        if pid not in props or not e['year'].isdigit() or not e['decade']:
            continue
        if e['source'].startswith('sponsor') and nr_summary_row(e['text']):
            continue   # NR summary rows dated to the build year (see build_explorer.py)
        if sponsor_only and not e['source'].startswith('sponsor'):
            continue
        if e['use_category'] in CATS and e['use_subcategory'] != GENERIC:
            rows.append((pid, e['use_category'], int(e['year'])))
    parcels = sorted(p for p in props if now.get(p))
    group = {p: props[p]['block_side_id'] for p in parcels}
    return dict(parcels=parcels, now={p: now[p] for p in parcels}, records=rows, group=group,
                n_unoccupied=len(props) - len(parcels))


def nr_summary_row(text):
    """A National Register summary row: dated to the build year, but it states the use as of 2013. Counting it as
    pre-cut-off history lets the outcome leak into the predictor, so both samples leave these rows out."""
    return ('B-5229' in text and text.startswith('Built ca')) or 'Use as of 2013' in text


MULTI_TENANT = 3   # a parcel with this many kinds of use today is a multi-tenant centre, not one storefront


def other_blocks(include_low=True, keep_nr_summary=False, stated_only=False, without=()):
    """Greenmount parcels outside the frontage, coded blind (outcomes_other_greenmount_2026-10.csv).
    stated_only: code a record from the business linked to it, or from a directory line, and from nothing else,
    so that a narrative summary which also mentions a later event cannot set the use (the review's "hindsight" point).
    without: property ids to leave out."""
    oc = [r for r in outcome_rows() if r['included'] == 'yes' and r['property_id'] not in without]
    if not include_low:
        oc = [r for r in oc if r['coding_confidence'] != 'low']
    parcels = sorted(r['property_id'] for r in oc)
    now = {r['property_id']: {c for c in r['use_today'].split(' ; ') if c in CATS} for r in oc}
    group = {r['property_id']: r['block_side'] for r in oc}
    subjects = {s['id']: s for s in rd('subjects.csv')}
    biz = collections.defaultdict(list)
    for link in rd('incident_subjects.csv'):
        s = subjects.get(link['subject_id'])
        if link['relationship'] == 'operated_at' and s and s['subject_type'] == 'business':
            biz[link['property_incident_id']].append(s['name'])
    keep = set(parcels)
    rows = []
    for r in rd('property_incidents.csv'):
        if r['property_id'] not in keep or is_admin(r['source']):
            continue
        if not keep_nr_summary and nr_summary_row(r['summary']):
            continue   # the leak found in the sponsor's review of 17 Nov 2026: frontage() left these out, this did not
        b = biz.get(r['id'], [])
        if not (b or r['source'] in A_SOURCES or r['category'] in A_CATEGORIES):
            continue
        y = r['occurred_at'][:4]
        if not y.isdigit():
            continue
        if stated_only:
            if b:
                text = ' '.join(b)
            elif r['source'] in A_SOURCES:
                text = r['summary']
            else:
                continue
        else:
            text = f"{r['summary']} {' '.join(b)}"
        c, s, _ = classify(text)
        if s == GENERIC and b:
            s = 'named store'
        if c in CATS and s != GENERIC:
            rows.append((r['property_id'], c, int(y)))
    address = {r['property_id']: r['address'].replace(' Greenmount Ave', '') for r in oc}
    return dict(parcels=parcels, now=now, records=rows, group=group, address=address)


def decades(records, cut):
    d = collections.defaultdict(lambda: collections.defaultdict(set))
    for pid, c, y in records:
        if y <= cut:
            d[pid][c].add(y // 10 * 10)
    return d


def design(data, cut, depth=False):
    """Rows of (parcel, category index, x, depth, y)."""
    dec = decades(data['records'], cut)
    out = []
    for p in data['parcels']:
        total = len(set().union(*dec[p].values())) if dec.get(p) else 0
        for j, c in enumerate(CATS):
            out.append((p, j, math.log1p(len(dec.get(p, {}).get(c, ()))), math.log1p(total),
                        1.0 if c in data['now'][p] else 0.0))
    return out


# ------------------------------------------------------------------ statistics
def solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(M[r][i]))
        M[i], M[piv] = M[piv], M[i]
        if abs(M[i][i]) < 1e-12:
            raise ValueError('singular')
        for r in range(n):
            if r != i:
                f = M[r][i] / M[i][i]
                for k in range(i, n + 1):
                    M[r][k] -= f * M[i][k]
    return [M[i][n] / M[i][i] for i in range(n)]


def sigmoid(z):
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


def fit_logit(X, y, ridge=1e-4, iters=50):
    """Maximum likelihood by Newton's method, with a tiny ridge so a category with no cases stays finite."""
    k = len(X[0])
    beta = [0.0] * k
    for _ in range(iters):
        g = [-ridge * b for b in beta]
        H = [[(ridge if i == j else 0.0) for j in range(k)] for i in range(k)]
        for xi, yi in zip(X, y):
            p = sigmoid(sum(a * b for a, b in zip(xi, beta)))
            w = p * (1 - p)
            for i in range(k):
                if xi[i]:
                    g[i] += (yi - p) * xi[i]
                    for j in range(k):
                        if xi[j]:
                            H[i][j] += w * xi[i] * xi[j]
        step = solve(H, g)
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-9:
            break
    ll = 0.0
    for xi, yi in zip(X, y):
        p = min(max(sigmoid(sum(a * b for a, b in zip(xi, beta))), 1e-12), 1 - 1e-12)
        ll += yi * math.log(p) + (1 - yi) * math.log(1 - p)
    return beta, ll


def matrix(rows, history=True, depth=False):
    X = []
    for _, j, x, d, _y in rows:
        v = [0.0] * len(CATS)
        v[j] = 1.0
        if depth:
            v.append(d)
        if history:
            v.append(x)
        X.append(v)
    return X, [r[4] for r in rows]


def predict(beta, X):
    return [sigmoid(sum(a * b for a, b in zip(xi, beta))) for xi in X]


def logloss(p, y):
    return -sum(yi * math.log(max(pi, 1e-12)) + (1 - yi) * math.log(max(1 - pi, 1e-12)) for pi, yi in zip(p, y)) / len(y)


def auc(score, y):
    pos = [s for s, t in zip(score, y) if t == 1]
    neg = [s for s, t in zip(score, y) if t == 0]
    if not pos or not neg:
        return None
    wins = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def chi2_sf1(x):
    return math.erfc(math.sqrt(max(x, 0) / 2))


def score_stat(rows, xs):
    """S = sum of x times (y minus the category's share of y): the score for beta under the base model."""
    share = collections.defaultdict(lambda: [0.0, 0])
    for _, j, _x, _d, yv in rows:
        share[j][0] += yv
        share[j][1] += 1
    return sum(x * (r[4] - share[r[1]][0] / share[r[1]][1]) for r, x in zip(rows, xs))


def permutation_p(rows, data, n=N_PERM, seed=SEED):
    """One-sided p for beta > 0: shuffle whole parcel histories among parcels on the same block side."""
    rng = random.Random(seed)
    parcels = data['parcels']
    k = len(CATS)
    hist = {p: [rows[i * k + j][2] for j in range(k)] for i, p in enumerate(parcels)}
    obs = score_stat(rows, [r[2] for r in rows])
    groups = collections.defaultdict(list)
    for p in parcels:
        groups[data['group'][p]].append(p)
    ge = 0
    for _ in range(n):
        perm = {}
        for ps in groups.values():
            sh = ps[:]
            rng.shuffle(sh)
            perm.update(zip(ps, sh))
        xs = [v for p in parcels for v in hist[perm[p]]]
        if score_stat(rows, xs) >= obs - 1e-12:
            ge += 1
    return (ge + 1) / (n + 1), obs


def fast_perm(rows, data, n=N_PERM, seed=SEED, cats=None):
    """The same test as permutation_p, computed from a parcel-by-parcel table so that it can be repeated many times.
    S(shuffle) = sum over parcels p of M[p][parcel whose history p receives], where
    M[p][q] = sum over categories of history(q, c) x (use today(p, c) - the category's share).
    cats: category indexes to count (default all), for the per-category runs."""
    rng = random.Random(seed)
    parcels = data['parcels']
    k = len(CATS)
    keep = range(k) if cats is None else cats
    share = collections.defaultdict(lambda: [0.0, 0])
    for _, j, _x, _d, yv in rows:
        share[j][0] += yv
        share[j][1] += 1
    hist = [[rows[i * k + j][2] for j in range(k)] for i in range(len(parcels))]
    res = [[rows[i * k + j][4] - share[j][0] / share[j][1] for j in range(k)] for i in range(len(parcels))]
    M = [[sum(hist[q][j] * res[p][j] for j in keep) for q in range(len(parcels))] for p in range(len(parcels))]
    idx = {p: i for i, p in enumerate(parcels)}
    obs = sum(M[i][i] for i in range(len(parcels)))
    groups = collections.defaultdict(list)
    for p in parcels:
        groups[data['group'][p]].append(p)
    ge = 0
    for _ in range(n):
        tot = 0.0
        for ps in groups.values():
            sh = ps[:]
            rng.shuffle(sh)
            for a, b in zip(ps, sh):
                tot += M[idx[a]][idx[b]]
        if tot >= obs - 1e-12:
            ge += 1
    return (ge + 1) / (n + 1), obs


def per_category(rows):
    """What each kind of use adds to the test statistic, and the plain count behind it."""
    out = []
    for j, c in enumerate(CATS):
        rs = [r for r in rows if r[1] == j]
        sh = sum(r[4] for r in rs) / len(rs)
        with_h = [r for r in rs if r[2] > 0]
        out.append(dict(category=c, parcels_with_use_today=int(sum(r[4] for r in rs)), base_rate=round(sh, 3),
                        parcels_with_history=len(with_h), of_which_have_it_today=int(sum(r[4] for r in with_h)),
                        expected_from_base_rate=round(sh * len(with_h), 2),
                        contribution=round(sum(r[2] * (r[4] - sh) for r in rs), 3)))
    return out


STOREFRONT_CATS = ('food & drink', 'retail goods', 'personal services')   # the general storefront trades


def category_runs(data, cut):
    """The same shuffle test counted over some kinds of use only: is the signal in ordinary storefront trades,
    or in buildings built for one purpose (garages)?"""
    rows = design(data, cut)
    runs = [('all eight kinds of use', list(range(len(CATS)))),
            ('ordinary storefront trades only (food and drink, retail goods, personal services)', [CATS.index(c) for c in STOREFRONT_CATS]),
            ('every kind except automotive', [j for j, c in enumerate(CATS) if c != 'automotive']),
            ('automotive only', [CATS.index('automotive')])]
    out = []
    for label, cats in runs:
        p, sc = fast_perm(rows, data, cats=cats)
        out.append(dict(kinds=label, p_perm=round(p, 4), score=round(sc, 3)))
    return out


def leave_one_parcel_out(data, cut):
    """The shuffle test with each parcel left out in turn: how much does the result hang on single buildings?"""
    full, _ = fast_perm(design(data, cut), data)
    out = []
    for p in data['parcels']:
        d = dict(data, parcels=[q for q in data['parcels'] if q != p])
        pv, _ = fast_perm(design(d, cut), d)
        out.append(dict(property_id=p, address=data.get('address', {}).get(p, p), p_perm=round(pv, 4)))
    ps = sorted(x['p_perm'] for x in out)
    side = (lambda x: x >= 0.05) if full < 0.05 else (lambda x: x < 0.05)
    return dict(cut=cut, p_all_parcels=round(full, 4), min=ps[0], max=ps[-1], median=ps[len(ps) // 2],
                below_0_05=sum(1 for x in ps if x < 0.05), parcels=len(ps),
                crosses_0_05=[x for x in sorted(out, key=lambda x: x['p_perm']) if side(x['p_perm'])],
                lowest=sorted(out, key=lambda x: x['p_perm'])[:3], highest=sorted(out, key=lambda x: -x['p_perm'])[:3])


def transfer_interval(train, test, cut, n=4000, seed=SEED):
    """A 95% interval for the transfer gain: the test parcels are drawn again with replacement (each parcel with its
    eight rows), the coefficients stay as fitted on the training parcels."""
    r_tr, r_te = design(train, cut), design(test, cut)
    X1, y1 = matrix(r_tr)
    X0, _ = matrix(r_tr, history=False)
    b1, _ = fit_logit(X1, y1)
    b0, _ = fit_logit(X0, y1)
    T1, yt = matrix(r_te)
    T0, _ = matrix(r_te, history=False)
    p1, p0 = predict(b1, T1), predict(b0, T0)
    k = len(CATS)
    ll = lambda p, y: -(y * math.log(max(p, 1e-12)) + (1 - y) * math.log(max(1 - p, 1e-12)))
    per = [(sum(ll(p0[i * k + j], yt[i * k + j]) for j in range(k)), sum(ll(p1[i * k + j], yt[i * k + j]) for j in range(k)))
           for i in range(len(test['parcels']))]
    m = len(per)
    gain = (sum(a for a, _ in per) - sum(b for _, b in per)) / (m * k)
    rng = random.Random(seed)
    gains, aucd = [], []
    for _ in range(n):
        pick = [rng.randrange(m) for _ in range(m)]
        gains.append(sum(per[i][0] - per[i][1] for i in pick) / (m * k))
        ys = [yt[i * k + j] for i in pick for j in range(k)]
        a0, a1 = auc([p0[i * k + j] for i in pick for j in range(k)], ys), auc([p1[i * k + j] for i in pick for j in range(k)], ys)
        if a0 is not None and a1 is not None:
            aucd.append(a1 - a0)
    gains.sort()
    aucd.sort()
    q = lambda xs, f: xs[min(len(xs) - 1, int(f * len(xs)))]
    return dict(cut=cut, draws=n, gain_per_row=round(gain, 4), gain_ci95=[round(q(gains, 0.025), 4), round(q(gains, 0.975), 4)],
                share_of_draws_with_a_gain=round(sum(1 for g in gains if g > 0) / n, 3),
                auc_change=round(auc(p1, yt) - auc(p0, yt), 3), auc_change_ci95=[round(q(aucd, 0.025), 3), round(q(aucd, 0.975), 3)],
                distinguishable_from_zero=bool(q(gains, 0.025) > 0))


def selection_check(cut, n=N_PERM, seed=SEED):
    """The test is run on storefronts in use; the plan is for empty ones. Do the two groups have different histories?
    Frontage storefronts only. Labels (empty or in use) are shuffled within block sides."""
    fa = {r['property_id']: r for r in rd('team', 'week1', 'out', 'focus_area_properties.csv')}
    gaps = rd('team', 'evidence', 'blocklot_gaps.csv')
    merged = {g['property_id']: g['current_property_id'] for g in gaps if g['current_property_id']}
    props = {k: v for k, v in fa.items() if v['block_side_id'] in FRONTAGE_SIDES and k not in merged}
    house = {r['property_id'] for r in rd('storefront_assessments.csv') if r['status'] == 'residential'}
    state = {}
    for t in rd('team', 'tenants', 'current_tenants_2026-10.csv'):
        pid = merged.get(t['property_id'], t['property_id'])
        if pid not in props or pid in house or pid in state:
            continue
        if t['status'] in ('vacant', 'for lease'):
            state[pid] = 'empty'
        elif t['status'] == 'occupied' and any(c in CATS for c in (t['business_type'] or '').split(' ; ')):
            state[pid] = 'in use'
    fr = frontage()
    dec = decades(fr['records'], cut)
    vec = {p: [len(dec.get(p, {}).get(c, ())) for c in CATS] for p in state}
    ids = sorted(state)

    def stats(lab):
        out = {}
        for g in ('empty', 'in use'):
            ps = [p for p in ids if lab[p] == g]
            tot = [sum(vec[p]) for p in ps]
            sh = [0.0] * len(CATS)
            for p in ps:
                t = sum(vec[p])
                if t:
                    for j in range(len(CATS)):
                        sh[j] += vec[p][j] / t
            nz = sum(1 for p in ps if sum(vec[p]))
            out[g] = dict(n=len(ps), depth=sum(tot) / len(ps), any=sum(1 for t in tot if t) / len(ps),
                          mix=[x / nz if nz else 0.0 for x in sh])
        return out

    obs = stats(state)
    d_depth = obs['empty']['depth'] - obs['in use']['depth']
    d_mix = sum(abs(a - b) for a, b in zip(obs['empty']['mix'], obs['in use']['mix']))
    rng = random.Random(seed)
    groups = collections.defaultdict(list)
    for p in ids:
        groups[props[p]['block_side_id']].append(p)
    ge_depth = ge_mix = 0
    for _ in range(n):
        lab = {}
        for ps in groups.values():
            ls = [state[p] for p in ps]
            rng.shuffle(ls)
            lab.update(zip(ps, ls))
        st = stats(lab)
        if abs(st['empty']['depth'] - st['in use']['depth']) >= abs(d_depth) - 1e-12:
            ge_depth += 1
        if sum(abs(a - b) for a, b in zip(st['empty']['mix'], st['in use']['mix'])) >= d_mix - 1e-12:
            ge_mix += 1
    return dict(cut=cut, empty=obs['empty']['n'], in_use=obs['in use']['n'],
                decades_on_record=dict(empty=round(obs['empty']['depth'], 2), in_use=round(obs['in use']['depth'], 2),
                                       p_two_sided=round((ge_depth + 1) / (n + 1), 4)),
                share_with_any_history=dict(empty=round(obs['empty']['any'], 3), in_use=round(obs['in use']['any'], 3)),
                mix_of_uses_on_record=dict(empty={c: round(v, 3) for c, v in zip(CATS, obs['empty']['mix'])},
                                           in_use={c: round(v, 3) for c, v in zip(CATS, obs['in use']['mix'])},
                                           distance=round(d_mix, 3), p=round((ge_mix + 1) / (n + 1), 4)))


def by_history(rows):
    """Observed against expected (from each category's share) by decades on record: the plain-words table."""
    share = collections.defaultdict(lambda: [0.0, 0])
    for _, j, _x, _d, yv in rows:
        share[j][0] += yv
        share[j][1] += 1
    out = []
    for label, lo, hi in (('none on record', 0, 0), ('1 decade', 1, 1), ('2 or more decades', 2, 99)):
        sel = [r for r in rows if lo <= round(math.expm1(r[2])) <= hi]
        exp = sum(share[r[1]][0] / share[r[1]][1] for r in sel)
        out.append(dict(group=label, pairs=len(sel), present=int(sum(r[4] for r in sel)), expected=round(exp, 1)))
    return out


def analyse(data, cut, perms=N_PERM):
    rows = design(data, cut)
    X1, y = matrix(rows)
    X0, _ = matrix(rows, history=False)
    b1, l1 = fit_logit(X1, y)
    b0, l0 = fit_logit(X0, y)
    Xd, _ = matrix(rows, depth=True)
    Xd0, _ = matrix(rows, history=False, depth=True)
    bd, ld = fit_logit(Xd, y)
    _, ld0 = fit_logit(Xd0, y)
    p_perm, s = permutation_p(rows, data, perms)
    lr = 2 * (l1 - l0)
    lrd = 2 * (ld - ld0)
    with_hist = sum(1 for p in data['parcels'] if any(r[2] > 0 for r in rows if r[0] == p))
    return dict(cut=cut, parcels=len(data['parcels']), parcels_with_history=with_hist, rows=len(rows), per_category=per_category(rows),
                present=int(sum(y)), beta=round(b1[-1], 3),
                odds_3_decades=round(math.exp(b1[-1] * math.log(4)), 2),
                lr=round(lr, 2), p_lr=round(chi2_sf1(lr) / 2 if b1[-1] > 0 else 1 - chi2_sf1(lr) / 2, 4),
                p_perm=round(p_perm, 4), score=round(s, 3),
                auc_base=round(auc(predict(b0, X0), y), 3), auc_history=round(auc(predict(b1, X1), y), 3),
                beta_with_depth_control=round(bd[-1], 3),
                p_lr_with_depth_control=round(chi2_sf1(lrd) / 2 if bd[-1] > 0 else 1 - chi2_sf1(lrd) / 2, 4),
                by_history=by_history(rows))


def transfer(train, test, cut):
    """Fit on one set of parcels, score another without refitting."""
    r_tr, r_te = design(train, cut), design(test, cut)
    X1, y1 = matrix(r_tr)
    X0, _ = matrix(r_tr, history=False)
    b1, _ = fit_logit(X1, y1)
    b0, _ = fit_logit(X0, y1)
    T1, yt = matrix(r_te)
    T0, _ = matrix(r_te, history=False)
    p1, p0 = predict(b1, T1), predict(b0, T0)
    return dict(cut=cut, logloss_base=round(logloss(p0, yt), 4), logloss_history=round(logloss(p1, yt), 4),
                auc_base=round(auc(p0, yt), 3), auc_history=round(auc(p1, yt), 3),
                beta_train=round(b1[-1], 3), better=logloss(p1, yt) < logloss(p0, yt))


def leave_one_side_out(data, cut):
    sides = sorted(set(data['group'].values()))
    ll0 = ll1 = 0.0
    n = 0
    s0, s1, ys = [], [], []
    for s in sides:
        tr = dict(data, parcels=[p for p in data['parcels'] if data['group'][p] != s])
        te = dict(data, parcels=[p for p in data['parcels'] if data['group'][p] == s])
        if not te['parcels']:
            continue
        r_tr, r_te = design(tr, cut), design(te, cut)
        X1, y1 = matrix(r_tr)
        X0, _ = matrix(r_tr, history=False)
        b1, _ = fit_logit(X1, y1)
        b0, _ = fit_logit(X0, y1)
        T1, yt = matrix(r_te)
        T0, _ = matrix(r_te, history=False)
        p1, p0 = predict(b1, T1), predict(b0, T0)
        ll1 += logloss(p1, yt) * len(yt)
        ll0 += logloss(p0, yt) * len(yt)
        n += len(yt)
        s0 += p0
        s1 += p1
        ys += yt
    return dict(cut=cut, sides=len(sides), logloss_base=round(ll0 / n, 4), logloss_history=round(ll1 / n, 4),
                auc_base=round(auc(s0, ys), 3), auc_history=round(auc(s1, ys), 3), better=ll1 < ll0)


def similarity(data_ids):
    """How the other blocks compare with the frontage on what the record says about the buildings."""
    props = {r['id']: r for r in rd('properties.csv')}
    def stats(ids):
        ps = [props[i] for i in ids if i in props]
        yb = sorted(int(p['year_built']) for p in ps if (p['year_built'] or '0').isdigit() and int(p['year_built']) > 1800)
        c1 = sum(1 for p in ps if p['zoning_code'] == 'C-1')
        return dict(parcels=len(ps), c1_share=round(c1 / len(ps), 2) if ps else None,
                    median_year_built=yb[len(yb) // 2] if yb else None)
    return {k: stats(v) for k, v in data_ids.items()}


def report(res):
    """The results as tables, written from the numbers so that no figure in it is typed by hand."""
    g = lambda key, cut: next(a for a in res[key] if a['cut'] == cut)
    pv = lambda x: f'{x:.3f}'
    o6, o4 = g('other_blocks', 1960), g('other_blocks', 1940)
    d = res['decision']
    L = ['# Back-test v2: results', '',
         'Written by `team/validation/backtest.py` from `out/backtest_v2.json`. Do not edit by hand; rerun the script.', '',
         '## The test', '',
         f"On {o6['parcels']} Greenmount parcels outside the frontage ({o6['rows']} pairs of a parcel and a kind of use, "
         f"{o6['present']} of them true today), with records up to 1960: one-sided shuffle test **p = {pv(o6['p_perm'])}**. "
         f"With records up to 1940: p = {pv(o4['p_perm'])}.",
         '',
         f"The rule agreed with the sponsor on 9 November 2026 needs p below 0.05 and a lower held-out log loss. "
         f"The test **{'passes' if d['passes'] else 'does not pass'}**. Before the leak found on 17 November 2026 was fixed, "
         f"the same test gave p = {pv(d['p_perm_before_leak_fix'])}.",
         '', 'If the rule fails: ' + d['if_it_fails'] + '.', '',
         '## Which kinds of use carry the result (records up to 1960)', '',
         '| Kind of use | Parcels that have it today | Base rate | Parcels with it on record before 1960 | Of those, have it today | Expected from the base rate | Adds to the test statistic |',
         '|---|---|---|---|---|---|---|']
    for c in o6['per_category']:
        L.append(f"| {c['category']} | {c['parcels_with_use_today']} | {c['base_rate']:.0%} | {c['parcels_with_history']} | "
                 f"{c['of_which_have_it_today']} | {c['expected_from_base_rate']:.1f} | {c['contribution']:+.2f} |")
    L += ['', '| Counting only | p, shuffle test |', '|---|---|']
    for r in g('other_blocks_by_kind_of_use', 1960)['runs']:
        L.append(f"| {r['kinds']} | {pv(r['p_perm'])} |")
    lo = g('other_blocks_leave_one_parcel_out', 1960)
    L += ['', '## How much hangs on single parcels (records up to 1960)', '',
          f"Leaving each of the {lo['parcels']} parcels out in turn, p runs from {pv(lo['min'])} to {pv(lo['max'])} "
          f"(median {pv(lo['median'])}); {lo['below_0_05']} of the {lo['parcels']} runs are below 0.05.", '',
          '| Leaving out | p |', '|---|---|']
    for x in lo['lowest'] + lo['highest'][::-1]:
        L.append(f"| {x['address']} Greenmount | {pv(x['p_perm'])} |")
    mt = res['multi_tenant_parcels']
    L += ['', f"Multi-tenant centres ({MULTI_TENANT} or more kinds of use today): "
          + (', '.join(f"{m['address']} Greenmount ({m['kinds_of_use_today']} kinds)" for m in mt) or 'none') + '. '
          f"Without them: p = {pv(g('other_blocks_without_multi_tenant', 1960)['p_perm'])} "
          f"on {g('other_blocks_without_multi_tenant', 1960)['parcels']} parcels.", '',
          '## All runs', '',
          '| Data | Cut-off | Parcels (with history) | p, shuffle test | Fit on the same data (AUC), without and with history | p with a control for how much is on record |',
          '|---|---|---|---|---|---|']
    for key, label in (('other_blocks', 'Other Greenmount blocks: the test'),
                       ('other_blocks_without_low_confidence', 'Other blocks, low-confidence codes of today\'s use left out'),
                       ('other_blocks_stated_uses_only', 'Other blocks, history coded from linked businesses and directory lines only'),
                       ('other_blocks_without_multi_tenant', 'Other blocks, multi-tenant centres left out'),
                       ('other_blocks_before_leak_fix', 'Other blocks before the leak fix (as first reported; not valid)'),
                       ('frontage', 'This frontage, all sources (exploratory: the model was chosen here)'),
                       ('frontage_sponsor_only', 'This frontage, sponsor records only')):
        for a in res[key]:
            L.append(f"| {label} | {a['cut']} | {a['parcels']} ({a['parcels_with_history']}) | {pv(a['p_perm'])} | "
                     f"{a['auc_base']:.3f} to {a['auc_history']:.3f} | {pv(a['p_lr_with_depth_control'])} |")
    L += ['', '## Held-out checks', '',
          '| Check | Cut-off | Forecast error (log loss), without and with history | Ranking (AUC), without and with history | Gain per row, with a 95% interval |',
          '|---|---|---|---|---|']
    for key, ikey, label in (('transfer_frontage_sponsor_to_other', 'transfer_interval_sponsor_to_other', 'Fitted on this frontage (sponsor records), applied to the other blocks: the rule\'s second condition'),
                             ('transfer_frontage_all_to_other', 'transfer_interval_all_to_other', 'Fitted on this frontage (all sources), applied to the other blocks')):
        for a in res[key]:
            ci = g(ikey, a['cut'])
            L.append(f"| {label} | {a['cut']} | {a['logloss_base']:.4f} to {a['logloss_history']:.4f} | {a['auc_base']:.3f} to {a['auc_history']:.3f} | "
                     f"{ci['gain_per_row']:+.4f} ({ci['gain_ci95'][0]:+.4f} to {ci['gain_ci95'][1]:+.4f})"
                     f"{'' if ci['distinguishable_from_zero'] else ': not distinguishable from zero'} |")
    for a in res['frontage_leave_one_side_out']:
        L.append(f"| This frontage, one block side left out at a time | {a['cut']} | {a['logloss_base']:.4f} to {a['logloss_history']:.4f} | {a['auc_base']:.3f} to {a['auc_history']:.3f} | |")
    sc = g('selection_empty_against_in_use', 1960)
    L += ['', '## Who the test covers', '',
          f"The test can only use storefronts with a business today. On this frontage that is {sc['in_use']} storefronts; "
          f"the plan is for the {sc['empty']} empty ones. Before 1960 the empty storefronts have "
          f"{sc['decades_on_record']['empty']} use-decades on record on average and the ones in use "
          f"{sc['decades_on_record']['in_use']} (two-sided shuffle p = {pv(sc['decades_on_record']['p_two_sided'])}); "
          f"the mix of uses on record differs by {sc['mix_of_uses_on_record']['distance']:.2f} on a scale from 0 (the same) to 2 "
          f"(p = {pv(sc['mix_of_uses_on_record']['p'])}). The test says nothing direct about the empty storefronts.", '']
    return '\n'.join(L)


def main():
    fr, frs, ob = frontage(), frontage(sponsor_only=True), other_blocks()
    ob_hi = other_blocks(include_low=False)
    ob_leak = other_blocks(keep_nr_summary=True)   # as first run and reported (p = 0.023), kept for the record
    ob_stated = other_blocks(stated_only=True)
    multi = sorted(p for p in ob['parcels'] if len(ob['now'][p]) >= MULTI_TENANT)
    ob_single = other_blocks(without=set(multi))
    res = dict(
        written_by='team/validation/backtest.py', plan='team/validation/PLAN_backtest_v2.md',
        categories=CATS, permutations=N_PERM, seed=SEED,
        frontage=[analyse(fr, c) for c in CUTS],
        frontage_sponsor_only=[analyse(frs, c) for c in CUTS],
        other_blocks=[analyse(ob, c) for c in CUTS],
        other_blocks_without_low_confidence=[analyse(ob_hi, c) for c in CUTS],
        other_blocks_before_leak_fix=[analyse(ob_leak, c) for c in CUTS],
        other_blocks_stated_uses_only=[analyse(ob_stated, c) for c in CUTS],
        other_blocks_without_multi_tenant=[analyse(ob_single, c) for c in CUTS],
        multi_tenant_parcels=[dict(property_id=p, address=ob['address'][p], kinds_of_use_today=len(ob['now'][p])) for p in multi],
        other_blocks_by_kind_of_use=[dict(cut=c, runs=category_runs(ob, c)) for c in CUTS],
        other_blocks_leave_one_parcel_out=[leave_one_parcel_out(ob, c) for c in CUTS],
        transfer_interval_sponsor_to_other=[transfer_interval(frs, ob, c) for c in CUTS],
        transfer_interval_all_to_other=[transfer_interval(fr, ob, c) for c in CUTS],
        selection_empty_against_in_use=[selection_check(c) for c in CUTS],
        frontage_parcels_tested=len(fr['parcels']), frontage_parcels_not_tested=fr['n_unoccupied'],
        transfer_frontage_sponsor_to_other=[transfer(frs, ob, c) for c in CUTS],
        transfer_frontage_all_to_other=[transfer(fr, ob, c) for c in CUTS],
        frontage_leave_one_side_out=[leave_one_side_out(fr, c) for c in CUTS],
        similarity=similarity({'frontage': fr['parcels'], 'other_blocks': ob['parcels']}),
    )
    o, t = res['other_blocks'][0], res['transfer_frontage_sponsor_to_other'][0]
    res['decision'] = dict(
        rule='other blocks, 1960: permutation p < 0.05 and lower held-out log loss with history (transfer test)',
        p_perm=o['p_perm'], transfer_better=t['better'],
        passes=bool(o['p_perm'] < 0.05 and t['better']),
        p_perm_before_leak_fix=res['other_blocks_before_leak_fix'][0]['p_perm'],
        if_it_fails='the money layer shows rent and revenue ranges from comparable listings only, labelled as planning '
                    'figures, and nothing that ranks uses or plans by history and money together (PLAN_backtest_v2.md)')
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    stem = 'backtest_v2_recoded' if OUTCOMES else 'backtest_v2'
    if OUTCOMES:
        res['outcomes_file'] = os.path.basename(OUTCOMES)
    with open(os.path.join(HERE, 'out', stem + '.json'), 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1)
        fh.write('\n')
    with open(os.path.join(HERE, 'out', stem + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(report(res))
    for k in ('frontage', 'frontage_sponsor_only', 'other_blocks', 'other_blocks_without_low_confidence',
              'other_blocks_stated_uses_only', 'other_blocks_without_multi_tenant', 'other_blocks_before_leak_fix'):
        for a in res[k]:
            print(f"{k:38s} cut {a['cut']}: parcels {a['parcels']} (with history {a['parcels_with_history']}), "
                  f"beta {a['beta']}, p_perm {a['p_perm']}, p_lr {a['p_lr']}, AUC {a['auc_base']} -> {a['auc_history']}, "
                  f"depth-controlled p {a['p_lr_with_depth_control']}")
    for k in ('transfer_frontage_sponsor_to_other', 'transfer_frontage_all_to_other', 'frontage_leave_one_side_out'):
        for a in res[k]:
            print(f"{k:38s} cut {a['cut']}: log loss {a['logloss_base']} -> {a['logloss_history']}, "
                  f"AUC {a['auc_base']} -> {a['auc_history']}, better {a['better']}")
    for x in res['other_blocks_leave_one_parcel_out']:
        print(f"leave one parcel out, cut {x['cut']}: p {x['min']} to {x['max']} (all parcels {x['p_all_parcels']}); crosses 0.05 without:",
              [(y['address'], y['p_perm']) for y in x['crosses_0_05']][:8])
    for x in res['transfer_interval_sponsor_to_other']:
        print(f"transfer gain, cut {x['cut']}: {x['gain_per_row']} per row, 95% {x['gain_ci95']}; AUC change {x['auc_change']} {x['auc_change_ci95']}")
    for x in res['other_blocks_by_kind_of_use']:
        print('by kind of use, cut', x['cut'], [(r['kinds'][:28], r['p_perm']) for r in x['runs']])
    print('multi-tenant parcels:', res['multi_tenant_parcels'])
    print('selection:', res['selection_empty_against_in_use'][0])
    print('decision:', res['decision'])


if __name__ == '__main__':
    main()
