# Comps engine v2: model card (working draft, 21 November 2026)

What ground-floor space on the Greenmount frontage rents for, from listed rents, and a check of which kinds of
business could cover that rent from typical sales (Idea 1). Standard library only: `python3 team/comps/comps_engine.py`
writes `comps_ranges.json`, which the explorer reads. Every number below is filled in from `team/NUMBERS.md`;
`comps_ranges.json` is always the current source.

## What changed from v1, and why

The sponsor's review of 17 November 2026 found that v1's ranking of uses by money was an artifact. v1 gave each use
the lower of two figures, its asking rent and the rent its sales could afford, as if they were independent draws.
That cut the figure of every use that had both kinds of evidence and left uses with one kind uncut, so a bike shop,
with one national sales figure and no listings, came out as the highest-rent use on every parcel. v2 removes that
figure and everything built on it.

| v1 | v2 |
|---|---|
| "Supportable rent" = min(asking rent, affordable rent) | Removed. One basis for every dollar figure: listed rents |
| "Chance it can pay" | Removed. A sales check with three answers: covers, does not cover, too close to call |
| Sales "percentiles" | Labelled low, mid and high scenarios, each with its source |
| Uses and plans ranked by rent | Nothing is ranked by money |
| Rent on whole-building floor area | Rent on the estimated ground floor (done in the explorer), low case first |
| Two Greenmount rents in place held but not read | Read as rows R-080 and R-081 |
| A Harford Road row counted as Waverly | Fixed (rule order in `engine_inputs.json`) |
| A switched-off step for private sales data | Removed, with every mention |

## What it is for, and what it is not

- **For:** a planning range for the rent of a ground-floor space on this corridor, and a flag for whether a kind of
  business could cover the listed rent for its use. Every number links to a library row or a named assumption.
- **Not for:** valuing buildings, comparing buildings or blocks by money, ranking uses or plans by money, picking
  buildings to buy, or promising income (the sponsor's proposal: "No appraisals").
- **Not yet for:** vehicle repair and upper-floor housing.

## Data

| Input | Rows | What |
|---|---|---|
| `library/rents.csv` | <!--=comps.library_rent_rows-->81<!--/--> (<!--=comps.rents_used-->60<!--/--> used) | Listed rents in <!--=comps.corridors-->17<!--/--> corridors: <!--=comps.asking-->57<!--/--> asking rents and <!--=comps.in_place-->3<!--/--> rents in place (<!--=comps.in_place_rows|list-->R-004, R-080, R-081<!--/-->). None is a newly signed lease. <!--=comps.waverly.rows-->6<!--/--> are in Waverly (<!--=comps.waverly.asking-->3<!--/--> asking, <!--=comps.waverly.in_place-->3<!--/--> in place). Dropped: housing, spaces under 300 sq ft, workshops over 6,000 sq ft, rows with no rate |
| `library/benchmarks.csv` | <!--=comps.benchmarks-->192<!--/--> | Sales per sq ft, rent as a share of sales, Census receipts per business |
| `library/operators.csv` | <!--=comps.operators-->45<!--/--> | Revenue from public filings; used as spot checks only |
| `parcel_tax.csv` | | City tax and building area per Greenmount parcel (Baltimore Real Property layer) |
| `engine_inputs.json` | | Every assumption, with its source or "team judgement" |

No row has been checked against its source by a person: `verified_by` is filled on
<!--=comps.library_rows_checked_by_a_person-->0<!--/--> of <!--=comps.library_rows-->318<!--/--> rows.

## How it works, and why each method

| Step | Method | Why this one | Rejected, and why |
|---|---|---|---|
| Lease terms | A listed rent that includes some or all building costs is reduced by $2 or $4 per sq ft, so every rent is before taxes and insurance | Makes listings comparable | A full adjustment grid: no paired listings to calibrate it |
| Rent level | Log rents pooled by corridor toward the city mean (empirical Bayes, closed form) | <!--=comps.rents_used-->60<!--/--> rows in <!--=comps.corridors-->17<!--/--> corridors is a thin-cell problem. Each corridor's weight on its own rows follows from how many it has, and every estimate is a visible weighted sum of listings | Regression on many attributes: too many parameters for the rows. Pooling by three tiers: the spread between tiers comes out as zero |
| Use multipliers | Each use's gap from its city mean, shrunk toward 1 by its number of listings. A multi-tenant average has no multiplier | One or two listings should not set a use's rent | Raw averages |
| Range | An 80% range, widened until it holds 80% of listings held out by source | The plain range held too few unseen listings | Splitting the sample in two: wastes half the rows |
| Rent for a space | The corridor level times the estimated ground floor, the same whatever the use (computed in the explorer) | The owner of an empty storefront is letting a space, not a use | A rent per use ranked against other uses (v1) |
| Sales check | Sales per sq ft in a low, mid and high scenario, times the usual share of sales spent on rent, minus the parcel's taxes and insurance. If the mid result is within <!--=comps.sales_check_margin|pct-->10%<!--/--> of the mid listed rent for the use, the answer is "too close to call" | Says something about viability without pretending to a probability | "Chance it can pay": no empirical basis |

## Results

- **Waverly's corridor.** <!--=comps.waverly.rows-->6<!--/--> rows average $<!--=comps.waverly.mean_of_own_rows|f2-->15.71<!--/--> per sq ft a year;
  pooled, $<!--=comps.waverly.pooled|f2-->16.22<!--/-->. The local rows carry <!--=comps.model.waverly_weight_on_its_own_rows|pct-->75%<!--/--> of the
  weight and the Baltimore mean ($<!--=comps.model.baltimore_mean|f2-->17.88<!--/-->) the rest. The range is
  $<!--=comps.waverly.rent_level_low_mid_high.0|f2-->9.33<!--/--> low, $<!--=comps.waverly.rent_level_low_mid_high.1|f2-->16.22<!--/--> in the middle and
  $<!--=comps.waverly.rent_level_low_mid_high.2|f2-->28.22<!--/--> high, before taxes and insurance.
- **Held out by source** (<!--=comps.held_out_detail.sources-->50<!--/--> sources, <!--=comps.held_out.rows-->59<!--/--> rows): the plain 80% range
  held <!--=comps.held_out.inside_plain_80_range-->41<!--/--> (<!--=comps.held_out_detail.share_plain|pct-->69%<!--/-->), with
  <!--=comps.held_out_detail.below-->8<!--/--> below and <!--=comps.held_out_detail.above-->10<!--/--> above, so it is widened
  ×<!--=comps.held_out.widened_by|f2-->1.26<!--/-->. Recomputing the widening without each held-out row, the widened range holds
  <!--=comps.held_out.inside_widened_range-->48<!--/--> (<!--=comps.held_out_detail.share_widened|pct-->81%<!--/-->). Baltimore rows only:
  <!--=comps.held_out_detail.baltimore_plain-->29<!--/--> of <!--=comps.held_out_detail.baltimore_rows-->40<!--/--> plain,
  <!--=comps.held_out_detail.baltimore_widened-->34<!--/--> widened.
- **Against a plain range of all listings**, the score that rewards narrow ranges and penalises misses is
  <!--=comps.held_out_detail.better_than_a_plain_range_of_all_listings|pct-->23%<!--/--> better.
- **A second method** that assumes no distribution gives $<!--=comps.held_out_detail.second_method_waverly_shop.0|f2-->9.85<!--/--> to
  $<!--=comps.held_out_detail.second_method_waverly_shop.1|f2-->31.21<!--/--> for a Waverly shop, close to the model's range.
- **Sales check:** cafe <!--=comps.sales_check.cafe-->too close to call<!--/-->; counter <!--=comps.sales_check.counter-->too close to call<!--/-->; tavern
  <!--=comps.sales_check.tavern-->too close to call<!--/-->; shop <!--=comps.sales_check.shop-->covers<!--/-->; showroom <!--=comps.sales_check.showroom-->does not cover<!--/-->; bike shop
  <!--=comps.sales_check.bike-->covers<!--/-->; services <!--=comps.sales_check.services-->covers<!--/-->; fitness <!--=comps.sales_check.fitness-->covers<!--/-->. Uses
  with no sales figure (offices, studios, community space) have no check.
- The page's JavaScript reproduces the Python figures to within half a percent on every worked example; a browser test
  fails if it does not.

## What moves the Waverly figure

| If | Waverly rent level, per sq ft a year |
|---|---|
| As built | $<!--=comps.waverly.pooled|f2-->16.22<!--/--> |
| Asking rents only (the three rents in place left out) | $<!--=comps.waverly_level_if.asking_rents_only|f2-->14.38<!--/--> |
| R-004 read with the tax record's floor area | $<!--=comps.waverly_level_if.r004_read_with_the_tax_record_floor_area|f2-->15.35<!--/--> |
| R-004 left out | $<!--=comps.waverly_level_if.r004_left_out|f2-->14.78<!--/--> |

R-004 (3217 Greenmount) is a rent in place from a for-sale listing. The listing's floor area and the tax record's
disagree, and the review asked for a person to re-read it. Until then the table above shows what rests on it.

## Limits

- Listings are asking rents, not signed leases. The three rents in place come from for-sale listings and are not
  dated to a lease.
- Waverly has <!--=comps.waverly.rows-->6<!--/--> rows. None is a small shop, and several Greenmount listings say "contact for
  pricing". Real rents by phone are planned for spring.
- The share of sales spent on rent is a national median or vendor guidance. Sales benchmarks come from other years
  and places, and some uses have one sales figure only; the page says so beside the check.
- The sales check compares two middle figures. It does not use the ranges, and a different rent share can change the
  answer (the page's sensitivity table shows which).
- With <!--=comps.held_out.rows-->59<!--/--> held-out rows the coverage check can catch a badly wrong range, not a slightly wrong
  one.
- Other cities' listings enter Waverly's range only through the pooled model. For side-by-side comparison the corridor
  table restates each corridor at Baltimore's price level (BEA all-items regional price parity, 2024).

## Checks to rerun after any change

1. `python3 team/comps/comps_engine.py`, then `python3 -m unittest team/comps/test_comps_engine.py`. The tests cover
   sources, the pooling arithmetic, the corridor of every Waverly row, the rents in place being read, one basis for
   every figure, nothing ranked by money, the sales check being a flag, guardrail words and determinism.
2. `python3 team/explorer/build_explorer.py`, then the rest of the rebuild in `team/explorer/README.md`.
3. Read the sensitivity table on the page.

## AI use

Built with Claude in October 2026 and reworked in November 2026, from the team's comps research and the sources
linked in the library. Before merge, a team member reruns the tests, spot-checks ten library rows against their
sources (filling `verified_by` and `verified_on`), re-reads R-004, R-080 and R-081, and signs below.

Checked by: ____________________ Date: __________
