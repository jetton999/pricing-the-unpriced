# Back-test v2: analysis plan

Written 26 October 2026, before the test below was run on the other Greenmount blocks. The commit
that adds this file is the record of what was fixed in advance. Results go in `README.md` and
`out/backtest_v2.json`, not here.

## The question

Does a building's documented past add information about what it is used for today, beyond how
common each kind of use is on the street? This is the "held-out predictive power" the sponsor's
proposal asks for before any dollar figure built on history is shown.

## What was already seen, and what was not

- **Seen (exploratory).** The 69 frontage parcels, E 29th to E 33rd St. Back-test v1 (a hit-or-miss
  comparison) came out weak: 26 of 41 against 25 of 41 for a plain guess. The model below was then
  chosen on the same parcels and gave p of about 0.001. That result is exploratory and is not
  claimed as a test.
- **Not seen.** The other Greenmount Ave parcels in the study area (the 2300 to 2800 and 3300 to 3700
  blocks). Their 2026 uses had not been coded, and no model had been run on them, when this plan
  was written.

## Data

- **Parcels.** Greenmount Ave parcels outside the 69-parcel frontage (and outside the parcels merged
  into it) that have a 2026 status in the sponsor's `storefront_assessments.csv` of `open_active`,
  `institution` or `office_industrial`.
- **Use today (the outcome).** Coded from the sponsor's storefront summary for each parcel, into the
  extractor's eight non-housing categories: food & drink, retail goods, personal services,
  automotive, entertainment & assembly, institutional & religious, office, production & light
  industry. A parcel can have more than one. Coding uses the summary text only, not the parcel's
  history. It is written to `outcomes_other_greenmount_2026-10.csv` with a short reason per row,
  and it was done with AI assistance, so a team member checks it.
- **History (the predictor).** Curated records in `property_incidents.csv` that state a use (the
  week-1 class A rule: a linked business, a Polk or census-directory row, or a directory,
  advertisement, commerce, commercial, construction or institution record), dated up to the
  cut-off year, coded with the extractor's rules (`team/extractor/rules.py`). Generic "store"
  labels, housing and vacancy are left out. H(p, c) is the number of different decades in which use
  c is on record at parcel p.
- **Cut-offs.** 1960 (primary) and 1940 (secondary). Nothing after the cut-off is used.

## Model

One row per parcel and use category. Outcome: the parcel has that use today (1 or 0).

- Base model: one intercept per category (this is "guess the common uses").
- History model: the base model plus beta x log(1 + H).
- Both fitted by maximum likelihood (logistic regression).

## Tests

1. **Primary.** One-sided permutation test of beta > 0. Statistic: S = sum over rows of
   log(1 + H) x (y minus the category's share of y). Whole parcel histories are shuffled among
   parcels on the same block side (hundred block and side of the street), 10,000 times. This keeps
   location fixed and treats each parcel as one unit.
2. **Secondary.** Likelihood-ratio test; AUC with and without history; the same model with a
   control for how much is on record at the parcel (log of 1 + decades with any use).
3. **Transfer.** Coefficients fitted on the 69 frontage parcels, applied without refitting to the
   other blocks. Compared on held-out log loss against the base model fitted the same way.
4. **Frontage holdout.** Leave one frontage block side out at a time, fit on the rest, score the one
   left out. Reported for information.

## Decision rule (proposed to the sponsor)

History counts as adding held-out predictive power if, on the other Greenmount blocks at the 1960
cut-off, the primary test gives p < 0.05 **and** the history model has a lower held-out log loss
than the base model in the transfer test. If either fails, the money layer shows rent and revenue
ranges from comparable listings only, labelled as planning figures, and nothing that ranks uses or
plans by history and money together.

## Known limits, stated in advance

- The other blocks have thinner records than the frontage (no team transcription of directories,
  permit cards or Sanborn sheets there), so the test has less power and a null result is weak
  evidence of no effect.
- The uses today come from the sponsor's own storefront assessments, which can be wrong.
- Records cluster at older commercial buildings. The record-depth control checks whether the signal
  is just "more paperwork".
- The spring validation repeats this on the four blind reference timelines once they exist.
