#!/usr/bin/env python3
"""Merge the 26 October 2026 desk research into team/explorer/library.json (run once; kept for the record).

    python3 team/explorer/research/merge_2026-10-26.py

Inputs, beside this script: districts_2026-10-26.json (19 corridors: displacement evidence, start
conditions, milestones, 2025-26 status), buildings_2026-10-26.json (32 reuse cases: cost, floor
area, timeline, financing, 2025-26 status) and new_districts_2026-10-26.json (3 corridors added).
Every value in them carries the URL of a page that was read on 2026-10-26. Standard library only.

What it changes:
- districts: adds displacement_evidence, milestones, status_now and start; re-rates displacement
  under the written rubric (library meta.displacement_rubric), keeping the old rating as
  displacement_v1; appends the three new corridors.
- buildings: adds cost (with cost per sq ft in 2025 dollars for US cases), timeline and
  financing_stack; updates floor area, operator model and status where a 2025-26 source says so,
  keeping the old values as *_previous.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB') or os.path.join(os.path.dirname(HERE), 'library.json')
DAY = '2026-10-26'

# CPI-U, U.S. city average, annual average = mean of the two semiannual values (FRED CUUS0000SA0).
# 2013-2025 as in team/comps/engine_inputs.json; 2002-2012 read from the same FRED table on 2026-10-26.
CPI = {2001: 177.05, 2002: 179.9, 2003: 183.95, 2004: 188.9, 2005: 195.3, 2006: 201.6, 2007: 207.3425,
       2008: 215.303, 2009: 214.537, 2010: 218.0555, 2011: 224.939, 2012: 229.594, 2013: 232.957,
       2014: 236.736, 2015: 237.017, 2016: 240.0075, 2017: 245.1195, 2018: 251.107, 2019: 255.6575,
       2020: 258.811, 2021: 270.9695, 2022: 292.655, 2023: 304.702, 2024: 313.689, 2025: 322.1145}
CPI_SOURCE = {'l': 'FRED, CPI-U U.S. city average, all items (CUUS0000SA0), semiannual', 'u': 'https://fred.stlouisfed.org/data/CUUS0000SA0'}

RUBRIC = {
    'high': 'A source ties a large loss of existing residents or businesses to the revival: a double-digit fall in '
            'the long-standing population share, or many households or long-standing businesses forced out. '
            'This holds whether or not protections came later.',
    'moderate': 'Sources show rising rents or prices, a smaller loss or the loss of one group, or a loss they do not '
                'tie to the revival.',
    'low': 'Sources describe protections that worked (affordability covenants, rent pacts, local or tenant '
           'ownership, buying only shop units) and no documented loss.',
    'unknown': 'No source addresses displacement. Unknown does not mean none.',
}

# The three added corridors, condensed from new_districts_2026-10-26.json (same sources).
NEW_TEXT = {
    'anacostia-mlk-marion-barry': dict(
        name='MLK Jr Ave SE and Marion Barry Ave SE, Historic Anacostia',
        historic='Anacostia Historic District (National Register 1978)',
        lead="ARCH Development Corp. (arts, 2007-13), the Anacostia BID (from 2012), DC's housing agency and partners (MLK Gateway), and the Douglass Community Land Trust.",
        outcomes="No vacancy series is published; a 2011 study found 'many' empty storefronts. The BID counted 25 new businesses in 2015; the Arts Center and Playhouse (2013) and MLK Gateway (150 office jobs, 2020) filled key corners.",
        displacement_note='The Black share of home-purchase mortgages east of the river fell from 92% to 75% (2007-21) while the Black share of homeowners slipped from 94% to 87%; a 230-unit land trust and business micro-grants came early.',
        lesson='Without buildings of its own, an arts nonprofit and a small BID took 15+ years to fill key corners. The transferable step: fund the land trust and business grants before the big capital project lands.'),
    'bronzeville-47th': dict(
        name='47th, 43rd and 51st Streets, Bronzeville',
        historic='Black Metropolis-Bronzeville District (Chicago Landmark 1998)',
        lead='Quad Communities Development Corp. (2003), the Bronzeville Retail Initiative with the Metropolitan Planning Council and LISC, Urban Juncture and Build Bronzeville, and the City through TIF districts.',
        outcomes='No storefront vacancy series exists; in 2012 about half the lots on 47th St were vacant land, mostly city-owned. Shops & Lofts at 47 (96 units, 55,000 sq ft) opened in 2014; Boxville hosted 64 local businesses in its first season (2017).',
        displacement_note="Median single-family prices rose nearly $200,000 (2018-22) against a 2024 median income of $40,692; a 2014 UIC study found the area 'improved but did not gentrify'; about 5,500 city-backed affordable units.",
        lesson='A mission owner bought cheap buildings early and tested tenants in $500-a-month containers while anchor projects took a decade. The city held about 90% of the vacant land, which Waverly does not have.'),
    'germantown-avenue': dict(
        name='Germantown Avenue, Germantown and Mt. Airy',
        historic='Colonial Germantown Historic District (National Historic Landmark 1965)',
        lead='Germantown United CDC (2011), the City Planning and Commerce departments, a business district (disbanded 2019), and Mt. Airy CDC (1980) with its business association.',
        outcomes='Central Germantown storefront vacancy moved from 21.5% (59 of 275, 2012) to 18% (50 of 282, 2023). Mt. Airy CDC rehabbed four buildings for $1.2M (2013); the publicly owned Town Hall and YWCA are still empty.',
        displacement_note='Median sale price up 142% to $184,000 (2012-22), still below the city median; the Black share stayed above 70% (2015-22); residents report neighbours leaving after rent rises.',
        lesson='A plan-and-grant approach with a thin CDC and no landlord role moved vacancy 3.5 points in eleven years while two public anchor buildings sat empty. Controlling a few key buildings matters more than another plan.'),
}


def load(name):
    with open(os.path.join(HERE, name), encoding='utf-8') as fh:
        return json.load(fh)


def add_sources(entry, urls):
    have = {s['u'] for s in entry.get('sources', [])}
    for label, url in urls:
        if url and url.startswith('http') and url not in have:
            entry.setdefault('sources', []).append({'l': label[:120], 'u': url})
            have.add(url)


def main():
    with open(LIB, encoding='utf-8') as fh:
        L = json.load(fh)
    D = {d['id']: d for d in load('districts_2026-10-26.json')}
    B = {b['id']: b for b in load('buildings_2026-10-26.json')}
    N = load('new_districts_2026-10-26.json')

    for d in L['districts']:
        r = D[d['id']]
        d['displacement_evidence'] = r['displacement_evidence']
        d['milestones'] = sorted(r.get('milestones') or [], key=lambda m: m.get('year') or 0)
        d['status_now'] = r.get('status_2025_26')
        d['start'] = r.get('start_conditions')
        st = r.get('start_conditions') or {}
        if d.get('start_vacancy_pct') is None and st.get('start_vacancy_pct') is not None:
            d['start_vacancy_pct'] = st['start_vacancy_pct']
        if d['displacement'] != r['displacement_rating_suggested']:
            d['displacement_v1'] = d['displacement']
        d['displacement'] = r['displacement_rating_suggested']
        d['displacement_reason'] = r['rating_reason']
        add_sources(d, [(e.get('source_title') or 'source', e.get('source_url')) for e in r['displacement_evidence']]
                    + [((d['status_now'] or {}).get('text', 'status')[:80], (d['status_now'] or {}).get('source_url'))])

    for r in N:
        t = NEW_TEXT[r['id']]
        L['districts'].append(dict(
            id=r['id'], name=t['name'], city=r['city'], country=r['country'], region='US', length_mi=r.get('length_mi'),
            storefronts=r.get('storefronts'), stock=None, historic=t['historic'], start_year=r.get('start_year'),
            start_vacancy_pct=r.get('start_vacancy_pct'), income=r.get('income'), majority_black=r.get('majority_black'),
            anchor_institution=r.get('anchor_institution'), concentrated_ownership=r.get('concentrated_ownership'),
            interventions=r.get('interventions') or [], lead=t['lead'], outcomes=t['outcomes'],
            vacancy_change=r.get('vacancy_change'), displacement=r['displacement'], displacement_note=t['displacement_note'],
            displacement_reason=t['displacement_note'], displacement_evidence=r.get('displacement_evidence') or [],
            milestones=sorted(r.get('milestones') or [], key=lambda m: m.get('year') or 0),
            status_now=r.get('status_2025_26'), lesson=t['lesson'], similarity=None, sources=r.get('sources') or [],
            added=DAY))

    for b in L['buildings']:
        r = B[b['id']]
        c = dict(r.get('cost') or {})
        lo, hi, tot = c.get('total_usd_low'), c.get('total_usd_high'), c.get('total_usd')
        mid = (lo + hi) / 2 if lo and hi else tot
        if r.get('sqft') and r.get('sqft') != b.get('sqft'):
            b['sqft_previous'] = b.get('sqft')
            b['sqft'] = r['sqft']
        sqft = b.get('sqft')
        if mid and sqft and b['country'] == 'USA' and c.get('cost_year') in CPI:
            c['per_sqft_2025'] = round(mid / sqft * CPI[2025] / CPI[c['cost_year']], 0)
            c['per_sqft_note'] = 'total / floor area, CPI-adjusted to 2025; not adjusted for local building costs'
        if mid:
            c['total_mid'] = mid
        b['cost'] = c if (mid or c.get('note')) else None
        b['timeline'] = r.get('timeline')
        b['financing_stack'] = r.get('financing_stack') or []
        s = r.get('status_2025_26') or {}
        if s.get('status'):
            if s['status'] != b.get('status'):
                b['status_previous'] = b.get('status')
            b['status'] = s['status']
            b['status_year'] = int(s['as_of'][:4]) if (s.get('as_of') or '')[:4].isdigit() else None
            b['status_evidence'] = dict(text=s.get('evidence'), url=s.get('source_url'), as_of=s.get('as_of'))
        if r.get('operator_model') and r['operator_model'] != b.get('operator_model'):
            b['operator_previous'] = b.get('operator_model')
            b['operator_model'] = r['operator_model']
        add_sources(b, [(c.get('source_title') or 'cost source', c.get('source_url')),
                        ('floor area', r.get('sqft_source_url')),
                        ((s.get('evidence') or 'status')[:80], s.get('source_url'))]
                    + [(f.get('item', 'financing')[:80], f.get('source_url')) for f in b['financing_stack']])

    L['meta']['updated'] = DAY
    L['meta']['research_2026_10_26'] = ('Desk research on 26 Oct 2026: every value added carries the URL of a page read that day '
                                        '(team/explorer/research/). Four claims were checked again by hand before merging.')
    L['meta']['displacement_rubric'] = RUBRIC
    L['meta']['cpi'] = dict(annual=CPI, source=CPI_SOURCE)
    with open(LIB, 'w', encoding='utf-8') as fh:
        json.dump(L, fh, indent=1, ensure_ascii=False)
    n_cost = sum(1 for b in L['buildings'] if (b.get('cost') or {}).get('per_sqft_2025'))
    print('districts', len(L['districts']), 'buildings', len(L['buildings']), 'with cost per sq ft', n_cost)


if __name__ == '__main__':
    main()
