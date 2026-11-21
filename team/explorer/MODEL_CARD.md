# Model card: Greenmount frontage explorer

Working draft, 21 November 2026. Covers the use score (v0.4), the evidence grades, the block plan, the comps at three
levels and the displacement flags. The rent figures have their own card: `team/comps/MODEL_CARD.md`. The back-test is
described in `team/validation/README.md`. Every number below is filled in from `team/NUMBERS.md`.

## What it is for

- **What it does.** It helps the sponsor's team and the CUSP team talk about one question, with sources: what could
  each empty storefront on Greenmount Ave (E 29th to E 33rd St) become, given what it was?
- **What it shows.** For each empty storefront, a short list of candidate uses, each with the evidence at that address
  and a statement of how much of its score comes from the building. For the block, one candidate per empty storefront
  under a cap, with a rent-pressure watch. For the space, a rent range from listed rents.
- **Who it is for.** Planning conversations, tenant recruiting and owner outreach. It is a pilot for the Property
  Dossier.
- **Status.** A working draft. No part of it has been checked by a second person, and the score has not been tested
  as a whole.

## What it must not be used for

- A valuation, appraisal or price for any building, or a promise of income.
- Choosing buildings to buy, or ranking buildings, blocks, uses or plans by money.
- Pressuring or replacing a business that trades today. The page makes no recommendation and shows no rent for a
  building in use or a house; a test opens the panel, the compare view, the Money page and the Comps page for every
  such building and fails if a dollar figure, a suggested use or a conversion cost appears.
- Deciding anyone's eligibility for a programme or a loan.
- Legal advice. The rules shown are the team's reading as students.

## How it works

1. **Which storefronts are empty.** The tenant list, which follows the sponsor's storefront audit of November 2026:
   <!--=frontage.empty-->24<!--/--> of <!--=frontage.storefronts-->62<!--/--> storefronts. <!--=frontage.houses-->7<!--/--> houses with no shop front are left
   out. A business in two street numbers counts once.
2. **Rules first.** C-1 zoning (the city's neighbourhood business zone, Baltimore code Table 10-301) and the Waverly
   Business Area Urban Renewal Plan remove uses that are not allowed and mark the ones that need an approval.
3. **Score.** Each allowed use gets a score from six inputs, with the weights agreed with the sponsor on 9 November
   2026 (<!--=score.weights_agreed_9_nov_2026.h-->35<!--/--> / <!--=score.weights_agreed_9_nov_2026.s-->20<!--/--> /
   <!--=score.weights_agreed_9_nov_2026.f-->15<!--/--> / <!--=score.weights_agreed_9_nov_2026.c-->10<!--/--> /
   <!--=score.weights_agreed_9_nov_2026.a-->10<!--/--> / <!--=score.weights_agreed_9_nov_2026.k-->10<!--/-->):
   - **Heritage:** the decades the use is on record at the building. Today's tenant is not counted as history
     (it was until 21 November 2026).
   - **Room on the block:** how many of the use are already on the block side and on the corridor, against the
     corridor's 1920-23 mix.
   - **Size fit:** the building's floor area against the sourced typical range of the use.
   - **Community:** what residents asked for or objected to. The same for every building.
   - **Neighbours:** a matrix grounded in law and research.
   - **Precedents:** how the most similar reuse cases in a hand-picked library turned out. <!--=library.cases_with_a_cafe-->20<!--/--> of the
     <!--=library.reuse_buildings-->32<!--/--> cases include a cafe or restaurant, so the input runs from
     <!--=score.inputs_by_use.cafe.precedents.0-->54<!--/--> to <!--=score.inputs_by_use.cafe.precedents.1-->100<!--/--> (of 100) for a cafe across the storefronts and is
     <!--=score.inputs_by_use.showroom.precedents.1-->0<!--/--> for a showroom at every one.
4. **Lift.** Every score is shown next to the score the same use gets at a building with no record at all, so a
   reader can see how much comes from this building.
5. **Evidence grade.** Each candidate carries one of four grades: two independent kinds of source that name the
   address and date from the building standing there; one kind; records placed by inference only (a neighbouring
   street number or the old York Road numbering); or no record of the use at the address. A sponsor record that
   transcribes a directory counts as the same kind of source as the directory.
6. **Block plan.** Candidates are placed one at a time, highest score first, under a cap of three of a kind per
   block side. Only empty storefronts are planned.
7. **Rent.** The corridor's rent level from listed rents, times the estimated ground floor, low case first. It is the
   same whatever the use. A separate flag says whether a business of each kind could cover the listed rent for that
   use at typical sales. Nothing is ranked by money.
8. **Ground floor.** The export records the floor area of whole buildings only. The ground floor is estimated as the
   smallest of the building outline, the recorded floor area and the lot; the upper bound is the smaller of the
   recorded floor area and the lot. Where the outline is missing or covers under half of the upper bound, the sheet
   says "measure first".
9. **Rent-pressure watch.** Block sides where the plan fills three or more storefronts at once, with the businesses
   trading there (long-standing ones first). The flag it replaces could not fire.
10. **Firmness.** For each candidate, the share of 1,000 nearby weightings under which it stays first.

## The cafe prior, and what the page does about it

The sponsor's review found that a cafe wins almost everywhere. The table is rebuilt from the page on every run.

| Ranking | Storefronts where a cafe or restaurant is the top candidate | Top candidate differs from the agreed ranking |
|---|---|---|
| Agreed weights | <!--=score.top_candidate_is_a_cafe.of_storefronts-->46<!--/--> of <!--=frontage.storefronts-->62<!--/--> (<!--=score.top_candidate_is_a_cafe.of_empty-->12<!--/--> of the <!--=frontage.empty-->24<!--/--> empty) | |
| Heritage weight at zero | <!--=score.if_heritage_weight_is_zero.cafe_top-->54<!--/--> | <!--=score.if_heritage_weight_is_zero.top_candidate_changes-->14<!--/--> (<!--=score.if_heritage_weight_is_zero.of_empty-->9<!--/--> of the empty) |
| Without community and precedents | <!--=score.without_community_and_precedents.cafe_top-->32<!--/--> | <!--=score.without_community_and_precedents.top_candidate_changes-->19<!--/--> (<!--=score.without_community_and_precedents.of_empty-->8<!--/--> of the empty) |
| Firmest records only | <!--=score.firmest_records_only.cafe_top-->46<!--/--> | <!--=score.firmest_records_only.top_candidate_changes-->2<!--/--> (<!--=score.firmest_records_only.of_empty-->1<!--/--> of the empty) |
| Today's tenant counted as history (the page until 21 November) | <!--=score.with_todays_tenant_as_history.cafe_top-->44<!--/--> | <!--=score.with_todays_tenant_as_history.top_candidate_changes-->4<!--/--> (<!--=score.with_todays_tenant_as_history.of_empty-->0<!--/--> of the empty) |

A building with no record at all scores <!--=score.a_building_with_no_record_scores.cafe-->63<!--/--> of 100 for a cafe or
restaurant, because community and precedents favour it everywhere. Of the <!--=frontage.storefronts-->62<!--/--> top candidates,
<!--=score.evidence_behind_top_candidates.two-->39<!--/--> rest on two kinds of source at the address,
<!--=score.evidence_behind_top_candidates.one-->5<!--/--> on one kind, <!--=score.evidence_behind_top_candidates.placed-->1<!--/--> on
inference only and <!--=score.evidence_behind_top_candidates.none-->17<!--/--> have no record of the use there;
<!--=score.top_candidate_no_higher_than_no_record-->6<!--/--> score no higher than at a building with no record.

**Open decision.** The review asks the team to rebalance or drop the community and precedent inputs until they are
sourced per parcel. The weights were agreed with the sponsor, so the default has not been changed by one person: the
page offers the ranking without the two inputs as the preset "Building evidence only" and shows the table above. The
team and the sponsor decide whether it becomes the default.

## How it was checked

| Check | Result | Where |
|---|---|---|
| Extractor against four hand-built timelines, using only sources that were not used to build them | finds <!--=evidence.extractor_against_hand_timelines.independent.recall-->28<!--/-->% of the reference uses (<!--=evidence.extractor_against_hand_timelines.independent.found-->9<!--/--> of <!--=evidence.extractor_against_hand_timelines.independent.rows-->32<!--/-->); the research plan's target is 90% | `team/extractor/out/validation.md` |
| The same with all sources. Not a test: the references were built from the same sponsor records | <!--=evidence.extractor_against_hand_timelines.all_sources.recall-->78<!--/-->% | the same |
| Does history predict use today? Back-test v2, corrected 17 November 2026, on <!--=backtest.parcels-->52<!--/--> Greenmount parcels outside the frontage, records up to 1960 | **Does not pass the agreed rule.** p = <!--=backtest.p_1960|p-->0.055<!--/--> (<!--=backtest.p_1960_before_leak_fix|p-->0.023<!--/--> before the leak was fixed). On blocks the model had not seen, the forecast error goes from <!--=backtest.held_out_log_loss.0|f4-->0.6070<!--/--> to <!--=backtest.held_out_log_loss.1|f4-->0.6050<!--/-->, a gain that cannot be told from zero, and the ranking measure from <!--=backtest.held_out_auc.0|f3-->0.631<!--/--> to <!--=backtest.held_out_auc.1|f3-->0.632<!--/-->. Ordinary storefront trades alone: p = <!--=backtest.p_1960_storefront_trades_only|p-->0.455<!--/--> | `team/validation` |
| First back-test (hit or miss, frontage, records up to 1960) | <!--=backtest.first_back_test_1960.hit-->21<!--/--> of <!--=backtest.first_back_test_1960.of-->35<!--/-->, against <!--=backtest.first_back_test_1960.plain_guess-->22<!--/--> for a plain guess | Evidence and method |
| The score as a whole | Not tested yet. The test planned for 30 November to 6 December holds out block sides and compares the candidates with a ranking that has no history | |
| Rent ranges on listings the model had not seen | <!--=comps.held_out.inside_widened_range-->48<!--/--> of <!--=comps.held_out.rows-->59<!--/--> inside the widened range | `team/comps` |
| What a reader sees | A browser test opens every tab and the panel of every building | `test_page_browser.py` |
| The rules of the page | Tests for the empty list, houses, history without today's tenant, the evidence grades, ground floors and the statements removed after the review | `test_page_rules.py` |
| Case library | Every value carries the URL of a page read on 26 October 2026; four claims re-checked by hand | `research/` |
| No brand names in the public build | A test checks the public files and the built page against hashed names | `test_explorer_data.py` |
| A second person | None yet. See "What a person has checked" in `team/NUMBERS.md` | |

## Where it fails or is weak

- **Records on the wrong building.** <!--=evidence.placed_by_the_next_parcel-->691<!--/--> history rows
  (<!--=evidence.share_placed_by_the_next_parcel|pct-->21%<!--/-->) were placed by the next street number down or up, and the
  sponsor's review found coding errors in a sample of the sponsor's narrative records. The evidence grade shows which
  candidates depend on such rows; the fixes to the extractor are open.
- **"On record" is easy to earn.** Of <!--=evidence.uses_on_record_parcel_by_kind-->229<!--/--> uses on record (parcel by kind,
  housing left out), <!--=evidence.of_which_two_kinds_of_source_at_the_address-->89<!--/--> meet the strict definition in point 5.
- **History and the use today.** On blocks the model had not seen, history adds nothing measurable for ordinary
  storefront trades. What signal there is comes from garages: all <!--=backtest.automotive.of_which_today-->4<!--/--> parcels with
  an automotive record before 1960 are automotive today.
- **Selection.** The back-test can only use storefronts that are in use today
  (<!--=backtest.frontage_storefronts_tested-->38<!--/--> on the frontage). The candidates are for the
  <!--=backtest.frontage_empty_storefronts_not_tested-->24<!--/--> that are empty.
- **Who trades where.** Of the <!--=frontage.in_use-->38<!--/--> storefronts in use,
  <!--=frontage.in_use_named_from_a_search_listing_only-->15<!--/--> rest on a search listing for the name of the business. The
  room-on-the-block and neighbour inputs read those names.
- **Weights are a judgement.** A close call (labelled on the page) can flip under other weights.
- **Size fit reads the whole building,** not the ground floor.
- **Ground floors are estimates.** <!--=plan.to_measure-->3<!--/--> of the <!--=plan.sheets-->24<!--/--> empty storefronts are marked "measure
  first".
- **Rent rests on listed rents:** <!--=comps.asking-->57<!--/--> asking rents and <!--=comps.in_place-->3<!--/--> rents in place, none a newly
  signed lease, and <!--=comps.waverly.rows-->6<!--/--> rows in Waverly.
- **The outline of the frontage was traced by hand** in the first week. The page lists the Greenmount parcels in the
  export between 2900 and 3299 that it leaves out, including 3001 and 3005, which the review asked the team to
  confirm.
- **Rare buildings, costs and case statuses.** Theatres, churches and banks have few comparable projects. Project
  costs differ in scope and are adjusted for inflation only. Each case status is dated, and "operating" needs a 2025
  or 2026 source.
- **Displacement ratings** rest on published sources. "Unknown" does not mean none.
- **Neighbourhood comparisons.** Three of the eight benchmark neighbourhoods rest on one or two rent rows. Vacancy is
  measured differently from place to place. Read them as orders of magnitude.
- **Data refreshes** can retire parcel ids. Rebuild after each refresh.

## Data, people and rights

- **Data.** Sponsor data is CC BY 4.0. Sensitivity-flagged records are never dropped and never quoted.
- **No private individuals.** The page shows the kind of owner (a company, a church or nonprofit, an individual),
  never a private person's name. The case library names organizations and businesses only.
- **No brand names.** Brand names go in reports only (the sponsor's rule, 26 October 2026).
- **Photos.** The sponsor's storefront photos are for the team only and are not in the repo.

## Maintenance

Rebuild in the order given in `README.md`, then run every test file listed in `team/NUMBERS.md`. When the case
library is updated, keep the URL and access date for every value. Re-rate displacement only under the written
rubric, and keep any earlier rating as `displacement_v1`.
