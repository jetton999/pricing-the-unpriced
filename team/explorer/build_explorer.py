#!/usr/bin/env python3
"""Build team/explorer/index.html, the Greenmount frontage explorer, from the repo's extractor v1 outputs.

Run from anywhere:  python3 team/explorer/build_explorer.py
Inputs: team/extractor/out, team/evidence, team/tenants, team/week1/out, properties.csv, property_incidents.csv,
and the two hand-made files beside this script (concepts.json, library.json). Output: index.html beside this script.

Same schema as screen_v0.py's explorer_data.json, so the page template keeps working.
Standard library only."""
import csv, json, collections, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
X = os.path.join(REPO, 'team', 'extractor', 'out')
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
    for c in cs:
        side_mix[props[cur]['block_side_id']][c] += 1
        corr_mix[c] += 1

BENCH = {
    'food & drink': dict(small=(25.0, 37.5), large=(15.0, 25.0),
                         note='Rent: fitted 800 SF cafe suites in Hampden ask $30-37.50/SF NNN (CAFE-01, CAFE-02); the 3226 rent roll implies at least $25.23/SF gross (CAFE-04). Sales: an owner-run Baltimore tea cafe reported $250k-285k a year (CAFE-03).'),
    'retail goods': dict(small=(20.0, 30.0), large=(10.9, 20.0),
                         note='Rent: large-format space asks $17-20/SF NNN in Hampden (SHOW-03, SHOW-04); a fully leased 14,000 SF 1920s building earns about $10.91/SF incl. CAM (SHOW-05). Sales: $167-185 per SF of showroom (SHOW-08, Havertys 10-K).'),
}
NOT_CAND = {'residential', 'institutional & religious', 'vacant'}

by = collections.defaultdict(list)
for e in ev:
    by[e['property_id']].append(e)

# proven uses from stated trades only (a bare "store" is a shop front, not a use)
proven = collections.defaultdict(list)
for pid, es in by.items():
    g = collections.defaultdict(list)
    for e in es:
        if e['use_category'] and e['year'] and e['use_subcategory'] != GENERIC:
            g[e['use_category']].append(e)
    for c, rows in g.items():
        decs = sorted({int(r['decade']) for r in rows})
        srcs = {r['source'].split(':')[0] for r in rows}
        bar = sum(1 for r in rows if r['use_subcategory'] == 'bar / tavern')
        proven[pid].append(dict(cat=c, nd=len(decs), ne=len(rows), first=min(int(r['year']) for r in rows),
                                last=max(int(r['year']) for r in rows), strong=len(decs) >= 2 or len(srcs) >= 2,
                                bar_share=bar / len(rows), nsrc=len(srcs)))

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
            why += '; most of the record is a saloon or tavern, and a new tavern is barred by the urban renewal plan (restaurant or cafe allowed)'
        cands.append(dict(use=r['cat'], format=fmt, score=round(2 * r['nd'] + min(r['ne'], 20) / 5 - pen, 2), why=why))
    cands.sort(key=lambda x: -x['score'])
    if not cands and any(r['cat'] == 'residential' for r in proven[pid]):
        cands = [dict(use='residential', format='no commercial use on record', score=0, why='only dwelling evidence so far')]
    econ = ''
    if cands and cands[0]['use'] in BENCH and sqft:
        b = BENCH[cands[0]['use']]
        lo, hi = b['large'] if sqft >= 5000 else b['small']
        econ = f"indicative rent ${sqft * lo / 1000:,.0f}k-${sqft * hi / 1000:,.0f}k/yr at ${lo:g}-{hi:g}/SF. " + b['note']
    pv = sorted([r for r in proven[pid] if r['strong']], key=lambda r: -r['nd'])
    screen.append(dict(pid=pid, address=p['address'], side=side, sqft=sqft or '', zoning=p['zoning_code'],
                       sponsor=p['matterport_tour'] == 'yes', status=status, tenant=t['tenant_name'],
                       uses_now=' ; '.join(cats_now(t)), availability=avail, evidence=sil[pid]['status'],
                       decades=int(sil[pid]['decades_all_sources']),
                       proven=' ; '.join(f"{r['cat']} ({r['nd']}d)" for r in pv),
                       cand1=(cands[0]['use'] + (' - ' + cands[0]['format'] if cands[0]['format'] else '')) if cands else '',
                       cand1_why=cands[0]['why'] if cands else '',
                       cand2=(cands[1]['use'] + (' - ' + cands[1]['format'] if cands[1]['format'] else '')) if len(cands) > 1 else '',
                       econ=econ))
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

SRC = {'polk_directory': 'Polk directory', 'permit_card': 'permit card', 'sanborn': 'Sanborn map',
       'nr_inventory': 'NR inventory', 'dhcd_1970s': '1970s DHCD file', 'current_2026': '2026 tenant check'}
DOM = ['food & drink', 'retail goods', 'personal services', 'automotive', 'entertainment & assembly',
       'institutional & religious', 'production & light industry', 'office', 'residential']
data = dict(props=[], generated='2026-10-18')
for s in screen:
    pid = s['pid']
    g = geo.get(pid, {})
    es = sorted(by[pid], key=lambda e: int(e['year'] or 0))
    strip = {}
    for e in es:
        if e['use_category'] in DOM and e['decade'] and e['use_subcategory'] != GENERIC:
            strip.setdefault(int(e['decade']), collections.Counter())[e['use_category']] += 1
    shown = [e for e in es if e['use_category'] or e['kind'] in ('business listed', 'current', 'building')]
    data['props'].append(dict(
        id=pid, address=s['address'].replace(' Greenmount Ave', ''), side=s['side'], sqft=s['sqft'], zoning=s['zoning'],
        sponsor=s['sponsor'], status=s['status'], tenant=s['tenant'], uses_now=s['uses_now'],
        availability=s['availability'], evidence=s['evidence'], decades=s['decades'], proven=s['proven'],
        cand1=s['cand1'], cand1_why=s['cand1_why'], cand2=s['cand2'], econ=s['econ'],
        lat=float(g.get('latitude') or 0), lon=float(g.get('longitude') or 0), ring=ring(pid),
        h={r['cat']: [r['nd'], r['ne'], r['nsrc'], r['first'], r['last'], round(r['bar_share'], 2)] for r in proven[pid] if r['cat'] != 'vacant'},
        story=story.get(pid, [0, 0]), now=sorted(c for c in parcel_now[pid] if c != 'vacant'), occ=pid in occupied,
        strip={str(d): c.most_common(1)[0][0] for d, c in strip.items()},
        ev=[dict(y=e['year'], src=SRC.get(e['source'], e['source'].replace('sponsor:', 'sponsor ').replace('_', ' ')),
                 cat=e['use_category'] + (' (shop front)' if e['use_subcategory'] == GENERIC else ''),
                 t=((e['business'] + ' - ') if e['business'] and e['source'] != 'polk_directory' else '') + e['text'][:160],
                 ref=e['source_ref'], url=e['url'], m=e['address_method'] if e['basis'] == 'inferred' else '')
            for e in shown][:150]))

srcs = collections.Counter(e['source'].split(':')[0] for e in ev)
data['totals'] = dict(srcs)
st = collections.Counter(s['status'] for s in sil.values())
mean = lambda k: round(sum(int(s[k]) for s in sil.values()) / len(sil), 1)
data['silence'] = dict(before=mean('decades_sponsor_only'), after=mean('decades_all_sources'), status=dict(st))
val = open(os.path.join(X, 'validation.md'), encoding='utf-8').read()
m = re.search(r'\| all sources \| (\d+) \| (\d+) \| (\d+)% \| (\d+)% \| (\d+) \| (\d+)% \|', val)
m2 = re.search(r'\| new sources only[^|]*\| (\d+) \| (\d+) \| (\d+)% \| (\d+)% \| (\d+) \| (\d+)% \|', val)
data['validation'] = (f"Against the four hand-built reference timelines, the extractor finds {m.group(4)}% of the reference uses where a "
                      f"source covers those years, and {m.group(6)}% of its {m.group(5)} coded records agree with the reference category. "
                      f"From the new sources alone: {m2.group(4)}% and {m2.group(6)}% of {m2.group(5)}. The references were built from the "
                      f"same sponsor records, so four blind reference timelines are still needed.")

# the mix then (Polk 1920-23, buildings with a coded line) and now (occupied in Oct 2026)
then = collections.defaultdict(set)
base_then = set()
for e in ev:
    if e['source'] == 'polk_directory' and e['year'] and 1920 <= int(e['year']) <= 1923 and e['use_category'] \
            and e['use_subcategory'] != GENERIC:
        base_then.add(e['property_id'])
        then[e['use_category']].add(e['property_id'])
occ = sorted(occupied)
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
OWNER_KIND = lambda n: ('sponsor-linked LLC' if '2631 GREENMOUNT' in n.upper() else
                        'company' if any(k in n.upper() for k in ('LLC', ' INC', 'CORP', 'COMPANY', 'TRUST', 'REALTY', 'LIMITED', 'NET-LEASED', 'HOMES', 'HOUSING', 'CAPITAL', 'INVESTMENT')) else
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
                      walk=q['sponsor'])
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
LIB = json.load(open(os.path.join(HERE, 'library.json'), encoding='utf-8'))
data['lib'] = {k: LIB[k] for k in ('buildings', 'districts', 'waverly', 'aversion', 'requested', 'adjacency', 'segments', 'history_value', 'match_lessons')}
# the page shows the sponsor's own rules; personal and ownership detail stays in the research report, not in shared page data
data['lib']['sponsor'] = {'guardrails': LIB['sponsor'].get('guardrails', []), 'goals': LIB['sponsor'].get('goals', [])}

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
data['n_summary'] = n_summary

# ---- candidate formats: heritage links, C-1 zoning status (Table 10-301), urban renewal plan, size range (team assumption)
data['formats'] = [
    dict(id='cafe', name='Cafe or sit-down restaurant', cat='food & drink', her=[['food & drink', 1]], z='Restaurant', zs='P', size=[800, 4000],
         note='Porch or sidewalk seating is outdoor dining: a conditional use in C-1 (Table 10-301, note 5).'),
    dict(id='counter', name='Take-away counter (coffee, ice cream)', cat='food & drink', her=[['food & drink', 1]], z='Carry-Out Food Shop', zs='CB', size=[250, 1500],
         note='Serving mostly to go in disposable containers makes it a carry-out food shop (zoning code 1-303).'),
    dict(id='foodmaker', name='Food maker with a shop (bakery, roaster, ice cream)', cat='food & drink', her=[['food & drink', 0.8], ['production & light industry', 0.8]], z='Food Processing: Light', zs='P', size=[1000, 6000], note=''),
    dict(id='tavern', name='Bar or tavern', cat='food & drink', her=[['food & drink', 1]], bar=True, z='Tavern', zs='CB', urp=True, size=[800, 5000],
         note='The urban renewal plan bars new taverns, liquor stores and pawnshops (since 4 Dec 1995).'),
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

# draft concepts for the three empty sponsor buildings (hand-written, every fact linked to a source)
C = json.load(open(os.path.join(HERE, 'concepts.json'), encoding='utf-8'))
data['concepts'] = {k: C[k] for k in C['order']}
data['concept_order'] = C['order']
data['concept_note'] = C['_note']
page = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
blob = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
assert page.count('__DATA__') == 1
html = ('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        + page.replace('__DATA__', blob) + '\n</html>\n')
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(html)
print('wrote index.html,', len(html) // 1024, 'KB;', 'props', len(data['props']), data['totals'], data['silence'])
print([(m['cat'], m['then'], m['then_base'], m['now'], m['now_base']) for m in data['mix']])
print(data['validation'])
print(collections.Counter(s['cand1'].split(' - ')[0] for s in screen).most_common())
print('backtest', [(b['cut'], b['n'], b['hit'], b['base']) for b in data['backtest']], 'summaries', n_summary)
