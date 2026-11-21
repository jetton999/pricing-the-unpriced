#!/usr/bin/env python3
"""Read the headline numbers off the built page and save them, so that documents quote the page and not memory.

    python3 team/explorer/page_numbers.py            # writes team/explorer/out/page_numbers.json
    python3 team/explorer/page_numbers.py --check    # exit 1 if the saved file is not what the page gives today

The score and the plan are computed in the page's own script, so the only honest way to quote them is to ask the page.
This opens team/explorer/index.html in a headless browser and calls its test hook, window.__ptu(), which reruns the
ranking from the agreed weights whatever the sliders say. Needs Playwright for Python (pip install playwright, then
playwright install chromium); nothing else in the repo does. team/numbers_of_record.py reads the saved file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'page_numbers.json')


def read_page(path=None):
    from playwright.sync_api import sync_playwright
    path = path or os.path.join(HERE, 'index.html')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        page.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())   # fonts only; nothing leaves
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('file://' + path)
        page.wait_for_function('typeof window.__ptu === "function"')
        numbers = page.evaluate('window.__ptu()')
        browser.close()
    if errors:
        raise RuntimeError('the page reported script errors: ' + '; '.join(errors[:3]))
    return numbers


def dump(numbers):
    return json.dumps(numbers, indent=1, sort_keys=True, ensure_ascii=False) + '\n'


def main():
    text = dump(read_page())
    if '--check' in sys.argv:
        with open(OUT, encoding='utf-8') as fh:
            if fh.read() != text:
                print('team/explorer/out/page_numbers.json is out of date: rerun team/explorer/page_numbers.py')
                return 1
        print('page_numbers.json matches the page')
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    n = json.loads(text)
    print(f"wrote {os.path.relpath(OUT, os.path.dirname(os.path.dirname(HERE)))}: {n['storefronts']} storefronts, {n['empty']} empty, "
          f"{n['plan']['sheets']} sheets; cafe is the top candidate on {n['ranking'][0]['cafe_top']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
