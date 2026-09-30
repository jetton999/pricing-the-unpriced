# The research desk

Some of the best sources for this corridor sit behind the sponsor's personal
accounts: Newspapers.com, MyHeritage, and Maryland Land Records. Their terms
don't allow sharing a login, and the clippings can only be read by eye, so
instead of accounts you get a desk. You ask; the sponsor's research agent runs
the search overnight on the sponsor's own machine, files what it finds into
the knowledge base with a citation on every row, and posts the answer back to
you.

## How to ask

Open a **[Lookup request](https://github.com/jetton999/pricing-the-unpriced/issues/new?template=lookup-request.yml)**.
One property per request. Give it:

- the address (and the old York Road number if you have one; the street was
  renumbered around 1910);
- the names, businesses or terms, one per line;
- a year range;
- what you are trying to establish. This is the part that matters most. "Was
  Wagner's the same operator as Eddie's" gets a better answer than "everything
  about 3313".

## What happens

The desk runs every night around 2am Eastern, on the sponsor's Mac. For each
open request, oldest first, it:

1. searches the sources you named (or all of them), using the methods the
   sponsor's own research uses: address and name together, the pre-1910
   address ladder, obituary and marriage facets, deed recitals to walk a title
   chain back past 1972;
2. reads what it finds and files each finding as a row in the knowledge base:
   one event, dated, graded (`verified`, `probable`, `possible`), cited to the
   page or instrument, on the property it belongs to;
3. comments on your request with a plain summary, the rows it filed and their
   citations, and what came back empty;
4. labels the request `lookup:done`, or `lookup:needs-info` with a question.

The rows reach this repository the next time the sponsor re-exports the data.
Until then the comment on your request is the record, and it carries the same
citations.

## Limits, stated up front

- About ten requests a night. Newspapers.com only lets a clipping be read as
  an image, and its viewer is slow.
- The desk searches what you ask for. It does not run the whole deep-dive
  playbook on a property; ask for that explicitly and expect it to take more
  than one night.
- Nothing is invented. A search that finds nothing is reported as nothing,
  and a claim the desk cannot pin to a page is graded `possible`, not `verified`.
- The desk runs on the sponsor's own computer. If it is off or Claude is closed at 2am, the queue runs when it next opens, so an answer can slip a day.

## Free sources you can use directly

You do not need the desk for these. Each has a method in the sponsor's
playbook; ask on the weekly if you want it.

| Source | What it holds | Where |
|---|---|---|
| Chronicling America | Free full-text newspapers to 1963, with an API | loc.gov |
| Polk city directories | The business at each address, year by year; free through 1923 | archive.org (`_djvu.txt` per volume) |
| Sanborn fire-insurance maps | Footprint, material and use per building; 1915, 1928, 1953 | Library of Congress, IIIF tiles |
| National Register nominations | Address-by-address inventory of the Waverly district (B-5229) | NPS |
| US census 1950 | Every household, free, by enumeration district | 1950census.archives.gov (county = "Baltimore", not "Baltimore City") |
| FamilySearch | Census 1900-1940 and vitals; free account | familysearch.org |
| FindAGrave | Burials, dates, family plots | findagrave.com |
| Maryland Business Express | Every Maryland company: formation, agent, forfeiture | egov.maryland.gov/businessexpress |
| USPTO trademark search | Marks by owner name and address; first-use dates | tmsearch.uspto.gov |
| Baltimore City Archives on Flickr | 1922 DPW street views and more, public | flickr.com/photos/baltimore_city_archives |
| SDAT and Open Baltimore | Sales, assessments, permits, vacancy, violations, liquor licenses | opendata.maryland.gov, data.baltimorecity.gov |
| Google Street View | The present exterior of every building, and past captures | maps.google.com |
