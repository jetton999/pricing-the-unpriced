"""Tests for the comps engine (standard library only):  python3 -m unittest team/comps/test_comps_engine.py

They check what would make the ranges wrong or unsafe: rows that must never enter, which corridor a row is
counted in, the pooling arithmetic, the own-listing rule, ranges in order, the sales check, that nothing ranks
uses by money, and the words the sponsor's guardrails rule out."""
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


    def test_no_brokers_names_in_notes(self):
        # team rule: no private individuals' names in the public repo; a listing's broker is named by firm only
        pat = re.compile(r"\b[Bb]rokers? [A-Z][\w'.-]+ [A-Z][\w'.-]+,|\((?:[A-Z]\. [A-Z][a-z]+(?:, )?)+\)")
        for name in ('rents.csv', 'benchmarks.csv', 'operators.csv'):
            for x in E.read_csv(name):
                self.assertIsNone(pat.search(x.get('notes') or ''), x['row_id'])

    def test_filters(self):
        self.assertFalse(any(d['fmt'] == 'housing' for d in self.rows))
        self.assertFalse(any(d['sqft'] is not None and d['sqft'] < 300 for d in self.rows))
        self.assertFalse(any(d['fmt'] == 'workshop' and d['sqft'] and d['sqft'] > 6000 for d in self.rows))

    def test_greenmount_numbers(self):
        self.assertEqual(E.greenmount_numbers('3028-3030 Greenmount Ave'), {'3028', '3030'})
        self.assertEqual(E.greenmount_numbers('3117 Greenmount Ave'), {'3117'})
        self.assertEqual(E.greenmount_numbers('2700 Loch Raven Rd'), set())

    def test_corridor_of_each_waverly_row(self):
        """A row belongs to Waverly only if it is on Greenmount in Waverly or on Loch Raven Rd in Better Waverly.
        The Harford Rd row names Waverly in its corridor text and was counted as Waverly until 17 Nov 2026."""
        wav = {d['id']: d for d in self.rows if d['grp'] == 'waverly'}
        for d in wav.values():
            self.assertRegex(d['corridor'], r'^(Greenmount Ave, Waverly|Loch Raven Rd, Better Waverly)', d['id'])
        harford = [d for d in self.rows if 'Harford Rd' in d['corridor']]
        self.assertTrue(harford)
        for d in harford:
            self.assertNotEqual(d['grp'], 'waverly', d['id'])
        self.assertEqual(self.inp.corridor('Harford Rd, 3500 block (21218, east of Waverly)'), 'charles_village')

    def test_rents_in_place_are_read_and_marked(self):
        """The two Greenmount rent rolls the team held (3226 and 3010) enter the model, marked as rents in place."""
        byid = {d['id']: d for d in self.rows}
        for rid, addr in (('R-080', '3226'), ('R-081', '3010'), ('R-004', '3217')):
            self.assertIn(rid, byid)
            self.assertEqual(byid[rid]['kind'], 'in place', rid)
            self.assertIn(addr, byid[rid]['parcels'], rid)
        for d in self.rows:
            self.assertIn(d['kind'], ('asking', 'in place'), d['id'])
        self.assertEqual(byid['R-080']['fmt'], E.MIXED)
        self.assertAlmostEqual(byid['R-080']['nnn'], 25.23 - self.inp.loads['gross'], places=6)

    def test_every_row_can_carry_a_check(self):
        for name in ('rents.csv', 'benchmarks.csv', 'operators.csv'):
            for x in E.read_csv(name):
                self.assertIn('verified_by', x, name)
                self.assertIn('verified_on', x, name)
                self.assertEqual(bool(x['verified_by']), bool(x['verified_on']), x['row_id'])


class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp = E.Inputs(E.load_inputs())
        cls.rows = E.rent_rows(cls.inp)
        cls.m = E.fit(cls.rows)
        cls.out = E.build()

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

    def test_mixed_rows_get_no_use_multiplier(self):
        self.assertEqual(self.m['feff'][E.MIXED], 0.0)
        self.assertNotIn(E.MIXED, self.m['fraw'])

    def test_ranges_in_order_and_every_use_has_one_basis(self):
        d = jload()
        self.assertTrue(0 < d['model']['space']['q'][0] < d['model']['space']['q'][1] < d['model']['space']['q'][2])
        for f, r in d['formats'].items():
            if r.get('not_estimated'):
                continue
            q = r['asking']['q']
            self.assertTrue(0 < q[0] < q[1] < q[2], (f, q))
            self.assertIn(r['asking']['basis'], ('own listings', 'borrowed from cafe', 'corridor level'), f)
            if r['n_listings'] == 0 and not r['borrowed_from']:
                # no listings of its own: the corridor's level, exactly, and it says so
                self.assertEqual(r['asking']['basis'], 'corridor level', f)
                self.assertEqual(q, d['model']['space']['q'], f)
                self.assertTrue(any('no listings' in x for x in r['flags']), f)

    def test_nothing_ranks_uses_by_money(self):
        """v1's supportable rent, mixture and chance of paying are gone, with the settings that fed the money search."""
        d = jload()
        text = json.dumps(d)
        for gone in ('"supportable"', '"can_pay"', '"typical"', '"rankable"', '"wA"', '"plan"', '"approval"', '"money_weight"',
                     '"sigma_default"', '"prior_rows"', '"p10"', '"p50"', '"p90"'):
            self.assertNotIn(gone, text, gone)
        cfg = E.load_inputs()
        for gone in ('plan', 'approval', 'combine', 'sigma_default', 'route_b'):
            self.assertNotIn(gone, cfg, gone)
        for gone in [k for k in cfg if 'calibration' in k or k.startswith('private')]:
            self.assertNotIn(gone, cfg, gone)
        src = read_text(os.path.join(HERE, 'comps_engine.py'))
        for gone in ('def supportable', 'def can_pay', 'def typical'):
            self.assertNotIn(gone, src, gone)

    def test_an_assumed_floor_area_is_said_out_loud(self):
        """Where a sales figure is receipts per business divided by a floor area the team assumed, the inputs name the
        area, the output says how far the verdict depends on it, and the figure is that division."""
        cfg = E.load_inputs()['sales_check']['uses']
        found = 0
        for use, spec in cfg.items():
            for key, pt in (spec.get('sales') or {}).items():
                m = re.search(r'\$([\d,]+)[^÷]*÷ ([\d,]+) sq ft', pt.get('how', ''))
                if not m:
                    self.assertNotIn('assumed_sqft', pt, (use, key))
                    continue
                found += 1
                receipts, area = (float(g.replace(',', '')) for g in m.groups())
                self.assertEqual(pt.get('assumed_sqft'), area, (use, key))
                self.assertAlmostEqual(pt['v'], receipts / area, delta=0.006 * pt['v'], msg=(use, key))
        self.assertGreaterEqual(found, 3)
        for use in ('shop', 'services'):
            ch = self.out['formats'][use]['check']
            self.assertEqual(ch['verdict'], 'covers')
            self.assertLess(ch['assumed_sqft'], ch['covers_up_to_sqft'])
            self.assertLess(ch['covers_up_to_sqft'], ch['does_not_cover_from_sqft'])
            self.assertTrue(any('assumed' in f for f in self.out['formats'][use]['flags']), use)

    def test_a_use_with_one_or_two_listings_says_how_much_of_its_gap_is_kept(self):
        for f, rec in self.out['formats'].items():
            if rec.get('n_listings') in (1, 2) and rec['asking']['basis'] == 'own listings':
                self.assertTrue(any('thin evidence' in x and '%' in x for x in rec['flags']), f)
                self.assertNotIn('mostly pulled back', ' '.join(rec['flags']))

    def test_sales_check_is_a_flag(self):
        self.assertEqual(E.sales_check(20.0, 23.0, 0.1), 'covers')
        self.assertEqual(E.sales_check(20.0, 17.0, 0.1), 'does not cover')
        self.assertEqual(E.sales_check(20.0, 20.5, 0.1), 'too close to call')
        self.assertEqual(E.afford(100.0, 0.1, 15.0), 0.0)            # never below zero
        d = jload()
        m = d['sales_check']['margin']
        for f, r in d['formats'].items():
            ch = r.get('check')
            if r.get('not_estimated'):
                continue
            if r['sales'] is None:
                self.assertIsNone(ch, f)
                self.assertTrue(r['sales_na'], f)
                continue
            s = r['sales']
            self.assertTrue(set(s['scenarios']) <= set(E.SCEN) and 'mid' in s['scenarios'], f)
            self.assertEqual(set(s['afford']), set(s['scenarios']), f)
            self.assertEqual(s['single'], set(s['scenarios']) == {'mid'}, f)
            self.assertIn(ch['verdict'], ('covers', 'does not cover', 'too close to call'), f)
            self.assertEqual(ch['verdict'], E.sales_check(ch['asking_mid'], ch['afford_mid'], m), f)
            self.assertAlmostEqual(ch['asking_mid'], r['asking']['q'][1], places=2, msg=f)
            # the rent a use could pay follows from its scenario by the stated arithmetic
            for k, v in s['scenarios'].items():
                self.assertAlmostEqual(s['afford'][k], max(0.0, s['share'] * v - d['model']['eti_median']), delta=0.02, msg=(f, k))

    def test_counts_of_asking_and_in_place(self):
        b = jload()['built_from']
        self.assertEqual(b['asking'] + b['in_place'], b['rows_used'])
        self.assertEqual(b['in_place_rows'], sorted(d['id'] for d in self.rows if d['kind'] == 'in place'))
        w = jload()['model']['waverly']
        self.assertEqual(w['asking'] + w['in_place'], w['n'])

    def test_own_listing_excluded(self):
        d = jload()
        p = d['parcels']['3117']
        self.assertIn('R-001', p['own_listings'])
        mi = E.fit([r for r in self.rows if r['id'] != 'R-001'])
        loc, sd = E.predict(mi, 'waverly', 'shop')
        self.assertAlmostEqual(p['A']['shop'][0], round(loc, 4), places=4)
        self.assertAlmostEqual(p['space'][0], round(E.level(mi, 'waverly')[0], 4), places=4)
        for a in ('3010', '3226', '3217'):          # a building's own rent in place is left out of its own level too
            self.assertTrue(d['parcels'][a]['own_listings'], a)
            self.assertEqual({r['kind'] for r in d['parcels'][a]['own_rows']}, {'in place'}, a)

    def test_distribution_functions(self):
        loc, s = math.log(20), 0.4
        for p in (0.1, 0.5, 0.9):
            self.assertAlmostEqual(E.cdf_ln(E.q_ln(p, loc, s), loc, s), p, places=9)

    def test_holdout_reported(self):
        h = jload()['holdout']
        self.assertGreaterEqual(h['widen'], 1.0)
        self.assertEqual(h['nominal_hits'] + h['below'] + h['above'], h['n'])
        self.assertLessEqual(h['nominal_ci95'][0], h['nominal_cover'])

    def test_the_estimators_that_were_tried_are_compared_on_the_same_listings(self):
        """The model card says no estimator that was tried gives a better range than the engine as built. If a change
        to the library makes that false, this fails: read the comparison again and rewrite the card."""
        h = jload()['holdout']
        tried = h['alternatives']
        self.assertEqual([x['estimator'] for x in tried][0], 'as built')
        self.assertEqual(len(tried), 6)
        built = tried[0]
        self.assertEqual((built['rows'], built['inside_plain_range'], built['widen'], built['interval_score']),
                         (h['n'], h['nominal_hits'], h['widen'], h['interval_score_model']))
        for x in tried[1:]:
            self.assertEqual(x['rows'], built['rows'], x['estimator'])
            self.assertGreater(x['interval_score'], built['interval_score'], x['estimator'])
        # dropping every multiplier is clearly worse on the middle figure too
        self.assertGreater(tried[-1]['log_rmse'], built['log_rmse'] + 0.05)


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
