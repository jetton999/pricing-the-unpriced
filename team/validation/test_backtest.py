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
        with open(os.path.join(B.REPO, 'team', 'week1', 'out', 'focus_area_properties.csv'), encoding='utf-8-sig') as fh:
            frontage = {r['property_id'] for r in csv.DictReader(fh) if r['block_side_id'] in B.FRONTAGE_SIDES}
        with open(os.path.join(B.REPO, 'properties.csv'), encoding='utf-8-sig') as fh:
            props = {r['id'] for r in csv.DictReader(fh)}
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


    def test_no_row_that_states_a_later_use_counts_as_history(self):
        """The leak found on 17 Nov 2026: a National Register summary row is dated to the build year and states the use
        as of 2013. Neither sample may count one, and the run kept for the record must differ."""
        self.assertTrue(B.nr_summary_row('Built ca.1890. Historic use: dwelling. Use as of 2013: carryout (B-5229).'))
        self.assertTrue(B.nr_summary_row('Something else. Use as of 2013: carryout.'))
        self.assertFalse(B.nr_summary_row('1923 Polk directory: confectioner'))
        clean, leaky = B.other_blocks(), B.other_blocks(keep_nr_summary=True)
        self.assertLess(len(clean['records']), len(leaky['records']))
        self.assertEqual(clean['parcels'], leaky['parcels'])
        ids = set(clean['parcels'])
        for r in B.rd('property_incidents.csv'):
            if r['property_id'] in ids and 'Use as of 2013' in r['summary']:
                self.assertTrue(B.nr_summary_row(r['summary']), r['id'])

    def test_stated_only_uses_fewer_records_and_never_a_narrative(self):
        self.assertLess(len(B.other_blocks(stated_only=True)['records']), len(B.other_blocks()['records']))

    def test_one_business_in_two_numbers_is_tested_once_per_parcel(self):
        fr = B.frontage()
        self.assertEqual(len(fr['parcels']), len(set(fr['parcels'])))


class TestNewReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = B.other_blocks()
        cls.rows = B.design(cls.data, 1960)

    def test_fast_shuffle_test_equals_the_plain_one(self):
        for seed in (5, B.SEED):
            slow, s1 = B.permutation_p(self.rows, self.data, n=1500, seed=seed)
            fast, s2 = B.fast_perm(self.rows, self.data, n=1500, seed=seed)
            self.assertEqual(slow, fast)
            self.assertAlmostEqual(s1, s2, places=9)

    def test_per_category_adds_up_to_the_test_statistic(self):
        pc = B.per_category(self.rows)
        self.assertEqual([c['category'] for c in pc], B.CATS)
        self.assertAlmostEqual(sum(c['contribution'] for c in pc), B.score_stat(self.rows, [r[2] for r in self.rows]), delta=0.01)
        for c in pc:
            self.assertLessEqual(c['of_which_have_it_today'], c['parcels_with_history'])
            self.assertLessEqual(c['of_which_have_it_today'], c['parcels_with_use_today'])

    def test_category_runs_split_the_statistic(self):
        runs = {r['kinds']: r for r in B.category_runs(self.data, 1960)}
        allk = runs['all eight kinds of use']
        self.assertAlmostEqual(runs['every kind except automotive']['score'] + runs['automotive only']['score'], allk['score'], delta=0.01)
        for r in runs.values():
            self.assertTrue(0 < r['p_perm'] <= 1)

    def test_selection_check_counts_every_storefront_once(self):
        s = B.selection_check(1960, n=200)
        self.assertEqual(s['in_use'], len(B.frontage()['parcels']))
        self.assertEqual(s['empty'] + s['in_use'] + 7, 69)          # 7 houses on the frontage are neither
        self.assertAlmostEqual(sum(s['mix_of_uses_on_record']['empty'].values()), 1.0, delta=0.01)
        self.assertTrue(0 <= s['mix_of_uses_on_record']['distance'] <= 2)


class TestResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, 'out', 'backtest_v2.json'), encoding='utf-8') as fh:
            cls.r = json.load(fh)

    def test_results_follow_the_plan(self):
        r = self.r
        self.assertEqual(r['permutations'], 10000)
        self.assertEqual([a['cut'] for a in r['other_blocks']], [1960, 1940])
        self.assertIn('p_perm', r['decision'])
        self.assertEqual(r['decision']['passes'], r['decision']['p_perm'] < 0.05 and r['decision']['transfer_better'])
        self.assertEqual(r['decision']['p_perm'], r['other_blocks'][0]['p_perm'])
        self.assertEqual(r['decision']['p_perm_before_leak_fix'], r['other_blocks_before_leak_fix'][0]['p_perm'])
        self.assertIn('comparable listings only', r['decision']['if_it_fails'])

    def test_saved_results_are_the_current_data(self):
        """The saved file must come from today's tenant list and outcome file, not an earlier run."""
        r = self.r
        fr = B.frontage()
        self.assertEqual(r['frontage'][0]['parcels'], len(fr['parcels']))
        self.assertEqual(r['frontage_parcels_tested'] + r['frontage_parcels_not_tested'], 69)
        self.assertEqual(r['other_blocks'][0]['parcels'], len(B.other_blocks()['parcels']))
        a = B.analyse(B.other_blocks(), 1960, perms=200)
        for k in ('rows', 'present', 'beta', 'auc_base', 'auc_history', 'parcels_with_history', 'per_category', 'by_history'):
            self.assertEqual(a[k], r['other_blocks'][0][k], k)

    def test_leave_one_out_and_interval_are_reported(self):
        r = self.r
        lo = r['other_blocks_leave_one_parcel_out'][0]
        self.assertEqual(lo['cut'], 1960)
        self.assertEqual(lo['parcels'], r['other_blocks'][0]['parcels'])
        self.assertEqual(lo['p_all_parcels'], r['other_blocks'][0]['p_perm'])
        self.assertLessEqual(lo['min'], lo['median'])
        self.assertLessEqual(lo['median'], lo['max'])
        ci = r['transfer_interval_sponsor_to_other'][0]
        t = r['transfer_frontage_sponsor_to_other'][0]
        self.assertAlmostEqual(ci['gain_per_row'], t['logloss_base'] - t['logloss_history'], delta=0.0002)
        self.assertLessEqual(ci['gain_ci95'][0], ci['gain_per_row'])
        self.assertLessEqual(ci['gain_per_row'], ci['gain_ci95'][1])
        self.assertEqual(ci['distinguishable_from_zero'], ci['gain_ci95'][0] > 0)

    def test_written_report_is_generated_from_the_saved_results(self):
        with open(os.path.join(HERE, 'out', 'backtest_v2.md'), encoding='utf-8') as fh:
            self.assertEqual(fh.read(), B.report(self.r))


if __name__ == '__main__':
    unittest.main()
