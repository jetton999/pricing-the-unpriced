#!/usr/bin/env python3
"""
Verify every quantitative claim in README.md against the CSVs in this repository, plus the
same numbers where AGENTS.md, PROJECT_IDEAS.md, LICENSE.md, map/, and site/ repeat them.

Standard library only. No pandas, no networkx, no install step.

    python3 verify_claims.py

Exits 0 if every claim matches, 1 otherwise. If you change the data, run this before
you trust the README. If it disagrees with the README, the data wins and the README
is the thing to fix.
"""
import collections
import csv
import hashlib
import json
import os
import re
import sys

csv.field_size_limit(sys.maxsize)
ROOT = os.path.dirname(os.path.abspath(__file__))

# The layer split, identical to section 1 of START_HERE.ipynb and to map/app.py.
ADMIN_PREFIXES = ("baltimore:",)
ADMIN_EXACT = {"sdat_assessments", "sdat:owner"}


# The September 2026 package's 52 incident rows with a sensitivity flag. Every one must survive a
# refresh (LICENSE.md).
SEPTEMBER_SENSITIVITY_IDS = """
18116 18122 18792 18793 18798 18799 18828 18834 18837 18838 18842 18845 18847 18849 18855 18859
18870 18873 18874 18875 18876 18877 18880 18881 18884 18890 18893 18895 18897 18898 18899 18900
18901 18903 18904 18907 18908 18912 18919 18920 18929 18934 18936 18938 20979 20984 20985 20990
20992 20995 20996 21000
""".split()

# baseline_snapshots.csv is frozen at t0. Any change to the file, even a re-keyed id, fails here.
BASELINE_SHA256 = "a90bd854b2e681a4c261f2bf99692d7f6258f567ce307dd1afe968d8adbede85"

# A North American phone number: (410) 235-4334, 410-235-4334, 410.235.4334. A digit group glued by a
# hyphen to a word or number before it ("SEB-487-235-1985", "mb19268-495-497") is a book/page or image
# id, not a phone, and is skipped.
PHONE = re.compile(r"(?<![A-Za-z0-9]-)(?<!\d)\(?\b[2-9]\d{2}\)?[-. ]?[2-9]\d{2}[-. ]\d{4}\b(?!-\w)")

IMAGE_FOLDERS = {"deeds-and-title-chain", "bca-brg4-1", "loc-sanborn", "passano-oneill", "pikl-greenmount"}


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


def doc_says(filename, snippet):
    """A doc outside the README repeats a number: check the computed snippet appears in it."""
    with open(os.path.join(ROOT, filename), encoding="utf-8") as handle:
        check("%s says %r" % (filename, snippet), snippet in handle.read(), True)


def main():
    incidents = list(rows("property_incidents.csv"))
    links = list(rows("incident_links.csv"))
    properties = list(rows("properties.csv"))
    subjects = list(rows("subjects.csv"))
    incident_subjects = list(rows("incident_subjects.csv"))
    registered_ips = list(rows("registered_ips.csv"))
    parcels = list(rows("property_parcels.csv"))
    grant_matches = list(rows("grant_program_matches.csv"))
    neighborhoods = list(rows("neighborhoods.csv"))
    baseline = list(rows("baseline_snapshots.csv"))
    archive_folders = list(rows("archive_folders.csv"))
    archive_scans = list(rows("archive_scans.csv"))
    tours = list(rows("matterport_tours.csv"))
    crosswalk = list(rows("property_id_crosswalk.csv"))
    storefronts = list(rows("storefront_assessments.csv"))
    images = list(rows("property_images.csv"))

    # Section 1: the two layers
    check("property_incidents rows", len(incidents), 17387)
    by_source = collections.Counter(r["source"] for r in incidents)
    administrative = sum(v for k, v in by_source.items() if is_admin(k))
    check("administrative rows", administrative, 9496)
    check("curated rows", len(incidents) - administrative, 7891)
    for source, claimed in [
        ("baltimore:311", 5158), ("baltimore:permits", 1642),
        ("sdat_assessments", 853), ("baltimore:crime", 822),
        ("whitepaper", 1126), ("newspapers_com", 1658),
        ("stjohns_interments", 583), ("mdlandrec", 1691),
        ("sanborn", 284), ("nrhp", 158),
        ("bca_dhcd", 696), ("bca_tax_rolls", 608), ("polk", 201), ("local_news", 181),
        ("hud:cdbg", 39),
    ]:
        check("source %s" % source, by_source.get(source, 0), claimed)

    def year_of(record):
        raw = (record.get("occurred_at") or "").strip()
        return int(raw[:4]) if len(raw) >= 4 and raw[:4].isdigit() else None

    years = years_all = [year_of(r) for r in incidents]
    check("incidents before 2000", sum(1 for y in years if y and y < 2000), 7086)
    check("incidents before 1950", sum(1 for y in years if y and y < 1950), 4699)

    # Section 2: documentation depth, curated only (notebook section 3)
    depth = collections.Counter(
        r["property_id"] for r in incidents
        if not is_admin(r["source"]) and (r["property_id"] or "").strip()
    )
    check("properties with >=1 curated", sum(1 for v in depth.values() if v >= 1), 441)
    check("properties with >=10 curated", sum(1 for v in depth.values() if v >= 10), 160)
    check("properties with >=25 curated", sum(1 for v in depth.values() if v >= 25), 61)

    # Section 3: evidence grading
    evidence = collections.Counter((r.get("evidence_status") or "").strip() for r in incidents)
    check("evidence graded total", sum(v for k, v in evidence.items() if k), 5538)
    for status, claimed in [("verified", 4757), ("probable", 611),
                            ("possible", 152), ("contested", 10), ("refuted", 8)]:
        check("evidence %s" % status, evidence.get(status, 0), claimed)
    check("rows with date_precision",
          sum(1 for r in incidents if (r.get("date_precision") or "").strip()), 6342)
    graded = [r for r in incidents if (r.get("evidence_status") or "").strip()]
    check("graded curated rows", sum(1 for r in graded if not is_admin(r["source"])), 4993)
    check("graded administrative rows", sum(1 for r in graded if is_admin(r["source"])), 545)
    check("ungraded curated rows", sum(
        1 for r in incidents
        if not is_admin(r["source"]) and not (r.get("evidence_status") or "").strip()), 2898)
    check("rows with a sensitivity flag",
          sum(1 for r in incidents if (r.get("sensitivity") or "").strip()), 126)

    check("incident_links rows", len(links), 1868)
    link_types = collections.Counter((r.get("link_type") or "").strip() for r in links)
    for link_type, claimed in [("related", 1053), ("supports", 769),
                               ("duplicates", 25), ("contradicts", 21)]:
        check("link %s" % link_type, link_types.get(link_type, 0), claimed)

    # Section 4: the tables
    check("properties rows", len(properties), 699)
    zips = collections.Counter((r.get("zip_code") or "").strip() for r in properties)
    check("properties in ZIP 21218", zips.get("21218", 0), 699)
    check("properties with coordinates", sum(
        1 for r in properties if (r.get("latitude") or "").strip() and (r.get("longitude") or "").strip()), 668)
    prices = [float(r["last_sale_price"]) for r in properties if (r.get("last_sale_price") or "").strip()]
    check("properties with a last_sale_price", len(prices), 668)
    check("last_sale_price of $0", sum(1 for p in prices if p == 0), 140)
    check("last_sale_price above $0", sum(1 for p in prices if p > 0), 528)
    # 701 Exeter Hall Ave: a portfolio sale whose other parcel was cut, so its price+date is unique here
    exeter = [r for r in properties if r["address"].startswith("701 Exeter Hall Ave")]
    deal = [(r["last_sale_price"], r["last_sale_date"]) for r in exeter]
    check("701 Exeter Hall Ave last sale", deal, [("19000000", "2026-03-19")])
    check("701 Exeter Hall Ave sale shared in the export", sum(
        1 for r in properties if (r["last_sale_price"], r["last_sale_date"]) in deal), 1)

    check("block sides", len({r["block_side_id"] for r in properties if (r.get("block_side_id") or "").strip()}), 59)

    # Columns the README says are blank, or hold one value, in every row of properties.csv
    def values(column):
        return {(r.get(column) or "").strip() for r in properties}
    for column in ["avm_estimate", "flood_zone", "walk_score", "transit_score", "bike_score", "building_condition",
                   "building_quality", "num_stories", "irs_agi_per_return", "irs_homeowner_pct"]:
        check("properties.%s blank in every row" % column, values(column), {""})
    for column, value in [("sale_count", "0"), ("nearby_restaurants", "0"), ("nearby_shops", "0"),
                          ("nearby_amenities_total", "0"), ("public_investment_total", "0"),
                          ("has_basement", "false"), ("has_central_ac", "false"),
                          ("opportunity_zone", "false"), ("inspire_eligible", "false"),
                          ("arts_district", "false"), ("lincs_corridor", "false"), ("hud_reo", "false"),
                          ("difficult_development_area", "false"), ("zip_code", "21218"),
                          ("fair_market_rent_2br", "2006"), ("market_median_sale_price", "240000"),
                          ("market_median_dom", "59"), ("market_inventory", "203")]:
        check("properties.%s is %s in every row" % (column, value), values(column), {value})

    check("subjects rows", len(subjects), 3093)
    subject_types = collections.Counter((r.get("subject_type") or "").strip() for r in subjects)
    for kind, claimed in [("person", 2037), ("business", 517),
                          ("organization", 298), ("family", 138)]:
        check("subject %s" % kind, subject_types.get(kind, 0), claimed)

    check("incident_subjects rows", len(incident_subjects), 5451)
    relationships = collections.Counter(
        (r.get("relationship") or "").strip() for r in incident_subjects)
    for relationship, claimed in [("owned", 923), ("operated_at", 675), ("sold", 659),
                                  ("interred_at", 596), ("purchased", 452), ("lived_at", 280)]:
        check("relationship %s" % relationship, relationships.get(relationship, 0), claimed)
    business_ids = {r["id"] for r in subjects if r["subject_type"] == "business"}
    business_links = sum(1 for r in incident_subjects
                         if r["relationship"] == "operated_at" and r["subject_id"] in business_ids)
    check("operated_at links to a business", business_links, 413)

    for filename, table, claimed in [("registered_ips.csv", registered_ips, 37),
                                     ("property_parcels.csv", parcels, 850),
                                     ("grant_program_matches.csv", grant_matches, 5319),
                                     ("neighborhoods.csv", neighborhoods, 5),
                                     ("baseline_snapshots.csv", baseline, 883)]:
        check("%s rows" % filename, len(table), claimed)

    ip_types = collections.Counter((r.get("ip_type") or "").strip() for r in registered_ips)
    for ip_type, claimed in [("trademark", 23), ("patent", 11), ("entity", 3)]:
        check("registered IP %s" % ip_type, ip_types.get(ip_type, 0), claimed)
    check("registered IP matched to a property",
          sum(1 for r in registered_ips if (r.get("property_id") or "").strip()), 16)
    check("neighborhoods with bounds",
          sum(1 for r in neighborhoods if (r.get("bounds") or "").strip()), 0)

    # Section 4c: the City Archives scans
    check("archive_folders.csv rows", len(archive_folders), 31)
    check("archive_scans.csv rows", len(archive_scans), 2260)
    check("archive folder scan counts add up",
          sum(int(r["scans"]) for r in archive_folders), len(archive_scans))
    check("archive distinct pages", len({(r["item"], r["page"]) for r in archive_scans}), 1692)
    check("archive folder page counts add up",
          sum(int(r["pages"]) for r in archive_folders), 1692)
    check("archive buildings", len({r["property_id"] for r in archive_scans}), 142)
    property_ids = {r["id"] for r in properties}
    check("archive buildings in properties.csv",
          len({r["property_id"] for r in archive_scans if r["property_id"] in property_ids}), 142)
    folder_items = {r["item"] for r in archive_folders}
    check("archive scans with a folder", sum(1 for r in archive_scans if r["item"] in folder_items),
          len(archive_scans))
    check("archive scan ids unique", len({r["id"] for r in archive_scans}), len(archive_scans))
    check("archive scans with a caption",
          sum(1 for r in archive_scans if (r["caption"] or "").strip()), len(archive_scans))
    years = [int(r["depicted_on"][:4]) for r in archive_scans if r["depicted_on"]]
    check("archive depicted years", (min(years), max(years)), (1877, 1988))
    doc_says("README.md", "2,260 scans, 1,692")
    doc_says("README.md", "All 142 buildings are in `properties.csv`")
    doc_says("README.md", "| `archive_scans.csv` | 2,260 |")
    doc_says("README.md", "| `archive_folders.csv` | 31 |")

    # Section 4d: the Matterport tours
    check("matterport_tours.csv rows", len(tours), 13)
    check("matterport tour buildings", len({r["property_id"] for r in tours}), 12)
    by_id = {r["id"]: r for r in properties}
    check("matterport tours that join to properties.csv",
          sum(1 for r in tours if r["property_id"] in by_id), len(tours))
    check("matterport tour addresses match properties.csv",
          sum(1 for r in tours if by_id.get(r["property_id"], {}).get("address") == r["address"]), len(tours))
    check("matterport primary tours per building",
          sorted(collections.Counter(r["property_id"] for r in tours if r["is_primary"] == "true").values()),
          [1] * 12)
    check("matterport links are public Matterport shares",
          sum(1 for r in tours if r["share_url"] == "https://my.matterport.com/show/?m=" + r["model_id"]), len(tours))
    check("matterport tour ids unique", len({r["id"] for r in tours}), len(tours))
    for number in ("3011", "3015", "3026", "3107", "3117", "3200", "3224"):
        check("matterport tour in focus area: %s" % number,
              any(r["address"].startswith(number + " Greenmount") for r in tours), True)
    doc_says("README.md", "13 tours of 12 buildings")
    doc_says("README.md", "| `matterport_tours.csv` | 13 |")

    # The October 2026 refresh: what changed (README, "What changed in the October 2026 refresh")
    check("September sensitivity rows in the September package", len(SEPTEMBER_SENSITIVITY_IDS), 52)
    incident_ids = {r["id"] for r in incidents}
    check("September sensitivity rows still present",
          sum(1 for i in SEPTEMBER_SENSITIVITY_IDS if i in incident_ids), 52)
    sensitivity = collections.Counter((r.get("sensitivity") or "").strip() for r in incidents)
    for value, claimed in [("trauma", 84), ("displacement", 27), ("personal_rights", 10),
                           ("commercialization", 5)]:
        check("sensitivity %s" % value, sensitivity.get(value, 0), claimed)

    # Phone numbers: redacted in property_incidents (summary and data), none left anywhere in the file
    check("incident rows with [phone redacted]",
          sum(1 for r in incidents if "[phone redacted]" in r["summary"] + r["data"]), 21)
    check("[phone redacted] occurrences",
          sum((r["summary"] + r["data"]).count("[phone redacted]") for r in incidents), 24)
    check("property_incidents rows with a phone number left",
          [r["id"] for r in incidents if any(PHONE.search(v or "") for v in r.values())], [])
    check("storefront_assessments rows with a business phone number",
          sum(1 for r in storefronts if any(PHONE.search(v or "") for v in r.values())), 39)

    field = [r for r in incidents if r["source"] == "field_report"]
    check("field_report rows from the PI.KL survey", sum(1 for r in field if "PI.KL" in r["summary"]), 17)
    check("other field_report rows (fire, demolition, condemnation)",
          sorted(r["id"] for r in field if "PI.KL" not in r["summary"]),
          ["35475", "35476", "35477", "35478", "35479"])

    # property_id_crosswalk.csv: retired September ids -> the parcel that absorbed them
    check("property_id_crosswalk.csv rows", len(crosswalk), 52)
    check("crosswalk old_id unique", len({r["old_id"] for r in crosswalk}), len(crosswalk))
    check("crosswalk new_id is a property", sum(1 for r in crosswalk if r["new_id"] in property_ids),
          len(crosswalk))
    check("crosswalk old_id is not a property", sum(1 for r in crosswalk if r["old_id"] in property_ids), 0)
    check("crosswalk surviving parcels", len({r["new_id"] for r in crosswalk}), 24)
    absorbed_by = {r["id"]: json.loads(r["absorbed_addresses"] or "[]") for r in properties}
    check("crosswalk old address is in the survivor's absorbed_addresses",
          sum(1 for r in crosswalk if r["old_address"].split(",")[0] in absorbed_by.get(r["new_id"], [])),
          len(crosswalk))
    check("crosswalk old ids into 2801 Greenmount Ave (688)",
          sum(1 for r in crosswalk if r["new_id"] == "688"), 14)
    check("crosswalk covers 2851 Greenmount Ave (old id 2273)",
          [r["new_id"] for r in crosswalk if r["old_id"] == "2273"], ["688"])

    # baseline_snapshots.csv: frozen at t0, keyed on September ids
    with open(os.path.join(ROOT, "baseline_snapshots.csv"), "rb") as handle:
        check("baseline_snapshots.csv unchanged since t0", hashlib.sha256(handle.read()).hexdigest(),
              BASELINE_SHA256)
    old_ids = {r["old_id"] for r in crosswalk}
    check("baseline ids that are neither a property nor a crosswalk old_id",
          {r["property_id"] for r in baseline if r["property_id"] not in property_ids
           and r["property_id"] not in old_ids}, set())
    check("baseline rows on a retired id (join through the crosswalk)",
          sum(1 for r in baseline if r["property_id"] in old_ids), 104)
    check("grant_program_matches property_ids resolve",
          sum(1 for r in grant_matches if r["property_id"] in property_ids), len(grant_matches))

    # New properties.csv columns
    check("properties with a tax sale year", sum(1 for r in properties if r["tax_sale_years"] != "{}"), 155)
    check("properties.city_since_years is {} in every row", values("city_since_years"), {"{}"})
    check("properties.vacant_lot true", sum(1 for r in properties if r["vacant_lot"] == "true"), 58)
    absorbed = [json.loads(r["absorbed_addresses"] or "[]") for r in properties]
    check("properties that absorbed an address", sum(1 for a in absorbed if a), 79)
    check("absorbed addresses", sum(len(a) for a in absorbed), 184)

    # storefront_assessments.csv
    check("storefront_assessments.csv rows", len(storefronts), 264)
    check("storefront one row per property", len({r["property_id"] for r in storefronts}), len(storefronts))
    check("storefront property_ids resolve",
          sum(1 for r in storefronts if r["property_id"] in property_ids), len(storefronts))
    status = collections.Counter(r["status"] for r in storefronts)
    for value, claimed in [("open_active", 87), ("residential", 56), ("vacant_storefront", 49),
                           ("vacant_lot", 39), ("institution", 19), ("office_industrial", 11),
                           ("listed_likely_dead", 2), ("needs_eyes", 1)]:
        check("storefront status %s" % value, status.get(value, 0), claimed)
    confidence = collections.Counter(r["confidence"] for r in storefronts)
    check("storefront confidence", dict(confidence), {"high": 142, "medium": 117, "low": 5})
    check("storefront assessed_on", {r["assessed_on"] for r in storefronts}, {"2026-10-07"})
    check("storefront observed_on set", sum(1 for r in storefronts if r["observed_on"].strip()), 0)
    findings = [f for r in storefronts for f in json.loads(r["evidence"] or "[]")]
    check("storefront evidence findings", len(findings), 1428)

    # property_images.csv
    check("property_images.csv rows", len(images), 3694)
    check("property_images ids unique", len({r["id"] for r in images}), len(images))
    check("property_images property_ids resolve",
          sum(1 for r in images if r["property_id"] in property_ids), len(images))
    check("property_images properties", len({r["property_id"] for r in images}), 348)
    check("property_images distinct image_key", len({r["image_key"] for r in images}), 3090)
    check("property_images image_key format",
          sum(1 for r in images if re.fullmatch(r"img/[0-9a-f]{64}\.jpg", r["image_key"])), len(images))
    check("property_images folders outside the five", {r["folder"] for r in images} - IMAGE_FOLDERS, set())
    for folder, claimed_rows, claimed_files in [("deeds-and-title-chain", 1054, 925),
                                                ("bca-brg4-1", 655, 228), ("loc-sanborn", 4, 2),
                                                ("passano-oneill", 104, 104),
                                                ("pikl-greenmount", 1877, 1831)]:
        check("property_images %s rows" % folder, sum(1 for r in images if r["folder"] == folder), claimed_rows)
        check("property_images %s files" % folder,
              len({r["image_key"] for r in images if r["folder"] == folder}), claimed_files)
    passano = [int(r["depicted_on"][:4]) for r in images if r["folder"] == "passano-oneill" and r["depicted_on"]]
    check("passano-oneill depicted years", (min(passano), max(passano)), (1802, 1938))
    pikl = [r for r in images if r["folder"] == "pikl-greenmount"]
    check("pikl-greenmount subjects", dict(collections.Counter(r["subject"] for r in pikl if r["subject"])),
          {"interior": 873, "detail": 415, "roof": 368, "exterior": 111, "streetscape": 61, "alley": 39, "other": 6})
    check("pikl-greenmount photos", sum(1 for r in pikl if r["category"] == "photo"), 1873)
    check("pikl-greenmount buildings", len({r["property_id"] for r in pikl}), 14)
    check("pikl-greenmount rows with a depicted_address", sum(1 for r in pikl if r["depicted_address"]), 150)
    check("property_images with a depicted_address", sum(1 for r in images if r["depicted_address"]), 150)
    records = [r for r in images if r["folder"] != "pikl-greenmount"]
    check("record scans without a depicted_on", sum(1 for r in records if not r["depicted_on"]), 164)
    check("record scans depicted_source manual", {r["depicted_source"] for r in records}, {"manual"})
    for folder, claimed_rows, claimed_files in [("deeds-and-title-chain", 1054, 925), ("bca-brg4-1", 655, 228),
                                                ("loc-sanborn", 4, 2), ("passano-oneill", 104, 104),
                                                ("pikl-greenmount", 1877, 1831)]:
        doc_says("README.md", "| `%s` | %s | %s |" % (folder, f"{claimed_rows:,}", f"{claimed_files:,}"))
    check("property_images with a depicted_on", sum(1 for r in images if r["depicted_on"]), 1654)
    years = [int(r["depicted_on"][:4]) for r in images if r["depicted_on"]]
    check("property_images depicted years", (min(years), max(years)), (1742, 2023))
    doc_says("README.md", "| `property_images.csv` | 3,694 |")
    doc_says("README.md", "| `storefront_assessments.csv` | 264 |")
    doc_says("README.md", "| `property_id_crosswalk.csv` | 52 |")
    with open(os.path.join(ROOT, "images_base_url.txt"), encoding="utf-8") as handle:
        doc_says("README.md", handle.read().strip())

    # Section 4b: the t0 baseline
    captures = collections.Counter((r.get("captured_on") or "")[:10] for r in baseline)
    check("baseline capture 2026-07-13", captures.get("2026-07-13", 0), 349)
    check("baseline capture 2026-07-22", captures.get("2026-07-22", 0), 534)
    keys = {"property_id", "captured_on", "captured_at"}
    fields = [c for c in baseline[0] if c not in keys]
    check("baseline fields per snapshot", len(fields), 28)
    captured_empty = [c for c in fields if all((r.get(c) or "").strip() in ("", "0") for r in baseline)]
    check("baseline fields captured empty or 0", len(captured_empty), 7)

    # Earliest dated curated record (the README's "back to 1658" claim)
    curated_years = [year_of(r) for r in incidents if not is_admin(r["source"])]
    check("earliest curated record year", min(y for y in curated_years if y), 1658)

    # The people-place graph from the README's incident_subjects row: property <-> subject,
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
    check("graph nodes", len(nodes), 3562)
    check("graph edges", len(edges), 3733)

    # The same numbers, where other docs repeat them. Snippets are built from the data, so a
    # data change that is not carried into these files fails here.
    curated = len(incidents) - administrative
    with_coords = sum(1 for r in properties if (r.get("latitude") or "").strip())
    doc_says("AGENTS.md", "%s administrative rows and %s curated" % (f"{administrative:,}", f"{curated:,}"))
    doc_says("AGENTS.md", "(%d properties)" % len(properties))
    doc_says("PROJECT_IDEAS.md", "covers %d properties" % len(properties))
    doc_says("PROJECT_IDEAS.md", "%d `operated_at` links" % relationships["operated_at"])
    doc_says("LICENSE.md", "of the %s incident rows" % f"{len(incidents):,}")
    doc_says("map/README.md", "properties ≠ %s, incidents ≠ %s, or curated ≠ %s"
             % (f"{len(properties):,}", f"{len(incidents):,}", f"{curated:,}"))
    doc_says("map/README.md", "Markers are the %d properties" % with_coords)
    doc_says("map/app.py", "EXPECTED_PROPERTIES = %d" % len(properties))
    doc_says("map/app.py", "EXPECTED_INCIDENTS = %d" % len(incidents))
    doc_says("map/app.py", "EXPECTED_CURATED = %d" % curated)
    doc_says("site/index.html", '<div class="n">%d</div>' % len(properties))
    doc_says("site/index.html", "%s incident rows of which %s are hand-researched"
             % (f"{len(incidents):,}", f"{curated:,}"))
    doc_says("site/index.html", '<div class="n te">%d</div>' % business_links)
    doc_says("site/index.html", "%d markers" % with_coords)
    doc_says("site/index.html", "<td>registered_ips.csv</td><td>%d</td>" % len(registered_ips))

    # row_counts.txt lists every exported table with its row count.
    with open(os.path.join(ROOT, "row_counts.txt"), encoding="utf-8") as handle:
        listed = dict(line.split(": ") for line in handle.read().split("\n") if line.strip())
    check("row_counts.txt lists every CSV", sorted(listed),
          sorted(f[:-4] for f in os.listdir(ROOT) if f.endswith(".csv")))
    for name, count in listed.items():
        check("row_counts.txt %s" % name, sum(1 for _ in rows(name + ".csv")), int(count))

    # Numbers the October 2026 refresh added to the docs.
    deepest = sorted(depth.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    check("deepest three properties (curated incidents)", deepest, [("2376", 603), ("2332", 293), ("726", 293)])
    check("sdat:owner rows, all verified",
          collections.Counter(r["evidence_status"] for r in incidents if r["source"] == "sdat:owner"),
          collections.Counter({"verified": 454}))
    check("incident categories", len({r["category"] for r in incidents}), 52)
    check("incident_subjects relationships", len(relationships), 299)
    check("parcels matched to a property",
          sum(1 for r in parcels if (r.get("matched_property_id") or "").strip()), 209)
    check("year_built 0", sum(1 for r in properties if r["year_built"] == "0"), 93)
    check("structure_sqft 0", sum(1 for r in properties if r["structure_sqft"] == "0"), 237)
    check("properties with no tax sale year", sum(1 for r in properties if r["tax_sale_years"] == "{}"), 544)
    check("properties that absorbed nothing", sum(1 for r in properties if r["absorbed_addresses"] == "[]"), 620)
    vacant_lot_status = {r["property_id"] for r in storefronts if r["status"] == "vacant_lot"}
    check("storefront vacant_lot that properties.vacant_lot calls false",
          sum(1 for r in properties if r["id"] in vacant_lot_status and r["vacant_lot"] == "false"), 13)
    check("baseline rows that join properties.csv directly",
          sum(1 for r in baseline if r["property_id"] in property_ids), 779)
    check("property_images categories", dict(collections.Counter(r["category"] for r in images)),
          {"photo": 1873, "document": 1807, "plan": 13, "ephemera": 1})
    check("property_images depicted_precision",
          dict(collections.Counter(r["depicted_precision"] for r in images if r["depicted_precision"])),
          {"day": 885, "year": 765, "month": 4})
    september = set(SEPTEMBER_SENSITIVITY_IDS)
    new_flags = collections.Counter(r["source"] for r in incidents
                                    if (r.get("sensitivity") or "").strip() and r["id"] not in september)
    check("sensitivity rows added in October, by source", dict(new_flags),
          {"local_news": 50, "newspapers_com": 20, "census_directory": 2, "public_record": 1, "msa_guide": 1})
    flagged = sum(1 for r in incidents if (r.get("sensitivity") or "").strip())
    doc_says("README.md", "explains why %d incident rows" % flagged)
    doc_says("AGENTS.md", "(%d incidents)" % flagged)
    doc_says("AGENTS.md", "%d `last_sale_price` values are $0" % sum(1 for p in prices if p == 0))
    doc_says("AGENTS.md", "`old_id` → `new_id`, %d rows" % len(crosswalk))
    doc_says("LICENSE.md", "%d of the %s incident rows" % (flagged, f"{len(incidents):,}"))
    doc_says("LICENSE.md", "and added %d" % (flagged - len(SEPTEMBER_SENSITIVITY_IDS)))
    doc_says("DATA_DICTIONARY.md", "`properties.csv` · %d rows" % len(properties))
    doc_says("DATA_DICTIONARY.md", "`property_incidents.csv` · %s rows" % f"{len(incidents):,}")
    doc_says("DATA_DICTIONARY.md", "**administrative** (%s rows); everything else is **curated** (%s)"
             % (f"{administrative:,}", f"{curated:,}"))
    doc_says("DATA_DICTIONARY.md", "`incident_subjects.csv` · %s rows" % f"{len(incident_subjects):,}")
    doc_says("DATA_DICTIONARY.md", "`incident_links.csv` · %s rows" % f"{len(links):,}")
    doc_says("DATA_DICTIONARY.md", "`property_parcels.csv` · %d rows" % len(parcels))
    doc_says("DATA_DICTIONARY.md", "`property_images.csv` · %s rows" % f"{len(images):,}")
    doc_says("DATA_DICTIONARY.md", "`storefront_assessments.csv` · %d rows" % len(storefronts))
    doc_says("DATA_DICTIONARY.md", "`property_id_crosswalk.csv` · %d rows" % len(crosswalk))
    doc_says("DATA_DICTIONARY.md", "**always `%s`**" % properties[0]["fair_market_rent_2br"])
    doc_says("START_HERE.py", "not** %s pieces of curated history" % f"{len(incidents):,}")
    doc_says("PROJECT_IDEAS.md", "%s newspaper clippings" % f"{by_source['newspapers_com']:,}")
    doc_says("PROJECT_IDEAS.md", "%s research white papers" % f"{by_source['whitepaper']:,}")
    doc_says("site/index.html", "%s research white papers" % f"{by_source['whitepaper']:,}")
    doc_says("site/index.html", "%s clippings, %d business-operated-here links"
             % (f"{by_source['newspapers_com']:,}", business_links))
    doc_says("site/index.html", '<div class="val">%s<small>back to 1658' % f"{sum(1 for y in years_all if y and y < 1950):,}")
    doc_says("site/index.html", "<td>property_images.csv</td><td>%s</td>" % f"{len(images):,}")
    doc_says("site/index.html", "<td>storefront_assessments.csv</td><td>%d</td>" % len(storefronts))
    doc_says("site/index.html", "<td>property_id_crosswalk.csv</td><td>%d</td>" % len(crosswalk))
    doc_says("map/README.md", "That gives %s / %s." % (f"{curated:,}", f"{administrative:,}"))
    doc_says("docs/students-and-coding-agents.md", "the %s / %s split" % (f"{curated:,}", f"{administrative:,}"))
    doc_says("docs/students-and-coding-agents.md", "%d / %d / %d depth tiers" % tuple(
        sum(1 for v in depth.values() if v >= n) for n in (1, 10, 25)))
    csv_count = sum(1 for f in os.listdir(ROOT) if f.endswith(".csv"))
    check("exported tables", csv_count, 16)
    doc_says("README.md", "The sixteen exported tables")
    doc_says("map/README.md", "`hud:cdbg` (%d rows)" % by_source["hud:cdbg"])

    failures = [c for c in checks if not c[0]]
    for _, label, actual, claimed in failures:
        print("MISMATCH  %-34s actual=%-8s claimed=%s" % (label, actual, claimed))
    print("%d/%d claims verified against the data." % (
        len(checks) - len(failures), len(checks)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
