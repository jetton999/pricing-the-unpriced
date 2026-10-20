# Greenmount frontage explorer (draft for review)

One page that shows, for each of the 69 frontage parcels (Greenmount Ave, E 29th to E 33rd St), what the
building was used for, what it could become and why. Download `index.html` and open it in a browser
(GitHub shows the source, not the page).

## What is on the page

| Section | What it does |
|---|---|
| Block faces, use ledger, building panel | Map of the frontage, the dominant use per decade from the 1880s to today, and every parcel's sourced evidence |
| How the recommendation works | Use score v0.3: two rule filters (C-1 zoning Table 10-301, the urban renewal plan), then six factors with adjustable weights: heritage, saturation, size fit, community wishes and objections, neighbours, precedents. Includes a preliminary back-test |
| Compare uses | Up to three uses for one building, factor by factor, with rent, revenue and the rent each could support |
| What each use could pay and earn | The comps engine (`team/comps`): ranges per use, the trail from each figure to its source rows, other cities' corridors side by side, held-out checks and sensitivity |
| Block plan | Places uses on the vacant parcels one at a time under a saturation limit, then ranks alternative plans for the same parcels by the rent the uses could support (with a search check) |
| Who it is for | Seven customer groups, their obstacles (ranked by evidence) and the programmes that help, with the buildings that fit each group |
| Comparable cases | 32 building reuses and 19 streets elsewhere, with their similarity to each building and to Waverly |
| What it could become | Hand-written concepts for 3117, 3107 and 3026 |
| Where this ends | The road to the final deliverable |

## Rebuild

```bash
python3 team/comps/comps_engine.py          # rent and revenue ranges (optional; the page uses the last comps_ranges.json)
python3 team/explorer/build_explorer.py      # standard library only; writes index.html
```

| File | What |
|---|---|
| `build_explorer.py` | Reads the extractor outputs, the evidence and tenant files, `properties.csv` and `team/comps/comps_ranges.json`, computes the per-parcel inputs and writes `index.html` |
| `template.html` | The page: layout, score engine and views |
| `concepts.json` | The three hand-written concepts, every fact with its source |
| `library.json` | The case library and evidence behind the community, neighbour and customer layers, every entry with its sources |
| `index.html` | The built page (generated; do not edit by hand) |

## Data vintage

Built from the week-2 extractor outputs, which use the September package ids. The October 2026 refresh retired
52 ids; none of the 69 frontage parcels is among them, so the parcel ids still match. Parcel facts such as the
owner type, vacant-building notices and permits come from the October `properties.csv`. The evidence and
timelines are still the September run. Rerunning the extractor on the October curated layer (7,891 rows, up
from 3,597), and using `storefront_assessments.csv` and `property_images.csv`, is the next step.

## Rules kept

- It ranks uses for a building, never buildings by price: no valuation, no appraisal language and no
  acquisition targeting, as the sponsor's proposal requires.
- A sponsor walk-through is not a statement of ownership; the owner of record comes from the state
  assessment snapshot.
- This public version names no business as a possible tenant. No NDA data is used.
- Every outside fact links to its source. None of the September package's 52 sensitivity-flagged records is
  among the frontage use records the page shows; the extractor keeps flagged rows, as the repo requires.

## Known limits

- The weights are team judgement; the sliders show how much the ranking depends on them.
- The back-test is preliminary: 41 parcels, measured on the same data the score uses.
- The community layer rests on news, testimony and plans, not a survey of residents.
- Most case statuses are not confirmed for 2025-26.
- Rent ranges rest on asking rents (five in Waverly) and national sales benchmarks; see `team/comps/MODEL_CARD.md`.
- Feedback voting works only in the team's hosted copy; this file shows the scores without it.

## AI use

Built with Claude (October 2026) from the team's notes and the sources linked in the data. Before merge, a team
member reviews the code, checks a sample of the case library and the concept facts against their sources, and
signs below.

Checked by: ____________________ Date: __________
