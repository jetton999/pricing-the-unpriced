#!/usr/bin/env python3
"""York Road -> Greenmount Avenue street-number crosswalk for the 2900-3299 frontage.

The stretch of York Road north of North Avenue was renamed Greenmount Avenue and renumbered;
the new numbers reach these blocks in the Polk directories between 1912 and 1914.
Method: the same person or firm listed at an old York Road number (Polk 1901-1913) and at a
new Greenmount number (Polk 1914-1915) gives a matched pair. Explicit statements in the
sponsor's curated records ("old 1102 York Rd") are added as anchors. Old numbers between two
anchors on the same side are interpolated. Standard library only.

Sanborn sheets that print the old number beside the new one (1915, 1928) are the strongest
anchors, and one hand-checked anchor is listed in MANUAL with its reasoning.

    python3 team/extractor/crosswalk.py        # from the repo root; run before extract.py

Inputs (team/evidence/): polk_york_1901_1913.tsv, crosswalk_raw.json (1909-1915 lines),
        polk_frontage_1912_1923.tsv, sanborn_frontage.csv; and the sponsor's
        property_incidents.csv and properties.csv at the repo root.
Output (team/evidence/): york_crosswalk.csv, york_crosswalk_pairs.csv
"""
import csv, json, re, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get('REPO') or os.path.abspath(os.path.join(HERE, '..', '..'))
EVD = os.environ.get('EVIDENCE') or os.path.join(REPO, 'team', 'evidence')
OUT = EVD

OCC = re.compile(r'\b(saloon|grocer\w*|gro\b|confr|confectr|livery|laund\w*|shoes?|shoemkr|plumber|tinner|barber|dairy|coal|feed|florist|jeweler|tailor|dry ?g\w*|hardware|stoves|photo\w*|bottler|upholst\w*|uphlstr|pool|dentist|real est\w*|fish|wagon|paints|notions|furn\w*)', re.I)


def namekey(text):
    t = re.sub(r"[^A-Za-z&' ]", ' ', text).split()
    if len(t) < 2:
        return None
    s = t[0].lower()
    if len(s) < 3 or s in ('mrs', 'the', 'and', 'york', 'road', 'waverly', 'propr', 'bldg'):
        return None
    return s[:6], t[1][0].lower()


def occ(text):
    m = OCC.search(text)
    return m.group(1).lower()[:4] if m else ''


old_rows = [(int(r['year']), int(r['old_york_number']), r['text'])
            for r in csv.DictReader(open(os.path.join(EVD, 'polk_york_1901_1913.tsv'), encoding='utf-8'), delimiter='\t')]
raw = json.load(open(os.path.join(EVD, 'crosswalk_raw.json')))
new_rows = []
for y in ('1914', '1915'):
    for sur, pre, n, mk in raw[y]:
        p = pre.strip()
        if p.split(' ')[0:1] == [sur] or re.match(r'^[A-Z][a-z]+ [A-Z]', p):
            new_rows.append((int(y), int(n), p))
for r in csv.DictReader(open(os.path.join(EVD, 'polk_frontage_1912_1923.tsv'), encoding='utf-8'), delimiter='\t'):
    if r['year'] in ('1914', '1915', '1917') and re.match(r'^[A-Z][a-z]+ [A-Z]', r['text']):
        new_rows.append((int(r['year']), int(r['address']), r['text']))

pairs = collections.defaultdict(list)
for y1, o, t1 in old_rows:
    if y1 < 1908 or re.search(r'Bldg|Building|Assn|Hall', t1):
        continue   # earlier listings mix in people who moved before the renumbering
    k1 = namekey(t1)
    if not k1:
        continue
    for y2, n, t2 in new_rows:
        if namekey(t2) != k1 or not (2900 <= n <= 3299):
            continue
        o1, o2 = occ(t1), occ(t2)
        if o1 and o2 and o1 != o2:
            continue
        if (o % 2) != (n % 2):
            continue   # the renumbering kept each side's parity
        pairs[(o, n)].append((y1, f'{y1} "{t1.strip()[:38]}" -> {y2} "{t2.strip()[:38]}"'))

# sponsor anchors
props = {r['id']: r for r in csv.DictReader(open(os.path.join(REPO, 'properties.csv'), encoding='utf-8-sig'))}
sponsor = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(REPO, 'property_incidents.csv'), encoding='utf-8-sig')):
    for m in re.finditer(r'(?:old|formerly|former)\s*(?:No\.?|number|#)?\s*(\d{3,4})\s*York\s*R(?:oa)?d', r['summary'], re.I):
        if not (900 <= int(m.group(1)) <= 1150):
            continue
        a = props.get(r['property_id'], {}).get('address', '')
        mm = re.match(r'(\d{4}) Greenmount', a)
        if mm and 2900 <= int(mm.group(1)) <= 3299 and int(m.group(1)) % 2 == int(mm.group(1)) % 2:
            sponsor[(int(m.group(1)), int(mm.group(1)))].append('incident ' + r['id'])

with open(os.path.join(OUT, 'york_crosswalk_pairs.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['old_york_number', 'new_greenmount_number', 'kind', 'n', 'evidence'])
    for (o, n), ev in sorted(pairs.items()):
        w.writerow([o, n, 'polk name match', len(ev), ' | '.join(e for _, e in ev[:4])])
    for (o, n), ev in sorted(sponsor.items()):
        w.writerow([o, n, 'sponsor statement', len(ev), ' | '.join(ev[:4])])

# modal new number per old number; sponsor statements count double
votes = collections.defaultdict(collections.Counter)
YW = {1908: 1, 1909: 2, 1912: 3, 1913: 3}   # later listings sit closer to the renumbering
for (o, n), ev in pairs.items():
    votes[o][n] += sum(YW.get(y, 1) for y, _ in ev)
for (o, n), ev in sponsor.items():
    votes[o][n] += 2 * len(ev)
anchors = {}
for o, c in votes.items():
    n, k = c.most_common(1)[0]
    anchors[o] = (n, k, sum(c.values()))

# drop anchors that break the order on their side (a person who moved between directories)
def clean(side_anchors):
    keep = dict(side_anchors)
    changed = True
    while changed:
        changed = False
        olds = sorted(keep)
        for i, o in enumerate(olds):
            n = keep[o][0]
            prev_bad = i > 0 and keep[olds[i - 1]][0] > n
            next_bad = i < len(olds) - 1 and keep[olds[i + 1]][0] < n
            if prev_bad and next_bad or (prev_bad and keep[o][1] <= keep[olds[i - 1]][1]) or (next_bad and keep[o][1] <= keep[olds[i + 1]][1]):
                del keep[o]; changed = True; break
    return keep

# Sanborn 1915 and 1928 sheets print the old number beside the new one: the strongest anchors
SANB = {}
for r in csv.DictReader(open(os.path.join(EVD, 'sanborn_frontage.csv'), encoding='utf-8')):
    m = re.match(r'^\s*(\d{3,4})(?:\s*1/2)?\s*$', r['old_numbers'] or '')
    n = re.match(r'(\d{4})', r['street_numbers'] or '')
    if m and n and 900 <= int(m.group(1)) <= 1150 and int(m.group(1)) % 2 == int(n.group(1)) % 2:
        o, nn = int(m.group(1)), int(n.group(1))
        if '1/2' in r['old_numbers']:
            continue
        SANB.setdefault(o, (nn, f"Sanborn {r['year']} sheet {r['sheet']} prints {o} beside {r['street_numbers']}"))
for o, (n, why) in SANB.items():
    anchors[o] = (n, 100, 100)
    sponsor[(o, n)].append(why)

# hand-checked anchors with stated reasoning
MANUAL = {(1029, 3123): 'Chemical Engine Co No 4 at 1029 York Rd (Polk 1901); the 1900-01 firehouse stands at 3123 (NR inventory)'}
for (o, n), why in MANUAL.items():
    anchors[o] = (n, 3, 3)
    sponsor[(o, n)].append(why)

rows = []
for parity, side in ((0, 'W'), (1, 'E')):
    sa = {o: v for o, v in anchors.items() if o % 2 == parity}
    keep = clean(sa)
    dropped = set(sa) - set(keep)
    ks = sorted(keep)
    lo_old, hi_old = 900 + parity, 1150
    for o in range(lo_old, hi_old + 1, 2):
        if o in keep:
            n, k, tot = keep[o]
            method = 'anchor'
            conf = 'high' if tot >= 2 else 'medium'
            ev = SANB[o][1] if o in SANB else (MANUAL.get((o, n)) or f'{tot} weighted Polk name match(es)')
        else:
            below = [a for a in ks if a < o]; above = [a for a in ks if a > o]
            if below and above:
                a, b = below[-1], above[0]
                na, nb = keep[a][0], keep[b][0]
                if nb - na > 120:   # a block boundary sits between them; do not interpolate across it
                    continue
                est = na + (nb - na) * (o - a) / (b - a)
                n = int(round(est))
                if n % 2 != parity:
                    n += 1
                method = 'interpolated'
                conf = 'medium' if (b - a) <= 8 else 'low'
                ev = f'between {a}->{na} and {b}->{nb}'
            else:
                continue
        rows.append(dict(old_york_number=o, side=side, new_greenmount_number=n, method=method, confidence=conf,
                         evidence=ev + (' ; outlier listings dropped' if o in dropped else '')))
with open(os.path.join(OUT, 'york_crosswalk.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print('pairs', len(pairs), 'sponsor', len(sponsor), 'anchors', len(anchors), 'crosswalk rows', len(rows))
print(collections.Counter((r['side'], r['method']) for r in rows))

# reconcile with the week-2 report's pairs (team/extractor/reference/york_road_crosswalk.csv), when present
REF = os.path.join(HERE, 'reference', 'york_road_crosswalk.csv')
if os.path.exists(REF):
    mine = {str(r['old_york_number']): dict(r, new_greenmount_number=str(r['new_greenmount_number'])) for r in rows}
    out = []
    for k in csv.DictReader(open(REF, encoding='utf-8')):
        o, n = k['old_york_rd'], k['modern_greenmount']
        lo = o.split('-')[0]
        m = mine.get(lo)
        if not m:
            res, verdict = '', 'outside this crosswalk (old 900-1150 only)'
        elif '-' in o:
            hi = mine.get(o.split('-')[1])
            res = f"{m['new_greenmount_number']}-{hi['new_greenmount_number'] if hi else '?'}"
            verdict = 'agrees' if res == n else 'differs'
        else:
            res = m['new_greenmount_number']
            if res == n:
                verdict = 'agrees'
            elif m['evidence'].startswith('Sanborn'):
                verdict = f"differs: {m['evidence']}; the report's record needs a check against the sheet"
            else:
                verdict = 'differs'
        out.append(dict(old_york_rd=o, report_modern=n, report_kind=k['kind'], report_status=k['status'],
                        report_records=k['source_incident_ids'], report_offset_predicts=k['offset_predicts'],
                        this_crosswalk=res, method=m['method'] if m else '', evidence=m['evidence'] if m else '',
                        verdict=verdict))
    with open(os.path.join(OUT, 'york_crosswalk_reconciliation.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print('reconciled with the week-2 report:', collections.Counter(r['verdict'].split(':')[0] for r in out))
