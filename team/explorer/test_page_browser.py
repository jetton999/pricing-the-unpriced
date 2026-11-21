"""What a reader sees on the built page:  python3 -m unittest team/explorer/test_page_browser.py

Opens team/explorer/index.html in a headless browser and reads the rendered page. Needs Playwright for Python
(pip install playwright, then playwright install chromium); without it every test here is skipped, and
test_page_rules.py still checks the page's data. Nothing is fetched from the network.

What it guards (the sponsor's review of 17 November 2026):
  - a building in use, or a house, shows no dollar figure and no recommendation anywhere;
  - every empty storefront shows candidates with their evidence, and a rent for the space with the low case first;
  - the plan has one sheet per empty storefront, never one for a building in use, and never more than three of a kind
    on a block side unless the street already has them;
  - the saved numbers the documents quote (out/page_numbers.json) are what the page gives today.
"""
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    from playwright.sync_api import sync_playwright
    HAVE = True
except ImportError:          # pragma: no cover
    HAVE = False

DOLLARS = re.compile(r'\$\s?\d')


@unittest.skipUnless(HAVE, 'Playwright for Python is not installed')
class TestPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
        cls.page = cls.browser.new_context(viewport={'width': 1440, 'height': 900}).new_page()
        cls.page.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
        cls.errors = []
        cls.page.on('pageerror', lambda e: cls.errors.append(str(e)))
        cls.page.goto('file://' + os.path.join(HERE, 'index.html'))
        cls.page.wait_for_function('typeof window.__ptu === "function"')
        with open(os.path.join(HERE, 'index.html'), encoding='utf-8') as fh:
            m = re.search(r'<script id="data" type="application/json">(.*?)</script>', fh.read(), re.S)
        cls.props = json.loads(m.group(1).replace('<\\/', '</'))['props']

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def tab(self, v):
        self.page.click(f'#tabs button[data-v="{v}"]')

    def pick(self, address):
        """Select a building the way a reader does: type its number in the Find box."""
        self.page.fill('#q', address)
        self.page.wait_for_function(f"document.querySelector('#panel .addr') && document.querySelector('#panel .addr').textContent.startsWith('{address} ')")
        self.page.fill('#q', '')

    def test_1_every_tab_opens_without_a_script_error(self):
        for v in 'bpmwcer':
            self.tab(v)
            self.page.wait_for_timeout(150)
        self.assertEqual(self.errors, [])

    def test_2_no_dollar_figure_and_no_recommendation_on_a_building_in_use_or_a_house(self):
        others = [p for p in self.props if p['availability'] != 'available now']
        self.assertEqual(len(others), 45)
        for p in others:
            self.tab('b')
            self.pick(p['address'])
            panel = self.page.inner_text('#panel')
            self.assertIsNone(DOLLARS.search(panel), f"{p['address']}: {panel[:0]}a dollar figure in the panel")
            self.assertNotIn('Candidates for this empty storefront', panel, p['address'])
            self.assertNotRegex(panel, r'(?i)best fit|recommended use|if this space ever came free|rents from', p['address'])
            if p['availability'] == 'house':
                self.assertIn('no use is suggested here', panel, p['address'])
            else:
                self.assertIn('makes no recommendation for a building in use', panel, p['address'])
                # the scored candidates sit in a fold that is closed until the reader opens it, and say what they are not
                self.assertNotRegex(panel, r'\d+\s*/100', p['address'])
                self.assertFalse(self.page.eval_on_selector('#panel details.ifempty', 'e => e.open'), p['address'])
                self.assertIn('Not a suggestion to replace the business here', self.page.text_content('#panel details.ifempty'), p['address'])
            self.tab('m')
            box = self.page.inner_text('#earnbld')
            self.assertIsNone(DOLLARS.search(box), f"{p['address']}: a dollar figure on the Money page")

    def test_3_every_empty_storefront_shows_candidates_evidence_and_the_low_case_first(self):
        empty = [p for p in self.props if p['availability'] == 'available now']
        self.assertEqual(len(empty), 24)
        for p in empty:
            self.tab('b')
            self.pick(p['address'])
            panel = self.page.inner_text('#panel')
            self.assertIn('CANDIDATES FOR THIS EMPTY STOREFRONT', panel.upper(), p['address'])
            self.assertIn('Evidence here', panel, p['address'])
            self.assertRegex(panel, r'(over|under|the same as) a building with no record', p['address'])
            self.assertRegex(panel, r'from about \$[\d,.]+k?\s*low case', p['address'])
            self.assertIn('whatever the use', panel, p['address'])
            cards = self.page.locator('#panel .verdict .cand').count()
            self.assertTrue(1 <= cards <= 3, p['address'])

    def test_4_the_plan_has_one_sheet_per_empty_storefront_and_keeps_the_cap(self):
        self.tab('p')
        ids = self.page.eval_on_selector_all('#plan article.sheet', 'a => a.map(x => x.id.replace("sheet-", ""))')
        empty = sorted(p['id'] for p in self.props if p['availability'] == 'available now')
        self.assertEqual(sorted(ids), empty)
        n = self.page.evaluate('window.__ptu()')
        self.assertEqual(n['plan']['sheets'], 24)
        self.assertEqual(n['plan']['cap_broken'], [])
        self.assertEqual(sum(n['plan']['evidence'].values()), 24)
        self.assertLessEqual(n['plan']['space_rent_low'], n['plan']['space_rent_mid'])
        self.assertLessEqual(n['plan']['ground_floor_sq_ft'], n['plan']['whole_building_sq_ft'])
        tile = self.page.inner_text('#plantiles')
        self.assertIn('in the low case', tile)
        self.assertNotRegex(self.page.inner_text('#planS'), r'(?i)highest rent|could support|chance it can pay|chance a business')

    def test_5_the_map_colours_a_top_candidate_only_on_empty_storefronts(self):
        self.tab('b')
        self.page.click('#m-rec')
        tip = lambda a: (self.pick(a), self.page.hover(f'#map [data-id="{next(p["id"] for p in self.props if p["address"] == a)}"]'), self.page.inner_text('#tip'))[2]
        self.assertIn('Top candidate', tip('3023'))
        self.assertNotIn('Top candidate', tip('3128'))
        self.page.click('#m-now')

    def test_6_the_saved_numbers_are_what_the_page_gives(self):
        with open(os.path.join(HERE, 'out', 'page_numbers.json'), encoding='utf-8') as fh:
            saved = json.load(fh)
        self.assertEqual(self.page.evaluate('window.__ptu()'), saved)
        self.assertTrue(saved['comps_probe']['within_half_a_percent_of_the_engine'])
        self.assertEqual(saved['storefronts'], 62)
        self.assertEqual(saved['empty'], 24)

    def test_7_marking_a_storefront_empty_plans_it_and_shows_its_rent(self):
        """The reader's switch: 3128 is in use on the tenant list; counted as empty it gets a sheet, and clearing the mark removes it."""
        self.tab('b')
        self.pick('3128')
        self.page.click('#panel [data-vac="empty"]')
        self.assertIn('your mark', self.page.inner_text('#panel'))
        self.assertRegex(self.page.inner_text('#panel'), r'from about \$')
        self.assertEqual(self.page.evaluate('window.__ptu().plan.sheets'), 25)
        self.page.click('#panel [data-vac="reset"]')
        self.assertEqual(self.page.evaluate('window.__ptu().plan.sheets'), 24)
        self.assertIsNone(DOLLARS.search(self.page.inner_text('#panel')))


if __name__ == '__main__':
    unittest.main()
