"""Score the extractor against the blind reference timelines.

Run after the four timelines are filled in:  python score_blind.py

The measures are the ones team/extractor/extract.py reports for the week-1 references (validate()):
  recall                   a reference use is found if the extractor has a record at that parcel, in that
                           category, within the reference years (one year of tolerance)
  recall where covered     the same, counted only over reference uses for which the extractor has any record
                           at that parcel in those years
  category agreement       of the extractor's coded records that fall inside a reference span, the share whose
                           category matches a reference use covering that year
Each is given for all sources and for the sources other than the sponsor's records.
The script refuses to score until every drawn parcel has rows and every row says it was built blind.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOL = 1


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))


def check(refs, sample):
    """Reasons the file is not ready to score (an empty list means it is)."""
    out = []
    have = {r['property_id'] for r in refs}
    for d in sample['drawn']:
        if d['property_id'] not in have:
            out.append(f"no rows yet for {d['address']} (property_id {d['property_id']})")
    extra = have - {d['property_id'] for d in sample['drawn']}
    if extra:
        out.append('rows for parcels that were not drawn: ' + ', '.join(sorted(extra)))
    for i, r in enumerate(refs, 2):
        if (r.get('saw_extractor_output') or '').strip().lower() != 'no':
            out.append(f'line {i}: saw_extractor_output must be "no" for a blind timeline')
        if not (r.get('built_by') or '').strip():
            out.append(f'line {i}: built_by is empty')
        try:
            if int(r['start_year']) > int(r['end_year']):
                out.append(f'line {i}: start_year is after end_year')
        except (KeyError, ValueError):
            out.append(f'line {i}: start_year and end_year must be years')
    return out


def coded_rows(evidence, props):
    """The extractor records that validate() scores: dated, coded with a use, not the 2026 tenant check."""
    return [e for e in evidence if e['property_id'] in props and e['use_category'] and e['year']
            and e['use_category'] != 'vacant' and e['kind'] != 'current'
            and e['use_subcategory'] != 'store building (generic)']


def score(refs, evidence):
    refs = [dict(r, start=int(r['start_year']), end=int(r['end_year']), category=(r['use_category'] or '').strip()) for r in refs]
    refs = [r for r in refs if r['category'] and r['category'] != 'vacant']
    coded = coded_rows(evidence, {r['property_id'] for r in refs})
    inside = lambda e, r: e['property_id'] == r['property_id'] and r['start'] - TOL <= int(e['year'][:4]) <= r['end'] + TOL
    res = {}
    for label, keep in (('all sources', lambda e: True), ('sources other than sponsor records', lambda e: not e['source'].startswith('sponsor'))):
        rows = [e for e in coded if keep(e)]
        detail = [(r, any(inside(e, r) and e['use_category'] == r['category'] for e in rows), any(inside(e, r) for e in rows)) for r in refs]
        covered = [d for d in detail if d[2]]
        n_in = agree = 0
        for e in rows:
            cover = [r for r in refs if inside(e, r)]
            if cover:
                n_in += 1
                agree += any(r['category'] == e['use_category'] for r in cover)
        res[label] = dict(reference_uses=len(refs), found=sum(1 for d in detail if d[1]),
                          recall=sum(1 for d in detail if d[1]) / max(1, len(refs)),
                          covered=len(covered), recall_where_covered=sum(1 for d in covered if d[1]) / max(1, len(covered)),
                          records_scored=n_in, category_agreement=agree / max(1, n_in), detail=detail)
    return res


def report(res, refs, sample):
    pc = lambda x: f'{round(100 * x)}%'
    L = ['# Extractor against the blind reference timelines', '',
         f"Parcels: {', '.join(d['address'] for d in sample['drawn'])}. Drawn with the rule and seed in `sample.json`.",
         f"Built by: {', '.join(sorted({r['built_by'].strip() for r in refs}))}. Every row is marked as built without seeing the extractor output.", '',
         '| Records used | Reference uses | Found | Recall | Recall where a source covers the years | Extractor records scored | Category agreement |',
         '|---|---|---|---|---|---|---|']
    for label, r in res.items():
        L.append(f"| {label} | {r['reference_uses']} | {r['found']} | {pc(r['recall'])} | {pc(r['recall_where_covered'])} of {r['covered']} | {r['records_scored']} | {pc(r['category_agreement'])} |")
    L += ['', '## Reference uses the extractor did not find (all sources)', '']
    miss = [d for d in res['all sources']['detail'] if not d[1]]
    L += [f"- {r['address']}, {r['start']}-{r['end']}: {r['use']} ({r['category']}); {'the extractor has other records for these years' if cov else 'no extractor record for these years'}" for r, _, cov in miss] or ['None.']
    L += ['', 'Four parcels is a small sample: read these as a check that nothing is badly wrong, not as a precise rate.', '']
    return '\n'.join(L)


def main():
    with open(os.path.join(HERE, 'sample.json'), encoding='utf-8') as fh:
        sample = json.load(fh)
    refs = read(os.path.join(HERE, 'blind_timelines.csv'))
    problems = check(refs, sample)
    if problems:
        print('Not ready to score:')
        for p in problems[:20]:
            print(' -', p)
        return 1
    res = score(refs, read(os.path.join(REPO, 'team', 'extractor', 'out', 'evidence.csv')))
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    with open(os.path.join(HERE, 'out', 'blind_validation.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(report(res, refs, sample))
    for label, r in res.items():
        print(label, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != 'detail'})
    return 0


if __name__ == '__main__':
    sys.exit(main())
