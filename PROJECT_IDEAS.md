# Pricing the Unpriced: Capstone Project Ideas
**NYU CUSP Capstone 2026–2027 · Sponsor: BNBD / Oxcart Assembly**

Two project sketches. Both run on the sponsor's Greenmount corridor knowledge base,
exported here as CSVs. Everything students need is in this repo. The corpus
covers 1,874 properties on Greenmount Ave, Baltimore, with ~3,600 hand-researched
historical records back to the 1650s and ~16,700 live city feeds.

---

## Idea 1: Heritage-anchored highest and best use

**Question.** Given an assemblage of properties, what should each one become, what would
that earn, and does the mix work as a block?

**Why heritage.** Conventional highest-and-best-use analysis starts from zoning and square
footage. This one starts from what the address *was*. The premise is that a documented
historic use is a strong prior for a future use: the building was built for it, and the
neighborhood remembers it. The corridor's own record is the source of these priors.

**One example.** The corridor has two documented theatres: the Boulevard (Art Deco,
1920s–70s) and the Waverly (c. 1910, now a Shoe City). A live-music hall in the Boulevard
is a use the building has already proven. That is one historic use inspiring one proposed
use. The same move applies to every address with a use history: a former grocery, a hall,
a bank, a garage, a church.

**Uses beyond the building.** A "use" need not be a tenant. The history is also raw
material, and the sponsor already treats it that way, anchoring new works to a deed:
a feature film rooted in the 1858 arson at St. John's (3009 Greenmount) and an album
rooted in a razed home on Barclay St. Candidate uses the optimizer should be able to
consider:
- **Screen and audio.** A documentary, series, or podcast per block or per property. The
  1,138 research white papers are the treatments. 115 registered trademarks and patents tied
  to corridor addresses are story seeds.
- **Immersive experience, Meow Wolf style.** One large vacant footprint becomes a walk-through
  of the corridor's own strata: the 1688 land patents, the turnpike tollgate, Mechanics'
  Hall, the theatres, the enslavers in the chain of title. The properties with the deepest
  records tell you which rooms have the most material.
- **Heritage revivals.** Reopen a business under its documented historic name and trade
  dress. The trademark research to clear the name is already in hand.
- **Interpretive layer.** Walking tours, plaques, an AR overlay on the storefronts. Cheap,
  and it raises the value of every other use on the block.

Content uses matter to the optimizer because they don't saturate: a podcast about the
Boulevard doesn't compete with a concert hall in it. Venues do saturate. The model should
treat the two differently.

**What the data already holds.**
- Use history per address: Sanborn maps (footprint, material, use, 1915), Polk city
  directories (business at each address by year), 661 newspaper clippings, ~680
  `operated_at` links between businesses and properties, NRHP nomination text.
- Present state, per property: zoning, year built, sqft, dwelling units, active permits,
  vacancy, violations, tax certificates, receivership, whether a business trades there.
- Market context, per property: market typology, median sale price, days on market, and
  inventory; HUD fair market rent; median household income; walkability index and transit
  access; historic district, main street, opportunity zone, and CDBG flags. Nearby business
  counts and walk scores are empty in this export.
- Assemblages: the export has no acquisition groupings. Use `block_side_id` (141 values) as
  the default unit, and let the sponsor name specific assemblages.
- One calibration point: the sponsor can share daily sales for an operating restaurant at
  2731 Greenmount, under NDA, to sanity-check revenue estimates.

**What students build.**
1. A use-history timeline per property, extracted from the curated layer.
2. A candidate-use generator that proposes uses anchored to that history.
3. A comps engine: find operating examples of each candidate use in comparable corridors
   and estimate performance (revenue per sqft, achievable rent).
4. An assemblage optimizer: assign uses across the assemblage with a saturation constraint, so
   three of the same thing don't land on one block. Measure saturation against the existing
   business mix.

**Hard parts.** A property with lots of paperwork is not necessarily significant. Comps
will mostly come from outside Baltimore. "Over-saturated" needs a definition students can
defend.

---

## Idea 2: Tenant-owned exit for a neighborhood REIT

**Question.** Design a lease that starts a business as an ordinary tenant and ends with it
owning the building, while the REIT's investors still get paid.

**Why.** The sponsor is recruiting businesses to start and operate in the corridor. They
sign as regular tenants of the REIT. The idea is that a tenant who succeeds can buy its
building from the REIT, on terms fixed at signing. That gives the REIT an exit other than
a sale to an institutional buyer, and keeps the upside in the neighborhood. Worker buyouts
are now routine in Baltimore. A tenant path to owning the *building* is not.

**What the local record shows.** Eleven cases were checked; full table with sources in
`docs/worker-owned-exits.md`. The ones that matter:

| Case | Year | What moved | Structure | Financing | Building? |
|---|---|---|---|---|---|
| Wine Source, Hampden | 2024 | Business | Worker co-op | BRED loan, GoFundMe | No, founder kept it |
| Waverly Ace Hardware (13-store chain) | 2021 | Business, 30% then phased to 100% | ESOP | National Cooperative Bank | Not reported |
| Common Ground Café, Hampden | 2023 | Business + lease | Worker co-op | BRED, GoFundMe | No |
| Tabard Inn, DC | 1993 / 2018 | Shares, 30% then 51% | ESOP | Undisclosed | Unconfirmed |
| Red Emma's, 3128 Greenmount | 2021–22 | Two buildings | Worker co-op | Seed Commons LOC, MD capital grant, CBP fund, ~$1.6M | Yes |
| WaterBottle co-op, West Baltimore | 2020 | Contracting firm + rentals | Worker co-op | BRED, ~$5M cumulative, 22 homes | Yes |
| East NY Community Land Trust, Brooklyn | 2026 | 9,500 sf commercial | CLT | $1M state, $650k CDFI loan, $720k crowdfund, $2.3M | Yes |
| 3218 Wisconsin Ave, DC | 2019 | 20-unit apartment | Limited-equity co-op via TOPA | LISC, DC Preservation Fund | Yes |
| Plaza 122, Portland | 2014–17 | 29k sf strip retail | Community Investment Trust | Bank at 75% LTV, sub-debt at 2–4%, $10/mo shares | Yes |

**Patterns worth designing around.**
- Worker buyouts almost always exclude the real estate. The seller keeps the dirt and the
  co-op leases. The two Baltimore co-ops that own property bought it later, with separate
  and larger financing. A REIT buyout looks like the land-trust and CIT cases, not the co-op
  conversions.
- One lender does most Baltimore deals: BRED, backed by Seed Commons. Repayment is a share of
  net profit, no personal guarantees. It is a business lender, and its real-estate exposure is
  the exception. For NYC the analogs are New Economy Project and The Working World; for DC,
  LISC and the DC Preservation Fund.
- Seller financing showed up in none of the cases. Bank plus CDFI, or CDFI alone, was the
  norm. Existing mortgages on the REIT's buildings would need lender consent, not a seller
  note.
- Every real-estate case used public capital: MD state grants for Red Emma's, a state
  earmark for East New York, DHCD money in DC. Crowdfunding is real but small.
- The recurring capital stack: senior debt at 70–75% LTV, a patient subordinated loan at
  2–4% from a nonprofit, a public grant, then community equity raised over time to retire the
  sub-debt.
- Plaza 122 is the only case where *neighbors*, not just tenants, bought in and could exit:
  $10 a month, a bank letter of credit against loss, 9% dividends. That securities scaffolding
  is the template for a tenants-plus-neighbors buyout.
- ESOPs suit scale (Ace, ~260 staff) and phase in over years. Co-ops suit storefronts and
  close in months.

**What the data already holds.**
- Property level, in the export: last sale price and date, assessed value, AVM estimate,
  fair market rent, owner name and type, ground rent, and baseline snapshots frozen at two
  dates in July 2026.
- Tenant level, from the sponsor under NDA: daily sales, channel split, and P&L for the
  operating restaurant at 2731 Greenmount.
- Deal level, from the sponsor: which properties the REIT holds, lease terms, investor
  return targets, and the cap table.

**What students build.**
1. A case file: the table above, extended and verified, with the deal terms that are public.
   Interview BRED, Red Emma's, and the Ace owners on what they would do differently.
2. The lease mechanics: how rent accrues toward equity, what triggers the option to buy,
   how the price is set at signing versus at conversion, and what happens if the tenant
   leaves early.
3. A cash-flow model from both sides: tenant cost of occupancy over the lease, REIT investor
   return under a range of conversion timings. Test the Plaza 122 stack against corridor
   numbers.
4. A stress test using the real tenant P&L. Can a new restaurant's margin carry rent now and
   a mortgage at 75% LTV plus sub-debt later?
5. A recommended lease-with-option term sheet the sponsor could use in recruiting.

**Hard parts.** New businesses fail often, and the lease has to survive that. Restaurant
margins are thin. Fixing a price years ahead means someone bears the appreciation risk.
Buildings with several tenants need a rule for who buys. Securities law applies once
neighbors are buying shares. Deal prices in worker buyouts are almost never disclosed, so
some of the case file will stay blank.

---

## How this relates to the proposal

The July proposal framed the capstone around scoring each property's documented history
and testing that score against sale prices. These two ideas are the sponsor's current
direction for what a team builds. The data package, its provenance layer, and its warnings
are the common substrate for either: the use-history timeline that idea 1 starts from is
what that layer produces. A revised proposal presenting the two ideas is in [`site/`](site/).

Repository layout, setup, the notebook, and the map app are described in
[README.md](README.md). Read the incident table carefully: administrative feeds and curated
history are mixed in one file, and separating them is the first job. Assessed value is an
administrative number, not a market price. Sponsor data is CC BY 4.0; see `LICENSE.md`.
