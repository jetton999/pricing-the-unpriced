# Blind reference timelines

**Status, 10 November 2026: the kit is ready; the four timelines are not started.** They have to be read and
written by a person. Nothing in this folder is a timeline yet.

## Why

The extractor is checked against four reference timelines from week 1. Those were built from the same sponsor
records the extractor reads, so only the "new sources only" row of `team/extractor/out/validation.md` is an
independent test. The research plan asks for four more, built blind: by someone who has not seen what the
extractor says about those parcels.

## The four parcels

| Parcel | Packet | Timeline |
|---|---|---|
| 2934 Greenmount Ave (west side, 2900 block) | `packets/2934_greenmount.md` | to do |
| 3011 Greenmount Ave (east side, 3000 block) | `packets/3011_greenmount.md` | to do |
| 3111 Greenmount Ave (east side, 3100 block) | `packets/3111_greenmount.md` | to do |
| 3204 Greenmount Ave (west side, 3200 block) | `packets/3204_greenmount.md` | to do |

They were drawn once, by `make_kit.py`: one parcel from each hundred block, at random with a fixed seed, among
the 59 of 69 frontage parcels that are not already a reference timeline and that the sponsor's storefront
assessment does not class as residential. The rule, the seed and the result are in `sample.json`, and a test
checks that the draw repeats. Do not redraw: a second draw made after looking at the result is no longer blind.

## How to build one

1. **Check that you can.** You should not have looked at this address in the explorer, in
   `team/extractor/out/` or in the map sidebar. If you have, hand the parcel to someone who has not.
2. **Read the packet** for the address. It lists where to read (directory volumes, map sheets, permit card
   folders, the National Register nomination, the 1970s files, the sponsor's records) and nothing about what
   is there.
3. **Write your rows** in `blind_timelines.csv`: one row per use and run of years, in your own words, with a
   category from the list in the packet and a source reference a second person could follow. Leave out years
   with no evidence. Put your initials in `built_by` and `no` in `saw_extractor_output`, if that is true.
4. **Commit your rows before you open the extractor's output.** The commit time is the record that the
   timeline came first.
5. **Score:** `python score_blind.py` writes `out/blind_validation.md`. It refuses to run until all four
   parcels have rows and every row is marked as built blind.

## What the score means

The same three measures as the week-1 check (`validate()` in `team/extractor/extract.py`): the share of
reference uses the extractor found, the same share where a source covers those years, and the share of the
extractor's coded records that agree with the reference category. Each is given for all sources and for the
sources other than the sponsor's records. Four parcels is a small sample: it can show that something is badly
wrong, not measure a rate precisely.

## What the kit took from the extractor

Two things, for location only: the list of frontage parcels with their block sides, and which directory
volumes, map sheets and permit card images cover a block side. No coded use and no occupant name: a test
checks that no packet contains an occupant the extractor found at that parcel.

## AI assistance

The draw, the packets, the scorer and the tests were prepared with AI assistance (Claude). The timelines
cannot be: the assistant has seen the extractor's output for every frontage parcel, so anything it wrote
would not be blind.

Run the checks with `python -m unittest` in this folder.
