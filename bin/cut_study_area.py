#!/usr/bin/env python3
"""
Cut the sponsor's full export down to the study area: Greenmount Ave and about one block
either side. This is how the CSVs in this repo were made (README §4, "How the study area was
cut"). Standard library only.

    mkdir /tmp/full && git archive e00b32b '*.csv' | tar -x -C /tmp/full   # the full export
    python3 bin/cut_study_area.py /tmp/full   # writes the cut CSVs into this repo
    git status                                # no change means the cut reproduces

A property is kept if:
  - its address is on Greenmount Ave, or
  - it is within 150 m of a Greenmount Ave property, by coordinates, or
  - it has no coordinates, and a neighbor on the same street within 10 house numbers is within
    150 m, or
  - it is the Old Waverly Village / York Road record (York Road is Greenmount's historic name).

Every other table keeps the rows for those properties: incidents, then the incident_subjects,
incident_links, and subjects they reach, then the property-keyed tables. Parcels and registered
IP with no property match are kept when their address is in the hundred-block of a kept
property's street. Patents are all kept: they carry only a city-level address and tie to the
corridor through people.
"""
import argparse
import collections
import csv
import io
import math
import os
import re
import sys

csv.field_size_limit(sys.maxsize)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RADIUS_M = 150
NEIGHBOR_HOUSE_NUMBERS = 10
HAND_KEEP = {"2367"}   # Old Waverly Village — York Road (Aull family and the toll gate)
DROP_NEIGHBORHOODS = {"Baltimore Peninsula"}

# Metres per degree near Baltimore (latitude 39.32).
KY = 111_000
KX = 111_000 * math.cos(math.radians(39.32))

SUFFIX = {"AVENUE": "AVE", "STREET": "ST", "ROAD": "RD", "DRIVE": "DR", "PLACE": "PL", "LANE": "LN"}


def street_block(address):
    """'452 E 28th St, Baltimore, MD' -> ('E 28TH ST', 400, 452). None without a house number."""
    first = (address or "").split(",")[0].upper().replace(".", "")
    match = re.match(r"^(\d+)(?:[-/ ]\d+)?(?: 1/2)?\s+(.+)$", first)
    if not match:
        return None
    street = " ".join(SUFFIX.get(word, word) for word in match[2].split())
    street = re.split(r"\s+(?:THIRD|FLOOR|SUITE|STE|UNIT|APT|#)", street)[0].strip()
    number = int(match[1])
    return street, number // 100 * 100, number


def read(source, name):
    with open(os.path.join(source, name), newline="", encoding="utf-8") as handle:
        raw = handle.read()
    rows = list(csv.reader(io.StringIO(raw)))
    newline = "\r\n" if "\r\n" in raw[:raw.find("\n") + 1] else "\n"
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:]], newline


def cut(source, out, name, keep):
    """Write the rows of `name` that pass `keep`, preserving the column order and line endings."""
    head, rows, newline = read(source, name)
    kept = [r for r in rows if keep(r)]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator=newline)
    writer.writerow(head)
    writer.writerows([r[c] for c in head] for r in kept)
    with open(os.path.join(out, name), "w", newline="", encoding="utf-8") as handle:
        handle.write(buffer.getvalue())
    print("%-28s %7s -> %7s" % (name, f"{len(rows):,}", f"{len(kept):,}"))
    return kept


def study_area(properties):
    """Return the ids of the properties in the study area."""
    def point(r):
        if r["latitude"] and r["longitude"]:
            return float(r["latitude"]) * KY, float(r["longitude"]) * KX
        return None

    greenmount = [r for r in properties if "greenmount" in r["address"].lower()]
    anchors = [p for p in map(point, greenmount) if p]
    distance = {}
    for r in properties:
        p = point(r)
        if p:
            distance[r["id"]] = min(math.sqrt((p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2) for a in anchors)

    keep = {r["id"] for r in greenmount} | HAND_KEEP
    keep |= {i for i, d in distance.items() if d <= RADIUS_M}

    # No coordinates: borrow the distance of a same-street neighbor within 10 house numbers.
    located = [(street_block(r["address"]), distance[r["id"]]) for r in properties if r["id"] in distance]
    for r in properties:
        sb = street_block(r["address"])
        if r["id"] in keep or r["id"] in distance or not sb:
            continue
        if any(o and o[0] == sb[0] and abs(o[2] - sb[2]) <= NEIGHBOR_HOUSE_NUMBERS and d <= RADIUS_M
               for o, d in located):
            keep.add(r["id"])
    return keep


def split_portfolio_deals(properties, keep):
    """Portfolio deals (one price and date on several parcels) that the cut splits.

    Once the other parcels are gone, a kept parcel from such a deal looks like a single sale,
    and the export alone can no longer tell. Report them so the docs can name them.
    """
    deals = collections.defaultdict(list)
    for r in properties:
        price = float(r["last_sale_price"] or 0)
        if price > 10_000:
            deals[(r["last_sale_price"], r["last_sale_date"])].append(r)
    for (price, date), rows in sorted(deals.items()):
        inside = [r for r in rows if r["id"] in keep]
        if len(rows) > 1 and len(inside) == 1:
            r = inside[0]
            print("  %s (%s): $%s on %s, shared with %d parcel(s) outside the study area"
                  % (r["address"], r["zoning_code"].strip(), f"{float(price):,.0f}", date, len(rows) - 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("source", help="folder holding the full export's CSVs (e.g. a worktree of e00b32b)")
    parser.add_argument("--out", default=ROOT, help="folder to write the cut CSVs to (default: this repo)")
    args = parser.parse_args()
    if os.path.abspath(args.source) == os.path.abspath(args.out):
        parser.error("source and --out are the same folder; the cut would overwrite its own input")

    _, properties, _ = read(args.source, "properties.csv")
    keep = study_area(properties)
    blocks = {street_block(r["address"])[:2] for r in properties
              if r["id"] in keep and street_block(r["address"])}

    def in_blocks(address):
        sb = street_block(address)
        return bool(sb) and sb[:2] in blocks

    cut(args.source, args.out, "properties.csv", lambda r: r["id"] in keep)
    incidents = cut(args.source, args.out, "property_incidents.csv", lambda r: r["property_id"] in keep)
    incident_ids = {r["id"] for r in incidents}
    links = cut(args.source, args.out, "incident_subjects.csv",
                lambda r: r["property_incident_id"] in incident_ids)
    subject_ids = {r["subject_id"] for r in links}
    cut(args.source, args.out, "subjects.csv", lambda r: r["id"] in subject_ids)
    cut(args.source, args.out, "incident_links.csv",
        lambda r: r["property_incident_id"] in incident_ids and r["related_incident_id"] in incident_ids)
    cut(args.source, args.out, "grant_program_matches.csv", lambda r: r["property_id"] in keep)
    cut(args.source, args.out, "baseline_snapshots.csv", lambda r: r["property_id"] in keep)
    cut(args.source, args.out, "registered_ips.csv",
        lambda r: r["property_id"] in keep or r["ip_type"] == "patent"
        or (not r["property_id"] and in_blocks(r["address_of_record"])))
    cut(args.source, args.out, "property_parcels.csv",
        lambda r: r["matched_property_id"] in keep or in_blocks(r["normalized_address"] or r["address"]))
    cut(args.source, args.out, "neighborhoods.csv", lambda r: r["name"] not in DROP_NEIGHBORHOODS)

    print("\nPortfolio deals split by the cut (they now look like single-building sales):")
    split_portfolio_deals(properties, keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
