# Reference files from the week-2 progress report

Copied on 18 October 2026 from the team Drive (`Week02_2026-10-19/02_data`), where the week-2 progress report keeps
them. They are inputs for testing, not outputs of this folder. The authoritative copies arrive with that report's
pull request (`team/week2/`); when it lands, point the tests there and delete these.

| File | Rows | Used for |
|---|---|---|
| `reference_occupants.csv` | 30 | The named occupants of the four reference timelines. `extract.py` checks whether each one on a frontage parcel (24) is named at its parcel within its years: the second test in `out/validation.md` |
| `york_road_crosswalk.csv` | 23 | Old York Road to Greenmount pairs read from the sponsor's records. `crosswalk.py` compares them with `team/evidence/york_crosswalk.csv` and writes `team/evidence/york_crosswalk_reconciliation.csv` |
