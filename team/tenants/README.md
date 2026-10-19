# Current tenants on the Greenmount frontage (draft, October 2026)

Who occupies each storefront today, for the 79 focus-area properties on the seven Greenmount frontage block
sides (65 and 67 to 72). Saturation has to be measured against today's business mix, so this list is an input
to the optimiser. One row per `property_id`; a building with several storefronts lists them in `tenant_name`,
separated by " ; ".

## Columns

| Column | Meaning |
|---|---|
| `status` | `occupied`, `vacant`, `for lease` or `unknown`. Never a guess: no source from 2024 or later means `unknown`. |
| `tenant_name`, `business_type` | Business type uses the team's use-category list (food & drink, retail goods, personal services, automotive, entertainment & assembly, institutional & religious, production & light industry, office, residential, vacant). |
| `evidence_date` | The date the source shows (article, listing update, review, licence renewal). |
| `source_type` | listing, news, business website, directory, licence data, search snippet, map listing. |
| `google_maps_2026_10_18` | What Google Maps showed for the address on 18 October 2026: the businesses it lists at that address, or "no business listed". A missing listing is weak evidence only; some operating businesses are not attached to their address on Google. |
| `confidence` | `high`: a dated 2025 or 2026 source names the business at that address, or two independent current sources agree (for example a 2026 Yelp update plus a Google Maps listing with opening hours). `medium`: 2024, undated, or one current map listing. `low`: one weak source. |
| `needs_street_view_check` | `yes` unless confidence is high. |

## What is still open

- Rows marked `unknown` or `low`, most of them on the 2900 block. These need Google Street View and the
  sponsor's walk-through.
- Address conflicts are written out in `notes`, for example Goodwill (listed at 3101, parcel 3031), Raven
  Grocery (listed at 3215, assigned to 3213), and 3224 (a 2025 permit for a restaurant conversion, but a clothing
  store is listed there).
- The Waverly Main Street directory is undated and partly out of date. Names found only there are in `notes`,
  not in `tenant_name`.

## Sources and rules

News (Baltimore Banner, Baltimore Fishbowl), sale and lease listings, business websites, the city's liquor
licence records, Google Maps place listings and search-result snippets (Yelp pages refuse automated access).
SDAT and MDLandRec were not scraped. Names of private individuals are left out; businesses, companies and
public bodies are named.

## AI use

Drafted with Claude on 16 to 18 October 2026 (`entered_by` on every row). A team member checks the rows against
their sources and Street View before merge.

Checked by: ____________________ Date: __________
