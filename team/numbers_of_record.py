#!/usr/bin/env python3
"""One generated file of headline numbers for every document to quote:  python3 team/numbers_of_record.py

Writes team/numbers_of_record.json and team/NUMBERS.md. Nothing in either is typed by hand: every figure is counted
from a data file or read from an output another script wrote. Run it last, after the comps engine, the back-test, the
explorer build and team/explorer/page_numbers.py.

It also keeps the figures quoted in the documents listed in DOCS in step with the data. In those documents a quoted
figure sits between two HTML comments, which do not show when the file is read on GitHub:

    <!--=frontage.empty-->24<!--/-->            the key is a path into numbers_of_record.json
    <!--=backtest.p_1960|p-->0.055<!--/-->      "|p" picks a format (see FORMATS)

Each run rewrites what is between the comments. To quote a figure in a document, add the two comments around it; never
type a headline number by itself. team/test_numbers_of_record.py fails if the two files or a document are out of date.

    python3 team/numbers_of_record.py --check     # exit 1 if a saved file or a document is not what the data gives today

Standard library only.
"""
import collections
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
csv.field_size_limit(sys.maxsize)


# every test file in team/, to be run from the repo root
TESTS = ['team/extractor/test_extract.py', 'team/comps/test_comps_engine.py', 'team/validation/test_backtest.py',
         'team/validation/blind_timelines/test_blind_kit.py', 'team/explorer/test_explorer_data.py', 'team/explorer/test_page_rules.py',
         'team/explorer/test_page_browser.py', 'team/validation/two_coder/test_two_coder.py', 'team/test_numbers_of_record.py']

# documents whose quoted figures this script fills in
DOCS = ['team/explorer/README.md', 'team/explorer/MODEL_CARD.md', 'team/explorer/DISPLACEMENT.md', 'team/comps/README.md',
        'team/comps/MODEL_CARD.md', 'team/validation/README.md', 'team/tenants/README.md', 'team/REVIEW_RESPONSE.md']
MARK = re.compile(r'<!--=([A-Za-z0-9_.& -]+?)(?:\|([a-z0-9]+))?-->(.*?)<!--/-->', re.S)
FORMATS = {
    None: lambda v: f'{v:,}' if isinstance(v, int) and not isinstance(v, bool) else str(v),
    'p': lambda v: f'{v:.3f}',            # a p-value
    'f1': lambda v: f'{v:.1f}',
    'f2': lambda v: f'{v:.2f}',
    'f3': lambda v: f'{v:.3f}',
    'f4': lambda v: f'{v:.4f}',
    's4': lambda v: f'{v:+.4f}',          # a signed difference
    's2': lambda v: f'{v:+.2f}',
    'pct': lambda v: f'{v:.0%}',          # a share held as 0.21
    'usd': lambda v: f'${v:,.0f}',
    'usd2': lambda v: f'${v:,.2f}',
    'x2': lambda v: f'{v:.2f}',
    'list': lambda v: ', '.join(str(x) for x in v),
}


def look(n, path):
    """The value at a dotted path, e.g. backtest.held_out_log_loss.0"""
    for k in path.split('.'):
        n = n[int(k)] if isinstance(n, list) else n[k]
    return n


def fill(text, n):
    """The text with every marked figure rewritten from the numbers."""
    def one(m):
        key, fmt = m.group(1), m.group(2)
        return f"<!--={key}{'|' + fmt if fmt else ''}-->{FORMATS[fmt](look(n, key))}<!--/-->"
    return MARK.sub(one, text)


def rows(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh, delimiter='\t' if parts[-1].endswith('.tsv') else ','))


def jload(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8') as fh:
        return json.load(fh)


def text(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8') as fh:
        return fh.read()


def page_data():
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', text('team', 'explorer', 'index.html'), re.S)
    return json.loads(m.group(1).replace('<\\/', '</'))


def person(entered_by):
    """True if a row says a person entered or checked it; AI-assisted entries name the model or say so."""
    e = (entered_by or '').strip()
    return bool(e) and not e.startswith('Claude') and 'AI-assisted' not in e


def sens(co, what, setting):
    """A dollar figure from the comps engine's sensitivity table, found by its labels."""
    row = [r for r in co['sensitivity'] if what in r['what'] and setting in r['setting']]
    assert len(row) == 1, (what, setting, len(row))
    return float(re.search(r'\$([\d.]+)', row[0]['result']).group(1))


def build():
    D = page_data()
    P = D['props']
    pn = jload('team', 'explorer', 'out', 'page_numbers.json')
    bt = jload('team', 'validation', 'out', 'backtest_v2.json')
    co = jload('team', 'comps', 'comps_ranges.json')
    g = lambda key, cut=1960: next(a for a in bt[key] if a['cut'] == cut)

    shops = [p for p in P if p['availability'] != 'house']
    empty = sorted(p['address'] for p in shops if p['availability'] == 'available now')
    in_use = [p for p in shops if p['availability'] == 'occupied']
    assert len(shops) == pn['storefronts'] and empty == pn['empty_addresses'], 'page_numbers.json is from another build: rerun page_numbers.py'
    frontage = collections.OrderedDict(
        parcels=len(P), storefronts=len(shops), houses=len(P) - len(shops), empty=len(empty), in_use=len(in_use), empty_addresses=empty,
        empty_follows="the sponsor's storefront audit of November 2026 (24 storefronts as of 17 November)",
        in_use_by_basis=dict(collections.Counter(p['basis']['src'] or 'none' for p in in_use).most_common()),
        in_use_checked_by_a_person=sum(1 for p in in_use if p['basis']['person']),
        in_use_named_from_a_search_listing_only=sum(1 for p in in_use if p['basis']['src'] == 'search snippet'),
        one_business_in_two_numbers=sorted(p['address'] for p in P if p['same_as']),
        businesses_counted=sum(1 for p in P if p['occ'] and not p['same_as']) - sum(1 for p in P if p['occ'] and p['availability'] == 'house'),
        with_a_3d_tour=sum(1 for p in P if p['tour']),
        long_standing_businesses=D['legacy_stats']['legacy'], long_standing_means_years=D['legacy_stats']['min_years'],
        oldest_long_standing_since=min([p['since']['year'] for p in P if p.get('since', {}).get('legacy')] or [0]))

    ev = rows('team', 'extractor', 'out', 'evidence.csv')
    hist = [e for e in ev if e['source'] != 'current_2026']
    pu = rows('team', 'extractor', 'out', 'proven_uses.csv')
    grade_col = next((c for c in pu[0] if c.lower() in ('strength', 'grade', 'status', 'proven')), None)
    evidence = collections.OrderedDict(
        rows=len(ev), history_rows=len(hist), tenant_check_rows=len(ev) - len(hist),
        by_source=dict(collections.Counter(e['source'].split(':')[0] for e in ev).most_common()),
        sponsor_rows=sum(1 for e in ev if e['source'].startswith('sponsor')),
        coded_with_a_use=sum(1 for e in hist if e['use_category'] and e['year'] and e['use_subcategory'] != 'store building (generic)'),
        address_inferred=D['placed']['inferred'], placed_by_the_next_parcel=D['placed']['next'],
        share_placed_by_the_next_parcel=round(D['placed']['next'] / D['placed']['total'], 3),
        spans=len(rows('team', 'extractor', 'out', 'timeline_table.csv')),
        parcel_use_rows=len(pu), parcel_use_rows_by_grade=dict(collections.Counter(r[grade_col] for r in pu).most_common()) if grade_col else None,
        unassigned_source_lines=len(rows('team', 'extractor', 'out', 'unassigned.csv')),
        uses_on_record_parcel_by_kind=sum(1 for p in P for c in p['hq'] if c != 'residential'),
        of_which_two_kinds_of_source_at_the_address=sum(1 for p in P for c, q in p['hq'].items() if c != 'residential' and q['strict']),
        parcels_where_todays_tenant_used_to_count_as_history=sum(1 for p in P if p['h0']),
        extractor_against_hand_timelines=D['validation_numbers'])

    r0 = pn['ranking'][0]
    rank = {x['id']: x for x in pn['ranking']}
    score = collections.OrderedDict(
        default_weights=pn['weights'], default_since=pn['default_since'], weights_agreed_9_nov_2026=pn['weights_agreed_9_nov'],
        a_building_with_no_record_scores=pn['no_record_baseline'],
        cafe_head_start_over_a_shop_with_no_record=dict(default=r0['no_record']['cafe'] - r0['no_record']['shop'],
                                                        agreed_9_nov=rank['nov9']['no_record']['cafe'] - rank['nov9']['no_record']['shop'],
                                                        cafe_agreed_9_nov=rank['nov9']['no_record']['cafe']),
        inputs_by_use=pn['inputs_by_use'],
        top_candidate_is_a_cafe=collections.OrderedDict(of_storefronts=r0['cafe_top'], of_empty=r0['cafe_top_empty'], storefronts=pn['storefronts']),
        top_candidate_no_higher_than_no_record=r0['no_lift'],
        evidence_behind_top_candidates=r0['evidence'],
        if_heritage_weight_is_zero=dict(cafe_top=rank['noher']['cafe_top'], top_candidate_changes=rank['noher']['differs'], of_empty=rank['noher']['differs_empty']),
        with_the_weights_agreed_9_nov=dict(cafe_top=rank['nov9']['cafe_top'], cafe_top_empty=rank['nov9']['cafe_top_empty'], top_candidate_changes=rank['nov9']['differs'], of_empty=rank['nov9']['differs_empty'],
                                           top_candidates_with_no_record_of_the_use=rank['nov9']['evidence']['none'], top_candidates_no_higher_than_no_record=rank['nov9']['no_lift']),
        firmest_records_only=dict(cafe_top=rank['strict']['cafe_top'], top_candidate_changes=rank['strict']['differs'], of_empty=rank['strict']['differs_empty']),
        with_todays_tenant_as_history=dict(cafe_top=rank['today']['cafe_top'], top_candidate_changes=rank['today']['differs'], of_empty=rank['today']['differs_empty']),
        with_the_whole_building_as_the_size=dict(cafe_top=rank['whole']['cafe_top'], top_candidate_changes=rank['whole']['differs'], of_empty=rank['whole']['differs_empty']))

    plan = collections.OrderedDict(pn['plan'])

    m, bf, h = co['model'], co['built_from'], co['holdout']
    sizes = {x['id']: x for x in jload('team', 'explorer', 'typical_sqft.json')['formats']}      # the sourced usual size of each use
    comps = collections.OrderedDict(
        engine=co['version'], library_rent_rows=bf['rents'], rents_used=bf['rows_used'], asking=bf['asking'], in_place=bf['in_place'],
        in_place_rows=bf['in_place_rows'], newly_signed_leases=0, corridors=bf['corridors'], sources=bf['sources'],
        benchmarks=bf['benchmarks'], operators=bf['operators'],
        waverly=collections.OrderedDict(rows=m['waverly']['n'], asking=m['waverly']['asking'], in_place=m['waverly']['in_place'],
                                        mean_of_own_rows=m['waverly']['raw'], pooled=m['waverly']['pooled'],
                                        rent_level_low_mid_high=m['space']['q']),
        held_out=collections.OrderedDict(rows=h['n'], inside_plain_80_range=h['nominal_hits'], inside_widened_range=h['honest_hits'], widened_by=co['interval']['widen']),
        held_out_detail=collections.OrderedDict(sources=h['sources'], share_plain=h['nominal_cover'], share_widened=h['honest_cover'], below=h['below'], above=h['above'],
                                             baltimore_rows=h['baltimore_n'], baltimore_plain=h['baltimore_nominal'], baltimore_widened=h['baltimore_widened'],
                                             better_than_a_plain_range_of_all_listings=h['skill'], second_method_waverly_shop=h['jackknife_plus_waverly_shop']),
        model=collections.OrderedDict(spread_within_a_corridor=m['within_sd'], spread_between_corridors=m['between_corridor_sd'],
                                      waverly_weight_on_its_own_rows=m['waverly']['own_share'], baltimore_mean=m['city_means']['baltimore']),
        waverly_level_if=collections.OrderedDict(
            asking_rents_only=sens(co, 'Rents in place', 'left out'),
            r004_read_with_the_tax_record_floor_area=sens(co, 'R-004', 'tax record'),
            r004_left_out=sens(co, 'R-004', 'row left out')),
        sales_check={f: r['check']['verdict'] for f, r in co['formats'].items() if r.get('check')},
        # where the sales check rests on a floor area the team assumed, and where its answer would change
        sales_check_floor_area={f: collections.OrderedDict(assumed_sq_ft=r['check']['assumed_sqft'], covers_up_to_sq_ft=r['check']['covers_up_to_sqft'],
                                                           does_not_cover_from_sq_ft=r['check']['does_not_cover_from_sqft'],
                                                           usual_size_sq_ft=[sizes[f]['low'], sizes[f]['high']])
                                for f, r in co['formats'].items() if r.get('check') and r['check'].get('assumed_sqft')},
        # the engine against the estimators that were tried on the same held-out listings (lower is better on both measures)
        estimators_tried=[collections.OrderedDict(estimator=x['estimator'], error_of_the_middle_figure_in_logs=x['log_rmse'],
                                                  widening_its_range_needs=x['widen'], interval_score=x['interval_score']) for x in h['alternatives']],
        sales_check_margin=co['sales_check']['margin'],
        library_rows_checked_by_a_person=sum(1 for n in ('rents.csv', 'benchmarks.csv', 'operators.csv') for r in rows('team', 'comps', 'library', n) if r.get('verified_by')),
        library_rows=sum(len(rows('team', 'comps', 'library', n)) for n in ('rents.csv', 'benchmarks.csv', 'operators.csv')))

    o6, o4, t6, ci = g('other_blocks'), g('other_blocks', 1940), g('transfer_frontage_sponsor_to_other'), g('transfer_interval_sponsor_to_other')
    lo, sc, kinds = g('other_blocks_leave_one_parcel_out'), g('selection_empty_against_in_use'), {r['kinds']: r['p_perm'] for r in g('other_blocks_by_kind_of_use')['runs']}
    auto = next(c for c in o6['per_category'] if c['category'] == 'automotive')
    oc = [r for r in rows('team', 'validation', 'outcomes_other_greenmount_2026-10.csv') if r['included'] == 'yes']
    backtest = collections.OrderedDict(
        passes_the_agreed_rule=bt['decision']['passes'], rule=bt['decision']['rule'], if_it_fails=bt['decision']['if_it_fails'],
        parcels=o6['parcels'], pairs=o6['rows'], pairs_true_today=o6['present'], parcels_with_history=o6['parcels_with_history'],
        p_1960=o6['p_perm'], p_1940=o4['p_perm'], p_1960_before_leak_fix=bt['decision']['p_perm_before_leak_fix'],
        p_1960_without_low_confidence=g('other_blocks_without_low_confidence')['p_perm'],
        p_1960_stated_uses_only=g('other_blocks_stated_uses_only')['p_perm'],
        p_1960_without_multi_tenant=g('other_blocks_without_multi_tenant')['p_perm'],
        multi_tenant_parcels=[x['address'] for x in bt['multi_tenant_parcels']],
        p_1960_storefront_trades_only=next(v for k, v in kinds.items() if k.startswith('ordinary storefront')),
        p_1960_without_automotive=kinds['every kind except automotive'], p_1960_automotive_only=kinds['automotive only'],
        automotive=dict(parcels_with_it_on_record=auto['parcels_with_history'], of_which_today=auto['of_which_have_it_today'], base_rate=auto['base_rate'],
                        adds_to_statistic=auto['contribution']),
        leave_one_parcel_out=dict(min=lo['min'], max=lo['max'], median=lo['median'], below_0_05=lo['below_0_05'], runs=lo['parcels']),
        by_kind=collections.OrderedDict((c['category'], collections.OrderedDict(
            parcels_with_it_on_record=c['parcels_with_history'], of_which_today=c['of_which_have_it_today'], base_rate=c['base_rate'],
            adds_to_statistic=c['contribution'], adds_to_statistic_before_leak_fix=cb['contribution'], of_which_today_before_leak_fix=cb['of_which_have_it_today'],
            parcels_with_it_on_record_before_leak_fix=cb['parcels_with_history']))
            for c, cb in zip(o6['per_category'], g('other_blocks_before_leak_fix')['per_category'])),
        p_1960_with_a_control_for_how_much_is_on_record=o6['p_lr_with_depth_control'],
        mix_of_uses_on_record_empty_against_in_use=dict(distance=sc['mix_of_uses_on_record']['distance'], p=sc['mix_of_uses_on_record']['p']),
        decades_on_record_p=sc['decades_on_record']['p_two_sided'],
        held_out_log_loss=[t6['logloss_base'], t6['logloss_history']], held_out_auc=[t6['auc_base'], t6['auc_history']],
        held_out_gain_per_row=ci['gain_per_row'], held_out_gain_ci95=ci['gain_ci95'], gain_distinguishable_from_zero=ci['distinguishable_from_zero'],
        in_sample_auc=[o6['auc_base'], o6['auc_history']],
        frontage_storefronts_tested=bt['frontage_parcels_tested'], frontage_empty_storefronts_not_tested=sc['empty'],
        decades_on_record_empty_against_in_use=[sc['decades_on_record']['empty'], sc['decades_on_record']['in_use']],
        outcome_rows=len(oc), outcome_rows_checked_by_a_person=sum(1 for r in oc if person(r['coded_by']) and 'to be checked' not in r['coded_by']),
        first_back_test_1960=next(dict(hit=b['hit'], plain_guess=b['base'], of=b['n']) for b in D['backtest'] if b['cut'] == 1960))

    ten = rows('team', 'tenants', 'current_tenants_2026-10.csv')
    blind = rows('team', 'validation', 'blind_timelines', 'blind_timelines.csv')
    md = {}
    for f in sorted(glob.glob(os.path.join(HERE, '**', '*.md'), recursive=True)):
        with open(f, encoding='utf-8') as fh:
            md[os.path.relpath(f, REPO).replace(os.sep, '/')] = fh.read()
    unsigned = [f for f, text in md.items() if re.search(r'Checked by:\s*_{3,}', text)]
    signed = [f for f, text in md.items() if re.search(r'Checked by:\s*[A-Za-z]', text)]
    checks = collections.OrderedDict(
        tenant_rows=len(ten), tenant_rows_entered_or_checked_by_a_person=sum(1 for r in ten if person(r['entered_by'])),
        outcome_rows_checked_by_a_person=backtest['outcome_rows_checked_by_a_person'], outcome_rows=len(oc),
        comps_library_rows_checked_by_a_person=comps['library_rows_checked_by_a_person'], comps_library_rows=comps['library_rows'],
        blind_timelines_built=len({r['property_id'] for r in blind}), blind_timelines_needed=len(jload('team', 'validation', 'blind_timelines', 'sample.json')['drawn']),
        checked_by_lines=len(unsigned) + len(signed), checked_by_lines_unsigned=len(unsigned), checked_by_lines_signed=len(signed), unsigned_files=unsigned)

    lib = jload('team', 'explorer', 'library.json')
    # living documents by other hands that still quote counts: listed, never edited from here
    ex = text('team', 'extractor', 'README.md')
    claims = []

    def claim(what, pattern, now, doc='team/extractor/README.md', body=None):
        m = re.search(pattern, body if body is not None else ex)
        if m and int(m.group(1).replace(',', '')) != now:
            claims.append(dict(document=doc, what=what, says=m.group(1), now=now))

    claim('rows in evidence.csv', r'`evidence\.csv` \| ([\d,]+) \|', evidence['rows'])
    claim('spans in timeline_table.csv', r'`timeline_table\.csv` \| ([\d,]+) \|', evidence['spans'])
    claim('rows in proven_uses.csv', r'`proven_uses\.csv` \| ([\d,]+) \|', evidence['parcel_use_rows'])
    claim('uses graded "proven"', r'`proven` \((\d+)\)', (evidence['parcel_use_rows_by_grade'] or {}).get('proven', 0))
    claim('sponsor records read', r'class A \("states a use"\) \| `[^`]+` \| ([\d,]+) \|', evidence['sponsor_rows'])
    claim('rows the inferred-address count is out of', r'\(\d+ of ([\d,]+)\)', evidence['rows'])
    claim('records scored for category agreement, all sources', r'\| All sources \| [^|]+\| [^|]+\| \d+% of (\d+) records', evidence['extractor_against_hand_timelines']['all_sources']['records'])

    library = collections.OrderedDict(reuse_buildings=len(lib['buildings']), corridors=len(lib['districts']), benchmark_neighbourhoods=len(D['nbhd']['rows']),
                                      corridor_displacement=dict(collections.Counter(d['displacement'] for d in lib['districts'])),
                                      neighbourhood_displacement=dict(collections.Counter(r['displacement_rating'] for r in D['nbhd']['rows'])),
                                      neighbourhoods_rated_high=[r['name'].split(' (')[0].split(' / ')[0] for r in D['nbhd']['rows'] if r['displacement_rating'] == 'high'],
                                      customer_groups=len(lib['segments']), cases_with_a_cafe=sum(1 for b in lib['buildings'] if set(b.get('new_formats') or []) & {'cafe', 'foodhall'}))
    return collections.OrderedDict(about='Written by team/numbers_of_record.py. Do not edit by hand.', frontage=frontage, evidence=evidence, score=score, plan=plan,
                                   comps=comps, backtest=backtest, human_checks=checks, library=library, other_documents=claims)


def usd(x):
    return f'${x:,.0f}'


def markdown(n):
    f, e, s, pl, c, b, k = n['frontage'], n['evidence'], n['score'], n['plan'], n['comps'], n['backtest'], n['human_checks']
    v = e['extractor_against_hand_timelines']
    pv = lambda x: f'{x:.3f}'
    L = ['# Numbers of record', '',
         'One file of headline numbers for every document, slide and email to quote. Written by `team/numbers_of_record.py` from the data',
         'and the scripts\' own outputs; nothing here is typed by hand. If a document disagrees with this file, the document is out of date.',
         'The same numbers, for scripts, are in `team/numbers_of_record.json`.', '',
         'The documents listed in `DOCS` in the script quote these figures between two hidden comments (`<!--=key-->` and `<!--/-->`), and each run',
         'of the script rewrites them. To quote a figure in a document, mark it the same way; do not type a headline number by itself.', '',
         '## The frontage', '',
         '| | Number | From |', '|---|---|---|',
         f"| Parcels on the frontage, E 29th to E 33rd St | {f['parcels']} | `team/explorer/index.html` (built from `team/week1/out` and `team/evidence/blocklot_gaps.csv`) |",
         f"| Storefronts | {f['storefronts']} | the same; a house with no shop front is not a storefront |",
         f"| Houses | {f['houses']} | sponsor's storefront assessments (`residential`) |",
         f"| **Empty storefronts** | **{f['empty']}** | `team/tenants/current_tenants_2026-10.csv`, which follows {f['empty_follows']} |",
         f"| Storefronts in use | {f['in_use']} | the same |",
         f"| Businesses counted (one business in two street numbers counts once: {', '.join(f['one_business_in_two_numbers']) or 'none'}) | {f['businesses_counted']} | the same |",
         f"| Businesses at the same address for {f['long_standing_means_years']} years or more | {f['long_standing_businesses']} (the oldest since {f['oldest_long_standing_since']}) | the tenant list and dated records |",
         f"| In-use rows a person has entered or checked | {f['in_use_checked_by_a_person']} of {f['in_use']} | `entered_by` in the tenant list |",
         f"| In-use rows whose business name rests on a search listing only | {f['in_use_named_from_a_search_listing_only']} of {f['in_use']} | `source_type` in the tenant list |",
         '', 'The empty storefronts: ' + ', '.join(f['empty_addresses']) + '.', '',
         '## The historical record', '',
         '| | Number | From |', '|---|---|---|',
         f"| Evidence rows | {e['rows']:,} | `team/extractor/out/evidence.csv` |",
         f"| of which history (the 2026 tenant check left out) | {e['history_rows']:,} | the same |",
         f"| of which sponsor records | {e['sponsor_rows']:,} | the same |",
         f"| History rows coded with a use | {e['coded_with_a_use']:,} | the same |",
         f"| History rows with an inferred address | {e['address_inferred']:,} | `basis = inferred` |",
         f"| of which placed on the next parcel down or up | {e['placed_by_the_next_parcel']:,} ({e['share_placed_by_the_next_parcel']:.0%} of history rows) | `address_method` |",
         f"| Spans in the timelines | {e['spans']:,} | `team/extractor/out/timeline_table.csv` |",
         f"| Parcel-and-use rows | {e['parcel_use_rows']:,}" + (f" ({', '.join(f'{v2} {k2}' for k2, v2 in e['parcel_use_rows_by_grade'].items())})" if e['parcel_use_rows_by_grade'] else '') + " | `team/extractor/out/proven_uses.csv` |",
         f"| Uses on record at a storefront or house, by parcel and kind (housing left out) | {e['uses_on_record_parcel_by_kind']} | `team/explorer/index.html` |",
         f"| of which rest on two independent kinds of source at the address and the standing building | {e['of_which_two_kinds_of_source_at_the_address']} | the same |",
         f"| Extractor against four hand-built timelines, sources not used to build them | finds {v['independent']['recall']}% ({v['independent']['found']} of {v['independent']['rows']}); {v['independent']['agreement']}% of {v['independent']['records']} records agree on the kind of use | `team/extractor/out/validation.md` |",
         f"| The same with all sources (not a test: the timelines were built from the same sponsor records) | finds {v['all_sources']['recall']}%; {v['all_sources']['agreement']}% of {v['all_sources']['records']} | the same |",
         '',
         '## The score', '',
         f"Default weights since {s['default_since']}: heritage {s['default_weights']['h']}, room on the block {s['default_weights']['s']}, size {s['default_weights']['f']}, "
         f"neighbours {s['default_weights']['a']}; community {s['default_weights']['c']} and precedents {s['default_weights']['k']}. "
         f"The six weights agreed with the sponsor on 9 November 2026 ({s['weights_agreed_9_nov_2026']['h']} / {s['weights_agreed_9_nov_2026']['s']} / {s['weights_agreed_9_nov_2026']['f']} / "
         f"{s['weights_agreed_9_nov_2026']['c']} / {s['weights_agreed_9_nov_2026']['a']} / {s['weights_agreed_9_nov_2026']['k']}) are a preset on the page; the sponsor has still to confirm the new default. "
         "Read from the built page by `team/explorer/page_numbers.py`.", '',
         '| | Number |', '|---|---|',
         f"| A building with no record at all scores, for a cafe or restaurant | {s['a_building_with_no_record_scores']['cafe']} of 100, {s['cafe_head_start_over_a_shop_with_no_record']['default']} more than for a shop "
         f"({s['cafe_head_start_over_a_shop_with_no_record']['cafe_agreed_9_nov']} and {s['cafe_head_start_over_a_shop_with_no_record']['agreed_9_nov']} more with the weights of 9 November) |",
         f"| Storefronts whose top candidate is a cafe or restaurant | {s['top_candidate_is_a_cafe']['of_storefronts']} of {s['top_candidate_is_a_cafe']['storefronts']} ({s['top_candidate_is_a_cafe']['of_empty']} of the {f['empty']} empty) |",
         f"| The same with the heritage weight at zero | {s['if_heritage_weight_is_zero']['cafe_top']} of {f['storefronts']}; the top candidate changes on {s['if_heritage_weight_is_zero']['top_candidate_changes']} |",
         f"| Precedent input for a cafe or restaurant, lowest and highest across the storefronts (0 to 100) | {s['inputs_by_use']['cafe']['precedents'][0]} to {s['inputs_by_use']['cafe']['precedents'][1]}; for a showroom {s['inputs_by_use']['showroom']['precedents'][0]} to {s['inputs_by_use']['showroom']['precedents'][1]} |",
         f"| Community input for a cafe or restaurant, the same at every storefront | {s['inputs_by_use']['cafe']['community'][0]} |",
         f"| The same with the six weights agreed on 9 November (community and precedents back in) | {s['with_the_weights_agreed_9_nov']['cafe_top']} of {f['storefronts']} ({s['with_the_weights_agreed_9_nov']['cafe_top_empty']} of the empty); the top candidate changes on {s['with_the_weights_agreed_9_nov']['top_candidate_changes']} ({s['with_the_weights_agreed_9_nov']['of_empty']} of the empty) |",
         f"| Top candidate changes when today's tenant is counted as history (as the page did until 21 November 2026) | {s['with_todays_tenant_as_history']['top_candidate_changes']} of {f['storefronts']} |",
         f"| Top candidate changes when only the firmest records count | {s['firmest_records_only']['top_candidate_changes']} of {f['storefronts']} |",
         f"| Top candidate changes when the size input reads the whole building, not the ground floor (as the page did until 24 November 2026) | {s['with_the_whole_building_as_the_size']['top_candidate_changes']} of {f['storefronts']} ({s['with_the_whole_building_as_the_size']['of_empty']} of the empty) |",
         f"| Top candidates that rest on two kinds of source at the address / one kind / inference only / no record of the use there | {s['evidence_behind_top_candidates']['two']} / {s['evidence_behind_top_candidates']['one']} / {s['evidence_behind_top_candidates']['placed']} / {s['evidence_behind_top_candidates']['none']} |",
         f"| Top candidates that score no higher than at a building with no record | {s['top_candidate_no_higher_than_no_record']} |",
         '',
         '## The plan for the empty storefronts', '',
         '| | Number |', '|---|---|',
         f"| Sheets | {pl['sheets']} |",
         '| Candidate uses | ' + ', '.join(f'{v2} {k2}' for k2, v2 in sorted(pl['uses'].items(), key=lambda kv: -kv[1])) + ' |',
         f"| Fit, on average | {pl['fit_mean']} of 100, {pl['lift_mean']:+d} over a building with no record |",
         f"| Candidates resting on two kinds of source / one / inference only / no record of the use there | {pl['evidence'].get('two', 0)} / {pl['evidence'].get('one', 0)} / {pl['evidence'].get('placed', 0)} / {pl['evidence'].get('none', 0)} |",
         f"| Ground floor of the {pl['sheets']} buildings, estimated | {pl['ground_floor_sq_ft']:,} sq ft (at most {pl['ground_floor_sq_ft_at_most']:,}; the whole buildings are {pl['whole_building_sq_ft']:,}) |",
         f"| Ground floors to measure first | {pl['to_measure']} of {pl['sheets']} |",
         f"| **What the spaces rent for, a year** | **{usd(pl['space_rent_low'])} in the low case**; {usd(pl['space_rent_mid'])} in the middle; {usd(pl['space_rent_high'])} high |",
         f"| Rent-pressure watch | {pl['pressure']['block_sides']} block sides, {pl['pressure']['businesses']} businesses, {pl['pressure']['long_standing']} long-standing |",
         '', 'The rent is for the space, from listed rents on this corridor, and is the same whatever the uses. It is not what a building is worth.', '',
         '## Rents', '',
         '| | Number | From |', '|---|---|---|',
         f"| Rents used | {c['rents_used']} ({c['asking']} asking, {c['in_place']} in place, {c['newly_signed_leases']} newly signed) in {c['corridors']} corridors | `team/comps/comps_ranges.json` ({c['engine']}) |",
         f"| Rents in Waverly | {c['waverly']['rows']} ({c['waverly']['asking']} asking, {c['waverly']['in_place']} in place) | the same |",
         f"| Rent level on Waverly's corridor, per sq ft a year, before taxes and insurance | ${c['waverly']['rent_level_low_mid_high'][0]:.2f} low, ${c['waverly']['rent_level_low_mid_high'][1]:.2f} middle, ${c['waverly']['rent_level_low_mid_high'][2]:.2f} high | the same |",
         f"| Held-out rents inside the range | {c['held_out']['inside_widened_range']} of {c['held_out']['rows']} (the range is widened ×{c['held_out']['widened_by']:.2f}; {c['held_out']['inside_plain_80_range']} before widening) | the same |",
         '| Sales check, use by use | ' + '; '.join(f'{k2}: {v2}' for k2, v2 in c['sales_check'].items()) + ' | the same |',
         '| Where the sales check rests on a floor area the team assumed | ' + '; '.join(
             f"{k2}: {v2['assumed_sq_ft']:,} sq ft assumed; reads \"covers\" up to about {v2['covers_up_to_sq_ft']:,} and \"does not cover\" from about "
             f"{v2['does_not_cover_from_sq_ft']:,} (usual size {v2['usual_size_sq_ft'][0]:,} to {v2['usual_size_sq_ft'][1]:,})" for k2, v2 in c['sales_check_floor_area'].items()) + ' | the same |',
         '| Estimators tried on the same held-out rents: error of the middle figure in logs, then the score of the range (lower is better on both) | ' + '; '.join(
             f"{x['estimator']}: {x['error_of_the_middle_figure_in_logs']:.3f}, {x['interval_score']:.1f}" for x in c['estimators_tried']) + ' | the same |',
         f"| Library rows checked against their source by a person | {c['library_rows_checked_by_a_person']} of {c['library_rows']} | `verified_by` in `team/comps/library/` |",
         '',
         '## The back-test', '',
         f"Does a use on record before 1960 predict the use today, on {b['parcels']} Greenmount parcels outside the frontage? "
         f"**The test {'passes' if b['passes_the_agreed_rule'] else 'does not pass'} the rule agreed with the sponsor on 9 November 2026.** From `team/validation/out/backtest_v2.json`.", '',
         '| | Number |', '|---|---|',
         f"| One-sided shuffle test, records up to 1960 | **p = {pv(b['p_1960'])}** ({b['pairs']} pairs, {b['pairs_true_today']} true today) |",
         f"| The same before the leak found on 17 November 2026 was fixed (not valid) | p = {pv(b['p_1960_before_leak_fix'])} |",
         f"| Records up to 1940 | p = {pv(b['p_1940'])} |",
         f"| Ordinary storefront trades only | p = {pv(b['p_1960_storefront_trades_only'])} |",
         f"| Every kind of use except automotive | p = {pv(b['p_1960_without_automotive'])} |",
         f"| Automotive: parcels with it on record before 1960, and how many are automotive today | {b['automotive']['of_which_today']} of {b['automotive']['parcels_with_it_on_record']} (base rate {b['automotive']['base_rate']:.0%}) |",
         f"| Leaving one parcel out at a time | p from {pv(b['leave_one_parcel_out']['min'])} to {pv(b['leave_one_parcel_out']['max'])}; {b['leave_one_parcel_out']['below_0_05']} of {b['leave_one_parcel_out']['runs']} runs below 0.05 |",
         f"| Without the multi-tenant centre ({', '.join(b['multi_tenant_parcels'])} Greenmount) | p = {pv(b['p_1960_without_multi_tenant'])} |",
         f"| History coded from linked businesses and directory lines only | p = {pv(b['p_1960_stated_uses_only'])} |",
         f"| Low-confidence codes of today's use left out | p = {pv(b['p_1960_without_low_confidence'])} |",
         f"| Held-out forecast error (log loss), without and with history | {b['held_out_log_loss'][0]:.4f} to {b['held_out_log_loss'][1]:.4f} |",
         f"| Held-out gain per row, with a 95% interval | {b['held_out_gain_per_row']:+.4f} ({b['held_out_gain_ci95'][0]:+.4f} to {b['held_out_gain_ci95'][1]:+.4f}): {'above zero' if b['gain_distinguishable_from_zero'] else 'not distinguishable from zero'} |",
         f"| Held-out ranking (AUC), without and with history | {b['held_out_auc'][0]:.3f} to {b['held_out_auc'][1]:.3f} |",
         f"| The same measure on the data the model was fitted to (flatters; do not quote alone) | {b['in_sample_auc'][0]:.3f} to {b['in_sample_auc'][1]:.3f} |",
         f"| Frontage storefronts the test can use, and empty ones it cannot | {b['frontage_storefronts_tested']} and {b['frontage_empty_storefronts_not_tested']} |",
         f"| First back-test (hit or miss, frontage, records up to 1960) | {b['first_back_test_1960']['hit']} of {b['first_back_test_1960']['of']}, against {b['first_back_test_1960']['plain_guess']} for a plain guess |",
         '', 'If the rule fails: ' + b['if_it_fails'] + '.', '',
         '## What a person has checked', '',
         '| | Checked | Of |', '|---|---|---|',
         f"| Tenant rows entered or checked by a person | {k['tenant_rows_entered_or_checked_by_a_person']} | {k['tenant_rows']} |",
         f"| \"Use today\" rows on the other blocks | {k['outcome_rows_checked_by_a_person']} | {k['outcome_rows']} |",
         f"| Comps library rows | {k['comps_library_rows_checked_by_a_person']} | {k['comps_library_rows']} |",
         f"| Blind reference timelines built | {k['blind_timelines_built']} | {k['blind_timelines_needed']} |",
         f"| \"Checked by\" lines signed | {k['checked_by_lines_signed']} | {k['checked_by_lines']} |",
         '', 'Unsigned: ' + ', '.join(f'`{u}`' for u in k['unsigned_files']) + '.', '',
         '## Documents that quote other numbers', '']
    if n['other_documents']:
        L += ['Living documents in `team/` whose counts differ from the data today. They are listed here for their authors; this script changes no document.', '',
              '| Document | What | It says | The data today |', '|---|---|---|---|']
        L += [f"| `{x['document']}` | {x['what']} | {x['says']} | {x['now']:,} |" for x in n['other_documents']]
    else:
        L.append('None found among the counts this script checks.')
    L += ['', '## To rebuild', '', '```bash',
          'python3 team/extractor/extract.py            # if the tenant list or a source changed',
          'python3 team/comps/comps_engine.py',
          'python3 team/validation/backtest.py          # about a minute',
          'python3 team/explorer/build_explorer.py',
          'python3 team/explorer/page_numbers.py        # needs Playwright for Python; reads the numbers off the built page',
          'python3 team/numbers_of_record.py',
          'python3 -m unittest ' + ' '.join(TESTS),
          '```', '']
    return '\n'.join(L)


def main():
    n = build()
    js = json.dumps(n, indent=1, ensure_ascii=False) + '\n'
    md = markdown(n)
    paths = (os.path.join(HERE, 'numbers_of_record.json'), os.path.join(HERE, 'NUMBERS.md'))
    docs = [(d, text(*d.split('/'))) for d in DOCS]
    stale_docs = [d for d, t in docs if fill(t, n) != t]
    if '--check' in sys.argv:
        ok = all(os.path.exists(p) and open(p, encoding='utf-8').read() == t for p, t in zip(paths, (js, md)))
        if not ok:
            print('team/NUMBERS.md or team/numbers_of_record.json is out of date: rerun team/numbers_of_record.py')
        for d in stale_docs:
            print(d, 'quotes a figure that is not in the data today: rerun team/numbers_of_record.py')
        if ok and not stale_docs:
            print('numbers of record are current, and so are the', len(DOCS), 'documents that quote them')
        return 0 if ok and not stale_docs else 1
    for p, t in zip(paths, (js, md)):
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(t)
    for d, t in docs:
        if d in stale_docs:
            with open(os.path.join(REPO, *d.split('/')), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(fill(t, n))
    print('wrote team/NUMBERS.md and team/numbers_of_record.json:', n['frontage']['empty'], 'empty of', n['frontage']['storefronts'], 'storefronts; back-test p =',
          n['backtest']['p_1960'], '; plan low case', usd(n['plan']['space_rent_low']), '; documents updated:', ', '.join(stale_docs) or 'none')
    return 0


if __name__ == '__main__':
    sys.exit(main())
