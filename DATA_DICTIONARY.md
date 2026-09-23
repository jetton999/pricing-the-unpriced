# Data Dictionary

Every column of every CSV, in file order. **Filled** is the share of rows with a value.
**blank** means empty in every row and **all 0** means `0` in every row: a placeholder, not a
measurement. Do not read a 0 there as "none". `python3 verify_claims.py` checks the blank and
all-0 markers on `properties.csv` against the data.

Joins: `property_incidents.property_id` → `properties.id`; `incident_subjects` links
`property_incidents` to `subjects`; `incident_links` links incidents to each other;
`registered_ips`, `grant_program_matches`, and `baseline_snapshots` hang off `properties.id`.

## properties

`properties.csv` · 1,874 rows. One row per property. **Two geographies:** 1,456 rows are on the Greenmount corridor (`zip_code` 21218) and 418 are Baltimore Peninsula parcels (21230). Filter on `zip_code` before describing "the corridor".

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `address` | string | 100% |  |
| `block_side_id` | bigint | 91% | One side of one block. The default assemblage unit (141 values). |
| `created_at` | datetime | 100% |  |
| `latitude` | decimal | 96% |  |
| `longitude` | decimal | 96% |  |
| `owner_name` | string | 96% |  |
| `owner_type` | string | 22% | Values: `unknown`, `city`, `private_owner`; blank in most rows. |
| `updated_at` | datetime | 100% |  |
| `blocklot` | string | 95% |  |
| `assessed_value` | integer | 95% | Administrative outcome, not a market price. |
| `vacancy_indicator` | boolean | 13% |  |
| `year_built` | integer | 95% | `0` means unknown (399 rows). |
| `zoning_code` | string | 95% | Has trailing spaces in some rows: `.str.strip()` before matching. The notebook treats codes starting `C` or `PC` as commercial. |
| `last_sale_price` | integer | 95% | 419 rows are $0 transfers. Portfolio sales repeat the whole deal price on every parcel. |
| `last_sale_date` | date | 95% |  |
| `lot_polygon` | jsonb | 95% |  |
| `building_polygons` | jsonb | 82% |  |
| `city_owned` | boolean | 100% |  |
| `alias` | string | 2% |  |
| `has_active_business` | boolean | 96% |  |
| `opportunity_zone` | boolean | 100% |  |
| `flood_zone` | string | <1% |  |
| `historic_district` | string | 21% |  |
| `enterprise_zone` | boolean | 100% |  |
| `incidents_12mo_count` | integer | 100% |  |
| `violations_12mo_count` | integer | 100% |  |
| `census_tract` | string | 95% |  |
| `environmental_flag` | boolean | 99% |  |
| `fair_market_rent_2br` | integer | 100% | HUD residential FMR for the ZIP; an order-of-magnitude anchor only. |
| `median_household_income` | integer | 83% |  |
| `vacant_notice_status` | string | 3% |  |
| `active_permit_count` | integer | 100% |  |
| `receivership_status` | string | 3% |  |
| `roof_damage_risk` | float | 1% |  |
| `tax_certificate_active` | boolean | 100% |  |
| `market_typology` | string | 84% | Market typology category (B–G in this export). |
| `crimes_12mo_count` | integer | 100% |  |
| `cdbg_eligible` | boolean | 100% |  |
| `inspire_eligible` | boolean | 100% |  |
| `arts_district` | boolean | 100% |  |
| `healthy_neighborhood` | boolean | 100% |  |
| `lincs_corridor` | boolean | 100% |  |
| `main_street_district` | boolean | 100% |  |
| `niif_area` | boolean | 100% |  |
| `sustainable_community` | boolean | 100% |  |
| `food_desert` | boolean | 100% |  |
| `public_investment_total` | integer | **all 0** |  |
| `walkability_index` | float | 83% |  |
| `transit_distance_m` | integer | 83% |  |
| `jobs_transit_45min` | integer | 83% |  |
| `lihtc_nearby_count` | integer | 100% |  |
| `hud_reo` | boolean | 100% |  |
| `qualified_census_tract` | boolean | 100% |  |
| `difficult_development_area` | boolean | 100% |  |
| `cdbg_investment_total` | integer | 100% |  |
| `hmda_loan_count` | integer | 83% |  |
| `hmda_median_value` | integer | 83% |  |
| `hmda_denial_rate` | float | 83% |  |
| `hpi_value` | float | 44% |  |
| `hpi_yoy_change` | float | 44% |  |
| `ground_rent` | integer | 95% |  |
| `dwelling_units` | integer | 95% |  |
| `structure_sqft` | integer | 95% | `0` means unknown (494 rows). |
| `building_condition` | string | **blank** |  |
| `building_quality` | string | **blank** |  |
| `num_stories` | integer | **blank** |  |
| `has_basement` | boolean | 100% |  |
| `has_central_ac` | boolean | 100% |  |
| `market_median_sale_price` | integer | 100% |  |
| `market_median_dom` | integer | 100% |  |
| `market_inventory` | integer | 100% |  |
| `walk_score` | integer | **blank** |  |
| `transit_score` | integer | **blank** |  |
| `bike_score` | integer | **blank** |  |
| `nearby_restaurants` | integer | **all 0** |  |
| `nearby_shops` | integer | **all 0** |  |
| `nearby_amenities_total` | integer | **all 0** |  |
| `irs_agi_per_return` | integer | **blank** |  |
| `irs_homeowner_pct` | float | **blank** |  |
| `avm_estimate` | integer | **blank** |  |
| `sale_count` | integer | **all 0** |  |
| `zip_code` | string | 100% | 21218 = Greenmount corridor, 21230 = Baltimore Peninsula. |
| `block_plat_url` | string | 95% |  |
| `tax_certificate_status` | string | 7% |  |
| `tax_certificate_sold_on` | date | 7% |  |
| `receivership_filed_on` | date | 1% |  |

## property_incidents

`property_incidents.csv` · 20,308 rows. The claim layer: one dated event at one property. Split it into two layers before any analysis. A `source` starting with `baltimore:`, or equal to `sdat_assessments` or `sdat:owner`, is **administrative** (16,706 rows); everything else is **curated** (3,602). See README §1.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_id` | bigint | 100% | → `properties.id`. |
| `source` | string | 100% | Decides the layer (see above). `stjohns_interments` is curated. |
| `source_id` | bigint | 100% | ID of the record in its source system. |
| `category` | string | 100% | 29 values: `complaint`, `permit`, `sale`, `crime`, `news`, `interment`, `ownership`, `civic`, … |
| `occurred_at` | datetime | 100% | Start of the event. Read with `date_precision`. |
| `summary` | string | 100% | Human-readable description of the claim. |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `created_at` | datetime | 100% |  |
| `evidence_status` | string | 7% | `verified` / `probable` / `possible` / `contested`; blank = ungraded. |
| `occurred_at_end` | datetime | <1% | End of a range, when `date_precision` is `range`. |
| `date_precision` | string | 9% | `exact` / `year` / `range` / `circa` / `decade` / `unknown`; blank = unset. |
| `sensitivity` | string | <1% | `trauma`, `personal_rights`, `displacement`, `commercialization`. Never drop these rows silently (LICENSE.md). |
| `rights` | string | 3% | `public` where set. |

## subjects

`subjects.csv` · 3,103 rows. People, businesses, organizations, families, and other named entities that appear in incidents.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `name` | string | 100% |  |
| `subject_type` | string | 100% | `person`, `business`, `organization`, `family`, `place`, `team`, `congregation`, `other`, `event`. |
| `slug` | string | 100% |  |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## incident_subjects

`incident_subjects.csv` · 5,462 rows. Edges between a subject and an incident: who did what, where. Join `property_incident_id` → `property_incidents.id` → `property_id` to reach the property.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_incident_id` | bigint | 100% | → `property_incidents.id`. |
| `subject_id` | bigint | 100% | → `subjects.id`. |
| `relationship` | string | 100% | 23 values: `owned`, `operated_at`, `sold`, `interred_at`, `purchased`, `lived_at`, …  `operated_at` links people and organizations too, not just businesses. |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## incident_links

`incident_links.csv` · 236 rows. Edges between two incidents, including where claims disagree.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_incident_id` | bigint | 100% | → `property_incidents.id`. |
| `related_incident_id` | bigint | 100% | → `property_incidents.id`. |
| `link_type` | string | 100% | `related`, `supports`, `duplicates`, `contradicts`. |
| `note` | text | 90% |  |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## registered_ips

`registered_ips.csv` · 115 rows. Trademarks, patents, and entity registrations, each with an address of record and a match confidence.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `address_of_record` | string | 100% |  |
| `created_at` | datetime | 100% |  |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `filing_date` | date | 91% |  |
| `grant_date` | date | 54% |  |
| `ip_type` | string | 100% | `trademark` (101), `patent` (11), `entity` (3). |
| `match_confidence` | string | 100% | `high`, `medium`, `low`, `inferred`: how sure the address match is. |
| `number` | string | 100% |  |
| `owner_name` | string | 100% |  |
| `property_id` | bigint | 15% | → `properties.id`; set for 17 of 115 rows. |
| `source` | string | 100% |  |
| `status` | string | 100% | `registered`, `abandoned`, `expired`, `pending`, `cancelled`. |
| `title` | string | 96% |  |
| `updated_at` | datetime | 100% |  |

## property_parcels

`property_parcels.csv` · 50,860 rows. The SDAT / city parcel roll for the surrounding area. The linkage layer, not the research set.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `source` | string | 100% |  |
| `source_id` | string | 100% |  |
| `blocklot` | string | 100% |  |
| `address` | string | 100% |  |
| `normalized_address` | string | 92% |  |
| `sqft` | integer | 92% |  |
| `land_use` | string | 100% |  |
| `owner` | string | 100% |  |
| `matched_property_id` | bigint | <1% | → `properties.id`; set for only 235 of 50,860 rows. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |
| `lot_sqft` | integer | 100% |  |

## grant_program_matches

`grant_program_matches.csv` · 11,789 rows. Property-to-program eligibility matches behind the live "Improve Your Property" tool.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_id` | bigint | 100% | → `properties.id`. |
| `program_key` | string | 100% |  |
| `program_name` | string | 100% |  |
| `category` | string | 100% |  |
| `amount_cap` | string | 46% |  |
| `summary` | text | 100% |  |
| `matched_reason` | string | 100% | Why the property qualified. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## neighborhoods

`neighborhoods.csv` · 6 rows. Names only: `bounds` is empty in this export, so there is no neighborhood geometry.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `bounds` | jsonb | **blank** | Empty in every row. |
| `created_at` | datetime | 100% |  |
| `name` | string | 100% |  |
| `updated_at` | datetime | 100% |  |

## baseline_snapshots

`baseline_snapshots.csv` · 887 rows. The t0 line: each property frozen on a capture date (2026-07-13 or 2026-07-22). `property_id` + `captured_on` identify a row; the other 28 columns are the frozen fields. See README §4b.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `property_id` | bigint | 100% | → `properties.id`. |
| `captured_on` | date | 100% | Capture date: 2026-07-13 or 2026-07-22. |
| `active_permit_count` | integer | 100% |  |
| `assessed_value` | integer | 82% |  |
| `avm_estimate` | integer | **blank** |  |
| `building_condition` | string | **blank** |  |
| `captured_at` | datetime | 100% | Capture timestamp. Not a frozen field. |
| `cdbg_investment_total` | integer | 100% |  |
| `city_owned` | boolean | 100% |  |
| `dwelling_units` | integer | <1% |  |
| `fair_market_rent_2br` | integer | 43% |  |
| `ground_rent` | integer | <1% | Blank or 0 in every row. |
| `has_active_business` | boolean | 82% |  |
| `hmda_denial_rate` | float | 62% |  |
| `hmda_loan_count` | integer | 62% |  |
| `hmda_median_value` | integer | 62% |  |
| `incident_count` | integer | 100% | Documentation depth at capture time. |
| `last_sale_date` | date | 82% |  |
| `last_sale_price` | integer | 82% |  |
| `market_median_sale_price` | integer | **blank** |  |
| `market_typology` | string | 34% |  |
| `owner_name` | string | 82% |  |
| `owner_type` | string | 27% |  |
| `public_investment_total` | integer | **all 0** |  |
| `receivership_status` | string | <1% |  |
| `registered_ip_count` | integer | 100% | Registered IP matched to the property at capture time. |
| `sale_count` | integer | **all 0** |  |
| `tax_certificate_active` | boolean | 100% |  |
| `vacancy_indicator` | boolean | 30% |  |
| `vacant_notice_status` | string | **blank** |  |
| `violations_12mo_count` | integer | 100% |  |
