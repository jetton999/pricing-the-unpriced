"""Week 1: focus-area inventory and use-record classification.

    python3 team/week1/focus_area.py

Standard library only. Reads the CSVs at the repo root and writes to team/week1/out/:
  focus_area.geojson            the working boundary (APPROXIMATE, see below); copy it to
                                map/focus_area.geojson when it changes
  focus_area_properties.csv     one row per property inside it
  use_records.csv               every curated record in the focus area, classified

The boundary is hand-traced from proposed-focus-area-phase1.png (sponsor commit c5b735c,
2026-10-05): E 33rd St south to E 29th St, Barclay St to Old York Rd, the whole St. John's
cemetery block, and only the west side of Greenmount below E 30th St. It is a working
approximation until the sponsor supplies an authoritative property list or polygon.
"""
import collections
import csv
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent / "out"
csv.field_size_limit(10**9)

# Boundary vertices traced in pixels on the sponsor PNG, then converted to lon/lat with two
# anchors read from properties.csv (Greenmount centreline; E 33rd and E 29th centrelines).
_PX = [(235, 180), (700, 160), (730, 200), (705, 300), (690, 480), (660, 620), (620, 760),
       (625, 825), (700, 860), (790, 920), (795, 1010), (765, 1105), (560, 1100), (545, 1130),
       (540, 1380), (520, 1400), (225, 1400), (225, 1150), (260, 1080), (350, 980), (420, 935),
       (425, 750), (385, 745), (380, 500), (235, 500)]
BOUNDARY = [(round(-76.6094 + (x - 540) * 5.3e-6, 6), round(39.3283 - (y - 210) * 3.95e-6, 6))
            for x, y in _PX]  # (lon, lat)

# Properties with no coordinates are placed by house number on Greenmount Ave.
def _by_address(number, street):
    if street != "Greenmount Ave" or number is None:
        return False
    return 3000 <= number < 3300 or (2900 <= number < 3000 and number % 2 == 0)

# --- use-record classification -------------------------------------------------------------
# A: the record states what one building was used for, or names a business trading there.
# B: the record may mention a use but has to be read: news and civic items, block-level maps
#    (a Sanborn sheet covers several blocks and its uses are in the image, not the row), atlas
#    landholder plates, and neighbourhood studies filed on one address.
# C: the record is about ownership, burial or an event, not use.
A_SOURCES = {"polk", "census_directory"}
A_CATEGORIES = {"directory", "advertisement", "commerce", "commercial", "construction",
                "institution"}
C_CATEGORIES = {"interment", "sale", "obituary", "death", "crime", "public_investment", "land"}


def is_admin(source):
    return source.startswith("baltimore:") or source in ("sdat_assessments", "sdat:owner")


def use_class(row, has_business_link):
    if has_business_link or row["source"] in A_SOURCES or row["category"] in A_CATEGORIES:
        return "A"
    if row["category"] in C_CATEGORIES:
        return "C"
    return "B"


def load(name):
    with open(ROOT / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def inside(lon, lat, poly=BOUNDARY):
    hit = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def split_address(address):
    m = re.match(r"^(\d+)(?:\s+1/2)?\s+(.*?), Baltimore", address)
    return (int(m.group(1)), m.group(2)) if m else (None, None)


def in_focus(prop):
    if prop["latitude"]:
        return inside(float(prop["longitude"]), float(prop["latitude"])), "coordinates"
    return _by_address(*split_address(prop["address"])), "address"


def main():
    OUT.mkdir(exist_ok=True)
    props, incidents = load("properties.csv"), load("property_incidents.csv")
    subjects = {s["id"]: s for s in load("subjects.csv")}
    links = load("incident_subjects.csv")
    tours = {t["property_id"] for t in load("matterport_tours.csv")}
    pages = collections.defaultdict(set)
    for a in load("archive_scans.csv"):
        pages[a["property_id"]].add((a["item"], a["page"]))

    curated = [r for r in incidents if not is_admin(r["source"])]
    print(f"layer split: {len(curated):,} curated / {len(incidents) - len(curated):,} administrative")

    biz_by_incident = collections.defaultdict(list)
    for l in links:
        s = subjects.get(l["subject_id"])
        if l["relationship"] == "operated_at" and s and s["subject_type"] == "business":
            biz_by_incident[l["property_incident_id"]].append(s["name"])

    focus = {}
    for p in props:
        hit, how = in_focus(p)
        if hit:
            focus[p["id"]] = (p, how)
    print(f"focus area: {len(focus)} properties "
          f"({sum(1 for _, h in focus.values() if h == 'address')} placed by address)")

    rec_rows, per = [], collections.defaultdict(collections.Counter)
    seen_pairs = collections.defaultdict(set)   # (property, year, business) -> sources
    names, years = collections.defaultdict(set), collections.defaultdict(list)
    for r in curated:
        pid = r["property_id"]
        if pid not in focus:
            continue
        biz = biz_by_incident.get(r["id"], [])
        cls = use_class(r, bool(biz))
        per[pid][cls] += 1
        per[pid]["flagged"] += bool(r["sensitivity"])
        names[pid].update(biz)
        for b in biz:
            seen_pairs[(pid, r["occurred_at"][:4], b)].add(r["source"])
        year = r["occurred_at"][:4]
        if cls == "A" and year.isdigit():
            years[pid].append(int(year))
        rec_rows.append({"incident_id": r["id"], "property_id": pid,
                         "address": focus[pid][0]["address"].split(",")[0], "year": year,
                         "date_precision": r["date_precision"], "source": r["source"],
                         "category": r["category"], "use_class": cls,
                         "businesses": "; ".join(biz), "evidence_status": r["evidence_status"],
                         "sensitivity": r["sensitivity"], "summary": r["summary"]})

    prop_rows = []
    for pid, (p, how) in focus.items():
        c = per[pid]
        total = c["A"] + c["B"] + c["C"]
        price = float(p["last_sale_price"] or 0)
        prop_rows.append({
            "property_id": pid, "address": p["address"].split(",")[0],
            "block_side_id": p["block_side_id"], "placed_by": how,
            "zoning_code": p["zoning_code"].strip(), "year_built": p["year_built"],
            "structure_sqft": p["structure_sqft"], "vacancy_indicator": p["vacancy_indicator"],
            "has_active_business": p["has_active_business"], "owner_name": p["owner_name"],
            "last_sale_price": int(price) if price > 0 else "",
            "last_sale_date": p["last_sale_date"][:10] if price > 0 else "",
            "curated_records": total, "use_A_states_use": c["A"], "use_B_read_needed": c["B"],
            "use_C_not_use": c["C"], "distinct_businesses": len(names[pid]),
            "first_use_year": min(years[pid]) if years[pid] else "",
            "last_use_year": max(years[pid]) if years[pid] else "",
            "sensitivity_flagged": c["flagged"], "archive_pages": len(pages[pid]),
            "matterport_tour": "yes" if pid in tours else "",
            "extractor_ready": "yes" if len(names[pid]) >= 3 and c["A"] >= 5 else "",
        })
    prop_rows.sort(key=lambda r: (-r["use_A_states_use"], r["address"]))

    for name, rows in (("focus_area_properties.csv", prop_rows), ("use_records.csv", rec_rows)):
        with open(OUT / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    geo = {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"name": "Proposed first focus area (working approximation)",
                       "traced_from": "proposed-focus-area-phase1.png @ c5b735c",
                       "status": "approximate; awaiting sponsor property list"},
        "geometry": {"type": "Polygon", "coordinates": [[list(v) for v in BOUNDARY + BOUNDARY[:1]]]}}]}
    (OUT / "focus_area.geojson").write_text(json.dumps(geo, indent=1) + "\n", encoding="utf-8")

    n = lambda f: sum(1 for r in prop_rows if f(r))
    tot = collections.Counter()
    for c in per.values():
        tot.update(c)
    print(f"  with any curated record: {n(lambda r: r['curated_records'] >= 1)}"
          f" | >=10: {n(lambda r: r['curated_records'] >= 10)}"
          f" | >=25: {n(lambda r: r['curated_records'] >= 25)}")
    print(f"  curated records: {len(rec_rows):,}  A={tot['A']:,}  B={tot['B']:,}  C={tot['C']:,}"
          f"  sensitivity-flagged={tot['flagged']}")
    twice = sum(1 for v in seen_pairs.values() if {"whitepaper", "newspapers_com"} <= v)
    print(f"  business-years recorded by both a white paper and a clipping: {twice}"
          f" of {len(seen_pairs)} (count once, not twice)")
    print(f"  with >=1 class-A record: {n(lambda r: r['use_A_states_use'] >= 1)}"
          f" | extractor-ready (>=3 businesses and >=5 class-A): {n(lambda r: r['extractor_ready'])}")
    print(f"  vacant: {n(lambda r: r['vacancy_indicator'] == 'true')}"
          f" | active business: {n(lambda r: r['has_active_business'] == 'true')}"
          f" | block sides: {len({r['block_side_id'] for r in prop_rows if r['block_side_id']})}"
          f" | Matterport: {n(lambda r: r['matterport_tour'])}"
          f" | with archive pages: {n(lambda r: r['archive_pages'])}")


if __name__ == "__main__":
    main()
