#!/usr/bin/env python3
"""
Write archive_folders.csv and archive_scans.csv: the Baltimore City Archives DHCD Waverly files
(record group BRG48-43-10) as the sponsor's Corridor app shows them to the public. Standard
library only. No login and no credentials: the signed-out City Archives viewer is public, and
this reads exactly what that page serves.

    python3 bin/fetch_archive_scans.py                # fetch the live page, rewrite both CSVs
    python3 bin/fetch_archive_scans.py --from-file page.html   # parse a saved copy of the page
    python3 bin/fetch_archive_scans.py --dry-run      # print the summary, write nothing

What is in it. Thirty-one DHCD folders of 1970s and 1980s Waverly planning papers (urban renewal
plan, parking lots, facade work, design standards, consultants, meetings), scanned one image per
page. A page that concerns several buildings is filed on each of them, so one page can appear in
more than one row. The viewer shows only visible scans from the corridor organization, so nothing
hidden or private is here.

The captions are one line each, written by a vision model or by hand. They describe a scan; they
are not a transcription. Read the scan (`scan_url`) before relying on one.
"""
import argparse
import collections
import csv
import html
import io
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://greenmountcorridor.com"
PAGE = BASE + "/properties/gallery?gal_source=archives"

SCAN_COLUMNS = ["id", "property_id", "address", "item", "reference", "folder_title", "page",
                "category", "subject", "caption", "depicted_on", "depicted_precision",
                "depicted_address", "scan_url", "original_url"]
FOLDER_COLUMNS = ["item", "reference", "title", "scans", "pages", "properties",
                  "first_year", "last_year"]


def load_page(path=None):
    if path:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    else:
        request = urllib.request.Request(PAGE, headers={"User-Agent": "pricing-the-unpriced/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            text = response.read().decode("utf-8", errors="replace")
    match = re.search(r'<script[^>]*data-page[^>]*>(.*?)</script>', text, re.S)
    if not match:
        sys.exit("could not find the page data; the viewer may have changed")
    props = json.loads(html.unescape(match.group(1)))["props"]
    if not props.get("public_view"):
        sys.exit("the page was not the signed-out archive viewer; refusing to write anything")
    return props


def absolute(url):
    return url if url.startswith("http") else BASE + url


def build(props):
    addresses = {row["id"]: row["address"] for row in props["properties"]}
    folders = {f["item"]: f for f in props["archive_folders"]}
    scans = []
    for photo in props["photos"]:
        located = photo.get("archive")
        if not located or located["item"] not in folders:
            continue
        folder = folders[located["item"]]
        scans.append({
            "id": photo["id"], "property_id": photo["property_id"],
            "address": addresses.get(photo["property_id"], ""),
            "item": located["item"], "reference": folder["reference"], "folder_title": folder["title"],
            "page": located["page"], "category": photo.get("category") or "",
            "subject": photo.get("subject") or "", "caption": (photo.get("caption") or "").strip(),
            "depicted_on": (photo.get("depicted_on") or "")[:10],
            "depicted_precision": photo.get("depicted_precision") or "",
            "depicted_address": photo.get("depicted_address") or "",
            "scan_url": absolute(photo["large_url"]), "original_url": absolute(photo["url"]),
        })
    scans.sort(key=lambda s: (s["item"], s["page"], s["id"]))

    grouped = collections.defaultdict(list)
    for scan in scans:
        grouped[scan["item"]].append(scan)
    rows = []
    for item in sorted(folders):
        group = grouped.get(item, [])
        years = [int(s["depicted_on"][:4]) for s in group if s["depicted_on"]]
        rows.append({
            "item": item, "reference": folders[item]["reference"], "title": folders[item]["title"],
            "scans": len(group), "pages": len({s["page"] for s in group}),
            "properties": len({s["property_id"] for s in group}),
            "first_year": min(years) if years else "", "last_year": max(years) if years else "",
        })
    return rows, scans


def write(name, columns, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    with open(os.path.join(ROOT, name), "w", newline="", encoding="utf-8") as handle:
        handle.write(buffer.getvalue())


def update_row_counts(counts):
    path = os.path.join(ROOT, "row_counts.txt")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    for name, total in counts.items():
        line = f"{name}: {total}"
        if re.search(rf"^{name}: \d+$", text, re.M):
            text = re.sub(rf"^{name}: \d+$", line, text, flags=re.M)
        else:
            text = text.rstrip("\n") + "\n" + line + "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--from-file", help="parse a saved copy of the viewer page")
    parser.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    args = parser.parse_args()
    folders, scans = build(load_page(args.from_file))
    print(f"archive_folders: {len(folders)} folders, {sum(1 for f in folders if f['scans'])} with scans")
    print(f"archive_scans:   {len(scans)} scans, {len({(s['item'], s['page']) for s in scans})} distinct pages, "
          f"{len({s['property_id'] for s in scans})} properties")
    if args.dry_run:
        print("dry run: nothing written")
        return
    write("archive_folders.csv", FOLDER_COLUMNS, folders)
    write("archive_scans.csv", SCAN_COLUMNS, scans)
    update_row_counts({"archive_folders": len(folders), "archive_scans": len(scans)})


if __name__ == "__main__":
    main()
