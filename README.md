# Pricing the Unpriced — Sample Data Package
**NYU CUSP Capstone 2026–2027 · Sponsor: BNBD / Oxcart Assembly**

This repository is the sponsor data package for the NYU CUSP 2026-2027 Capstone project
*Pricing the Unpriced*. It is a full export of the sponsor's Greenmount corridor knowledge base,
plus the public source files, so a student team can judge data readiness before committing.
Everything here is sponsor-produced or public record. No personal user data is included: property
owner names are retained because they are SDAT public record and are the substance of ownership
research, but 17 individual contact phone numbers that had come through the liquor-license,
permit, and white-paper feeds were redacted to `[phone redacted]` before publication. They
carried no analytical value.

---

## QUICKSTART

You need Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
(`brew install uv` on macOS, or `pipx install uv`, or `curl -LsSf https://astral.sh/uv/install.sh | sh` on Linux).

```bash
git clone https://github.com/jetton999/pricing-the-unpriced.git
cd pricing-the-unpriced
uv sync                                   # creates .venv with every dependency
uv run pre-commit install                 # keeps notebook outputs out of git
uv run jupyter lab START_HERE.ipynb       # opens the starter notebook
```

Run the notebook top to bottom (Run > Run All Cells). It takes under a minute and walks through:

| § | What it shows |
|---|---|
| 0 | The two traps in `properties.csv`: two geographies, and columns that are blank or all-zero |
| 1 | The curated archival layer vs the administrative feeds (read §1 below first) |
| 2 | Evidence grading, sensitivity flags, and claim-to-claim links |
| 3 | Where documentation depth is concentrated, and when (the decade chart) |
| 4 | **Idea 1:** one property's use history, which properties have one, and block sides as the assemblage unit |
| 5 | **Idea 2:** what corridor commercial buildings cost, the July 2026 baseline, and a toy lease-to-own calculator |
| 6 | A one-row-per-property starter table for both ideas |

Two more things work with no install beyond Python itself:

```bash
python3 map/app.py            # map of every property; open http://localhost:8765
python3 verify_claims.py      # checks every number in this README against the CSVs
```

<details>
<summary>No uv? Use pip in a virtual environment instead.</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install pandas matplotlib jupyterlab jupytext nbstripout pre-commit
pre-commit install
jupyter lab START_HERE.ipynb
```

A bare `pip install` outside a virtual environment fails on recent macOS (Homebrew) and
Debian/Ubuntu Python with `externally-managed-environment`. That is why the venv step is there.
</details>

**Editing the notebook.** `START_HERE.py` and `START_HERE.ipynb` are the same notebook, paired
with [jupytext](https://jupytext.readthedocs.io/). The `.py` is the source of truth: edit it, then
run `uv run jupytext --sync START_HERE.py`. Once `pre-commit install` has run, the sync and the
output stripping happen automatically on every commit. Working with a coding agent? Point it at
[`AGENTS.md`](AGENTS.md) and have it run `bin/check` before it says it is done.

### What's where

| Path | What it is |
|---|---|
| `START_HERE.ipynb` / `.py` | The starter notebook. Start here. |
| `PROJECT_IDEAS.md` | The two applied project ideas, in full. |
| `DATA_DICTIONARY.md` | Every column of every table, with the empty ones marked. |
| `*.csv` | The ten exported tables (§4). |
| `map/` | Standard-library map app over the CSVs. See `map/README.md`. |
| `docs/` | Background research: worker- and tenant-owned exit cases; the coding-agent setup plan. |
| `site/` | The revised proposal (September 2026) as a single HTML page, plus its PDF. |
| `public_sources/` | Third-party files: National Register, federal DOEs, HOLC polygons (§5). |
| `Pricing_the_Unpriced_CUSP_Proposal.pdf` | The original July 2026 proposal (§7). |
| `verify_claims.py` | Checks every number in this README. Standard library only. |
| `bin/check` | Runs all the checks: README claims, map data, notebook sync, notebook execution. |
| `05_incidents_by_decade.png` | The corpus at a glance (§1). |
| `row_counts.txt` | Export row counts. |

---

## Two applied project ideas (September 2026)

Since the July proposal, the sponsor has sketched two applied projects that run on this same
record. Both are described in **[PROJECT_IDEAS.md](PROJECT_IDEAS.md)**, and a revised proposal
presenting them is in **[`site/`](site/)**.

1. **Heritage-anchored highest and best use.** Given an assemblage of buildings, what should each
   one become, what would it earn, and does the mix work as a block? It starts from what each
   address *was*. The use-history timeline it needs is exactly what the provenance layer in this
   package produces.
2. **From tenant to owner.** A lease that starts a business as an ordinary tenant of the sponsor's
   real estate trust and ends with it owning the building. It is designed against eleven documented
   worker- and tenant-ownership cases in Baltimore, DC, New York, and Portland
   (`docs/worker-owned-exits.md`).

A team may take one idea or both. The data package below, its layer distinction, and its warnings
carry over unchanged.

---

## 1. Read this before you look at the row counts

The incident table has **20,308 rows, and that number is misleading on its own.**

| Layer | Rows | What it is |
|---|---|---|
| **Administrative feeds** | ~16,700 | Machine-ingested: 311 complaints (6,641), permits (5,329), SDAT assessments (3,064), crime (803), tax certificates, code violations. Overwhelmingly 2020s. |
| **Curated historical records** | ~3,600 | Hand-researched across 40+ archival sources: research white papers (1,138), Newspapers.com (661), church interment rolls (583), MDLandRec deeds (492), Sanborn fire-insurance maps (254), NRHP nominations (139), Polk directories, Hopkins atlases, Chronicling America, census records. |

The rule: a `source` is administrative if it starts with `baltimore:` or is `sdat_assessments`
or `sdat:owner`. Everything else is curated. The notebook, the map, and `verify_claims.py` all
use this one rule.

**3,633 incidents predate 2000. 2,259 predate 1950.** The earliest dated record is 1658, the
Stansbury land assignment that underlies the 1688 Huntington and Merryman's Lot patent; the first
recorded residence on the tract is 1736.

Separating these two layers is not a preprocessing chore. **It is the research problem.**
An index that rewards whichever property generated the most paperwork has learned nothing
about historical significance. The proposal names this the archival-abundance risk and
commits to a source-coverage measure; this package is where you will first see why.

See `05_incidents_by_decade.png` for the picture: one panel per layer, each on its own scale.

## 2. Documentation depth is concentrated

| Curated incidents | Properties |
|---|---|
| ≥ 1 | 316 |
| ≥ 10 | 68 |
| ≥ 25 | 22 |

(These are what section 3 of the notebook prints. The deepest three are 2376 with 599
curated incidents, 2332 with 260, and 742 with 150.)

The deep end is the labeled spine the index gets built and validated on. The rest of the
1,874 properties carry mostly administrative traces. Sparse documentation is **not**
evidence of no history; treat it as unmeasured.

## 3. Evidence grading is real but partial

Every incident is a *claim*, not a fact. The schema carries `evidence_status`
(verified / probable / possible / contested), `date_precision` (exact / year / range /
circa / decade / unknown), `sensitivity`, and `rights`.

Coverage today: **1,328 incidents graded** (1,162 verified, 105 probable, 59 possible,
2 contested) and **1,908 with explicit date precision**. Those totals span both layers: 841 of
the graded rows are curated, and 487 are administrative (almost all `sdat:owner` ownership
records, marked verified). Of the 3,602 curated rows, 2,761 are still ungraded. Back-filling
and validating this grading is committed capstone work.

`incident_links.csv` already encodes disagreement between claims: 112 `related`,
100 `supports`, 21 `duplicates`, 3 `contradicts`.

## 4. Tables

| File | Rows | What it is |
|---|---|---|
| `properties.csv` | 1,874 | Properties under research with ~80 enrichment fields: assessment, sale history, vacancy, zoning, market, transit, HMDA, program-eligibility flags. **1,456 are on the Greenmount corridor (ZIP 21218); 418 are Baltimore Peninsula parcels (ZIP 21230).** 1,791 have coordinates. 1,789 have a `last_sale_price`, but 419 of those are $0 transfers, so 1,370 carry a real price. |
| `property_incidents.csv` | 20,308 | The claim layer. See §1 before using. |
| `subjects.csv` | 3,103 | Graph nodes: 2,035 people, 527 businesses, 300 organizations, 138 families, plus places, teams, congregations. |
| `incident_subjects.csv` | 5,462 | Subject↔incident edges: `owned` (926), `operated_at` (678), `sold` (661), `interred_at` (596), `purchased` (455), `lived_at` (280), and more. Joined through incidents, subjects and properties form a graph of 3,613 nodes and 3,765 edges. |
| `incident_links.csv` | 236 | Incident↔incident edges, including contradictions. |
| `registered_ips.csv` | 115 | 101 trademarks, 11 patents, and 3 entity registrations, with address of record and match confidence. 17 are matched to a specific property. |
| `property_parcels.csv` | 50,860 | Parcel roll (SDAT / city): address, blocklot, owner, land use, sqft. The linkage layer. |
| `grant_program_matches.csv` | 11,789 | Property↔program matches behind the live "Improve Your Property" tool. |
| `neighborhoods.csv` | 6 | Neighborhood names only. The `bounds` column is empty in this export. |
| `baseline_snapshots.csv` | 887 | **The t0 line.** See §4b. |

Notes: `data` columns are JSON payloads. Respect `sensitivity` and `rights` on incidents —
some claims are flagged restricted or consent-dependent. Row counts are the full database;
the proposal's corridor figures describe the deeply documented pilot spine within it.

**Columns that look like data but are not.** Some `properties.csv` columns are blank in every
row (`avm_estimate`, `walk_score`, `transit_score`, `bike_score`, `building_condition`,
`building_quality`, `num_stories`, `irs_agi_per_return`, `irs_homeowner_pct`). Others are `0` in
every row, which is a placeholder, not a measurement: `sale_count`, `nearby_restaurants`,
`nearby_shops`, `nearby_amenities_total`, `public_investment_total`. `DATA_DICTIONARY.md` marks
them all, and section 0 of the notebook finds them programmatically.

## 4b. The t0 baseline — the "before" line already exists

`baseline_snapshots.csv` is the most time-sensitive asset in this package, because a
before/after design cannot recreate its own starting line retroactively.

Two capture days are on record: **2026-07-13 (351 properties)** and **2026-07-22 (536 properties)**.
Each row freezes one property as of that date across 28 fields: `assessed_value`, `avm_estimate`,
`last_sale_price` / `last_sale_date`, `sale_count`, `vacancy_indicator`, `vacant_notice_status`,
`active_permit_count`, `violations_12mo_count`, `building_condition`, `dwelling_units`,
`has_active_business`, `owner_name` / `owner_type`, `ground_rent`, `city_owned`,
`receivership_status`, `tax_certificate_active`, `hmda_loan_count` / `hmda_denial_rate` /
`hmda_median_value`, `cdbg_investment_total`, `public_investment_total`, `market_typology`,
`market_median_sale_price`, `fair_market_rent_2br` —
**and, critically, `incident_count` and `registered_ip_count`, the provenance depth at that moment.**
Seven of the 28 were captured empty: `avm_estimate`, `building_condition`, `market_median_sale_price`,
and `vacant_notice_status` are blank; `ground_rent` is blank or 0; `sale_count` and
`public_investment_total` are 0.

That last pair is what makes this a research instrument rather than a property dump. It records how
much was *known* about each property on a fixed date, so later documentation work becomes a
measurable treatment rather than an untracked confound. Capture continues on the sponsor's side.

## 5. Public sources (`/public_sources`)

- `national-register-listed_20260522.xlsx` — NPS National Register, 100,867 dated listings. Treatment data for the conditional external analysis.
- `federal-DOEs_20260522.xlsx` — Federal Determinations of Eligibility. Included so you can verify the proposal's finding that it is **unsuitable** as a control: rows are federal projects, undated.
- `holc_baltimore_1937.geojson` — HOLC "redlining" polygons (Mapping Inequality, Univ. of Richmond).

Fetch directly, not redistributed here: Open Baltimore (parcels, permits, vacancy),
Maryland SDAT, NPS IRMA GIS (Ref. 2210280), ACS/TIGER. ZTRAX is restricted-use via ICPSR
and cannot be redistributed; the committed corridor work does not depend on it.

## 6. Known limitations, stated up front

- **Two geographies share one table.** 418 of the 1,874 properties are Baltimore Peninsula parcels (ZIP 21230), several miles from Greenmount. Filter on `zip_code == 21218` for corridor statistics; unfiltered, the median commercial sale price comes out several times too high.
- **Coverage is uneven by design.** Research followed interest and grant funding, not a sampling frame. Expect selection effects in which properties are deeply documented.
- **Evidence grading is incomplete** (see §3).
- **Some columns are empty or zero-filled** (see §4). A `0` in `nearby_restaurants` or `sale_count` means "not captured", not "none".
- **Sale prices include portfolio deals.** When several parcels sell together, each parcel carries the whole deal price. Drop any price and date shared by more than one parcel before computing price per building or per sqft (notebook §5a).
- **Geocoding and parcel matching are imperfect.** `property_parcels.matched_property_id` is null for most rows.
- **Temporal leakage is the sharpest methodological trap.** A white paper written in 2026 cannot inform a 2005 sale price. Reconstruct what was knowable *as of* the outcome date.
- **`assessed_value` is an administrative outcome, not a market price.** Do not present it as one.
- **Only two baseline days exist so far.** Treat t0 as a fixed reference point, not a time series.

## 7. About the proposal PDF

`Pricing_the_Unpriced_CUSP_Proposal.pdf` is the full July 2026 proposal: methods, tiered scope,
work plan, risk register. It was written before the CSVs here were exported, so the corpus grew
underneath it. Where the proposal says "~354 documented properties, ~2,600 documented incidents,"
this export holds 1,874 properties and 20,308 incidents (3,602 of them curated). The one figure
that moved the other way is registered IP: the proposal says "~150 registered
intellectual-property records," and the actual count is 115 (101 trademarks, 11 patents,
3 entity registrations). The CSVs are authoritative.

`verify_claims.py` checks every number in this README against the CSVs. It is standard library
only: run `python3 verify_claims.py`. If it ever disagrees with this README, the data wins and the
README is what needs fixing.

Live tools the pilot extends: **greenmountcorridor.com/research** · **greenmountcorridor.com/improve**

---

## 8. License

Sponsor-produced data is CC BY 4.0. Third-party files in `/public_sources` carry their own
terms, and the HOLC polygons are CC BY-NC-SA 4.0. See [LICENSE.md](LICENSE.md), which also
explains why 52 incident rows carry a `sensitivity` flag and why you should not silently
drop them.

## 9. Questions

Open an issue on this repository, or contact the sponsor directly. The sponsor maintains the
production system this pilot extends, so you will not be the IT department.
