# Response to the sponsor's review of 17 November 2026

Finding by finding: what was done, where to see it, and what is still open. Written on 21 November 2026 for the
branch `team/week7-review-fixes`. Every number is filled in from `team/NUMBERS.md`.

**Status words.** *Done*: changed and covered by a test. *Partly*: the page or the report now says it; the cause is
not fixed. *Open*: not started, with who has to do it. Work that only a person can do (checking, signing, coding by
two people, reading a source) is marked *People*.

## In short

- **Done:** the back-test leak and everything that reports the test (A1 to A5, A9, A10, C7); the empty list, houses
  and one business counted once (C3); ground floors and the low case first (C4); no recommendation and no dollars on
  a building in use (C5); the rule cited to the plan (C6); the rent engine on one basis with no ranking by money
  (D1, D3, D6); the private step and the statements about the sponsor (F1 to F3); one generated numbers file that
  the documents quote (E6, C8).
- **Partly:** the cafe prior is shown and measured, but the weights are unchanged (C1); history without today's
  tenant is in, the test of the score itself is not (C2); the evidence grade shows which candidates rest on inferred
  placements, but the extractor still makes them (B1 to B3); the stale counts in the extractor README are listed, not
  yet changed (B7).
- **Open, people:** every human check (A6, B6, D4, D5, F4, E7): <!--=human_checks.checked_by_lines_signed-->0<!--/--> of
  <!--=human_checks.checked_by_lines-->8<!--/--> "Checked by" lines are signed,
  <!--=human_checks.outcome_rows_checked_by_a_person-->0<!--/--> of <!--=human_checks.outcome_rows-->52<!--/--> outcome rows and
  <!--=human_checks.comps_library_rows_checked_by_a_person-->0<!--/--> of <!--=human_checks.comps_library_rows-->318<!--/--> library rows are
  checked, and <!--=human_checks.blind_timelines_built-->0<!--/--> of <!--=human_checks.blind_timelines_needed-->4<!--/--> blind timelines are
  built. The sheets and scripts for that week are in place.
- **Open, extractor:** the address table, the coding of narrative records, the definition of "proven", the crosswalk
  and the silent drops (B1 to B5, A8).
- **Open, literature review:** E1 to E5. Its quoted back-test result is the one from before the leak was fixed.

## A. Validation

| # | Finding | Status | What was done, and where |
|---|---|---|---|
| A1 | Leak: National Register summary rows counted as history on the other blocks | Done | The same exclusion on both samples. p = <!--=backtest.p_1960|p-->0.055<!--/--> after, <!--=backtest.p_1960_before_leak_fix|p-->0.023<!--/--> before; both runs are kept. A test fails if such a row reaches either sample. `team/validation/backtest.py`, `test_backtest.py` |
| A2 | With the leak fixed the rule fails | Done; one decision open | Every document and the page say "does not pass". The page follows the failure branch written in the plan: rent from listed rents only, for the space, and nothing ranked by money. **Open for the team and the sponsor:** whether any dollar total stays on the Block plan page |
| A3 | The signal is automotive | Done | Results by kind of use: ordinary storefront trades p = <!--=backtest.p_1960_storefront_trades_only|p-->0.455<!--/-->, every kind except automotive <!--=backtest.p_1960_without_automotive|p-->0.484<!--/-->, automotive only <!--=backtest.p_1960_automotive_only|p-->0.004<!--/-->. `team/validation/out/backtest_v2.md`, the page's Evidence tab |
| A4 | Fragile; multi-tenant centre | Done | One parcel left out at a time: p from <!--=backtest.leave_one_parcel_out.min|p-->0.028<!--/--> to <!--=backtest.leave_one_parcel_out.max|p-->0.148<!--/-->. Without <!--=backtest.multi_tenant_parcels|list-->2801<!--/--> Greenmount: <!--=backtest.p_1960_without_multi_tenant|p-->0.087<!--/--> |
| A5 | Transfer gain not distinguishable from zero | Done | Gain <!--=backtest.held_out_gain_per_row|s4-->+0.0020<!--/--> a row, 95% interval <!--=backtest.held_out_gain_ci95.0|s4-->-0.0043<!--/--> to <!--=backtest.held_out_gain_ci95.1|s4-->+0.0088<!--/-->; held-out AUC <!--=backtest.held_out_auc.0|f3-->0.631<!--/--> to <!--=backtest.held_out_auc.1|f3-->0.632<!--/-->, quoted beside the log loss wherever the result appears |
| A6 | Outcomes unverified | Open, people | `team/validation/two_coder/` has a blank sheet per coder for the <!--=backtest.outcome_rows-->52<!--/--> parcels, a script that reports agreement and Cohen's kappa, and a way to rerun the back-test on the agreed codes |
| A7 | The plan is four minutes older than the results | Done for the fall; open for spring | `PLAN_backtest_v2.md` and `README.md` now say so. Spring: lodge the plan with the faculty advisor by dated email before any data is coded |
| A8 | Hindsight in the text being classified | Partly | A run that codes history from linked businesses and directory lines only: p = <!--=backtest.p_1960_stated_uses_only|p-->0.086<!--/-->. The keyword rules are unchanged (see B2) |
| A9 | Selection: the test covers storefronts in use, the plan is for empty ones | Done | Stated wherever the test is reported. The two groups' records before 1960 are compared in `out/backtest_v2.md` |
| A10 | Stale results file; "awaits sign-off"; two different log-loss figures | Done | Regenerated; one figure per quantity, from `team/NUMBERS.md` |

## B. Historical-evidence pipeline

The extractor's method is unchanged in this branch. What changed is what the page does with its output.

| # | Finding | Status | What was done, and where |
|---|---|---|---|
| B1 | The next-parcel rule credits other buildings' histories | Partly. Open, extractor | <!--=evidence.placed_by_the_next_parcel-->691<!--/--> history rows (<!--=evidence.share_placed_by_the_next_parcel|pct-->21%<!--/-->) are placed this way. Each candidate on the page now shows how many of its records name the address and how many were placed by inference, and a candidate that rests on inference only is graded so. The reviewed address table is not built |
| B2 | Keyword coding of narrative summaries | Open, extractor and people | `team/validation/two_coder/` draws 200 coded history records (100 from the sponsor's records) for two people to code. The rules are unchanged |
| B3 | "Proven" is too easy to earn | Partly | The page says "on record", and grades each use by the review's definition (two independent kinds of source, a stated address, a named trade, the standing building): <!--=evidence.of_which_two_kinds_of_source_at_the_address-->89<!--/--> of <!--=evidence.uses_on_record_parcel_by_kind-->229<!--/--> uses on record meet it. The ranking with only those records is in the table on the Evidence tab. The extractor's own rule is unchanged |
| B4 | Crosswalk errors | Open, extractor | |
| B5 | Silent drops | Open, extractor | |
| B6 | Circular validation; 96% and 91% quoted | Partly. Open, people | The page and the model card lead with the independent figure: <!--=evidence.extractor_against_hand_timelines.independent.recall-->28<!--/-->% (<!--=evidence.extractor_against_hand_timelines.independent.found-->9<!--/--> of <!--=evidence.extractor_against_hand_timelines.independent.rows-->32<!--/-->). The two-coder gold set is ready to be coded |
| B7 | Stale READMEs | Partly | `team/NUMBERS.md` lists each count in the extractor README that differs from the data today, and a test keeps that list current. The README is its author's file, so it is not changed here |
| B8 | 3001 and 3005 missing; prototype has no banner | Partly | The page's known limits list every Greenmount parcel in the export between 2900 and 3299 that it leaves out, with 3001 and 3005 named. **Open:** a "superseded" banner on `team/prototype_v0/README.md`, which is its author's file; and confirming with the sponsor whether 3001 and 3005 belong |

## C. Explorer and scoring model

| # | Finding | Status | What was done, and where |
|---|---|---|---|
| C1 | Cafe prior | Partly; one decision open | Every score is shown with its lift over a building with no record (<!--=score.a_building_with_no_record_scores.cafe-->63<!--/--> of 100 for a cafe). The Evidence tab publishes the table: cafe is the top candidate on <!--=score.top_candidate_is_a_cafe.of_storefronts-->46<!--/--> of <!--=frontage.storefronts-->62<!--/--> storefronts, on <!--=score.if_heritage_weight_is_zero.cafe_top-->54<!--/--> with the heritage weight at zero, and on <!--=score.without_community_and_precedents.cafe_top-->32<!--/--> without community and precedents. That last ranking is a preset. **Open for the team and the sponsor:** whether it becomes the default, since the weights were agreed on 9 November |
| C2 | Today's tenant counts as heritage | Done; the re-test is open | The 2026 tenant check no longer feeds the heritage score; the top candidate changed on <!--=score.with_todays_tenant_as_history.top_candidate_changes-->4<!--/--> storefronts. A test fails if it returns. **Open (30 November to 6 December):** test the candidates themselves on held-out block sides against a ranking with no history |
| C3 | Vacancy list | Done | <!--=frontage.empty-->24<!--/--> empty, from the tenant list, which follows the sponsor's audit. <!--=frontage.houses-->7<!--/--> houses are left out of the plan. One business in two street numbers counts once. Each in-use row says how the list knows it: <!--=frontage.in_use_named_from_a_search_listing_only-->15<!--/--> of <!--=frontage.in_use-->38<!--/--> rest on a search listing only |
| C4 | Rent total used whole-building area | Done as an estimate; measuring is open | Ground floor estimated from building outlines: <!--=plan.ground_floor_sq_ft-->57,133<!--/--> sq ft for the <!--=plan.sheets-->24<!--/--> empty storefronts (the whole buildings are <!--=plan.whole_building_sq_ft-->82,606<!--/-->). The low case leads: <!--=plan.space_rent_low|usd-->$538,200<!--/--> a year, <!--=plan.space_rent_mid|usd-->$937,600<!--/--> in the middle. <!--=plan.to_measure-->3<!--/--> ground floors are marked "measure first" |
| C5 | Rent-pressure flag cannot fire; replacement uses with dollars on occupied buildings | Done | A watch that fires where the plan fills three or more storefronts on a block side (<!--=plan.pressure.block_sides-->4<!--/--> block sides, <!--=plan.pressure.businesses-->11<!--/--> businesses today). A building in use shows no recommendation and no rent; a browser test opens every such panel |
| C6 | Legal rule stated as fact | Done; one reading open | Cited to the plan (Ordinance 1029 of 24 May 1979, Amendment No. 2 of 4 December 1995), with no attribution to the sponsor and "not legal advice" on every panel. **People:** open the plan once and confirm the page numbers |
| C7 | Back-test shown selectively | Done | Held-out figures lead; the in-sample figure is labelled as flattering; the first back-test is described as it is (<!--=backtest.first_back_test_1960.hit-->21<!--/--> of <!--=backtest.first_back_test_1960.of-->35<!--/--> against <!--=backtest.first_back_test_1960.plain_guess-->22<!--/-->) |
| C8 | Stale documents | Done; signing is open | Rewritten, with every figure filled in from `team/NUMBERS.md` |
| C9 | Tests cover sourcing only; jargon | Done | `test_page_rules.py` and `test_page_browser.py` cover the score, the plan, the empty list, names and the sponsor terms. Lease jargon is replaced by "before taxes and insurance"; "log loss" and "AUC" appear only beside a plain description |

## D. Comps engine

| # | Finding | Status | What was done, and where |
|---|---|---|---|
| D1 | The money ranking is an artifact | Done | Engine v2: one basis for every figure (listed rents), the sales check as a flag with three answers, and nothing ranked by money. `team/comps/MODEL_CARD.md` |
| D2 | Thin local evidence | Partly. Open, people | The rule order is fixed and the two Greenmount rents in place are read (R-080, R-081): <!--=comps.waverly.rows-->6<!--/--> Waverly rows. Rents by phone are planned for spring |
| D3 | "Percentiles" that are not | Done | Labelled low, mid and high scenarios; no probability |
| D4 | R-004 | Open, people | Flagged in the library, and the model card shows what rests on it. A person re-reads the listing |
| D5 | No verification on record | Open, people | `verified_by` and `verified_on` columns added to the three library files; <!--=comps.library_rows_checked_by_a_person-->0<!--/--> of <!--=comps.library_rows-->318<!--/--> filled |
| D6 | BENCH strings; unexplained sigma | Done | Both removed |

## E. Written work

| # | Finding | Status | What was done, and where |
|---|---|---|---|
| E1 to E5 | The literature review | Open, review owner | Version 2.1 is in the repo. It still quotes the back-test from before the leak was fixed and describes the withdrawn "supportable rent"; the corrected figures are in `team/NUMBERS.md` |
| E6 | Inconsistent numbers across documents | Done | `team/NUMBERS.md` and `team/numbers_of_record.json`, generated. Documents quote them through markers that the script fills, and a test fails when one is stale |
| E7 | No progress-report material in the repo | Open, team | |

## F. Public repo and the client agreement

| # | Finding | Status | What was done, and where |
|---|---|---|---|
| F1 | The private step for sales data | Done; one answer owed | The step and every mention are removed from the team's files. **The team still owes the sponsor the answer to its question** whether any such file was ever received |
| F2 | Statements about the sponsor | Done | The eleven places listed in the review are changed and the page rebuilt. A test searches the team's files and the built page for the phrases, by hash |
| F3 | A phrase about one apartment's tenant | Done | Removed from the library row |
| F4 | Team review of AI-collected content | Open, people | The verification week: `team/validation/two_coder/`, `team/validation/blind_timelines/`, the `verified_by` columns and the "Checked by" lines |

## What is on the sponsor

The review lists what the export cannot give yet. Three of those shape this branch: the export has whole-building
floor area only (so ground floors are estimates), National Register rows are filed under the build year (so they are
left out of the test), and the empty list is the sponsor's audit (so the page follows it and lets a reader change
it).
