"""Apply the sponsor's storefront audit of November 2026 to the tenant list.

Source: Jeff Jetton's email of 16 November 2026. The sponsor's BDC storefront audit (records, September Street View
and walks on 30 October and 3 November) marks 22 of the 69 frontage parcels empty, gives 3000 as open, and says 2936 is
a vacant house rather than a storefront. Run after apply_streetview_2026-11.py. Standard library only.

    python3 team/tenants/apply_sponsor_audit_2026-11.py
"""
import csv
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEN = os.path.join(REPO, 'team/tenants/current_tenants_2026-10.csv')
SOURCE = "Sponsor's storefront audit, November 2026 (records, September Street View, walks on 30 Oct and 3 Nov)"
DATE = '2026-11-16'

# The 22 the audit marks empty, with the sponsor's reason where the email gives one.
EMPTY = {
    '2920': '', '2930': 'old barber sign still up', '2932': '', '2934': '', '2946': '', '2958': '',
    '3010': 'convenience store closed (checked 3 Nov)', '3011': '', '3015': '', '3019': '', '3023': '', '3026': '',
    '3029': '', '3036': '', '3038': '', '3107': '', '3111': '', '3117': '',
    '3120': "the neon sign belongs to the next building", '3122': 'old jewelry sign still up', '3200': '', '3224': '',
}
# Street numbers inside a parcel the audit marks empty.
PART_OF = {'3013': '3011', '3124': '3122'}
OPEN = {'3000': ('The Practitioner Provider (medical practice)', 'office')}
HOUSE = {'2936': 'vacant house, not a storefront: out of the block plan'}


def stamp(t, conf='high'):
    t.update(evidence_date=DATE, source_type='sponsor audit', source_title=SOURCE, source_url='', accessed_on=DATE,
             confidence=conf, needs_street_view_check='no', entered_by='Sponsor storefront audit (email of 16 Nov 2026)')


def main():
    with open(TEN, encoding='utf-8-sig') as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        rows = list(rd)
    n = 0
    for t in rows:
        num = t['address'].split()[0]
        was = f"Was: {t['status']}" + (f" ({t['tenant_name']})" if t['tenant_name'] else '')
        if num in EMPTY or num in PART_OF:
            why = EMPTY.get(num) or (f'part of {PART_OF[num]}, which the audit marks empty' if num in PART_OF else '')
            t['status'] = 'for lease' if t['status'] == 'for lease' else 'vacant'
            t['tenant_name'], t['business_type'] = '', 'vacant'
            note = 'Sponsor audit (Nov 2026): empty' + (f'; {why}' if why else '') + f'. {was}.'
        elif num in OPEN:
            t['status'] = 'occupied'
            t['tenant_name'], t['business_type'] = OPEN[num]
            note = f'Sponsor audit (Nov 2026): open. {was}.'
        elif num in HOUSE:
            t['status'], t['tenant_name'], t['business_type'] = 'vacant', '', 'residential'
            note = f'Sponsor audit (Nov 2026): {HOUSE[num]}. {was}.'
        else:
            continue
        stamp(t)
        t['notes'] = (note + ' | ' + t['notes']).strip(' |')
        n += 1
    with open(TEN, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(f'{n} rows updated')


if __name__ == '__main__':
    main()
