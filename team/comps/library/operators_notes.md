# Operator revenue benchmarks for Greenmount Ave, Waverly (operators.csv)

Researched 2026-10-20. 45 rows in `operators.csv` (O-001 to O-045): 2 waverly, 18 baltimore_corridor, 25 other_city, 0 national. Every format except housing has at least 2 rows. Every figure was opened by the researcher, and the URL is in the row. Rows already in `team/comps/comps.csv` and `comps_alternates.csv` (Emma's Tea Spot, Square Cafe, Georgie's, Second Chance, Community Forklift and others) were not repeated. The NDA restaurant at 2731 Greenmount Ave is not used anywhere.

## Conventions used in the CSV (read before using the numbers)

- **Form C rows (private businesses)**: revenue is from the SEC Form C cover (`primary_doc.xml`, fields `revenueMostRecentFiscalYear` / `revenuePriorFiscalYear`) or from the campaign page or offering PDF filed with it. Many covers do not name the fiscal year. Where the year is inferred from the filing date, `revenue_year` says "(inferred)". Where the year cannot be inferred safely (filed in January to March), it says "not stated". All are owner-certified, unaudited figures. "Projected rent" figures from Mainvest pro formas are mentioned in the notes column only. They are **not** put in `rent_paid_usd_per_yr`.
- **990 rows (nonprofits)**: `annual_revenue_usd` is **earned revenue**, so it can be compared with private-business sales. It is program service revenue (Part VIII line 2), plus gross real-estate rents and gross sales of inventory where these exist. When lines are summed, `figure_type` = calculated and the notes show the arithmetic. Total revenue (which includes grants) is always given in the notes. One exception: The Book Thing (O-016) shows **total revenue**, because it has no earned revenue (books are given away). The ProPublica API does not expose the 990 occupancy (rent) line, so no 990 row has rent paid.
- **Organisation-level 990s**: BARCO/Motor House (O-010), Rebuild/Stony Island (O-024), MACC/The Commons (O-025) and ARCH/Anacostia Arts Center (O-026) cover more than the one building. They have no revenue per sq ft.
- **Revenue per sq ft** is computed only where a source states both the revenue and the floor area (6 rows: O-003, O-006, O-009, O-011, O-021, O-022). Creative Alliance's area is itself calculated from stated dimensions (85 x 150 ft).
- `evidence_quote` for XML or JSON sources quotes the field name and value. For tables, it quotes the cell values.

## Results by format (revenue = most recent full-year figure in the row)

| Format | Rows | Revenue range (USD/yr) | Revenue per sq ft | Notes |
|---|---|---|---|---|
| cafe | O-002, O-003, O-004, O-021, O-023, O-028 | $478K (Cafe Reconcile, earned, 2023) to $2.45M (Maketto 2019); Driftwood Oven $1.42M (2019); Red Emma's >$1M (c.2014) | Maketto $409 (2019) and $247 (2020); Red Emma's at least $200 | Red Emma's previous rent was at least $180K/yr (O-004). No sq ft for Cafe Reconcile or Driftwood. |
| counter | O-001, O-008, O-031 | $70K (Remember When, half-year 2017) to $321K (My Mama's Vegan, 2021); Juice On The Go $142K | none | No floor areas disclosed. |
| foodmaker | O-005, O-007, O-044 | $132K (Southeastern Roastery 2022) and $178K (B'More Made) to $4.03M (Jenny Lee, mostly wholesale, upper bound) | none | |
| shop | O-017, O-027, O-029, O-035 | $180K (Expect Lace) to $279K (a Fells Point fair-trade shop, 2024; $339K-$560K in earlier years); Brambler $226K | Anacostia Arts Center suite asking rent $33.58/sq ft/yr (500 sq ft, $1,399/mo, stated as 50% below market) | |
| showroom | O-032, O-040 | $1.87M (Construction Junction, earned) to $2.16M (Philly AIDS Thrift gross sales) | none | Both nonprofit reuse/thrift stores. |
| bike | O-013, O-037 | $77K (Velocipede, volunteer, program revenue) to $1.27M (Salem Cycle 2020; $627K in 2019, may include a second shop) | none | Weak tier: no staffed independent shop on a case-library corridor found. |
| services | O-033, O-041 | $337K (StyleBar FY21) to $590K (Twelve27, FY2018 inferred) | none | Both in affluent or downtown locations. |
| fitness | O-036, O-042, O-043 | $168K (boxing gym, N 2nd St Philadelphia) to $325K (Toolbox Pilates FY21); innerglow yoga $268K-$345K | none | Toolbox and innerglow each have a second site. |
| studio | O-010, O-024, O-026, O-034, O-038, O-039 | $57K (Ubuntu Fine Art 2022) and $143K (Playground Detroit 2023) for private galleries; $84K-$1.08M earned for nonprofit arts centres (ARCH $84K, Rebuild $237K, Hyde Park Art Center $638K, BARCO $1.08M) | none (org-level) | |
| venue | O-009, O-018, O-019, O-022 | $104K (Theatre Project) and $213K (Baltimore Improv Group) to $620K (Creative Alliance) and $995K (Atlas) earned | Creative Alliance $48.66; Atlas $16.58 | Earned revenue covers only 21-36% of total revenue at Creative Alliance and Atlas; the rest is grants. |
| office | O-006, O-045 | $149K (SENO gross rents 2023, provenance caveat) to $379K (Cube Cowork 2022) | Cube Cowork $25.27 (timing caveat) | Cube's Form C cover gives a conflicting $192K. |
| workshop | O-011, O-012, O-015, O-030 | $343K (Station North Tool Library 2024) to $1.07M (Pittsburgh Glass Center); Open Works $858K; Clayworks $852K | Open Works $25.25 | |
| community | O-014, O-016, O-020, O-025 | Earned $47K (Village Learning Place) to $354K (Paul's Place); The Commons $254K; Book Thing total $190K | none | Total budgets run $0.19M-$2.4M, mostly grants. |

Takeaways:
- Small private storefront formats (counter, shop, studio-gallery, services, fitness) disclosed **$57K-$590K**, mostly $140K-$340K.
- Only sit-down food (Maketto, Driftwood, Red Emma's) and large reuse showrooms passed $1M.
- Revenue per sq ft splits clearly: food and beverage **$200-$409**, against nonprofit venues, workshops and coworking at **$17-$49**.

## Examples most like Waverly and why

Waverly benchmark, from the team's case library: a 0.4-mile National Register main street of early 20th-century rowhouse storefronts, majority-Black, with income below the city median of $62,177. It has concentrated ownership and many small empty shops.

1. **My Mama's Vegan, 2915 Greenmount (O-001)**. Same block group and same building stock. It shows what a small carryout earned there: $261K (2020) to $321K (2021). Current status at Greenmount is unclear.
2. **Red Emma's, 3128 Greenmount and 415 E 32nd St (O-002 to O-004)**. A worker co-op that bought two Waverly buildings (one from the 1920s). Its earlier 5,000 sq ft space passed $1M in sales, at least $200/sq ft. Buying the buildings roughly halved occupancy cost against a rent of over $15K/month. This is the clearest evidence that a destination cafe-bookstore can work on this street. Its Waverly revenue is not public.
3. **Harford Rd, Hamilton-Lauraville: B'More Made with Pride (O-005) and Cube Cowork (O-006)**. A streetcar-era strip of small 500-1,500 sq ft shops (case library). Like Waverly, it is a city Main Street of modest income. They show a kitchen/cafe at $103K-$178K and a coworking space at about $379K.
4. **Nearby north-central Baltimore nonprofits: Book Thing (O-016, near Waverly, owner-occupied warehouse), Velocipede (O-013, 22nd St), Village Learning Place (O-014, St Paul St), Open Works (O-011, 1400 Greenmount)**. These are the same submarket and show the community/workshop end of the range. Open Works earns about $25/sq ft but relies on $1.6M a year in grants.
5. **Germantown Ave, Philadelphia: Ubuntu Fine Art (O-034)**. A historic, majority-Black, lower-income corridor (case library: Germantown Ave). Its small gallery revenue of $26K-$57K is a realistic floor for a studio-gallery storefront.
6. **O.C. Haley, New Orleans: Cafe Reconcile (O-023)** and **Mack Ave, Detroit: The Commons (O-025)**. Both are low-income corridors in the library, with 1800s-1920s buildings and a nonprofit-anchored reuse. Earned revenue is $254K-$478K.
7. **Chartiers Ave mill-town strip: Remember When Ice Cream (O-031)**. A 1960 one-storey ice cream shop in a working-class area, at about $70K for half a year.

Less like Waverly (use as upper bounds): Maketto and Atlas on H Street NE (the corridor has gentrified; Maketto is 6,000 sq ft); the Dupont Circle salon and Pilates studio; Lawrenceville's Driftwood Oven and Brambler (Butler St is now high-rent); Salem MA and Mashpee MA; Jenny Lee (wholesale).

## Gaps

- **Floor area** was disclosed for only 10 rows; no Form C storefront except Maketto gave square footage. **Rent paid** is known only for Red Emma's (at least $180K/yr, Mount Vernon). The 990 occupancy line was not available through the API.
- **Corridors with no revenue found**: East Passyunk, Hampden (the Bisnow piece on The Wine Source sale gives only a 9,640 sq ft building), Livernois/Live6 (Whiff & Nibble on W McNichols reported $2,332, too small to use), Belair-Edison and Highlandtown private shops.
- **Library cases with no revenue**:
  - Capitol Theatre: Freshwater 2017 gives only about 50,000 patrons a year.
  - Cafe Hon, Red Canoe, R. House, Carver, St Roch: not searched in depth.
  - Kelly Strayhorn Theater: EIN not found on ProPublica.
  - Anacostia Playhouse: no filings.
  - Seminary Co-op: the DNAinfo 2017 article gives only growth ($144K = 5%); revenue was not back-calculated.
- **Waverly pipeline with no revenue yet**: Zehbras CrossFit gym at 3313 Greenmount (Form C 2024: in buildout, $0 revenue). Jerk Taco (2958 and 3328 Greenmount) and Kora Lee's (Banner 2024-06-14) have no figures.
- **Excluded after checking**:
  - Jibe Cycling ($1.21M): multi-city.
  - Junto Bicycle Works ($66K): business model unverified.
  - Legitfit, Hiatus Cheesecake, Death Comes Lifting: no storefront.
  - Modtempo: e-commerce.
  - Neighborhood Bike Works: grants only.
  - Single Carrot Theatre: no fixed venue now.
  - Forze gym, Middle River: suburban strip.
  - BizQuest yoga-studio listings: pages blocked.
- **Weak tiers**: bike (no staffed corridor shop with revenue), services and fitness (mostly affluent DC or New England sites).
- **Still-operating status** was confirmed only for Velocipede (Banner 2025-09-04) and the Book Thing. The rest are "unknown" with the latest filing year given.
- The SENO row (O-045) depends on the researcher's identification of SENO as Propeller.
