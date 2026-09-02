# Piece 1 — Scaffold, Loaders, Data-Readiness Audit, Frozen Protocol

**Date:** 2026-09-01
**Parent:** `2026-09-01-provenance-engine-roadmap-design.md`
**Status:** Approved design

## 1. Goal

Stand up the package and its stage contract, load every sponsor table with a typed loader,
write the protocol that fixes every judgment call the index will depend on, and produce the
data-readiness audit that the proposal schedules for fall weeks 1–3. At the end of this piece:
`prov audit` runs on the real data and on the fixture, `docs/data_readiness.md` exists,
`protocol/v1.yaml` is committed with its hash recorded, and no outcome data has been used for
anything except counting coverage.

## 2. Deliverables

1. `pyproject.toml` with `uv` lockfile; dependencies for this piece: `pandas`, `pyarrow`,
   `pyyaml`, `typer`. Dev: `pytest`.
2. `src/provenance/io.py`, `protocol.py`, `audit.py`, `cli.py`.
3. `protocol/v1.yaml`.
4. `tests/fixtures/` synthetic corpus + generator, and tests for io, protocol, audit.
5. `docs/data_readiness.md` (generated, committed) and `data/derived/audit.json` (generated,
   gitignored).
6. `.gitignore` additions: `data/derived/`, `.venv/` (already), `*.egg-info`.

## 3. `io.py` — loaders

One function per table, all returning pandas DataFrames with explicit dtypes:

| Function | Notes |
|---|---|
| `load_properties(outcome_blind: bool)` | When `outcome_blind=True` the columns `last_sale_price`, `last_sale_date`, `assessed_value`, `avm_estimate`, `sale_count`, `market_median_sale_price`, `hpi_value`, `hpi_yoy_change`, `hmda_median_value` are dropped before return. `lot_polygon` and `building_polygons` are parsed from JSON strings. |
| `load_incidents()` | `occurred_at`, `occurred_at_end`, `created_at` parsed to datetimes (coerce); `data` parsed from JSON. |
| `load_subjects()`, `load_incident_subjects()`, `load_incident_links()`, `load_registered_ips()`, `load_parcels()`, `load_programs()`, `load_neighborhoods()`, `load_baselines()` | Straight loads with datetime parsing and JSON parsing where the dictionary says `jsonb`. |

All loaders take `data_dir: Path` (default: repo root) so tests point them at the fixture.
Each loader validates required columns against a per-table list and raises
`SchemaError(table, missing_columns)` on drift.

## 4. `protocol.py`

- `load_protocol(path) -> Protocol`: parses YAML into a frozen dataclass, validates types and
  ranges, and computes `protocol.hash` = SHA-256 of the canonical (sorted-key) JSON dump.
- `Protocol.layer_of(source) -> "administrative" | "curated"`.
- `Protocol.evidence_weight(status) -> float` (None → `ungraded`).
- `Protocol.relationship_weight(rel) -> float` (unlisted → `default`).
- `Protocol.salience(category) -> float`; unknown category → `ProtocolError`.
- `Protocol.knowable_from(source, occurred_at, data) -> date`; unknown source → `ProtocolError`.
  Rules: `at_occurrence` returns `occurred_at`; `at_publication` returns the `publication_date`
  found in the claim's `data` JSON under the configured key if present, else the source's
  `fallback_date`; `fixed` returns the configured date.
- `Protocol.is_arms_length(price, owner_type) -> bool`.

## 5. `protocol/v1.yaml` — the frozen values

```yaml
version: 1
description: Pre-specified coding protocol for the Provenance Index. Frozen before any
  outcome data is examined. Changes require a new version and re-scoring.

layers:
  administrative_prefixes: ["baltimore:"]
  administrative_exact: [sdat_assessments, "sdat:owner"]
  # Everything else is curated. Matches the sponsor's definition so that counts reconcile
  # with README.md (3,602 curated / 16,706 administrative).

evidence_weights:
  verified: 1.0
  probable: 0.7
  possible: 0.4
  contested: 0.15
  ungraded: 0.5

index:
  beta: 0.5          # weight of Connectivity relative to Density
  gamma: 1.0         # exponent on Salience
  sensitivity_grid:  # pre-specified; evaluated, never selected on
    beta: [0.25, 0.5, 1.0]
    gamma: [0.5, 1.0, 2.0]

relationship_weights:
  default: 0.5
  groups:
    tenure: 1.0        # the subject owned, occupied, ran, or built the place
    participation: 0.7 # the subject did something dated at the place
    mention: 0.4       # the subject is merely associated in a record
  members:
    tenure: [owned, purchased, sold, lived_at, operated_at, occupied, leased, built, founded,
      resided_at, worked_at, business_at, headquartered_at, mortgaged, current_owner,
      prior_owner, owner, resident, occupant, operator, founder, ran_business_at,
      employed_at, proprietor_of, located_at, officed_at, maintained_office_at,
      acquired_leasehold, received_leasehold, granted_leasehold, moved_into, based_at]
    participation: [played_at, performed_at, hosted, competed_at, played_for, led, designed,
      died_at, born_at, married, interred_at, attended, member_of, trustee_of,
      party_to_suit, brokered, lent_to, borrowed_from, lender, foreclosed_on, victim_of,
      perpetrator_of, applied_for, authored, created_artwork, painted, photographed,
      party_to_deed, party_to_conveyance, grantor_grantee, refinanced, demolished_for,
      commissioned_construction, contracted_to_construct, funded_renovation]
    mention: [mentioned_in, depicted_in, advertised_in, listed_in, subject_of, related_to,
      reported_by, recalled_in_comment, located_near, across_street, formerly_located_at,
      family, possible_relative_of_owner, visible_at, identified_at, depicted_on]

salience:              # per incident category, applied to curated claims only
  designation: 1.0
  institution: 0.7
  civic: 0.7
  news: 0.8
  obituary: 0.6
  photo: 0.6
  commerce: 0.6
  advertisement: 0.5
  construction: 0.5
  demolition: 0.5
  commercial: 0.5
  map: 0.4
  interment: 0.4
  death: 0.4
  directory: 0.3
  sale: 0.3
  ownership: 0.3
  land: 0.3
  liquor_license: 0.3
  # administrative categories, listed so the map is exhaustive; never scored
  complaint: 0.0
  permit: 0.0
  crime: 0.0
  tax_certificate: 0.0
  violation: 0.0
  foreclosure: 0.0
  receivership: 0.0
  vacant_notice: 0.0
  public_investment: 0.0
  open_bid: 0.0

knowability:           # when a claim became knowable to the market
  publication_date_key: publication_date   # looked up in the claim's data JSON
  sources:
    at_occurrence: [newspapers_com, chronicling_america, nytimes, mdlandrec, sanborn, polk,
      hopkins_atlas_1876, census_directory, stjohns_interments, blum_1910,
      fhlbb_waverly_1940, baltimore_plat, ephemera, federal_records, msa_ce168, msa_guide,
      sdat_charter, sdat_business_entity, findagrave, public_record, web_press,
      "baltimore:311", "baltimore:permits", "baltimore:crime", "baltimore:tax_certificates",
      "baltimore:code_violations", "baltimore:foreclosures", "baltimore:receivership",
      "baltimore:vacant_notices", "baltimore:demolitions", "baltimore:liquor_licenses",
      "baltimore:public_spending", "baltimore:open_bid", sdat_assessments, "sdat:owner",
      "hud:cdbg", bca_dhcd, bca_dpw]
    at_publication:
      whitepaper:       {fallback_date: 2026-01-01}
      web_research:     {fallback_date: 2026-01-01}
      research_note:    {fallback_date: 2026-01-01}
      field_report:     {fallback_date: 2026-01-01}
      internal:         {fallback_date: 2026-01-01}
      the_yard:         {fallback_date: 2026-01-01}
      stjohns_history:  {fallback_date: 2026-01-01}
      jmm_collections:  {fallback_date: 2026-01-01}
      bmi_collections:  {fallback_date: 2026-01-01}
    fixed:
      nrhp: 2013-12-31   # Waverly Main Street HD listing date

coverage:
  # archival_silence is true when a property has zero curated claims. silence_type is
  # "unsearched" when the property's block side has fewer than block_min_sources distinct
  # curated sources, else "searched".
  block_min_sources: 3

outcome:
  primary: last_sale_price       # modelled as ln(price)
  secondary: assessed_value      # administrative; never displayed as market value
  arms_length:
    min_price: 10000
    exclude_owner_types: [city]
  temporal_holdout_start: 2024-01-01

validation:
  min_panel_rows: 300
  min_transaction_coverage: 0.50   # share of properties with an arm's-length sale
  spatial_block_key: block_side_id
  spatial_folds: 5
  bootstrap_draws: 1000
  monetary_display_requires:
    r2_gain_min: 0.02
    r2_gain_ci_lower_gt: 0.0
    mae_reduction_min: 0.03
    connectivity_beyond_proximity: true   # C must also clear r2_gain_ci_lower_gt with a spatial lag present
```

Every source and category present in the export on 2026-09-01 appears above. A new value
in a future export makes `prov audit` fail until the protocol is revised and re-versioned.

## 6. `audit.py` — the data-readiness audit

`prov audit [--data-dir] [--protocol] [--out data/derived] [--report docs/data_readiness.md]`

Computes and writes `audit.json` and renders the markdown report with these sections:

1. **Row counts** per table, compared to `row_counts.txt`; mismatch is reported, not fatal.
2. **Layer split**: rows per source with layer label; curated vs administrative totals.
3. **Evidence grading**: `evidence_status` and `date_precision` distributions, split by layer;
   share of curated claims graded.
4. **Knowability**: for each source, the rule applied and, for `at_publication` sources, how
   many claims had an explicit publication date vs the fallback.
5. **Outcome coverage** (the only place outcome columns are read in this piece): properties
   with a sale date; with price > 0; passing the arm's-length filter; sale-year histogram;
   properties with `assessed_value`; count with sale before `temporal_holdout_start`.
6. **Covariate missingness**: non-null share for `year_built`, `structure_sqft`,
   `lot_polygon`, `dwelling_units`, `zoning_code`, `latitude`, `longitude`, `census_tract`,
   `market_typology`, `vacancy_indicator`, `block_side_id`.
7. **Linkage readiness**: share of `property_parcels.matched_property_id` populated; share
   of properties whose normalized address matches a parcel `normalized_address` exactly
   (a helper `normalize_address()` lives in `io.py` and is reused by stage 2).
8. **Documentation depth**: properties with ≥1 / ≥10 / ≥25 curated claims; distribution of
   distinct curated sources per property; count of properties in archival silence, split by
   `silence_type`.
9. **Sensitivity and rights**: counts by flag.
10. **Thresholds**: pass/fail for `min_panel_rows` and `min_transaction_coverage`, computed
    from §5; and a vocabulary check confirming every source and category is in the protocol.
11. **Protocol**: version and hash.

`audit.json` holds the same numbers as nested dicts; the markdown is rendered from it.

## 7. `cli.py`

Typer app named `prov`. This piece registers `audit` and `protocol-hash`. Later pieces add
their stages. `prov all` is registered now and runs whatever stages exist in order.

## 8. Fixture corpus

`tests/fixtures/make_fixture.py` writes nine CSVs (same columns as the real export, values
synthetic) into `tests/fixtures/data/`, checked in. Twenty properties on two block sides,
covering: an administrative-only property; a deeply documented one with claims across
five curated sources; an ungraded curated claim; a contested claim; a sensitivity-flagged
claim; two subjects that are near-duplicate spellings; a $1 sale; a city-owned sale; a sale
in 2019 and one in 2025; a white-paper claim with `occurred_at` 1920 attached to a
property sold in 2019 (the leakage case); one property with no parcel match.

## 9. Tests

- `test_io.py`: every loader returns expected dtypes on the fixture; blind loader has none
  of the outcome columns; `SchemaError` on a CSV missing a column.
- `test_protocol.py`: hash is stable across key order and whitespace; every fixture source
  and category resolves; unknown source raises; `knowable_from` returns occurrence date for
  a newspaper claim, fallback for a white paper without a publication date, and the JSON
  date when present; arm's-length filter rejects $1 and city sales.
- `test_audit.py`: `prov audit` on the fixture writes both outputs; thresholds section
  reports fail on the 20-row fixture (below `min_panel_rows`), which is the expected result
  and proves the check fires; row-count comparison tolerates a missing `row_counts.txt`.
- `test_real_data.py` (skipped unless the real CSVs are present): the audit's curated count
  equals 3,602 and the protocol vocabulary check passes.

## 10. Out of scope for this piece

Entity resolution, the graph, any score, any model. Lot-area computation from polygons
(piece 3). Notebooks. The audit reads outcome columns only to count coverage and never
joins them to claims.
