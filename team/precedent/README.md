# Precedent case: the City's Waverly commercial revitalization files, 1973-1984 (draft for review)

The sponsor's scope for this fall: "an indexed summary of the 31 folders plus the interventions table. The before
and after comparison can wait." Everything here is built from `archive_scans.csv` (BRG48-43-10, DHCD's Waverly
commercial revitalization files) at the repo root.

| File | Rows | What |
|---|---|---|
| `folder_index.csv` | 31 | One row per folder: title, group (from the week-2 progress report), years, distinct pages and pages by type, document types, buildings and businesses named, the plan or work it records, key pages, and how many pages have only generic or truncated captions |
| `interventions.csv` | 79 | One row per intervention on a building or the street: address, business, year, type (streetscape, sign, design review, facade renovation, parking, loan and others), description, funding, status, the scan pages behind it, and `report_id`, the matching entry of the week-2 progress report's 14-row draft |
| `precedent_memo_draft.md` | | The case write-up: what the programme was, what the folders hold, which buildings were touched, how the City worked with the merchants, gaps, and careful use for the highest-and-best-use work |

## Method

- Pages are counted as distinct `item` + `page`, not rows (AGENTS.md). The 31 folders hold 1,692 distinct pages.
- Every statement comes from the one-line captions. No scan image was opened, so open a page's `scan_url` before
  citing it. References are folder-page: 20-3 is BRG48-43-10-20, page 3.
- `status` keeps the evidence for its value: `completed (inferred: ...)` names the caption it rests on.
- The extractor reads `interventions.csv` for the 1970s businesses at each address (`dhcd_1970s` rows). Businesses
  given as "former", "ex-" or "vacant" are not coded to a use.

## What the captions show and do not show

- The City paid for the public works (streetscape, median, parking lot: about $1.1 million stated in the captions)
  and gave design help at no cost. Owners were asked to fix their facades within two years under the urban-renewal
  design standards, with low-interest loans on offer.
- No caption mentions a facade grant or shows a loan closing.
- 106 pages have only generic captions and 61 captions are cut off. These need a person to read the scans before
  the memo's counts are final (section 5 of the memo lists them by folder).

## AI use

Indexed and drafted with Claude on 18 October 2026 from the captions only. A team member reads the key pages and a
sample of the generic ones before merge.

Checked by: ____________________ Date: __________
