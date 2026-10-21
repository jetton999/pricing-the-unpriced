# Greenmount frontage explorer (draft for review)

One page that shows, for each of the 69 frontage parcels (Greenmount Ave, E 29th to E 33rd St), what the
building was used for, what it could become and why. Download `index.html` and open it in a browser
(GitHub shows the source, not the page).

## What is on the page

Five tabs, so each reads as a short page:

| Tab | What it does |
|---|---|
| Buildings | Map of the frontage, the use ledger (dominant use per decade, 1880s to today) and a panel per building: best fit and why in one line, what it could support per year, a heritage-revival name where one is documented, the rules that apply, and, for retail, which trade and its modern version. Detail (factor scores, evidence, similar buildings) is folded away. Compare up to three uses side by side; three hand-written concepts |
| Block plan | Places uses on the vacant parcels under a saturation limit, then ranks alternative plans for the same parcels by the rent the uses could support |
| Money | The comps engine (`team/comps`): ranges per use, the trail from each figure to its source rows, other cities' corridors side by side, held-out checks |
| Evidence and method | How the score works (adjustable weights, rules, community, neighbours, back-test), retail broken into seven trades with reference brands, customer groups, comparable cases, the screening table |
| Roadmap | The road to the final deliverable |

"Today" shows the team's tenant check next to the sponsor's October 2026 storefront assessments
(`storefront_assessments.csv`). Where our check found no listing at an address and the sponsor found a business, a
church or a house, the page says so; houses with no shop front are left out of the block plan.

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
| `extras.py` | The sponsor's storefront check, heritage-revival names, retail trades and survey-photo counts per parcel |
| `retail_types.json` | Seven retail trades: the modern version, usual size, reference brands and cautions, every claim with its source |
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
- This public version names no business as a possible tenant. The retail brands are reference points for a modern format, not prospects. No NDA data is used.
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
