# Use-history extractor v1 (draft for review)

For each of the 69 frontage parcels (2900 to 3299 Greenmount, block sides 65 and 67 to 72), this script finds what
the building was used for, decade by decade, and names the source of every claim. It replaces
`team/prototype_v0/` (same idea, fewer sources, no York Road crosswalk, no tests).

```bash
python3 team/extractor/crosswalk.py       # York Road -> Greenmount numbers (writes into team/evidence/)
python3 team/extractor/extract.py         # evidence, spans, proven uses, silence map, validation (writes out/)
python3 -m unittest discover team/extractor
```

Standard library only. It needs the week-1 package (`team/week1/out/`), `team/evidence/`, `team/tenants/` and
`team/precedent/interventions.csv`. The map reads `out/` (see `map/README.md`).

## What goes in

| Source | Where | Rows used | Years |
|---|---|---|---|
| Sponsor curated records, class A ("states a use") | `team/week1/out/use_records.csv` | 326 | 1872-2025 |
| Polk directories under the old York Road numbers | `team/evidence/polk_york_1901_1913.tsv` via `york_crosswalk.csv` | 730 of 1,054 | 1901-1913 |
| Polk directories under the Greenmount numbers | `team/evidence/polk_frontage_1912_1923.tsv` | 934 | 1912-1923 |
| Building permit index cards (BRG48-53) | `team/evidence/permit_cards_1924_1961.csv` | 615 | 1924-1961 |
| Sanborn sheets, 1915, 1928, 1953 | `team/evidence/sanborn_frontage.csv` | 274 | 1915-1953 |
| National Register inventory (B-5229) | `team/evidence/nr_inventory_frontage.csv` | 187 | built 1880-1930s; uses 1920s-1930s and c. 2011 |
| 1970s DHCD revitalization files (BRG48-43-10) | `team/precedent/interventions.csv` | 11 | 1977-1980 |
| 2026 tenant check | `team/tenants/current_tenants_2026-10.csv` | 79 | 2026 |
| Sponsor's list of records with no block and lot of their own | `team/evidence/blocklot_gaps.csv` | 20 | merges of 25 and 30 September 2026 |

512 source lines could not be placed on a frontage parcel; they are listed in `out/unassigned.csv` (mostly York Road
numbers outside the crosswalk).

## How it works

1. **Parcels.** The export has 79 frontage records, but the sponsor's `blocklot_gaps.csv` says 10 of them were merged
   into a neighbouring parcel (for example "3028 to 3032 are one parcel"). The extractor works on the 69 parcels as
   they stand today. A merged record's id, its street number and the numbers inside a stated merge range all point to
   the parcel that holds them, and the sponsor's curated records filed on a merged id follow it. The one merge the
   sponsor marks "not verified" (3103 into 3031) is used but marked inferred. Eight historic numbers on the east side
   of the 2900 block, buildings gone with no parcel today, are never handed to a neighbour.
2. **Address.** An exact number goes to its parcel. A range ("3226-3240") goes to the parcel that holds it. Otherwise
   the line goes to the next parcel down on the same side (up to 14 numbers) or up (2), because one parcel often holds
   several old house numbers. Every row records how it was placed in `address_method`. A York Road number is first
   turned into a Greenmount number with `team/evidence/york_crosswalk.csv`. Rows placed by a crosswalk interpolation
   or a neighbouring number, or by the unverified merge, are marked `basis = inferred` (754 of 3,156). A record counts
   as stated only when every step that placed it read the address as written.
3. **Use.** `rules.py` is one ordered list of keyword rules for the team's ten categories; the first match wins. Two
   guards matter: a backyard garage is residential, not automotive, and a bare "store" or "shop" is coded
   `store building (generic)`, because it says there was a shop front, not what was sold. When a business is named,
   it becomes `named store`. Sanborn labels are coded from their words first, then from the map letters (D, F, S, V).
4. **Spans.** Records of the same use at the same property join into one span while the gap between them is 10 years
   or less. Each span gets a grade: `single record`, `repeated (2+ records)` or `documented (2+ source types)`.
5. **Proven uses.** A use is `proven` at a property when it appears in two or more decades or in a documented span.
6. **Silence map.** For each property, the decades from 1900 to 2020 with a coded use, before (sponsor records only)
   and after the new sources, and which source would fill each gap.

## What comes out (`out/`)

| File | Rows | What |
|---|---|---|
| `evidence.csv` | 3,156 | One row per source line: property, year, source, reference, link, how the address was placed, text, coded use |
| `timeline_table.csv` | 566 | One row per span: years, use, subcategories, occupants, grade, sources, the source rows behind it |
| `proven_uses.csv` | 283 | Per parcel and use: first and last year, spans, records, decades, `proven` (186) or `single mention` (97) |
| `silence_map.csv` | 69 | Decades covered before and after the new sources; status `documented` (8+ decades), `partial` (5-7), `thin` |
| `unassigned.csv` | 512 | Lines that could not be placed |
| `validation.md` | | The scores below, row by row |

Mean decades with a coded use per parcel, 1900s to 2020s: **2.2 from the sponsor records alone, 5.9 with the new
sources.** Status: 13 documented, 41 partial, 15 thin. Every parcel now has at least one coded decade (5 had none
from the sponsor records alone).

## Validation

Against the four reference timelines in `team/week1/out/use_timelines.md` (built by hand from the sponsor records).

| Scope | Recall | Recall where a source covers those years | Category agreement |
|---|---|---|---|
| All sources | 78% (25 of 32) | 96% | 91% of 117 records |
| New sources only | 28% (9 of 32) | 82% | 89% of 28 records |

The research-plan targets are 90% recall and 85% agreement. The "all sources" scores are not independent: the
references were built from the same sponsor records. The "new sources only" row is the independent check. The
four **blind** reference timelines in the plan, built by a team member who has not seen this output, are still
needed before these numbers can be reported. Five of the seven misses are at 401 E 30th St (the ballpark, then the
bottling plant), which is in the focus area but not on the Greenmount frontage the extractor covers. The other two
are short "for rent" notices (3224 in 1906, 3200 in 1929).

**Second test: named occupants.** The week-2 progress report's 30 reference occupants (`reference/`), 24 of them on
frontage parcels: all 24 are named in a record at their parcel within their years (100%). 6 of the 24 (25%) are named
in the new sources alone: five in the directories up to 1923, and Joe the Motorist's Friend in the National Register
inventory, which takes its tenant names from the 1928 and 1937 directories. Permit cards and
Sanborn sheets do not name occupants, so later occupants still rest on the sponsor's records.

**Crosswalk check.** Against the report's 23 hand-read pairs (`team/evidence/york_crosswalk_reconciliation.csv`): 16
agree, 3 fall outside this crosswalk's range, and 4 differ. Three of the four are the report's own open conflicts,
settled by the Sanborn prints (1027 is 3117, 1112 is 3220, 1113 is 3219). The fourth is 1023: the report puts it at
the 3107 corner; the 1928 Sanborn sheet and the report's own block offset give 3111. Check the sheet by eye.

## Known limits

- Polk lines are raw OCR. Names are often misspelled and some digits misread.
- The classified-business half of each Polk volume loses the trade heading, so those lines are `listed (uncoded)`.
- The crosswalk has 42 anchors; the rest is interpolation (13 rows medium, 107 low confidence). See
  `team/evidence/README.md`.
- No source has been read yet for the 1960s to 1990s, except a few sponsor records. Blank decades there mean
  "not read yet", not "empty".
- 28 of the 79 tenant-check rows are still `unknown` (no business on Google Maps); they need a Street View check.

## AI use

Written with Claude on 18 October 2026. The rules, the crosswalk and a sample of coded rows need a check by a team
member against the sources before merge.

Checked by: ____________________ Date: __________
