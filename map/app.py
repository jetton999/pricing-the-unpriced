#!/usr/bin/env python3
"""
Map browser for the Greenmount corridor knowledge base.

Standard library only. Loads the CSVs from the repo root (one level up from this
file), builds in-memory indexes, and serves a Leaflet page plus a small JSON API.

    python3 map/app.py            # serve on http://localhost:8765
    python3 map/app.py --check    # load, print counts + layer split, exit 1 on mismatch
"""
import collections
import csv
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

csv.field_size_limit(sys.maxsize)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = 8765

EXPECTED_PROPERTIES = 1874
EXPECTED_INCIDENTS = 20308
EXPECTED_CURATED = 3602

# ---------------------------------------------------------------------------
# Layer rule. Identical to START_HERE.ipynb cell 3 and verify_claims.py.
#
# Administrative = every `baltimore:*` feed, plus the two SDAT feeds
# (`sdat_assessments` is a bare key but is a machine-ingested assessment roll,
# and `sdat:owner` is the namespaced owner feed). Everything else is curated.
# This is the only rule that reproduces the README's 3,602 curated rows.
# `hud:cdbg` (41 rows) looks namespaced but is counted as curated by the
# sponsor; see map/README.md.
# ---------------------------------------------------------------------------
ADMIN_PREFIXES = ("baltimore:",)
ADMIN_EXACT = {"sdat_assessments", "sdat:owner"}
ROSTER_SUFFIX = "_interments"


def layer_of(source):
    source = source or ""
    if source.startswith(ADMIN_PREFIXES) or source in ADMIN_EXACT:
        return "administrative"
    return "curated"


def source_kind(source):
    """UI label: 'roster' for cemetery rosters, else the layer name."""
    if (source or "").endswith(ROSTER_SUFFIX):
        return "roster"
    return layer_of(source)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def rows(filename):
    with open(os.path.join(ROOT, filename), newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def parse_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text


def num(text):
    """Best-effort numeric conversion for CSV cells; leaves strings alone."""
    if text is None or text == "":
        return None
    try:
        if "." in text or "e" in text.lower():
            return float(text)
        return int(text)
    except ValueError:
        return text


def boolish(text):
    if text == "true":
        return True
    if text == "false":
        return False
    return None if text == "" else text


def ring_is_clockwise(ring):
    area = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        area += (x2 - x1) * (y2 + y1)
    return area > 0


def esri_to_geojson(obj):
    """Esri {"rings": [...]} -> GeoJSON Polygon / MultiPolygon.

    Esri outer rings are clockwise, holes counter-clockwise. A hole is attached
    to the most recent outer ring.
    """
    if not isinstance(obj, dict) or "rings" not in obj:
        return None
    polys = []
    for ring in obj["rings"]:
        if len(ring) < 4:
            continue
        if ring_is_clockwise(ring) or not polys:
            polys.append([ring])
        else:
            polys[-1].append(ring)
    if not polys:
        return None
    if len(polys) == 1:
        return {"type": "Polygon", "coordinates": polys[0]}
    return {"type": "MultiPolygon", "coordinates": polys}


class Corpus:
    def __init__(self):
        self.properties = {}
        self.incidents = {}
        self.incidents_by_property = collections.defaultdict(list)
        self.subjects = {}
        self.subject_links_by_incident = collections.defaultdict(list)
        self.properties_by_subject = collections.defaultdict(set)
        self.ips_by_property = collections.defaultdict(list)
        self.unmatched_ips = []
        self.grants_by_property = collections.defaultdict(list)
        self.baselines_by_property = collections.defaultdict(list)
        self.neighborhoods = []
        self.source_counts = collections.Counter()
        self.curated_count = collections.Counter()
        self.admin_count = collections.Counter()
        self.notes = []
        self.load()

    def load(self):
        for p in rows("properties.csv"):
            self.properties[p["id"]] = p

        for r in rows("property_incidents.csv"):
            self.incidents[r["id"]] = r
            self.incidents_by_property[r["property_id"]].append(r)
            self.source_counts[r["source"]] += 1
            if layer_of(r["source"]) == "curated":
                self.curated_count[r["property_id"]] += 1
            else:
                self.admin_count[r["property_id"]] += 1

        for s in rows("subjects.csv"):
            self.subjects[s["id"]] = s

        for link in rows("incident_subjects.csv"):
            iid = link["property_incident_id"]
            self.subject_links_by_incident[iid].append(link)
            inc = self.incidents.get(iid)
            if inc is not None:
                self.properties_by_subject[link["subject_id"]].add(inc["property_id"])

        for ip in rows("registered_ips.csv"):
            if ip["property_id"]:
                self.ips_by_property[ip["property_id"]].append(ip)
            else:
                self.unmatched_ips.append(ip)

        for g in rows("grant_program_matches.csv"):
            self.grants_by_property[g["property_id"]].append(g)

        for b in rows("baseline_snapshots.csv"):
            self.baselines_by_property[b["property_id"]].append(b)

        self.neighborhoods = list(rows("neighborhoods.csv"))

        # Pre-sort incidents per property once.
        for pid, lst in self.incidents_by_property.items():
            lst.sort(key=lambda r: r["occurred_at"][:19])

        self.points_geojson = self.build_points()
        self.neighborhoods_geojson = self.build_neighborhoods()
        self.search_index = self.build_search_index()

    # ------------------------------------------------------------------
    def build_points(self):
        features = []
        for pid, p in self.properties.items():
            if not p["latitude"] or not p["longitude"]:
                continue
            features.append({
                "type": "Feature",
                "id": int(pid),
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(p["longitude"]), float(p["latitude"])],
                },
                "properties": {
                    "id": int(pid),
                    "address": p["address"],
                    "zoning_code": p["zoning_code"],
                    "land_use": p.get("land_use", ""),
                    "year_built": num(p["year_built"]),
                    "structure_sqft": num(p["structure_sqft"]),
                    "dwelling_units": num(p["dwelling_units"]),
                    "vacancy_indicator": boolish(p["vacancy_indicator"]),
                    "vacant_notice_status": p["vacant_notice_status"],
                    "owner_name": p["owner_name"],
                    "owner_type": p["owner_type"],
                    "assessed_value": num(p["assessed_value"]),
                    "last_sale_price": num(p["last_sale_price"]),
                    "last_sale_date": p["last_sale_date"],
                    "curated_count": self.curated_count.get(pid, 0),
                    "administrative_count": self.admin_count.get(pid, 0),
                    "registered_ip_count": len(self.ips_by_property.get(pid, [])),
                    "block_side_id": num(p["block_side_id"]),
                    "census_tract": p["census_tract"],
                },
            })
        return {"type": "FeatureCollection", "features": features}

    def build_neighborhoods(self):
        features = []
        for n in self.neighborhoods:
            bounds = parse_json(n["bounds"])
            geom = None
            if isinstance(bounds, dict):
                if "rings" in bounds:
                    geom = esri_to_geojson(bounds)
                elif bounds.get("type") in ("Polygon", "MultiPolygon"):
                    geom = bounds
                elif bounds.get("type") == "Feature":
                    geom = bounds.get("geometry")
            if geom is None:
                continue
            features.append({
                "type": "Feature",
                "id": int(n["id"]),
                "geometry": geom,
                "properties": {"id": int(n["id"]), "name": n["name"]},
            })
        if not features:
            self.notes.append(
                "neighborhoods.csv: `bounds` is empty or unparseable for all %d rows; "
                "/api/neighborhoods returns an empty collection." % len(self.neighborhoods))
        return {"type": "FeatureCollection", "features": features}

    def build_search_index(self):
        """List of (lowercased haystack, kind, label, property_id)."""
        index = []
        for pid, p in self.properties.items():
            if p["address"]:
                index.append((p["address"].lower(), "address", p["address"], pid))
            if p["owner_name"]:
                index.append((p["owner_name"].lower(), "owner", p["owner_name"], pid))
        for sid, s in self.subjects.items():
            for pid in self.properties_by_subject.get(sid, ()):
                if pid in self.properties:
                    index.append((s["name"].lower(), s["subject_type"] or "subject",
                                  s["name"], pid))
        return index

    def search(self, q, limit=20):
        q = (q or "").strip().lower()
        if not q:
            return []
        seen = set()
        out = []
        # Prefix matches first, then substring matches.
        for pass_no in (0, 1):
            for hay, kind, label, pid in self.search_index:
                hit = hay.startswith(q) if pass_no == 0 else (q in hay and not hay.startswith(q))
                if not hit:
                    continue
                key = (kind, label, pid)
                if key in seen:
                    continue
                seen.add(key)
                p = self.properties[pid]
                out.append({
                    "property_id": int(pid),
                    "address": p["address"],
                    "match_type": kind,
                    "label": label,
                    "lat": num(p["latitude"]),
                    "lng": num(p["longitude"]),
                    "curated_count": self.curated_count.get(pid, 0),
                })
                if len(out) >= limit:
                    return out
        return out

    # ------------------------------------------------------------------
    def incident_json(self, r):
        links = []
        for link in self.subject_links_by_incident.get(r["id"], ()):
            s = self.subjects.get(link["subject_id"])
            links.append({
                "subject_id": int(link["subject_id"]),
                "name": s["name"] if s else "(unknown subject %s)" % link["subject_id"],
                "kind": s["subject_type"] if s else "",
                "relationship": link["relationship"],
                "incident_id": int(r["id"]),
                "data": parse_json(link["data"]) if link["data"] not in ("", "{}") else None,
            })
        return {
            "id": int(r["id"]),
            "source": r["source"],
            "source_kind": source_kind(r["source"]),
            "source_id": r["source_id"],
            "category": r["category"],
            "occurred_at": r["occurred_at"],
            "occurred_at_end": r["occurred_at_end"],
            "date_precision": r["date_precision"],
            "evidence_status": r["evidence_status"],
            "sensitivity": r["sensitivity"],
            "rights": r["rights"],
            "summary": r["summary"],
            "data": parse_json(r["data"]),
            "subjects": links,
        }

    def property_detail(self, pid):
        p = self.properties.get(pid)
        if p is None:
            return None
        fields = {}
        for k, v in p.items():
            if k in ("lot_polygon", "building_polygons"):
                continue
            if v in ("true", "false"):
                fields[k] = boolish(v)
            elif k in ("id", "block_side_id") or k.endswith(("_count", "_total", "_value",
                                                              "_price", "_sqft", "_units",
                                                              "_m", "_rate", "_pct")):
                fields[k] = num(v)
            elif k in ("latitude", "longitude", "year_built", "num_stories", "ground_rent",
                       "walk_score", "transit_score", "bike_score", "walkability_index",
                       "hpi_value", "hpi_yoy_change", "roof_damage_risk",
                       "median_household_income", "irs_agi_per_return", "avm_estimate",
                       "jobs_transit_45min", "market_median_dom", "market_inventory",
                       "nearby_restaurants", "nearby_shops"):
                fields[k] = num(v)
            else:
                fields[k] = v

        lot = esri_to_geojson(parse_json(p["lot_polygon"]))
        buildings = []
        raw_b = parse_json(p["building_polygons"])
        if isinstance(raw_b, list):
            for b in raw_b:
                g = esri_to_geojson(b)
                if g:
                    buildings.append({"type": "Feature", "geometry": g, "properties": {}})
        elif isinstance(raw_b, dict):
            g = esri_to_geojson(raw_b)
            if g:
                buildings.append({"type": "Feature", "geometry": g, "properties": {}})

        incidents = self.incidents_by_property.get(pid, [])
        curated = [self.incident_json(r) for r in incidents if layer_of(r["source"]) == "curated"]
        admin = [self.incident_json(r) for r in reversed(incidents)
                 if layer_of(r["source"]) == "administrative"]

        # People & businesses: unique subjects across all incidents at this property.
        subjects = collections.OrderedDict()
        for inc in curated + admin:
            for link in inc["subjects"]:
                entry = subjects.setdefault(link["subject_id"], {
                    "subject_id": link["subject_id"],
                    "name": link["name"],
                    "kind": link["kind"],
                    "relationships": collections.Counter(),
                    "incident_ids": [],
                })
                entry["relationships"][link["relationship"]] += 1
                entry["incident_ids"].append(inc["id"])
        subject_list = []
        for entry in subjects.values():
            entry["relationships"] = dict(entry["relationships"])
            entry["incident_count"] = len(entry["incident_ids"])
            entry["other_property_ids"] = sorted(
                int(x) for x in self.properties_by_subject.get(str(entry["subject_id"]), ())
                if x != pid and x in self.properties)
            subject_list.append(entry)

        ips = []
        for ip in self.ips_by_property.get(pid, []):
            ips.append({
                "id": int(ip["id"]),
                "ip_type": ip["ip_type"],
                "number": ip["number"],
                "title": ip["title"],
                "owner_name": ip["owner_name"],
                "status": ip["status"],
                "filing_date": ip["filing_date"],
                "grant_date": ip["grant_date"],
                "source": ip["source"],
                "match_confidence": ip["match_confidence"],
                "address_of_record": ip["address_of_record"],
                "data": parse_json(ip["data"]),
            })

        grants = [{
            "id": int(g["id"]),
            "program_key": g["program_key"],
            "program_name": g["program_name"],
            "category": g["category"],
            "amount_cap": g["amount_cap"],
            "summary": g["summary"],
            "matched_reason": g["matched_reason"],
        } for g in self.grants_by_property.get(pid, [])]

        baselines = []
        for b in sorted(self.baselines_by_property.get(pid, []), key=lambda x: x["captured_on"]):
            row = {}
            for k, v in b.items():
                row[k] = boolish(v) if v in ("true", "false") else (num(v) if k not in (
                    "captured_on", "captured_at", "last_sale_date", "owner_name",
                    "owner_type", "building_condition", "market_typology",
                    "receivership_status", "vacant_notice_status") else v)
            baselines.append(row)

        return {
            "id": int(pid),
            "fields": fields,
            "lot_polygon": lot,
            "building_polygons": {"type": "FeatureCollection", "features": buildings},
            "counts": {
                "curated": len(curated),
                "administrative": len(admin),
                "roster": sum(1 for c in curated if c["source_kind"] == "roster"),
                "sensitive": sum(1 for c in curated + admin if c["sensitivity"]),
            },
            "incidents": {"curated": curated, "administrative": admin},
            "subjects": subject_list,
            "registered_ips": ips,
            "grant_program_matches": grants,
            "baseline_snapshots": baselines,
        }

    def lots(self, ids):
        features = []
        for pid in ids:
            p = self.properties.get(pid)
            if p is None or not p["lot_polygon"]:
                continue
            g = esri_to_geojson(parse_json(p["lot_polygon"]))
            if g:
                features.append({
                    "type": "Feature", "id": int(pid), "geometry": g,
                    "properties": {"id": int(pid), "address": p["address"]},
                })
        return {"type": "FeatureCollection", "features": features}

    # ------------------------------------------------------------------
    def summary(self):
        total = sum(self.source_counts.values())
        curated = sum(v for k, v in self.source_counts.items() if layer_of(k) == "curated")
        return {
            "properties": len(self.properties),
            "properties_with_coords": len(self.points_geojson["features"]),
            "incidents": total,
            "curated": curated,
            "administrative": total - curated,
            "subjects": len(self.subjects),
            "registered_ips": sum(len(v) for v in self.ips_by_property.values()) + len(self.unmatched_ips),
            "grant_program_matches": sum(len(v) for v in self.grants_by_property.values()),
            "baseline_snapshots": sum(len(v) for v in self.baselines_by_property.values()),
            "neighborhoods": len(self.neighborhoods),
            "neighborhoods_with_bounds": len(self.neighborhoods_geojson["features"]),
            "layer_rule": {
                "administrative_prefixes": list(ADMIN_PREFIXES),
                "administrative_exact": sorted(ADMIN_EXACT),
                "roster_suffix": ROSTER_SUFFIX,
            },
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def make_handler(corpus):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GreenmountMap/1.0"

        def log_message(self, fmt, *args):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

        def send_json(self, obj, status=200):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_bytes(self, body, ctype, status=200):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urllib.parse.urlsplit(self.path)
            path = url.path
            query = urllib.parse.parse_qs(url.query)

            if path in STATIC:
                name, ctype = STATIC[path]
                try:
                    with open(os.path.join(HERE, name), "rb") as fh:
                        return self.send_bytes(fh.read(), ctype)
                except OSError:
                    return self.send_bytes(b"not found", "text/plain", 404)

            if path == "/favicon.ico":
                return self.send_bytes(b"", "image/x-icon", 204)

            if path == "/api/properties":
                return self.send_bytes(corpus.points_bytes, "application/json; charset=utf-8")

            if path.startswith("/api/properties/"):
                pid = path[len("/api/properties/"):].strip("/")
                detail = corpus.property_detail(pid)
                if detail is None:
                    return self.send_json({"error": "no property with id %s" % pid}, 404)
                return self.send_json(detail)

            if path == "/api/neighborhoods":
                return self.send_json(corpus.neighborhoods_geojson)

            if path == "/api/search":
                return self.send_json({"results": corpus.search(query.get("q", [""])[0])})

            if path == "/api/lots":
                ids = [x for x in query.get("ids", [""])[0].split(",") if x][:600]
                return self.send_json(corpus.lots(ids))

            if path == "/api/summary":
                return self.send_json(corpus.summary())

            return self.send_json({"error": "not found"}, 404)

    return Handler


def run_check(corpus):
    s = corpus.summary()
    print("properties            %6d  (with coordinates: %d)" % (s["properties"], s["properties_with_coords"]))
    print("property_incidents    %6d" % s["incidents"])
    print("  curated             %6d" % s["curated"])
    print("  administrative      %6d" % s["administrative"])
    print("subjects              %6d" % s["subjects"])
    print("registered_ips        %6d" % s["registered_ips"])
    print("grant_program_matches %6d" % s["grant_program_matches"])
    print("baseline_snapshots    %6d" % s["baseline_snapshots"])
    print("neighborhoods         %6d  (with parseable bounds: %d)" % (
        s["neighborhoods"], s["neighborhoods_with_bounds"]))
    print()
    print("Layer rule: administrative = source starts with %s or in %s; "
          "everything else curated; curated sources ending in '%s' are labelled 'roster'."
          % (list(ADMIN_PREFIXES), sorted(ADMIN_EXACT), ROSTER_SUFFIX))
    print()
    print("%-28s %6s  %s" % ("source", "rows", "layer"))
    for source, count in corpus.source_counts.most_common():
        print("%-28s %6d  %s" % (source, count, source_kind(source)))
    print()
    for note in corpus.notes:
        print("note:", note)

    tiers = collections.Counter()
    for pid in corpus.properties:
        c = corpus.curated_count.get(pid, 0)
        tiers["0" if c == 0 else "1-9" if c < 10 else "10-24" if c < 25 else "25+"] += 1
    print("curated depth tiers:", dict(tiers))

    ok = True
    for label, actual, expected in [
        ("properties", s["properties"], EXPECTED_PROPERTIES),
        ("incidents", s["incidents"], EXPECTED_INCIDENTS),
        ("curated", s["curated"], EXPECTED_CURATED),
    ]:
        if actual != expected:
            print("MISMATCH %s: actual=%d expected=%d" % (label, actual, expected))
            ok = False
    print("check", "passed" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    corpus = Corpus()
    corpus.points_bytes = json.dumps(corpus.points_geojson).encode("utf-8")
    if "--check" in argv:
        return run_check(corpus)
    for note in corpus.notes:
        print("note:", note)
    s = corpus.summary()
    print("loaded %d properties (%d with coordinates), %d incidents (%d curated / %d administrative)"
          % (s["properties"], s["properties_with_coords"], s["incidents"],
             s["curated"], s["administrative"]))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), make_handler(corpus))
    except OSError as exc:
        print("could not bind port %d (%s); is another map/app.py still running?" % (PORT, exc))
        return 2
    print("serving on http://localhost:%d  (Ctrl-C to stop)" % PORT, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
