# License and attribution

## Sponsor-produced content

The corridor knowledge base in this repository (all root-level `.csv` files, `README.md`,
`DATA_DICTIONARY.md`, `START_HERE.ipynb`, `05_incidents_by_decade.png`) is released by
Oxcart Assembly / BNBD under Creative Commons Attribution 4.0 International (CC BY 4.0).

You may share and adapt it, including commercially, with attribution:

> Greenmount Corridor knowledge base, Oxcart Assembly / BNBD, 2026.

Full license text: https://creativecommons.org/licenses/by/4.0/

`Pricing_the_Unpriced_CUSP_Proposal.pdf` is the sponsor's proposal document, provided for
reference and reproduced with permission of the author. It is not CC-licensed.

## Third-party sources in `/public_sources`

These files are redistributed here so the analysis in the proposal can be checked
independently. They carry their own terms.

| File | Source | Terms |
|---|---|---|
| `national-register-listed_20260522.xlsx` | National Park Service, National Register of Historic Places | U.S. federal government work, public domain (17 U.S.C. 105) |
| `federal-DOEs_20260522.xlsx` | National Park Service, federal Determinations of Eligibility | U.S. federal government work, public domain |
| `holc_baltimore_1937.geojson` | Mapping Inequality: Redlining in New Deal America, Digital Scholarship Lab, University of Richmond | CC BY-NC-SA 4.0. Attribution required, derivatives share-alike. See https://dsl.richmond.edu/panorama/redlining/ |

## A note on the sensitivity flags

52 of the 20,308 incident rows carry a `sensitivity` value: `trauma`, `personal_rights`,
`displacement`, `commercialization`. Every one of them is sourced to published newspaper
reporting, federal court records, land records, or a public CHAP landmark report. Nothing in
this package is private personal data.

The flags exist for a design reason, not a legal one. A naive salience score would rank a
property higher precisely because something terrible happened there, and would then surface it
in a public address lookup with no framing at all. The flags are how a downstream interface
knows to handle a claim carefully. Treat them as a design input, not as rows to quietly drop.
