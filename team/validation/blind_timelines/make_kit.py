"""Blind reference timelines: draw the four parcels and write a reading packet for each.

Run once, before anyone starts reading:  python make_kit.py

The draw is fixed by SEED and by the rule below, so anyone can rerun it and get the same four parcels.
Nothing here reads the extractor's coded uses. Two extractor files are read for location only: the list of
frontage parcels with their block sides (out/silence_map.csv), and which directory volumes, map sheets and
permit folders cover a block side (the source, source_ref and url columns of out/evidence.csv).
"""
import collections
import csv
import json
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SEED = 'blind reference timelines, 2026-11-10'
ALREADY_REFERENCE = {'742', '752', '768'}        # the week-1 reference timelines on the frontage
HOUSE = {'residential'}                           # sponsor's storefront assessment: a house, no shop front
FIELDS = ['property_id', 'address', 'start_year', 'end_year', 'use', 'use_category', 'occupant',
          'stated_or_inferred', 'source', 'source_ref', 'note', 'built_by', 'built_on', 'saw_extractor_output']
CATEGORIES = ['retail goods', 'food & drink', 'personal services', 'automotive', 'entertainment & assembly',
              'institutional & religious', 'office', 'production & light industry', 'residential', 'vacant']
SIDES = {'65': 'west side, 2900 block', '67': 'west side, 3000 block', '68': 'east side, 3000 block',
         '69': 'west side, 3100 block', '70': 'east side, 3100 block', '71': 'west side, 3200 block',
         '72': 'east side, 3200 block'}


def rows(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))


def number(address):
    m = re.match(r'\s*(\d+)', address)
    return int(m.group(1)) if m else 0


def draw():
    """One parcel from each hundred block, among frontage parcels that are neither a house nor already a reference."""
    parcels = rows('team', 'extractor', 'out', 'silence_map.csv')
    status = {r['property_id']: r['status'] for r in rows('storefront_assessments.csv')}
    eligible = [p for p in parcels if p['property_id'] not in ALREADY_REFERENCE and status.get(p['property_id']) not in HOUSE]
    blocks = collections.defaultdict(list)
    for p in eligible:
        blocks[number(p['address']) // 100 * 100].append(p)
    rng = random.Random(SEED)
    picked = []
    for b in sorted(blocks):
        pool = sorted(blocks[b], key=lambda p: number(p['address']))
        picked.append(rng.choice(pool))
    return parcels, eligible, {b: len(v) for b, v in sorted(blocks.items())}, picked


def volume(url):
    """Trim a link to the volume, sheet set or folder, so a packet points at where to read, not at an entry."""
    return re.sub(r'[?#].*$', '', url or '')


def packet(p, parcels, ev):
    side = p['block_side_id']
    same_side = {q['property_id'] for q in parcels if q['block_side_id'] == side}
    polk = sorted({(e['year'][:4], volume(e['url'])) for e in ev if e['source'].startswith('polk') and e['url']})
    sheets = sorted({(e['source_ref'], e['url']) for e in ev if e['source'].startswith('sanborn') and e['property_id'] in same_side and e['url']})
    cards = sorted({volume(e['url']) for e in ev if e['source'].startswith('permit') and e['property_id'] in same_side and e['url']})
    nr = sorted({volume(e['url']) for e in ev if e['source'].startswith('nr_') and e['url']})
    n = number(p['address'])
    old = [r for r in rows('team', 'evidence', 'york_crosswalk.csv') if r['new_greenmount_number'].strip() == str(n)]
    sponsor = sum(1 for r in rows('property_incidents.csv') if r['property_id'] == p['property_id'])
    L = [f"# Reading packet: {p['address']} (property_id {p['property_id']})", '',
         f"Block side: {SIDES.get(side, side)}.", '',
         'Build the timeline from the sources below, read at the source. Write one row per use and period in',
         '`../blind_timelines.csv`. Do not open the explorer page, `team/extractor/out/` or the map sidebar for this',
         'address until your rows are committed.', '',
         '## Where to read', '']
    if old:
        L.append('- **Before about 1914 this block was numbered as York Road.** The team\'s crosswalk gives the old number as '
                 + '; '.join(f"{r['old_york_number']} ({r['confidence']} confidence, method: {r['method']})" for r in old)
                 + '. Check it against a Sanborn sheet before relying on it.')
    else:
        L.append('- **Before about 1914 this block was numbered as York Road.** The team\'s crosswalk has no old number for this '
                 'address: find it from a Sanborn sheet that prints both numbers, or from neighbours listed at both.')
    L.append('- **Polk city directories** (street guide, under York Road and Greenmount Avenue): '
             + ', '.join(f'[{y}]({u})' for y, u in polk) + '.')
    if sheets:
        L.append('- **Sanborn maps** for this block side: ' + ', '.join(f'[{s}]({u})' for s, u in sheets) + '.')
    if cards:
        L.append('- **Building permit index cards** (City Archives, BRG48-53), folders holding this block side: '
                 + ', '.join(f'[{i + 1}]({u})' for i, u in enumerate(cards)) + '.')
    if nr:
        L.append('- **National Register nomination** for Waverly Main Street (B-5229), inventory entry for this address: '
                 + ', '.join(f'[file]({u})' for u in nr) + '.')
    L.append('- **City revitalization files, 1970s** (City Archives, BRG48-43-10): survey sheets and photographs by address.')
    L.append(f"- **Sponsor records**: {sponsor} row{'s' if sponsor != 1 else ''} for property_id {p['property_id']} in `property_incidents.csv`.")
    L.append('- Anything else you find (newspapers, photographs, licences). Cite it in `source` and `source_ref`.')
    L += ['', '## What to write', '',
          '- One row for each use over a run of years: `start_year`, `end_year`, `use` in your own words, the occupant if named.',
          '- `use_category`: one of ' + ', '.join(f'`{c}`' for c in CATEGORIES) + '.',
          '- `stated_or_inferred`: `stated` if the source names the use, `inferred` if you read it from a name or a building type.',
          '- `source` and `source_ref`: enough for a second person to find the line (volume and page, sheet, card image).',
          '- Leave years with no evidence out. A gap is an answer.',
          '- `built_by`: your initials. `saw_extractor_output`: `no`, if that is true for this address.', '']
    return '\n'.join(L)


def main():
    parcels, eligible, blocks, picked = draw()
    ev = rows('team', 'extractor', 'out', 'evidence.csv')
    os.makedirs(os.path.join(HERE, 'packets'), exist_ok=True)
    for p in picked:
        with open(os.path.join(HERE, 'packets', f"{number(p['address'])}_greenmount.md"), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(packet(p, parcels, ev))
    sample = dict(seed=SEED, rule='one parcel per hundred block, drawn with random.Random(seed).choice over the eligible parcels '
                  'sorted by street number; eligible = frontage parcels that are not already a reference timeline and that the '
                  "sponsor's storefront assessment does not class as residential",
                  frontage_parcels=len(parcels), eligible=len(eligible), eligible_by_block=blocks,
                  drawn=[dict(property_id=p['property_id'], address=p['address'], block_side=SIDES.get(p['block_side_id'], p['block_side_id'])) for p in picked])
    with open(os.path.join(HERE, 'sample.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sample, fh, indent=1)
        fh.write('\n')
    path = os.path.join(HERE, 'blind_timelines.csv')
    if not os.path.exists(path):                  # never overwrite rows a person has entered
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            csv.writer(fh, lineterminator='\n').writerow(FIELDS)
    print('eligible', len(eligible), 'of', len(parcels), blocks)
    for p in picked:
        print('drawn', p['property_id'], p['address'], SIDES.get(p['block_side_id']))


if __name__ == '__main__':
    main()
