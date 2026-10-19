# Prototype v0: use timelines, proven uses and a first screen for the frontage

A first end-to-end pass over the 79 frontage properties, to see what the fall deliverables can look like.
It is a draft for the team to test and replace piece by piece, not the extractor or the optimiser.

```bash
python3 team/prototype_v0/build_v0.py    # joins the evidence, codes uses, writes the tables
python3 team/prototype_v0/screen_v0.py   # proven uses x today's mix x indicative economics
```

Standard library only. Needs `team/week1/out/` (the week-1 package), `team/evidence/` and `team/tenants/`.

## Outputs (`out/`)

| File | What |
|---|---|
| `evidence_v0.csv` | One row per record: sponsor class-A records, Polk lines, permit lines and the 2026 tenant check, each with its source and a coded use category |
| `decade_matrix_v0.csv` | Property x decade, 1880s to 2020s, with the use categories found |
| `proven_uses_v0.csv` | Per property, the uses it has carried: records, decades, first and last year, sources |
| `silence_map_v0.csv` | Decades with use evidence, 1910s to 2010s, before (sponsor records only) and after the new sources |
| `hbu_screen_v0.csv` | Best-proven use per property, today's status and an indicative rent range from the comps |
| `validation_v0.txt` | How the new sources compare with the hand-built reference timelines |
| `unassigned_v0.csv` | Lines whose street number could not be matched to a frontage parcel |

## Results so far

- 1,963 records joined: 326 sponsor, 943 Polk, 615 permit, 79 current.
- Decades with use evidence, 1910s to 2010s, average per building: 1.8 before, 3.4 after. 4 buildings are well
  documented (7+ decades), 32 partial, 43 still thin.
- On the three frontage reference timelines (3117, 3200, 3224), 12 of 13 coded Polk and permit rows agree with the
  hand-built decade categories.
- In 1920 to 1923, 17 of 50 frontage buildings with a listed business had food or drink and 12 had a trade shop.
  In October 2026, 10 of 44 occupied buildings have food or drink and none has a trade shop.

## Known limits

- Use coding is a keyword rule (`RULES` in `build_v0.py`). It should give way to the team's agreed category list
  and the extractor.
- A directory or permit number that is not a parcel in the export is assigned to the next parcel down the same
  side (`address_method` says so). The York Road crosswalk is not applied yet, so nothing before 1912 from Polk.
- The screen ranks uses by decades of evidence minus a penalty when the same use is common on the block side
  today. It is a conversation starter for the sponsor meeting, not a recommendation.

## AI use

Written with Claude on 18 October 2026. Review the code and spot-check outputs before merge.

Checked by: ____________________ Date: __________
