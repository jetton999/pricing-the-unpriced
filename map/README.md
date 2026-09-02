# Greenmount corridor map

A map browser for the CSVs in this repo. No install step: `python3 map/app.py` and open
http://localhost:8765. `python3 map/app.py --check` loads the data, prints row counts and the
per-source layer table, and exits 1 if properties ≠ 1,874, incidents ≠ 20,308, or curated ≠ 3,602.

Markers are the 1,791 properties with coordinates, coloured by curated depth (0 / 1–9 / 10–24 / 25+).
Click one for a right-hand panel: key fields, a **History** timeline of curated incidents (oldest
first; dashed dots mark `circa`/`decade`/`range`/unset precision), the **Administrative feed** (newest
first, 50 at a time), people & businesses, registered IP, grant matches, and the two July 2026
baseline snapshots. Search matches addresses, owners, and subject names. Toggles draw lot polygons
for the visible set; neighborhood bounds are empty in this export, so that layer draws nothing.

**Layer rule** (same as `START_HERE.ipynb` and `verify_claims.py`): a source is *administrative*
if it starts with `baltimore:` or is `sdat_assessments` / `sdat:owner`; everything else is
*curated*. That gives 3,602 / 16,706. Two sources cut against the "namespaced = administrative"
heuristic: `hud:cdbg` (41 rows) is namespaced but counted as curated, and `sdat_assessments`
(3,064) is a bare key but is an assessment roll, so administrative. Moving `hud:cdbg` would give
3,561. `stjohns_interments` (583) is curated but labelled **roster** in the UI.

Rows with a `sensitivity` flag are never dropped: they get a red badge and their summary sits
behind a "show" button. `rights` is shown as a chip when present. Only outbound calls are OSM tiles
and the Leaflet 1.9.4 CDN.
