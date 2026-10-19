# Team Greenmount: week 1 (12–18 October 2026)

Work for Idea 1, heritage-anchored highest and best use, on the proposed first focus area.

| File | What it is |
|---|---|
| `focus_area.py` | Standard-library script. Builds everything in `out/` from the CSVs at the repo root. |
| `out/focus_area.geojson` | The working boundary. **Approximate**: hand-traced from `proposed-focus-area-phase1.png`. A copy sits at `map/focus_area.geojson` for the map app. |
| `out/focus_area_properties.csv` | One row per property in the focus area: present state, curated depth, use-record counts, scans, tours. |
| `out/use_records.csv` | Every curated record in the focus area, classified A / B / C for use extraction. |
| `out/use_timelines.md` | Four hand-built use timelines with source rows: the reference answers for the extractor. |
| `comps_template.csv` | Column layout for the comps library. |

Run `python3 team/week1/focus_area.py` to rebuild `out/`. If the boundary changes, copy
`out/focus_area.geojson` over `map/focus_area.geojson`.

## The use-record classes

- **A, states a use.** Directory, advertisement, commerce and construction records, Polk and
  census-directory rows, and any record linked to a business by `operated_at`.
- **B, has to be read.** News and civic items, Sanborn sheets (block-level; the uses are in the
  image), atlas landholder plates, neighbourhood studies.
- **C, not about use.** Interments, deeds and sales, obituaries, crime, public investment.

Rows with a `sensitivity` flag are kept in every output and carry the flag in their own column.
