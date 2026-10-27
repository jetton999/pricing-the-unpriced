#!/usr/bin/env python3
"""Suggest where each unfiled City Archives page belongs (BRG48-43-10), from the filed pages on either side.

Run from anywhere:  python3 team/evidence/triage_unfiled_pages.py

Input:
- city_archives_unfiled_pages_2026-10-26.csv (beside this script): the sponsor's list of 26 Oct 2026, 174 pages
  scanned but not filed on any building. 122 sit inside a filed range; 52 come after the last filed page of their
  folder.
- archive_scans.csv (data package): the filed pages, one row per page per building.

Output: archive_unfiled_triage_2026-10-26.csv beside this script. Every row is a suggestion to check against the
scan, not a filing: open the page before filing it or citing it (AGENTS.md, "Archive scans").

The rule, most specific first:
1. The folder is about one building (every filed page is on it, leaving out the area record): that building.
2. The filed pages just before and just after are on the same building(s): those.
3. They share some buildings: the shared ones.
4. Only a page before (the page comes after the last filed one): the building(s) of the last filed page.
5. Otherwise both neighbours' buildings, low confidence.
The export files area-wide documents on one intersection record (Greenmount Ave & E 33rd St); a suggestion that is
only that record reads "area-wide document".
Standard library only.
"""
import collections
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
IN = os.path.join(HERE, 'city_archives_unfiled_pages_2026-10-26.csv')
OUT = os.path.join(HERE, 'archive_unfiled_triage_2026-10-26.csv')
AREA = {'2366'}                                 # Greenmount Ave & E 33rd St: the area-wide record in the export
FRONTAGE_SIDES = {'65', '67', '68', '69', '70', '71', '72'}
FLAGS = {
    '9': "Urban renewal plan text: read for the use rules. The sponsor said on 26 Oct that the plan bars taverns, not "
         "restaurants (a restaurant can hold a liquor licence); confirm the wording and section here.",
    '8': 'Final plan text after the last filed page: check for use rules and design standards before filing.',
}


def rd(path):
    with open(path, encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def main():
    props = {r['id']: r for r in rd(os.path.join(REPO, 'properties.csv'))}
    fa = {r['property_id']: r for r in rd(os.path.join(REPO, 'team', 'week1', 'out', 'focus_area_properties.csv'))}
    filed = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rd(os.path.join(REPO, 'archive_scans.csv')):
        filed[r['item']][int(r['page'])].append(r)
    unfiled = rd(IN)
    run_of, runs = {}, collections.defaultdict(list)
    for r in sorted(unfiled, key=lambda r: (int(r['item']), int(r['page']))):
        k = (r['item'], int(r['page']))
        prev = (r['item'], int(r['page']) - 1)
        run_of[k] = run_of.get(prev, k)
        runs[run_of[k]].append(k)

    addr = lambda ids: '; '.join(props.get(i, {}).get('address', i).replace(', Baltimore, MD', '').replace(' 21218', '') for i in sorted(ids))
    out = []
    for r in unfiled:
        item, page = r['item'], int(r['page'])
        pages = sorted(filed[item])
        before = [p for p in pages if p < page]
        after = [p for p in pages if p > page]
        pb, pa = (before[-1] if before else None), (after[0] if after else None)
        ib = {x['property_id'] for x in filed[item].get(pb, [])}
        ia = {x['property_id'] for x in filed[item].get(pa, [])}
        folder = {x['property_id'] for rows in filed[item].values() for x in rows} - AREA
        if len(folder) == 1:
            sug, basis, conf = folder, 'every filed page of this folder is on this building', 'high'
        elif pb and pa and ib == ia:
            sug, basis, conf = ib, f'filed pages {pb} and {pa}, either side, are both on it', 'medium'
        elif pb and pa and ib & ia:
            sug, basis, conf = ib & ia, f'shared by filed pages {pb} and {pa}, either side', 'medium'
        elif pb and not pa:
            sug, basis, conf = ib, f'after the last filed page ({pb})', 'low'
        else:
            sug, basis, conf = ib | ia, f'between filed pages {pb} and {pa}, which are on different buildings', 'low'
        area_only = bool(sug) and sug <= AREA
        on_frontage = sorted(i for i in sug if fa.get(i, {}).get('block_side_id') in FRONTAGE_SIDES)
        run = runs[run_of[(item, page)]]
        cap = (filed[item].get(pb) or [{}])[0].get('caption', '')
        out.append(dict(
            item=item, reference=r['reference'], folder_title=r['folder_title'], page=page, file_name=r['file_name'],
            status=r['status'], run=f"pp. {run[0][1]}-{run[-1][1]}" if len(run) > 1 else '',
            filed_page_before=pb or '', buildings_before=addr(ib), filed_page_after=pa or '', buildings_after=addr(ia),
            suggested_property_ids=' ; '.join(sorted(sug)),
            suggested=('area-wide document' if area_only else addr(sug - AREA) + (' (and the area record)' if sug & AREA else '')),
            on_frontage=' ; '.join(on_frontage), confidence=conf, basis=basis,
            caption_of_page_before=cap[:160], flag=FLAGS.get(item, ''), checked_by='', filed_as=''))
    out.sort(key=lambda x: (int(x['item']), x['page']))
    with open(OUT, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    c = collections.Counter(x['confidence'] for x in out)
    print(f"wrote {os.path.basename(OUT)}: {len(out)} pages; confidence {dict(c)}; "
          f"area-wide {sum(x['suggested'] == 'area-wide document' for x in out)}; "
          f"on the frontage {sum(bool(x['on_frontage']) for x in out)}; flagged {sum(bool(x['flag']) for x in out)}")
    return out


if __name__ == '__main__':
    main()
