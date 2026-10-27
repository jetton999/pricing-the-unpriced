# Validation: does a building's past predict its use today?

**Result (back-test v2, 26 October 2026).** On Greenmount parcels the model had never seen, a use
with a documented past at a building is more likely to be there today than its frequency on the
street predicts. At the 1960 cut-off, the one-sided permutation test gives **p = 0.023**. The
history model also has a lower held-out log loss than the base model when frontage coefficients
are applied to those parcels. The test therefore **passes the rule written down before it was
run** (`PLAN_backtest_v2.md`, commit `fac73ce`). The rule still needs the sponsor's sign-off. The
transfer gain is small, so the case rests mainly on the permutation test.

## In plain words

Take every pair of a building and a kind of use: for example, 3117 and "retail goods". For the
other Greenmount blocks at the 1960 cut-off:

| Record before 1960 | Pairs | Has that use in 2026 | Expected from how common the use is |
|---|---|---|---|
| none | 362 | 44 | 48.3 |
| 1 decade | 41 | 7 | 5.8 |
| 2 or more decades | 13 | 6 | 2.9 |

Uses on record for two or more decades are there today about twice as often as their frequency
on the street predicts. The numbers are small (13 pairs), which is why the test counts every
parcel and uses the gradient, not only the top group.

## All results

| Data set | Cut-off | Parcels (with history) | One-sided p, permutation | AUC, base to history | With a record-depth control |
|---|---|---|---|---|---|
| **Other Greenmount blocks (not seen before)** | 1960 | 52 (34) | **0.023** | 0.707 to 0.741 | p = 0.013 |
| Other Greenmount blocks | 1940 | 52 (33) | 0.007 | 0.707 to 0.743 | p = 0.003 |
| Other blocks, low-confidence codes left out | 1960 | 47 (32) | 0.035 | 0.729 to 0.767 | p = 0.031 |
| Frontage, all sources (exploratory) | 1960 | 44 (42) | 0.0004 | 0.839 to 0.870 | p = 0.0003 |
| Frontage, sponsor records only | 1960 | 44 (37) | 0.061 | 0.839 to 0.851 | p = 0.119 |

| Out-of-sample check | Cut-off | Log loss, base to history | AUC, base to history |
|---|---|---|---|
| Frontage coefficients (sponsor records) applied to the other blocks | 1960 | 0.6187 to 0.6145 | 0.604 to 0.600 |
| Frontage coefficients (all sources) applied to the other blocks | 1960 | 0.6187 to 0.6132 | 0.604 to 0.598 |
| Frontage, leave one block side out | 1960 | 0.3405 to 0.3304 | 0.789 to 0.830 |

Read the tables with these points in mind:

- **The other blocks are the test.** The model was chosen on the frontage, so the frontage
  p-values are exploratory and are not claimed.
- **The transfer improvement is small.** Log loss improves, but AUC does not. The frontage's base
  rates fit the other blocks poorly: there is more automotive and office use south of 29th Street.
  So the transfer mostly tests calibration, not ranking.
- **Sponsor-only records on the frontage are weaker** (p = 0.06). The team's directory, permit-card
  and Sanborn transcriptions are what make the frontage signal strong.
- **The record-depth control.** It adds the number of decades a building is on record for any use.
  The signal survives it, so this is not only "older buildings have more paperwork".
- **Random seed.** p moves between 0.021 and 0.023 across seeds.

## How it was done

1. **The question.** For each parcel and each of eight kinds of use (food and drink, retail goods,
   personal services, automotive, entertainment and assembly, institutional and religious,
   office, light industry), is that use there today (yes or no)?
2. **The base model.** One intercept per kind of use. This is "guess the common uses".
3. **The history model.** The base model plus beta x log(1 + decades on record before the cut-off).
4. **The primary test.** Shuffle whole parcel histories among parcels on the same block side,
   10,000 times, and count how often the shuffled histories line up with today's uses as well as
   the real ones. Keeping block sides fixed controls for location.
5. **Where the data come from:**
   - **Other blocks, use today:** coded from the sponsor's October 2026 storefront summaries, without
     looking at history (`outcomes_other_greenmount_2026-10.csv`; coded with AI assistance; a team
     member should check it).
   - **Other blocks, history:** the sponsor's curated records that state a use (the week-1 class A
     rule), coded with the extractor's rules.
   - **Frontage, use today:** the team's October tenant check.

## What this does not show

- **It does not prove that history causes the use.** The same buildings suit the same uses
  (shopfronts, garages), so history is partly a stand-in for building form.
- **It is one corridor.** The parcels are small in number.
- **The uses today are the sponsor's and the team's own checks,** and both have known errors.
- **The spring validation repeats the test** on the four blind reference timelines.

## Run it

```bash
python3 team/validation/backtest.py              # about 10 seconds; writes out/backtest_v2.json
python3 -m unittest team/validation/test_backtest.py
```
