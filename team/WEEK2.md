# Team Greenmount: week 2 package (draft, 18 October 2026)

For the 19 October meeting. The research plan's week-2 milestone is "draft timelines for all 79 frontage
properties". This branch (`team/week2-integration`) is `main` plus the week-1 package plus this week's work. It is
a proposal for the team to review. Nothing is merged until one other person has reviewed it.

## What is in the branch

| Commit | What |
|---|---|
| `f2a8838`, `4608627` | Week 1 package: focus area, use-record classes, four reference timelines, focus layer on the map |
| `03175b0` | First ten comps and the 2026 tenant check for the 79 frontage properties |
| `807bbe7` | Permit index cards 1924-1961, Polk lines 1912-1923, prototype v0 |
| this commit | York Road crosswalk, Polk 1901-1913, Sanborn 1915/1928/1953, NR inventory, extractor v1 with tests, precedent index, interventions table and memo, use history in the map |

## Against the plan

| Plan item | Plan week, lead | Status |
|---|---|---|
| Extractor v1 on every class-A record | Week 2, timelines lead | Done: all 326 frontage class-A records, plus seven other source types (`team/extractor/`) |
| Sanborn 1915, 1928 and 1953 for the seven block sides | Week 2, timelines lead | Done: 307 footprints (`team/evidence/sanborn_frontage.csv`) |
| Four more reference timelines, built blind | Week 2, timelines lead | **Not done. Needs a person** who has not seen the extractor output |
| Read the 1979 Waverly Plan, the urban renewal plan and the design standards | Week 2, precedent lead | Current urban renewal plan read (memo section 7). The 1979 consultant plan is not online. The 1979 standards survive only in the captions (folders 5 and 23) |
| Draft timelines for all 79 frontage properties | Week 2 milestone | Done: 592 spans, every property has evidence |
| Fill gaps from Polk; proven-use test | Week 3 | Polk 1901-1913 placed through the crosswalk; proven uses done. Chronicling America and desk requests not started |
| Interventions table; precedent memo draft | Week 3, precedent lead | Draft done (`team/precedent/`) |
| Validation memo (two pages) | Week 3 | Waits for the blind references. Scores so far are in `team/extractor/out/validation.md` |
| Timelines in the map sidebar | Week 4, precedent lead | Done (`map/`) |
| Midterm report | 4 November | Not started (put off until the project work holds) |

## What this adds over the base

"Snapshot" is the sponsor repo at `a13feb5`. "Week 1" is the week-1 package.

| | Snapshot | Week 1 | This branch |
|---|---|---|---|
| Use evidence on the frontage | 326 curated class-A records. `baltimore:permits` covers 2019-2026 only. 63 Polk records, none on the frontage. 81 Sanborn records on the frontage, at block level (the uses are in the image) | Same records, classified A/B/C | 2,830 more rows from seven source types: Polk 1901-1923 (1,664 placed), permit cards 1924-1961 (615), Sanborn footprints (274), NR inventory (187), 1970s DHCD files (11), 2026 tenant check (79) |
| Addresses before 1914 | York Road numbers cannot be placed | | Crosswalk: 42 anchors, 162 old numbers mapped (`team/evidence/york_crosswalk.csv`) |
| Decades with a coded use per property, 1900s-2020s (mean) | 2.0 | 2.0 | 5.5 |
| Properties with no coded decade | 12 | 12 | 1 (3206, no coordinates either) |
| Use coding | Free-text summaries | Team category list; four timelines by hand | `rules.py`, tested; 91% agreement with the hand timelines, 89% on the new sources alone |
| Timelines | | 4 properties, by hand | 79 properties: 592 spans with grade, occupants and source rows; 198 proven uses |
| Map | Curated depth and a curated history list | Focus-area layer | Use-history section with a decade grid and source links; "Colour by use" for any decade |
| Precedent case | 1,692 captioned pages | | Folder index (31), interventions (79), memo draft with the plan in force |
| Today's tenants | Fields such as `has_active_business` | | 79-row check with sources: 51 resolved, 28 unknown |
| Comps | | Template | 10 comps and alternates |

## Findings to raise on Monday

1. **History is now readable for almost the whole frontage.** 78 of 79 properties have at least one proven use
   (two or more decades, or two source types).
2. **Food and drink is the frontage's most-proven trade.** It is proven at 36 properties, against 31 for retail
   once bare "store" records are set aside (56 with them). 14 properties have
   a span coded bar / tavern (saloon, tavern, bar or liquor), 11 of them starting before 1930.
3. **The urban renewal plan still in force bars new taverns, liquor stores and pawnshops (since 1995).** It also
   sets facade, sign and awning rules for every commercial building. A heritage-anchored screen has to mark
   "proven but not permitted" (memo section 7). Whether the City applies the plan's B-2 use list under today's C-1
   zoning needs a call to Planning.
4. **The 1960s to 1990s are the gap.** Apart from a few sponsor records, no source has been read for those decades.
   That is where desk requests and newspapers should go.
5. **The 1970s programme was a design deal, not a grant programme.** The City paid about $1.1 million for public
   works and gave free design help. Owners paid for their own facades. No caption shows a facade grant or a loan
   closing.

## Needs a person

| Item | Why it cannot be AI | Suggested owner |
|---|---|---|
| Four blind reference timelines | The test is only independent if the builder has not seen the output | Timelines or precedent lead |
| Spot checks before merge: 30 coded evidence rows, 10 permit lines, 10 Sanborn rows, the `low` crosswalk rows | Repo rule: a person checks AI work against the source | Whoever reviews the PR |
| 28 tenant rows still `unknown` | Needs Street View and a walk-by | Timelines lead |
| 106 generic and 61 truncated scan captions | The scans must be read by eye | Precedent lead |
| Exhibit 2 of the urban renewal plan (parcels to be acquired) | The labels are not in the text layer | Precedent lead |
| Desk-request priority; the sponsor's `blocklot_gaps.csv` | Sponsor decision | Project manager, with the sponsor |
| Reflections and peer assessments | Written without AI | Everyone |

## How to look at it

```bash
python3 team/extractor/crosswalk.py && python3 team/extractor/extract.py
python3 -m unittest discover team/extractor
python3 map/app.py        # http://localhost:8765, click a frontage marker or tick "Colour by use"
bin/check                 # passes on this branch
```

`team/prototype_v0/` is replaced by `team/extractor/`. Proposal: drop it at merge.

## AI use

Most of this week's collection, code and drafting was done with Claude (18 October 2026), under the repo rules: every
claim cites a source row, sensitivity-flagged rows are kept, no Sanborn images are committed, and nothing was
pushed. A team member reviews and tests the code before it goes into `main`.
