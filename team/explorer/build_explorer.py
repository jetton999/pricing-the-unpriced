#!/usr/bin/env python3
"""Build team/explorer/index.html, the Greenmount frontage explorer, from the repo's extractor v1 outputs.

Run from anywhere:  python3 team/explorer/build_explorer.py
Inputs: team/extractor/out, team/evidence, team/tenants, team/week1/out, properties.csv, property_incidents.csv,
and the hand-made files beside this script (concepts.json, library.json, retail_types.json, typical_sqft.json).
Output: index.html beside this script.

The team's private copy is built by the same script with PTU_LIBRARY, PTU_CONCEPTS, PTU_PRIVATE_BRANDS,
PTU_PRIVATE_SIZES and PTU_OUT pointing at files kept outside the repo (the reference brands, which the sponsor
keeps out of the public repo; PTU_BARE=1 writes the page without its html wrapper). Unset, it reads repo files only.

Same schema as screen_v0.py's explorer_data.json, so the page template keeps working.
Standard library only."""
import csv, json, collections, math, re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
X = os.path.join(REPO, 'team', 'extractor', 'out')
csv.field_size_limit(sys.maxsize)
rd = lambda p: list(csv.DictReader(open(p, encoding='utf-8-sig')))

fa = {r['property_id']: r for r in rd(os.path.join(REPO, 'team/week1/out/focus_area_properties.csv'))}
SIDES = {'65', '67', '68', '69', '70', '71', '72'}
gaps = rd(os.path.join(REPO, 'team/evidence/blocklot_gaps.csv'))
merged = {g['property_id']: g['current_property_id'] for g in gaps if g['current_property_id']}
props = {k: v for k, v in fa.items() if v['block_side_id'] in SIDES and k not in merged}   # 69 parcels today
geo = {r['id']: r for r in rd(os.path.join(REPO, 'properties.csv'))}
ten = {r['property_id']: r for r in rd(os.path.join(REPO, 'team/tenants/current_tenants_2026-10.csv'))}
ev = rd(os.path.join(X, 'evidence.csv'))
# Sponsor white-paper rows that summarise the NR inventory entry ("Built ca.1880 ... Historic use: ...") are dated to the
# build year and coded by their first keyword, which invents early uses. The NR inventory rows carry the same facts with
# their own years, so these summaries are kept as records but not coded here. Fix goes into extractor v1.1.
SUMMARY = lambda e: e['source'].startswith('sponsor') and e['text'].startswith('Built ca') and 'B-5229' in e['text']
n_summary = 0
for e in ev:
    if SUMMARY(e):
        e['use_category'] = ''; e['use_subcategory'] = ''; e['kind'] = 'building'; n_summary += 1
sil = {r['property_id']: r for r in rd(os.path.join(X, 'silence_map.csv'))}
GENERIC = 'store building (generic)'


def cats_now(t):
    if t['status'] in ('vacant', 'for lease'):
        return ['vacant']
    if t['status'] != 'occupied':
        return []
    return [c for c in (t['business_type'] or '').split(' ; ') if c]


# One business in two street numbers is one business: the tenant list says "same store as 3127" on the second row,
# and that parcel is then left out of every count of businesses (the cap of three, the corridor mix, the back-test).
SAME = re.compile(r'same (?:store|business|shop|church|office) as (\d{3,4})', re.I)
by_number = {v['address'].split()[0]: k for k, v in props.items()}
same_as = {}
for pid, t in ten.items():
    m = SAME.search(t['tenant_name'] or '')
    cur = merged.get(pid, pid)
    if m and cur in props and by_number.get(m.group(1)) and by_number[m.group(1)] != cur:
        same_as[cur] = by_number[m.group(1)]

side_mix = collections.defaultdict(collections.Counter)
corr_mix = collections.Counter()
parcel_now = collections.defaultdict(set)      # a parcel's uses today, across the tenant rows filed on it
occupied = set()
for pid, t in ten.items():
    cur = merged.get(pid, pid)
    if cur not in props:
        continue
    parcel_now[cur] |= set(cats_now(t))
    if t['status'] == 'occupied':
        occupied.add(cur)
for cur, cs in parcel_now.items():
    if cur in same_as:
        continue
    for c in cs:
        side_mix[props[cur]['block_side_id']][c] += 1
        corr_mix[c] += 1


def now_basis(t):
    """How the tenant list knows what is at an address today, in the page's words, and whether a person has checked the row."""
    st = (t['source_type'] or '').strip()
    who = (t['entered_by'] or '')
    person = not who.startswith('Claude') and 'AI-assisted' not in who
    label = {'sponsor audit': "the sponsor's storefront audit, November 2026", 'street view': 'Street View, September 2026 imagery',
             'sponsor photo': "the sponsor's walk photos, 3 November 2026", 'search snippet': 'a search listing only',
             'map listing': 'a map listing', 'business website': "the business's website", 'news': 'a news article',
             'licence data': 'licence records', 'listing': 'a property listing', 'directory': 'a directory',
             'team check': "the team's check"}.get(st, st or 'no source')
    return dict(src=st, label=label, person=person)

NOT_CAND = {'residential', 'institutional & religious', 'vacant'}

by = collections.defaultdict(list)
for e in ev:
    by[e['property_id']].append(e)

# Kinds of source. Two rows count as independent only if they come from different kinds: a sponsor record that
# transcribes a directory is the same kind as the directory.
FAMILY = {'polk_directory': 'directory', 'sponsor:polk': 'directory', 'sponsor:census_directory': 'directory',
          'permit_card': 'permit card', 'sanborn': 'fire-insurance map',
          'nr_inventory': 'National Register', 'sponsor:nrhp': 'National Register',
          'dhcd_1970s': '1970s city file', 'sponsor:bca_dhcd': '1970s city file',
          'sponsor:newspapers_com': 'newspaper', 'sponsor:web_press': 'newspaper', 'sponsor:chronicling_america': 'newspaper',
          'sponsor:mdlandrec': 'land record', 'sponsor:msa_ce168': 'land record',
          'sponsor:whitepaper': 'sponsor research note', 'sponsor:ephemera': 'ephemera', 'sponsor:web_research': 'web research'}
CURRENT = lambda e: e['source'] == 'current_2026' or e['kind'] == 'current'    # the tenant check is today, not history
for e in ev:
    assert e['source'] in FAMILY or CURRENT(e), 'source with no family: ' + e['source']


def summarise(rows):
    decs = sorted({int(r['decade']) for r in rows})
    srcs = {r['source'].split(':')[0] for r in rows}
    bar = sum(1 for r in rows if r['use_subcategory'] == 'bar / tavern')
    return dict(nd=len(decs), ne=len(rows), first=min(int(r['year']) for r in rows), last=max(int(r['year']) for r in rows),
                strong=len(decs) >= 2 or len(srcs) >= 2, bar_share=bar / len(rows), nsrc=len(srcs))


def proven_from(keep):
    """Uses on record per parcel, from stated trades only (a bare "store" is a shop front, not a use)."""
    out = collections.defaultdict(list)
    for pid, es in by.items():
        g = collections.defaultdict(list)
        for e in es:
            if e['use_category'] and e['year'] and e['use_subcategory'] != GENERIC and keep(e):
                g[e['use_category']].append(e)
        for c, rows in g.items():
            out[pid].append(dict(summarise(rows), cat=c, rows=rows))
    return out


# The score's heritage reads history only. Until 21 Nov 2026 the 2026 tenant check counted too, so a business
# trading today raised the score of its own use (sponsor's review, 17 Nov 2026). proven_with_today keeps the old
# reading for the comparison the page publishes.
proven = proven_from(lambda e: not CURRENT(e))
proven_with_today = proven_from(lambda e: True)

screen = []
for pid, p in props.items():
    t = ten[pid]
    sqft = int(float(p['structure_sqft'])) if p['structure_sqft'] else None
    side = p['block_side_id']
    status = t['status']
    avail = 'available now' if status in ('vacant', 'for lease') else ('possibly available' if status == 'unknown' else 'occupied')
    cands = []
    for r in proven[pid]:
        if r['cat'] in NOT_CAND or not r['strong']:
            continue
        sat = side_mix[side][r['cat']]
        pen = 3 if sat >= 3 else (1 if sat == 2 else 0)
        why = f"{r['ne']} records across {r['nd']} decade(s) ({r['first']}-{r['last']}); {sat} on this block side today"
        fmt = ''
        if r['cat'] == 'retail goods' and sqft and sqft >= 5000:
            fmt = 'large-format retail / showroom'
        elif r['cat'] == 'food & drink' and sqft and sqft <= 3000:
            fmt = 'small cafe / counter service'
        if r['cat'] == 'food & drink' and r['bar_share'] >= 0.5:
            why += '; most of the record is a saloon or tavern, and a new tavern is barred by the urban renewal plan (a restaurant or cafe is allowed and can serve alcohol)'
        cands.append(dict(use=r['cat'], format=fmt, score=round(2 * r['nd'] + min(r['ne'], 20) / 5 - pen, 2), why=why))
    cands.sort(key=lambda x: -x['score'])
    if not cands and any(r['cat'] == 'residential' for r in proven[pid]):
        cands = [dict(use='residential', format='no commercial use on record', score=0, why='only dwelling evidence so far')]
    pv = sorted([r for r in proven[pid] if r['strong']], key=lambda r: -r['nd'])
    screen.append(dict(pid=pid, address=p['address'], side=side, sqft=sqft or '', zoning=p['zoning_code'],
                       tour=p['matterport_tour'] == 'yes', status=status, tenant=t['tenant_name'],
                       uses_now=' ; '.join(cats_now(t)), availability=avail, evidence=sil[pid]['status'],
                       decades=int(sil[pid]['decades_all_sources']),
                       proven=' ; '.join(f"{r['cat']} ({r['nd']}d)" for r in pv),
                       cand1=(cands[0]['use'] + (' - ' + cands[0]['format'] if cands[0]['format'] else '')) if cands else '',
                       cand1_why=cands[0]['why'] if cands else '',
                       cand2=(cands[1]['use'] + (' - ' + cands[1]['format'] if cands[1]['format'] else '')) if len(cands) > 1 else ''))
screen.sort(key=lambda r: int(r['address'].split()[0]))


def ring(pid):
    try:
        j = json.loads(geo.get(pid, {}).get('lot_polygon') or 'null')
        return [[round(x, 6), round(y, 6)] for x, y in j['rings'][0]] if j else None
    except Exception:
        return None


inc = rd(os.path.join(REPO, 'property_incidents.csv'))
ADM = lambda src: src.startswith('baltimore:') or src in ('sdat_assessments', 'sdat:owner')
story = collections.defaultdict(lambda: [0, 0])          # [curated records excluding the burial register, white papers]
for r in inc:
    if ADM(r['source']) or r['source'] == 'stjohns_interments':
        continue
    cur = merged.get(r['property_id'], r['property_id'])
    if cur in props:
        story[cur][0] += 1
        story[cur][1] += r['source'] == 'whitepaper'


def ring_sqft(ring):
    """Area of one outline in sq ft: the shoelace formula on a local flat projection (the outlines are in longitude and latitude)."""
    lat0 = sum(pt[1] for pt in ring) / len(ring)
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0
    pts = [(pt[0] * kx, pt[1] * ky) for pt in ring]
    return abs(sum(pts[j][0] * pts[(j + 1) % len(pts)][1] - pts[(j + 1) % len(pts)][0] * pts[j][1] for j in range(len(pts)))) / 2 * 10.7639


def outline_sqft(pid, column):
    """Total area of the outlines the sponsor's export gives in one column (lot_polygon or building_polygons); None if none."""
    try:
        j = json.loads(geo.get(pid, {}).get(column) or 'null')
    except ValueError:
        return None
    total = 0.0
    for poly in (j if isinstance(j, list) else [j] if j else []):
        for i, ring in enumerate(poly.get('rings') or []):
            total += ring_sqft(ring) * (1 if i == 0 else -1)          # a second ring in one polygon is a hole
    return round(total) if total > 0 else None


def ground_floor(pid, sqft):
    """Ground-floor area for the rent figures. The export records the floor area of the whole building only, so this
    is an estimate from its outlines until someone measures the shop floor:
      low   the building outline, capped at the recorded floor area and at the lot (the planning figure);
      high  the smaller of the recorded floor area and the lot (the most the ground floor can be).
    Some outlines cover only part of a building. Where the outline is under half of the high figure, or the export has
    no outline, the parcel is marked "measure first"; with no outline the high figure is all there is."""
    fp, lot = outline_sqft(pid, 'building_polygons'), outline_sqft(pid, 'lot_polygon')
    caps = [x for x in (sqft, lot) if x]
    hi = min(caps) if caps else None
    lo = min([fp] + caps) if fp else hi
    note = 'no outline' if not fp else ('outline may be partial' if hi and fp < 0.5 * hi else 'outline')
    return dict(lo=lo, hi=hi, note=note, lot=lot, outline=fp)

SRC = {'polk_directory': 'Polk directory', 'permit_card': 'permit card', 'sanborn': 'Sanborn map',
       'nr_inventory': 'NR inventory', 'dhcd_1970s': '1970s DHCD file', 'current_2026': '2026 tenant check'}
DOM = ['food & drink', 'retail goods', 'personal services', 'automotive', 'entertainment & assembly',
       'institutional & religious', 'production & light industry', 'office', 'residential']
data = dict(props=[])
for s in screen:
    pid = s['pid']
    g = geo.get(pid, {})
    es = sorted(by[pid], key=lambda e: int(e['year'] or 0))
    strip = {}
    for e in es:
        if e['use_category'] in DOM and e['decade'] and e['use_subcategory'] != GENERIC:
            strip.setdefault(int(e['decade']), collections.Counter())[e['use_category']] += 1
    shown = [e for e in es if e['use_category'] or e['kind'] in ('business listed', 'current', 'building')]
    gfl = ground_floor(pid, s['sqft'] or None)
    hrow = lambda r: [r['nd'], r['ne'], r['nsrc'], r['first'], r['last'], round(r['bar_share'], 2)]
    h_now = {r['cat']: hrow(r) for r in proven[pid] if r['cat'] != 'vacant'}
    h_old = {r['cat']: hrow(r) for r in proven_with_today[pid] if r['cat'] != 'vacant'}
    data['props'].append(dict(
        id=pid, address=s['address'].replace(' Greenmount Ave', ''), side=s['side'], sqft=s['sqft'], zoning=s['zoning'],
        gf=gfl['lo'], gf_hi=gfl['hi'], gf_note=gfl['note'], tour=s['tour'], status=s['status'], tenant=s['tenant'], uses_now=s['uses_now'],
        same_as=same_as.get(pid), basis=now_basis(ten[pid]),
        availability=s['availability'], evidence=s['evidence'], decades=s['decades'], proven=s['proven'],
        cand1=s['cand1'], cand1_why=s['cand1_why'], cand2=s['cand2'],
        lat=float(g.get('latitude') or 0), lon=float(g.get('longitude') or 0), ring=ring(pid),
        h=h_now, h0=h_old if h_old != h_now else None,
        story=story.get(pid, [0, 0]), now=sorted(c for c in parcel_now[pid] if c != 'vacant'), occ=pid in occupied,
        strip={str(d): c.most_common(1)[0][0] for d, c in strip.items()},
        ev=[dict(y=e['year'], src=SRC.get(e['source'], e['source'].replace('sponsor:', 'sponsor ').replace('_', ' ')),
                 cat=e['use_category'] + (' (shop front)' if e['use_subcategory'] == GENERIC else ''),
                 t=((e['business'] + ' - ') if e['business'] and e['source'] != 'polk_directory' else '') + e['text'][:160],
                 ref=e['source_ref'], url=e['url'], m=e['address_method'] if e['basis'] == 'inferred' else '',
                 k='' if CURRENT(e) else FAMILY[e['source']])
            for e in shown][:150]))

srcs = collections.Counter(e['source'].split(':')[0] for e in ev)
data['totals'] = dict(srcs)
# how records reached a parcel: by the address they state, or by inference (the next parcel down, the York Road crosswalk)
_hist = [e for e in ev if not CURRENT(e)]
# Greenmount parcels the export has between 2900 and 3299 that are not among the frontage parcels on this page: the
# focus outline was traced by hand from the sponsor's map in week 1 (team/week1/focus_area.py). Shown under "known limits".
_assess = {r['property_id']: r['status'] for r in rd(os.path.join(REPO, 'storefront_assessments.csv'))}
_out = []
_word = {'vacant_lot': 'a vacant lot', 'open_active': 'an open business', 'institution': 'an institution', 'vacant_storefront': 'a vacant storefront'}
for _id, _r in geo.items():
    _m = re.match(r'(\d+(?: 1/2)?) Greenmount', _r['address'])
    if _m and 2900 <= int(_m.group(1).split()[0]) <= 3299 and _id not in props and _id not in merged:
        _out.append(dict(address=_m.group(1), east_2900=_r['block_side_id'] == '66',
                         status=_word.get(_assess.get(_id), (_assess.get(_id) or 'no assessment').replace('_', ' '))))
data['left_out'] = sorted(_out, key=lambda r: (int(r['address'].split()[0]), r['address']))
data['source_kinds'] = sorted({FAMILY[e['source']] for e in _hist})      # kinds of source among the history records
data['placed'] = dict(total=len(_hist), inferred=sum(1 for e in _hist if e['basis'] == 'inferred'),
                      next=sum(1 for e in _hist if 'next parcel' in e['address_method']))
st = collections.Counter(s['status'] for s in sil.values())
mean = lambda k: round(sum(int(s[k]) for s in sil.values()) / len(sil), 1)
data['silence'] = dict(before=mean('decades_sponsor_only'), after=mean('decades_all_sources'), status=dict(st))
val = open(os.path.join(X, 'validation.md'), encoding='utf-8').read()
m = re.search(r'\| all sources \| (\d+) \| (\d+) \| (\d+)% \| (\d+)% \| (\d+) \| (\d+)% \|', val)
m2 = re.search(r'\| new sources only[^|]*\| (\d+) \| (\d+) \| (\d+)% \| (\d+)% \| (\d+) \| (\d+)% \|', val)
# Lead with the independent figure. The "all sources" row is not a test: the references were built from the same sponsor
# records the extractor reads (sponsor's review, 17 Nov 2026: the page and the model card had quoted the flattering one).
data['validation'] = (f"Against the four hand-built reference timelines, using only the sources that were not used to build them, the "
                      f"extractor finds {m2.group(3)}% of the reference uses ({m2.group(2)} of {m2.group(1)}; {m2.group(4)}% where those sources cover the "
                      f"years), and {m2.group(6)}% of its {m2.group(5)} coded records agree with the reference category. With all sources it finds "
                      f"{m.group(3)}%, but the references were built from the same sponsor records, so that figure is not a test. The four blind "
                      f"reference timelines that would be one are not started.")
data['validation_numbers'] = dict(independent=dict(rows=int(m2.group(1)), found=int(m2.group(2)), recall=int(m2.group(3)), recall_covered=int(m2.group(4)),
                                                   records=int(m2.group(5)), agreement=int(m2.group(6))),
                                  all_sources=dict(rows=int(m.group(1)), found=int(m.group(2)), recall=int(m.group(3)), recall_covered=int(m.group(4)),
                                                   records=int(m.group(5)), agreement=int(m.group(6))))

# the mix then (Polk 1920-23, buildings with a coded line) and now (occupied in Oct 2026)
then = collections.defaultdict(set)
base_then = set()
for e in ev:
    if e['source'] == 'polk_directory' and e['year'] and 1920 <= int(e['year']) <= 1923 and e['use_category'] \
            and e['use_subcategory'] != GENERIC:
        base_then.add(e['property_id'])
        then[e['use_category']].add(e['property_id'])
occ = sorted(occupied - set(same_as))             # one business in two street numbers counts once
data['mix'] = [dict(cat=c, then=len(then[c]), then_base=len(base_then), now=corr_mix[c], now_base=len(occ))
               for c in DOM if c != 'residential']
data['mix'].sort(key=lambda m: -m['then'] / max(1, m['then_base']))
# ---- building form, readiness and neighbours per parcel
nr = rd(os.path.join(REPO, 'team/evidence/nr_inventory_frontage.csv'))
def nr_row(num, odd):
    for r in nr:
        try:
            a, b = int(r['number_first']), int(r['number_last'] or r['number_first'])
        except ValueError:
            continue
        if a <= num <= b and (a % 2 == 1) == odd and 'Greenmount' in r['address_as_listed']:
            return r
    return None
def btype_of(prop, r):
    st = (r['style_or_form'] if r else '').lower()
    h = prop.get('h', {})
    if 'theat' in st: return 'theatre'
    if 'bank' in st: return 'bank'
    if 'church' in st: return 'church'
    if 'gas station' in st or 'garage' in st: return 'garage/showroom'
    if h.get('automotive') and h['automotive'][0] >= 3 and (prop['sqft'] or 0) >= 4000: return 'garage/showroom'
    if ('rowhouse' in st or 'row house' in st or 'dwelling' in st) and not any(k in st for k in ('storefront', 'commercial')): return 'rowhouse/house'
    return 'small storefront'
OWNER_KIND = lambda n: ('company' if any(k in n.upper() for k in ('LLC', ' INC', 'CORP', 'COMPANY', 'TRUST', 'REALTY', 'LIMITED', 'NET-LEASED', 'HOMES', 'HOUSING', 'CAPITAL', 'INVESTMENT')) else
                        'church or nonprofit' if any(k in n.upper() for k in ('CHURCH', 'TEMPLE', 'MINIST', 'OUTREACH', 'PARISH')) else
                        'individual' if n.strip() else 'unknown')
for q in data['props']:
    num = int(q['address'].split()[0]); r = nr_row(num, num % 2 == 1)
    q['btype'] = btype_of(q, r)
    m = re.search(r'(1[89]\d\d)', (r or {}).get('construction_date', '') or '')
    q['built'] = int(m.group(1)) if m else (int(geo.get(q['id'], {}).get('year_built') or 0) or None)
    q['form'] = (r or {}).get('style_or_form', '')
    g = geo.get(q['id'], {})
    q['ready'] = dict(vbn=g.get('vacant_notice_status', ''), viol=int(g.get('violations_12mo_count') or 0),
                      permits=int(g.get('active_permit_count') or 0), receiv=g.get('receivership_status', ''),
                      taxcert=g.get('tax_certificate_active', '') == 'true', owner=OWNER_KIND(g.get('owner_name', '')),
                      tour=q['tour'])
# Evidence behind each use at each building: how many records name the address itself, how many kinds of source they
# come from, and whether they date from the building that stands there now. "strict" follows the definition in the
# sponsor's review of 17 Nov 2026: two independent kinds of source, a stated address, a named trade, the standing building.
for q in data['props']:
    built = q['built']
    hq, hs = {}, {}
    for r in proven[q['id']]:
        if r['cat'] == 'vacant':
            continue
        rows = r['rows']
        stated = [e for e in rows if e['basis'] != 'inferred']
        standing = [e for e in stated if not built or int(e['year']) >= built - 1]
        fams = sorted({FAMILY[e['source']] for e in standing})
        strict = len(fams) >= 2
        hq[r['cat']] = dict(n=len(rows), stated=len(stated), inferred=len(rows) - len(stated), before=len(stated) - len(standing),
                            fams=fams, strict=strict)
        if strict:
            x = summarise(standing)
            hs[r['cat']] = [x['nd'], x['ne'], len(fams), x['first'], x['last'], round(x['bar_share'], 2)]
    q['hq'] = hq
    q['hs'] = hs
by_side = collections.defaultdict(list)
for q in data['props']:
    by_side[q['side']].append(q)
ACROSS = {'67': '68', '68': '67', '69': '70', '70': '69', '71': '72', '72': '71'}
for sd, qs in by_side.items():
    qs.sort(key=lambda q: int(q['address'].split()[0]))
    for i, q in enumerate(qs):
        q['nb'] = dict(left=qs[i - 1]['id'] if i > 0 else None, right=qs[i + 1]['id'] if i + 1 < len(qs) else None, across=[])
for q in data['props']:
    other = by_side.get(ACROSS.get(q['side'], ''), [])
    if other and q['lat']:
        q['nb']['across'] = [o['id'] for o in sorted(other, key=lambda o: abs(o['lat'] - q['lat']))[:2]]
LIB = json.load(open(os.environ.get('PTU_LIBRARY') or os.path.join(HERE, 'library.json'), encoding='utf-8'))
data['lib'] = {k: LIB[k] for k in ('buildings', 'districts', 'waverly', 'aversion', 'requested', 'adjacency', 'segments', 'history_value', 'match_lessons')}
# the page shows the ground rules from the sponsor's proposal, and nothing else about the sponsor
data['lib']['sponsor'] = {'guardrails': LIB['sponsor'].get('guardrails', [])}
data['lib']['meta'] = {k: LIB['meta'][k] for k in ('displacement_rubric', 'updated', 'research_2026_10_26') if k in LIB['meta']}
# the count of empty storefronts in the Waverly facts box comes from the tenant list at build time, never from typed text
data['lib']['waverly'] = dict(LIB['waverly'])

# ---- preliminary back-test of the heritage prior: do uses proven before a cut-off year predict the 2026 use?
NOTUSE = {'residential', 'vacant', ''}
now_cats = collections.defaultdict(set)
for pid, t in ten.items():
    cur = merged.get(pid, pid)
    if cur in props and t['status'] == 'occupied':
        now_cats[cur] |= {c for c in (t['business_type'] or '').split(' ; ') if c and c not in NOTUSE}


def proven_before(cut):
    g = collections.defaultdict(lambda: collections.defaultdict(list))
    for e in ev:
        if e['use_subcategory'] == GENERIC or e['use_category'] in NOTUSE or not e['year'] or int(e['year']) > cut:
            continue
        g[e['property_id']][e['use_category']].append(e)
    return {pid: {c for c, rows in cs.items() if len({r['decade'] for r in rows}) >= 2
                  or len({r['source'].split(':')[0] for r in rows}) >= 2} for pid, cs in g.items()}


bt = []
for cut in (1940, 1960):
    pv = proven_before(cut)
    order = [c for c, _ in collections.Counter(c for v in pv.values() for c in v).most_common()]
    rows = [(pid, pv[pid], oc) for pid, oc in now_cats.items() if oc and pv.get(pid)]
    hit = sum(bool(oc & v) for _, v, oc in rows)
    base = sum(bool(oc & set(order[:len(v)])) for _, v, oc in rows)
    percat = []
    for c in DOM:
        if c == 'residential':
            continue
        have = [pid for pid in now_cats if c in pv.get(pid, set())]
        other = [pid for pid in now_cats if pid in pv and c not in pv[pid]]
        percat.append(dict(cat=c, a=sum(c in now_cats[x] for x in have), an=len(have),
                           b=sum(c in now_cats[x] for x in other), bn=len(other)))
    bt.append(dict(cut=cut, n=len(rows), hit=hit, base=base, percat=percat))
data['backtest'] = bt

# back-test v2 (team/validation): the parcel-by-use test, run on the frontage and on the other Greenmount blocks
_bt2p = os.path.join(REPO, 'team', 'validation', 'out', 'backtest_v2.json')
if os.path.exists(_bt2p):
    _b2 = json.load(open(_bt2p, encoding='utf-8'))
    _keep = ('cut', 'parcels', 'parcels_with_history', 'rows', 'present', 'p_perm', 'p_lr', 'auc_base', 'auc_history', 'odds_3_decades',
             'p_lr_with_depth_control', 'by_history', 'per_category')
    data['backtest2'] = {k: [{kk: a[kk] for kk in _keep if kk in a} for a in _b2[k]]
                         for k in ('frontage', 'frontage_sponsor_only', 'other_blocks', 'other_blocks_without_low_confidence',
                                   'other_blocks_stated_uses_only', 'other_blocks_without_multi_tenant', 'other_blocks_before_leak_fix')}
    data['backtest2']['transfer'] = _b2['transfer_frontage_sponsor_to_other']
    data['backtest2']['transfer_ci'] = _b2['transfer_interval_sponsor_to_other']
    data['backtest2']['holdout'] = _b2['frontage_leave_one_side_out']
    data['backtest2']['by_kind'] = _b2['other_blocks_by_kind_of_use']
    data['backtest2']['loo'] = [{k: x[k] for k in ('cut', 'p_all_parcels', 'min', 'max', 'median', 'below_0_05', 'parcels', 'lowest', 'highest')}
                                for x in _b2['other_blocks_leave_one_parcel_out']]
    data['backtest2']['multi'] = _b2['multi_tenant_parcels']
    data['backtest2']['selection'] = _b2['selection_empty_against_in_use']
    data['backtest2']['decision'] = _b2['decision']
    data['backtest2']['similarity'] = _b2['similarity']
data['n_summary'] = n_summary

# ---- candidate formats: heritage links, C-1 zoning status (Table 10-301), urban renewal plan, size range (team assumption; the page uses the sourced typical range where there is one, score v0.4)
data['formats'] = [
    dict(id='cafe', name='Cafe or sit-down restaurant', cat='food & drink', her=[['food & drink', 1]], z='Restaurant', zs='P', size=[800, 4000],
         note='Porch or sidewalk seating is outdoor dining: a conditional use in C-1 (Table 10-301, note 5). The urban renewal plan bars taverns, not restaurants, so a restaurant can serve alcohol (Waverly Business Area Urban Renewal Plan, Amendment No. 2, 4 December 1995). This is the team\'s reading, not legal advice.'),
    dict(id='counter', name='Take-away counter (coffee, ice cream)', cat='food & drink', her=[['food & drink', 1]], z='Carry-Out Food Shop', zs='CB', size=[250, 1500],
         note='Serving mostly to go in disposable containers makes it a carry-out food shop (zoning code 1-303).'),
    dict(id='foodmaker', name='Food maker with a shop (bakery, roaster, ice cream)', cat='food & drink', her=[['food & drink', 0.8], ['production & light industry', 0.8]], z='Food Processing: Light', zs='P', size=[1000, 6000], note=''),
    dict(id='tavern', name='Bar or tavern', cat='food & drink', her=[['food & drink', 1]], bar=True, z='Tavern', zs='CB', urp=True, size=[800, 5000],
         note="The urban renewal plan bars new taverns, liquor stores and pawnshops (Waverly Business Area Urban Renewal Plan, Amendment No. 2, 4 December 1995). It bars taverns, not restaurants, so a restaurant can serve alcohol. This is the team's reading, not legal advice."),
    dict(id='shop', name='Small shop', cat='retail goods', her=[['retail goods', 1]], z='Retail Goods Establishment (no alcohol)', zs='P', size=[400, 2500], note=''),
    dict(id='showroom', name='Showroom or large shop', cat='retail goods', her=[['retail goods', 1]], z='Retail Goods Establishment (no alcohol)', zs='P', size=[2500, 12000], note=''),
    dict(id='bike', name='Bike shop', cat='retail goods', her=[['automotive', 0.6], ['retail goods', 0.4]], z='Retail Goods Establishment (no alcohol)', zs='P', size=[800, 4000],
         note='Heritage borrowed from the transport trades (livery, garage). A repair bay may need a zoning check.'),
    dict(id='garage', name='Vehicle repair or garage', cat='automotive', her=[['automotive', 1]], z='Motor Vehicle Service and Repair', zs='NP', size=[1500, 10000],
         note='Not permitted in C-1.'),
    dict(id='services', name='Barber, salon or other personal services', cat='personal services', her=[['personal services', 1]], z='Personal Services Establishment', zs='P', size=[400, 2000], note=''),
    dict(id='fitness', name='Fitness studio', cat='personal services', her=[['personal services', 0.6], ['entertainment & assembly', 0.5]], z='Health and Fitness Center', zs='P', size=[1500, 6000], note=''),
    dict(id='studio', name='Arts studio, gallery or rehearsal space', cat='entertainment & assembly', her=[['entertainment & assembly', 1], ['production & light industry', 0.5]], z='Arts Studio; Art Gallery', zs='P', size=[400, 8000], note=''),
    dict(id='venue', name='Performance or event venue', cat='entertainment & assembly', her=[['entertainment & assembly', 1]], z='Entertainment: Indoor', zs='CB', size=[2000, 15000],
         note='Live entertainment is not permitted in C-1 except as an accessory use (conditional).'),
    dict(id='office', name='Office', cat='office', her=[['office', 1]], z='Office', zs='P', size=[300, 10000], note=''),
    dict(id='workshop', name='Maker workshop with a counter', cat='production & light industry', her=[['production & light industry', 1]], z='Arts Studio: Industrial', zs='P', size=[500, 6000],
         note='General light industry is not permitted in C-1.'),
    dict(id='community', name='Community, health or nonprofit space', cat='institutional & religious', her=[['institutional & religious', 1]], z='Community Center; Health-Care Clinic', zs='CB', size=[1000, 10000], note=''),
    dict(id='housing', name='Housing (rowhouse or upper floors)', cat='residential', her=[['residential', 1]], z='Dwelling: Rowhouse; Above Non-Residential Ground Floor', zs='P', size=[600, 100000], note=''),
]
data['zoning_src'] = 'https://codes.baltimorecity.gov/us/md/cities/baltimore/code/32/zoning-tables/10-301'
data['urp_src'] = 'https://www.baltimorecity.gov/media/document/waverlybusinessareaurppdf'

# draft concepts for three empty buildings (hand-written, every fact linked to a source)
C = json.load(open(os.environ.get('PTU_CONCEPTS') or os.path.join(HERE, 'concepts.json'), encoding='utf-8'))
data['concepts'] = {k: C[k] for k in C['order']}
data['concept_order'] = C['order']
data['concept_note'] = C['_note']
COMPS_DIR = os.path.join(REPO, 'team', 'comps')
# comps engine v1 (team/comps): rent and revenue ranges; only the library rows the page cites are kept
_cp = os.path.join(COMPS_DIR, 'comps_ranges.json')
if os.path.exists(_cp):
    _comps = json.load(open(_cp, encoding='utf-8'))
    _srcs = _comps.pop('sources')
    _cited = set(re.findall(r'\b[RBO]-\d{3}\b', json.dumps(_comps)))
    _comps['sources'] = {k: v for k, v in _srcs.items() if k in _cited}
    data['comps'] = _comps

# extra layers: the sponsor's storefront check, heritage revivals, retail broken down, survey photos (extras.py)
sys.path.insert(0, HERE)
import extras  # noqa: E402
extras.apply(REPO, data, {'brands': os.environ.get('PTU_PRIVATE_BRANDS'), 'sizes': os.environ.get('PTU_PRIVATE_SIZES')})
# The mix today is a share of the storefronts in use, as the 1920-23 mix is a share of the buildings with a listed
# business: a lived-in house is not in either base. (Until 21 November 2026 the houses were in today's base, which
# made every storefront use look a little rarer today than it is.) One business in two street numbers counts once.
_now_base = sum(1 for q in data['props'] if q['occ'] and q['availability'] != 'house' and not q['same_as'])
for _m in data['mix']:
    _m['now_base'] = _now_base
_fn = data['frontage_now']
data['lib']['waverly']['vacancy_note'] = (LIB['waverly']['vacancy_note'].rstrip() + f" On this frontage, E 29th to E 33rd St, {_fn['vacant']} of "
                                          f"{_fn['storefronts']} storefronts are empty on the tenant list, which follows the sponsor's storefront "
                                          f"audit of November 2026 ({_fn['houses']} of the {len(data['props'])} parcels are houses).")
page = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
blob = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
assert page.count('__DATA__') == 1
html = page.replace('__DATA__', blob)
if not os.environ.get('PTU_BARE'):
    html = ('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + html + '\n</html>\n')
OUT = os.environ.get('PTU_OUT') or os.path.join(HERE, 'index.html')
open(OUT, 'w', encoding='utf-8').write(html)
print('wrote', os.path.basename(OUT) + ',', len(html) // 1024, 'KB;', 'props', len(data['props']), data['totals'], data['silence'])
print([(m['cat'], m['then'], m['then_base'], m['now'], m['now_base']) for m in data['mix']])
print(data['validation'])
print(collections.Counter(s['cand1'].split(' - ')[0] for s in screen).most_common())
print('one business in two numbers:', {props[k]['address']: props[v]['address'] for k, v in same_as.items()})
print('backtest', [(b['cut'], b['n'], b['hit'], b['base']) for b in data['backtest']], 'summaries', n_summary)
