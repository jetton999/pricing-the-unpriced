# Numbers of record

One file of headline numbers for every document, slide and email to quote. Written by `team/numbers_of_record.py` from the data
and the scripts' own outputs; nothing here is typed by hand. If a document disagrees with this file, the document is out of date.
The same numbers, for scripts, are in `team/numbers_of_record.json`.

The documents listed in `DOCS` in the script quote these figures between two hidden comments (`<!--=key-->` and `<!--/-->`), and each run
of the script rewrites them. To quote a figure in a document, mark it the same way; do not type a headline number by itself.

## The frontage

| | Number | From |
|---|---|---|
| Parcels on the frontage, E 29th to E 33rd St | 69 | `team/explorer/index.html` (built from `team/week1/out` and `team/evidence/blocklot_gaps.csv`) |
| Storefronts | 62 | the same; a house with no shop front is not a storefront |
| Houses | 7 | sponsor's storefront assessments (`residential`) |
| **Empty storefronts** | **24** | `team/tenants/current_tenants_2026-10.csv`, which follows the sponsor's storefront audit of November 2026 (24 storefronts as of 17 November) |
| Storefronts in use | 38 | the same |
| Businesses counted (one business in two street numbers counts once: 3133) | 37 | the same |
| Businesses at the same address for 15 years or more | 4 (the oldest since 1977) | the tenant list and dated records |
| In-use rows a person has entered or checked | 5 of 38 | `entered_by` in the tenant list |
| In-use rows whose business name rests on a search listing only | 15 of 38 | `source_type` in the tenant list |

The empty storefronts: 2920, 2930, 2932, 2934, 2942, 2946, 2958, 3010, 3011, 3015, 3019, 3023, 3026, 3029, 3036, 3038, 3107, 3111, 3117, 3120, 3122, 3200, 3211, 3224.

## The historical record

| | Number | From |
|---|---|---|
| Evidence rows | 3,331 | `team/extractor/out/evidence.csv` |
| of which history (the 2026 tenant check left out) | 3,252 | the same |
| of which sponsor records | 501 | the same |
| History rows coded with a use | 1,433 | the same |
| History rows with an inferred address | 753 | `basis = inferred` |
| of which placed on the next parcel down or up | 691 (21% of history rows) | `address_method` |
| Spans in the timelines | 619 | `team/extractor/out/timeline_table.csv` |
| Parcel-and-use rows | 303 (208 proven, 95 single mention) | `team/extractor/out/proven_uses.csv` |
| Uses on record at a storefront or house, by parcel and kind (housing left out) | 229 | `team/explorer/index.html` |
| of which rest on two independent kinds of source at the address and the standing building | 89 | the same |
| Extractor against four hand-built timelines, sources not used to build them | finds 28% (9 of 32); 89% of 28 records agree on the kind of use | `team/extractor/out/validation.md` |
| The same with all sources (not a test: the timelines were built from the same sponsor records) | finds 78%; 88% of 135 | the same |

## The score

Weights agreed with the sponsor on 9 November 2026: heritage 35, room on the block 20, size 15, community 10, neighbours 10, precedents 10. Read from the built page by `team/explorer/page_numbers.py`.

| | Number |
|---|---|
| A building with no record at all scores, for a cafe or restaurant | 63 of 100 |
| Storefronts whose top candidate is a cafe or restaurant | 46 of 62 (12 of the 24 empty) |
| The same with the heritage weight at zero | 54 of 62; the top candidate changes on 14 |
| Precedent input for a cafe or restaurant, lowest and highest across the storefronts (0 to 100) | 54 to 100; for a showroom 0 to 0 |
| Community input for a cafe or restaurant, the same at every storefront | 100 |
| The same without community and precedents | 32 of 62; the top candidate changes on 19 (8 of the empty) |
| Top candidate changes when today's tenant is counted as history (the page until 21 November 2026) | 4 of 62 |
| Top candidate changes when only the firmest records count | 2 of 62 |
| Top candidates that rest on two kinds of source at the address / one kind / inference only / no record of the use there | 39 / 5 / 1 / 17 |
| Top candidates that score no higher than at a building with no record | 6 |

## The plan for the empty storefronts

| | Number |
|---|---|
| Sheets | 24 |
| Candidate uses | 10 cafe, 6 services, 3 shop, 2 office, 1 showroom, 1 studio, 1 workshop |
| Fit, on average | 72 of 100, +19 over a building with no record |
| Candidates resting on two kinds of source / one / inference only / no record of the use there | 14 / 2 / 0 / 8 |
| Ground floor of the 24 buildings, estimated | 57,133 sq ft (at most 70,926; the whole buildings are 82,606) |
| Ground floors to measure first | 3 of 24 |
| **What the spaces rent for, a year** | **$538,200 in the low case**; $937,600 in the middle; $1,633,500 high |
| Rent-pressure watch | 4 block sides, 11 businesses, 1 long-standing |

The rent is for the space, from listed rents on this corridor, and is the same whatever the uses. It is not what a building is worth.

## Rents

| | Number | From |
|---|---|---|
| Rents used | 60 (57 asking, 3 in place, 0 newly signed) in 17 corridors | `team/comps/comps_ranges.json` (comps engine v2) |
| Rents in Waverly | 6 (3 asking, 3 in place) | the same |
| Rent level on Waverly's corridor, per sq ft a year, before taxes and insurance | $9.33 low, $16.22 middle, $28.22 high | the same |
| Held-out rents inside the range | 48 of 59 (the range is widened ×1.26; 41 before widening) | the same |
| Sales check, use by use | cafe: too close to call; counter: too close to call; tavern: too close to call; shop: covers; showroom: does not cover; bike: covers; services: covers; fitness: covers | the same |
| Library rows checked against their source by a person | 0 of 318 | `verified_by` in `team/comps/library/` |

## The back-test

Does a use on record before 1960 predict the use today, on 52 Greenmount parcels outside the frontage? **The test does not pass the rule agreed with the sponsor on 9 November 2026.** From `team/validation/out/backtest_v2.json`.

| | Number |
|---|---|
| One-sided shuffle test, records up to 1960 | **p = 0.055** (416 pairs, 57 true today) |
| The same before the leak found on 17 November 2026 was fixed (not valid) | p = 0.023 |
| Records up to 1940 | p = 0.024 |
| Ordinary storefront trades only | p = 0.455 |
| Every kind of use except automotive | p = 0.484 |
| Automotive: parcels with it on record before 1960, and how many are automotive today | 4 of 4 (base rate 17%) |
| Leaving one parcel out at a time | p from 0.028 to 0.148; 12 of 52 runs below 0.05 |
| Without the multi-tenant centre (2801 Greenmount) | p = 0.087 |
| History coded from linked businesses and directory lines only | p = 0.086 |
| Low-confidence codes of today's use left out | p = 0.084 |
| Held-out forecast error (log loss), without and with history | 0.6070 to 0.6050 |
| Held-out gain per row, with a 95% interval | +0.0020 (-0.0043 to +0.0088): not distinguishable from zero |
| Held-out ranking (AUC), without and with history | 0.631 to 0.632 |
| The same measure on the data the model was fitted to (flatters; do not quote alone) | 0.707 to 0.724 |
| Frontage storefronts the test can use, and empty ones it cannot | 38 and 24 |
| First back-test (hit or miss, frontage, records up to 1960) | 21 of 35, against 22 for a plain guess |

If the rule fails: the money layer shows rent and revenue ranges from comparable listings only, labelled as planning figures, and nothing that ranks uses or plans by history and money together (PLAN_backtest_v2.md).

## What a person has checked

| | Checked | Of |
|---|---|---|
| Tenant rows entered or checked by a person | 23 | 79 |
| "Use today" rows on the other blocks | 0 | 52 |
| Comps library rows | 0 | 318 |
| Blind reference timelines built | 0 | 4 |
| "Checked by" lines signed | 0 | 8 |

Unsigned: `team/comps/MODEL_CARD.md`, `team/comps/README.md`, `team/evidence/README.md`, `team/explorer/README.md`, `team/extractor/README.md`, `team/precedent/README.md`, `team/prototype_v0/README.md`, `team/tenants/README.md`.

## Documents that quote other numbers

Living documents in `team/` whose counts differ from the data today. They are listed here for their authors; this script changes no document.

| Document | What | It says | The data today |
|---|---|---|---|
| `team/extractor/README.md` | rows in evidence.csv | 3,156 | 3,331 |
| `team/extractor/README.md` | spans in timeline_table.csv | 566 | 619 |
| `team/extractor/README.md` | rows in proven_uses.csv | 283 | 303 |
| `team/extractor/README.md` | uses graded "proven" | 186 | 208 |
| `team/extractor/README.md` | sponsor records read | 326 | 501 |
| `team/extractor/README.md` | rows the inferred-address count is out of | 3,156 | 3,331 |
| `team/extractor/README.md` | records scored for category agreement, all sources | 117 | 135 |

## To rebuild

```bash
python3 team/extractor/extract.py            # if the tenant list or a source changed
python3 team/comps/comps_engine.py
python3 team/validation/backtest.py          # about a minute
python3 team/explorer/build_explorer.py
python3 team/explorer/page_numbers.py        # needs Playwright for Python; reads the numbers off the built page
python3 team/numbers_of_record.py
python3 -m unittest team/extractor/test_extract.py team/comps/test_comps_engine.py team/validation/test_backtest.py team/validation/blind_timelines/test_blind_kit.py team/explorer/test_explorer_data.py team/explorer/test_page_rules.py team/explorer/test_page_browser.py team/validation/two_coder/test_two_coder.py team/test_numbers_of_record.py
```
