# Provenance Engine — Roadmap Design

**Date:** 2026-09-01
**Status:** Approved design; implemented piece by piece (see "Sequencing")
**Scope:** The four committed pieces of the NYU CUSP 2026–27 capstone *Pricing the Unpriced*
(proposal deliverables 1–7, excluding conditional extensions).

## 1. Goal

Build, inside this repository, a reproducible pipeline that turns the sponsor's corridor
knowledge base into an auditable, pre-specified Provenance Index; validates that index against
sale prices on held-out data; decides whether a monetary interpretation may be displayed; and
serves the result through a JSON API and a minimal demo page that the sponsor can wire into
their existing Property Dossier interface.

Non-goals: National Register causal analysis, equity heterogeneity, improvement-scenario
model, production deployment, and any modification of the sponsor's live tools.

## 2. Constraints carried from the proposal

- **Score before dollars.** Index parameters (β, γ, all weights) are fixed in a
  version-controlled protocol before any outcome data is examined. Enforced mechanically
  (see §4.2), not by convention.
- **Archival abundance ≠ significance.** Every score carries a source-coverage measure and an
  explicit archival-silence flag. Sparse documentation is never scored as "no history".
- **No temporal leakage.** Each claim carries a *knowable-from* date. Validation uses only
  claims knowable as of the sale date.
- **Assessed value is administrative.** It may be analysed as a secondary outcome but is never
  presented as a market price.
- **Sensitivity and rights are honoured.** Flagged claims are summarized, not dropped and not
  displayed verbatim.

## 3. Data facts that shape the design

| Fact | Consequence |
|---|---|
| Outcome data is one `last_sale_*` pair per property (1,370 with price > 0; ~80% of sales are 2020+) | Validation is a cross-section with sale date as a control, not a repeat-sales panel. |
| 61 sales are under $10,000 (nominal transfers) | An arm's-length filter is part of the protocol. |
| Every curated incident has `occurred_at`; the only "documented when" field is DB `created_at` (all 2026) | Knowability must come from a per-source rule, not from timestamps. |
| `whitepaper` is the largest curated source (1,138 rows) and is written 2025–27 | Main leakage risk; the protocol dates it at publication, and a drop-white-papers robustness run is pre-specified. |
| 300+ distinct relationship types with a long tail | Relationship weights are assigned by group with an explicit default. |
| `num_stories` is entirely null; `structure_sqft`, `dwelling_units`, `year_built`, `lot_polygon` are ~95% populated | Covariate set excludes stories; lot area derives from `lot_polygon`. |
| 141 `block_side_id` values, 10 census tracts | Spatial blocking uses block side; tract is a control. |

## 4. Architecture

### 4.1 Layout

```
pyproject.toml            uv-managed; Python >= 3.12
src/provenance/
  io.py                   typed loaders for the nine CSVs (+ JSON column parsing)
  protocol.py             load/validate/hash protocol YAML
  audit.py                stage 1
  resolve.py              stage 2  (subjects, parcels)
  graph.py                stage 3
  index.py                stage 4
  panel.py                stage 5a
  validate.py             stage 5b
  api.py                  stage 6  (FastAPI)
  cli.py                  `prov` entry point
protocol/v1.yaml          the frozen coding protocol
data/derived/             parquet + JSON stage outputs (gitignored)
tests/                    pytest; tests/fixtures/ holds a ~20-property synthetic corpus
notebooks/                report-style views over derived outputs only
docs/                     specs, data-readiness report, validation report, model card,
                          API contract, productionization notes
demo/index.html           single static page served by the API
```

### 4.2 Stage contract

Every stage is a `prov <stage>` subcommand. A stage reads only the sponsor CSVs (via `io.py`)
and the parquet outputs of earlier stages, and writes its own outputs plus a small
`<stage>.meta.json` recording inputs, row counts, protocol hash, and timestamp.

Two mechanical guards:

1. `io.load_properties(outcome_blind=True)` drops `last_sale_price`, `last_sale_date`,
   `assessed_value`, `avm_estimate`, `sale_count`, `market_median_sale_price`, `hpi_value`,
   `hpi_yoy_change`, `hmda_median_value`. Stages 2–4 only ever call the blind loader. A test
   asserts that `index.py` cannot observe those columns.
2. `prov validate` aborts if `protocol/v1.yaml`'s hash differs from the hash stamped in
   `index.meta.json`. Changing the protocol after scoring requires re-running the index and
   is visible in git history.

### 4.3 Stages

**Stage 1 — audit + protocol.** See the piece 1 spec
(`2026-09-01-piece1-audit-protocol-design.md`).

**Stage 2 — resolve.**
- Subjects: normalize names (case, punctuation, corporate suffixes, initials); block on
  `subject_type` + first significant token; score candidate pairs with token-set ratio
  (rapidfuzz); pairs ≥ 0.92 auto-merge, 0.80–0.92 go to `data/derived/subject_review.csv`
  for hand adjudication, below 0.80 stay separate. Output `subject_clusters.parquet`
  (`subject_id → canonical_id`). Adjudications are read back from
  `protocol/subject_adjudications.csv` if present.
- Parcels: normalize `properties.address` and `property_parcels.normalized_address`
  (house number + street token + suffix), match exactly, then by house-number range for
  hyphenated addresses. Output `parcel_matches.parquet` and a match rate in the meta file.
  Parcel `lot_sqft` backfills only where the property's `lot_polygon` is null.

**Stage 3 — graph.**
- `nodes.parquet`: properties, canonical subjects, incidents.
- `edges.parquet`: property–incident, incident–subject (with relationship, relationship weight,
  evidence weight), incident–incident (link_type). Every edge carries `knowable_from`.
- `graph.as_of(date)` filters edges by `knowable_from <= date` and returns a networkx graph.
- Property projection: two properties are linked when they share a canonical subject; edge
  weight is the sum over shared subjects of relationship weight × evidence weight. Connectivity
  is eigenvector centrality on this projection, normalized to [0, 1] across the corridor.

**Stage 4 — index.** For each property and an as-of date (default: today, plus one row per
sale date for panel use):

```
Π = V × (D + β·C) × S^γ × X
```

| Term | Definition (all in [0, 1]) |
|---|---|
| V, Verifiability | evidence-weighted mean over curated claims; ungraded curated claims take the protocol's `ungraded` weight |
| D, Density | log1p(curated claim count) / log1p(corridor max) |
| C, Connectivity | eigenvector centrality on the property projection |
| S, Salience | mean of category salience weights over curated claims |
| X, Distinctiveness | mean inverse-frequency of the property's claim categories across the corridor, rescaled to [0, 1] |

Also emitted per property: `source_coverage` (distinct curated sources), `curated_claims`,
`archival_silence` (true when curated claims = 0), `silence_type` (`unsearched` when the
property's block side has fewer than the protocol's `block_min_sources` distinct curated
sources, else `searched`), and `index_audit.parquet` mapping each property to every claim id
that contributed.

**Stage 5a — panel.** One row per property with an arm's-length sale (protocol filter).
Outcome `ln(last_sale_price)`. Covariates: `year_built`, `structure_sqft`, lot area (from
`lot_polygon`, else parcel backfill), `dwelling_units`, `zoning_code`, `latitude`,
`longitude`, `census_tract`, `market_typology`, `vacancy_indicator`, sale year. Π and its
components computed as of the sale date. Secondary panel on `ln(assessed_value)` labelled
administrative.

**Stage 5b — validate.**
- Baseline: OLS hedonic on the covariates with tract and sale-year effects; alternative:
  gradient boosting on the same features.
- Incremental: baseline + Π (and, separately, + components).
- Holdouts: GroupKFold on `block_side_id` (spatial); one temporal split training on sales
  before 2024-01-01.
- Metrics: out-of-sample R² gain, MAE reduction, calibration slope; 1,000-draw bootstrap CIs.
- Connectivity test: add a k-nearest-neighbour spatial lag of the outcome (computed within
  training folds only) and test whether C still adds held-out power.
- Robustness: the protocol's pre-specified β/γ grid; drop-white-papers; graded-claims-only.
- Decision: `decision.json` with `monetary_display: bool`, the metrics that produced it, and
  the protocol hash. Rule is in the protocol. Report generated to `docs/validation_report.md`.

**Stage 6 — serve.**
- `GET /health`, `GET /properties/{id}`, `GET /address?q=` (normalized address lookup).
- Address response: `history` (curated claims with source, date, precision, evidence status,
  and a `summary_only` flag for sensitivity-flagged claims), `evidence` (components, Π,
  coverage, silence flag, protocol version, and `monetary_band` only when
  `decision.monetary_display` is true), `actions` (grant program matches).
- OpenAPI document is the API/data contract; prose contract, model card, and
  productionization notes live in `docs/`.
- `demo/index.html`: address box, three panels, no framework.

## 5. Testing

- `tests/fixtures/`: a synthetic ~20-property corpus with every table, exercising each
  source class, an ungraded claim, a sensitivity flag, a duplicate subject, a $1 sale, and
  a white-paper claim postdating a sale.
- Unit tests per stage; an integration test runs `prov all` on the fixture.
- Index invariants: blind loader exposes no outcome column; Π is monotone non-decreasing in
  V holding other terms fixed; Π as of an earlier date never exceeds Π as of a later date.
- API tests via FastAPI's test client, including that `monetary_band` is absent when the
  decision is false.

## 6. Failure modes

Stages fail loudly, never default silently:
- schema drift in a CSV (missing/renamed column) → error naming the column;
- a `source` value absent from the protocol's knowability map → error listing it;
- protocol hash mismatch at validate → error with both hashes;
- panel below the protocol's minimum usable sample → validation writes `decision.json` with
  `monetary_display: false, reason: "insufficient_sample"` and still generates the report.

## 7. Sequencing

Four implementation plans, each preceded by its own spec where the roadmap is not already
specific enough:

1. **Piece 1** — scaffold, loaders, audit, protocol (spec written alongside this document).
2. **Piece 2** — resolve, graph, index.
3. **Piece 3** — panel, validate, decision, validation report.
4. **Piece 4** — API, demo page, model card, contract, productionization notes.

Each piece ends with `prov all` passing on the fixture and on the real data.
