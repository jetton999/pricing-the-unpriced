# Greenmount frontage explorer (working draft, 24 November 2026)

For each of the <!--=frontage.parcels-->69<!--/--> frontage parcels on Greenmount Ave, E 29th to E 33rd St, one page shows:

- what the building has been used for, with the source of every record;
- for each empty storefront, candidate uses and the evidence for each at that address;
- what ground-floor space on the corridor rents for;
- whether a set of candidates works as a block.

It makes no recommendation and shows no rent for a building in use or for a house. **Nothing on it has been
checked by a second person yet**: see "What a person has checked" in `team/NUMBERS.md`.

To view it, download `index.html` and open it in a browser. GitHub shows the source, not the page.

Every headline number in this file is filled in from `team/NUMBERS.md` by `team/numbers_of_record.py`. The page was
reworked on 21 November 2026 after the sponsor's review of 17 November; `team/REVIEW_RESPONSE.md` lists each finding
and what was done about it.

## The frontage today

<!--=frontage.parcels-->69<!--/--> parcels: <!--=frontage.storefronts-->62<!--/--> storefronts and <!--=frontage.houses-->7<!--/--> houses with no shop front.
<!--=frontage.empty-->24<!--/--> storefronts are empty and <!--=frontage.in_use-->38<!--/--> are in use, on the tenant list
(`team/tenants/current_tenants_2026-10.csv`), which follows the sponsor's storefront audit of November 2026. A reader
can switch any storefront between empty and in use; the page then says so on every sheet, in the print view and in
the CSV.

## What is on the page

| Tab | What it does |
|---|---|
| Buildings | **Map and ledger.** The map can be coloured by use today, by the use with the longest record, or by top candidate (empty storefronts only). The ledger shows the main use in each decade, 1880s to today.<br>**Panel of an empty storefront.** Up to three candidate uses. Each shows its fit score, how far the score is above the same use at a building with no record, the evidence at this address (two kinds of source, one kind, placed by inference only, or no record), a sales check, who the use is for and how firm the choice is under other weights. Below: what the space rents for at its estimated ground floor, low case first.<br>**Panel of a building in use.** Today's business and how the tenant list knows it, today's use against the record, and the uses on record. No recommendation and no rent. What the record would support if the storefront ever stood empty is in a fold that is closed until the reader opens it.<br>**Panel of a house.** The record only.<br>**Also:** compare uses factor by factor; three concepts drafted with AI assistance. |
| Block plan | **The plan.** One candidate for each empty storefront, placed one at a time under a cap of three of a kind per block side. Businesses already there count toward the cap, and a business that occupies two street numbers counts once.<br>**A sheet per storefront.** The candidate, its fit and its lift over a building with no record, the evidence grade, the ground-floor estimate (flagged "measure first" where the outline is partial or missing), the rent for the space, the sales check, who the use is for, what to watch, the next candidate and how firm the choice is. Any candidate can be changed.<br>**Block by block.** Businesses today and after the plan, and long-standing businesses.<br>**Rent-pressure watch.** Block sides where the plan fills three or more storefronts at once, with the businesses trading there, long-standing ones first.<br>**Output.** Print view and CSV. |
| Money | **What a space rents for.** The rent level on Waverly's corridor from listed rents, and each empty storefront's rent at its estimated ground floor. The figure is for the space and is the same whatever the use.<br>**Use by use.** The listed rent for each use and a sales check: at typical sales, does a business of this kind cover that rent (covers, does not cover, or too close to call). The check is a flag. It never changes a rent figure and nothing is ranked by it.<br>**Folded.** The full table, the trail from each figure to its source rows, other corridors, the held-out check and what moves the numbers.<br>**Why no dollar figure rests on history.** The rule agreed with the sponsor and the test result. |
| Who it is for | Seven customer groups: who they are, what they need from a building, what stops them, the programmes that help, and the empty storefronts that fit each group. |
| Comps | **Three levels.** Buildings like this one (<!--=library.reuse_buildings-->32<!--/--> reuse cases), streets like Greenmount (<!--=library.corridors-->22<!--/--> corridors) and neighbourhoods like Waverly (<!--=library.benchmark_neighbourhoods-->8<!--/--> benchmark neighbourhoods), each with sources. |
| Evidence and method | **Weights.** One pie that always adds to 100%, and five presets. **How much of each score is the building.** A table of the ranking with the six weights agreed on 9 November, with the heritage weight at zero, with only the firmest records, with today's tenant counted as history, and with the whole building as the size.<br>**Back-test.** The corrected result, kind of use by kind of use, with one parcel left out at a time, and on blocks the model had not seen.<br>**Also:** the extractor check, the rules with their citation, the community and neighbour layers, retail in seven trades, and the known limits. |
| Roadmap | The road to the final deliverable, with what is done and what is not. |

## The score in one paragraph

Six inputs. Since <!--=score.default_since-->24 November 2026<!--/--> four of them carry all the weight by default (score v0.5): heritage
<!--=score.default_weights.h-->44<!--/-->, room on the block <!--=score.default_weights.s-->25<!--/-->, size <!--=score.default_weights.f-->19<!--/--> and neighbours
<!--=score.default_weights.a-->12<!--/-->. These are the proportions agreed with the sponsor on 9 November 2026, with community and
precedents at <!--=score.default_weights.c-->0<!--/-->. Neither of the two comes from the building: community is the same number at every
storefront, and precedents come from a hand-picked library of reuse cases in which <!--=library.cases_with_a_cafe-->20<!--/--> of
<!--=library.reuse_buildings-->32<!--/--> include a cafe or restaurant, so the precedent input for a cafe runs from
<!--=score.inputs_by_use.cafe.precedents.0-->54<!--/--> to <!--=score.inputs_by_use.cafe.precedents.1-->100<!--/--> of 100 across the storefronts and is
<!--=score.inputs_by_use.showroom.precedents.1-->0<!--/--> for a showroom at every one.
With the six weights of 9 November (<!--=score.weights_agreed_9_nov_2026.h-->35<!--/--> / <!--=score.weights_agreed_9_nov_2026.s-->20<!--/--> /
<!--=score.weights_agreed_9_nov_2026.f-->15<!--/--> / <!--=score.weights_agreed_9_nov_2026.c-->10<!--/--> / <!--=score.weights_agreed_9_nov_2026.a-->10<!--/--> /
<!--=score.weights_agreed_9_nov_2026.k-->10<!--/-->) a cafe is the top candidate on <!--=score.with_the_weights_agreed_9_nov.cafe_top-->42<!--/--> of the
<!--=frontage.storefronts-->62<!--/--> storefronts; with the default it is on <!--=score.top_candidate_is_a_cafe.of_storefronts-->29<!--/-->
(<!--=score.top_candidate_is_a_cafe.of_empty-->7<!--/--> of the <!--=frontage.empty-->24<!--/--> empty ones), and the top candidate differs on
<!--=score.with_the_weights_agreed_9_nov.top_candidate_changes-->19<!--/--> (<!--=score.with_the_weights_agreed_9_nov.of_empty-->10<!--/--> empty).

The set of 9 November stays on the page as the preset "Agreed on 9 November", and the Evidence tab shows the two
rankings side by side. **The sponsor has still to confirm the new default.** A building with no record at all still
scores <!--=score.a_building_with_no_record_scores.cafe-->54<!--/--> of 100 for a cafe or restaurant and
<!--=score.a_building_with_no_record_scores.shop-->48<!--/--> for a shop, from the street's record and the room on the block, so the page
shows every score next to its lift over such a building. `MODEL_CARD.md` has the table.

Also since 24 November 2026, the size input reads the estimated ground floor, as the rent does, and no longer the
floor area of the whole building: a storefront use takes the ground floor. With the whole building the top candidate
differs on <!--=score.with_the_whole_building_as_the_size.top_candidate_changes-->7<!--/--> storefronts
(<!--=score.with_the_whole_building_as_the_size.of_empty-->4<!--/--> empty). The history input counts independent kinds of source, so a
copy of a directory is not a second source.

## Rebuild

```bash
python3 team/extractor/extract.py            # only if the tenant list or a source changed
python3 team/comps/comps_engine.py           # rents; writes team/comps/comps_ranges.json
python3 team/validation/backtest.py          # about a minute; writes team/validation/out/
python3 team/explorer/build_explorer.py      # standard library only; writes index.html
python3 team/explorer/page_numbers.py        # needs Playwright for Python; reads the numbers off the built page
python3 team/numbers_of_record.py            # writes team/NUMBERS.md and fills the figures quoted in the documents
python3 -m unittest team/explorer/test_explorer_data.py team/explorer/test_page_rules.py team/explorer/test_page_browser.py
```

| File | What |
|---|---|
| `build_explorer.py` | Reads the extractor outputs, the evidence and tenant files, `properties.csv`, `storefront_assessments.csv`, `team/comps/comps_ranges.json` and `team/validation/out/backtest_v2.json`, and writes `index.html` |
| `template.html` | The page: layout, score and views |
| `extras.py` | The tenant list against the sponsor's assessments, houses, heritage-revival names, retail trades, long-standing businesses, typical sizes and the neighbourhood benchmarks |
| `page_numbers.py`, `out/page_numbers.json` | The numbers the built page computes in the browser (the ranking, the plan, the totals), saved so that documents and tests can read them |
| `concepts.json` | Three drafted concepts (written with AI assistance), every fact with its source |
| `library.json` | The case library (<!--=library.reuse_buildings-->32<!--/--> reuse buildings, <!--=library.corridors-->22<!--/--> corridors) and the evidence behind the community, neighbour and customer layers |
| `retail_types.json`, `typical_sqft.json` | Seven retail trades and the typical floor area of 20 uses, every claim with its source |
| `research/` | The desk research of 26 October 2026 merged into `library.json`, and the script that merged it |
| `test_explorer_data.py` | Sources, the neighbourhood arithmetic and the no-brand-names rule |
| `test_page_rules.py` | The empty list, houses, history without today's tenant, a copy of a source not counted as a second source, the evidence grades, one business counted once, ground floors, the size input rebuilt from the ground floor, no stored rent on a building in use, nothing ranked by money, and the statements removed after the sponsor's review |
| `test_page_browser.py` | What a reader sees: no dollar figure and no recommendation on a building in use or a house, candidates with evidence and the low case first on every empty storefront, one sheet per empty storefront, the cap, no broken number when every storefront is marked empty or in use, and nothing past the edge of a phone screen |
| `DISPLACEMENT.md` | What the displacement rating measures and how it could be used in planning |
| `MODEL_CARD.md` | What the page is for, what it must not be used for, how it was checked and where it fails |
| `index.html` | The built page (generated; do not edit by hand) |

## Rules kept

- **Uses, not buildings.** The page lists candidate uses for a building. It never ranks buildings or blocks by money,
  and nothing is ranked by money at all. There is no valuation, appraisal language or acquisition targeting.
- **Buildings in use.** No recommendation and no rent. The plan fills empty storefronts only.
- **Rent is for the space.** It comes from listed rents on the corridor and the estimated ground floor, with the low
  case first. It is not what a building is worth.
- **Ownership.** The page shows the kind of owner (company, individual, public body), from the state assessment
  snapshot in the export. It names no private individual.
- **Rules of the street.** The limits on taverns, liquor stores and pawnshops are cited to the Waverly Business Area
  Urban Renewal Plan (Ordinance 1029 of 24 May 1979, Amendment No. 2 of 4 December 1995). Every panel that states a
  rule says it is the team's reading as students, not legal advice. A team member still has to open the plan once and
  confirm the page numbers.
- **Feedback.** Team and sponsor votes are shown beside each score. They change scores only when switched on,
  because the sponsor's rules say the sponsor cannot override model results.
- **Named businesses.** This public version names no business as a possible tenant. Brand names go in reports only
  (the sponsor's rule, 26 October 2026), and a test checks the public files and the built page for them by hash. The
  page names businesses already trading on the frontage, the reuse projects and corridors in the case library, and
  the local operators whose own figures are checked against the sales scenarios.
- **Photos.** The sponsor's storefront photos are for the team only and are not in the repo or on the page.
- **Sources.** Every outside fact links to its source. The pipeline never drops the export's sensitivity-flagged
  records, as the repo requires; none is among the frontage records and none is quoted on the page.

## Known limits

The page lists them under "Evidence and method", and `MODEL_CARD.md` explains them. The main ones:

- **No human check yet.** A person has entered or checked <!--=human_checks.tenant_rows_entered_or_checked_by_a_person-->23<!--/-->
  of the <!--=human_checks.tenant_rows-->79<!--/--> tenant rows, <!--=human_checks.outcome_rows_checked_by_a_person-->0<!--/--> of the
  <!--=human_checks.outcome_rows-->52<!--/--> "use today" rows on the other blocks and
  <!--=human_checks.comps_library_rows_checked_by_a_person-->0<!--/--> of the <!--=human_checks.comps_library_rows-->318<!--/--> rows of the comps
  library.
- **The back-test does not pass the agreed rule** (p = <!--=backtest.p_1960|p-->0.055<!--/--> after a leak was fixed;
  <!--=backtest.p_1960_before_leak_fix|p-->0.023<!--/--> before). No dollar figure on the page rests on history.
- **History records can sit on the wrong building.** <!--=evidence.placed_by_the_next_parcel-->691<!--/--> history rows
  (<!--=evidence.share_placed_by_the_next_parcel|pct-->21%<!--/-->) were placed by the next street number, and the extractor has
  found <!--=evidence.extractor_against_hand_timelines.independent.recall-->28<!--/-->% of the reference uses from sources that
  were not used to build the references.
- **The score has not been tested as a whole.** The back-test asks whether history predicts use. It does not test
  the candidates the score puts first.
- **Ground floors are estimates** from building outlines, because the export records whole buildings only. The size
  input and the rent both read them.
- **The default weights have still to be confirmed by the sponsor.** Community and precedents are switched off, not
  fixed.

## AI use

Built with Claude (October and November 2026) from the team's notes and the sources linked in the data. Before
merge, a team member reviews the code, checks a sample of the case library and the concept facts against their
sources, and signs below.

Checked by: ____________________ Date: __________
