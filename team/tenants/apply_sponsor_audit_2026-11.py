"""Fold the sponsor's storefront audit (November 2026) into the tenant list.

The sponsor checked the list of empty storefronts against its own audit (records, September 2026 Street View, and
walks on 30 October and 3 November) and sent the result on 16 November 2026: 22 of the 69 frontage parcels are
empty. On 17 November it added 2942 and confirmed 3211, making 24. This applies the rows where the audit differs from the list. A Yelp page marked "Updated <month>" was the
main cause: that date is when the page was refreshed, not proof the shop is open. Standard library only.

    python3 team/tenants/apply_sponsor_audit_2026-11.py

Rows already stamped by this script are skipped, so it can be run again when the audit changes.
"""
import csv
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEN = os.path.join(REPO, 'team/tenants/current_tenants_2026-10.csv')
SOURCE = "Sponsor's storefront audit, November 2026 (records, September 2026 Street View, walks on 30 October and 3 November)"
BY = "Team, from the sponsor's storefront audit (AI-assisted entry)"

# Empty on the audit, not empty on the list. The value is what the audit says about the address, if anything.
EMPTY = {
    '2920': '', '2930': 'The old barber sign is still up.', '3010': 'The convenience store has closed (seen 3 November).',
    '3011': '', '3015': '', '3019': '', '3029': '', '3038': '', '3111': '',
    '3120': "The neon sign belongs to the next building.", '3122': 'The old jewelry sign is still up.',
    '3200': '', '3224': '', '2942': 'Added by the sponsor on 17 November.',
}
# Open on the audit; the list had no occupant. The use category is not coded yet.
OPEN = {'3000': 'The Practitioner Provider'}
# A vacant house, not a storefront: it stays vacant, as a residence, so the plan leaves it out.
HOUSE = {'2936'}


def main():
    with open(TEN, encoding='utf-8', newline='') as fh:
        rd = csv.DictReader(fh)
        fields, rows = rd.fieldnames, list(rd)
    seen = set()
    for r in rows:
        n = r['address'].split()[0]
        stamp = dict(evidence_date='2026-11', source_title=SOURCE, source_url='', source_type='sponsor audit',
                     accessed_on='2026-11-16', confidence='high', needs_street_view_check='no', entered_by=BY)
        if r['source_type'] == 'sponsor audit':
            seen.add(n)
            continue                      # already applied
        if n in EMPTY:
            was = r['tenant_name'].strip()
            note = 'Empty on the sponsor\'s audit.' + (' ' + EMPTY[n] if EMPTY[n] else '') + (f' The list had: {was}.' if was else '')
            r.update(stamp, status='vacant', tenant_name='', business_type='vacant', notes=(note + ' ' + r['notes']).strip())
        elif n in OPEN:
            r.update(stamp, status='occupied', tenant_name=OPEN[n], business_type='',
                     notes=('Open on the sponsor\'s audit; use category not coded yet. ' + r['notes']).strip())
        elif n in HOUSE:
            r.update(stamp, status='vacant', tenant_name='', business_type='residential',
                     notes=('A vacant house, not a storefront (sponsor\'s audit): left out of the plan. ' + r['notes']).strip())
        else:
            continue
        seen.add(n)
    missing = (set(EMPTY) | set(OPEN) | HOUSE) - seen
    assert not missing, f'addresses not in the tenant list: {sorted(missing)}'
    with open(TEN, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print('updated', len(seen), 'rows; empty now:', sum(1 for r in rows if r['status'] in ('vacant', 'for lease') and r['business_type'] != 'residential'))


if __name__ == '__main__':
    main()
