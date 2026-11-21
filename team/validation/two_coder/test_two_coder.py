"""Tests of the two-coder kit: the draw is fixed, the sheets carry no code, and the scoring arithmetic is right.
Run from the repo root:  python3 -m unittest team/validation/two_coder/test_two_coder.py"""
import csv
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_sheets as M      # noqa: E402
import score_agreement as S  # noqa: E402


def read(name):
    with open(os.path.join(HERE, name), encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


class TestSheets(unittest.TestCase):
    def test_the_draw_is_fixed_and_balanced(self):
        a, pools, n = M.draw_history()
        b, _, _ = M.draw_history()
        self.assertEqual([(e['sample_id'], e['n']) for e in a], [(e['sample_id'], e['n']) for e in b])
        self.assertEqual(len(a), 200)
        self.assertEqual(sum(1 for e in a if e['stratum'] == 'sponsor records'), 100)
        self.assertEqual(len({e['n'] for e in a}), 200, 'a record drawn twice')
        self.assertEqual(sum(pools.values()), n)

    def test_the_saved_sheets_are_the_draw_and_carry_no_code(self):
        drawn, _, _ = M.draw_history()
        for coder in 'AB':
            h = read(f'history_coder_{coder}.csv')
            self.assertEqual([r['sample_id'] for r in h], [e['sample_id'] for e in drawn])
            self.assertEqual([r['text'] for r in h], [e['text'] for e in drawn])
            for hidden in ('extractor_use_category', 'use_subcategory', 'matched_keyword', 'basis', 'address_method', 'stratum', 'decade', 'kind', 'business'):
                self.assertNotIn(hidden, h[0])
            if not any(r['coded_by'].strip() for r in h):      # a blank sheet shows no code at all, the extractor's included
                for col in ('use_category', 'use_is_dated_to_this_year', 'record_is_about_this_address', 'note', 'saw_other_codes'):
                    self.assertEqual({r[col] for r in h}, {''}, col)
            o = read(f'outcomes_coder_{coder}.csv')
            self.assertEqual(len(o), 52)
            self.assertNotIn('use_today', o[0])
            if not any(r['coded_by'].strip() for r in o):
                self.assertEqual({r['uses_today'] for r in o}, {''})
            self.assertNotIn('reason', o[0])
            self.assertNotIn('summary', o[0], "the sponsor's text is read in its own file, not copied here")
            self.assertTrue(all(r['property_id'] in r['read'] for r in o))

    def test_the_key_points_at_the_right_evidence_rows(self):
        ev = M.rows('team', 'extractor', 'out', 'evidence.csv')
        for k in read('history_key.csv'):
            e = ev[int(k['evidence_row']) - 2]           # row 1 is the header
            self.assertEqual((e['property_id'], e['year'], e['source'], e['use_category']),
                             (k['property_id'], k['year'], k['source'], k['extractor_use_category']))


class TestScoring(unittest.TestCase):
    def test_kappa(self):
        self.assertEqual(S.kappa([(1, 1), (0, 0), (1, 1), (0, 0)]), 1.0)
        self.assertAlmostEqual(S.kappa([(1, 1), (1, 0), (0, 1), (0, 0)]), 0.0)
        # 20 items: both yes 5, both no 10, A yes B no 3, A no B yes 2 -> po 0.75, pe 0.4*0.35 + 0.6*0.65 = 0.53
        pairs = [(1, 1)] * 5 + [(0, 0)] * 10 + [(1, 0)] * 3 + [(0, 1)] * 2
        self.assertAlmostEqual(S.kappa(pairs), (0.75 - 0.53) / (1 - 0.53))

    def test_uses_reads_a_cell(self):
        self.assertEqual(S.uses('Food & Drink ; retail goods'), {'food & drink', 'retail goods'})
        self.assertEqual(S.uses('food and drink, office'), {'food & drink', 'office'})
        self.assertEqual(S.uses(''), set())

    def test_an_unfinished_sheet_is_refused(self):
        blank = read('outcomes_coder_A.csv')
        if any(r['uses_today'].strip() for r in blank):
            self.skipTest('the sheet has been started')
        self.assertTrue(S.problems(blank, 'address', 'uses_today', set(M.CATEGORIES) | {'none'}, 'A', many=True))

    def test_two_coders_who_copy_the_repo_agree_fully(self):
        repo = [r for r in M.rows('team', 'validation', 'outcomes_other_greenmount_2026-10.csv') if r['included'] == 'yes']
        fill = lambda who: [dict(property_id=r['property_id'], address=r['address'], uses_today=r['use_today'], sure='yes', coded_by=who,
                                 saw_other_codes='no') for r in repo]
        o, dis, agreed = S.score_outcomes(fill('AA'), fill('BB'))
        self.assertEqual((o['parcels'], o['parcels_same'], o['items']), (52, 52, 416))
        self.assertEqual((o['agreement'], o['kappa'], o['repo_same']), (1.0, 1.0, 1.0))
        self.assertEqual(dis, [])
        self.assertEqual({r['property_id']: S.uses(r['use_today']) for r in agreed}, {r['property_id']: S.uses(r['use_today']) for r in repo})

    def test_a_coder_who_differs_shows_up(self):
        repo = [r for r in M.rows('team', 'validation', 'outcomes_other_greenmount_2026-10.csv') if r['included'] == 'yes']
        a = [dict(property_id=r['property_id'], address=r['address'], uses_today=r['use_today'], sure='yes', coded_by='AA', saw_other_codes='no') for r in repo]
        b = [dict(x) for x in a]
        b[0]['uses_today'] = 'office' if 'office' not in S.uses(a[0]['uses_today']) else 'automotive'
        o, dis, agreed = S.score_outcomes(a, b)
        self.assertEqual(o['parcels_same'], 51)
        self.assertLess(o['kappa'], 1.0)
        self.assertEqual([d['what'] for d in dis], ['the coders differ'])
        self.assertIn('to be settled', next(r['coded_by'] for r in agreed if r['property_id'] == a[0]['property_id']))


if __name__ == '__main__':
    unittest.main()
