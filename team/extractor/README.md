# Use-history extractor v1 (draft for review)

For each of the 79 frontage properties (2900 to 3299 Greenmount, block sides 65 and 67 to 72), this script finds what
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

512 source lines could not be placed on a frontage parcel; they are listed in `out/unassigned.csv` (mostly York Road
numbers outside the crosswalk).

## How it works

1. **Address.** An exact number goes to its parcel. A range ("3226-3240") goes to the parcel that holds it. Otherwise
   the line goes to the next parcel down on the same side (up to 14 numbers) or up (2), because one parcel often holds
   several old house numbers. Every row records how it was placed in `address_method`. A York Road number is first
   turned into a Greenmount number with `team/evidence/york_crosswalk.csv`. Rows placed by a crosswalk interpolation
   or a neighbouring number are marked `basis = inferred` (535 of 3,156).
2. **Use.** `rules.py` is one ordered list of keyword rules for the team's ten categories; the first match wins. Two
   guards matter: a backyard garage is residential, not automotive, and a bare "store" or "shop" is coded
   `store building (generic)`, because it says there was a shop front, not what was sold. When a business is named,
   it becomes `named store`. Sanborn labels are coded from their words first, then from the map letters (D, F, S, V).
3. **Spans.** Records of the same use at the same property join into one span while the gap between them is 10 years
   or less. Each span gets a grade: `single record`, `repeated (2+ records)` or `documented (2+ source types)`.
4. **Proven uses.** A use is `proven` at a property when it appears in two or more decades or in a documented span.
5. **Silence map.** For each property, the decades from 1900 to 2020 with a coded use, before (sponsor records only)
   and after the new sources, and which source would fill each gap.

## What comes out (`out/`)

| File | Rows | What |
|---|---|---|
| `evidence.csv` | 3,156 | One row per source line: property, year, source, reference, link, how the address was placed, text, coded use |
| `timeline_table.csv` | 592 | One row per span: years, use, subcategories, occupants, grade, sources, the source rows behind it |
| `proven_uses.csv` | 305 | Per property and use: first and last year, spans, records, decades, `proven` (198) or `single mention` (107) |
| `silence_map.csv` | 79 | Decades covered before and after the new sources; status `documented` (8+ decades), `partial` (5-7), `thin` |
| `unassigned.csv` | 512 | Lines that could not be placed |
| `validation.md` | | The scores below, row by row |

Mean decades with a coded use per property, 1900s to 2020s: **2.0 from the sponsor records alone, 5.5 with the new
sources.** Status: 11 documented, 45 partial, 23 thin.

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
