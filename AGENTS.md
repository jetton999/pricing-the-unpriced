# AGENTS.md

Instructions for coding agents (Claude Code, Codex, Cursor, Copilot, Gemini CLI) working in this
repo. Humans: the same rules apply to you; `README.md` is the friendlier version.

## What this repo is

The sponsor data package for the NYU CUSP 2026–2027 capstone *Pricing the Unpriced*: a CSV
export of a Baltimore corridor knowledge base, a starter notebook, and a map app. Students pick
one or both of two project ideas (full text in `PROJECT_IDEAS.md`):

1. **Heritage-anchored highest and best use.** What should each building in an assemblage
   become, anchored on what it historically *was*, and does the mix work as a block?
2. **From tenant to owner.** A lease that starts a business as a tenant of the sponsor's real
   estate trust and ends with it owning the building.

## Setup and commands

```bash
uv sync                     # install everything into .venv
uv run pre-commit install   # strip notebook outputs and sync the .py/.ipynb pair on commit
bin/check                   # run ALL checks; run this before you say you are done
```

`bin/check` runs `python3 verify_claims.py`, `python3 map/app.py --check`, a read-only check that
`START_HERE.py` and `START_HERE.ipynb` match, and executes the notebook top to bottom. It needs
bash; it uses `uv run` if uv is installed, else the active environment. `verify_claims.py` and `map/app.py` are standard library only.

## Data rules (these are the mistakes that produce wrong answers)

- **Layer split.** In `property_incidents.csv`, a `source` is *administrative* if it starts with
  `baltimore:` or equals `sdat_assessments` or `sdat:owner`. Everything else is *curated*.
  That gives 7,017 administrative rows and 3,597 curated. Historical analysis uses the curated layer.
- **Study area.** The export covers only Greenmount Ave and about one block either side
  (673 properties). The cut rule is in README §4, "How the study area was cut".
- **Blank and single-value columns.** `avm_estimate`, `flood_zone`, `walk_score`,
  `transit_score`, `bike_score`, `building_condition`, `building_quality`, `num_stories`, `irs_*`
  are blank. Eighteen more hold one value in every row: the `0`/`False` placeholders
  (`sale_count`, `nearby_*`, `public_investment_total`, `has_basement`, `has_central_ac`, and six
  program flags) and area-wide figures (`zip_code`, `fair_market_rent_2br`, `market_median_*`,
  `market_inventory`). Never use them as features or read a 0 as "none". `neighborhoods.bounds`
  is empty. `DATA_DICTIONARY.md` marks every such column; notebook §0 lists them.
- **Sale prices.** 114 `last_sale_price` values are $0. Portfolio sales repeat the whole deal
  price on every parcel: drop rows whose price and date are shared with another parcel.
- **`assessed_value` is administrative**, not a market price. Never present it as one.
- **Never drop rows with a `sensitivity` flag** (52 incidents). See `LICENSE.md`.
- **`operated_at` links people and organizations too.** Filter `subjects.subject_type ==
  "business"` when you mean businesses.
- **Temporal leakage.** A record created in 2026 cannot inform a 2005 outcome.

## Editing rules

- **Edit `START_HERE.py`, never `START_HERE.ipynb` directly.** They are a jupytext pair; the
  `.py` is the source of truth. Run `uv run jupytext --sync START_HERE.py` after editing.
- **Never commit notebook outputs.** The pre-commit hook strips them.
- **If you change a number in `README.md` or another doc, update `verify_claims.py` to check it.** If the
  script disagrees with the README, the data wins and the README is what needs fixing.
- **Keep `map/app.py` and `verify_claims.py` standard-library only.** A student with a bare
  Python install must be able to run them.
- **Cite a source row for any historical claim** you write into a use history
  (`property_incidents.id` or the `source` + `source_id`).

## Where things are

| Need | Look in |
|---|---|
| Column meanings, fill rates, empty columns | `DATA_DICTIONARY.md` |
| Worked joins and starter tables | `START_HERE.py` |
| Idea 2 financing cases | `docs/worker-owned-exits.md` |
| Sensitivity and licensing rules | `LICENSE.md` |
| Map app internals | `map/README.md` |
