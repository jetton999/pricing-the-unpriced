"""Tests for back-test v2 (standard library only):  python3 -m unittest team/validation/test_backtest.py"""
import csv
import json
import math
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import backtest as B  # noqa: E402


class TestStatistics(unittest.TestCase):
    def test_logit_recovers_known_coefficients(self):
        rng = random.Random(1)
        X, y = [], []
        for _ in range(4000):
            j = rng.randrange(2)
            x = rng.random() * 2
            z = (-1.0 if j == 0 else 0.5) + 0.8 * x
            X.append([1.0 if j == 0 else 0.0, 1.0 if j == 1 else 0.0, x])
            y.append(1.0 if rng.random() < 1 / (1 + math.exp(-z)) else 0.0)
        beta, _ = B.fit_logit(X, y)
        self.assertAlmostEqual(beta[0], -1.0, delta=0.15)
        self.assertAlmostEqual(beta[1], 0.5, delta=0.15)
        self.assertAlmostEqual(beta[2], 0.8, delta=0.12)

    def test_score_is_zero_when_history_is_flat(self):
        rows = [('a', 0, 1.0, 0, 1.0), ('a', 1, 1.0, 0, 0.0), ('b', 0, 1.0, 0, 0.0), ('b', 1, 1.0, 0, 1.0)]
        self.assertAlmostEqual(B.score_stat(rows, [r[2] for r in rows]), 0.0)

    def test_auc(self):
        self.assertEqual(B.auc([0.9, 0.8, 0.1], [1, 1, 0]), 1.0)
        self.assertEqual(B.auc([0.1, 0.9], [1, 0]), 0.0)
        self.assertEqual(B.auc([0.5, 0.5], [1, 0]), 0.5)

    def test_permutation_p_is_a_probability_and_repeatable(self):
        data = B.other_blocks()
        rows = B.design(data, 1960)
        p1, _ = B.permutation_p(rows, data, n=300, seed=5)
        p2, _ = B.permutation_p(rows, data, n=300, seed=5)
        self.assertEqual(p1, p2)
        self.assertTrue(0 < p1 <= 1)


class TestData(unittest.TestCase):
    def test_records_after_the_cut_are_never_used(self):
        d = B.decades([('p', 'retail goods', 1955), ('p', 'retail goods', 1961), ('p', 'office', 1990)], 1960)
        self.assertEqual(d['p']['retail goods'], {1950})
        self.assertNotIn('office', d['p'])

    def test_outcome_coding(self):
        with open(os.path.join(HERE, 'outcomes_other_greenmount_2026-10.csv'), encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        frontage = {r['property_id'] for r in csv.DictReader(open(os.path.join(B.REPO, 'team', 'week1', 'out', 'focus_area_properties.csv'), encoding='utf-8-sig'))
                    if r['block_side_id'] in B.FRONTAGE_SIDES}
        props = {r['id'] for r in csv.DictReader(open(os.path.join(B.REPO, 'properties.csv'), encoding='utf-8-sig'))}
        for r in rows:
            self.assertIn(r['property_id'], props)
            self.assertNotIn(r['property_id'], frontage)
            self.assertIn('blind to history', r['coded_by'])
            if r['included'] == 'yes':
                cats = r['use_today'].split(' ; ')
                self.assertTrue(cats and all(c in B.CATS for c in cats), r)
                self.assertIn(r['coding_confidence'], ('high', 'medium', 'low'))
            else:
                self.assertTrue(r['reason'].startswith('left out'))

    def test_frontage_is_the_same_69(self):
        self.assertEqual(B.frontage()['n_unoccupied'] + len(B.frontage()['parcels']), 69)


class TestResults(unittest.TestCase):
    def test_results_follow_the_plan(self):
        with open(os.path.join(HERE, 'out', 'backtest_v2.json'), encoding='utf-8') as fh:
            r = json.load(fh)
        self.assertEqual(r['permutations'], 10000)
        self.assertEqual([a['cut'] for a in r['other_blocks']], [1960, 1940])
        self.assertIn('p_perm', r['decision'])
        self.assertEqual(r['decision']['passes'], r['decision']['p_perm'] < 0.05 and r['decision']['transfer_better'])


if __name__ == '__main__':
    unittest.main()
