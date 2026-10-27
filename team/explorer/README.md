# Greenmount frontage explorer (release candidate, 26 October 2026)

For each of the 69 frontage parcels on Greenmount Ave, E 29th to E 33rd St, one page shows:

- what the building was used for;
- what it could become, and why;
- what that use could pay;
- whether the mix works as a block.

Every answer links to its source. To view it, download `index.html` and open it in a browser. GitHub shows the
source, not the page.

## What is on the page

| Tab | What it does |
|---|---|
| Buildings | **Map and ledger:** the map of the frontage, and the use ledger (the main use in each decade, 1880s to today).<br>**Building panel:**<br>- the best fit, why, and the rent that use could support;<br>- a label for how firm the verdict is (holds up, close call, or depends on priorities), from 1,000 mixes of priorities;<br>- the rules that apply;<br>- a heritage-revival name where one is documented;<br>- for retail, the trade and its modern version;<br>- long-standing businesses, marked with the years they have traded there.<br>For a building with a business in it, the verdict reads as planning for if the space comes free, never as a suggestion to replace the tenant.<br>**Also:** compare up to three uses; three concepts drafted with AI assistance. |
| Block plan | **Planning:** places uses on the vacant and for-lease parcels under a saturation limit, then ranks alternative plans for the same parcels by the rent the uses could support.<br>**Year to plan for:** a typical, cautious or bad year.<br>**Rent-pressure check:** each plan flags businesses already trading on the same block sides whose kind of business typically supports at least 20% less rent than the plan's new uses. Long-standing businesses are named on each block side.<br>**Hidden plans:** the balanced plan is hidden when another plan beats it on both fit and rent. |
| Money | **Comps engine (`team/comps`):**<br>- ranges per use;<br>- the typical unit for each use and the total rent a year at that size (`typical_sqft.json`, 20 uses, sourced);<br>- the trail from each figure to its source rows;<br>- other cities' corridors side by side;<br>- held-out checks.<br>**When dollar figures may be shown:** the state of the rule the sponsor's proposal sets. |
| Comps | **Three levels, from the building out:**<br>- **Buildings like this one:** the selected building side by side with its three closest reuse cases (size, uses, operator, cost, money sources, time to open, 2025-26 status, lesson); what projects like it spent per sq ft in 2025 dollars; filters.<br>- **Streets like Greenmount:** 22 corridors with a Waverly-today row, the comps engine's corridor rent beside each street, the displacement rubric, milestones and evidence per street; filters.<br>- **Neighbourhoods like Waverly:** the sponsor's benchmark set (Waverly, Pigtown, Hampden, Ohio City, Fishtown, U Street, Melrose Hill, Bed-Stuy) on public asking rents (made triple-net equivalent), a typical shop's rent a year, vacancy with how it was measured, residents and displacement; a chart, cards with every row and source, and "how Greenmount compares", written from the rows at build time. |
| Evidence and method | **Weights:** one pie that always adds to 100%. Move one slider and the others give way in proportion; four presets (team default, history first, neighbourhood first, proven elsewhere) set all six at once. Feedback changes scores only when switched on; it is off by default.<br>**Back-test v2:** the results from `team/validation`.<br>**Also:** the rules, community and neighbour layers, retail broken into seven trades, customer groups, the screening table. |
| Roadmap | The road to the final deliverable, with what is done |

"Today" shows the team's tenant check next to the sponsor's October 2026 storefront assessments
(`storefront_assessments.csv`). Where the team's check found no listing at an address but the sponsor found a
business, a church or a house, the page says so. Houses with no shop front are left out of the block plan.

## Rebuild

```bash
python3 team/comps/comps_engine.py           # rent and revenue ranges (optional; the page uses the last comps_ranges.json)
python3 team/validation/backtest.py          # back-test v2 (optional; the page uses the last out/backtest_v2.json)
python3 team/explorer/build_explorer.py       # standard library only; writes index.html
python3 -m unittest team/explorer/test_explorer_data.py team/validation/test_backtest.py team/comps/test_comps_engine.py
```

| File | What |
|---|---|
| `build_explorer.py` | Reads the extractor outputs, the evidence and tenant files, `properties.csv`, `storefront_assessments.csv`, `team/comps/comps_ranges.json` and `team/validation/out/backtest_v2.json`, and writes `index.html`. The `PTU_*` variables let the team build a private copy from files kept outside the repo; unset, it reads repo files only |
| `template.html` | The page: layout, score engine and views |
| `concepts.json` | The three drafted concepts (written with AI assistance), every fact with its source |
| `library.json` | The case library (32 reuse buildings, 22 corridors) and the evidence behind the community, neighbour and customer layers. Every entry has its sources; `meta.displacement_rubric` holds the rating rule |
| `research/` | The 26 Oct 2026 desk research merged into `library.json` (costs, floor areas, timelines, financing, 2025-26 statuses, displacement evidence, milestones, three added corridors), and the script that merged it |
| `extras.py` | The sponsor's storefront check, heritage-revival names, retail trades, survey-photo counts, long-standing businesses, typical sizes, and the neighbourhood benchmarks (rents made triple-net equivalent, Waverly's own rents and vacancy, and the comparison sentences) |
| `retail_types.json` | Seven retail trades: the modern version, usual size and cautions, every claim with its source. No reference brands (see Rules kept) |
| `typical_sqft.json` | The typical floor area of 20 uses (low, typical, high), 96 sources read on 26 Oct 2026; chains' filings and sites are labelled by kind |
| `research/neighbourhoods_2026-10-26.json` | The eight benchmark neighbourhoods as researched: asking rents with the lease type as stated, vacancy with its definition, residents, displacement evidence and sources |
| `DISPLACEMENT.md` | What the displacement rating measures and how it could be used in planning (note for the sponsor, 26 Oct 2026) |
| `MODEL_CARD.md` | What the page is for, what it must not be used for, how it was checked and where it fails |
| `index.html` | The built page (generated; do not edit by hand) |

## Data vintage

- Built from the extractor's October 2026 rerun (PR #12), on the sponsor's 69-parcel frontage.
- Parcel facts (owner type, vacant-building notices, permits) come from the October `properties.csv`.
- The case library was last checked on 26 October 2026. Statuses say "operating" only where a 2025 or 2026 source
  says so.

## Rules kept

- **Uses, not buildings.** The page ranks uses for a building and compares plans for the same parcels. It never
  ranks buildings or blocks by money. There is no valuation, appraisal language or acquisition targeting.
- **Ownership.** A sponsor walk-through is not a statement of ownership. The owner of record comes from the state
  assessment snapshot.
- **Feedback.** Team and sponsor votes are shown beside each score. They change scores only when switched on,
  because the sponsor's rules say the sponsor cannot override model results.
- **Displacement.** Buildings with a business in them are never planned. The block plan flags rent pressure on
  businesses already trading, and long-standing businesses are named. `DISPLACEMENT.md` explains the rating.
- **Named businesses.** This public version names no business as a possible tenant. Brand names go in reports
  only, not the public repo (the sponsor's rule, 26 Oct 2026): the reference brands are kept in the team report, and
  a test checks the public files and the built page for them by hash. National chains whose filings, sites or
  listings back a size or a benchmark are cited by link and labelled by kind ("a drive-thru coffee chain's 10-K").
  The page still names businesses already trading on or next to the frontage (as the sponsor's storefront data
  does), the reuse projects and corridors in the case library, and the local operators whose own figures are
  checked against the ranges. No NDA data is used.
- **Sources.** Every outside fact links to its source. The pipeline never drops the export's 126
  sensitivity-flagged records, as the repo requires. None of them is among the frontage records, and none is quoted
  on the page.

## Known limits

See `MODEL_CARD.md`. In short:

- **The weights are team judgement.** The sponsor has not yet agreed a set.
- **Back-test v2 passes on blocks the model had not seen** (p = 0.023), but the gain over "how common is this use"
  is modest, and history does not show cause.
- **Project costs are adjusted for inflation only.** Scope differs between projects.
- **The displacement rubric is applied by the team** from published sources. "Unknown" does not mean none.
- **Long-standing businesses are found only where a record or a check documents them.** Others may exist.

## AI use

Built with Claude (October 2026) from the team's notes and the sources linked in the data. Before merge, a team
member reviews the code, checks a sample of the case library and the concept facts against their sources, and
signs below.

Checked by: ____________________ Date: __________
