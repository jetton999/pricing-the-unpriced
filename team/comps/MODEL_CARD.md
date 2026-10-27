# Comps engine v1: model card (draft for review)

What a ground-floor use could pay and earn on the Greenmount frontage (Idea 1). Standard library only:
`python3 team/comps/comps_engine.py` writes `comps_ranges.json`, which the explorer reads. Figures below are
from the 20 October 2026 build; `comps_ranges.json` is always the current source.

## What it is for, and what it is not

- **For:** ranking uses for one building, and ranking use plans for the same set of parcels, by the rent the
  uses could support. Every number links to a library row or a named assumption.
- **Not for:** valuing buildings, comparing buildings or blocks by money, picking buildings to buy, or
  promising income. These are planning ranges with stated assumptions (the sponsor's proposal: "No appraisals").
- **Not yet for:** uses with no sales benchmark and fewer than 3 listings (food maker, workshop), vehicle
  repair, and upper-floor housing.

## Data

| Input | Rows | What |
|---|---|---|
| `library/rents.csv` | 79 (58 used) | Asking rents: 5 in Waverly, 33 elsewhere in Baltimore, 20 in six other cities. Dropped: housing, spaces under 300 sq ft, workshops over 6,000 sq ft |
| `library/benchmarks.csv` | 192 | Sales per sq ft, rent as a share of sales, Census receipts per business |
| `library/operators.csv` | 45 | Revenue from SEC Form C and IRS Form 990 filings; used as spot checks |
| `parcel_tax.csv` | 60 | City tax and building area per Greenmount parcel (Baltimore Real Property layer) |
| `engine_inputs.json` | — | Every assumption, with its source or "team judgement" |

The NDA restaurant at 2731 Greenmount is not in any of these files and is never used in a public output.

## How it works, and why each method

| Step | Method | Why this one | Rejected, and why |
|---|---|---|---|
| Lease basis | Asking rent minus $2 (modified gross) or $4 (gross) | Makes listings comparable | A full adjustment grid: no paired listings to calibrate it |
| Rent level | Empirical Bayes pooling of log rents by corridor toward the city mean (DerSimonian-Laird; closed form) | 58 rows in 17 corridors is the classic thin-cell case. Each corridor's weight on its own rows follows from its sample size, and every estimate is a visible weighted sum of listings | Hedonic regression: about 28 parameters for 58 rows. Quantile regression and random forests: too few rows in the tails, hard to trace. Pooling by three tiers: the between-tier spread comes out as zero. Full Bayesian sampling: needs libraries |
| Use multipliers | Each use's gap from its city mean, shrunk toward 1 by its number of listings | One or two listings should not set a use's rent | Raw averages |
| Range width | Lognormal 80% range, widened by the 80th percentile of held-out standardised residuals (normalised conformal) | The plain range held 68% of unseen listings | Split conformal: wastes half the rows |
| Affordability | Sales per sq ft (two-piece lognormal through the benchmark P10, P50, P90; 2025 dollars) × the usual rent share − the parcel's taxes and $1 insurance | Independent of local listings, and the only route for bike shops | Census receipts per business as the median: chains included and no floor area |
| Combining | Mixture with weight n/(n+3) on listings | Forecast-combination research: simple weights rarely lose | One route only; a fixed 50/50 |
| Supportable rent | max(0, min(asking rent, affordable rent)) | A tenant who cannot pay does not stay | Ranking by asking rent |
| Revenue | Sales per sq ft × usable area (up to three units of the use) | Matches the size factor's split rule | — |

## Results (20 Oct 2026 build)

- Waverly corridor: 5 listings average $15.69 after format adjustment; pooled $16.31. The local rows carry
  72%, the Baltimore mean ($18.03) the rest. Spread within a corridor about ±38%; between corridors about ±26%.
- Held out by source (48 sources, 57 predictable rows): the nominal 80% range held 39 (68%; 95% interval
  55-80%), with 8 below and 10 above. Widened ×1.30. Recomputing the widening without each held-out row, the
  widened range holds 46 (81%; 68-90%). Baltimore rows only: 27 of 38 nominal, 32 of 38 widened.
- Interval score (width plus a penalty for misses) is 22% better than a plain P10-P90 of all listings.
- Jackknife+ for a Waverly shop, $9.29-$31.36, agrees with the model's $9.64-$30.65.
- The page's JavaScript reproduces the Python figures to within 0.1% on 198 worked examples.

## Other cities

Other cities' listings enter Waverly's range only through the pooled model. For side-by-side comparison, the
corridor table shows each corridor's pooled mean and the same at Baltimore's price level (BEA all-items
regional price parity, 2024). Predicting each of the 8 other-city corridors from Baltimore's mean, the factor
lowers the median error from 23.8% to 22.3%, so it is kept for comparisons. The housing parity is not used: it
would turn Penn Ave's $16.50 into $27.09. Operators' revenue per sq ft is moved by CPI and the price parity and
checked against the benchmark range: both cafes (Baltimore and DC) fall inside.

## The NDA operator (private step)

- The operator's data is a single draw from many businesses. It gets a weight of about 0.2: tau² / (tau² +
  sigma²), with tau the between-corridor spread and sigma the cafe sales spread.
- A calibrated figure can be inverted to recover the private one. So the step runs only when
  `PTU_PRIVATE_OPERATOR` points at a file outside the repo. It writes `private_annex.json` beside that file and
  never touches `comps_ranges.json`. `test_comps_engine.py` checks both.
- Keep the input and the annex in the team's CUSP RCF project space. Do not upload them to AI tools without
  instructor permission (Week 2 rule). Share even a yes/no ("inside the public range") only with the sponsor's
  approval.

## Limits

- Listings are asking rents, not signed leases. Only 3217 is a rent being paid, and it moves Waverly's shop
  median from $17.19 to $15.69.
- Waverly has five listings and none of them is a shop. Four Greenmount listings say "contact for pricing".
- Rent shares are national medians or vendor guidance. Benchmarks come from other years and places (Boulder,
  Ontario).
- Within one building, rent and sales are treated as independent.
- Plan scenarios share half of each building's uncertainty across the corridor. That share, the same-use
  haircut (15%) and the neighbour pull (4%) are team judgement.
- Coverage checks with 57 rows can catch a badly wrong range, not a slightly wrong one.

## Checks to rerun after any change

1. `python3 team/comps/comps_engine.py`, then `python3 -m unittest team/comps/test_comps_engine.py` (15 tests:
   sources, NDA absence, pooling arithmetic, own-listing exclusion, quantile order, private-step isolation,
   guardrail words, determinism).
2. `python3 team/explorer/build_explorer.py`, and open `index.html`.
3. Read the sensitivity table on the page: lease allowances, the 3217 lease, the combining weight, the
   borrowed spread and the rent shares.

## AI use

Built with Claude on 20 October 2026 from the team's comps research and the sources linked in the library.
Before merge, a team member reruns the tests, spot-checks ten library rows against their sources, and signs
below.

Checked by: ____________________ Date: __________
