#!/usr/bin/env python3
"""Back-test v2: does a building's documented past add information about its use today?

    python3 team/validation/backtest.py        # writes team/validation/out/backtest_v2.json

The plan, written before the test was run on the other Greenmount blocks, is PLAN_backtest_v2.md.
Standard library only.

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
        if e['source'].startswith('sponsor') and e['text'].startswith('Built ca') and 'B-5229' in e['text']:
            continue   # NR summary rows dated to the build year (see build_explorer.py)
        if sponsor_only and not e['source'].startswith('sponsor'):
            continue
        if e['use_category'] in CATS and e['use_subcategory'] != GENERIC:
            rows.append((pid, e['use_category'], int(e['year'])))
    parcels = sorted(p for p in props if now.get(p))
    group = {p: props[p]['block_side_id'] for p in parcels}
    return dict(parcels=parcels, now={p: now[p] for p in parcels}, records=rows, group=group,
                n_unoccupied=len(props) - len(parcels))


def other_blocks(include_low=True):
    """Greenmount parcels outside the frontage, coded blind (outcomes_other_greenmount_2026-10.csv)."""
    oc = [r for r in rd('team', 'validation', 'outcomes_other_greenmount_2026-10.csv') if r['included'] == 'yes']
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
        b = biz.get(r['id'], [])
        if not (b or r['source'] in A_SOURCES or r['category'] in A_CATEGORIES):
            continue
        y = r['occurred_at'][:4]
        if not y.isdigit():
            continue
        c, s, _ = classify(f"{r['summary']} {' '.join(b)}")
        if s == GENERIC and b:
            s = 'named store'
        if c in CATS and s != GENERIC:
            rows.append((r['property_id'], c, int(y)))
    return dict(parcels=parcels, now=now, records=rows, group=group)


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
    return dict(cut=cut, parcels=len(data['parcels']), parcels_with_history=with_hist, rows=len(rows),
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


def main():
    fr, frs, ob = frontage(), frontage(sponsor_only=True), other_blocks()
    ob_hi = other_blocks(include_low=False)
    res = dict(
        written_by='team/validation/backtest.py', plan='team/validation/PLAN_backtest_v2.md',
        categories=CATS, permutations=N_PERM, seed=SEED,
        frontage=[analyse(fr, c) for c in CUTS],
        frontage_sponsor_only=[analyse(frs, c) for c in CUTS],
        other_blocks=[analyse(ob, c) for c in CUTS],
        other_blocks_without_low_confidence=[analyse(ob_hi, c) for c in CUTS],
        transfer_frontage_sponsor_to_other=[transfer(frs, ob, c) for c in CUTS],
        transfer_frontage_all_to_other=[transfer(fr, ob, c) for c in CUTS],
        frontage_leave_one_side_out=[leave_one_side_out(fr, c) for c in CUTS],
        similarity=similarity({'frontage': fr['parcels'], 'other_blocks': ob['parcels']}),
    )
    o, t = res['other_blocks'][0], res['transfer_frontage_sponsor_to_other'][0]
    res['decision'] = dict(
        rule='other blocks, 1960: permutation p < 0.05 and lower held-out log loss with history (transfer test)',
        p_perm=o['p_perm'], transfer_better=t['better'],
        passes=bool(o['p_perm'] < 0.05 and t['better']))
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    with open(os.path.join(HERE, 'out', 'backtest_v2.json'), 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1)
    for k in ('frontage', 'frontage_sponsor_only', 'other_blocks', 'other_blocks_without_low_confidence'):
        for a in res[k]:
            print(f"{k:38s} cut {a['cut']}: parcels {a['parcels']} (with history {a['parcels_with_history']}), "
                  f"beta {a['beta']}, p_perm {a['p_perm']}, p_lr {a['p_lr']}, AUC {a['auc_base']} -> {a['auc_history']}, "
                  f"depth-controlled p {a['p_lr_with_depth_control']}")
    for k in ('transfer_frontage_sponsor_to_other', 'transfer_frontage_all_to_other', 'frontage_leave_one_side_out'):
        for a in res[k]:
            print(f"{k:38s} cut {a['cut']}: log loss {a['logloss_base']} -> {a['logloss_history']}, "
                  f"AUC {a['auc_base']} -> {a['auc_history']}, better {a['better']}")
    print('decision:', res['decision'])


if __name__ == '__main__':
    main()
