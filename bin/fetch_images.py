#!/usr/bin/env python3
"""
Download the images listed in property_images.csv into images/ (gitignored). Standard library
only. No login: the bucket is public, read-only, at the URL in images_base_url.txt.

    python3 bin/fetch_images.py                          # everything (about 420 MB)
    python3 bin/fetch_images.py --folder loc-sanborn     # one folder
    python3 bin/fetch_images.py --property 688           # one property's images
    python3 bin/fetch_images.py --dry-run                # count and size nothing; just list

What is in it. Scans of public records the sponsor collected: recorded deeds, liens and city
building-permit cards (deeds-and-title-chain), the 1896-1915 City tax ledgers and assessment
rolls (bca-brg4-1), and four 1915 Sanborn sheets (loc-sanborn). Every file was re-encoded as JPEG
with all metadata removed. Documents are at most 2,048 px on the long side, photos 1,600 px.

Each image_key is content-addressed (img/<sha256>.jpg): a key never changes meaning, so a file
already on disk is never fetched again. One scan filed on several properties is one file and
several rows. The captions describe a scan; they are not a transcription.
"""
import argparse
import csv
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "images")


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--folder", help="only this folder (see the folder column)")
    parser.add_argument("--property", help="only this property_id")
    parser.add_argument("--dry-run", action="store_true", help="list what would be fetched")
    args = parser.parse_args()

    with open(os.path.join(ROOT, "images_base_url.txt"), encoding="utf-8") as handle:
        base = handle.read().strip().rstrip("/")
    with open(os.path.join(ROOT, "property_images.csv"), newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows = [r for r in rows if (not args.folder or r["folder"] == args.folder)
            and (not args.property or r["property_id"] == args.property)]
    keys = sorted({r["image_key"] for r in rows})
    todo = [k for k in keys if not os.path.exists(os.path.join(OUT, k))]
    print(f"{len(rows)} rows, {len(keys)} files, {len(keys) - len(todo)} already in images/")
    if args.dry_run:
        for key in todo:
            print(f"{base}/{key}")
        return 0

    failed = 0
    for n, key in enumerate(todo, 1):
        path = os.path.join(OUT, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        request = urllib.request.Request(f"{base}/{key}", headers={"User-Agent": "pricing-the-unpriced/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
        except OSError as error:
            print(f"  {key}: {error}", file=sys.stderr)
            failed += 1
            continue
        with open(path + ".part", "wb") as handle:
            handle.write(data)
        os.replace(path + ".part", path)
        if n % 100 == 0:
            print(f"  {n}/{len(todo)}")
    print(f"fetched {len(todo) - failed}, failed {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
