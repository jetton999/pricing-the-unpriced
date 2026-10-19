"""Tests for the use-history extractor. Run from the repo root:

    python3 -m unittest discover team/extractor
"""
import os, sys, csv, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract as X  # noqa: E402
from rules import classify, classify_sanborn  # noqa: E402


class Rules(unittest.TestCase):
    def test_uses(self):
        cases = {
            'Chant Louis C saloon': 'food & drink',
            'Zoll Henry C, livery,': 'automotive',
            'Inspect for motion pictures': 'entertainment & assembly',
            'Convert garage to roller skating rink': 'entertainment & assembly',
            'Sam Lee Laundry': 'personal services',
            'Fink & Holmes dry gds': 'retail goods',
            'Waverly Bldg Assn': 'office',
            'Chemical Engine Co No 4': 'institutional & religious',
            "Franz H. Samstag's soft drinks store (1928)": 'food & drink',
            'Raze frame dwelling': 'vacant',
        }
        for text, cat in cases.items():
            self.assertEqual(classify(text)[0], cat, text)

    def test_building_words_are_not_uses(self):
        self.assertEqual(classify('Erect metal garage 10x16')[0], 'residential')   # a backyard garage
        self.assertEqual(classify('Erect one 1-story brick store')[1], 'store building (generic)')
        self.assertEqual(classify('Replace flat wall sign')[0], '')
        self.assertEqual(classify('2936 Greenmount was a two-story brick dwelling near the ballpark')[0], 'residential')
        self.assertEqual(classify('the 3200 block as new 7-room, 2-story rowhouses (Cityco Realty Co.)')[0], 'residential')
        self.assertEqual(classify('Theatre is a house of moving pictures')[0], 'entertainment & assembly')
        self.assertEqual(classify('used as a store and dwelling')[1], 'store building (generic)')

    def test_sanborn_labels(self):
        self.assertEqual(classify_sanborn('D', 'dwelling')[0], 'residential')
        self.assertEqual(classify_sanborn('S', 'store')[1], 'store building (generic)')
        self.assertEqual(classify_sanborn('Moving Pictures', '')[0], 'entertainment & assembly')
        self.assertEqual(classify_sanborn('Sal.', 'saloon')[0], 'food & drink')


class Addresses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.A = X.Addresser(X.load_frontage())

    def test_exact_and_ranges(self):
        self.assertEqual(self.A.assign(3117)[1], 'exact')
        p, how = self.A.assign(3228)          # inside the 3226-3240 store row
        self.assertEqual(p['address'].split()[0], '3226')
        p, how = self.A.assign(3101, 3101, 3103)
        self.assertEqual((p['address'].split()[0], how), ('3103', 'range'))

    def test_parity_is_kept(self):
        p, _ = self.A.assign(3102)
        self.assertEqual(int(p['address'].split()[0]) % 2, 0)

    def test_range_parser(self):
        self.assertEqual(X.parse_range('range 3226-3240'), (3226, 3240))
        self.assertEqual(X.parse_range('3100-02 Greenmount'), (3100, 3102))


class Crosswalk(unittest.TestCase):
    def test_known_anchors(self):
        rows = {int(r['old_york_number']): int(r['new_greenmount_number'])
                for r in csv.DictReader(open(os.path.join(X.EVIDENCE, 'york_crosswalk.csv'), encoding='utf-8'))}
        # stated in the sponsor records or printed on the 1915 / 1928 Sanborn sheets
        for old, new in {1102: 3200, 1116: 3224, 1027: 3117, 1038: 3126, 1047: 3139}.items():
            self.assertEqual(rows.get(old), new, old)


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.props, cls.E, cls.sens = X.build()
        cls.spans = X.spans(cls.E)

    def test_frontage_count(self):
        self.assertEqual(len(self.props), 79)

    def test_every_row_has_a_source(self):
        self.assertTrue(all(e['source'] and e['source_ref'] for e in self.E.rows))

    def test_spans_merge_close_years(self):
        s = [r for r in self.spans if r['address'].startswith('3211 ') and r['use_category'] == 'entertainment & assembly']
        self.assertTrue(any(int(r['end_year']) - int(r['start_year']) >= 40 for r in s), s)

    def test_reference_parse(self):
        refs = X.parse_reference(X.rp('team', 'week1', 'out', 'use_timelines.md'))
        self.assertEqual(len([r for r in refs if r['address'].startswith('3117')]), 10)

    def test_validation_targets(self):
        refs = X.parse_reference(X.rp('team', 'week1', 'out', 'use_timelines.md'))
        res = X.validate(self.E, refs)['all sources']
        self.assertGreaterEqual(res['recall_where_source_covers'], 0.90)
        self.assertGreaterEqual(res['category_agreement'], 0.85)


if __name__ == '__main__':
    unittest.main()
