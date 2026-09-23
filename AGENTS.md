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

`bin/check` runs `python3 verify_claims.py`, `python3 map/app.py --check`, a jupytext sync, and
executes the notebook top to bottom. `verify_claims.py` and `map/app.py` are standard library only.

## Data rules (these are the mistakes that produce wrong answers)

- **Layer split.** In `property_incidents.csv`, a `source` is *administrative* if it starts with
  `baltimore:` or equals `sdat_assessments` or `sdat:owner`. Everything else is *curated*.
  That gives 16,706 administrative rows and 3,602 curated. Historical analysis uses the curated layer.
- **Two geographies.** `properties.csv` holds 1,456 Greenmount corridor properties (`zip_code`
  21218) and 418 Baltimore Peninsula parcels (21230). Filter to 21218 for corridor statistics.
- **Empty and zero-filled columns.** `avm_estimate`, `walk_score`, `transit_score`, `bike_score`,
  `building_condition`, `building_quality`, `num_stories`, `irs_*` are blank. `sale_count`,
  `nearby_restaurants`, `nearby_shops`, `nearby_amenities_total`, `public_investment_total` are
  0 in every row: placeholders, not measurements. `neighborhoods.bounds` is empty.
  `DATA_DICTIONARY.md` marks every such column.
- **Sale prices.** 419 `last_sale_price` values are $0. Portfolio sales repeat the whole deal
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
- **If you change a number in `README.md`, update `verify_claims.py` to check it.** If the
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
