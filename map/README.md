# Greenmount corridor map

A map browser for the CSVs in this repo. No install step: `python3 map/app.py` and open
http://localhost:8765. `python3 map/app.py --check` loads the data, prints row counts and the
per-source layer table, and exits 1 if properties ≠ 699, incidents ≠ 17,387, or curated ≠ 7,891.

Markers are the 668 properties with coordinates, coloured by curated depth (0 / 1–9 / 10–24 / 25+).
Click one for a right-hand panel: key fields, a **History** timeline of curated incidents (oldest
first; dashed dots mark `circa`/`decade`/`range`/unset precision), the **Administrative feed** (newest
first, 50 at a time), people & businesses, registered IP, grant matches, and the two July 2026
baseline snapshots. Search matches addresses, owners, and subject names. **Focus area** draws the proposed first focus area from `map/focus_area.geojson`, a working outline traced
from `proposed-focus-area-phase1.png` (replace the file when the sponsor supplies an authoritative
one); **Focus area only** dims every marker outside it and zooms to it. Other toggles draw lot polygons
for the visible set; neighborhood bounds are empty in this export, so that layer draws nothing.

**Use history (team layer).** When `team/extractor/out/` exists, the 69 frontage parcels (2900 to 3299
Greenmount) get a **Use history** section above the curated history: chips for the uses the property has carried,
a decade grid from the 1870s to the 2020s (click a cell for its records), a coverage line saying which decades no
source has been read for yet, and the spans of use, each with its source rows and links. Rows from the sponsor's
records link down to the matching curated incident. **Colour by use** in the top bar recolours those properties by
the use found in a chosen decade (step with the arrows) or by the use found in the most decades; the other markers
fade. A hollow dashed marker means no record for that decade, which is not the same as vacant; a blue ring is a shop
front whose trade is not stated (a permit for "one store", a Sanborn "S"). Ten frontage records in the September export
were merged into a neighbouring parcel (`team/evidence/blocklot_gaps.csv`); the map points each to the parcel that
holds its history. The October 2026 refresh retired all ten ids (`property_id_crosswalk.csv`), so none of them is a marker any more. The layer is optional: without `team/extractor/out/` the map runs as
before and `--check` prints a note. Run `python3 team/extractor/extract.py` to rebuild it.

**Layer rule** (same as `START_HERE.ipynb` and `verify_claims.py`): a source is *administrative*
if it starts with `baltimore:` or is `sdat_assessments` / `sdat:owner`; everything else is
*curated*. That gives 7,891 / 9,496. Two sources cut against the "namespaced = administrative"
heuristic: `hud:cdbg` (39 rows) is namespaced but counted as curated, and `sdat_assessments`
(853) is a bare key but is an assessment roll, so administrative. Moving `hud:cdbg` would give
7,793. `stjohns_interments` (583) is curated but labelled **roster** in the UI.

Rows with a `sensitivity` flag are never dropped: they get a red badge and their summary sits
behind a "show" button. `rights` is shown as a chip when present. Only outbound calls are OSM tiles
and the Leaflet 1.9.4 CDN.
