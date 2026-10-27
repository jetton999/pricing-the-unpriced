"""Extra per-parcel layers for the explorer, shared by the build scripts (standard library only).

- storefront: the sponsor's October 2026 storefront assessments (storefront_assessments.csv) next to the team's
  own tenant check; fills the records our check could not confirm, and marks houses with no shop front.
- revivals: the longest-documented business names at each address (team/extractor/out/evidence.csv), for the
  "heritage revival" idea in PROJECT_IDEAS.md (reopen under a documented name, after a trademark check).
- retail: retail broken down into seven trades: what each building and the street have carried
  (evidence.csv), plus the modern version, usual size and cautions (retail_types.json, every claim sourced). The
  public files name no brand as a reference (sponsor, 26 Oct 2026: brand names go in reports only); a private build
  can pass a brands file kept outside the repo.
- photos: how many 2026 survey photos the sponsor has filed on each building (property_images.csv).
- legacy: how long the business there today has been at the address, where a record or the checks say so, so
  that plans can be read with long-standing businesses in view (an anti-displacement aid, not a score input).
- sizes: the typical floor area of each use (typical_sqft.json, every figure sourced), for total rents.
- neighbourhoods: the sponsor's benchmark set (research/neighbourhoods_2026-10-26.json): asking rents made
  triple-net equivalent with the comps engine's allowances, vacancy with its definition, residents, displacement,
  and how Greenmount compares. Waverly's own rents come from the comps library and its storefront vacancy from
  the sponsor's storefront assessments, so the comparison is computed, not typed.
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


def retail(repo, props, brands_file=None):
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
    private = {}
    if brands_file:                      # private build only: the reference brands live outside the repo
        with open(brands_file, encoding='utf-8') as fh:
            private = json.load(fh)['brands']
    for t in types['types']:
        t['fmt'] = RETAIL_FMT[t['id']]
        t['street'] = street.get(t['id'], 0)
        t['brands'] = [b for b in private.get(t['id'], []) if b.get('verified_operating')]
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


def apply(repo, data, private=None):
    """private: optional dict of files kept outside the repo, for the team's own build ({'brands': path, 'sizes': path})."""
    private = private or {}
    props = data['props']
    data['sa_stats'] = storefront(repo, props)
    revivals(repo, props)
    data['retail'] = retail(repo, props, private.get('brands'))
    data['sizes'] = sizes(private.get('sizes'))
    data['nbhd'] = neighbourhoods(repo, {p['id'] for p in props}, data['sizes']['formats']['shop']['typical'])
    photos(repo, props)
    data['legacy_stats'] = legacy(repo, props)


def sizes(private_file=None):
    """Typical floor area per use. The public file labels chains' filings by kind; a private copy may name them."""
    path = private_file or os.path.join(HERE, 'typical_sqft.json')
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)
    return dict(about=d['about'], brands=d['brands'], accessed_on=d['accessed_on'],
                formats={f['id']: f for f in d['formats']})


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


WAVERLY_ROWS = ('R-001', 'R-002', 'R-004')   # the comps library's ground-floor rows on Greenmount Ave in Waverly
RANGE_MAX = 1.25                              # a listing range wider than this is a summary of several spaces


def _nnn(r, loads):
    v = r.get('value')
    if v is None and r.get('value_low') is not None and r.get('value_high') is not None:
        if r['value_high'] / r['value_low'] > RANGE_MAX:
            return None
        v = (r['value_low'] + r['value_high']) / 2
    if v is None:
        return None
    return round(v - loads.get(r.get('lease_type') or 'unknown', loads['unknown']), 2)


def _vkind(d):
    """A short name for how a vacancy figure was measured, so different measures are never read as one."""
    d = d.lower()
    for key, name in (('storefronts counted on foot', 'storefronts counted on foot'),
                      ('counted from the desk', "storefronts counted from the desk (sponsor)"),
                      ('corridor survey', 'city corridor survey'), ('live xyz', 'storefront index (small businesses)'),
                      ('broker availability', 'broker availability'), ('costar', 'broker vacancy rate'),
                      ('broker vacancy', 'broker vacancy rate'), ('broker survey', 'broker survey'),
                      ('stated', 'stated by a local nonprofit'), ('buildings that appear', 'news count of empty buildings')):
        if key in d:
            return name
    return 'other'


def _first_last(rows):
    """Earliest and latest year of a resident indicator; several tracts in one year give their median."""
    by = collections.defaultdict(list)
    for r in rows or []:
        if r.get('value') is not None and r.get('year'):
            by[int(r['year'])].append(r['value'])
    if not by:
        return None
    y0, y1 = min(by), max(by)
    return dict(y0=y0, v0=_median(by[y0]), y1=y1, v1=_median(by[y1]), n_areas=max(len(v) for v in by.values()))


def storefront_vacancy(repo, frontage_ids):
    """Vacant storefront parcels / storefront parcels, from the sponsor's storefront assessments."""
    rows = _csv(os.path.join(repo, 'storefront_assessments.csv'))
    props = {r['id']: r for r in _csv(os.path.join(repo, 'properties.csv'))}
    VAC, OCC = ('vacant_storefront', 'listed_likely_dead'), ('open_active', 'office_industrial', 'institution')

    def rate(rs):
        v = sum(r['status'] in VAC for r in rs)
        o = sum(r['status'] in OCC for r in rs)
        return dict(vacant=v, storefronts=v + o, pct=round(100 * v / (v + o), 1) if v + o else None,
                    assessed_on=max((r['assessed_on'] for r in rs), default=''))
    return dict(frontage=rate([r for r in rows if r['property_id'] in frontage_ids]),
                greenmount=rate([r for r in rows if 'greenmount' in props.get(r['property_id'], {}).get('address', '').lower()]))


def neighbourhoods(repo, frontage_ids, typical_shop_sqft):
    with open(os.path.join(HERE, 'research', 'neighbourhoods_2026-10-26.json'), encoding='utf-8') as fh:
        src = json.load(fh)
    with open(os.path.join(repo, 'team', 'comps', 'engine_inputs.json'), encoding='utf-8') as fh:
        loads = {k: v for k, v in json.load(fh)['lease_basis_loads'].items() if isinstance(v, (int, float))}
    lib = {r['row_id']: r for r in _csv(os.path.join(repo, 'team', 'comps', 'library', 'rents.csv'))}
    sv = storefront_vacancy(repo, frontage_ids)
    out = []
    for n in src['neighbourhoods']:
        n = json.loads(json.dumps(n))
        if n['id'] == 'waverly-greenmount':
            for rid in WAVERLY_ROWS:
                r = lib[rid]
                n['retail_asking_rents'].append(dict(
                    value=float(r['asking_rent_usd_per_sqft_yr']), value_low=None, value_high=None, unit='$/sq ft/yr',
                    lease_type=r['rent_basis'], kind='listing' if r['figure_type'] == 'asking' else 'rent being paid',
                    area=r['address'], sqft=int(r['space_sqft']) if r['space_sqft'] else None, date=r['figure_year'],
                    source_url=r['source_url'], source_title=r['source_title'], accessed_on=r['accessed_on'], row=rid))
            for i, (key, label) in enumerate((('frontage', 'Greenmount Ave, E 29th to E 33rd St (this frontage)'),
                                              ('greenmount', 'Greenmount Ave, all blocks the sponsor assessed (2300 to 3700)'))):
                x = sv[key]
                n['retail_vacancy'].insert(i, dict(
                    value_pct=x['pct'], definition="storefront parcels counted from the desk (the sponsor's storefront assessment)",
                    area=label, date=x['assessed_on'][:7], count_note=f"{x['vacant']} of {x['storefronts']} storefront parcels vacant",
                    source_url='storefront_assessments.csv', source_title="Sponsor's storefront assessments (data package, Oct 2026)",
                    accessed_on=x['assessed_on']))
        for v in n['retail_vacancy']:
            v['kind'] = _vkind(v['definition'])
        used, ctx = [], []
        for r in n['retail_asking_rents']:
            v = _nnn(r, loads) if r.get('kind') in ('listing', 'rent being paid') else None
            r['nnn_equiv'] = v
            (used if v is not None else ctx).append(r)
        vals = [r['nnn_equiv'] for r in used]
        med = _median(vals)
        res = {k: _first_last(v) for k, v in (n.get('residents') or {}).items()}
        n['short'] = SHORT.get(n['id'], n['name'])
        n['calc'] = dict(rent_median=round(med, 2) if med is not None else None, rent_n=len(vals),
                         rent_min=min(vals) if vals else None, rent_max=max(vals) if vals else None,
                         shop_year=round(med * typical_shop_sqft) if med is not None else None, residents=res)
        out.append(n)
    W = out[0]['calc']
    for n in out:
        c = n['calc']
        c['rent_x_waverly'] = round(c['rent_median'] / W['rent_median'], 2) if c['rent_median'] and W['rent_median'] else None
        inc = (c['residents'].get('median_household_income') or {}).get('v1')
        c['rent_per_10k_income'] = round(c['rent_median'] / (inc / 10000), 2) if c['rent_median'] and inc else None
    engine = {}
    cr = os.path.join(repo, 'team', 'comps', 'comps_ranges.json')
    if os.path.exists(cr):
        with open(cr, encoding='utf-8') as fh:
            for c in json.load(fh)['corridors']:
                engine['waverly-greenmount' if c['id'] == 'waverly' else c.get('district_id')] = dict(pooled=c['pooled'], n=c['n'], name=c['name'])
    return dict(about=src['about'], accessed_on=src['accessed_on'], loads=loads, range_max=RANGE_MAX,
                typical_shop_sqft=typical_shop_sqft, storefront_vacancy=sv, rows=out,
                compare=compare(out, sv, typical_shop_sqft, engine))


SHORT = {'waverly-greenmount': 'Greenmount', 'pigtown-washington-blvd': 'Pigtown', 'hampden-36th': 'Hampden',
         'ohio-city-cleveland': 'Ohio City', 'fishtown-philadelphia': 'Fishtown', 'u-street-dc': 'U Street',
         'melrose-hill-la': 'Melrose Hill', 'bedford-stuyvesant': 'Bed-Stuy'}


def _usd(x):
    if x >= 10000:
        return f"${round(x, -2):,.0f}"
    return f"${x:,.0f}" if x >= 100 else f"${x:,.2f}".replace('.00', '')


def _and(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def _day(iso):
    y, m, d = iso.split('-')
    return f"{int(d)} {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(m) - 1]} {y}"


def compare(rows, sv, shop, engine=None):
    """How Greenmount compares, in sentences built from the rows (so every number traces to a row)."""
    W, others = rows[0], rows[1:]
    w = W['calc']
    nm = lambda n: SHORT[n['id']]
    idx = lambda n: f"${n['calc']['rent_per_10k_income']:.2f}"
    rated = sorted((n for n in others if n['calc']['rent_median']), key=lambda n: n['calc']['rent_median'])
    cheap = all(w['rent_median'] < n['calc']['rent_median'] for n in rated)
    lo, hi = rated[0], rated[-1]
    thin = [n for n in rated if n['calc']['rent_n'] <= 2]
    out = [dict(k='Rent', t=(
        f"Ground-floor space on Greenmount asks about {_usd(w['rent_median'])} per sq ft a year, triple-net equivalent "
        f"({w['rent_n']} rows from the comps library). {'That is the lowest of the eight on listing medians' if cheap else 'Some ask less'}: "
        f"the others ask {lo['calc']['rent_x_waverly']:.1f} to {hi['calc']['rent_x_waverly']:.1f} times as much "
        f"({', '.join(nm(n) + ' ' + format(n['calc']['rent_x_waverly'], '.1f') for n in rated)}). "
        f"A typical {shop:,} sq ft shop would pay about {_usd(w['shop_year'])} a year here, {_usd(lo['calc']['shop_year'])} "
        f"in {nm(lo)} and {_usd(hi['calc']['shop_year'])} in {nm(hi)}."
        + (f" {_and(nm(n) for n in thin)} rest on one or two rows, so read those as rough." if thin else '')
        + (f" On the comps engine's corridor means, which adjust for the mix of uses listed, Greenmount and Pigtown are level "
           f"({_usd(engine['waverly-greenmount']['pooled'])} and {_usd(engine['pigtown-washington-blvd']['pooled'])}) and Hampden "
           f"is {_usd(engine['hampden-36th']['pooled'])}."
           if engine and all(k in engine for k in ('waverly-greenmount', 'pigtown-washington-blvd', 'hampden-36th')) else '')))]
    ri = sorted((n for n in rows if n['calc']['rent_per_10k_income']), key=lambda n: n['calc']['rent_per_10k_income'])
    near = [n for n in ri if n is not W and n['calc']['rent_per_10k_income'] <= 1.15 * w['rent_per_10k_income']]
    far = [n for n in ri if n['calc']['rent_per_10k_income'] >= 1.6 * w['rent_per_10k_income']]
    out.append(dict(k='Rent against local incomes', t=(
        f"Set against what households nearby earn, the gap narrows: Greenmount asks {idx(W)} per sq ft for every $10,000 "
        f"of median household income"
        + (f", close to {_and(nm(n) + ' (' + idx(n) + ')' for n in near)}" if near else '')
        + (f"; {_and(nm(n) for n in far)} ask 1.6 times or more as much per dollar of local income" if far else '')
        + ". Low rent here partly reflects lower spending power nearby. Visitors and workers shop too, so this is a rough "
          "check, not a demand model.")))
    f, g = sv['frontage'], sv['greenmount']
    counted = lambda n: n['retail_vacancy'] and (n['retail_vacancy'][0]['definition'].startswith('storefronts counted')
                                                 or 'corridor survey' in n['retail_vacancy'][0]['definition'])
    counts = [f"{nm(n)}'s {'on-foot count' if n['retail_vacancy'][0]['definition'].startswith('storefronts') else 'city survey'} "
              f"found {n['retail_vacancy'][0]['value_pct']:.0f}% ({n['retail_vacancy'][0]['date'][:4]})"
              for n in others if counted(n)]
    none = [nm(n) for n in others if not n['retail_vacancy']]
    out.append(dict(k='Vacancy', t=(
        f"{f['vacant']} of {f['storefronts']} storefront parcels on this stretch are empty ({f['pct']:.0f}%, the sponsor's "
        f"assessment of {_day(f['assessed_on'])}), and {g['pct']:.0f}% along all of Greenmount ({g['vacant']} of {g['storefronts']}). "
        + (f"{_and(counts)}. " if counts else '')
        + "Broker availability rates (DC and Hollywood, 7 to 9%) measure something else and run lower"
        + (f"; {_and(none)} have no published count." if none else '.'))))
    inc = lambda n: (n['calc']['residents'].get('median_household_income') or {}).get('v1')
    blk = lambda n: (n['calc']['residents'].get('black_share_pct') or {}).get('v1')
    by_inc = sorted((n for n in rows if inc(n)), key=inc)
    top_black = max((n for n in rows if blk(n) is not None), key=blk)
    low3 = by_inc[:3]
    y1 = W['calc']['residents']['black_share_pct']['y1']
    fish = next(n for n in rows if n['id'] == 'fishtown-philadelphia')
    out.append(dict(k='Residents', t=(
        f"{'Waverly has the highest Black share of the eight' if top_black is W else 'Waverly is majority-Black'} "
        f"({blk(W):.0f}%, {str(y1 - 4) + '-' + str(y1)[2:] if y1 == 2023 else y1} estimate) and "
        f"{'one of the three lowest' if W in low3 else 'a middle'} median household incomes ({_usd(inc(W))}), "
        f"with {_and(nm(n) + ' (' + _usd(inc(n)) + ')' for n in low3 if n is not W)}. Fishtown's is {_usd(inc(fish))}.")))
    high = [n for n in rows if n['displacement_rating'] == 'high']
    rest = {n['displacement_rating'] for n in rows if n not in high}
    out.append(dict(k='Displacement', t=(
        f"Waverly rates {W['displacement_rating']}: prices and rents are up and the Black share fell "
        f"{W['calc']['residents']['black_share_pct']['v0'] - blk(W):.1f} points since 2010. "
        f"The places rated high, {_and(nm(n) for n in high)}, lost a large share of their Black residents, and their asking "
        f"rents today are {min(n['calc']['rent_x_waverly'] for n in high):.1f} to {max(n['calc']['rent_x_waverly'] for n in high):.1f} "
        f"times Greenmount's. The rest of the set rates {_and(sorted(rest))}.")))
    out.append(dict(k='What it means', t=(
        "In dollars, Greenmount and Pigtown are the cheapest places in the set to open a shop, well under the other "
        "corridors they are compared with, Hampden and Ohio City included. The discount comes with the highest vacancy and among the lowest incomes nearby, so a plan "
        "has to bring customers as well as tenants. For a single use, the rent it could support (Money tab) is a better "
        "guide than asking rents elsewhere.")))
    return out
