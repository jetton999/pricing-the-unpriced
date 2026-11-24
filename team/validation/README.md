# Validation: does a building's past predict its use today?

**Result.** On Greenmount parcels the model had not seen, the back-test **does not pass** the rule agreed with the
sponsor on 9 November 2026. The one-sided shuffle test gives **p = <!--=backtest.p_1960|p-->0.055<!--/-->** against a bar of 0.05, and
on held-out blocks the gain from history cannot be told from zero. What signal there is comes from garages. For
ordinary storefront trades (food and drink, retail goods, personal services) history adds nothing measurable beyond
how common each use is on the street: p = <!--=backtest.p_1960_storefront_trades_only|p-->0.455<!--/-->.

Every number in this file is filled in from `team/NUMBERS.md`. The full tables are in `out/backtest_v2.md`, which
`backtest.py` writes on every run, and `out/backtest_v2.json` holds every run.

## What the result means for the page

The plan written for this test (`PLAN_backtest_v2.md`) says what happens if the rule fails: <!--=backtest.if_it_fails-->the money layer shows rent and revenue ranges from comparable listings only, labelled as planning figures, and nothing that ranks uses or plans by history and money together (PLAN_backtest_v2.md)<!--/-->.
The explorer follows that branch. Its rent figures come from listed rents only and are for the space, the same
whatever the use, and nothing on it ranks uses or plans by money. Whether any dollar total stays on the Block plan
page is for the team and the sponsor to decide together.

## The correction of 17 November 2026

The sponsor's review found a leak in the test on the other Greenmount blocks. The export files a National Register
summary row under a building's build year, but the row states the building's use as of 2013. The frontage sample
left such rows out; the other-blocks sample did not, so 12 of them counted as history before 1960. With the same
exclusion applied to both samples:

| | Before the fix (not valid) | After |
|---|---|---|
| Shuffle test, records up to 1960 | p = <!--=backtest.p_1960_before_leak_fix|p-->0.023<!--/--> | **p = <!--=backtest.p_1960|p-->0.055<!--/-->** |
| Food and drink: parcels with it on record before 1960, and how many have it today | <!--=backtest.by_kind.food & drink.of_which_today_before_leak_fix-->6<!--/--> of <!--=backtest.by_kind.food & drink.parcels_with_it_on_record_before_leak_fix-->19<!--/--> | <!--=backtest.by_kind.food & drink.of_which_today-->4<!--/--> of <!--=backtest.by_kind.food & drink.parcels_with_it_on_record-->16<!--/--> (base rate <!--=backtest.by_kind.food & drink.base_rate|pct-->31%<!--/-->) |
| Food and drink adds to the test statistic | <!--=backtest.by_kind.food & drink.adds_to_statistic_before_leak_fix|s2-->+0.52<!--/--> | <!--=backtest.by_kind.food & drink.adds_to_statistic|s2-->-0.50<!--/--> |
| Personal services adds | <!--=backtest.by_kind.personal services.adds_to_statistic_before_leak_fix|s2-->+1.49<!--/--> | <!--=backtest.by_kind.personal services.adds_to_statistic|s2-->+0.47<!--/--> |
| Automotive adds | <!--=backtest.by_kind.automotive.adds_to_statistic_before_leak_fix|s2-->+2.87<!--/--> | <!--=backtest.by_kind.automotive.adds_to_statistic|s2-->+2.87<!--/--> |

The "before" column reproduces the figures in the sponsor's review. Both runs are kept in the JSON (`other_blocks`
and `other_blocks_before_leak_fix`).

## The result, piece by piece (records up to 1960)

| | |
|---|---|
| Parcels, pairs of a parcel and a kind of use, pairs true today | <!--=backtest.parcels-->52<!--/-->, <!--=backtest.pairs-->416<!--/-->, <!--=backtest.pairs_true_today-->57<!--/--> |
| Shuffle test, all eight kinds of use | p = <!--=backtest.p_1960|p-->0.055<!--/--> |
| Records up to 1940 (secondary) | p = <!--=backtest.p_1940|p-->0.024<!--/--> |
| Ordinary storefront trades only | p = <!--=backtest.p_1960_storefront_trades_only|p-->0.455<!--/--> |
| Every kind except automotive | p = <!--=backtest.p_1960_without_automotive|p-->0.484<!--/--> |
| Automotive only | p = <!--=backtest.p_1960_automotive_only|p-->0.004<!--/--> |
| Automotive: parcels with it on record before 1960, and how many are automotive today | <!--=backtest.automotive.of_which_today-->4<!--/--> of <!--=backtest.automotive.parcels_with_it_on_record-->4<!--/--> (base rate <!--=backtest.automotive.base_rate|pct-->17%<!--/-->) |
| One parcel left out at a time | p from <!--=backtest.leave_one_parcel_out.min|p-->0.028<!--/--> to <!--=backtest.leave_one_parcel_out.max|p-->0.148<!--/-->; <!--=backtest.leave_one_parcel_out.below_0_05-->12<!--/--> of <!--=backtest.leave_one_parcel_out.runs-->52<!--/--> runs below 0.05 |
| Without the multi-tenant centre (<!--=backtest.multi_tenant_parcels|list-->2801<!--/--> Greenmount) | p = <!--=backtest.p_1960_without_multi_tenant|p-->0.087<!--/--> |
| History coded from linked businesses and directory lines only | p = <!--=backtest.p_1960_stated_uses_only|p-->0.086<!--/--> |
| Low-confidence codes of today's use left out | p = <!--=backtest.p_1960_without_low_confidence|p-->0.084<!--/--> |
| With a control for how much is on record at the parcel (a likelihood-ratio test, not the shuffle test) | p = <!--=backtest.p_1960_with_a_control_for_how_much_is_on_record|p-->0.114<!--/--> |
| Held-out forecast error (log loss), without and with history | <!--=backtest.held_out_log_loss.0|f4-->0.6070<!--/--> to <!--=backtest.held_out_log_loss.1|f4-->0.6050<!--/--> |
| Held-out gain per row, with a 95% interval | <!--=backtest.held_out_gain_per_row|s4-->+0.0020<!--/--> (<!--=backtest.held_out_gain_ci95.0|s4-->-0.0043<!--/--> to <!--=backtest.held_out_gain_ci95.1|s4-->+0.0088<!--/-->) |
| Held-out ranking measure (AUC), without and with history | <!--=backtest.held_out_auc.0|f3-->0.631<!--/--> to <!--=backtest.held_out_auc.1|f3-->0.632<!--/--> |
| The same measure on the data the model was fitted to. It flatters; do not quote it alone | <!--=backtest.in_sample_auc.0|f3-->0.707<!--/--> to <!--=backtest.in_sample_auc.1|f3-->0.724<!--/--> |

How to read it:

- **History predicts use where the building is specialised.** A garage stays a garage. For an ordinary storefront,
  what was there before 1960 says little about what is there now.
- **The result is fragile.** It moves across the 0.05 line when single parcels are left out.
- **The held-out gain is tiny and its interval spans zero.** The rule's second condition (a lower held-out log loss)
  is met in the letter only.
- **The 1940 cut-off gives a smaller p, but the rule names 1960** as the cut-off that decides, so 1960 is the result.
- **The held-out figures moved after 17 November** because the frontage sample changed: the corrected tenant list
  leaves <!--=backtest.frontage_storefronts_tested-->38<!--/--> storefronts in use to fit the coefficients on.

## Who the test covers

The test can only use storefronts with a business today. On this frontage that is
<!--=backtest.frontage_storefronts_tested-->38<!--/-->; the candidates on the page are for the
<!--=backtest.frontage_empty_storefronts_not_tested-->24<!--/--> that are empty. The two groups have about the same amount of
history on record before 1960 (<!--=backtest.decades_on_record_empty_against_in_use.0|f2-->6.75<!--/--> and
<!--=backtest.decades_on_record_empty_against_in_use.1|f2-->6.79<!--/--> use-decades a parcel; p =
<!--=backtest.decades_on_record_p|p-->0.986<!--/-->), and the mix of uses on record does not differ measurably (p =
<!--=backtest.mix_of_uses_on_record_empty_against_in_use.p|p-->0.177<!--/-->). That does not show the empty storefronts behave like
the ones in use; it shows only that their records look alike.

## What is not tested yet

- **The score itself.** This test asks whether history predicts use. It does not test the candidates the explorer
  puts first, which also depend on five other inputs. The next test holds out block sides and compares the
  candidates with a ranking that has no history, with intervals (planned for 30 November to 6 December 2026).
- **The first back-test** (hit or miss, frontage, records up to 1960) scored
  <!--=backtest.first_back_test_1960.hit-->21<!--/--> of <!--=backtest.first_back_test_1960.of-->35<!--/-->, against
  <!--=backtest.first_back_test_1960.plain_guess-->22<!--/--> for a plain guess. It does not beat the guess.

## What a person still has to check

- **The uses today on the other blocks.** All <!--=backtest.outcome_rows-->52<!--/--> rows of
  `outcomes_other_greenmount_2026-10.csv` were coded with AI assistance from the sponsor's storefront summaries,
  without looking at history; a person has checked <!--=backtest.outcome_rows_checked_by_a_person-->0<!--/-->. With so few pairs
  carrying the result, one coding error can change it. `two_coder/` has the sheets for two team members to code
  them independently and a script that reports their agreement.
- **The history codes.** The extractor codes the sponsor's narrative records by keyword, and the review found errors
  in a sample. The run on linked businesses and directory lines only (above) is a partial check. `two_coder/` also
  draws 200 history records for the same two-coder check.
- **The four blind reference timelines** (`blind_timelines/`): the parcels are drawn and each has a reading packet.
  The timelines need a person outside the team and are not started.

## How the plan was written, said accurately

The analysis plan was committed four minutes before the first results, in the same working session
(`PLAN_backtest_v2.md`). It names the cut-off, the test and the rule, but the plan, the coded outcomes and the first
results all come from one working session, so it is not an independent pre-registration. For the spring test the plan will be lodged with the faculty advisor, by dated email,
before any data is coded.

## How it was done

1. **The question.** For each parcel and each of eight kinds of use, is that use there today (yes or no)?
2. **The base model.** One intercept per kind of use: "guess the common uses".
3. **The history model.** The base model plus a coefficient on log(1 + decades on record before the cut-off).
4. **The primary test.** Shuffle whole parcel histories among parcels on the same block side, 10,000 times, and
   count how often the shuffled histories line up with today's uses as well as the real ones. Keeping block sides
   fixed controls for location.
5. **The held-out check.** Coefficients fitted on this frontage are applied without refitting to the other blocks.
   The interval for the gain comes from resampling parcels.
6. **Where the data come from.** Use today on the other blocks: the sponsor's October 2026 storefront summaries.
   History on the other blocks: the sponsor's curated records that state a use, coded with the extractor's rules,
   without the National Register summary rows. Use today on the frontage: the tenant list.

## What this does not show

- **It does not show that history causes the use.** The same buildings suit the same uses, so history partly stands
  in for building form.
- **It is one corridor,** and the parcels are few.
- **A result that does not pass is weak evidence of no effect.** The other blocks have thinner records than the
  frontage.

## Run it

```bash
python3 team/validation/backtest.py              # about a minute; writes out/backtest_v2.json and out/backtest_v2.md
python3 -m unittest team/validation/test_backtest.py
```
