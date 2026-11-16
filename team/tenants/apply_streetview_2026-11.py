"""Fold the Street View check (team/evidence/streetview_check_2026-11.csv) into the October tenant list.

Only the 28 rows still marked `unknown` are touched. Each settled address gets its status, business type and a
dated source; the 9 that stay unclear keep `unknown` and gain a note. Standard library only.

    python3 team/tenants/apply_streetview_2026-11.py
"""
import csv
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEN = os.path.join(REPO, 'team/tenants/current_tenants_2026-10.csv')
SV = os.path.join(REPO, 'team/evidence/streetview_check_2026-11.csv')

# What each settled address is, in the team's use categories. Names are the businesses on the signs; houses get
# no name (private residences).
SETTLED = {
    '2934 Greenmount Ave': ('vacant', '', 'vacant'),
    '2936 Greenmount Ave': ('vacant', '', 'vacant'),
    '2938 Greenmount Ave': ('occupied', 'Outreach Temple Apostolic (church; entrance at 2940)', 'institutional & religious'),
    '2940 Greenmount Ave': ('occupied', 'Outreach Temple Apostolic (church)', 'institutional & religious'),
    '2944 Greenmount Ave': ('occupied', '', 'residential'),
    '2946 Greenmount Ave': ('vacant', '', 'vacant'),
    '2948 Greenmount Ave': ('occupied', '', 'residential'),
    '2950 Greenmount Ave': ('occupied', '', 'residential'),
    '2952 Greenmount Ave': ('occupied', '', 'residential'),
    '2954 Greenmount Ave': ('occupied', '', 'residential'),
    '2956 Greenmount Ave': ('occupied', '', 'residential'),
    '2958 Greenmount Ave': ('for lease', '', 'vacant'),
    '3023 Greenmount Ave': ('vacant', '', 'vacant'),
    '3040 Greenmount Ave': ('occupied', 'Blossom Care & Behavioral Services', 'office'),
    '3110 Greenmount Ave': ('occupied', "Herman's Discount (same shop as 3106)", 'retail goods'),
    '3127 Greenmount Ave': ('occupied', 'Citi Trends (clothing)', 'retail goods'),
    '3133 Greenmount Ave': ('occupied', 'Citi Trends (clothing; same store as 3127)', 'retail goods'),
    '3206 Greenmount Ave': ('occupied', "Magic Men's Wear (same shop as 3204)", 'retail goods'),
    '3212 Greenmount Ave': ('occupied', 'Blackstone Menswear (entrance at 3210)', 'retail goods'),
}
# Settled by the sponsor's walk photos of 3 November rather than the September imagery alone.
PHOTO = {'3127 Greenmount Ave', '3133 Greenmount Ave'}
DIRECT = {'2946 Greenmount Ave'}   # closure confirmed by Kevin Lin, 10 November 2026


def main():
    sv = {r['address']: r for r in csv.DictReader(open(SV, encoding='utf-8'))}
    with open(TEN, encoding='utf-8-sig') as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        rows = list(rd)
    n = 0
    for t in rows:
        a = t['address']
        if t['status'] != 'unknown' or a not in sv:
            continue
        s = sv[a]
        seen = f"Street View {s['imagery']}: {s['streetview_status']}; {s['what_is_visible']}"
        if s['final_note']:
            seen += f" Final: {s['final_note']}"
        if a in SETTLED:
            t['status'], name, t['business_type'] = SETTLED[a]
            t['tenant_name'] = name
            t['confidence'] = 'high' if s['confidence'] == 'high' or a in PHOTO | DIRECT else 'medium'
            t['needs_street_view_check'] = 'no'
            if a in DIRECT:
                t['evidence_date'], t['source_type'] = '2026-11-10', 'team check'
                t['source_title'] = 'Team check, 10 November 2026 (business closed)'
            elif a in PHOTO:
                t['evidence_date'], t['source_type'] = '2026-11-03', 'sponsor photo'
                t['source_title'] = "Sponsor's walk photos, 3 November 2026 (team only, not in the repo)"
            else:
                t['evidence_date'], t['source_type'] = s['imagery'], 'street view'
                t['source_title'] = 'Google Street View, September 2026 imagery'
            t['source_url'] = ''
        else:
            t['needs_street_view_check'] = 'walk'
        t['accessed_on'] = s['checked_on']
        t['entered_by'] = 'Kevin Lin (Street View check, team/evidence/streetview_check_2026-11.csv)'
        seen = seen.replace('\u00e7', 'c').replace('\u2013', '-')   # keep the file ASCII, as it was
        t['notes'] = (seen + ' | ' + t['notes']).strip(' |')
        n += 1
    with open(TEN, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(f'{n} rows updated')


if __name__ == '__main__':
    main()
