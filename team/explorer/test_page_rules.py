"""Rules the built page must keep (standard library only):  python3 -m unittest team/explorer/test_page_rules.py

Each test is one finding of the sponsor's review of 17 November 2026, written so that it cannot come back unnoticed:
which storefronts are empty, what counts as history, one business counted once, the floor area behind a rent figure,
no figure that ranks uses by money, and no statement about the sponsor. test_page_browser.py checks what a reader sees.
"""
import collections
import csv
import hashlib
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
csv.field_size_limit(sys.maxsize)

# The sponsor's storefront audit, as sent on 16 November 2026 and extended on 17 November (24 storefronts).
AUDIT_EMPTY = """2920 2930 2932 2934 2942 2946 2958 3010 3011 3015 3019 3023 3026 3029 3036 3038 3107 3111 3117 3120 3122
3200 3211 3224""".split()


def read(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8') as fh:
        return fh.read()


def rows(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def page_data():
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', read('team', 'explorer', 'index.html'), re.S)
    return json.loads(m.group(1).replace('<\\/', '</'))


class TestWhichStorefrontsAreEmpty(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.P = page_data()['props']

    def test_the_empty_storefronts_are_the_sponsors_24(self):
        empty = sorted(p['address'] for p in self.P if p['availability'] == 'available now')
        self.assertEqual(empty, sorted(AUDIT_EMPTY))

    def test_69_parcels_are_62_storefronts_and_7_houses(self):
        c = collections.Counter(p['availability'] for p in self.P)
        self.assertEqual(len(self.P), 69)
        self.assertEqual(c['house'], 7)
        self.assertEqual(c['available now'] + c['occupied'], 62)
        self.assertEqual(c['possibly available'], 0, 'no storefront is left unsettled after the audit')

    def test_a_house_is_never_a_storefront(self):
        sa = {r['property_id']: r['status'] for r in rows('storefront_assessments.csv')}
        for p in self.P:
            if sa.get(p['id']) == 'residential':
                self.assertEqual(p['availability'], 'house', p['address'])
        self.assertEqual({p['address'] for p in self.P if p['availability'] == 'house'} & set(AUDIT_EMPTY), set())

    def test_the_page_is_built_from_the_current_tenant_list(self):
        ten = {r['property_id']: r for r in rows('team', 'tenants', 'current_tenants_2026-10.csv')}
        for p in self.P:
            self.assertEqual(p['status'], ten[p['id']]['status'], p['address'])
            self.assertEqual(p['tenant'], ten[p['id']]['tenant_name'], p['address'])

    def test_every_in_use_call_says_what_it_rests_on(self):
        for p in self.P:
            if p['availability'] == 'occupied':
                self.assertTrue(p['basis']['src'], p['address'])
                self.assertIsInstance(p['basis']['person'], bool)


class TestHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.D = page_data()
        cls.P = cls.D['props']
        cls.ev = rows('team', 'extractor', 'out', 'evidence.csv')

    def test_todays_tenant_is_not_history(self):
        """Heritage is rebuilt here from the evidence file with the 2026 tenant check left out, and must equal the page's."""
        generic = 'store building (generic)'
        summary = lambda e: e['source'].startswith('sponsor') and e['text'].startswith('Built ca') and 'B-5229' in e['text']
        g = collections.defaultdict(lambda: collections.defaultdict(list))
        for e in self.ev:
            if e['source'] == 'current_2026' or e['kind'] == 'current' or summary(e):
                continue
            if e['use_category'] and e['year'] and e['use_subcategory'] != generic and e['use_category'] != 'vacant':
                g[e['property_id']][e['use_category']].append(e)
        for p in self.P:
            want = {c: [len({int(r['decade']) for r in rs}), len(rs), len({r['source'].split(':')[0] for r in rs})] for c, rs in g[p['id']].items()}
            self.assertEqual({c: v[:3] for c, v in p['h'].items()}, want, p['address'])

    def test_the_old_reading_is_kept_only_for_comparison(self):
        differ = [p for p in self.P if p['h0']]
        self.assertTrue(differ)
        for p in differ:
            self.assertNotEqual(p['h0'], p['h'], p['address'])

    def test_the_tenant_check_in_the_evidence_file_is_the_current_one(self):
        """The extractor's output must have been rerun after the tenant list last changed (it had not been on 17 Nov)."""
        ten = rows('team', 'tenants', 'current_tenants_2026-10.csv')
        cur = [e for e in self.ev if e['source'] == 'current_2026']
        self.assertEqual(sum(e['use_subcategory'] in ('vacant', 'for lease') for e in cur), sum(t['status'] in ('vacant', 'for lease') for t in ten))
        self.assertEqual(collections.Counter(e['text'] for e in cur if e['text'] in ('vacant', 'for lease', 'unknown')),
                         collections.Counter(t['status'] for t in ten if t['status'] in ('vacant', 'for lease', 'unknown')))

    def test_strict_evidence_is_two_kinds_of_source_at_the_address(self):
        for p in self.P:
            for c, q in p['hq'].items():
                self.assertEqual(q['n'], q['stated'] + q['inferred'], (p['address'], c))
                self.assertLessEqual(q['before'], q['stated'])
                self.assertEqual(q['strict'], len(q['fams']) >= 2, (p['address'], c))
                self.assertEqual(c in p['hs'], q['strict'], (p['address'], c))

    def test_placed_records_are_counted(self):
        pl = self.D['placed']
        hist = [e for e in self.ev if e['source'] != 'current_2026']
        self.assertEqual(pl['total'], len(hist))
        self.assertEqual(pl['inferred'], sum(e['basis'] == 'inferred' for e in hist))
        self.assertLessEqual(pl['next'], pl['inferred'])


class TestCounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.D = page_data()
        cls.P = cls.D['props']

    def test_one_business_in_two_numbers_counts_once(self):
        by = {p['address']: p for p in self.P}
        self.assertEqual(by['3133']['same_as'], by['3127']['id'])
        self.assertIn('same store as 3127', by['3133']['tenant'])
        # today's mix is a share of the storefronts in use, each business once; a lived-in house is not in the base,
        # as a house was not in the base of the 1920-23 mix (buildings with a listed business)
        base = sum(1 for p in self.P if p['occ'] and p['availability'] != 'house' and not p['same_as'])
        self.assertEqual(base, 37)
        for m in self.D['mix']:
            self.assertEqual(m['now_base'], base)
        retail = sum(1 for p in self.P if p['occ'] and not p['same_as'] and 'retail goods' in p['now'])
        self.assertEqual(next(m for m in self.D['mix'] if m['cat'] == 'retail goods')['now'], retail)

    def test_ground_floor_is_never_more_than_the_building_or_the_lot(self):
        notes = collections.Counter()
        for p in self.P:
            notes[p['gf_note']] += 1
            self.assertIn(p['gf_note'], ('outline', 'outline may be partial', 'no outline'))
            if p['sqft']:
                self.assertTrue(p['gf'] and p['gf'] <= p['sqft'], p['address'])
                self.assertTrue(p['gf'] <= p['gf_hi'] <= p['sqft'], p['address'])
            if p['gf_note'] == 'outline may be partial':
                self.assertLess(p['gf'], 0.5 * p['gf_hi'], p['address'])
        self.assertGreater(notes['outline'], 40)

    def test_no_rent_figure_is_stored_for_any_building(self):
        """Rent is worked out on the page from one corridor level; the data carries no per-building dollar estimate."""
        for p in self.P:
            self.assertNotIn('econ', p)
            for k, v in p.items():
                if isinstance(v, str) and k not in ('tenant',):
                    self.assertNotRegex(v, r'indicative rent|\$\d+k', (p['address'], k))


class TestOneBasisForMoney(unittest.TestCase):
    def test_the_page_has_nothing_that_ranks_uses_by_money(self):
        t = read('team', 'explorer', 'template.html')
        for gone in ('qSupport', 'canPay', 'rankPlans', 'searchBlock', 'drawPlanRank', 'Highest rent</button>', 'money_weight', 'same_use_haircut',
                     'neighbour_uplift', 'usableOf', 'apprOf'):
            self.assertNotIn(gone, t, gone)
        comps = page_data()['comps']
        self.assertEqual(comps['version'], 'comps engine v2')
        for f, r in comps['formats'].items():
            for gone in ('supportable', 'typical', 'can_pay', 'rankable'):
                self.assertNotIn(gone, r, (f, gone))

    def test_the_back_test_decides_what_money_may_rest_on(self):
        d = page_data()['backtest2']['decision']
        if not d['passes']:
            self.assertIn('comparable listings only', d['if_it_fails'])
            self.assertIn('no dollar figure on the page rests on history', read('team', 'explorer', 'template.html'))


# The phrases the sponsor's review of 17 November 2026 asks to be gone from the team's files (its last page lists them).
# They are checked by hash, as the brand names are, so that this file does not itself answer the sponsor's search.
# The first hash is a canary for the phrase in test_the_check_works.
GONE_HASHES = set("""
    3c45982ef15de171 7f9f33ce1272e29d ba0979624c1acf7b 9f9903381d626097 62723f393e3bb686 361283d261170771
    56e4b7e6c0ff80c8 bfa1e9e21e320ee5 6832869445e943a3 7458ce91e85e1744 0846262091174793 5b28b39ad07fbb80
    b1627b60a03d3706 ca078c1221eef0a4 1df3a715876db160 dbd4926edb8d6b11 37242106bee67850 d58144b2c72e6dbb
    eed89085480902d3 b77db965defb48b8 7c7fbddf498dc9d7 fb0b24bed1202b3d 62538e797ba2e069 eb3c4b0bc4f46a1f
    55e5abfa420ce57a
""".split())


def _hits(text, hashes=GONE_HASHES, longest=6):
    toks, out = re.sub(r'[^a-z0-9]+', ' ', text.lower()).split(), []
    for n in range(1, longest + 1):
        for i in range(len(toks) - n + 1):
            g = ' '.join(toks[i:i + n])
            if hashlib.sha256(g.encode()).hexdigest()[:16] in hashes:
                out.append(g)
    return out


class TestNothingAboutTheSponsor(unittest.TestCase):
    """The search the sponsor's review asks for, kept as a test over the files this team's explorer, comps and
    validation work is made of. The back-test's outcome file and the two blank coding sheets made from it are left out
    on purpose: they list the 52 tested parcels by address, and one of those addresses is a number the review names."""
    FILES = [('team', 'explorer', f) for f in ('template.html', 'build_explorer.py', 'extras.py', 'concepts.json', 'library.json', 'index.html',
                                             'MODEL_CARD.md', 'README.md', 'DISPLACEMENT.md', 'retail_types.json', 'typical_sqft.json',
                                             'test_page_rules.py', 'test_page_browser.py', 'test_explorer_data.py', 'page_numbers.py')] + \
            [('team', 'comps', f) for f in ('comps_engine.py', 'engine_inputs.json', 'comps_ranges.json', 'MODEL_CARD.md', 'README.md',
                                           'test_comps_engine.py')] + \
            [('team', 'comps', 'library', f) for f in ('rents.csv', 'benchmarks.csv', 'operators.csv', 'SCHEMA.md', 'rents_notes.md',
                                                      'benchmarks_notes.md', 'operators_notes.md')] + \
            [('team', 'validation', f) for f in ('README.md', 'PLAN_backtest_v2.md', 'backtest.py', 'test_backtest.py')] + \
            [('team', 'validation', 'out', 'backtest_v2.md'), ('team', 'prototype_v0', 'screen_v0.py'),
             ('team', 'prototype_v0', 'out', 'hbu_screen_v0.csv'), ('team', 'tenants', 'README.md'), ('team', 'NUMBERS.md',),
             ('team', 'numbers_of_record.py',), ('team', 'test_numbers_of_record.py',), ('team', 'numbers_of_record.json',),
             ('team', 'REVIEW_RESPONSE.md',), ('team', 'explorer', 'out', 'page_numbers.json'), ('team', 'week1', 'comps_template.csv'),
             ('team', 'validation', 'two_coder', 'README.md'), ('team', 'validation', 'two_coder', 'make_sheets.py'),
             ('team', 'validation', 'two_coder', 'score_agreement.py'), ('team', 'validation', 'two_coder', 'history_coder_A.csv'),
             ('team', 'validation', 'two_coder', 'history_key.csv')]

    def test_the_check_works(self):
        self.assertEqual(_hits('A canary sponsor phrase check, in a sentence.'), ['canary sponsor phrase check'])
        self.assertEqual(len(GONE_HASHES), 25)

    def test_the_named_phrases_are_gone(self):
        seen = 0
        for parts in self.FILES:
            if not os.path.exists(os.path.join(REPO, *parts)):
                continue
            seen += 1
            # the canary is the made-up phrase test_the_check_works uses; it is in this file and nowhere else
            self.assertEqual([h for h in _hits(read(*parts)) if not h.startswith('canary ')], [], '/'.join(parts))
        self.assertGreater(seen, 30)

    def test_no_sentence_ties_a_trust_to_the_sponsor(self):
        for parts in self.FILES:
            if not os.path.exists(os.path.join(REPO, *parts)) or parts[-1] == 'index.html' or parts[-1].endswith('.csv'):   # prose only
                continue
            for sent in re.split(r'(?<=[.!?"])\s+|\n', read(*parts)):
                if re.search(r'\btrusts?\b', sent, re.I) and re.search(r'sponsor', sent, re.I) and 'def test_' not in sent and 're.search' not in sent:
                    self.fail(f"{'/'.join(parts)}: {sent.strip()[:160]}")

    def test_the_tour_flag_is_not_called_sponsor(self):
        for p in page_data()['props']:
            self.assertNotIn('sponsor', p)
            self.assertIn('tour', p)
            self.assertNotIn('walk', p['ready'])

    def test_owner_kind_treats_every_company_alike(self):
        kinds = {p['ready']['owner'] for p in page_data()['props']}
        self.assertTrue(kinds <= {'company', 'church or nonprofit', 'individual', 'unknown'}, kinds)


class TestRulesAreCitedFromThePlan(unittest.TestCase):
    def test_the_renewal_plan_is_cited_and_not_called_unverified(self):
        lib = read('team', 'explorer', 'library.json')
        for sent in re.split(r'(?<=[.;"])\s+', lib):
            if re.search(r'urban renewal', sent, re.I):
                self.assertNotRegex(sent, r'(?i)unverified|could not be verified|not verified', sent[:120])
        for parts in (('team', 'explorer', 'library.json'), ('team', 'explorer', 'template.html'), ('team', 'explorer', 'build_explorer.py')):
            t = read(*parts)
            self.assertIn('Amendment No. 2', t, parts[-1])
            self.assertNotIn('Council Bill 2278', t, parts[-1])
        self.assertIn('Ordinance 1029', read('team', 'explorer', 'template.html'))

    def test_every_statement_of_a_rule_says_it_is_not_legal_advice(self):
        t = read('team', 'explorer', 'template.html')
        for m in re.finditer(r'no new taverns, liquor stores or pawnshops', t):
            self.assertIn('not legal advice', t[m.start():m.start() + 900], t[m.start():m.start() + 80])
        for f in page_data()['formats']:
            if 'urban renewal plan bars' in f['note']:
                self.assertIn('not legal advice', f['note'], f['id'])


if __name__ == '__main__':
    unittest.main()
