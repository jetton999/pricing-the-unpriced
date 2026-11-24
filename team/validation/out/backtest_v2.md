# Back-test v2: results

Written by `team/validation/backtest.py` from `out/backtest_v2.json`. Do not edit by hand; rerun the script.

## The test

On 52 Greenmount parcels outside the frontage (416 pairs of a parcel and a kind of use, 57 of them true today), with records up to 1960: one-sided shuffle test **p = 0.055**. With records up to 1940: p = 0.024.

The rule agreed with the sponsor on 9 November 2026 needs p below 0.05 and a lower held-out log loss. The test **does not pass**. Before the leak found on 17 November 2026 was fixed, the same test gave p = 0.023.

If the rule fails: the money layer shows rent and revenue ranges from comparable listings only, labelled as planning figures, and nothing that ranks uses or plans by history and money together (PLAN_backtest_v2.md).

## Which kinds of use carry the result (records up to 1960)

| Kind of use | Parcels that have it today | Base rate | Parcels with it on record before 1960 | Of those, have it today | Expected from the base rate | Adds to the test statistic |
|---|---|---|---|---|---|---|
| food & drink | 16 | 31% | 16 | 4 | 4.9 | -0.50 |
| retail goods | 8 | 15% | 3 | 0 | 0.5 | -0.32 |
| personal services | 4 | 8% | 10 | 1 | 0.8 | +0.47 |
| automotive | 9 | 17% | 4 | 4 | 0.7 | +2.87 |
| entertainment & assembly | 0 | 0% | 9 | 0 | 0.0 | +0.00 |
| institutional & religious | 9 | 17% | 2 | 0 | 0.3 | -0.24 |
| office | 9 | 17% | 1 | 0 | 0.2 | -0.12 |
| production & light industry | 2 | 4% | 4 | 1 | 0.1 | +0.59 |

| Counting only | p, shuffle test |
|---|---|
| all eight kinds of use | 0.055 |
| ordinary storefront trades only (food and drink, retail goods, personal services) | 0.455 |
| every kind except automotive | 0.484 |
| automotive only | 0.004 |

## How much hangs on single parcels (records up to 1960)

Leaving each of the 52 parcels out in turn, p runs from 0.028 to 0.148 (median 0.055); 12 of the 52 runs are below 0.05.

| Leaving out | p |
|---|---|
| 2601 Greenmount | 0.028 |
| 2733 Greenmount | 0.035 |
| 3300 Greenmount | 0.036 |
| 3419 Greenmount | 0.096 |
| 2739 Greenmount | 0.123 |
| 3427 Greenmount | 0.148 |

Multi-tenant centres (3 or more kinds of use today): 2801 Greenmount (4 kinds). Without them: p = 0.087 on 51 parcels.

## All runs

| Data | Cut-off | Parcels (with history) | p, shuffle test | Fit on the same data (AUC), without and with history | p with a control for how much is on record |
|---|---|---|---|---|---|
| Other Greenmount blocks: the test | 1960 | 52 (32) | 0.055 | 0.707 to 0.724 | 0.114 |
| Other Greenmount blocks: the test | 1940 | 52 (31) | 0.024 | 0.707 to 0.731 | 0.039 |
| Other blocks, low-confidence codes of today's use left out | 1960 | 47 (30) | 0.084 | 0.729 to 0.756 | 0.201 |
| Other blocks, low-confidence codes of today's use left out | 1940 | 47 (29) | 0.038 | 0.729 to 0.763 | 0.077 |
| Other blocks, history coded from linked businesses and directory lines only | 1960 | 52 (17) | 0.086 | 0.707 to 0.727 | 0.061 |
| Other blocks, history coded from linked businesses and directory lines only | 1940 | 52 (16) | 0.036 | 0.707 to 0.725 | 0.032 |
| Other blocks, multi-tenant centres left out | 1960 | 51 (31) | 0.087 | 0.715 to 0.731 | 0.197 |
| Other blocks, multi-tenant centres left out | 1940 | 51 (30) | 0.051 | 0.715 to 0.735 | 0.108 |
| Other blocks before the leak fix (as first reported; not valid) | 1960 | 52 (34) | 0.023 | 0.707 to 0.741 | 0.013 |
| Other blocks before the leak fix (as first reported; not valid) | 1940 | 52 (33) | 0.007 | 0.707 to 0.743 | 0.003 |
| This frontage, all sources (exploratory: the model was chosen here) | 1960 | 38 (37) | 0.013 | 0.847 to 0.870 | 0.005 |
| This frontage, all sources (exploratory: the model was chosen here) | 1940 | 38 (37) | 0.028 | 0.847 to 0.861 | 0.011 |
| This frontage, sponsor records only | 1960 | 38 (33) | 0.218 | 0.847 to 0.850 | 0.198 |
| This frontage, sponsor records only | 1940 | 38 (33) | 0.146 | 0.847 to 0.850 | 0.133 |

## Held-out checks

| Check | Cut-off | Forecast error (log loss), without and with history | Ranking (AUC), without and with history | Gain per row, with a 95% interval |
|---|---|---|---|---|
| Fitted on this frontage (sponsor records), applied to the other blocks: the rule's second condition | 1960 | 0.6070 to 0.6050 | 0.631 to 0.632 | +0.0020 (-0.0043 to +0.0088): not distinguishable from zero |
| Fitted on this frontage (sponsor records), applied to the other blocks: the rule's second condition | 1940 | 0.6070 to 0.6035 | 0.631 to 0.636 | +0.0035 (-0.0048 to +0.0124): not distinguishable from zero |
| Fitted on this frontage (all sources), applied to the other blocks | 1960 | 0.6070 to 0.6040 | 0.631 to 0.631 | +0.0030 (-0.0119 to +0.0181): not distinguishable from zero |
| Fitted on this frontage (all sources), applied to the other blocks | 1940 | 0.6070 to 0.5993 | 0.631 to 0.649 | +0.0077 (-0.0048 to +0.0205): not distinguishable from zero |
| This frontage, one block side left out at a time | 1960 | 0.3060 to 0.3037 | 0.780 to 0.826 | |
| This frontage, one block side left out at a time | 1940 | 0.3060 to 0.3029 | 0.780 to 0.814 | |

## Who the test covers

The test can only use storefronts with a business today. On this frontage that is 38 storefronts; the plan is for the 24 empty ones. Before 1960 the empty storefronts have 6.75 use-decades on record on average and the ones in use 6.79 (two-sided shuffle p = 0.986); the mix of uses on record differs by 0.44 on a scale from 0 (the same) to 2 (p = 0.177). The test says nothing direct about the empty storefronts.
