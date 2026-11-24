# Current tenants on the Greenmount frontage (draft; last changed November 2026)

Who occupies each storefront today, for the 79 focus-area properties on the seven Greenmount frontage block
sides (65 and 67 to 72). Saturation has to be measured against today's business mix, so this list is an input
to the optimiser. One row per `property_id`; a building with several storefronts lists them in `tenant_name`,
separated by " ; ".

**Where it stands** (filled in from `team/NUMBERS.md`). Ten of the 79 records are merged into a neighbouring parcel,
which leaves <!--=frontage.parcels-->69<!--/--> parcels: <!--=frontage.storefronts-->62<!--/--> storefronts, of which <!--=frontage.empty-->24<!--/--> are empty
and <!--=frontage.in_use-->38<!--/--> in use, and <!--=frontage.houses-->7<!--/--> houses with no shop front. A person has entered or checked
<!--=human_checks.tenant_rows_entered_or_checked_by_a_person-->23<!--/--> of the <!--=human_checks.tenant_rows-->79<!--/--> rows (the Street View
check); the rest were entered with AI assistance. Of the <!--=frontage.in_use-->38<!--/--> storefronts in use,
<!--=frontage.in_use_named_from_a_search_listing_only-->15<!--/--> rest on a search listing for the name of the business: the
sponsor's audit settles whether they are empty, and nobody has yet confirmed what trades there.

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

## Street View update (November 2026)

The 28 rows that were `unknown` were checked in Google Street View (September 2026 imagery) and against the
sponsor's walk photos of 3 November; `team/evidence/streetview_check_2026-11.csv` has the record and
`apply_streetview_2026-11.py` writes it into this file. 19 are settled: 8 occupied (a church on two numbers, a clinic, four
shops on five numbers), 6 houses, 5 empty (vacant or for lease, three of them boarded). 9 were left `unknown` and
marked `needs_street_view_check = walk`; the sponsor's audit below settled four of them. Houses carry no name.

## Sponsor's storefront audit (November 2026)

On 16 November 2026 the sponsor checked the list of empty storefronts against its own audit (records, September
2026 Street View, walks on 30 October and 3 November). `apply_sponsor_audit_2026-11.py` writes the differences
into this file: 13 addresses become empty (2920, 2930, 3010, 3011, 3015, 3019, 3029, 3038, 3111, 3120, 3122,
3200, 3224), 3000 is open, and 2936 is a vacant house, not a storefront, so the plan leaves it out. The main
cause was Yelp: "Updated <month>" on a page is when the page was refreshed, not proof that the shop is open.
On 17 November the sponsor added 2942 and confirmed 3211 (listed for lease), so 24 of the 69 frontage parcels are
empty on the audit and the explorer plans 24. The list has moved twice in two days and may move again.

## What is still open

- 5 rows are still `unknown` and marked `walk`: 2902, 3013, 3032, 3103 and 3124. Each is an export record that the
  sponsor lists as merged into a neighbouring parcel, so none of the <!--=frontage.parcels-->69<!--/--> parcels is `unknown`. A
  visit would settle whether a separate storefront exists at each.
- A second person has not checked any row. The sponsor's review of 17 November 2026 found that a search listing
  alone does not show a business is open; the rows that rest on one are listed by `source_type = search snippet`.
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
