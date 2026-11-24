"""Tests for the comps engine (standard library only):  python3 -m unittest team/comps/test_comps_engine.py

They check what would make the ranges wrong or unsafe: rows that must never enter, the pooling arithmetic,
the own-listing rule, quantiles in order, and the words
the sponsor's guardrails rule out."""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import comps_engine as E  # noqa: E402

OUT = os.path.join(HERE, 'comps_ranges.json')
BANNED = re.compile(r'\b(apprais\w*|valuation|valued?|undervalued|worth|cap rate|acquisition|acquire)\b', re.I)


def jload(path=None):
    with open(path or OUT, encoding='utf-8') as fh:
        return json.load(fh)


def read_text(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def run_engine(env=None):
    e = dict(os.environ)
    e.update(env or {})
    subprocess.run([sys.executable, os.path.join(HERE, 'comps_engine.py')], check=True, env=e, capture_output=True, text=True)
    with open(OUT, 'rb') as fh:
        return fh.read()


class TestRows(unittest.TestCase):
    def setUp(self):
        self.inp = E.Inputs(E.load_inputs())
        self.rows = E.rent_rows(self.inp)

    def test_every_row_is_sourced(self):
        for d in self.rows:
            self.assertTrue(d['url'].startswith('http'), d['id'])
        for name in ('rents.csv', 'benchmarks.csv', 'operators.csv'):
            for x in E.read_csv(name):
                self.assertTrue(x['source_url'].startswith('http'), x['row_id'])
                self.assertRegex(x['accessed_on'], r'^\d{4}-\d{2}-\d{2}$', x['row_id'])


    def test_filters(self):
        self.assertFalse(any(d['fmt'] == 'housing' for d in self.rows))
        self.assertFalse(any(d['sqft'] is not None and d['sqft'] < 300 for d in self.rows))
        self.assertFalse(any(d['fmt'] == 'workshop' and d['sqft'] and d['sqft'] > 6000 for d in self.rows))

    def test_greenmount_numbers(self):
        self.assertEqual(E.greenmount_numbers('3028-3030 Greenmount Ave'), {'3028', '3030'})
        self.assertEqual(E.greenmount_numbers('3117 Greenmount Ave'), {'3117'})
        self.assertEqual(E.greenmount_numbers('2700 Loch Raven Rd'), set())


class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp = E.Inputs(E.load_inputs())
        cls.rows = E.rent_rows(cls.inp)
        cls.m = E.fit(cls.rows)

    def test_pooling_formula(self):
        m = self.m
        for k in m['post']:
            B = m['B'][k]
            self.assertAlmostEqual(m['post'][k], B * m['mu'][m['city_of'][k]] + (1 - B) * m['raw'][k], places=12)
            self.assertTrue(0 <= B <= 1)

    def test_row_weights_sum_to_one(self):
        w = E.row_weights(self.m, self.rows)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=9)

    def test_fewer_rows_pull_harder(self):
        m = self.m
        one = [k for k in m['n'] if m['n'][k] == 1]
        many = max(m['n'], key=lambda k: m['n'][k])
        for k in one:
            self.assertGreater(m['B'][k], m['B'][many])

    def test_quantiles_in_order(self):
        d = jload()
        for f, r in d['formats'].items():
            for key in ('typical', 'supportable'):
                q = r.get(key)
                if q:
                    self.assertTrue(0 <= q[0] <= q[1] <= q[2], (f, key, q))

    def test_own_listing_excluded(self):
        d = jload()
        p = d['parcels']['3117']
        self.assertIn('R-001', p['own_listings'])
        mi = E.fit([r for r in self.rows if r['id'] != 'R-001'])
        loc, sd = E.predict(mi, 'waverly', 'shop')
        self.assertAlmostEqual(p['A']['shop'][0], round(loc, 4), places=4)

    def test_distribution_functions(self):
        loc, s = math.log(20), 0.4
        for p in (0.1, 0.5, 0.9):
            self.assertAlmostEqual(E.cdf_ln(E.q_ln(p, loc, s), loc, s), p, places=9)
            self.assertAlmostEqual(E.cdf_tp(E.q_tp(p, 5.9, 0.6, 0.3), 5.9, 0.6, 0.3), p, places=9)

    def test_holdout_reported(self):
        h = jload()['holdout']
        self.assertGreaterEqual(h['widen'], 1.0)
        self.assertEqual(h['nominal_hits'] + h['below'] + h['above'], h['n'])
        self.assertLessEqual(h['nominal_ci95'][0], h['nominal_cover'])


class TestWords(unittest.TestCase):
    def test_no_guardrail_words_in_outputs(self):
        d = jload()
        d.pop('sources')   # source titles are quoted as published (e.g. a valuation firm's guidance)
        text = json.dumps(d)
        hits = BANNED.findall(text)
        self.assertEqual(hits, [], hits)

    def test_deterministic(self):
        self.assertEqual(run_engine(), run_engine())


if __name__ == '__main__':
    unittest.main()
