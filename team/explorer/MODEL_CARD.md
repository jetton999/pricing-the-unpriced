# Model card: Greenmount frontage explorer

Release candidate, 26 October 2026. Covers the use score (v0.3), the block plan (v1), the comps at three levels,
the typical units and the displacement flags. The rent and revenue ranges have their own card: `team/comps/MODEL_CARD.md`.

## What it is for

- **What it does.** It helps the sponsor's team and the CUSP team talk about one question, with sources: what
  could each empty storefront on Greenmount Ave (E 29th to E 33rd St) become, given what it was?
- **What it shows.**
  - For each building: a short list of uses with reasons, the rent each use could support, and comparable
    projects elsewhere.
  - For the block: alternative plans for the same parcels, with saturation, neighbour and rent-pressure checks.
- **Who it is for.** Planning conversations, tenant recruiting and owner outreach. It is a pilot for the
  Property Dossier.

## What it must not be used for

- A valuation, appraisal or price for any building, or a promise of income.
- Choosing buildings to buy, or ranking buildings or blocks by money. Plans compare uses for the same parcels.
- Pressuring or replacing a business that trades today. Occupied buildings are never planned. Their panel reads
  "if this space ever came free".
- Deciding anyone's eligibility for a programme or a loan.
- Any public use before the sponsor has agreed the weights, the money rule and which names may appear.

## How it works

1. **Rules first.** C-1 zoning (Baltimore code Table 10-301) and the urban renewal plan remove uses that are not
   allowed, and mark conditional ones.
2. **Score.** Each allowed use gets a score from six inputs:
   - **Heritage:** the decades the use is on record at the building.
   - **Room on the block:** saturation on the block side and on the corridor against its 1920-23 mix.
   - **Size fit.**
   - **Community:** what residents asked for or objected to.
   - **Neighbours:** a matrix grounded in law and research.
   - **Precedents:** how the most similar reuse cases turned out.

   The weights are shares of one score and always add to 100%; they are team judgement, and four presets show how
   much the ranking depends on them. A label says how firm each verdict is: the share of 1,000 priority mixes in
   which it comes first.
3. **Block plan.** Uses are placed one at a time under a cap of three of a kind per block side. A search then
   ranks whole plans by the rent the uses could support (typical, cautious or bad year), and checks itself
   against an exhaustive search.
4. **Comps at three levels.** 32 reuse buildings and 22 corridors, each with sources. Buildings are matched on
   type, history, size, age and income context; streets on income, race, anchor, ownership, history, length and
   country. Project costs are total cost divided by floor area, adjusted to 2025 dollars with CPI-U. They are
   not adjusted for local building costs. Eight benchmark neighbourhoods (the sponsor's set) are compared on
   public asking rents, made triple-net equivalent with the comps engine's allowances, on vacancy with its
   definition, and on residents; the comparison sentences are written from the rows at build time.
5. **Typical units.** The typical floor area of 20 uses (sourced) turns a rent per sq ft into a total rent a
   year. The size fit in the score still uses the team's wider ranges, pending the sponsor.
6. **Displacement flags.**
   - **Long-standing businesses:** where a dated record or a check documents them (5 so far).
   - **Rent pressure:** businesses already trading on a block side whose kind of business typically supports
     at least 20% less rent than a plan's new uses there.
   - **Corridors:** each comparison corridor is rated high, moderate, low or unknown under a written rubric
     (`library.json`, `meta.displacement_rubric`).

## How it was checked

| Check | Result | Where |
|---|---|---|
| Use timelines against four hand-built references | 96% of reference uses found where a source covers those years; 88% of 135 coded records agree on the category | `team/extractor` |
| Does history predict use today? Back-test v2, plan committed before the run | On 52 Greenmount parcels outside the frontage, records up to 1960: one-sided p = 0.023 (shuffle test within block sides); AUC 0.707 to 0.741; held-out log loss 0.6187 to 0.6145. Passes the written rule, which the sponsor has not yet signed off | `team/validation` |
| Rent ranges on listings the model had not seen | 46 of 57 inside the widened 80% range | `team/comps` |
| Plan search against exhaustive search | 100% of the best plan over each parcel's top five uses | Block plan page |
| Case library, desk research of 26 Oct 2026 | Every added value carries the URL of a page read that day; four claims re-checked by hand, all matched | `research/` |
| Neighbourhood benchmarks | Tests recompute every triple-net equivalent, check Waverly's vacancy against the sponsor's storefront assessments, and check that the comparison quotes the rows | `test_explorer_data.py` |
| No brand names in the public build | A test checks the public files and the built page against hashed names | `test_explorer_data.py` |

## Where it fails or is weak

- **Thin records.** About ten parcels have little on record (the silence map), so history says little about them.
- **Weights not agreed.** The weights are not the sponsor's yet. A close call (labelled on the page) can flip
  with them.
- **Uses that cannot be ranked by money.** A use with no sales benchmark and fewer than three listings (a food
  maker, a maker workshop) gets no money estimate, and plans that include it understate rent.
- **Rare buildings.** Theatres, churches and banks have few comparable projects with costs, so cost ranges are
  wide or missing.
- **Costs.** Project costs differ in scope (some include buying the building) and exclude this building's
  condition.
- **Case statuses age.** Each status is dated, and "operating" needs a 2025 or 2026 source.
- **Displacement ratings.** They rest on published sources. "Unknown" does not mean none.
- **Back-test limits.** It shows an association, not a cause: buildings suited to a use keep attracting it.
- **Neighbourhood comparisons.** Pigtown, U Street and Melrose Hill rest on one or two rent rows (Melrose Hill's is
  one property's projected rent). Vacancy is measured differently from place to place, residents come from
  different geographies, and dollars are nominal, not adjusted for local price levels. Read them as orders of
  magnitude.
- **Typical sizes.** Many come from chains' site criteria, which run larger than old rowhouse storefronts; the
  low end of each range is closer to Greenmount's units.
- **Data refreshes.** A refresh can retire parcel ids (52 in October 2026). Rebuild after each refresh.

## Data, people and rights

- **Data.** Sponsor data is CC BY 4.0. Sensitivity-flagged records are never dropped and never quoted.
- **No NDA data.** No NDA operator data is used. A private check against one operator's sales is built but switched
  off, and needs the sponsor's approval.
- **No private individuals.** The case library names organizations and businesses only.
- **No brand names.** Brand names go in reports only (the sponsor's rule, 26 Oct 2026); reference brands and the
  chains behind the typical sizes stay in the team report.

## Maintenance

Rebuild order: comps engine, then back-test, then explorer (see `README.md`), then run the three test files. When
the case library is updated, keep the URL and access date for every value. Re-rate displacement only under the
written rubric, and keep any earlier rating as `displacement_v1`.
