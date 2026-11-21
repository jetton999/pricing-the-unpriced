"""Two-coder check: score the filled sheets.

Run when both coders have finished:   python3 team/validation/two_coder/score_agreement.py

Writes out/agreement.md (the figures to report), out/disagreements.csv (every row the two coders, or the coders and
the repo's code, do not agree on, for a third person to settle) and out/outcomes_agreed.csv (the back-test's outcome
file with the two coders' codes wherever they agree). It refuses to score a sheet that is incomplete, unsigned, or
filled in by a coder who saw other codes.

Measures
  agreement        the share of items on which the two coders give the same code
  kappa            Cohen's kappa: agreement beyond what two coders with these habits would reach by chance
                   (0 = chance, 1 = perfect)
  against the repo of the items where the two coders agree, the share where the repo's AI-assisted code says the same
  precision        per kind of use, of the records the extractor coded as that kind, the share both coders also
                   coded as that kind
Standard library only.
"""
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from make_sheets import CATEGORIES, NO_USE, rows   # noqa: E402

STOREFRONT = CATEGORIES[:8]            # the eight kinds of use the back-test scores
YES = {'yes', 'y', '1', 'true'}
csv.field_size_limit(sys.maxsize)


def sheet(name):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def norm(code):
    return ' '.join((code or '').strip().lower().replace(' and ', ' & ').split())


def uses(cell):
    """The set of kinds of use in a cell such as "food & drink ; retail goods"."""
    return {norm(x) for x in (cell or '').replace(',', ';').split(';') if norm(x)}


def problems(rows_, key, code, allowed, label, many=False):
    """Reasons a sheet is not ready to score (an empty list means it is)."""
    out = []
    if rows_ is None:
        return [f'{label}: the sheet is missing; run make_sheets.py']
    who = {(r.get('coded_by') or '').strip() for r in rows_}
    if '' in who:
        out.append(f'{label}: coded_by is empty on some rows')
    if len(who - {''}) > 1:
        out.append(f'{label}: more than one coder ({", ".join(sorted(who - {""}))}); one person fills one sheet')
    for r in rows_:
        got = uses(r[code]) if many else {norm(r[code])}
        if got == {''} or not got:
            out.append(f'{label}: {r[key]} has no code')
        elif got - allowed:
            out.append(f'{label}: {r[key]} has a code that is not on the list: {", ".join(sorted(got - allowed))}')
        if norm(r.get('saw_other_codes')) != 'no':
            out.append(f'{label}: {r[key]}: saw_other_codes must be "no" (the other sheet, the repo\'s codes and the explorer were not looked at)')
    return out[:12]


def kappa(pairs):
    """Cohen's kappa for a list of (code of A, code of B)."""
    n = len(pairs)
    if not n:
        return None
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def pct(x):
    return 'n/a' if x is None else f'{100 * x:.0f}%'


def score_outcomes(a, b):
    """Use today on the 52 parcels. Each parcel and kind of use is one yes-or-no item, as in the back-test."""
    repo = {r['property_id']: r for r in rows('team', 'validation', 'outcomes_other_greenmount_2026-10.csv') if r['included'] == 'yes'}
    A, B = {r['property_id']: r for r in a}, {r['property_id']: r for r in b}
    ids = [i for i in repo if i in A and i in B]
    pairs, agreed, vs_repo, dis = [], 0, [], []
    for i in ids:
        ua, ub, ur = uses(A[i]['uses_today']) & set(STOREFRONT), uses(B[i]['uses_today']) & set(STOREFRONT), uses(repo[i]['use_today']) & set(STOREFRONT)
        for c in STOREFRONT:
            pairs.append((c in ua, c in ub))
            if (c in ua) == (c in ub):
                vs_repo.append((c in ua) == (c in ur))
        if ua == ub:
            agreed += 1
        if ua != ub or ua != ur:
            dis.append(dict(task='use today', item=repo[i]['address'], coder_a=' ; '.join(sorted(ua)) or 'none of the eight',
                            coder_b=' ; '.join(sorted(ub)) or 'none of the eight', repo=' ; '.join(sorted(ur)) or 'none of the eight',
                            what='the coders differ' if ua != ub else 'the coders agree and the repo differs', settled_as=''))
    agreed_rows = []
    for i in repo:
        r = dict(repo[i])
        if i in A and i in B and uses(A[i]['uses_today']) == uses(B[i]['uses_today']):
            r['use_today'] = ' ; '.join(sorted(uses(A[i]['uses_today'])))
            r['coding_confidence'] = 'high' if norm(A[i].get('sure')) in YES and norm(B[i].get('sure')) in YES else 'low'
            r['coded_by'] = f"two coders agree ({A[i]['coded_by'].strip()}, {B[i]['coded_by'].strip()})"
        else:
            r['coded_by'] = 'the two coders differ: to be settled by a third person; the AI-assisted code is kept until then'
        agreed_rows.append(r)
    return dict(parcels=len(ids), parcels_same=agreed, items=len(pairs), agreement=sum(1 for x, y in pairs if x == y) / max(1, len(pairs)),
                kappa=kappa(pairs), items_agreed=len(vs_repo), repo_same=sum(vs_repo) / max(1, len(vs_repo)),
                repo_differs=sum(1 for d in dis if d['what'].startswith('the coders agree'))), dis, agreed_rows


def score_history(a, b):
    """The kind of use of 200 history records, and whether the year and the address hold."""
    key = {r['sample_id']: r for r in sheet('history_key.csv')}
    A, B = {r['sample_id']: r for r in a}, {r['sample_id']: r for r in b}
    ids = [i for i in key if i in A and i in B]
    res, dis = collections.OrderedDict(), []
    for stratum in ['sponsor records', 'other sources']:
        sel = [i for i in ids if key[i]['stratum'] == stratum]
        pairs = [(norm(A[i]['use_category']), norm(B[i]['use_category'])) for i in sel]
        both = [i for i in sel if norm(A[i]['use_category']) == norm(B[i]['use_category'])]
        same = [i for i in both if norm(A[i]['use_category']) == norm(key[i]['extractor_use_category'])]
        yr = [i for i in both if norm(A[i]['use_is_dated_to_this_year']) in YES and norm(B[i]['use_is_dated_to_this_year']) in YES]
        ad = [i for i in both if norm(A[i]['record_is_about_this_address']) in YES and norm(B[i]['record_is_about_this_address']) in YES]
        by = collections.OrderedDict()
        for c in CATEGORIES:
            coded = [i for i in sel if norm(key[i]['extractor_use_category']) == c]
            if coded:
                by[c] = (sum(1 for i in coded if norm(A[i]['use_category']) == c and norm(B[i]['use_category']) == c), len(coded))
        res[stratum] = dict(n=len(sel), agreement=len(both) / max(1, len(sel)), kappa=kappa(pairs), both=len(both),
                            extractor_same=len(same) / max(1, len(both)), year_ok=len(yr) / max(1, len(both)),
                            address_ok=len(ad) / max(1, len(both)), by=by)
        for i in sel:
            ca, cb, cx = norm(A[i]['use_category']), norm(B[i]['use_category']), norm(key[i]['extractor_use_category'])
            if ca != cb or ca != cx:
                dis.append(dict(task='history record', item=f"{i} (evidence.csv row {key[i]['evidence_row']})", coder_a=ca, coder_b=cb, repo=cx,
                                what='the coders differ' if ca != cb else 'the coders agree and the extractor differs', settled_as=''))
    return res, dis


def report(o, h, sample):
    L = ['# Two-coder check: agreement', '',
         'Written by `score_agreement.py` from the two filled sheets of each task. Do not edit by hand.', '']
    if o:
        L += ['## Use today on the other blocks', '',
              f"{o['parcels']} parcels, each coded by two people who did not see each other's sheet, the AI-assisted codes or the explorer. "
              'As in the back-test, each parcel and kind of use is one yes-or-no item.', '',
              '| | |', '|---|---|',
              f"| Parcels where the two coders give the same set of uses | {o['parcels_same']} of {o['parcels']} |",
              f"| Items (parcel and kind of use) where they agree | {pct(o['agreement'])} of {o['items']} |",
              f"| Cohen's kappa | {o['kappa']:.2f} |",
              f"| Of the items where they agree, the AI-assisted code in the repo says the same | {pct(o['repo_same'])} of {o['items_agreed']} |",
              f"| Parcels where the coders agree and the repo differs | {o['repo_differs']} |", '',
              'To rerun the back-test on the agreed codes (the files of record are left alone):', '',
              '```bash', 'PTU_OUTCOMES=team/validation/two_coder/out/outcomes_agreed.csv python3 team/validation/backtest.py',
              '```', '']
    if h:
        L += ['## Kind of use of history records', '',
              f"{sum(v['n'] for v in h.values())} records the extractor coded with a use, drawn as `sample.json` says "
              f"({sample['history_pools']['sponsor records']} coded sponsor records and {sample['history_pools']['other sources']} from the other sources in the pool).", '',
              '| Records | Coded | Coders agree | Kappa | Of those, the extractor says the same | Of those, the use is dated to that year | Of those, the record is about that address |',
              '|---|---|---|---|---|---|---|']
        for name, v in h.items():
            L.append(f"| {name} | {v['n']} | {pct(v['agreement'])} | {v['kappa']:.2f} | {pct(v['extractor_same'])} of {v['both']} | {pct(v['year_ok'])} | {pct(v['address_ok'])} |")
        w = sample['history_pools']
        tot = sum(w.values())
        est = sum(h[k]['extractor_same'] * w[k] for k in h) / tot
        L += ['', f"Weighted back to all {tot:,} coded history records, the extractor's kind of use matches the two coders on about {pct(est)}.", '',
              '### Precision by kind of use', '',
              'Of the records the extractor coded as each kind, the share both coders also coded as that kind.', '',
              '| Kind of use | Sponsor records | Other sources |', '|---|---|---|']
        cats = [c for c in CATEGORIES if any(c in v['by'] for v in h.values())]
        cell = lambda v, c: f"{v['by'][c][0]} of {v['by'][c][1]}" if c in v['by'] else ''
        L += [f"| {c} | {cell(h['sponsor records'], c)} | {cell(h['other sources'], c)} |" for c in cats]
        L.append('')
    L += ['Rows the coders, or the coders and the repo, do not agree on are in `disagreements.csv`, for a third person to settle.', '']
    return '\n'.join(L)


def main():
    import json
    with open(os.path.join(HERE, 'sample.json'), encoding='utf-8') as fh:
        sample = json.load(fh)
    oa, ob, ha, hb = (sheet(f'{t}_coder_{c}.csv') for t in ('outcomes', 'history') for c in ('A', 'B'))
    hist_allowed = set(CATEGORIES) | {NO_USE}
    todo = {'use today': problems(oa, 'address', 'uses_today', set(CATEGORIES) | {'none'}, 'outcomes_coder_A.csv', many=True)
            + problems(ob, 'address', 'uses_today', set(CATEGORIES) | {'none'}, 'outcomes_coder_B.csv', many=True),
            'history records': problems(ha, 'sample_id', 'use_category', hist_allowed, 'history_coder_A.csv')
            + problems(hb, 'sample_id', 'use_category', hist_allowed, 'history_coder_B.csv')}
    if not todo['use today'] and (oa[0]['coded_by'].strip() == ob[0]['coded_by'].strip()):
        todo['use today'] = ['the two outcome sheets carry the same coded_by: two different people are needed']
    if not todo['history records'] and (ha[0]['coded_by'].strip() == hb[0]['coded_by'].strip()):
        todo['history records'] = ['the two history sheets carry the same coded_by: two different people are needed']
    for task, ps in todo.items():
        if ps:
            print(f'Not ready to score ({task}):')
            for p in ps:
                print(' -', p)
    if all(todo.values()):
        return 1
    o = dis_o = agreed = h = None
    dis = []
    if not todo['use today']:
        o, dis_o, agreed = score_outcomes(oa, ob)
        dis += dis_o
    if not todo['history records']:
        h, dis_h = score_history(ha, hb)
        dis += dis_h
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    with open(os.path.join(HERE, 'out', 'agreement.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(report(o, h, sample))
    with open(os.path.join(HERE, 'out', 'disagreements.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['task', 'item', 'coder_a', 'coder_b', 'repo', 'what', 'settled_as'], lineterminator='\n')
        w.writeheader()
        w.writerows(dis)
    if agreed:
        with open(os.path.join(HERE, 'out', 'outcomes_agreed.csv'), 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(agreed[0].keys()), lineterminator='\n')
            w.writeheader()
            w.writerows(agreed)
    print('wrote out/agreement.md;', len(dis), 'rows to settle')
    return 0


if __name__ == '__main__':
    sys.exit(main())
