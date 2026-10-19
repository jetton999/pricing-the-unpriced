#!/usr/bin/env python3
"""Prototype v0: merge use evidence for the 79 Greenmount frontage properties.

Inputs (same folder):
  frontage79.csv             79 frontage properties (from team/week1 focus_area_properties)
  use_records.csv            sponsor curated records classified A/B/C (team week 1)
  polk_raw.tsv               Polk city directory lines, 1912-1923 (archive.org OCR)
  permit_cards_raw.csv       BRG48-53 permit index cards, 1924-1961 (transcribed)
  current_tenants_draft_79.csv  current tenants, Oct 2026

Outputs (out/):
  evidence_v0.csv, decade_matrix_v0.csv, proven_uses_v0.csv, silence_map_v0.csv,
  hbu_screen_v0.csv, unassigned_v0.csv

Standard library only. A prototype: every row keeps its source so a person can check it.
"""
import csv, re, os, collections
import os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get('REPO') or os.path.abspath(os.path.join(HERE, '..', '..'))
def rp(*a): return os.path.join(REPO, *a)
FRONTAGE_SIDES = {'65', '67', '68', '69', '70', '71', '72'}
def load_frontage():
    rows = list(csv.DictReader(open(rp('team', 'week1', 'out', 'focus_area_properties.csv'), encoding='utf-8-sig')))
    return [r for r in rows if r['block_side_id'] in FRONTAGE_SIDES]

OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
CATS = ['food & drink', 'retail goods', 'personal services', 'automotive',
        'entertainment & assembly', 'institutional & religious',
        'production & light industry', 'office', 'residential', 'vacant']

# ---------------------------------------------------------------- properties
props = load_frontage()
for p in props:
    p['num'] = int(p['address'].split()[0])
by_num = {p['num']: p for p in props}
nums = sorted(by_num)


def assign(n, lo=None, hi=None):
    """Map a street number to a frontage property. Returns (property, method)."""
    if n in by_num:
        return by_num[n], 'exact'
    if lo is not None and hi is not None:
        inside = [m for m in nums if lo <= m <= hi and m % 2 == lo % 2]
        if inside:
            return by_num[inside[0]], 'range'
    same = [m for m in nums if m % 2 == n % 2 and m // 100 == n // 100]
    lower = [m for m in same if m < n]
    if lower and n - max(lower) <= 14:
        m = max(lower)
        return by_num[m], f'nearest-lower(+{n - m})'
    higher = [m for m in same if m > n]
    if higher and min(higher) - n <= 2:
        m = min(higher)
        return by_num[m], f'nearest-higher(-{m - n})'
    return None, 'unassigned'


# ---------------------------------------------------------------- classifier
RULES = [
    ('residential', 'private garage', r"\b(private garage|(metal|frame|brick|block|1.car|2.car) garage|garage \d+\s*(ft|'|x))"),
    ('residential', 'dwelling (stated)', r'\b(was|is|as) an? [\w\- ,]{0,40}?(dwelling|rowhouse|residence|house)\b'),
    # (category, subcategory, regex)
    ('vacant', 'demolition', r'\b(raz(e|ed|ing)|demoli\w*|wreck)\b'),
    ('entertainment & assembly', 'theatre / pictures', r'\b(mov\w*\s*pict\w*|motion pict\w*|theat(re|er)|marquee|cinema|movie)\b'),
    ('entertainment & assembly', 'recreation', r'\b(billiard|pool\b|bowling|skating|rink|miniature golf|dance hall|dancing|night ?club|ball ?park|bleacher|grandstand|carnival|bingo|amusement|pleasure club)'),
    ('entertainment & assembly', 'hall / lodge', r'\b(hall\b|lodge|council no|conclave|castle no|assembly hall|club\b)'),
    ('institutional & religious', '', r'\b(church|parochial|school|fir\S* dept|fire (dept|house|engine)|engine co|police|post office|library|mission|temple|chapel|rectory|parish)\b'),
    ('food & drink', 'bar / tavern', r'\b(saloon|tavern|near beer|cocktail|lounge|bar\b|bartndr|beer|liquor|rectifier)\b'),
    ('food & drink', 'restaurant / lunch', r'\b(lunch|restaurant|cafe|café|diner|carry.?out|eat|coffee|soda fountain|ice cream|sandwich|pizza|chicken|grill)\b'),
    ('food & drink', 'food retail', r'\b(grocer\w*|gro\b|xrocer|srocer|meats?\b|market|confr|eonfr|cohfr|confx|confectio\w*|bak(er|ery)|butter and eggs|oysters|sea food|fish\b|dairy|soft drinks|soda water|delicatessen|deli\b|produce|prod\b)'),
    ('automotive', '', r'\b(garage|auto\w*|livery|filling station|gas(oline)? station|service station|used car|tire|retread|car wash|motor)\b'),
    ('personal services', '', r'\b(barber|tailor|shoemkr|sboemkr|slioemkr|shoe ?repair|laund\w*|dressmkr|beauty|hair\w*|cleaner|dyer|photo\w*|dentist|ph[yv]s\w*|chemist|optic\w*|undertaker|funeral|dog hospital|animal hospital|veterin\w*|pressing|valet|pawn|loan office|finance co|cash)\b'),
    ('retail goods', '', r'\b(hardware|hdwe?\b|hdw\b|dry ?g(oo)?ds|shoes|boots|furn(iture|gs|s)\b|fu[mr]n?gs|turns\b|fnriigs|notions|milliner|jewel\w*|jwlr|florist|drugs?\b|druggist|cigars?|tobacco|pianos?|musical|5 ?(&|and) ?10|5c|gen\w* mdse|hat shop|clothing|apparel|men.?s (wear|furn\w*)|store\b|stores\b|shop\b|retail|sales|showroom|toy)'),
    ('production & light industry', '', r'\b(mn?fg|mnfr|manufact\w*|bottl\w*|printing|plumb\w*|plmbr|tinner|sheet metal|metalwkr|contr\w*|lumber|cabtmkr|upholst\w*|uphlstr|coal|feed\b|warehouse|factory|plant|shop for|welder|painter|plstr|pipef\w*|metalwk\w*|r[ae]+talwkr|paperhngr|carp\b)\b'),
    ('office', '', r'\b(real est\w*|bldg (assn|&|and)|building (assn|association|and loan)|loan assn|savings|sav (and|&) loan|notary|insurance|office|realty|bank|lawyer|attorney|solr)\b'),
    ('residential', '', r'\b(dwellings?|apartments?|apts?\b|rowhouses?|residence|living quarters)\b'),
]
RULES_C = [(c, s, re.compile(rx, re.I)) for c, s, rx in RULES]


def classify(text):
    t = text or ''
    for c, s, rx in RULES_C:
        m = rx.search(t)
        if m:
            return c, s, m.group(0)
    return '', '', ''


def year_from_date(s):
    m = re.search(r'(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})', s or '')
    if not m:
        m2 = re.search(r'\b(19[2-6]\d)\b', s or '')
        return int(m2.group(1)) if m2 else None
    y = int(m.group(3))
    if y < 100:
        y += 1900
    return y if 1900 <= y <= 1975 else None


ev = []        # evidence rows
unassigned = []


def add(p, method, year, source, source_ref, text, business='', evidence_kind='use'):
    c, s, kw = classify(text + ' ' + business)
    ev.append(dict(property_id=p['property_id'], address=p['address'], block_side_id=p['block_side_id'],
                   year=year, decade=(year // 10 * 10) if year else '', source=source, source_ref=source_ref,
                   address_method=method, business=business.strip(), text=text.strip()[:300],
                   use_category=c, use_subcategory=s, matched_keyword=kw, evidence_kind=evidence_kind))


# ---------------------------------------------------------------- 1 sponsor class-A records
fid = {p['property_id']: p for p in props}
for r in csv.DictReader(open(rp('team', 'week1', 'out', 'use_records.csv'), encoding='utf-8-sig')):
    if r['use_class'] != 'A' or r['property_id'] not in fid:
        continue
    y = int(r['year']) if (r['year'] or '').isdigit() else None
    add(fid[r['property_id']], 'sponsor', y, 'sponsor:' + r['source'], 'incident ' + r['incident_id'],
        r['summary'], r['businesses'])

# ---------------------------------------------------------------- 2 Polk directories 1912-1923
NOISE = re.compile(r'^(and|n Gilmor|ay \d|w North|line \d|\d+ [nsew] |North and Maryland|\(See page)', re.I)
for r in csv.DictReader(open(rp('team', 'evidence', 'polk_frontage_1912_1923.tsv'), encoding='utf-8'), delimiter='\t'):
    txt = r['text']
    if NOISE.search(txt) or len(re.sub(r'[^A-Za-z]', '', txt)) < 4:
        continue
    n = int(r['address'])
    p, method = assign(n)
    if not p:
        unassigned.append(dict(source='polk', year=r['year'], number=n, text=txt))
        continue
    kind = 'use'
    if not classify(txt)[0]:
        kind = 'business listed' if re.search(r',\s*$|\b(Co|Bros|Assn|Son|& )\b', txt) else 'listed (uncoded)'
    add(p, method, int(r['year']), 'polk_directory', f"Polk {r['year']}, line at {n} Greenmount av", txt,
        evidence_kind=kind)

# ---------------------------------------------------------------- 3 permit cards 1924-1961
for r in csv.DictReader(open(rp('team', 'evidence', 'permit_cards_1924_1961.csv'), encoding='utf-8')):
    an = r['address_normalized'] or ''
    if 'not Greenmount' in an or not an.strip():
        unassigned.append(dict(source='permit', year=r['application_date'], number=an, text=r['purpose_of_application']))
        continue
    m = re.match(r'(\d{4})', an)
    if not m:
        continue
    n = int(m.group(1))
    rg = re.search(r'range (\d{4})\s*-\s*(\d{2,4})', an)
    lo = hi = None
    if rg:
        lo = int(rg.group(1)); h = rg.group(2)
        hi = int(h) if len(h) == 4 else int(str(lo)[:4 - len(h)] + h)
    p, method = assign(n, lo, hi)
    if not p:
        unassigned.append(dict(source='permit', year=r['application_date'], number=n, text=r['purpose_of_application']))
        continue
    purpose = (r['purpose_expanded'] or r['purpose_of_application'] or '')
    y = year_from_date(r['application_date']) or year_from_date(r['permit_date'])
    add(p, method, y, 'permit_card', f"BRG48-53 image {r['image_id']} line {r['line_no']}",
        purpose + (' | occupancy ' + r['occupancy_class'] if r['occupancy_class'] else ''),
        evidence_kind='permit')

# ---------------------------------------------------------------- 4 current tenants 2026
for r in csv.DictReader(open(rp('team', 'tenants', 'current_tenants_2026-10.csv'), encoding='utf-8')):
    p = fid.get(r['property_id'])
    if not p:
        continue
    cat = (r['business_type'] or '').split(' ; ')[0]
    if r['status'] in ('vacant', 'for lease'):
        cat = 'vacant'
    ev.append(dict(property_id=p['property_id'], address=p['address'], block_side_id=p['block_side_id'],
                   year=2026, decade=2020, source='current_2026', source_ref=r['source_url'],
                   address_method='exact', business=r['tenant_name'], text=r['status'],
                   use_category=cat if r['status'] != 'unknown' else '', use_subcategory='',
                   matched_keyword='', evidence_kind='current'))

with open(f'{OUT}/evidence_v0.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(ev[0].keys()))
    w.writeheader(); w.writerows(ev)
with open(f'{OUT}/unassigned_v0.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['source', 'year', 'number', 'text'])
    w.writeheader(); w.writerows(unassigned)

# ---------------------------------------------------------------- decade matrix + proven uses
DECS = list(range(1880, 2030, 10))
mat = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for e in ev:
    if e['use_category'] and e['decade'] != '' and e['use_category'] != 'vacant':
        mat[e['property_id']][int(e['decade'])][e['use_category']] += 1

rows = []
for p in props:
    row = {'property_id': p['property_id'], 'address': p['address'], 'block_side_id': p['block_side_id']}
    for d in DECS:
        c = mat[p['property_id']].get(d)
        row[str(d)] = '; '.join(f'{k} ({v})' for k, v in c.most_common()) if c else ''
    rows.append(row)
with open(f'{OUT}/decade_matrix_v0.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

proven = []
for p in props:
    pe = [e for e in ev if e['property_id'] == p['property_id'] and e['use_category']
          and e['use_category'] not in ('vacant',) and e['evidence_kind'] != 'current']
    byc = collections.defaultdict(list)
    for e in pe:
        byc[e['use_category']].append(e)
    for c, es in byc.items():
        yrs = sorted(int(e['year']) for e in es if e['year'])
        decs = sorted({y // 10 * 10 for y in yrs})
        srcs = collections.Counter(e['source'].split(':')[0] for e in es)
        strength = 'strong' if (len(decs) >= 2 or len(srcs) >= 2) else 'single'
        proven.append(dict(property_id=p['property_id'], address=p['address'], use_category=c,
                           n_evidence=len(es), n_decades=len(decs), first_year=yrs[0] if yrs else '',
                           last_year=yrs[-1] if yrs else '', decades=' '.join(map(str, decs)),
                           sources='; '.join(f'{k} {v}' for k, v in srcs.items()), strength=strength))
proven.sort(key=lambda r: (int(r['address'].split()[0]), -r['n_evidence']))
with open(f'{OUT}/proven_uses_v0.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(proven[0].keys()))
    w.writeheader(); w.writerows(proven)

# ---------------------------------------------------------------- silence map (before vs after)
sil = []
for p in props:
    pid = p['property_id']
    def decs(filt):
        return sorted({int(e['decade']) for e in ev if e['property_id'] == pid and e['decade'] != ''
                       and (e['use_category'] or e['evidence_kind'] == 'business listed') and filt(e)})
    before = decs(lambda e: e['source'].startswith('sponsor'))
    after = decs(lambda e: e['evidence_kind'] != 'current')
    span = [d for d in DECS if 1910 <= d <= 2010]
    gaps = [d for d in span if d not in after]
    status = 'documented' if len([d for d in span if d in after]) >= 7 else ('partial' if len([d for d in span if d in after]) >= 4 else 'silent')
    sil.append(dict(property_id=pid, address=p['address'], block_side_id=p['block_side_id'],
                    decades_before=len([d for d in span if d in before]),
                    decades_after=len([d for d in span if d in after]),
                    status_after=status, gap_decades_1910_2010=' '.join(map(str, gaps)),
                    next_source=('Sanborn 1928/1953 + Polk 1930s-60s (desk)' if status != 'documented' else '')))
with open(f'{OUT}/silence_map_v0.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(sil[0].keys()))
    w.writeheader(); w.writerows(sil)

print('evidence rows', len(ev), collections.Counter(e['source'].split(':')[0] for e in ev))
print('coded', sum(1 for e in ev if e['use_category']), 'unassigned', len(unassigned))
print('silence before/after', collections.Counter(s['status_after'] for s in sil))
print('mean decades before', sum(s['decades_before'] for s in sil) / len(sil),
      'after', sum(s['decades_after'] for s in sil) / len(sil))
