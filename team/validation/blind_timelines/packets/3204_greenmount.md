# Reading packet: 3204 Greenmount Ave (property_id 755)

Block side: west side, 3200 block.

Build the timeline from the sources below, read at the source. Write one row per use and period in
`../blind_timelines.csv`. Do not open the explorer page, `team/extractor/out/` or the map sidebar for this
address until your rows are committed.

## Where to read

- **Before about 1914 this block was numbered as York Road.** The team's crosswalk gives the old number as 1104 (high confidence, method: anchor). Check it against a Sanborn sheet before relying on it.
- **Polk city directories** (street guide, under York Road and Greenmount Avenue): [1901](https://archive.org/details/rlpolkcosbaltimo1901rlpo), [1903](https://archive.org/details/rlpolkcosbaltimo1903rlpo), [1904](https://archive.org/details/rlpolkcosbaltimo1904rlpo), [1905](https://archive.org/details/baltimorecitydir1905rlpo), [1906](https://archive.org/details/baltimorecitydir1906rlpo), [1907](https://archive.org/details/baltimorecitydir1907rlpo), [1908](https://archive.org/details/baltimorecitydir1908rlpo), [1909](https://archive.org/details/baltimorecitydir1909rlpo), [1912](https://archive.org/details/baltimorecitydir1912rlpo), [1913](https://archive.org/details/baltimorecitydir1913rlpo), [1914](https://archive.org/details/baltimorecitydir1914rlpo), [1915](https://archive.org/details/baltimorecitydir1915rlpo), [1917](https://archive.org/details/baltimorecitydir1917rlpo), [1918](https://archive.org/details/baltimorecitydir1918rlpo), [1920](https://archive.org/details/baltimorecitydir1920rlpo), [1921](https://archive.org/details/baltimorecitydir1921rlpo), [1922](https://archive.org/details/polksbaltimoreci1922rlpo), [1923](https://archive.org/details/polksbaltimoreci1923rlpo).
- **Sanborn maps** for this block side: [Sanborn 1915 sheet 717](https://www.loc.gov/resource/g3844bm.g3844bm_g03573191507/?sp=58), [Sanborn 1928 sheet 654](https://www.loc.gov/resource/g3844bm.g3844bm_g03573192806/?sp=58), [Sanborn 1953 sheet 654](https://www.loc.gov/resource/g3844bm.g3844bm_g03573195306/?sp=49).
- **Building permit index cards** (City Archives, BRG48-53), folders holding this block side: [1](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0589.html), [2](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0647.html), [3](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0648.html), [4](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0650.html), [5](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0651.html), [6](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0652.html), [7](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0654.html), [8](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0655.html), [9](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0657.html), [10](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0658.html), [11](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0659.html), [12](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0660.html), [13](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0662.html), [14](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0663.html), [15](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0664.html), [16](https://mdhistory.msa.maryland.gov/bca_brg48/bca000675/html/brg48_bca675-0665.html).
- **National Register nomination** for Waverly Main Street (B-5229), inventory entry for this address: [file](https://github.com/jetton999/pricing-the-unpriced-reading/blob/main/waverly/NR-Waverly-Main-Street-Historic-District-NPS-13001020-B-5229.pdf).
- **City revitalization files, 1970s** (City Archives, BRG48-43-10): survey sheets and photographs by address.
- **Sponsor records**: 35 rows for property_id 755 in `property_incidents.csv`.
- Anything else you find (newspapers, photographs, licences). Cite it in `source` and `source_ref`.

## What to write

- One row for each use over a run of years: `start_year`, `end_year`, `use` in your own words, the occupant if named.
- `use_category`: one of `retail goods`, `food & drink`, `personal services`, `automotive`, `entertainment & assembly`, `institutional & religious`, `office`, `production & light industry`, `residential`, `vacant`.
- `stated_or_inferred`: `stated` if the source names the use, `inferred` if you read it from a name or a building type.
- `source` and `source_ref`: enough for a second person to find the line (volume and page, sheet, card image).
- Leave years with no evidence out. A gap is an answer.
- `built_by`: your initials. `saw_extractor_output`: `no`, if that is true for this address.
