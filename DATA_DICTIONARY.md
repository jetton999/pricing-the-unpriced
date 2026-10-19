# Data Dictionary

Every column of every CSV, in file order. **Filled** is the share of rows with a value.
**blank** means empty in every row. **all 0** and **always `x`** mean one value in every row:
either a placeholder (`0`, `false`) or an area-wide figure, identical for every property. Either
way the column cannot tell one property from another. Do not read a 0 there as "none".
`python3 verify_claims.py` checks these markers on `properties.csv` against the data.

Joins: `property_incidents.property_id` → `properties.id`; `incident_subjects` links
`property_incidents` to `subjects`; `incident_links` links incidents to each other;
`registered_ips`, `grant_program_matches`, `storefront_assessments`, and `property_images` hang off
`properties.id`. `baseline_snapshots` keeps the September ids: re-key it through
`property_id_crosswalk` (`old_id` → `new_id`) first.

## properties

`properties.csv` · 699 rows. One row per property: Greenmount Ave and about one block either side (README §4, "How the study area was cut").

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `address` | string | 100% | House format: mixed case, no ZIP, ending `, Baltimore, MD` (`608 E 30th St, Baltimore, MD`). Five named places have no house number and keep their own names. |
| `block_side_id` | bigint | 66% | One side of one block. The default assemblage unit (59 values). |
| `created_at` | datetime | 100% |  |
| `latitude` | decimal | 96% |  |
| `longitude` | decimal | 96% |  |
| `owner_name` | string | 96% |  |
| `owner_type` | string | 17% | Values: `unknown`, `city`, `private_owner`; blank in most rows. |
| `updated_at` | datetime | 100% |  |
| `blocklot` | string | 95% |  |
| `assessed_value` | integer | 95% | Administrative outcome, not a market price. |
| `vacancy_indicator` | boolean | 28% |  |
| `year_built` | integer | 96% | `0` means unknown (93 rows). |
| `zoning_code` | string | 95% | `C-*` codes are commercial. Earlier exports had trailing spaces; `.str.strip()` is harmless. |
| `last_sale_price` | integer | 96% | 140 rows are $0 transfers. Portfolio sales repeat the whole deal price on every parcel. 701 Exeter Hall Ave ($19,000,000) is a portfolio sale whose other parcel is outside the study area. |
| `last_sale_date` | date | 96% |  |
| `lot_polygon` | jsonb | 96% |  |
| `building_polygons` | jsonb | 92% |  |
| `city_owned` | boolean | 100% |  |
| `alias` | string | 5% |  |
| `has_active_business` | boolean | 96% |  |
| `opportunity_zone` | boolean | **always `false`** |  |
| `flood_zone` | string | **blank** |  |
| `historic_district` | string | 39% |  |
| `enterprise_zone` | boolean | 100% |  |
| `incidents_12mo_count` | integer | 100% |  |
| `violations_12mo_count` | integer | 100% |  |
| `census_tract` | string | 95% |  |
| `environmental_flag` | boolean | 100% |  |
| `fair_market_rent_2br` | integer | **always `2006`** | HUD residential FMR for the ZIP; an order-of-magnitude anchor only. |
| `median_household_income` | integer | 83% |  |
| `vacant_notice_status` | string | 6% |  |
| `active_permit_count` | integer | 100% |  |
| `receivership_status` | string | 7% |  |
| `roof_damage_risk` | float | 2% |  |
| `tax_certificate_active` | boolean | 100% |  |
| `market_typology` | string | 96% | Market typology category (B–G in this export). |
| `crimes_12mo_count` | integer | 100% |  |
| `cdbg_eligible` | boolean | 100% |  |
| `inspire_eligible` | boolean | **always `false`** |  |
| `arts_district` | boolean | **always `false`** |  |
| `healthy_neighborhood` | boolean | 100% |  |
| `lincs_corridor` | boolean | **always `false`** |  |
| `main_street_district` | boolean | 100% |  |
| `niif_area` | boolean | 100% |  |
| `sustainable_community` | boolean | 100% |  |
| `food_desert` | boolean | 100% |  |
| `public_investment_total` | integer | **all 0** |  |
| `walkability_index` | float | 95% |  |
| `transit_distance_m` | integer | 95% |  |
| `jobs_transit_45min` | integer | 95% |  |
| `lihtc_nearby_count` | integer | 100% |  |
| `hud_reo` | boolean | **always `false`** |  |
| `qualified_census_tract` | boolean | 100% |  |
| `difficult_development_area` | boolean | **always `false`** |  |
| `cdbg_investment_total` | integer | 100% |  |
| `hmda_loan_count` | integer | 95% |  |
| `hmda_median_value` | integer | 95% |  |
| `hmda_denial_rate` | float | 95% |  |
| `hpi_value` | float | 51% |  |
| `hpi_yoy_change` | float | 51% |  |
| `ground_rent` | integer | 95% |  |
| `dwelling_units` | integer | 95% |  |
| `structure_sqft` | integer | 95% | `0` means unknown (237 rows). |
| `building_condition` | string | **blank** |  |
| `building_quality` | string | **blank** |  |
| `num_stories` | integer | **blank** |  |
| `has_basement` | boolean | **always `false`** |  |
| `has_central_ac` | boolean | **always `false`** |  |
| `market_median_sale_price` | integer | **always `240000`** |  |
| `market_median_dom` | integer | **always `59`** |  |
| `market_inventory` | integer | **always `203`** |  |
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
| `zip_code` | string | **always `21218`** | 21218 for every row. |
| `block_plat_url` | string | 95% |  |
| `tax_certificate_status` | string | 14% |  |
| `tax_certificate_sold_on` | date | 14% |  |
| `receivership_filed_on` | date | 3% |  |
| `tax_sale_years` | array | 100% | Added October 2026. Years the property went to a City tax sale, as a Postgres array (`{2021,2024}`). `{}` (none) in 544 rows; 155 have at least one year. Detail is in the `baltimore:tax_sale_history` incidents. |
| `city_since_years` | array | **always `{}`** | Added October 2026. Empty in every row. |
| `vacant_lot` | boolean | 100% | Added October 2026. `true` for 58 rows. Corridor's parcel flag; it disagrees with `storefront_assessments.status` = `vacant_lot` for 13 properties. |
| `absorbed_addresses` | jsonb | 100% | Added October 2026. JSON array of the addresses this parcel absorbed when Corridor merged them; `[]` in 620 rows. 79 parcels absorbed 184 addresses. The retired ids are in `property_id_crosswalk.csv`. |

## property_incidents

`property_incidents.csv` · 17,387 rows. The claim layer: one dated event at one property. Split it into two layers before any analysis. A `source` starting with `baltimore:`, or equal to `sdat_assessments` or `sdat:owner`, is **administrative** (9,496 rows); everything else is **curated** (7,891). See README §1.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_id` | bigint | 100% | → `properties.id`. |
| `source` | string | 100% | Decides the layer (see above). `stjohns_interments` is curated. |
| `source_id` | bigint | 100% | ID of the record in its source system. |
| `category` | string | 100% | 52 values: `complaint`, `permit`, `sale`, `crime`, `title`, `history`, `news`, `tax`, `interment`, `ownership`, … |
| `occurred_at` | datetime | 100% | Start of the event. Read with `date_precision`. |
| `summary` | string | 100% | Human-readable description of the claim. |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `created_at` | datetime | 100% |  |
| `evidence_status` | string | 32% | `verified` / `probable` / `possible` / `contested` / `refuted`; blank = ungraded. |
| `occurred_at_end` | datetime | 2% | End of a range, when `date_precision` is `range`. |
| `date_precision` | string | 36% | `exact` / `year` / `range` / `circa` / `decade` / `unknown`; blank = unset. |
| `sensitivity` | string | <1% | `trauma`, `personal_rights`, `displacement`, `commercialization`. Never drop these rows silently (LICENSE.md). |
| `rights` | string | 4% | `public` where set. |

## subjects

`subjects.csv` · 3,093 rows. People, businesses, organizations, families, and other named entities that appear in incidents.

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

`incident_subjects.csv` · 5,451 rows. Edges between a subject and an incident: who did what, where. Join `property_incident_id` → `property_incidents.id` → `property_id` to reach the property.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_incident_id` | bigint | 100% | → `property_incidents.id`. |
| `subject_id` | bigint | 100% | → `subjects.id`. |
| `relationship` | string | 100% | 299 distinct values; the common ones are `owned`, `operated_at`, `sold`, `interred_at`, `purchased`, `lived_at`, …  `operated_at` links people and organizations too, not just businesses. |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## incident_links

`incident_links.csv` · 1,868 rows. Edges between two incidents, including where claims disagree.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_incident_id` | bigint | 100% | → `property_incidents.id`. |
| `related_incident_id` | bigint | 100% | → `property_incidents.id`. |
| `link_type` | string | 100% | `related`, `supports`, `duplicates`, `contradicts`. |
| `note` | text | 11% |  |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## registered_ips

`registered_ips.csv` · 37 rows. Trademarks, patents, and entity registrations, each with an address of record and a match confidence.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `address_of_record` | string | 100% |  |
| `created_at` | datetime | 100% |  |
| `data` | jsonb | 100% | JSON payload; source-specific detail. |
| `filing_date` | date | 73% |  |
| `grant_date` | date | 49% |  |
| `ip_type` | string | 100% | `trademark` (23), `patent` (11), `entity` (3). Patents have a city-level address only. |
| `match_confidence` | string | 100% | `high`, `medium`, `low`, `inferred`: how sure the match is. `inferred` patents are unconfirmed surname leads. |
| `number` | string | 100% |  |
| `owner_name` | string | 100% |  |
| `property_id` | bigint | 43% | → `properties.id`; set for 16 of 37 rows. |
| `source` | string | 100% |  |
| `status` | string | 100% | `registered`, `abandoned`, `expired`, `pending`, `cancelled`, `forfeited`. |
| `title` | string | 100% |  |
| `updated_at` | datetime | 100% |  |

## property_parcels

`property_parcels.csv` · 850 rows. The city parcel roll for the study area's blocks. The linkage layer, not the research set.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `source` | string | **always `baltimore:parcels`** |  |
| `source_id` | string | 100% |  |
| `blocklot` | string | 100% |  |
| `address` | string | 100% |  |
| `normalized_address` | string | 100% |  |
| `sqft` | integer | 99% |  |
| `land_use` | string | 100% |  |
| `owner` | string | 100% |  |
| `matched_property_id` | bigint | 25% | → `properties.id`; set for 209 of 850 rows. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |
| `lot_sqft` | integer | 100% |  |

## grant_program_matches

`grant_program_matches.csv` · 5,319 rows. Property-to-program eligibility matches behind the live "Improve Your Property" tool. Carried forward unchanged from September; every `property_id` is a current property.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_id` | bigint | 100% | → `properties.id`. |
| `program_key` | string | 100% |  |
| `program_name` | string | 100% |  |
| `category` | string | 100% |  |
| `amount_cap` | string | 39% |  |
| `summary` | text | 100% |  |
| `matched_reason` | string | 100% | Why the property qualified. |
| `created_at` | datetime | 100% |  |
| `updated_at` | datetime | 100% |  |

## neighborhoods

`neighborhoods.csv` · 5 rows. Names only: `bounds` is empty in this export, so there is no neighborhood geometry.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `bounds` | jsonb | **blank** | Empty in every row. |
| `created_at` | datetime | 100% |  |
| `name` | string | 100% |  |
| `updated_at` | datetime | 100% |  |

## baseline_snapshots

`baseline_snapshots.csv` · 883 rows. The t0 line: each property frozen on a capture date (2026-07-13 or 2026-07-22). Frozen byte for byte, so it keeps the September ids. `property_id` + `captured_on` identify a row; the other 28 columns are the frozen fields. See README §4b.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `property_id` | bigint | 100% | September id. → `properties.id` directly for 779 rows; the other 104 join through `property_id_crosswalk` first. |
| `captured_on` | date | 100% | Capture date: 2026-07-13 or 2026-07-22. |
| `active_permit_count` | integer | 100% |  |
| `assessed_value` | integer | 81% |  |
| `avm_estimate` | integer | **blank** |  |
| `building_condition` | string | **blank** |  |
| `captured_at` | datetime | 100% | Capture timestamp. Not a frozen field. |
| `cdbg_investment_total` | integer | 100% |  |
| `city_owned` | boolean | 100% |  |
| `dwelling_units` | integer | <1% |  |
| `fair_market_rent_2br` | integer | 43% |  |
| `ground_rent` | integer | <1% | Blank or 0 in every row. |
| `has_active_business` | boolean | 82% |  |
| `hmda_denial_rate` | float | 61% |  |
| `hmda_loan_count` | integer | 61% |  |
| `hmda_median_value` | integer | 61% |  |
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

`archive_folders.csv` · 31 rows. The index of the Baltimore City Archives DHCD Waverly files (record group BRG48-43-10), one row per folder. See README §4c.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `item` | integer | 100% | Folder number, 1 to 31. Joins to `archive_scans.item`. |
| `reference` | string | 100% | The archive's reference, `BRG48-43-10-<item>`. |
| `title` | string | 100% | The folder title from the archive's delivery. |
| `scans` | integer | 100% | Rows in `archive_scans.csv` for this folder. |
| `pages` | integer | 100% | Distinct pages. Less than `scans` when a page is filed on several buildings. |
| `properties` | integer | 100% | Distinct buildings the folder's pages are filed on. |
| `first_year` | integer | 100% | Earliest `depicted_on` year in the folder. |
| `last_year` | integer | 100% | Latest `depicted_on` year in the folder. |

`archive_scans.csv` · 2,260 rows. One row per scanned page filed on a building: 1,692 distinct pages on 142 buildings. Exactly what the public City Archives viewer shows; the scans are links, not files. See README §4c.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | The image's id. Unique. |
| `property_id` | bigint | 100% | → `properties.id`. All 142 buildings join. |
| `address` | string | 100% | The building's address, house format. |
| `item` | integer | 100% | Folder number. → `archive_folders.item`. |
| `reference` | string | 100% | `BRG48-43-10-<item>`. |
| `folder_title` | string | 100% | The folder title. |
| `page` | integer | 100% | Page number within the folder, in the archive's order. `item` + `page` identify a page; a page can have several rows. |
| `category` | string | 100% | `document` (1,699), `plan` (241), `sketch` (234), `photo` (49), `ephemera` (37). |
| `subject` | string | 2% | Set for photos only: `streetscape`, `exterior`, `detail`. |
| `caption` | string | 100% | One line, written by a vision model or by hand. Not a transcription. |
| `depicted_on` | date | 100% | The date the page depicts, not the scan date. Read it with `depicted_precision`. |
| `depicted_precision` | string | 100% | `year` (1,022), `day` (905), `month` (239), `decade` (94). A `year` date is the first of January. |
| `depicted_address` | string | 7% | An address the page names, when one was read off it. |
| `scan_url` | string | 100% | A 1,600 px JPEG of the page. Public, no login. |
| `original_url` | string | 100% | The full-size image. Public, no login. |

`matterport_tours.csv` · 13 rows. The sponsor's public, active Matterport 3D tours: 13 tours of 12 buildings, scanned April to August 2026. The scans are links, not files. See README §4d.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | The tour's id in the sponsor's database. Unique. |
| `property_id` | bigint | 100% | → `properties.id`. Every row joins. |
| `address` | string | 100% | The building's address, house format; equal to `properties.address`. |
| `label` | string | 31% | A note on the tour, when it needs one: `auxiliary room`, `Aug 2026 rescan`, or the Matterport title when it differs from the building. |
| `scan_date` | date | 100% | The day the space was scanned (Baltimore time). |
| `floors` | integer | 100% | Floors captured. |
| `rooms` | integer | 100% | Rooms Matterport detected. |
| `is_primary` | boolean | 100% | `true` for the building's main tour. One per building. |
| `model_id` | string | 100% | The Matterport model id; the part after `?m=` in the link. |
| `share_url` | string | 100% | Open it to walk the building. Public, no login. |

`property_images.csv` · 3,694 rows. Images filed on properties: scans of records, and PI.KL Studio's 2026 building-conditions survey photos. 3,090 image files on 348 properties. One image filed on several properties, or listed under two ids, is one file and several rows: count distinct `image_key`. The images are not in git; `python3 bin/fetch_images.py` downloads them. See README §4e.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. Unique. |
| `property_id` | bigint | 100% | → `properties.id`. Every row joins. |
| `category` | string | 100% | `photo` (1,873), `document` (1,807), `plan` (13), `ephemera` (1). |
| `subject` | string | 51% | Survey photos only: `interior` (873), `detail` (415), `roof` (368), `exterior` (111), `streetscape` (61), `alley` (39), `other` (6). |
| `caption` | string | 100% | Describes the image. Not a transcription. |
| `depicted_on` | date | 45% | The date the record depicts, not the scan date. Read it with `depicted_precision`. 1742 to 2023. Blank for the 2026 survey photos. |
| `depicted_precision` | string | 45% | `day` (885), `year` (765), `month` (4). A `year` date is the first of January. |
| `depicted_source` | string | 49% | `manual` (1,817 rows, every scan of a record) or `classifier` (1). Blank for the survey photos. |
| `depicted_address` | string | 4% | Survey photos only: the address the photo was taken at, when recorded (150 rows). |
| `folder` | string | 100% | `deeds-and-title-chain` (1,054 rows: deeds, mortgages, leases, liens, City building-permit cards), `bca-brg4-1` (655: City tax ledgers and assessment rolls, 1896 to 1915, Baltimore City Archives), `loc-sanborn` (4: 1915 Sanborn sheets), `passano-oneill` (104: Passano-O'Neill file cards, 1802 to 1938, Maryland Center for History and Culture; reproduction cleared), `pikl-greenmount` (1,877: PI.KL Studio's 2026 building-conditions survey for the Maryland Historical Trust; 68 photos were held back after review). |
| `image_key` | string | 100% | `img/<sha256>.jpg`. Append it to the URL in `images_base_url.txt`. Re-encoded JPEG, metadata stripped. |

`storefront_assessments.csv` · 264 rows. The sponsor's street-level assessment of what occupies each ground floor in 2026, one row per property. See README §4f.

| Column | Type | Filled | Notes |
|---|---|---|---|
| `id` | bigint | 100% | Primary key. |
| `property_id` | bigint | 100% | → `properties.id`. One row per property; every row joins. |
| `status` | string | 100% | `open_active` (87), `residential` (56), `vacant_storefront` (49), `vacant_lot` (39), `institution` (19), `office_industrial` (11), `listed_likely_dead` (2), `needs_eyes` (1). |
| `confidence` | string | 100% | `high` (142), `medium` (117), `low` (5). |
| `summary` | text | 100% | A few sentences on what is there and why the status was chosen. |
| `evidence` | jsonb | 100% | JSON array of findings (1,428 in all), each with `source`, `as_of`, `finding`, and usually `url`. Sources include `google`, `photos` (Street View), `zoning`, `city_vacancy`, `listing`, `news`. Findings quote business phone numbers from public listings and shop signs. |
| `assessed_on` | date | **always `2026-10-07`** | When the assessment was made. |
| `observed_on` | date | **blank** |  |

`property_id_crosswalk.csv` · 52 rows. Every September property id the October 2026 refresh retired, each mapped to the parcel that absorbed it (24 surviving parcels).

| Column | Type | Filled | Notes |
|---|---|---|---|
| `old_id` | bigint | 100% | The retired September id. Not in `properties.csv`; may appear in `baseline_snapshots.csv` and in team files. |
| `new_id` | bigint | 100% | → `properties.id`. The surviving parcel. |
| `old_address` | string | 100% | The retired property's address. |
| `new_address` | string | 100% | The surviving parcel's address. |
| `reason` | string | 100% | Why the id was mapped there, in prose. In every row the old address is in the survivor's `absorbed_addresses`. |
