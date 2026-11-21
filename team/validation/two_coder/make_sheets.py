"""Two-coder check: write the blank coding sheets.

Run once, before anyone starts coding:   python3 team/validation/two_coder/make_sheets.py

Two things were coded with AI assistance and never checked by a person (sponsor's review, 17 November 2026):
  1. the use today of the 52 Greenmount parcels in the back-test (team/validation/outcomes_other_greenmount_2026-10.csv);
  2. the use the extractor's keyword rules gave each history record (team/extractor/out/evidence.csv).
This script writes, for each, one blank sheet per coder. Two team members fill them in without seeing each other's
sheet, the AI-assisted codes or the explorer; score_agreement.py then reports how often they agree with each other
and with the codes in the repo.

The history sample is fixed by SEED and by the rule in draw_history(), so anyone can rerun it and get the same 200
records. A sheet that already has a code typed into it is never overwritten.
Standard library only.
"""
import collections
import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SEED = 'two-coder gold set, 2026-11-21'
N_HISTORY = 200
CATEGORIES = ['food & drink', 'retail goods', 'personal services', 'automotive', 'entertainment & assembly',
              'institutional & religious', 'office', 'production & light industry', 'residential', 'vacant']
NO_USE = 'no use stated'            # the text does not say what the building was used for
OUTCOME_FIELDS = ['property_id', 'address', 'sponsor_status', 'read', 'uses_today', 'sure', 'note', 'coded_by', 'coded_on',
                  'saw_other_codes']
HISTORY_FIELDS = ['sample_id', 'property_id', 'address', 'year', 'source', 'source_ref', 'url', 'text',
                  'use_category', 'use_is_dated_to_this_year', 'record_is_about_this_address', 'note', 'coded_by', 'coded_on',
                  'saw_other_codes']
# what a coder is shown; every other column of a sheet starts blank, whatever the source row holds
OUTCOME_SHOWN = ['property_id', 'address', 'sponsor_status', 'read']
HISTORY_SHOWN = ['sample_id', 'property_id', 'address', 'year', 'source', 'source_ref', 'url', 'text']
csv.field_size_limit(sys.maxsize)


def rows(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def outcome_sheet():
    """One row per parcel in the back-test, with no code. The coder reads the sponsor's storefront summary for the
    parcel where the first coding read it: storefront_assessments.csv at the top of the repo, the row with the same
    property_id. The summary is not copied into the sheet."""
    summary = {r['property_id']: r for r in rows('storefront_assessments.csv')}
    out = []
    for r in rows('team', 'validation', 'outcomes_other_greenmount_2026-10.csv'):
        if r['included'] != 'yes':
            continue
        s = summary.get(r['property_id'], {})
        assert (s.get('summary') or '').strip(), 'no sponsor summary to code from: ' + r['property_id']
        out.append(dict(property_id=r['property_id'], address=r['address'], sponsor_status=s.get('status', ''),
                        read='storefront_assessments.csv, property_id ' + r['property_id'] + ', column summary'))
    return sorted(out, key=lambda r: (int(r['address'].split()[0]), r['property_id']))


def draw_history():
    """200 history records the extractor coded with a use: 100 from the sponsor's records (narrative prose, where the
    review found most of the errors) and 100 from the other sources, each a simple random draw. The two strata are
    reported separately and weighted back to the whole when a single figure is given."""
    ev = [dict(e, n=i) for i, e in enumerate(rows('team', 'extractor', 'out', 'evidence.csv'))]
    coded = [e for e in ev if e['source'] != 'current_2026' and e['kind'] != 'current' and e['use_category'] and e['year']
             and e['use_subcategory'] != 'store building (generic)']
    strata = collections.OrderedDict((('sponsor records', [e for e in coded if e['source'].startswith('sponsor')]),
                                      ('other sources', [e for e in coded if not e['source'].startswith('sponsor')])))
    rng = random.Random(SEED)
    picked = []
    for name, pool in strata.items():
        pool = sorted(pool, key=lambda e: e['n'])
        for e in rng.sample(pool, min(N_HISTORY // 2, len(pool))):
            picked.append(dict(e, stratum=name))
    rng.shuffle(picked)                     # so that a coder cannot tell the stratum from the order
    for i, e in enumerate(picked, 1):
        e['sample_id'] = f'H{i:03d}'
    return picked, {k: len(v) for k, v in strata.items()}, len(coded)


def write(path, fields, shown, data):
    """Write a blank sheet unless a person has started on it. Only the columns in `shown` are copied from the source."""
    if os.path.exists(path):
        with open(path, encoding='utf-8-sig', newline='') as fh:
            started = any((r.get('coded_by') or r.get('uses_today') or r.get('use_category') or '').strip() for r in csv.DictReader(fh))
        if started:
            print('kept (already started):', os.path.relpath(path, REPO))
            return
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator='\n', extrasaction='ignore')
        w.writeheader()
        for r in data:
            w.writerow({k: (r.get(k, '') if k in shown else '') for k in fields})
    print('wrote', os.path.relpath(path, REPO), len(data), 'rows')


def main():
    oc = outcome_sheet()
    hist, pools, n_coded = draw_history()
    for coder in ('A', 'B'):
        write(os.path.join(HERE, f'outcomes_coder_{coder}.csv'), OUTCOME_FIELDS, OUTCOME_SHOWN, oc)
        write(os.path.join(HERE, f'history_coder_{coder}.csv'), HISTORY_FIELDS, HISTORY_SHOWN, hist)
    # the key: which evidence row each sample id is, and what the extractor coded it as. Coders do not open this file.
    with open(os.path.join(HERE, 'history_key.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(['sample_id', 'stratum', 'evidence_row', 'property_id', 'year', 'source', 'source_ref', 'extractor_use_category',
                    'extractor_use_subcategory', 'matched_keyword', 'basis'])
        for e in sorted(hist, key=lambda e: e['sample_id']):
            w.writerow([e['sample_id'], e['stratum'], e['n'] + 2, e['property_id'], e['year'], e['source'], e['source_ref'],
                        e['use_category'], e['use_subcategory'], e['matched_keyword'], e['basis']])
    with open(os.path.join(HERE, 'sample.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(dict(seed=SEED, outcomes=len(oc), history=len(hist), history_coded_rows=n_coded, history_pools=pools,
                       rule='history: 100 drawn at random from the coded sponsor records and 100 from the coded records of '
                            'the other sources, with random.Random(seed).sample over each pool in file order; outcomes: '
                            'every parcel in the back-test'), fh, indent=1)
        fh.write('\n')
    print('history sample:', len(hist), 'of', n_coded, 'coded history records;', pools)


if __name__ == '__main__':
    main()
