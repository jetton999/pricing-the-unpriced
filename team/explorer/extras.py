"""Extra per-parcel layers for the explorer, shared by the build scripts (standard library only).

- storefront: the sponsor's October 2026 storefront assessments (storefront_assessments.csv) next to the team's
  own tenant check; fills the records our check could not confirm, and marks houses with no shop front.
- revivals: the longest-documented business names at each address (team/extractor/out/evidence.csv), for the
  "heritage revival" idea in PROJECT_IDEAS.md (reopen under a documented name, after a trademark check).
- retail: retail broken down into seven trades: what each building and the street have carried
  (evidence.csv), plus the modern version and reference brands (retail_types.json, every claim sourced).
- photos: how many 2026 survey photos the sponsor has filed on each building (property_images.csv).
- legacy: how long the business there today has been at the address, where a record or the checks say so, so
  that plans can be read with long-standing businesses in view (an anti-displacement aid, not a score input).
"""
import collections
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

SA_LABEL = {'open_active': 'open business', 'residential': 'house, no shop front', 'vacant_storefront': 'vacant storefront',
            'vacant_lot': 'vacant lot', 'institution': 'church or institution', 'office_industrial': 'office or workshop',
            'listed_likely_dead': 'listed, probably closed', 'needs_eyes': 'needs a look'}

RETAIL_RX = {
    'furniture_home': r'\bfurnitur|\bfurnish(?!ing goods)|\bupholster|\bcarpets?\b|\brugs?\b|\bmattress|\bbedding\b|\bappliances?\b|\bradios?\b|\btelevisions?\b',
    'clothing': r'\bcloth(es|ing|iers?)\b|\bapparel|\bdress(es|maker|making)?\b|\bmen.?s ?(wear|furn)|\btailor|\bhaberdash|\bfashions?\b|\bhosiery|\bmillin|\bdry goods|\bshoes?\b|\bboots?\b|\bjewel|\bwatch(es| repair)',
    'grocery': r'\bgrocer|\bmarket\b|\bmeats?\b|\bbutcher|\bproduce\b|\bdelicatessen|\bdeli\b|\bfruits?\b|\bdairy\b|\bconfection|\bcandy\b',
    'hardware': r'\bhardware|\bpaints?\b|\bplumb|\blumber|\belectrical suppl',
    'pharmacy': r'\bdrug ?stores?\b|\bdrugs\b|\bdruggists?\b|\bpharmac|\bapothec|\boptic',
    'books_music': r'\bbooks?(store|shop|s)?\b|\brecord (shop|store)|\bmusic\b|\bstationer|\bnews ?(stand|dealer)',
    'gifts_makers': r'\bgifts?\b|\bnovelt|\bnotions\b|\bvariety\b|\bcrafts?\b|\bantiques?\b|\bflorist',
}
RETAIL_FMT = {'furniture_home': 'showroom', 'clothing': 'shop', 'grocery': 'shop', 'hardware': 'showroom', 'pharmacy': 'shop',
              'books_music': 'shop', 'gifts_makers': 'shop'}
NAME_JUNK = re.compile(r'\b(co|company|inc|incorporated|corp|corporation|the|and|&|llc|bros|brothers)\b\.?', re.I)


def _csv(path):
    with open(path, encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def storefront(repo, props):
    rows = {r['property_id']: r for r in _csv(os.path.join(repo, 'storefront_assessments.csv'))}
    filled = disagree = houses = 0
    for p in props:
        s = rows.get(p['id'])
        if not s:
            continue
        try:
            ev = json.loads(s['evidence'])
        except ValueError:
            ev = []
        sv = max((e.get('as_of', '') for e in ev if e.get('source') == 'photos'), default='')
        summ = re.split(r'(?<=[.!?])\s', s['summary'].strip())[0][:220]
        p['sa'] = dict(st=s['status'], label=SA_LABEL.get(s['status'], s['status']), conf=s['confidence'], summary=summ, sv=sv[:7])
        if p['status'] == 'unknown':
            if s['status'] in ('open_active', 'institution', 'office_industrial'):
                p['availability'] = 'occupied'
                p['status_note'] = 'our check found no listing at this number; the sponsor found ' + SA_LABEL[s['status']]
                filled += 1
            elif s['status'] == 'residential':
                p['availability'] = 'house'
                houses += 1
        elif p['status'] == 'occupied' and s['status'] in ('vacant_storefront', 'vacant_lot', 'listed_likely_dead'):
            disagree += 1
            p['status_note'] = 'our check and the sponsor disagree: check on the walk-by'
        elif p['status'] in ('vacant', 'for lease') and s['status'] == 'open_active':
            disagree += 1
            p['status_note'] = 'our check and the sponsor disagree: check on the walk-by'
    return dict(filled=filled, houses=houses, disagree=disagree, n=sum(1 for p in props if 'sa' in p))


def _norm(name):
    n = NAME_JUNK.sub(' ', name.lower())
    return re.sub(r'[^a-z0-9 ]', ' ', re.sub(r'\s+', ' ', n)).strip()


def revivals(repo, props):
    ids = {p['id'] for p in props}
    g = collections.defaultdict(lambda: dict(names=collections.Counter(), years=[], cats=collections.Counter(), refs=[]))
    for e in _csv(os.path.join(repo, 'team', 'extractor', 'out', 'evidence.csv')):
        b = (e.get('business') or '').strip()
        if e['property_id'] not in ids or not b or not e.get('year', '').isdigit():
            continue
        if e.get('use_category') in ('residential', 'institutional & religious', 'office', '') or len(_norm(b)) < 3:
            continue
        k = (e['property_id'], _norm(b))
        g[k]['names'][b] += 1
        g[k]['years'].append(int(e['year']))
        g[k]['cats'][e['use_category']] += 1
        if e.get('source_ref'):
            g[k]['refs'].append(e['source_ref'])
    per = collections.defaultdict(list)
    for (pid, _), v in g.items():
        ys = v['years']
        if len(ys) < 2:
            continue
        per[pid].append(dict(name=v['names'].most_common(1)[0][0], first=min(ys), last=max(ys), n=len(ys),
                             cat=v['cats'].most_common(1)[0][0], refs=sorted(set(v['refs']))[:4]))
    for p in props:
        c = sorted(per.get(p['id'], []), key=lambda r: (-min(r['n'], 10), -(r['last'] - r['first'])))   # best documented first
        c = [r for r in c if r['last'] < 2024]   # a business still trading is not a revival
        if c:
            p['rv'] = c[:2]


def retail(repo, props):
    ids = {p['id'] for p in props}
    rx = {k: re.compile(v, re.I) for k, v in RETAIL_RX.items()}
    hits = collections.defaultdict(lambda: collections.defaultdict(list))
    for e in _csv(os.path.join(repo, 'team', 'extractor', 'out', 'evidence.csv')):
        if e['property_id'] not in ids or e.get('use_category') not in ('retail goods', 'food & drink'):
            continue
        text = ' '.join([e.get('business') or '', e.get('use_subcategory') or '', e.get('matched_keyword') or '', e.get('text') or ''])
        for k, r in rx.items():
            if k != 'grocery' and e['use_category'] != 'retail goods':
                continue
            if r.search(text):
                hits[e['property_id']][k].append((int(e['year']) if e.get('year', '').isdigit() else None, (e.get('business') or '').strip()))
    street = collections.Counter()
    for p in props:
        h = hits.get(p['id'], {})
        out = {}
        for k, lst in h.items():
            ys = [y for y, _ in lst if y]
            names = collections.Counter(n for _, n in lst if n)
            out[k] = [len(lst), min(ys) if ys else None, max(ys) if ys else None, names.most_common(1)[0][0] if names else '']
            street[k] += 1
        if out:
            p['rt'] = out
    with open(os.path.join(HERE, 'retail_types.json'), encoding='utf-8') as fh:
        types = json.load(fh)
    for t in types['types']:
        t['fmt'] = RETAIL_FMT[t['id']]
        t['street'] = street.get(t['id'], 0)
        t['brands'] = [b for b in t['brands'] if b.get('verified_operating')]
    return dict(types=types['types'], context=types.get('corridor_context', []), accessed_on=types.get('accessed_on'))


def photos(repo, props):
    ids = {p['id'] for p in props}
    c = collections.defaultdict(set)
    for r in _csv(os.path.join(repo, 'property_images.csv')):
        if r['property_id'] in ids and r['folder'] == 'pikl-greenmount':
            c[r['property_id']].add(r['image_key'])
    for p in props:
        if c.get(p['id']):
            p['ph'] = len(c[p['id']])


TENURE_SOURCES = ('dhcd_1970s', 'polk_directory', 'permit_card', 'sponsor:newspapers_com', 'sponsor:mdlandrec', 'sponsor:polk',
                  'sponsor:census_directory', 'sponsor:local_news')   # dated per record; white papers are dated to the building
TENURE_LABEL = {'dhcd_1970s': '1970s city housing file', 'polk_directory': 'Polk directory', 'permit_card': 'permit card',
                'sponsor:newspapers_com': 'newspaper item', 'sponsor:mdlandrec': 'land record', 'sponsor:polk': 'Polk directory',
                'sponsor:census_directory': 'census directory', 'sponsor:local_news': 'local news item'}
NAME_STOP = {'greenmount', 'baltimore', 'store', 'shop', 'the', 'and', 'of', 'market', 'deli', 'grocery', 'inc', 'llc'}
SINCE = re.compile(r"\b(?:since|opened in|open since|founded in|in business since)\s+((?:19|20)\d\d)\b", re.I)
YEARS = re.compile(r"\b(?:owner|run|open|trading|here|tenant)\b[^.]{0,30}?\b(?:of|for)\s+(?:about\s+|over\s+|more than\s+)?(\d{1,2})\s+years", re.I)


def _toks(name):
    return {t for t in _norm(name).split() if len(t) > 2 and t not in NAME_STOP}


def legacy(repo, props, now_year=2026, min_years=15):
    """Earliest year the business there today is documented at the address (records, tenant check, sponsor's check)."""
    byid = {p['id']: p for p in props}
    gaps = _csv(os.path.join(repo, 'team', 'evidence', 'blocklot_gaps.csv'))
    merged = {g['property_id']: g['current_property_id'] for g in gaps if g['current_property_id']}
    recs = collections.defaultdict(list)
    for e in _csv(os.path.join(repo, 'team', 'extractor', 'out', 'evidence.csv')):
        if e.get('business') and e.get('year', '').isdigit() and e['source'] in TENURE_SOURCES:
            recs[merged.get(e['property_id'], e['property_id'])].append((int(e['year']), e['business'], e['source'], e.get('source_ref', '')))
    sa = {r['property_id']: r for r in _csv(os.path.join(repo, 'storefront_assessments.csv'))}
    n = 0
    for t in _csv(os.path.join(repo, 'team', 'tenants', 'current_tenants_2026-10.csv')):
        pid = merged.get(t['property_id'], t['property_id'])
        p = byid.get(pid)
        types = {x for x in (t['business_type'] or '').split(' ; ') if x}
        if not p or t['status'] != 'occupied' or not types or types <= {'institutional & religious'}:
            continue   # public and religious uses are not at risk from rents in the same way
        found = []
        for nm in [x.strip() for x in re.split(r'[;(]', t['tenant_name']) if x.strip()]:
            tk = _toks(nm)
            for y, bn, src, ref in recs.get(pid, []):
                if tk and len(tk & _toks(bn)) >= min(2, len(tk)):
                    found.append((y, f"{nm} in a {TENURE_LABEL.get(src, src)}, {y}"))
        for txt, label in ((t.get('notes') or '', "team's tenant check"), ((sa.get(pid) or {}).get('summary') or '', "sponsor's storefront check")):
            m = SINCE.search(txt)
            if m:
                found.append((int(m.group(1)), f'{label}: "since {m.group(1)}"'))
            m = YEARS.search(txt)
            if m and 0 < int(m.group(1)) < 80:
                found.append((now_year - int(m.group(1)), f'{label}: "{m.group(1)} years"'))
        if found:
            y, basis = min(found)
            yrs = now_year - y
            p['since'] = dict(year=y, years=yrs, basis=basis, legacy=yrs >= min_years, name=re.split(r'[;(]', t['tenant_name'])[0].strip())
            n += p['since']['legacy']
    return dict(legacy=n, min_years=min_years)


def apply(repo, data):
    props = data['props']
    data['sa_stats'] = storefront(repo, props)
    revivals(repo, props)
    data['retail'] = retail(repo, props)
    photos(repo, props)
    data['legacy_stats'] = legacy(repo, props)
