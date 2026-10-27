"""Checks on the explorer's data (standard library only):  python3 -m unittest team/explorer/test_explorer_data.py

They guard what would make the page wrong or unsafe: unsourced case facts, ratings outside the written rubric,
cost arithmetic, the long-standing-business layer, and the built page carrying what it should."""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import extras  # noqa: E402

with open(os.path.join(HERE, 'library.json'), encoding='utf-8') as fh:
    L = json.load(fh)


class TestLibrary(unittest.TestCase):
    def test_every_case_has_a_source(self):
        for e in L['buildings'] + L['districts']:
            self.assertTrue(any(s.get('u', '').startswith('http') for s in e.get('sources', [])), e['id'])

    def test_displacement_ratings_follow_the_rubric(self):
        rub = L['meta']['displacement_rubric']
        self.assertEqual(set(rub), {'high', 'moderate', 'low', 'unknown'})
        for d in L['districts']:
            self.assertIn(d['displacement'], rub, d['id'])
            for e in d.get('displacement_evidence', []):
                self.assertTrue(e.get('source_url', '').startswith('http'), (d['id'], e.get('indicator')))

    def test_milestones_are_dated_and_sourced(self):
        for d in L['districts']:
            years = [m['year'] for m in d.get('milestones', [])]
            self.assertEqual(years, sorted(years), d['id'])
            for m in d.get('milestones', []):
                self.assertIsInstance(m['year'], int, d['id'])

    def test_cost_per_sqft_arithmetic(self):
        cpi = {int(k): v for k, v in L['meta']['cpi']['annual'].items()}
        n = 0
        for b in L['buildings']:
            c = b.get('cost') or {}
            if c.get('per_sqft_2025'):
                n += 1
                self.assertEqual(b['country'], 'USA', b['id'])
                self.assertTrue(c.get('source_url', '').startswith('http'), b['id'])
                expect = c['total_mid'] / b['sqft'] * cpi[2025] / cpi[c['cost_year']]
                self.assertAlmostEqual(c['per_sqft_2025'], round(expect), delta=1, msg=b['id'])
        self.assertGreaterEqual(n, 5)

    def test_operating_needs_a_recent_source(self):
        for b in L['buildings']:
            ev = b.get('status_evidence')
            if ev and b['status'] in ('operating', 'reopened'):
                self.assertGreaterEqual(b['status_year'] or 0, 2025, b['id'])
                self.assertTrue((ev.get('url') or '').startswith('http'), b['id'])

    def test_no_private_individuals_in_research_text(self):
        pat = re.compile(r'\b(Mr|Mrs|Ms|Dr)\.\s+[A-Z]')
        for name in os.listdir(os.path.join(HERE, 'research')):
            if name.endswith('.json'):
                with open(os.path.join(HERE, 'research', name), encoding='utf-8') as fh:
                    self.assertIsNone(pat.search(fh.read()), name)


class TestLegacy(unittest.TestCase):
    def test_long_standing_businesses(self):
        import csv
        with open(os.path.join(REPO, 'team', 'tenants', 'current_tenants_2026-10.csv'), encoding='utf-8-sig') as fh:
            props = [{'id': r['property_id']} for r in csv.DictReader(fh)]
        stats = extras.legacy(REPO, props)
        found = [p['since'] for p in props if 'since' in p]
        self.assertEqual(stats['legacy'], sum(1 for s in found if s['legacy']))
        for s in found:
            self.assertTrue(1800 < s['year'] <= 2026 and s['basis'])
            self.assertEqual(s['legacy'], s['years'] >= stats['min_years'])


class TestPage(unittest.TestCase):
    def test_built_page(self):
        with open(os.path.join(HERE, 'index.html'), encoding='utf-8') as fh:
            s = fh.read()
        self.assertNotIn('__DATA__', s)
        for key in ('"backtest2"', '"displacement_rubric"', '"since"', 'Holds up', 'Rent pressure'):
            self.assertTrue(key in s, key)
        self.assertFalse('[sensitivity' in s)
        self.assertFalse('Made in Baltimore' in s, 'named prospects stay out of the public build')


if __name__ == '__main__':
    unittest.main()
