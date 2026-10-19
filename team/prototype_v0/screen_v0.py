#!/usr/bin/env python3
"""Prototype v0 screening: proven uses x today's mix x indicative economics, per frontage property.
Run after build_v0.py. Standard library only. Writes out/hbu_screen_v0.csv, out/validation_v0.txt,
out/explorer_data.json (for the explorer page)."""
import csv, json, collections, re
import os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get('REPO') or os.path.abspath(os.path.join(HERE, '..', '..'))
def rp(*a): return os.path.join(REPO, *a)
FRONTAGE_SIDES = {'65', '67', '68', '69', '70', '71', '72'}
def load_frontage():
    rows = list(csv.DictReader(open(rp('team', 'week1', 'out', 'focus_area_properties.csv'), encoding='utf-8-sig')))
    return [r for r in rows if r['block_side_id'] in FRONTAGE_SIDES]

props = {r['property_id']: r for r in load_frontage()}
fa = {r['property_id']: r for r in csv.DictReader(open(rp('team', 'week1', 'out', 'focus_area_properties.csv'), encoding='utf-8-sig'))}
ev = list(csv.DictReader(open(os.path.join(HERE, 'out', 'evidence_v0.csv'), encoding='utf-8')))
proven = list(csv.DictReader(open(os.path.join(HERE, 'out', 'proven_uses_v0.csv'), encoding='utf-8')))
sil = {r['property_id']: r for r in csv.DictReader(open(os.path.join(HERE, 'out', 'silence_map_v0.csv'), encoding='utf-8'))}
ten = {r['property_id']: r for r in csv.DictReader(open(rp('team', 'tenants', 'current_tenants_2026-10.csv'), encoding='utf-8'))}
geo = {r['id']: r for r in csv.DictReader(open(rp('properties.csv'), encoding='utf-8-sig'))}
permits = {r['image_id']: r['page_url'] for r in csv.DictReader(open(rp('team', 'evidence', 'permit_cards_1924_1961.csv'), encoding='utf-8'))}
POLK_ID = {'1912': 'baltimorecitydir1912rlpo', '1913': 'baltimorecitydir1913rlpo', '1914': 'baltimorecitydir1914rlpo',
           '1915': 'baltimorecitydir1915rlpo', '1917': 'baltimorecitydir1917rlpo', '1918': 'baltimorecitydir1918rlpo',
           '1920': 'baltimorecitydir1920rlpo', '1921': 'baltimorecitydir1921rlpo', '1922': 'polksbaltimoreci1922rlpo',
           '1923': 'polksbaltimoreci1923rlpo'}

def cats_now(t):
    if t['status'] in ('vacant', 'for lease'):
        return ['vacant']
    if t['status'] != 'occupied':
        return []
    return [c for c in (t['business_type'] or '').split(' ; ') if c]

# today's mix by block side
side_mix = collections.defaultdict(collections.Counter)
corr_mix = collections.Counter()
for pid, t in ten.items():
    for c in set(cats_now(t)):
        side_mix[props[pid]['block_side_id']][c] += 1
        corr_mix[c] += 1

BENCH = {
    'food & drink': dict(small=(25.0, 37.5), large=(15.0, 25.0),
                         note='Rent: fitted 800 SF cafe suites in Hampden ask $30-37.50/SF NNN (CAFE-01, CAFE-02); the 3226 rent roll implies at least $25.23/SF gross (CAFE-04). Sales: an owner-run Baltimore tea cafe reported $250k-285k a year (CAFE-03).'),
    'retail goods': dict(small=(20.0, 30.0), large=(10.9, 20.0),
                         note='Rent: large-format space asks $17-20/SF NNN in Hampden (SHOW-03, SHOW-04); a fully leased 14,000 SF 1920s building earns about $10.91/SF incl. CAM (SHOW-05). Sales: $167-185 per SF of showroom (SHOW-08, Havertys 10-K).'),
}
NOT_CAND = {'residential', 'institutional & religious', 'vacant'}

pv = collections.defaultdict(list)
for r in proven:
    pv[r['property_id']].append(r)

screen = []
for pid, p in props.items():
    t = ten[pid]
    sqft = int(float(p['structure_sqft'])) if p['structure_sqft'] else None
    side = p['block_side_id']
    now = cats_now(t)
    status = t['status']
    gm = t.get('google_maps_2026_10_18', '')
    avail = 'available now' if status in ('vacant', 'for lease') else (
        'possibly available' if status == 'unknown' else 'occupied')
    cands = []
    for r in pv[pid]:
        c = r['use_category']
        if c in NOT_CAND:
            continue
        if r['sources'].strip().startswith('permit_card') and ';' not in r['sources'] and int(r['n_evidence']) < 2:
            continue  # a single permit is not enough to call a use proven
        nd, ne = int(r['n_decades']), int(r['n_evidence'])
        score = 2 * nd + min(ne, 20) / 5
        sat = side_mix[side][c]
        pen = 3 if sat >= 3 else (1 if sat == 2 else 0)
        why = f"{ne} records across {nd} decade(s) ({r['first_year']}-{r['last_year']}); {sat} on this block side today"
        fmt = ''
        if c == 'retail goods' and sqft and sqft >= 5000:
            fmt = 'large-format retail / showroom'
        elif c == 'food & drink' and sqft and sqft <= 3000:
            fmt = 'small cafe / counter service'
        cands.append(dict(use=c, format=fmt, score=round(score - pen, 2), saturation=sat, why=why,
                          strength=r['strength']))
    cands.sort(key=lambda x: -x['score'])
    if not cands and any(r['use_category'] == 'residential' for r in pv[pid]):
        cands = [dict(use='residential', format='no commercial use on record', score=0, saturation=0,
                      why='only dwelling evidence so far', strength='')]
    econ = ''
    if cands and cands[0]['use'] in BENCH and sqft:
        b = BENCH[cands[0]['use']]
        lo, hi = b['large'] if sqft >= 5000 else b['small']
        econ = f"indicative rent ${sqft * lo / 1000:,.0f}k-${sqft * hi / 1000:,.0f}k/yr at ${lo:g}-{hi:g}/SF. " + b['note']
    screen.append(dict(property_id=pid, address=p['address'], block_side_id=side, structure_sqft=sqft or '',
                       zoning=p['zoning_code'], sponsor_building=fa.get(pid, {}).get('matterport_tour', ''),
                       status_2026=status, tenant_2026=t['tenant_name'], uses_2026=' ; '.join(now),
                       availability=avail, evidence_status=sil[pid]['status_after'],
                       decades_with_evidence=sil[pid]['decades_after'],
                       proven_uses=' ; '.join(f"{r['use_category']} ({r['n_decades']}d)" for r in sorted(pv[pid], key=lambda r: -int(r['n_decades']))),
                       candidate_1=(cands[0]['use'] + (' - ' + cands[0]['format'] if cands[0]['format'] else '')) if cands else '',
                       candidate_1_why=cands[0]['why'] if cands else '',
                       candidate_2=(cands[1]['use'] + (' - ' + cands[1]['format'] if cands[1]['format'] else '')) if len(cands) > 1 else '',
                       economics_note=econ))
screen.sort(key=lambda r: int(r['address'].split()[0]))
with open(os.path.join(HERE, 'out', 'hbu_screen_v0.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(screen[0].keys()))
    w.writeheader(); w.writerows(screen)

# ---------------- validation: do the NEW sources agree with the reference timelines?
REF = {  # decade -> categories, from team/week1 use_timelines.md (hand-built)
    '3117 Greenmount Ave': {1880: {'automotive'}, 1890: {'automotive'}, 1900: {'automotive'}, 1910: {'automotive'},
                            1920: {'automotive', 'retail goods'}, 1930: {'retail goods', 'automotive'},
                            1940: {'automotive', 'retail goods'}, 1950: {'automotive', 'retail goods'},
                            1960: {'retail goods'}, 1970: {'retail goods'}, 1980: {'retail goods'}, 1990: {'retail goods'}},
    '3200 Greenmount Ave': {1900: {'food & drink'}, 1910: {'food & drink'}, 1920: {'food & drink', 'retail goods'},
                            1930: {'food & drink', 'retail goods'}, 1940: {'food & drink'}, 1950: {'food & drink'},
                            1960: {'food & drink'}, 1970: {'food & drink'}, 1980: {'food & drink'}, 2010: {'food & drink'}},
    '3224 Greenmount Ave': {1900: {'personal services'}, 1910: {'personal services'}, 1920: {'personal services'},
                            1930: {'personal services', 'retail goods', 'automotive'}, 1940: {'retail goods'},
                            1950: {'retail goods'}, 1960: {'food & drink', 'retail goods'}, 1970: {'retail goods', 'food & drink'}},
}
lines = []
agree = total = 0
for a, ref in REF.items():
    new = [e for e in ev if e['address'] == a and e['source'] in ('polk_directory', 'permit_card') and e['use_category']]
    for e in new:
        if e['decade'] == '':
            continue
        d = int(e['decade'])
        ok = e['use_category'] in ref.get(d, set())
        total += 1; agree += ok
        lines.append(f"{a} | {e['year']} | {e['source']} | {e['use_category']} | {'AGREES' if ok else 'differs'} | {e['text'][:70]}")
lines.insert(0, f'New-source rows on the three frontage reference timelines: {agree}/{total} agree with the hand-built reference decade categories.')
open(os.path.join(HERE, 'out', 'validation_v0.txt'), 'w').write('\n'.join(lines) + '\n')
print(lines[0])

# ---------------- explorer JSON
def ring(pid):
    g = geo.get(pid, {})
    try:
        j = json.loads(g.get('lot_polygon') or 'null')
        return [[round(x, 6), round(y, 6)] for x, y in j['rings'][0]] if j else None
    except Exception:
        return None

def link(e):
    s, ref = e['source'], e['source_ref']
    if s == 'permit_card':
        m = re.search(r'image (\S+)', ref)
        return permits.get(m.group(1), '') if m else ''
    if s == 'polk_directory':
        return 'https://archive.org/details/' + POLK_ID.get(str(e['year']), '')
    if s == 'current_2026':
        return ref
    return ''

DOM = ['food & drink', 'retail goods', 'personal services', 'automotive', 'entertainment & assembly',
       'institutional & religious', 'production & light industry', 'office', 'residential']
data = dict(props=[], corridor_now=dict(corr_mix), polk_1920s={}, generated='2026-10-18')
c20 = collections.Counter(e['use_category'] for e in ev if e['source'] == 'polk_directory' and e['use_category'])
data['polk_1920s'] = dict(c20)
bys = collections.defaultdict(list)
for e in ev:
    bys[e['property_id']].append(e)
for s in screen:
    pid = s['property_id']
    g = geo.get(pid, {})
    es = sorted(bys[pid], key=lambda e: int(e['year'] or 0))
    strip = {}
    for e in es:
        if e['use_category'] and e['use_category'] in DOM and e['decade'] != '':
            strip.setdefault(int(e['decade']), collections.Counter())[e['use_category']] += 1
    data['props'].append(dict(
        id=pid, address=s['address'].replace(' Greenmount Ave', ''), side=s['block_side_id'], sqft=s['structure_sqft'],
        zoning=s['zoning'], sponsor=s['sponsor_building'] == 'yes', status=s['status_2026'], tenant=s['tenant_2026'],
        uses_now=s['uses_2026'], availability=s['availability'], evidence=s['evidence_status'],
        decades=int(s['decades_with_evidence']), proven=s['proven_uses'], cand1=s['candidate_1'],
        cand1_why=s['candidate_1_why'], cand2=s['candidate_2'], econ=s['economics_note'],
        lat=float(g.get('latitude') or 0), lon=float(g.get('longitude') or 0), ring=ring(pid),
        strip={str(d): c.most_common(1)[0][0] for d, c in strip.items()},
        ev=[dict(y=e['year'], src=e['source'].replace('sponsor:', 'sponsor ').replace('_', ' '),
                 cat=e['use_category'], t=((e['business'] + ' - ') if e['business'] and e['source'] != 'polk_directory' else '') + e['text'][:160],
                 ref=e['source_ref'], url=link(e), m=e['address_method'])
            for e in es if (e['use_category'] or e['evidence_kind'] in ('business listed', 'current'))][:80]))
json.dump(data, open(os.path.join(HERE, 'out', 'explorer_data.json'), 'w'), separators=(',', ':'))
print('explorer json bytes', len(json.dumps(data)))
print('availability', collections.Counter(s['availability'] for s in screen))
print('corridor now', corr_mix.most_common())
