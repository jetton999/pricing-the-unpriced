#!/usr/bin/env python3
"""
Standardize property addresses and merge the duplicate properties in the study-area CSVs.
Standard library only. Run it from anywhere; it edits the CSVs in this repo in place.

    python3 bin/clean_addresses.py            # apply (idempotent: a second run changes nothing)
    python3 bin/clean_addresses.py --dry-run  # print the summary, write nothing

Why it exists. An import on 2026-04-06 added about 140 properties with SDAT/City-style addresses
("608 E 30TH ST, Baltimore, MD 21218"). The house format, used by every other property, is mixed
case with no ZIP ("608 E 30th St, Baltimore, MD"). Eight of the imported rows duplicate a house-
format property: each pair shares an SDAT account (blocklot), which proves it is the same parcel.

1. Rewrite every property address: title-case street words, lowercase ordinals (30th), uppercase
   directionals (E), suffixes Ave / St / Road / Lane / Pl, no ZIP, ending ", Baltimore, MD".
   Records with no house number (the named places) are left unchanged.
2. Merge the 8 duplicate pairs into the house-format copy (the survivor): every row that points at
   the retired copy (incidents, parcels, grant matches, baseline snapshots, registered IP) is
   moved to the survivor, the survivor takes the retired copy's block side, and the retired
   property is dropped. incident_subjects and incident_links hang off incident ids, so they follow
   their incident and need no change.
3. Drop exact repeats on the survivors: incidents with the same source and source_id, and grant
   matches with the same program_key. The survivor's own row wins. A curated incident or one with
   a sensitivity flag is never dropped (the script stops if one would be).

Run it after bin/cut_study_area.py to reproduce the CSVs in this repo.
"""
import argparse
import collections
import csv
import io
import os
import re
import sys

csv.field_size_limit(sys.maxsize)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# survivor id -> (retired id, block side the survivor takes). The block sides are SDAT's: 600 E 31st
# St sits on E 31st St (163) and 601 Homestead St on Homestead St (189), not on the sides the
# survivors previously carried (105 and 213).
PAIRS = {
    "2374": ("1778", "185"),   # 3101 Tinges Lane
    "2375": ("1777", "185"),   # 3103 Tinges Lane
    "2447": ("1621", "159"),   # 600 E 33rd St
    "2464": ("1660", "169"),   # 600 Venable Ave
    "2463": ("1670", "160"),   # 601 E 34th St
    "2373": ("2053", "193"),   # 601 Montpelier St
    "1116": ("2031", "163"),   # 600 E 31st St
    "2326": ("1771", "189"),   # 601 Homestead St
}
RETIRED = {retired: survivor for survivor, (retired, _) in PAIRS.items()}

SUFFIX = {"AVE": "Ave", "AVENUE": "Ave", "ST": "St", "STREET": "St", "RD": "Road", "ROAD": "Road",
          "LN": "Lane", "LANE": "Lane", "PL": "Pl", "PLACE": "Pl"}
DIRECTIONAL = {"N", "S", "E", "W", "NE", "NW", "SE", "SW"}
# The one imported-era address that never had a suffix.
ADDRESS_FIXES = {"601 Homestead": "601 Homestead St"}

ADMINISTRATIVE_SOURCES = {"sdat_assessments", "sdat:owner"}


def is_administrative(source):
    return source.startswith("baltimore:") or source in ADMINISTRATIVE_SOURCES


def standardize(address):
    """'608 E 30TH ST, Baltimore, MD 21218' -> '608 E 30th St, Baltimore, MD'. None if the address
    has no house number (a named place), which is left alone."""
    street = address.split(",")[0].strip()
    street = ADDRESS_FIXES.get(street, street)
    match = re.match(r"^(\d+(?:-\d+)?(?: 1/2)?)\s+(.+)$", street)
    if not match:
        return None
    words = match[2].split()
    out = []
    for i, word in enumerate(words):
        upper = word.upper()
        if upper in DIRECTIONAL:
            out.append(upper)
        elif re.fullmatch(r"\d+(ST|ND|RD|TH)", upper):
            out.append(upper.lower())
        elif i == len(words) - 1 and i > 0 and upper in SUFFIX:
            out.append(SUFFIX[upper])
        else:
            out.append(word.capitalize() if word.isupper() or word.islower() else word)
    return f"{match[1]} {' '.join(out)}, Baltimore, MD"


def read(name):
    with open(os.path.join(ROOT, name), newline="", encoding="utf-8") as handle:
        raw = handle.read()
    rows = list(csv.reader(io.StringIO(raw)))
    newline = "\r\n" if "\r\n" in raw[:raw.find("\n") + 1] else "\n"
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:]], newline


def write(name, head, rows, newline):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator=newline)
    writer.writerow(head)
    writer.writerows([r[c] for c in head] for r in rows)
    with open(os.path.join(ROOT, name), "w", newline="", encoding="utf-8") as handle:
        handle.write(buffer.getvalue())


def repeats(rows, key, moved):
    """The rows to drop: every row after the first for its key. Rows already on the survivor sort
    ahead of rows moved in from the retired copy (`moved` holds their ids), so the survivor's own
    row is the one kept."""
    ordered = sorted(rows, key=lambda r: (r["id"] in moved, int(r["id"])))
    seen, dropped = set(), []
    for row in ordered:
        k = key(row)
        if k in seen:
            dropped.append(row)
        seen.add(k)
    return dropped


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    args = parser.parse_args()
    out = {}
    report = []

    # ---- properties ----------------------------------------------------------------------------
    head, props, newline = read("properties.csv")
    by_id = {p["id"]: p for p in props}
    present = {r for r in RETIRED if r in by_id}
    if present and len(present) != len(RETIRED):
        sys.exit("only some of the 8 retired properties are present; the CSVs are in an unknown state")

    if present:
        for survivor, (retired, side) in PAIRS.items():
            a, b = by_id[survivor]["blocklot"], by_id[retired]["blocklot"]
            # SDAT "0309034075 013" and City "4075 013" are one account; "030903" is the ward prefix.
            same = a == b or a.replace(" ", "").endswith(b.replace(" ", "")) and a.startswith("030903")
            if not same:
                sys.exit(f"{survivor} and {retired} do not share an SDAT account: {a!r} vs {b!r}")
            if by_id[retired]["block_side_id"] != side:
                sys.exit(f"{retired} carries block side {by_id[retired]['block_side_id']}, expected {side}")
            by_id[survivor]["block_side_id"] = side
        props = [p for p in props if p["id"] not in RETIRED]

    renamed = []
    for p in props:
        new = standardize(p["address"])
        if new is not None and new != p["address"]:
            renamed.append((p["id"], p["address"], new))
            p["address"] = new
    collisions = {a: n for a, n in collections.Counter(p["address"] for p in props).items() if n > 1}
    if collisions:
        sys.exit(f"addresses collide after standardizing: {collisions}")
    out["properties.csv"] = (head, props, newline)
    report.append(f"properties: {len(by_id)} -> {len(props)} ({len(present)} retired, "
                  f"{len(renamed)} renamed)")

    # ---- property_incidents --------------------------------------------------------------------
    head, incidents, newline = read("property_incidents.csv")
    moved = {i["id"] for i in incidents if i["property_id"] in RETIRED}
    for i in incidents:
        i["property_id"] = RETIRED.get(i["property_id"], i["property_id"])
    survivors = set(PAIRS)
    candidates = [i for i in incidents if i["property_id"] in survivors]
    dropped = repeats(candidates, lambda i: (i["property_id"], i["source"], i["source_id"]), moved)
    protected = [i for i in dropped if not is_administrative(i["source"]) or i["sensitivity"]]
    if protected:
        sys.exit(f"would drop curated or sensitivity-flagged incidents: {[i['id'] for i in protected]}")
    gone = {i["id"] for i in dropped}
    kept = [i for i in incidents if i["id"] not in gone]
    out["property_incidents.csv"] = (head, kept, newline)
    curated = sum(1 for i in kept if not is_administrative(i["source"]))
    report.append(f"property_incidents: {len(incidents)} -> {len(kept)} ({len(moved)} moved, "
                  f"{len(gone)} repeats dropped, {curated} curated)")

    h, subjects, nl = read("incident_subjects.csv")
    h2, links, nl2 = read("incident_links.csv")
    stranded = [s["id"] for s in subjects if s["property_incident_id"] in gone] + \
               [l["id"] for l in links if l["property_incident_id"] in gone or l["related_incident_id"] in gone]
    if stranded:
        sys.exit(f"incident_subjects / incident_links reference dropped incidents: {stranded}")

    # ---- grant_program_matches -----------------------------------------------------------------
    head, matches, newline = read("grant_program_matches.csv")
    moved = {m["id"] for m in matches if m["property_id"] in RETIRED}
    for m in matches:
        m["property_id"] = RETIRED.get(m["property_id"], m["property_id"])
    candidates = [m for m in matches if m["property_id"] in survivors]
    dropped = repeats(candidates, lambda m: (m["property_id"], m["program_key"]), moved)
    gone = {m["id"] for m in dropped}
    kept = [m for m in matches if m["id"] not in gone]
    out["grant_program_matches.csv"] = (head, kept, newline)
    report.append(f"grant_program_matches: {len(matches)} -> {len(kept)} ({len(moved)} moved, "
                  f"{len(gone)} repeats dropped)")

    # ---- baseline_snapshots, property_parcels, registered_ips ----------------------------------
    head, snaps, newline = read("baseline_snapshots.csv")
    n = sum(1 for s in snaps if s["property_id"] in RETIRED)
    for s in snaps:
        s["property_id"] = RETIRED.get(s["property_id"], s["property_id"])
    days = collections.Counter((s["property_id"], s["captured_on"]) for s in snaps)
    if any(c > 1 for c in days.values()):
        sys.exit("two baseline snapshots would share a property and day")
    out["baseline_snapshots.csv"] = (head, snaps, newline)
    report.append(f"baseline_snapshots: {n} moved")

    head, parcels, newline = read("property_parcels.csv")
    n = sum(1 for p in parcels if p["matched_property_id"] in RETIRED)
    for p in parcels:
        p["matched_property_id"] = RETIRED.get(p["matched_property_id"], p["matched_property_id"])
    out["property_parcels.csv"] = (head, parcels, newline)
    report.append(f"property_parcels: {n} re-pointed")

    head, ips, newline = read("registered_ips.csv")
    n = sum(1 for p in ips if p["property_id"] in RETIRED)
    for p in ips:
        p["property_id"] = RETIRED.get(p["property_id"], p["property_id"])
    out["registered_ips.csv"] = (head, ips, newline)
    report.append(f"registered_ips: {n} re-pointed")

    # ---- row_counts.txt ------------------------------------------------------------------------
    counts_path = os.path.join(ROOT, "row_counts.txt")
    with open(counts_path, encoding="utf-8") as handle:
        counts = handle.read()
    new_counts = {"properties": len(out["properties.csv"][1]),
                  "property_incidents": len(out["property_incidents.csv"][1]),
                  "grant_program_matches": len(out["grant_program_matches.csv"][1])}
    for name, total in new_counts.items():
        counts = re.sub(rf"^{name}: \d+$", f"{name}: {total}", counts, flags=re.M)

    block_sides = {p["block_side_id"] for p in props if p["block_side_id"]}
    coords = sum(1 for p in props if p["latitude"] and p["longitude"])
    report.append(f"block sides: {len(block_sides)}; properties with coordinates: {coords}")

    print("\n".join(report))
    if args.dry_run:
        print("dry run: nothing written")
        return
    for name, (head, rows, newline) in out.items():
        write(name, head, rows, newline)
    with open(counts_path, "w", encoding="utf-8") as handle:
        handle.write(counts)


if __name__ == "__main__":
    main()
