# Comps library: first ten (draft for review)

Ten comparable businesses and spaces for two candidate uses, one row per comp, in the column layout of
`team/week1/comps_template.csv`. Six further rows that did not make the first ten are in
`comps_alternates.csv`.

| File | Rows | What |
|---|---|---|
| `comps.csv` | 10 | Five per candidate use |
| `comps_alternates.csv` | 6 | Swap-ins: a closed Pittsburgh cafe (downside case), a DC corner space, a low-end Greenmount rent, two nonprofit salvage stores, a Pittsburgh showroom space |

## The two candidate uses (to be confirmed by the team on 19 October)

Each use is anchored on what the building has already shown it can carry, with the source rows in
`anchor_incident_ids`:

- **Corner cafe / all-day diner**, anchored on 3200 Greenmount (property 752). About 115 years of food and
  drink at this corner: saloon (incident 10424), drugstore soda fountain (5196), White Coffee Pot (18027).
- **Large-format furniture / home-goods showroom**, anchored on 3117 Greenmount (property 742), a purpose-built
  showroom with furniture tenants from 1928 to 1989 (Miller Bros. 11818 and 4929, Moses Zalis 11861 to 11863).

## How to read a row

- `figure_type`: `reported` is a figure the source states; `asking` is a listed rent; `estimated` is an
  industry benchmark. Where we divided one stated number by another (rent per square foot from a rent roll,
  revenue per square foot), the `notes` say "calculated" and show the arithmetic.
- `rent_basis`: NNN, gross or modified gross, as the source states it. CAFE-04 is a rent roll that includes
  tenants' expense payments, so it is entered as gross.
- Revenue from SEC Form C filings is certified by the business owner, not reviewed by an accountant. Revenue
  from IRS Form 990 is program-service revenue and can mix sales with service fees.

## Open checks before these figures are used

- SHOW-04, 3700 Falls Rd: the listing says $20.00/SF NNN (re-checked 16 Oct), but the broker flyer's text reads
  "$2 SF/YR". Confirm with the broker.
- SHOW-01: the rent is the asking rate for another suite in the same building, not the showroom's own lease.
- CAFE-04, SHOW-03, SHOW-05: rent per square foot is our calculation from a stated total.
- CAFE-03 and CAFE-07: the shops' floor areas are not published, so no revenue per square foot.
- Figures re-checked against the source page on 16 October 2026: CAFE-03 revenue, CAFE-04 rent roll and
  tenants, SHOW-04 rent.

## Sources and rules

Public listing pages (CityFeet, CommercialCafe, Showcase, broker and MLS pages), SEC EDGAR Form C filings, IRS
Form 990 data on ProPublica, and the Haverty Furniture 10-K. LoopNet, Crexi and BizBuySell refused automated
access, so their listings were read through the sites that repost them. No figures from the NDA restaurant data
are used here, and none may be added.

## AI use

The rows were drafted with Claude on 16 October 2026 (`entered_by` says so on every row). Before merge, a team
member checks each figure against its `source_url`, as the charter requires.

Checked by: ____________________ Date: __________
