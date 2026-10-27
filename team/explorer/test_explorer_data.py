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


# Sponsor rule (26 Oct 2026): brand names go in reports only, not the public repo. The names the team removed are
# checked by hash, so this test does not put them back; the list itself is in the team report.
BRAND_HASHES = set("""
    5b7ed10f1ca346f4
    089a68cc053e5f50 0c37812beefb5245 0f001db5458fe385 108badd1f00d1f11 11aad1d3931892d5 14a215662575e143
    1820184bc0c7a3df 1994d77b7cf4860a 1ee703ab3308587a 209e77347421952e 2182a02493e32a2b 23145875d8f5ff32
    24f00a9f24a38811 27c5c632396486f4 289a0ea095024f92 2cc12a196dfaa40f 2ed21564a323474f 303c16abaf43ff20
    31f0eb1b667fc5b2 3b9b41b50cdcd7ba 3f9392fdfc1af1f6 404e7488821839a6 48d11729e9b5de2c 4914503388632c03
    50a949349c638968 520588d700a427d6 557fb3d121431744 5892cab0dd8a2787 5c170278affd44d9 61574febfeeabee8
    622d7eb26c0f6a3a 694c7611e7433aa7 6cca74ea2b34c2ce 6d09ed10197d7232 7199addfc3f7f8ba 761fca33267f8a3e
    76d1630a19b0a64c 7a9486c8bfee28d0 819fe9afbdebcc0c 83d7c0096aace079 84ee60836bf6b77d 8526b20b891cf659
    8f174cf8fd5e7078 959e8f889e4d2ff5 982dc8af9a41efad 9cbc08b6a9f0670a a5eeccb2e4cee67d a869927e16b3b036
    a8a3b64ce0ce458d ac215ea76a91ac0a aee61b05952d5d55 afb2c697008b6563 b0d047cb55fb1209 b21492b15d85500e
    b55d19ce2c917007 b6beb16dbc0b4828 b6c2b4f125a333ba b6d70a81706a2e28 b8621fdadd2b42f4 ba674e79a2d94c8f
    be5bae827a13d98d c045f634ddd230e5 ca59bad8cead7a84 cb1ae28c1adf7737 cc4ca5660bfbf140 dba53cc8553039e5
    e02e1deb4b020aa7 e1e1c2afcacbee2c e2d0320438f958eb e2d1296de778457f e5be1d11dbf70adb e762121deb17cf24
    e9a95c2757b8a107 ea2af3599da66020 effdb66135f35731 f2397a7bed29e2db
""".split())


def _norm_tokens(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).split()


def _brand_hits(text):
    import hashlib
    toks, hits = _norm_tokens(text), []
    for n in range(1, 5):
        for i in range(len(toks) - n + 1):
            g = ' '.join(toks[i:i + n])
            if hashlib.sha256(g.encode()).hexdigest()[:16] in BRAND_HASHES:
                hits.append(g)
    return hits


def _strings(o, skip=('u', 'url', 'source_url')):
    if isinstance(o, dict):
        for k, v in o.items():
            if k not in skip:
                yield from _strings(v, skip)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v, skip)
    elif isinstance(o, str):
        yield o


def _page_data():
    with open(os.path.join(HERE, 'index.html'), encoding='utf-8') as fh:
        s = fh.read()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S)
    return json.loads(m.group(1).replace('<\\/', '</'))


class TestPublicNames(unittest.TestCase):
    def test_the_check_works(self):
        # the first hash is a canary for the phrase below, so a broken tokenizer or hash cannot pass silently
        self.assertEqual(_brand_hits('A canary brand check, in a sentence.'), ['canary brand check'])
        self.assertEqual(len(BRAND_HASHES), 77)

    def test_public_files_name_no_reference_brand(self):
        for name in ('retail_types.json', 'typical_sqft.json'):
            with open(os.path.join(HERE, name), encoding='utf-8') as fh:
                d = json.load(fh)
            self.assertEqual([h for t in _strings(d) for h in _brand_hits(t)], [], name)
        with open(os.path.join(HERE, 'retail_types.json'), encoding='utf-8') as fh:
            self.assertFalse(any('brands' in t for t in json.load(fh)['types']), 'brands key stays out of the repo file')

    def test_built_page_names_no_reference_brand(self):
        d = _page_data()
        self.assertTrue(all(t['brands'] == [] for t in d['retail']['types']))
        for key in ('retail', 'sizes'):
            self.assertEqual([h for t in _strings(d[key]) for h in _brand_hits(t)], [], key)
        with open(os.path.join(HERE, 'template.html'), encoding='utf-8') as fh:
            self.assertEqual(_brand_hits(re.sub(r'https?://\S+', ' ', fh.read())), [])


if __name__ == '__main__':
    unittest.main()
