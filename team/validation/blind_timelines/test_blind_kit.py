"""Checks on the blind-timeline kit: the draw can be repeated, the packets give nothing away, the scorer adds up."""
import csv
import json
import os
import unittest

import make_kit as K
import score_blind as S

HERE = os.path.dirname(os.path.abspath(__file__))


class Kit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parcels, cls.eligible, cls.blocks, cls.picked = K.draw()
        with open(os.path.join(HERE, 'sample.json'), encoding='utf-8') as fh:
            cls.sample = json.load(fh)
        cls.ev = K.rows('team', 'extractor', 'out', 'evidence.csv')

    def test_draw_repeats_and_matches_the_committed_sample(self):
        again = K.draw()[3]
        self.assertEqual([p['property_id'] for p in again], [p['property_id'] for p in self.picked])
        self.assertEqual([d['property_id'] for d in self.sample['drawn']], [p['property_id'] for p in self.picked])
        self.assertEqual(self.sample['seed'], K.SEED)

    def test_one_eligible_parcel_per_block(self):
        self.assertEqual(len(self.picked), 4)
        self.assertEqual(sorted(K.number(p['address']) // 100 for p in self.picked), [29, 30, 31, 32])
        status = {r['property_id']: r['status'] for r in K.rows('storefront_assessments.csv')}
        for p in self.picked:
            self.assertNotIn(p['property_id'], K.ALREADY_REFERENCE)
            self.assertNotIn(status.get(p['property_id']), K.HOUSE)

    def test_packets_name_no_occupant_the_extractor_found(self):
        for p in self.picked:
            path = os.path.join(HERE, 'packets', f"{K.number(p['address'])}_greenmount.md")
            with open(path, encoding='utf-8') as fh:
                text = fh.read().lower()
            names = {e['business'].strip().lower() for e in self.ev if e['property_id'] == p['property_id'] and len(e['business'].strip()) >= 5}
            self.assertEqual([n for n in names if n in text], [], p['address'])
            self.assertNotIn('?sp=', text.split('sanborn maps')[0])        # directory links stop at the volume

    def test_template_has_the_agreed_columns(self):
        with open(os.path.join(HERE, 'blind_timelines.csv'), encoding='utf-8', newline='') as fh:
            self.assertEqual(next(csv.reader(fh)), K.FIELDS)

    def test_scorer_refuses_until_filled_and_blind(self):
        self.assertEqual(len(S.check([], self.sample)), 4)
        d = self.sample['drawn'][0]
        row = dict(property_id=d['property_id'], address=d['address'], start_year='1920', end_year='1930', use='grocer',
                   use_category='food & drink', built_by='AB', saw_extractor_output='yes')
        self.assertTrue(any('saw_extractor_output' in x for x in S.check([row], self.sample)))

    def test_scorer_on_a_worked_example(self):
        ref = lambda a, b, c: dict(property_id='1', address='1 Test St', start_year=str(a), end_year=str(b), use=c, use_category=c, built_by='AB')
        ev = lambda y, c, src='polk_directory', kind='listing', sub='': dict(property_id='1', year=str(y), use_category=c, source=src, kind=kind, use_subcategory=sub)
        refs = [ref(1910, 1920, 'food & drink'), ref(1930, 1940, 'retail goods'), ref(1950, 1955, 'office')]
        rows = [ev(1915, 'food & drink'), ev(1921, 'food & drink', src='sponsor'), ev(1935, 'office'), ev(1960, 'office'),
                ev(1936, 'retail goods', kind='current'), ev(1937, 'retail goods', sub='store building (generic)')]
        r = S.score(refs, rows)['all sources']
        self.assertEqual((r['reference_uses'], r['found'], r['covered']), (3, 1, 2))     # food found; retail covered but missed; office not covered
        self.assertAlmostEqual(r['recall'], 1 / 3)
        self.assertAlmostEqual(r['recall_where_covered'], 1 / 2)
        self.assertEqual(r['records_scored'], 3)                                          # 1915, 1921 and 1935 fall inside a span
        self.assertAlmostEqual(r['category_agreement'], 2 / 3)
        self.assertEqual(S.score(refs, rows)['sources other than sponsor records']['records_scored'], 2)


if __name__ == '__main__':
    unittest.main()
