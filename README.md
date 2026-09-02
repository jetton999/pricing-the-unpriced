# Pricing the Unpriced — Sample Data Package
**NYU CUSP Capstone 2026–2027 · Sponsor: BNBD / Oxcart Assembly**

This repository is the sponsor data package for the NYU CUSP 2026-2027 Capstone project
*Pricing the Unpriced*. It is a full export of the sponsor's corridor knowledge base, plus the
public source files, so a student team can judge data readiness before committing. Everything
here is sponsor-produced or public record. No personal user data is included: property owner
names are retained because they are SDAT public record and are the substance of ownership
research, but 17 individual contact phone numbers that had come through the liquor-license,
permit, and white-paper feeds were redacted to `[phone redacted]` before publication. They
carried no analytical value.

---

## QUICKSTART

```bash
git clone https://github.com/jetton999/pricing-the-unpriced.git
cd pricing-the-unpriced
pip install pandas matplotlib networkx jupyter
jupyter notebook START_HERE.ipynb
```

Open **`START_HERE.ipynb`** in the same folder as the CSVs and run it top to bottom.
GitHub also renders it in the browser, if you would rather read the code and its output first.
Needs `pandas`, `matplotlib`, `networkx`. In about five minutes it will:

1. Load all nine tables and show you how they join
2. Separate the curated archival layer from the administrative feeds (read §1 below first)
3. Profile the evidence grading
4. Rank properties by documentation depth — the labeled spine
5. Build the people–place–event graph (3,613 nodes, 3,765 edges)
6. Compute a first, deliberately naive connectivity score
7. Leave you at the open research question with a modeling frame in hand

---

## 1. Read this before you look at the row counts

The incident table has **20,308 rows, and that number is misleading on its own.**

| Layer | Rows | What it is |
|---|---|---|
| **Administrative feeds** | ~16,700 | Machine-ingested: 311 complaints (6,641), permits (5,329), SDAT assessments (3,064), crime (803), tax certificates, code violations. Overwhelmingly 2020s. |
| **Curated historical records** | ~3,600 | Hand-researched across 40+ archival sources: research white papers (1,138), Newspapers.com (661), church interment rolls (583), MDLandRec deeds (492), Sanborn fire-insurance maps (254), NRHP nominations (139), Polk directories, Hopkins atlases, Chronicling America, census records. |

**3,633 incidents predate 2000. 2,259 predate 1950.** The archival layer runs back to the 1730s.

Separating these two layers is not a preprocessing chore. **It is the research problem.**
An index that rewards whichever property generated the most paperwork has learned nothing
about historical significance. The proposal names this the archival-abundance risk and
commits to a source-coverage measure; this package is where you will first see why.

See `05_incidents_by_decade.png` for the picture.

## 2. Documentation depth is concentrated

| Curated incidents | Properties |
|---|---|
| ≥ 1 | 316 |
| ≥ 10 | 68 |
| ≥ 25 | 22 |

(These are what cell 7 of `START_HERE.ipynb` prints. The deepest three are 2376 with 599
curated incidents, 2332 with 260, and 742 with 150.)

The deep end is the labeled spine the index gets built and validated on. The rest of the
1,874 properties carry mostly administrative traces. Sparse documentation is **not**
evidence of no history; treat it as unmeasured.

## 3. Evidence grading is real but partial

Every incident is a *claim*, not a fact. The schema carries `evidence_status`
(verified / probable / possible / contested), `date_precision` (exact / year / range /
circa / decade / unknown), `sensitivity`, and `rights`.

Coverage today: **1,328 incidents graded** (1,162 verified, 105 probable, 59 possible,
2 contested) and **1,908 with explicit date precision**. The rest are ungraded — mostly
administrative rows where grading is not meaningful, but some curated rows too.
Back-filling and validating this grading is committed capstone work.

`incident_links.csv` already encodes disagreement between claims: 112 `related`,
100 `supports`, 21 `duplicates`, 3 `contradicts`.

## 4. Tables

| File | Rows | What it is |
|---|---|---|
| `properties.csv` | 1,874 | Properties under research with ~80 enrichment fields: assessment, sale history, vacancy, zoning, market, transit, HMDA, program-eligibility flags. 1,791 have coordinates; 1,789 have a last sale price. |
| `property_incidents.csv` | 20,308 | The claim layer. See §1 before using. |
| `subjects.csv` | 3,103 | Graph nodes: 2,035 people, 527 businesses, 300 organizations, 138 families, plus places, teams, congregations. |
| `incident_subjects.csv` | 5,462 | Subject↔incident edges: `owned` (926), `operated_at` (678), `sold` (661), `interred_at` (596), `purchased` (455), `lived_at` (280), and more. |
| `incident_links.csv` | 236 | Incident↔incident edges, including contradictions. |
| `registered_ips.csv` | 115 | Patents and trademarks with address of record and match confidence. |
| `property_parcels.csv` | 50,860 | Parcel roll (SDAT / city): address, blocklot, owner, land use, sqft. The linkage layer. |
| `grant_program_matches.csv` | 11,789 | Property↔program matches behind the live "Improve Your Property" tool. |
| `neighborhoods.csv` | 6 | Neighborhood boundaries. |
| `baseline_snapshots.csv` | 887 | **The t0 line.** See §4b. |

Notes: `data` columns are JSON payloads. Respect `sensitivity` and `rights` on incidents —
some claims are flagged restricted or consent-dependent. Row counts are the full database;
the proposal's corridor figures describe the deeply documented pilot spine within it.

## 4b. The t0 baseline — the "before" line already exists

`baseline_snapshots.csv` is the most time-sensitive asset in this package, because a
before/after design cannot recreate its own starting line retroactively.

Two capture days are on record: **2026-07-13 (351 properties)** and **2026-07-22 (536 properties)**.
Each row freezes one property as of that date across 29 fields: `assessed_value`, `avm_estimate`,
`last_sale_price` / `last_sale_date`, `sale_count`, `vacancy_indicator`, `vacant_notice_status`,
`active_permit_count`, `violations_12mo_count`, `building_condition`, `owner_name` / `owner_type`,
`ground_rent`, `city_owned`, `receivership_status`, `tax_certificate_active`,
`hmda_loan_count` / `hmda_denial_rate` / `hmda_median_value`, `cdbg_investment_total`,
`public_investment_total`, `market_typology`, `market_median_sale_price`, `fair_market_rent_2br` —
**and, critically, `incident_count` and `registered_ip_count`, the provenance depth at that moment.**

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

- **Coverage is uneven by design.** Research followed interest and grant funding, not a sampling frame. Expect selection effects in which properties are deeply documented.
- **Evidence grading is incomplete** (see §3).
- **Geocoding and parcel matching are imperfect.** `property_parcels.matched_property_id` is null for most rows.
- **Temporal leakage is the sharpest methodological trap.** A white paper written in 2026 cannot inform a 2005 sale price. Reconstruct what was knowable *as of* the outcome date.
- **`assessed_value` is an administrative outcome, not a market price.** Do not present it as one.
- **Only two baseline days exist so far.** Treat t0 as a fixed reference point, not a time series.

## 7. Also in this folder

- `Pricing_the_Unpriced_CUSP_Proposal.pdf` — the full proposal: methods, tiered scope, work plan, risk register.
  Note that the proposal was written in July 2026 and the CSVs here were exported later, so the
  corpus grew underneath it. Where the proposal says "~354 documented properties, ~2,600
  documented incidents," this export holds 1,874 properties and 20,308 incidents (3,602 of them
  curated). The one figure that moved the other way is registered IP: the proposal says "~150
  registered intellectual-property records," and the actual count is 115 (101 trademarks,
  11 patents, 3 entity registrations). The CSVs are authoritative; `verify_claims.py` checks them.
- `DATA_DICTIONARY.md` — column listings per table.
- `row_counts.txt` — export row counts.
- `05_incidents_by_decade.png` — the corpus at a glance.
- `verify_claims.py` — checks all 51 numbers in this README against the CSVs. Standard library
  only, no install step. Run `python3 verify_claims.py`. If it ever disagrees with this README,
  the data wins and the README is what needs fixing.

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
