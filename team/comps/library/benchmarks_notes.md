# Revenue and occupancy-cost benchmarks for small independent businesses, by format (Greenmount Ave, Waverly comps engine)

All figures below are in `benchmarks.csv` (row IDs in brackets). Accessed 2026-10-20. Housing is out of scope. "Inference" items are my arithmetic or judgment built from cited rows; they are not in the CSV and are flagged as such.

**How an engine can use these.** Affordable occupancy cost per sq ft per year = sales per sq ft x sustainable occupancy share. Annual revenue range = sales per sq ft x the format's floor area. Census receipts per establishment are a cross-check on that revenue range. They are employer-only averages that include chains, so they sit high for a new independent on Greenmount.

## Cross-cutting: sources, definitions and access limits

### Takeaway
The firmest numbers are the 2022 Economic Census figures for Baltimore City and the US (receipts, employees and payroll per establishment), plus the National Restaurant Association's 2024 medians for restaurant occupancy cost (5.2-6.0% of sales). Sales per sq ft for independents is thin everywhere. It is solid only for bike shops (NBDA, 2013) and fitness studios (AFS, 2015). Restaurant and shop figures come from planning studies and rules of thumb.

### Cited Findings
- Economic Census 2022 figures came from the data.census.gov table API (tables EC2272BASIC, EC2244BASIC, EC2281BASIC, EC2271BASIC, EC2254BASIC, EC2251BASIC) for Baltimore city (GEO 0500000US24510) and the US. Receipts (RCPTOT) and payroll are in $1,000. I pulled the Baltimore sector 72/44/71/81 tables twice, with independent extractions, and the values matched. [Census EC2272BASIC Baltimore](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2272BASIC&g=050XX00US24510)
- Economic Census counts employer establishments only: chains and independents together, no nonemployers. Small Baltimore cells are suppressed (flag D): 459110 sporting goods/bike, 811490 repair, 512131 cinemas, 711110 theatre establishment count, 459920 art-dealer receipts, and payroll for 722515, 449110 and 711310. [Census EC2244BASIC Baltimore](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2244BASIC&g=050XX00US24510)
- Nonemployer Statistics 2022 for Baltimore city could be read only at sector level. Sector 81: 5,452 nonemployers, $131.0M receipts, about $24K each [B-119]. Sector 54: 5,997 nonemployers, about $48.9K each [B-170]. [Census NS2200NONEMP](https://data.census.gov/api/access/data/table?id=NONEMP2022.NS2200NONEMP&g=050XX00US24510)
- NRA's 2023 survey form defines occupancy costs as "Rent, taxes and property insurance". [NRA Restaurant Operations Survey 2023](https://restaurant.org/NRA/media/Research/Restaurant-Operations-Survey-2023.pdf) The Restaurant Business guideline adds CAM. [Restaurant Business](https://restaurantbusinessonline.com/advice-guy/how-figure-out-prime-cost-occupancy-percentages)
- A 2026 vendor blog could find no primary source for the common "6-10% rent-to-sales" restaurant rule: "No survey, no dataset, no trade association study, no filing". [Katalyst blog](https://www.katalystos.com/blog/restaurant-lease-negotiation)
- Local rent context, for whoever handles rent comps:
  - Southwest Baltimore commercial rents were $8.00-$16.20/sq ft (2014). [CLUE Group, SW Baltimore](https://swpbal.org/wp-content/uploads/2015/11/Southwest-Baltimore-retail-development-strategy-1.pdf)
  - Good-quality retail on West Baltimore Street rents for $10-15/sq ft, per a property owner. CoStar average asking retail rent was $15.24 (Q4 2020) and $20.16 (Q4 2021). [BAE, West Baltimore Street study, Sep 2022](https://static1.squarespace.com/static/63979ae6a2fa423bf9ce0e70/t/6397a57f4ef3a1514a6e1417/1670882688414/West+Baltimore+Street+Commercial+Corridor+Market+Study+and+Action+Plan.pdf)
- The Boulder study [B-014, B-068, B-089, B-100, B-051] quotes 2017 Census expense data for occupancy shares:
  - food services, about 9%
  - clothing, home furnishings and sporting goods/hobby stores, about 9%
  - food and general-merchandise stores, about 4%

  These are secondary citations. I could not open the primary Census tables. [Gruen Gruen + Associates for Boulder, 2019](https://bouldercolorado.gov/media/1262/download)

### Inferences
- Payroll as a share of receipts, calculated from Census [labour rows], understates full labour cost. It leaves out benefits, payroll taxes and owner pay. Industry labour shares (NRA 34-36.5%) run 2-12 points higher than the Census payroll-only shares.
- Census means include chains, and chains raise both revenue and sales per establishment. A new independent in a low-income corridor should sit below them. Use the means as upper-middle values, not midpoints.

### Gaps
- **2022 Annual Retail Trade Survey (ARTS).** This is the official primary source for retail gross margin by kind of business and for rent share (Detailed Operating Expenses). Its xlsx files are on www2.census.gov, which the fetch tool and the sandbox could not reach (robots/proxy block). [ARTS 2022 operating expenses page](https://www.census.gov/data/tables/2022/econ/arts/operating-expenses.html)
- **Single-unit vs multiunit firms (EC2200SIZESUMU).** This table would give receipts per establishment for independents alone. It exists, but it was too large to fetch, the NAICS filter failed, and api.census.gov now needs a key. [API group list](https://api.census.gov/data/2022/ecnsize/groups.html)
- **NAICS 311811 (on-site retail bakeries).** The manufacturing table's 140+ columns could not be aligned reliably, so the bakery value is left blank. I used 445291 as a proxy.
- **Nonemployer detail for 812111-812113 in Baltimore.** The page was rate-limited (HTTP 429) and not retried.
- **Paywalled or closed sources.** None were used:
  - full NRA Data Abstract tables (sales per sq ft, sales per seat)
  - ULI *Dollars & Cents of Shopping Centers*
  - NBDA 2024 Cost of Doing Business
  - recent ABACUS
  - IHRSA/HFA *Profiles of Success*
  - IBISWorld, RMA, BizMiner
- **SEC 10-K MD&A sections.** The fetch truncated them at about 100K characters, so chain cost lines came from earnings-release exhibits instead.

## cafe (sit-down cafe or restaurant, 800-4,000 sq ft)

### Takeaway
I would use sales of $200 / $400 / $650 per sq ft (low / mid / high), an occupancy share of 6.0% (typical urban) with a 10% ceiling, payroll and benefits of about 36.5%, and pre-tax margin of about 3%.

### Cited Findings
- **NRA occupancy, fullservice, 2024:** median 5.7%; urban/city-centre 6.0% [B-007, B-008]. [NRA](https://restaurant.org/research-and-media/research/restaurant-economic-insights/analysis-commentary/restaurant-occupancy-costs-were-more-than-5-of-sales-in-2024/)
- **NRA 2025 Abstract, fullservice:** payroll and benefits median 36.5%; pre-tax income median 2.8% [B-009, B-010]. [NRA release](https://restaurant.org/research-and-media/media/press-releases/new-resource-from-national-restaurant-association-provides-insights-into-operational-realities/)
- **Rules of thumb:**
  - Withum (SBA lending context): rent 6-10% and labour 25-35% [B-011, B-012]. [Withum](https://www.withum.com/resources/whats-on-the-menu-in-restaurant-valuations-a-recipe-for-managing-sba-lending-risk/)
  - Restaurant Business: occupancy should not exceed 8-10% [B-013]. [Restaurant Business](https://restaurantbusinessonline.com/advice-guy/how-figure-out-prime-cost-occupancy-percentages)
  - Webinar deck: 10% maximum, ideally 6-7% [B-018]. [2021 Restaurant Benchmarks](https://business.brucecounty.on.ca/hubfs/Fall%202021%20Webinars/Oct%209th-%202021%20Restaurant%20Benchmarks.pdf)
- **Sales per sq ft:**
  - Webinar deck viability tiers [B-019]: under $200 means "little chance of generating profit"; $200-300 is break-even; $300-400 earns 5-10% net. [2021 Restaurant Benchmarks](https://business.brucecounty.on.ca/hubfs/Fall%202021%20Webinars/Oct%209th-%202021%20Restaurant%20Benchmarks.pdf)
  - Southwest Baltimore plan assumes $400/sq ft for dining out [B-017]. [CLUE Group](https://swpbal.org/wp-content/uploads/2015/11/Southwest-Baltimore-retail-development-strategy-1.pdf)
  - Boulder independents: half of food-service respondents exceed $650/sq ft (n=14) [B-015]. Average food-service space is 3,100 sq ft [B-016]. [Boulder](https://bouldercolorado.gov/media/1262/download)
- **Census 2022, 722511 (full-service restaurants):**
  - Baltimore: $1,618,426 receipts per establishment, 20.8 employees, payroll 34.3% of receipts [B-001 to B-003]
  - US: $1,466,570, 20.2 employees, 34.4% [B-004 to B-006]
  - [Census EC2272BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2272BASIC&g=050XX00US24510)
- **Chain reference, a daytime cafe chain:** AUV $2.3M [B-020]. [10-K](https://www.sec.gov/Archives/edgar/data/1789940/000178994026000014/fwrg-20251228.htm) Occupancy 8.3% and labour 33.5% of restaurant sales, calculated from the FY2025 income statement [B-021, B-022]. [8-K/A Ex. 99.1](https://www.sec.gov/Archives/edgar/data/1789940/000178994026000017/exhibit991q42025corrected.htm)

### Inferences
- **Spread.** Occupancy medians cluster at 5.2-6.0% (NRA), and every source puts the "sustainable" ceiling at 8-10%. Sales per sq ft spreads more than threefold, from $200 to $650.
- **Affordable occupancy cost.** $200 x 6% = $12/sq ft; $400 x 6% = $24; $650 x 6% = $39. At the 10% ceiling: $20 / $40 / $65.
- **Revenue range.** 800 sq ft x $200 = $160K; 4,000 sq ft x $650 = $2.6M; mid case 2,000 sq ft x $400 = $800K. The Baltimore Census mean ($1.62M) fits about 4,000 sq ft at $400.

### Gaps
- There is no published sales-per-sq-ft median for independent US restaurants that I could open. The NRA Abstract has one but is paywalled.
- Seats per sq ft and sales per seat were not found.

## counter (take-away coffee, ice cream; 250-1,500 sq ft)

### Takeaway
Occupancy is solid: 5.2% median, 6.0% urban, 10% ceiling. I found no independent sales-per-sq-ft figure. The only per-sq-ft numbers are a $200-500 tier framework and a drive-thru chain ceiling of $2,115-2,644.

### Cited Findings
- **NRA, limited-service:**
  - occupancy median 5.2%, urban 6.0% (2024) [B-034, B-035]. [NRA](https://restaurant.org/research-and-media/research/restaurant-economic-insights/analysis-commentary/restaurant-occupancy-costs-were-more-than-5-of-sales-in-2024/)
  - labour 34.0% (FY2022) [B-036]. [NRA 2024 Abstract note](https://restaurant.org/research-and-media/research/restaurant-economic-insights/analysis-commentary/new-report-provides-operational-data-on-restaurants/)
  - pre-tax income 4.0% [B-037]. [NRA release](https://restaurant.org/research-and-media/media/press-releases/new-resource-from-national-restaurant-association-provides-insights-into-operational-realities/)
- **Limited-service sales tiers (webinar deck):** $400-500/sq ft earns about 10-15% net [B-039]. [2021 Restaurant Benchmarks](https://business.brucecounty.on.ca/hubfs/Fall%202021%20Webinars/Oct%209th-%202021%20Restaurant%20Benchmarks.pdf)
- **Independent coffee shops:** average "profit margin" 13.8%, with most between 10% and 25%. The margin is undefined and the sample size is not stated [B-038]. [Coffee Shop Keys](https://coffee-shop-keys.beehiiv.com/p/the-2025-independent-coffee-shop-industry-report-subscriber-discount-inside)
- **Census 2022:**
  - 722515 (snack and non-alcoholic beverage bars): Baltimore $687,158 per establishment, 10.2 employees [B-029, B-030]; US $803,603, 12.6 employees, payroll 27.3% [B-031 to B-033]
  - 722513 (limited-service restaurants): Baltimore $811,651, 9.0 employees, payroll 23.8% [B-023 to B-025]
  - [Census EC2272BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2272BASIC&g=010XX00US)
- **Chain ceiling, a drive-thru coffee chain:**
  - AUV $2.115M [B-040] and shop size about 800-1,000 sq ft [B-041]. [8-K Ex. 99.1](https://www.sec.gov/Archives/edgar/data/1866581/000186658126000003/a2025-q4_ex991.htm), [10-K](https://www.sec.gov/Archives/edgar/data/1866581/000186658126000006/bros-20251231.htm)
  - Implies $2,115-2,644/sq ft [B-042].
  - Occupancy plus other costs 16.6% and labour 26.9% [B-043, B-044].

### Inferences
- **Affordable occupancy at 6%:** $300 x 6% = $18/sq ft; $500 x 6% = $30/sq ft (tier values).
- **Revenue route.** The Baltimore 722515 mean is $687K. At 6%, that supports about $41K a year in occupancy, but the mean includes chain coffee units. For an independent, I would use the tier-based sales per sq ft rather than the Census mean.

### Gaps
- No Specialty Coffee Association, Square or Toast figure on sales per sq ft or revenue for independent counters could be opened.
- Ice-cream shop economics were not found.

## foodmaker (bakery, roaster or ice-cream maker with a shop; 1,000-6,000 sq ft)

### Takeaway
Weakest of the food formats. Only proxy figures are available: Census 445291 (baked goods retailers) and the retail food-store occupancy share (~4%, grocery-dominated). I would borrow the restaurant occupancy range (5-6% typical, 10% ceiling) and treat foodmaker sales per sq ft as unknown.

### Cited Findings
- **Census 2022, 445291 (baked goods retailers):**
  - Baltimore (8 establishments): $177,125 per establishment, 2.0 employees, payroll 33.8% [B-045 to B-047]
  - US: $674,694, 6.6 employees, payroll 23.4% [B-048 to B-050]
  - [Census EC2244BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2244BASIC&g=010XX00US)
- **Occupancy:** food and beverage stores and general-merchandise retailers "averaged about four percent" (2017 Census via the Boulder study) [B-051]. [Boulder](https://bouldercolorado.gov/media/1262/download)

### Inferences
- A bakery or roaster with a café counter behaves more like the counter or cafe formats for occupancy tolerance than like a grocery store. The 4% figure is likely too low a ceiling.

### Gaps
- No receipts for NAICS 311811 (retail bakeries making goods on site), 311920 (coffee roasters) or 311520 (ice cream).
- No industry body figure (e.g., Retail Bakers of America) on sales per sq ft or occupancy.

## shop (small independent gift, apparel or book shop; 400-2,500 sq ft)

### Takeaway
I would use an occupancy share of about 9%, inside a 6-12% band. Sales per sq ft runs $50 / $325 / $649 (derived below). Gross margin is about 50% for gift and about 41% for books. Payroll is about 13-21% of sales.

### Cited Findings
- **Occupancy:**
  - Clothing and similar stores "closer to nine percent" (2017 Census via Boulder) [B-068]. [Boulder](https://bouldercolorado.gov/media/1262/download)
  - Successful retailers spend "6-12 percent of their gross sales on rent" (Southwest Baltimore plan) [B-069]. [CLUE Group](https://swpbal.org/wp-content/uploads/2015/11/Southwest-Baltimore-retail-development-strategy-1.pdf)
  - Independent bookstores: 8.95% [B-070]. [ABA ABACUS 2005](https://bookweb.org/node/20527)
- **ABACUS (independent bookstores, FY2004):** payroll 21.4%, gross margin 41.45%, net -0.72% (top third 6.66%) [B-071 to B-073]. [ABA](https://bookweb.org/node/20527)
- **Gift retailers (2001 survey, n=114)** [B-074 to B-077]. [Gifts & Decorative Accessories](https://www.giftsanddec.com/business-news/todays-gift-retailer)
  - payroll median 16%
  - 58% of stores at 2,000 sq ft or smaller
  - 64% with sales of $100K-$1M
  - pricing at 2x cost, which works out to 50% initial margin
- **Boulder independents:** median retail sales band $450-649/sq ft, with 78% below $650 [B-078]. Average retail space 2,600 sq ft [B-079]. [Boulder](https://bouldercolorado.gov/media/1262/download)
- **Census 2022:**
  - Baltimore gift (459420): $650,440 per establishment, 4.4 employees, payroll 12.7% [B-057 to B-059]
  - Baltimore clothing (458110): $1,378,270, 10.2 employees, payroll 15.2% [B-052 to B-054]
  - Baltimore books (459210): $1,398,400 [B-063]
  - US gift: $1,132,161 [B-060]; US clothing: $3,156,246 [B-055], chain-heavy
  - [Census EC2244BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2244BASIC&g=050XX00US24510)

### Inferences
- **Derived sales per sq ft:**
  - low: $100K / 2,000 sq ft = $50 (gift-survey floor band)
  - mid: Baltimore gift mean $650K / 2,000 sq ft = $325 (two different sources combined)
  - high: Boulder median band top, $649
- **Affordable occupancy at 9%:** about $4.50 / $29 / $58 per sq ft.
- **Spread.** The spread is wide, and the 2001 and 2004 survey data are old. The Waverly mid case should probably sit nearer the low-to-mid end than the Boulder figure.

### Gaps
- No current independent gift or apparel survey reporting sales per sq ft.
- ARTS 2022 gross margins by kind of business could not be opened (see Cross-cutting).

## showroom (furniture, home goods, makers' store; 2,500-12,000 sq ft)

### Takeaway
Occupancy is about 9% (Census 2017 via Boulder). The only sales-per-sq-ft figure is a chain's: $167. I would treat that as the efficient-operator level for furniture, so an independent sits at or below it.

### Cited Findings
- **A furniture store chain, FY2025** [B-090 to B-093]. [10-K](https://www.sec.gov/Archives/edgar/data/216085/000162828026012199/hvt-20251231.htm)
  - $167 sales per weighted-average sq ft ($164 in 2024, $197 in 2023)
  - average store about 35,000 sq ft
  - gross margin 60.7%
  - about $5.88M per store
- **Occupancy:** home furnishing stores "closer to nine percent" [B-089]. [Boulder](https://bouldercolorado.gov/media/1262/download)
- **Census 2022:**
  - Baltimore furniture (449110): $759,947 per establishment, 4.2 employees [B-080, B-081]
  - Baltimore furniture and home furnishings (4491): $741,462 [B-085]
  - US 449110: $3,837,755, payroll 11.8% [B-082 to B-084]
  - US 449129 (all other home furnishings): $4,618,101 [B-087]
  - [Census EC2244BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2244BASIC&g=010XX00US)

### Inferences
- **Affordable occupancy:** $167 x 9% = about $15/sq ft at the chain level.
- **Census cross-check.** The Baltimore furniture mean ($760K) spread over 2,500-12,000 sq ft implies about $63-304/sq ft. Large showrooms will afford much lower rent per sq ft than small shops.

### Gaps
- No independent furniture or makers'-store sales-per-sq-ft or occupancy survey (e.g., the Home Furnishings Association) could be opened.

## bike (bike shop with repairs; 800-4,000 sq ft)

### Takeaway
I would use $179 sales per sq ft (NBDA, 2013, independent specialty dealers) and about 9% occupancy (sporting goods/hobby). That gives about $16/sq ft affordable occupancy.

### Cited Findings
- **NBDA 2013** [B-097 to B-099]. [Bicycle Retailer, reporting NBDA](https://bicycleretailer.com/retail-news/2014/07/17/fred-clements-bike-shop-metrics-are-rise)
  - $179/sq ft ($111 in 2004)
  - average store sales $997,761
  - average store size 5,562 sq ft
  - 88.1% of dealers are single-store operations
- **Occupancy:** sporting goods/hobby stores about 9% (2017 Census via Boulder) [B-100]. [Boulder](https://bouldercolorado.gov/media/1262/download)
- **Census 2022, US 459110 (sporting goods retailers):** $3,567,664 per establishment, 12.5 employees, payroll 11.1%. Chain-dominated; Baltimore suppressed [B-094 to B-096]. [Census EC2244BASIC US](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2244BASIC&g=010XX00US)

### Inferences
- **Revenue range:** 800-4,000 sq ft x $179 = $143K-$716K.
- **Affordable occupancy:** $179 x 9% = about $16.1/sq ft. The 2013 figure predates the 2020-21 boom and 2023-24 bust, so treat it as approximate.

### Gaps
- NBDA's 2015, 2017, 2023 and 2024 studies are paywalled; only their sample sizes are public.
- No bike-specific occupancy share or repair-revenue share was found.

## services (barber, hair or nail salon; 400-2,000 sq ft)

### Takeaway
I would use Census Baltimore receipts per employer establishment (barber $338K, beauty $265K, nail $453K) and a rent share of 8-15% (vendor estimate). Labour is high: Census payroll shares are 35-52% of receipts. Many operators are nonemployers averaging about $24K.

### Cited Findings
- **Census 2022, Baltimore employer establishments:**
  - barber shops: $338,312 per establishment, 5.9 employees, payroll 51.6% [B-101 to B-103]
  - beauty salons: $265,284, 6.7 employees, 47.2% [B-104 to B-106]
  - nail salons: $452,517, 5.6 employees, 35.3% [B-107 to B-109]
  - US: barber $236,749, beauty $307,752, nail $342,237 [B-110 to B-118]
  - [Census EC2281BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2281BASIC&g=050XX00US24510)
- **Baltimore nonemployers, all of sector 81:** about $24,033 each [B-119]. [Census NS2200NONEMP](https://data.census.gov/api/access/data/table?id=NONEMP2022.NS2200NONEMP&g=050XX00US24510)
- **Boulevard (vendor estimates):** rent 8-15%, payroll 40-50%, net 10-15%; a mid-sized salon is 1,000-1,500 sq ft [B-120 to B-123]. [Boulevard](https://www.joinblvd.com/blog/salon-budget-examples)
- **Strategies:** service payroll 30-35% of total revenue [B-124]. [Strategies](https://strategies.com/the-dirty-truth-about-salon-spa-service-payroll-costs)
- **BizBuySell, NAICS 812113 US average (2021):** revenue $504,132, gross margin 76.96%, net 11.0% [B-125 to B-127]. [BizBuySell](https://www.bizbuysell.com/learning-center/revenue-profit-benchmarks/nail-salons)

### Inferences
- **Sales per sq ft (combining sources):** beauty $265K over 1,000-1,500 sq ft is about $177-265/sq ft. At an 8-15% rent share, that affords about $14-40/sq ft.
- **Booth-rental model.** A shop run on booth rental (nonemployers) will show much lower receipts per operator. Rent capacity then depends on chair count, not on sales.

### Gaps
- No Professional Beauty Association figure that I could open.
- No salon occupancy figure from a survey (the Boulevard figure is an estimate).
- Nonemployer 812111-812113 detail for Baltimore was rate-limited.

## fitness (boutique fitness or yoga studio; 1,500-6,000 sq ft)

### Takeaway
I would use revenue of $77-104 per sq ft (independent studios, 2015) and a rent share of 13-21%. That affords about $10-22/sq ft. The franchise ceiling, a boutique-fitness franchisor, is $273-455/sq ft.

### Cited Findings
- **AFS/ClubIntel, 2015 data:** revenue $104/sq ft for studios under 2,000 sq ft and for 2,001-5,000 sq ft; industry average $77; top quartile $189 [B-135, B-136]. [Health Club Management](https://www.healthclubmanagement.co.uk/health-club-management-features/Report-Why-the-boutique-studio-market-continues-to-grow/31471)
- **Same source, cost shares:** rent 21% of revenue (top quartile 13%), staffing 63% (51%), EBITDA 24% [B-137 to B-139]. [Health Club Management](https://www.healthclubmanagement.co.uk/health-club-management-features/Report-Why-the-boutique-studio-market-continues-to-grow/31471)
- **AFS, 2014:** average studio revenue $297,468; EBITDA margin 26% [B-140]. [American Spa](https://www.americanspa.com/commercial-clubs/afs-report-average-fitness-studio-revenue-was-less-than-300-000-2014)
- **A boutique-fitness franchisor:** run-rate AUV $683,000 (Q4 2025) [B-141]; studios 1,500-2,500 sq ft [B-142]; calculated $273-455/sq ft [B-143]. [8-K Ex. 99.1](https://www.sec.gov/Archives/edgar/data/1802156/000119312526076678/d102623dex991.htm), [10-K](https://www.sec.gov/Archives/edgar/data/1802156/000180215626000016/xpof-20251231.htm)
- **Census 2022, 713940 (fitness and recreational sports centers):**
  - Baltimore: $1,148,275 per establishment, 22.9 employees, payroll 34.7% [B-128 to B-130]; taxable establishments only, $937,381 [B-131]
  - US: $924,209 [B-132]
  - Both include big gyms and YMCAs.
  - [Census EC2271BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2271BASIC&g=050XX00US24510)

### Inferences
- **Affordable occupancy:**
  - $77 x 21% = $16.2/sq ft
  - $104 x 21% = $21.8; $104 x 13% = $13.5
  - top quartile $189 x 13% = $24.6
- **Revenue range:** 1,500-6,000 sq ft x $77-104 = $116K-$624K.
- **Inconsistent cost shares.** The AFS shares do not sum (63 + 21 + 24 > 100), so they come from different subsets. Fitness tolerates a much higher rent share than retail or food.

### Gaps
- The 2015 data are old and pre-pandemic.
- No current HFA (formerly IHRSA) or ABC Fitness boutique figures could be opened.

## studio (arts studio, gallery or rehearsal space; 400-8,000 sq ft)

### Takeaway
Only Census per-establishment figures exist, and they are poor proxies: national averages skewed by large galleries, museums and high-earning artists. I found no sales-per-sq-ft or occupancy benchmark.

### Cited Findings
- **Census 2022:**
  - US 711510 (independent artists, writers and performers): $738,630 per establishment, 2.3 employees [B-144, B-145]
  - US 459920 (art dealers): $2,126,297, 3.8 employees [B-146, B-147]
  - Baltimore art dealers: 2.2 employees; receipts suppressed [B-148]
  - Museums: Baltimore $3,784,000, US $2,589,752 [B-149 to B-152]
  - [Census EC2271BASIC US](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2271BASIC&g=010XX00US)

### Inferences
- Arts studio and rehearsal tenants typically pay per-sq-ft or per-hour rent from grants or member fees, not from sales. The engine may need a rent-capacity input that does not depend on revenue. That is a judgment call, not a sourced figure.

### Gaps
- No Americans for the Arts, Artspace or NCAR figure on studio rent burden or gallery sales per sq ft was found within the search budget.

## venue (small performance, event or cinema venue; 2,000-15,000 sq ft)

### Takeaway
Only Census per-establishment figures exist, and these categories include arenas and multiplexes. I found no independent-venue revenue, sales-per-sq-ft or occupancy figure.

### Cited Findings
- **Census 2022:**
  - Baltimore 711310 (promoters with facilities): $4,032,364 per establishment, 60.4 employees [B-153, B-154]
  - US 711310: $5,545,372 [B-155]
  - US 711110 (theatre companies and dinner theatres): $2,514,106, 19.0 employees [B-157, B-158]
  - US 512131 (cinemas): $3,036,594, 26.3 employees [B-159, B-160]
  - Baltimore 711110 and 512131 are suppressed.
  - [Census EC2271BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2271BASIC&g=050XX00US24510), [Census EC2251BASIC US](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2251BASIC&g=010XX00US)

### Gaps
- No NIVA independent-venue survey figures; I did not search for them because the search budget was spent.
- No data on per-screen economics for independent cinemas.

## office (small office or coworking; 300-10,000 sq ft)

### Takeaway
Census shows Baltimore professional-services establishments average $4.48M in receipts and 18.2 employees, and a design firm averages 4.7 employees. I found no occupancy-to-revenue benchmark, so office rent capacity is better modelled per employee than per sales.

### Cited Findings
- **Census 2022, Baltimore:**
  - NAICS 54 (professional, scientific and technical services): $4,476,047 per establishment, 18.2 employees, payroll 40.4% [B-161 to B-163]
  - accounting/tax: $4,490,993 [B-164]
  - specialized design: $1,153,901, 4.7 employees [B-166, B-167]
  - consulting: $3,649,854 [B-168]
  - nonemployers in 54: about $48,891 [B-170]
  - [Census EC2254BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2254BASIC&g=050XX00US24510)
- **Coworking:** average North American space 9,084 sq ft with 96 members (Deskmag 2019) [B-171]. [Yardi Kube / Deskmag](https://www.yardikube.com/blog/2019-deskmag-global-coworking-survey-results/) A "healthy" margin is 10-30% (vendor claim, no source) [B-172]. [OfficeRnD](https://officernd.com/blog/coworking-financial-benchmarks/)
- **Southwest Baltimore office rents:** $14-32/sq ft (BAE 2022). [BAE](https://static1.squarespace.com/static/63979ae6a2fa423bf9ce0e70/t/6397a57f4ef3a1514a6e1417/1670882688414/West+Baltimore+Street+Commercial+Corridor+Market+Study+and+Action+Plan.pdf)

### Gaps
- No sq-ft-per-employee figure and no occupancy share of revenue for small professional firms.
- No coworking revenue per sq ft or per desk from a survey.

## workshop (maker workshop with a counter; 500-6,000 sq ft)

### Takeaway
Only Census repair-industry proxies are available: about $500K per establishment and about 4 employees.

### Cited Findings
- **Census 2022:**
  - Baltimore 8114 (personal and household goods repair): $496,125 per establishment, 3.8 employees, payroll 33.5% [B-173 to B-175]
  - Baltimore reupholstery and furniture repair: $763,286 [B-176]
  - US 811490 (other repair, including bicycles): $524,569, 4.1 employees, payroll 29.2% [B-178 to B-180]
  - [Census EC2281BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2281BASIC&g=010XX00US)

### Gaps
- No sales-per-sq-ft or occupancy benchmark for woodwork, ceramics or repair workshops.
- Not fetched: Census 327110 (pottery manufacturing) and 611610 (fine-arts schools).

## community (community, health or nonprofit space; 1,000-10,000 sq ft)

### Takeaway
Census gives budgets per establishment: Baltimore civic and social organizations average $1.17M and 9.3 employees. I found no published occupancy share for nonprofits.

### Cited Findings
- **Census 2022, all tax-exempt establishments:**
  - Baltimore 813410 (civic and social organizations): $1,166,684 per establishment, 9.3 employees, payroll 33.9% [B-181 to B-183]
  - Baltimore social advocacy (8133): $2,121,122 [B-184]
  - Baltimore other social advocacy (813319): $1,125,150 [B-186]
  - US 813410: $788,971 [B-188]
  - Baltimore NAICS 813 overall is dominated by grantmaking foundations ($497.75M across 52 establishments), so I did not use it.
  - [Census EC2281BASIC](https://data.census.gov/api/access/data/table?id=ECNBASIC2022.EC2281BASIC&g=050XX00US24510)
- **Nonprofit Centers Network:** occupancy is "the second largest line item for nonprofits after personnel", but no percentage is given. [Nonprofit Centers Network](https://www.nonprofitcenters.org/?p=1567)

### Gaps
- No occupancy share of the budget for small nonprofits or community health spaces.
- Health-care NAICS (621) was not pulled.
