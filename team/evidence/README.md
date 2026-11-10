# New use evidence for the Greenmount frontage (draft for review)

Sources the export holds only in part, collected for the 79 frontage records (69 parcels today; block sides 65 and
67 to 72).
`team/extractor/` reads all of them.

| File | Rows | What |
|---|---|---|
| `permit_cards_1924_1961.csv` | 671 | Transcription of the City's Master Index Cards, Building Permits (BRG48-53), one row per permit line |
| `polk_frontage_1912_1923.tsv` | 1,080 | Lines from the Baltimore city directories, 1912 to 1923, that give a Greenmount number from 2900 to 3299 |
| `polk_york_1901_1913.tsv` | 1,054 | Lines from the 1901 to 1913 directories that give a York Road number from 900 to 1149, before the renumbering (week 2) |
| `crosswalk_raw.json` | 549 | Name lines from the 1909, 1912, 1914 and 1915 directories used to match old and new numbers (week 2) |
| `york_crosswalk.csv` | 162 | Old York Road number to Greenmount number, with method and confidence; written by `team/extractor/crosswalk.py` (week 2) |
| `york_crosswalk_pairs.csv` | 30 | The matched pairs and sponsor statements behind the crosswalk (week 2) |
| `sanborn_frontage.csv` | 307 | One row per footprint on the 1915, 1928 and 1953 Sanborn sheets for the frontage (week 2) |
| `nr_inventory_frontage.csv` | 98 | The frontage entries of the Waverly Main Street Historic District nomination (B-5229) (week 2) |
| `blocklot_gaps.csv` | 20 | From the sponsor: export records with no block and lot of their own, merged into a neighbour or gone (week 2) |
| `city_archives_unfiled_pages_2026-10-26.csv` | 174 | From the sponsor: City Archives pages (BRG48-43-10) scanned but not filed on any building |
| `archive_unfiled_triage_2026-10-26.csv` | 174 | A suggested building for each unfiled page, from the filed pages either side; written by `triage_unfiled_pages.py` |

## Permit cards, 1924 to 1961

- Read one image at a time in the Maryland State Archives viewer, using the image ranges in the sponsor's City
  Archives finding guide (15 October). 114 images attempted: 108 transcribed (89 fronts, 19 backs), 4 failed to load
  (675-0656, 675-0661, 677-0864, 677-0871). 674-3873, 3874 and 3875 are rescans of cards already in the set.
- One row per permit line, with the card header (address as written, owner, occupancy class, stories, block, lot) on
  every row. `page_url` opens the card.
- Unreadable parts are marked `[?]`; nothing was guessed. `legibility` is high, medium or low per line.
- Side-street cards in the ranges are kept and marked in `address_normalized` (444 E 29th St, 2900 Barclay St,
  3105 Brentwood Ave).
- The 3212 card gives block 3881, not 3882 as the guide lists.

## Polk directories, 1912 to 1923

- Source: the archive.org text of the Baltimore city directories (identifiers `baltimorecitydir1912rlpo` to
  `baltimorecitydir1921rlpo`, `polksbaltimoreci1922rlpo`, `polksbaltimoreci1923rlpo`). 1909 and earlier use the old
  York Road numbers and are left for the address crosswalk; the 1912 and 1913 volumes have few Greenmount numbers in
  this range, so the new numbering reaches these blocks around 1913 to 1914.
- Extraction: every OCR line matching a number from 2900 to 3299 followed by "Greenmt av" (with OCR variants).
  Lines where the address follows `h`, `r` or `b` (home, rooms, boards) were dropped, as were employee-only lines
  (clerk, laborer, driver and similar), so what is left is mostly businesses and the people who ran them.
  `[h do]` means the person also lived at that address.
- The second half of each year is the classified business section, where the trade heading is lost; those lines
  carry a name and address only.
- This is raw OCR: names are often misspelled and some digits are misread. Check a line against the page image on
  archive.org before citing it.

## Polk directories under York Road, 1901 to 1913 (week 2)

- Same archive.org text as above (identifiers in `team/extractor/extract.py`, `POLK_ID`): 1901, 1903 to 1909, 1912
  and 1913. The 1902, 1910 and 1911 volumes are not in this set.
- Every line giving a York Road number from 900 to 1149 is kept, residents and businesses alike. The extractor codes
  a use only where a trade word appears.
- The numbers are the old ones. They reach a Greenmount parcel only through `york_crosswalk.csv`.

## York Road to Greenmount crosswalk (week 2)

- The new Greenmount numbers reach these blocks in the directories between 1912 and 1914. The old and new numbers
  do not map by a fixed offset, so the crosswalk is built from evidence (method in `team/extractor/crosswalk.py`):
  - **Sanborn sheets that print both numbers** (1915 and 1928) are the strongest anchors;
  - **sponsor statements** such as "old 1102 York Rd" in `property_incidents.csv`;
  - **Polk name matches**: the same person or firm at an old number in 1908 to 1913 and at a new number in 1914 to
    1917, on the same side of the street, with no clash of trade;
  - one hand-checked anchor (1029 to 3123, the Chemical Engine Co. No. 4 firehouse), with its reasoning in the script.
- Anchors that break the street order on their side are dropped (usually a person who moved). Numbers between two
  anchors are interpolated on the same side, never across a gap of more than 120 new numbers.
- Result: 42 anchors (high), 13 interpolated rows at medium and 107 at low confidence. Spot checks that hold:
  1102 to 3200, 1116 to 3224, 1027 to 3117, 1038 to 3126, 1047 to 3139. Treat any `low` row as a lead.

## Sanborn sheets, 1915, 1928 and 1953 (week 2)

- Read on the Library of Congress viewer, one sheet at a time (`loc_url` opens the sheet). 1915: sheets 710, 717 and
  718. 1928 and 1953: sheets 648, 654, 735 and 739 (the west side is in volume 6).
- One row per footprint: printed numbers, old numbers where printed (49 rows), side, stories, construction, the use
  label as printed (`use_label`) and spelled out (`use_expanded`), notes and legibility (267 high, 39 medium, 1 low).
- No map images are stored here. Do not publish the sheet images in this repo.

## National Register inventory, B-5229 (week 2)

- From the nomination PDF in the public reading library (`pricing-the-unpriced-reading`, `waverly/`), pages 14 to 41.
  One row per inventory entry on the frontage: construction date, stories, materials, style, historic names with
  their years, the use at the time of fieldwork (about 2011), contributing status and alterations.
- The historic tenant names come from the 1928 and 1937 directories, as the nomination says. "Use at nomination"
  is what the surveyors saw around 2011, not today.
- No entry was found for 3030, 3032 or 3218.

## Records with no block and lot (sponsor file, week 2)

- `blocklot_gaps.csv` came from the sponsor with the data export. Twelve records were merged into a neighbouring
  parcel on 25 or 30 September 2026; ten of them are on the frontage (2902, 2940, 3008, 3013, 3030, 3032, 3103, 3110,
  3124 and 3206). Eight are historic addresses on the east side of the 2900 block whose buildings are gone.
- The sponsor marks one merge "not verified": 3103 and 3031 may have been swapped, to be checked against the block
  and lot in SDAT (by hand). The permit card filed as "3101 Greenmount Ave (range 3101-3103; also 3031)" points the
  same way.
- Ask the sponsor before this file goes into the public repo.

## AI use

Collected and transcribed with Claude, 15 to 18 October 2026. A team member checks a sample of rows against the
source images before merge.

Checked by: ____________________ Date: __________

## Unfiled City Archives pages (26 October 2026)

- **Source.** The sponsor's list of pages from the City's revitalization files (BRG48-43-10) that are scanned but
  not attached to any building in `archive_scans.csv`. Of the 174, 122 sit inside a folder's filed range and 52 come
  after the last filed page.
- **The triage.** `triage_unfiled_pages.py` suggests a building for each page from the folder and the filed pages
  on either side. It writes the confidence and the reason on every row. The rule, most specific first:
  - a folder about one building gives that building (high);
  - the same building(s) on both neighbouring pages gives those (medium);
  - only a page before gives its building(s) (low).
  - The export files area-wide documents on one intersection record (Greenmount Ave and E 33rd St), so 107 pages
    read "area-wide document".
- **Not a filing.** Open the scan before filing or citing a page. `checked_by` and `filed_as` are blank for the
  person who does.
- **First to read.** Item 9 (the urban renewal plan), pages 4 to 29, all after the last filed page. On 26 October
  the sponsor said the plan bars taverns, not restaurants, and that a restaurant can get a liquor licence more
  easily. The explorer now says so, marked as still to confirm on these pages. Item 8 (the final Waverly plan,
  pages 28 to 49) is next.

