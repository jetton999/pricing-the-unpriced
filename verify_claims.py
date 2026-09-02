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

# The layer split, identical to cell 3 of START_HERE.ipynb.
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


def main():
    incidents = list(rows("property_incidents.csv"))
    links = list(rows("incident_links.csv"))
    properties = list(rows("properties.csv"))
    subjects = list(rows("subjects.csv"))
    incident_subjects = list(rows("incident_subjects.csv"))

    # Section 1: the two layers
    check("property_incidents rows", len(incidents), 20308)
    by_source = collections.Counter(r["source"] for r in incidents)
    administrative = sum(v for k, v in by_source.items() if is_admin(k))
    check("administrative rows", administrative, 16706)
    check("curated rows", len(incidents) - administrative, 3602)
    for source, claimed in [
        ("baltimore:311", 6641), ("baltimore:permits", 5329),
        ("sdat_assessments", 3064), ("baltimore:crime", 803),
        ("whitepaper", 1138), ("newspapers_com", 661),
        ("stjohns_interments", 583), ("mdlandrec", 492),
        ("sanborn", 254), ("nrhp", 139),
    ]:
        check("source %s" % source, by_source.get(source, 0), claimed)

    def year_of(record):
        raw = (record.get("occurred_at") or "").strip()
        return int(raw[:4]) if len(raw) >= 4 and raw[:4].isdigit() else None

    years = [year_of(r) for r in incidents]
    check("incidents before 2000", sum(1 for y in years if y and y < 2000), 3633)
    check("incidents before 1950", sum(1 for y in years if y and y < 1950), 2259)

    # Section 2: documentation depth, curated only (notebook cell 7)
    depth = collections.Counter(
        r["property_id"] for r in incidents
        if not is_admin(r["source"]) and (r["property_id"] or "").strip()
    )
    check("properties with >=1 curated", sum(1 for v in depth.values() if v >= 1), 316)
    check("properties with >=10 curated", sum(1 for v in depth.values() if v >= 10), 68)
    check("properties with >=25 curated", sum(1 for v in depth.values() if v >= 25), 22)

    # Section 3: evidence grading
    evidence = collections.Counter((r.get("evidence_status") or "").strip() for r in incidents)
    check("evidence graded total", sum(v for k, v in evidence.items() if k), 1328)
    for status, claimed in [("verified", 1162), ("probable", 105),
                            ("possible", 59), ("contested", 2)]:
        check("evidence %s" % status, evidence.get(status, 0), claimed)
    check("rows with date_precision",
          sum(1 for r in incidents if (r.get("date_precision") or "").strip()), 1908)

    check("incident_links rows", len(links), 236)
    link_types = collections.Counter((r.get("link_type") or "").strip() for r in links)
    for link_type, claimed in [("related", 112), ("supports", 100),
                               ("duplicates", 21), ("contradicts", 3)]:
        check("link %s" % link_type, link_types.get(link_type, 0), claimed)

    # Section 4: the tables
    check("properties rows", len(properties), 1874)
    check("subjects rows", len(subjects), 3103)
    subject_types = collections.Counter((r.get("subject_type") or "").strip() for r in subjects)
    for kind, claimed in [("person", 2035), ("business", 527),
                          ("organization", 300), ("family", 138)]:
        check("subject %s" % kind, subject_types.get(kind, 0), claimed)

    check("incident_subjects rows", len(incident_subjects), 5462)
    relationships = collections.Counter(
        (r.get("relationship") or "").strip() for r in incident_subjects)
    for relationship, claimed in [("owned", 926), ("operated_at", 678), ("sold", 661),
                                  ("interred_at", 596), ("purchased", 455), ("lived_at", 280)]:
        check("relationship %s" % relationship, relationships.get(relationship, 0), claimed)

    for filename, claimed in [("registered_ips.csv", 115), ("property_parcels.csv", 50860),
                              ("grant_program_matches.csv", 11789), ("neighborhoods.csv", 6),
                              ("baseline_snapshots.csv", 887)]:
        check("%s rows" % filename, sum(1 for _ in rows(filename)), claimed)

    # Section 4b: the t0 baseline
    captures = collections.Counter(
        (r.get("captured_on") or "")[:10] for r in rows("baseline_snapshots.csv"))
    check("baseline capture 2026-07-13", captures.get("2026-07-13", 0), 351)
    check("baseline capture 2026-07-22", captures.get("2026-07-22", 0), 536)

    # The graph, built exactly as notebook cell 11 builds it: property <-> subject,
    # joined through the incident, parallel edges collapsed.
    incident_to_property = {r["id"]: r["property_id"] for r in incidents}
    subject_ids = {r["id"] for r in subjects}
    nodes, edges = set(), set()
    for record in incident_subjects:
        incident_id = (record.get("property_incident_id") or "").strip()
        subject_id = (record.get("subject_id") or "").strip()
        if incident_id in incident_to_property and subject_id in subject_ids:
            property_node = "prop:%s" % incident_to_property[incident_id]
            subject_node = "subj:%s" % subject_id
            nodes.add(property_node)
            nodes.add(subject_node)
            edges.add((property_node, subject_node))
    check("graph nodes", len(nodes), 3613)
    check("graph edges", len(edges), 3765)

    failures = [c for c in checks if not c[0]]
    for _, label, actual, claimed in failures:
        print("MISMATCH  %-34s actual=%-8s README=%s" % (label, actual, claimed))
    print("%d/%d README claims verified against the data." % (
        len(checks) - len(failures), len(checks)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
