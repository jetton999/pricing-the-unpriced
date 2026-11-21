# Two-coder check of the AI-assisted codes

Two things in the repo were coded with AI assistance and have not been checked by a person (sponsor's review,
17 November 2026):

1. **The use today** of the 52 Greenmount parcels in the back-test (`../outcomes_other_greenmount_2026-10.csv`). So
   few pairs carry the back-test's result that one coding error can change it.
2. **The kind of use the extractor gave each history record** (`team/extractor/out/evidence.csv`), by keyword rules
   over text that is often narrative prose.

This folder holds the sheets for two team members to code both independently, and the script that reports how often
they agree with each other and with the codes in the repo. It cannot be done by an AI assistant: the point is a
check by people.

## What to do

1. **Two different people** each take one sheet of each kind: `outcomes_coder_A.csv` and `history_coder_A.csv` for
   one, the `_B` files for the other. Do not open the other person's sheet, `history_key.csv`,
   `../outcomes_other_greenmount_2026-10.csv`, `team/extractor/out/` or the explorer until both sheets are committed.
2. **Use today** (52 rows). For each row, read the sponsor's October 2026 storefront summary: `storefront_assessments.csv`
   at the top of the repo, the row with the same `property_id`, column `summary`. In `uses_today` write every
   kind of use at the address today, separated by " ; ", from this list: food & drink, retail goods, personal
   services, automotive, entertainment & assembly, institutional & religious, office, production & light industry,
   residential, vacant. Write `none` if none applies. `sure`: yes or no.
3. **History records** (200 rows). Read `text` (and the source, if you want to open it). In `use_category` write the
   one kind of use the text states for the building, from the same list, or `no use stated`. Code what the record
   says for its own date, not a later event the same sentence mentions. `use_is_dated_to_this_year`: yes or no.
   `record_is_about_this_address`: yes, no or cannot tell.
4. On every row fill `coded_by` (your initials), `coded_on` and `saw_other_codes` = `no`, if that is true.
5. Commit both sheets, then run `python3 team/validation/two_coder/score_agreement.py`. It writes `out/agreement.md`
   (the figures to report), `out/disagreements.csv` (rows for a third person to settle) and
   `out/outcomes_agreed.csv`.
6. Rerun the back-test on the agreed codes:
   `PTU_OUTCOMES=team/validation/two_coder/out/outcomes_agreed.csv python3 team/validation/backtest.py`. It writes
   `../out/backtest_v2_recoded.md` and leaves the files of record alone. Report both results.

## The history sample

200 of the history records the extractor coded with a use: 100 drawn at random from the sponsor's records, where
the review found most of the coding errors, and 100 from the other sources (directories, permit cards, Sanborn maps,
the National Register inventory, the 1970s files). The draw is fixed by the seed in `make_sheets.py`; `sample.json`
records it. The two groups are reported separately, and weighted back to all coded records for a single figure.

## Files

| File | What |
|---|---|
| `make_sheets.py` | Draws the history sample and writes the blank sheets. It never overwrites a sheet someone has started |
| `outcomes_coder_A.csv`, `outcomes_coder_B.csv` | The 52 parcels, with where to read the sponsor's summary and no code |
| `history_coder_A.csv`, `history_coder_B.csv` | The 200 records, with their text and no code |
| `history_key.csv` | Which evidence row each sample id is and what the extractor coded it as. For the scoring script only |
| `sample.json` | The seed, the rule and the sizes of the pools |
| `score_agreement.py` | Agreement, Cohen's kappa, the share matching the repo's codes, and precision by kind of use |
| `test_two_coder.py` | Tests of the draw and of the scoring arithmetic |
