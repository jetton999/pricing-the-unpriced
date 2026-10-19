#!/usr/bin/env python3
"""Use-history extractor v1 for the 79 Greenmount frontage properties.

Joins every source the team has for the frontage into one evidence table, codes each record
to the team's use categories, and writes the deliverables the research plan names:
a timeline table (one row per span), proven uses, a silence map, and a validation report
against the hand-built reference timelines.

    python3 team/extractor/extract.py          # from the repo root
    python3 -m unittest discover team/extractor

Standard library only. Paths resolve from the repo root (REPO env var overrides).
"""
import csv, json, os, re, collections, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rules import classify, classify_sanborn, CATEGORIES  # noqa: E402

REPO = os.environ.get('REPO') or os.path.abspath(os.path.join(HERE, '..', '..'))
EVIDENCE = os.environ.get('EVIDENCE') or os.path.join(REPO, 'team', 'evidence')
OUT = os.environ.get('OUT') or os.path.join(HERE, 'out')
FRONTAGE_SIDES = {'65', '67', '68', '69', '70', '71', '72'}
USE_CATS = [c for c in CATEGORIES if c != 'vacant']


def rp(*a):
    return os.path.join(REPO, *a)


def ep(name):
    return os.path.join(EVIDENCE, name)


def read_csv(path, **kw):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, **kw))


def write_csv(path, rows, fields=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------------ properties and addresses
def load_frontage():
    rows = read_csv(rp('team', 'week1', 'out', 'focus_area_properties.csv'))
    out = [r for r in rows if r['block_side_id'] in FRONTAGE_SIDES]
    for r in out:
        r['num'] = int(r['address'].split()[0])
    return out


class Addresser:
    """Map a Greenmount street number (or range) to a frontage parcel."""

    def __init__(self, props):
        self.by_num = {p['num']: p for p in props}
        self.nums = sorted(self.by_num)

    def assign(self, n, lo=None, hi=None):
        if n in self.by_num:
            return self.by_num[n], 'exact'
        if lo is not None and hi is not None:
            inside = [m for m in self.nums if lo <= m <= hi and m % 2 == lo % 2]
            if inside:
                return self.by_num[inside[0]], 'range'
        same = [m for m in self.nums if m % 2 == n % 2 and m // 100 == n // 100]
        lower = [m for m in same if m < n]
        if lower and n - max(lower) <= 14:
            return self.by_num[max(lower)], f'next parcel down (+{n - max(lower)})'
        higher = [m for m in same if m > n]
        if higher and min(higher) - n <= 2:
            return self.by_num[min(higher)], f'next parcel up (-{min(higher) - n})'
        return None, 'unassigned'


def parse_range(text):
    m = re.search(r'(\d{4})\s*[-–/]\s*(\d{2,4})', text or '')
    if not m:
        return None, None
    lo, h = int(m.group(1)), m.group(2)
    hi = int(h) if len(h) == 4 else int(str(lo)[:4 - len(h)] + h)
    return (lo, hi) if hi >= lo else (None, None)


def year_of(s):
    m = re.search(r'(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})', s or '')
    if m:
        y = int(m.group(3))
        y = y + 1900 if y < 100 else y
        return y if 1880 <= y <= 1975 else None
    m = re.search(r'\b(18[89]\d|19\d\d|20[0-2]\d)\b', s or '')
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ evidence
FIELDS = ['property_id', 'address', 'year', 'decade', 'source', 'source_ref', 'url', 'address_method',
          'business', 'text', 'use_category', 'use_subcategory', 'matched_keyword', 'kind', 'basis']


class Evidence:
    def __init__(self, props):
        self.props = props
        self.by_id = {p['property_id']: p for p in props}
        self.addr = Addresser(props)
        self.rows, self.unassigned = [], []

    def add(self, p, year, source, ref, text, business='', method='exact', kind='use', url='', coded=None):
        c, s, kw = coded if coded is not None else classify(f'{text} {business}')
        if s == 'store building (generic)' and (business or '').strip():
            s = 'named store'   # a business is named, so this is a shop in use, not just a shop front
        exact = method in ('exact', 'sponsor', 'range') or method.startswith('York crosswalk anchor')
        self.rows.append(dict(
            property_id=p['property_id'], address=p['address'], year=year or '',
            decade=(year // 10 * 10) if year else '', source=source, source_ref=ref, url=url,
            address_method=method, business=(business or '').strip()[:120], text=(text or '').strip()[:300],
            use_category=c, use_subcategory=s, matched_keyword=kw, kind=kind,
            basis='stated' if exact else 'inferred'))

    def miss(self, source, year, number, text):
        self.unassigned.append(dict(source=source, year=year, number=number, text=(text or '')[:120]))


def load_sponsor(E):
    sens = 0
    for r in read_csv(rp('team', 'week1', 'out', 'use_records.csv')):
        if r['use_class'] != 'A' or r['property_id'] not in E.by_id:
            continue
        y = int(r['year']) if (r['year'] or '').isdigit() else None
        text = r['summary']
        if r['sensitivity']:
            sens += 1   # never dropped; the flag travels at the front of the text so the map can hide it
            text = f"[sensitivity: {r['sensitivity']}] " + text
        E.add(E.by_id[r['property_id']], y, 'sponsor:' + r['source'], 'incident ' + r['incident_id'],
              text, r['businesses'], method='sponsor')
    return sens


POLK_ID = {'1901': 'rlpolkcosbaltimo1901rlpo', '1903': 'rlpolkcosbaltimo1903rlpo', '1904': 'rlpolkcosbaltimo1904rlpo',
           '1905': 'baltimorecitydir1905rlpo', '1906': 'baltimorecitydir1906rlpo', '1907': 'baltimorecitydir1907rlpo',
           '1908': 'baltimorecitydir1908rlpo', '1909': 'baltimorecitydir1909rlpo', '1912': 'baltimorecitydir1912rlpo',
           '1913': 'baltimorecitydir1913rlpo', '1914': 'baltimorecitydir1914rlpo', '1915': 'baltimorecitydir1915rlpo',
           '1917': 'baltimorecitydir1917rlpo', '1918': 'baltimorecitydir1918rlpo', '1920': 'baltimorecitydir1920rlpo',
           '1921': 'baltimorecitydir1921rlpo', '1922': 'polksbaltimoreci1922rlpo', '1923': 'polksbaltimoreci1923rlpo'}
POLK_NOISE = re.compile(r'^(and|n Gilmor|ay \d|w North|line \d|\d+ [nsew] |North and Maryland|\(See page|propr,?$)', re.I)
LISTED = re.compile(r',\s*\.?$|\b(Co|Bros|Assn|Son|& )\b')


def polk_kind(text):
    if classify(text)[0]:
        return 'use'
    return 'business listed' if LISTED.search(text) else 'listed (uncoded)'


def load_polk_greenmount(E):
    for r in read_csv(ep('polk_frontage_1912_1923.tsv'), delimiter='\t'):
        t = r['text']
        if POLK_NOISE.search(t) or len(re.sub(r'[^A-Za-z]', '', t)) < 4:
            continue
        n = int(r['address'])
        p, method = E.addr.assign(n)
        if not p:
            E.miss('polk', r['year'], n, t)
            continue
        E.add(p, int(r['year']), 'polk_directory', f"Polk {r['year']}: {n} Greenmount av", t, method=method,
              kind=polk_kind(t), url='https://archive.org/details/' + POLK_ID.get(r['year'], ''))


def load_crosswalk():
    cw = {}
    for r in read_csv(ep('york_crosswalk.csv')):
        cw[int(r['old_york_number'])] = (int(r['new_greenmount_number']), r['method'], r['confidence'])
    return cw


def load_polk_york(E, cw):
    for r in read_csv(ep('polk_york_1901_1913.tsv'), delimiter='\t'):
        t = r['text']
        if POLK_NOISE.search(t) or len(re.sub(r'[^A-Za-z]', '', t)) < 4:
            continue
        o = int(r['old_york_number'])
        if o not in cw:
            E.miss('polk_york', r['year'], o, t)
            continue
        n, how, conf = cw[o]
        p, method = E.addr.assign(n)
        if not p:
            E.miss('polk_york', r['year'], f'{o}->{n}', t)
            continue
        E.add(p, int(r['year']), 'polk_directory', f"Polk {r['year']}: {o} York rd (now {n} Greenmount)", t,
              method=f'York crosswalk {how} ({conf}); ' + method, kind=polk_kind(t),
              url='https://archive.org/details/' + POLK_ID.get(r['year'], ''))


def load_permits(E):
    for r in read_csv(ep('permit_cards_1924_1961.csv')):
        an = r['address_normalized'] or ''
        m = re.match(r'(\d{4}) Greenmount', an)
        if not m or 'not Greenmount' in an:
            E.miss('permit', r['application_date'], an, r['purpose_of_application'])
            continue
        lo, hi = parse_range(an.split('(')[1] if '(' in an else '')
        p, method = E.addr.assign(int(m.group(1)), lo, hi)
        if not p:
            E.miss('permit', r['application_date'], an, r['purpose_of_application'])
            continue
        purpose = r['purpose_expanded'] or r['purpose_of_application'] or ''
        y = year_of(r['application_date']) or year_of(r['permit_date'])
        occ = (' | occupancy ' + r['occupancy_class']) if r['occupancy_class'] else ''
        E.add(p, y, 'permit_card', f"BRG48-53 image {r['image_id']} line {r['line_no']}", purpose + occ,
              method=method, kind='permit', url=r['page_url'])


def load_sanborn(E):
    for r in read_csv(ep('sanborn_frontage.csv')):
        m = re.match(r'(\d{4})', r['street_numbers'] or '')
        if not m:
            continue
        lo, hi = parse_range(r['street_numbers'])
        p, method = E.addr.assign(int(m.group(1)), lo, hi)
        if not p:
            E.miss('sanborn', r['year'], r['street_numbers'], r['use_label'])
            continue
        desc = f"{r['stories']}-story {r['construction']} {r['use_expanded'] or r['use_label']}".strip()
        if r['notes']:
            desc += f" ({r['notes']})"
        E.add(p, int(r['year']), 'sanborn', f"Sanborn {r['year']} sheet {r['sheet']}", desc, method=method,
              kind='map', url=r['loc_url'], coded=classify_sanborn(r['use_label'], r['use_expanded']))


def load_nr(E):
    for r in read_csv(ep('nr_inventory_frontage.csv')):
        if not r['number_first'].isdigit():
            continue
        n = int(r['number_first'])
        hi = int(r['number_last']) if r['number_last'].isdigit() else None
        p, method = E.addr.assign(n, n if hi else None, hi)
        if not p:
            E.miss('nr', '', n, r['summary'])
            continue
        ref = f"NR nomination B-5229 p. {r['pdf_page']}"
        url = 'https://github.com/jetton999/pricing-the-unpriced-reading/blob/main/waverly/NR-Waverly-Main-Street-Historic-District-NPS-13001020-B-5229.pdf'
        cy = year_of(r['construction_date'])
        if cy:
            E.add(p, cy, 'nr_inventory', ref, f"built {r['construction_date']}: {r['style_or_form'] or ''} {r['original_or_historic_use'] or ''}".strip(),
                  method=method, kind='building', url=url,
                  coded=classify(r['original_or_historic_use']) if r['original_or_historic_use'] else ('', '', ''))
        for part in re.split(r';\s*', r['historic_names'] or ''):
            ym = re.search(r'\((?:[^)]*?)(19\d\d)', part)
            if ym and part.strip():
                E.add(p, int(ym.group(1)), 'nr_inventory', ref, part.strip(), method=method, kind='use', url=url)
        if r['use_at_nomination']:
            E.add(p, 2011, 'nr_inventory', ref + ' (use at fieldwork, c. 2011)', r['use_at_nomination'],
                  method=method, kind='use', url=url)


def load_interventions(E):
    path = rp('team', 'precedent', 'interventions.csv')
    if not os.path.exists(path):
        return
    for r in read_csv(path):
        m = re.match(r'(\d{4}) Greenmount', r['address'] or '')
        if not m:
            continue
        p, method = E.addr.assign(int(m.group(1)))
        if not p:
            continue
        y = year_of(r['year'])
        biz = r['business'] or ''
        if re.match(r'\s*(former|ex-|vacant)', biz, re.I):
            biz_code = ('', '', '')
        else:
            biz_code = classify(biz)
        E.add(p, y, 'dhcd_1970s', f"BRG48-43-10 {r['intervention_id']}: {r['source'][:60]}",
              f"{r['intervention_type']}: {r['description']}", business=r['business'], method=method,
              kind='use' if biz_code[0] else 'business listed', coded=biz_code)


def load_current(E):
    for r in read_csv(rp('team', 'tenants', 'current_tenants_2026-10.csv')):
        p = E.by_id.get(r['property_id'])
        if not p:
            continue
        if r['status'] in ('vacant', 'for lease'):
            coded = ('vacant', r['status'], '')
        elif r['status'] == 'occupied':
            coded = ((r['business_type'] or '').split(' ; ')[0], '', '')
        else:
            coded = ('', '', '')
        E.add(p, 2026, 'current_2026', r['source_title'] or 'tenant check', r['status'], business=r['tenant_name'],
              kind='current', url=r['source_url'], coded=coded)


def build():
    props = load_frontage()
    E = Evidence(props)
    sens = load_sponsor(E)
    cw = load_crosswalk()
    load_polk_york(E, cw)
    load_polk_greenmount(E)
    load_permits(E)
    load_sanborn(E)
    load_nr(E)
    load_interventions(E)
    load_current(E)
    return props, E, sens


# ------------------------------------------------------------------ timeline spans
GAP = 10   # years: records of one use this close together form one span (directories thin out after 1923)


def spans(E):
    by = collections.defaultdict(list)
    for e in E.rows:
        if e['use_category'] and e['use_category'] != 'vacant' and e['year'] and e['kind'] in ('use', 'map', 'permit', 'building', 'current'):
            by[(e['property_id'], e['use_category'])].append(e)
    out = []
    for (pid, cat), es in by.items():
        es.sort(key=lambda e: int(e['year']))
        cur = [es[0]]
        for e in es[1:]:
            if int(e['year']) - int(cur[-1]['year']) <= GAP:
                cur.append(e)
            else:
                out.append(span_row(pid, cat, cur, E)); cur = [e]
        out.append(span_row(pid, cat, cur, E))
    out.sort(key=lambda r: (int(r['address'].split()[0]), int(r['start_year'])))
    return out


def span_row(pid, cat, es, E):
    names = collections.Counter(e['business'] for e in es if e['business'])
    srcs = collections.Counter(e['source'].split(':')[0] for e in es)
    grade = 'documented (2+ source types)' if len(srcs) >= 2 else ('repeated (2+ records)' if len(es) >= 2 else 'single record')
    return dict(property_id=pid, address=E.by_id[pid]['address'], start_year=es[0]['year'], end_year=es[-1]['year'],
                use_category=cat, subcategories='; '.join(sorted({e['use_subcategory'] for e in es if e['use_subcategory']})),
                occupant='; '.join(n for n, _ in names.most_common(3)),
                stated_or_inferred='stated' if any(e['basis'] == 'stated' for e in es) else 'inferred',
                evidence_grade=grade, n_records=len(es), sources='; '.join(f'{k} {v}' for k, v in srcs.most_common()),
                source_rows=' | '.join(e['source_ref'] for e in es[:8]) + (' | ...' if len(es) > 8 else ''))


def proven_uses(span_rows):
    by = collections.defaultdict(list)
    for s in span_rows:
        if s['use_category'] in ('residential',) or s['address'] == '':
            pass
        by[(s['property_id'], s['address'], s['use_category'])].append(s)
    out = []
    for (pid, addr, cat), ss in by.items():
        yrs = sorted({int(s['start_year']) for s in ss} | {int(s['end_year']) for s in ss})
        decs = sorted({d for s in ss for d in range(int(s['start_year']) // 10 * 10, int(s['end_year']) // 10 * 10 + 1, 10)})
        nrec = sum(int(s['n_records']) for s in ss)
        strong = len(decs) >= 2 or any(s['evidence_grade'].startswith('documented') for s in ss)
        out.append(dict(property_id=pid, address=addr, use_category=cat, first_year=yrs[0], last_year=yrs[-1],
                        n_spans=len(ss), n_records=nrec, decades=' '.join(map(str, decs)), n_decades=len(decs),
                        strength='proven' if strong else 'single mention'))
    out.sort(key=lambda r: (int(r['address'].split()[0]), -r['n_decades']))
    return out


def silence(props, E):
    span = list(range(1900, 2030, 10))
    out = []
    for p in props:
        pid = p['property_id']

        def decs(filt):
            return {int(e['decade']) for e in E.rows if e['property_id'] == pid and e['decade'] != ''
                    and (e['use_category'] or e['kind'] == 'business listed') and filt(e)}
        before = decs(lambda e: e['source'].startswith('sponsor'))
        after = decs(lambda e: e['kind'] != 'current')
        have = [d for d in span if d in after]
        gaps = [d for d in span if d not in after and d < 2020]
        status = 'documented' if len(have) >= 8 else ('partial' if len(have) >= 5 else 'thin')
        out.append(dict(property_id=pid, address=p['address'], block_side_id=p['block_side_id'],
                        decades_sponsor_only=len([d for d in span if d in before]), decades_all_sources=len(have),
                        status=status, gap_decades=' '.join(map(str, gaps)),
                        what_would_fill_it=fill_hint(gaps)))
    return out


def fill_hint(gaps):
    h = []
    if any(1930 <= d <= 1960 for d in gaps):
        h.append('Polk 1930s-60s via the research desk; 1931 Building Survey')
    if any(1960 <= d <= 2000 for d in gaps):
        h.append('newspapers 1960s-90s (desk); Open Baltimore licences')
    if 2000 in gaps or 2010 in gaps:
        h.append('business registrations (Maryland Business Express); Street View history')
    if 1900 in gaps or 1910 in gaps:
        h.append('Sanborn 1901 index; Polk 1901-13 at the crosswalk number')
    return '; '.join(h)


# ------------------------------------------------------------------ validation against the reference timelines
def parse_reference(path):
    refs, prop = [], None
    for line in open(path, encoding='utf-8'):
        m = re.match(r'##\s+(\d{3,4} [^()]+?)\s*\(property (\d+)\)', line)
        if m:
            prop = (m.group(2), m.group(1).strip()); continue
        if prop and line.startswith('|') and not line.startswith('| Period') and not line.startswith('|---'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) < 5:
                continue
            period, use, occ, basis, rows = cells[:5]
            yrs = [int(y) for y in re.findall(r'(1[89]\d\d|20[0-2]\d)', period)]
            if not yrs:
                continue
            start = yrs[0]
            end = yrs[1] if len(yrs) > 1 else (start + 9 if re.search(r'[–-]\s*$', period) else start)
            if '1920s' in period:
                end = 1929
            if period.strip().lower().startswith('to '):
                start = end - 5
            cat = classify(f'{use} {occ}')[0]
            refs.append(dict(property_id=prop[0], address=prop[1], start=start, end=end, use=use, occupant=occ,
                             category=cat, basis=basis, rows=rows))
    return refs


def validate(E, refs, tol=1):
    ref_props = {r['property_id'] for r in refs}
    coded = [e for e in E.rows if e['property_id'] in ref_props and e['use_category'] and e['year']
             and e['use_category'] not in ('vacant',) and e['kind'] != 'current'
             and e['use_subcategory'] != 'store building (generic)']
    res = {}
    for label, filt in (('all sources', lambda e: True),
                        ('new sources only (not used to build the references)', lambda e: not e['source'].startswith('sponsor'))):
        rows = [e for e in coded if filt(e)]
        hit = 0
        recall_detail = []
        for r in refs:
            if not r['category']:
                continue
            ok = any(e['property_id'] == r['property_id'] and e['use_category'] == r['category']
                     and r['start'] - tol <= int(e['year']) <= r['end'] + tol for e in rows)
            have_any = any(e['property_id'] == r['property_id'] and r['start'] - tol <= int(e['year']) <= r['end'] + tol for e in rows)
            hit += ok
            recall_detail.append((r, ok, have_any))
        scored = [x for x in recall_detail if x[2]]
        agree = n_in = 0
        for e in rows:
            cover = [r for r in refs if r['property_id'] == e['property_id'] and r['start'] - tol <= int(e['year']) <= r['end'] + tol and r['category']]
            if not cover:
                continue
            n_in += 1
            agree += any(r['category'] == e['use_category'] for r in cover)
        res[label] = dict(ref_rows=len([r for r in refs if r['category']]), recalled=hit,
                          recall=hit / max(1, len([r for r in refs if r['category']])),
                          recall_where_source_covers=sum(1 for x in scored if x[1]) / max(1, len(scored)),
                          rows_scored=n_in, category_agreement=agree / max(1, n_in), detail=recall_detail)
    return res


def write_validation(res, refs, path):
    L = ['# Extractor v1 validation against the reference timelines', '',
         'Reference: `team/week1/out/use_timelines.md`, built by hand from the sponsor records in week 1. '
         'A reference row counts as recalled when the extractor has at least one record of the same use category '
         f'at that property within its years (one year either side). Category agreement is the share of the '
         'extractor\'s coded records that fall inside a reference row\'s years and carry a category that row has.', '',
         'Targets from the research plan: recall 90% or more, category agreement 85% or more.', '',
         '| Scope | Reference rows | Recalled | Recall | Recall where the source covers those years | Records scored | Category agreement |',
         '|---|---|---|---|---|---|---|']
    for k, v in res.items():
        L.append(f"| {k} | {v['ref_rows']} | {v['recalled']} | {v['recall']:.0%} | {v['recall_where_source_covers']:.0%} | {v['rows_scored']} | {v['category_agreement']:.0%} |")
    L += ['', 'The "all sources" row is not an independent test: the references were built from the sponsor records the '
          'extractor also reads. The "new sources only" row is the independent one. The four blind reference timelines in the '
          'research plan, built by a team member without looking at this output, are still needed.', '',
          '## Reference rows and whether each was found (all sources)', '', '| Property | Period | Use | Category | Found |', '|---|---|---|---|---|']
    for r, ok, _ in res['all sources']['detail']:
        L.append(f"| {r['address']} | {r['start']}-{r['end']} | {r['use']} | {r['category']} | {'yes' if ok else 'no'} |")
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def main():
    props, E, sens = build()
    os.makedirs(OUT, exist_ok=True)
    write_csv(os.path.join(OUT, 'evidence.csv'), E.rows, FIELDS)
    write_csv(os.path.join(OUT, 'unassigned.csv'), E.unassigned, ['source', 'year', 'number', 'text'])
    sp = spans(E)
    write_csv(os.path.join(OUT, 'timeline_table.csv'), sp)
    pu = proven_uses(sp)
    write_csv(os.path.join(OUT, 'proven_uses.csv'), pu)
    sil = silence(props, E)
    write_csv(os.path.join(OUT, 'silence_map.csv'), sil)
    refs = parse_reference(rp('team', 'week1', 'out', 'use_timelines.md'))
    res = validate(E, refs)
    write_validation(res, refs, os.path.join(OUT, 'validation.md'))
    src = collections.Counter(e['source'].split(':')[0] for e in E.rows)
    print('evidence', len(E.rows), dict(src), 'unassigned', len(E.unassigned), 'sensitivity-flagged kept', sens)
    print('spans', len(sp), 'proven uses', sum(1 for r in pu if r['strength'] == 'proven'))
    print('silence', collections.Counter(s['status'] for s in sil),
          'mean decades sponsor-only %.1f all %.1f' % (sum(s['decades_sponsor_only'] for s in sil) / len(sil),
                                                       sum(s['decades_all_sources'] for s in sil) / len(sil)))
    for k, v in res.items():
        print(k, 'recall %.0f%%' % (100 * v['recall']), 'recall(covered) %.0f%%' % (100 * v['recall_where_source_covers']),
              'agreement %.0f%% of %d' % (100 * v['category_agreement'], v['rows_scored']))
    return props, E, sp, pu, sil, res


if __name__ == '__main__':
    main()
