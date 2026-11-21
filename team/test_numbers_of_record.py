"""Tests of the numbers of record: the two generated files are current, and the documents quote them.
Run from the repo root:  python3 -m unittest team/test_numbers_of_record.py"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import numbers_of_record as N   # noqa: E402


def read(rel):
    with open(os.path.join(REPO, *rel.split('/')), encoding='utf-8') as fh:
        return fh.read()


class TestNumbersOfRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = N.build()

    def test_the_saved_files_are_what_the_data_gives_today(self):
        self.assertEqual(read('team/numbers_of_record.json'), json.dumps(self.n, indent=1, ensure_ascii=False) + '\n',
                         'rerun team/numbers_of_record.py')
        self.assertEqual(read('team/NUMBERS.md'), N.markdown(self.n), 'rerun team/numbers_of_record.py')

    def test_every_listed_document_quotes_the_numbers_through_markers(self):
        for doc in N.DOCS:
            text = read(doc)
            self.assertGreaterEqual(len(N.MARK.findall(text)), 3, doc + ' quotes almost nothing from the numbers file')
            self.assertEqual(N.fill(text, self.n), text, doc + ' quotes a figure that is not in the data today: rerun team/numbers_of_record.py')

    def test_a_marker_is_rewritten_from_the_numbers(self):
        n = {'a': {'b': [0.0546, 7]}, 'c': 1234, 'd': 0.212}
        self.assertEqual(N.fill('p = <!--=a.b.0|p-->9<!--/-->, <!--=c-->x<!--/--> rows, <!--=d|pct--><!--/-->', n),
                         'p = <!--=a.b.0|p-->0.055<!--/-->, <!--=c-->1,234<!--/--> rows, <!--=d|pct-->21%<!--/-->')
        with self.assertRaises(KeyError):
            N.fill('<!--=no.such.key-->1<!--/-->', n)

    def test_the_figures_the_review_found_inconsistent_are_not_typed_by_hand(self):
        """Outside the markers, a document may not state a p-value or the back-test's loss figures, or one of the
        empty-storefront counts and accuracy figures that the sponsor's review found in different documents."""
        stale = re.compile(r'p\s*=\s*0\.\d+|0\.61[0-9]{2}\b|0\.60[0-9]{2}\b|\b(?:6|11|12|16|22|23) (?:empty|vacant) storefronts?\b|\b9[16]% of (?:reference|the reference)')
        for doc in N.DOCS:
            text = re.sub(r'```.*?```', '', N.MARK.sub('', read(doc)), flags=re.S)
            self.assertEqual(stale.findall(text), [], doc)

    def test_the_headline_numbers_agree_with_each_other(self):
        f, p, b, k = self.n['frontage'], self.n['plan'], self.n['backtest'], self.n['human_checks']
        self.assertEqual(f['parcels'], f['storefronts'] + f['houses'])
        self.assertEqual(f['storefronts'], f['empty'] + f['in_use'])
        self.assertEqual(len(f['empty_addresses']), f['empty'])
        self.assertEqual(p['sheets'], f['empty'], 'one sheet per empty storefront')
        self.assertEqual(sum(p['uses'].values()), p['sheets'])
        self.assertEqual(sum(p['evidence'].values()), p['sheets'])
        self.assertLessEqual(p['ground_floor_sq_ft'], p['ground_floor_sq_ft_at_most'])
        self.assertLessEqual(p['ground_floor_sq_ft_at_most'], p['whole_building_sq_ft'])
        self.assertLess(p['space_rent_low'], p['space_rent_mid'])
        self.assertLess(p['space_rent_mid'], p['space_rent_high'])
        self.assertEqual(b['frontage_storefronts_tested'], f['in_use'])
        self.assertEqual(b['frontage_empty_storefronts_not_tested'], f['empty'])
        self.assertEqual(b['passes_the_agreed_rule'], b['p_1960'] < 0.05 and b['held_out_log_loss'][1] < b['held_out_log_loss'][0])
        self.assertEqual(sum(self.n['score']['evidence_behind_top_candidates'].values()), f['storefronts'])
        self.assertEqual(k['checked_by_lines_unsigned'], len(k['unsigned_files']))

    def test_the_rent_total_is_the_ground_floor_times_the_corridor_level(self):
        """The plan's middle rent is the estimated ground floor times a rent level per sq ft. A building with a listing of
        its own is priced without that listing, so the average level sits near the corridor's, not on it."""
        p, level = self.n['plan'], self.n['comps']['waverly']['rent_level_low_mid_high']
        per_sq_ft = p['space_rent_mid'] / p['ground_floor_sq_ft']
        self.assertAlmostEqual(per_sq_ft, level[1], delta=0.06 * level[1])
        self.assertAlmostEqual(p['space_rent_low'] / p['ground_floor_sq_ft'], level[0], delta=0.06 * level[0])


if __name__ == '__main__':
    unittest.main()
