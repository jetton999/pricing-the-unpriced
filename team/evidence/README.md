# New use evidence for the Greenmount frontage (draft for review)

Two sources the export holds only in part, collected for the 79 frontage properties (block sides 65 and 67 to 72).

| File | Rows | What |
|---|---|---|
| `permit_cards_1924_1961.csv` | 671 | Transcription of the City's Master Index Cards, Building Permits (BRG48-53), one row per permit line |
| `polk_frontage_1912_1923.tsv` | 1,080 | Lines from the Baltimore city directories, 1912 to 1923, that give a Greenmount number from 2900 to 3299 |

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

## AI use

Collected and transcribed with Claude on 18 October 2026. A team member checks a sample of rows against the
source images before merge.

Checked by: ____________________ Date: __________
