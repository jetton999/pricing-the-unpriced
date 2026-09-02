#!/usr/bin/env python3
"""
Verify every quantitative claim in README.md against the CSVs in this repository.

Standard library only. No pandas, no networkx, no install step.

    python3 verify_claims.py

Exits 0 if every claim matches, 1 otherwise. If you change the data, run this before
you trust the README. If it disagrees with the README, the data wins and the README
is the thing to fix.
"""
import collections
import csv
import os
import sys

csv.field_size_limit(sys.maxsize)
ROOT = os.path.dirname(os.path.abspath(__file__))

# The layer split, identical to cell 3 of START_HERE.ipynb and map/app.py.
ADMIN_PREFIXES = ("baltimore:",)
ADMIN_EXACT = {"sdat_assessments", "sdat:owner"}


def is_admin(source):
    source = str(source)
    return source.startswith(ADMIN_PREFIXES) or source in ADMIN_EXACT


def rows(filename):
    path = os.path.join(ROOT, filename)
    with open(path, newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


checks = []


def check(label, actual, claimed):
    checks.append((actual == claimed, label, actual, claimed))


def check_about(label, actual, claimed, tolerance):
    """For claims the README states as approximate ("~3,600")."""
    checks.append((abs(actual - claimed) <= tolerance, label, actual, "~%s" % claimed))


def main():
    incidents = list(rows("property_incidents.csv"))
    properties = list(rows("properties.csv"))
    incident_subjects = list(rows("incident_subjects.csv"))

    # Intro: corpus size and the two layers
    check("properties rows", len(properties), 1874)
    by_source = collections.Counter(r["source"] for r in incidents)
    administrative = sum(v for k, v in by_source.items() if is_admin(k))
    curated = len(incidents) - administrative
    check_about("curated rows (~3,600)", curated, 3600, 50)
    check_about("administrative rows (~16,700)", administrative, 16700, 50)

    def year_of(record):
        raw = (record.get("occurred_at") or "").strip()
        return int(raw[:4]) if len(raw) >= 4 and raw[:4].isdigit() else None

    earliest = min(y for y in (year_of(r) for r in incidents) if y)
    check("earliest record is in the 1650s", earliest // 10 * 10, 1650)

    # Idea 1: use-history sources
    check("newspaper clippings", by_source.get("newspapers_com", 0), 661)
    check("research white papers", by_source.get("whitepaper", 0), 1138)
    relationships = collections.Counter(
        (r.get("relationship") or "").strip() for r in incident_subjects)
    check_about("operated_at links (~680)", relationships.get("operated_at", 0), 680, 5)
    check("registered IP rows", sum(1 for _ in rows("registered_ips.csv")), 115)
    block_sides = {(r.get("block_side_id") or "").strip() for r in properties}
    block_sides.discard("")
    check("distinct block_side_id values", len(block_sides), 141)

    # Idea 2: the baseline capture dates
    captures = sorted({(r.get("captured_on") or "")[:7]
                       for r in rows("baseline_snapshots.csv")} - {""})
    check("baseline captured in July 2026 only", captures, ["2026-07"])
    check("baseline capture dates", len({(r.get("captured_on") or "")[:10]
                                         for r in rows("baseline_snapshots.csv")}), 2)

    failures = [c for c in checks if not c[0]]
    for _, label, actual, claimed in failures:
        print("MISMATCH  %-36s actual=%-8s README=%s" % (label, actual, claimed))
    print("%d/%d README claims verified against the data." % (
        len(checks) - len(failures), len(checks)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
