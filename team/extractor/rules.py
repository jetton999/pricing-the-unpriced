"""Use-category rules for the Greenmount use-history extractor.

One ordered list of (category, subcategory, regex). The first rule that matches wins, so
specific rules sit above general ones. Categories are the team's list.
Standard library only.
"""
import re

CATEGORIES = ['food & drink', 'retail goods', 'personal services', 'automotive',
              'entertainment & assembly', 'institutional & religious',
              'production & light industry', 'office', 'residential', 'vacant']

RULES = [
    ('residential', 'private garage', r"\b(private garage|(metal|frame|brick|block|1.car|2.car) garage|garage \d+\s*(ft|'|x))"),
    ('residential', 'dwelling (stated)', r'\b(was|is|as) (an? )?(?:(?!stores?\b|shops?\b|theat)[\w\- ,]){0,60}?(dwellings?|rowhouses?|residences?|houses?)\b(?! of)'),
    ('vacant', 'demolition', r'\b(raz(e|ed|ing)|demoli\w*|wreck(ed|ing)?)\b'),
    ('vacant', 'vacant', r'\b(vacant|for lease|for rent|empty)\b'),
    ('entertainment & assembly', 'theatre / pictures', r'\b(mov\w*\s*pict\w*|motion pict\w*|picture show|theat(re|er)|marquee|cinema|movie)\b'),
    ('entertainment & assembly', 'recreation', r'\b(billiard|pool\b|bowling|skating|rink|miniature golf|dance hall|dancing|night ?club|ball ?park|bleacher|grandstand|carnival|bingo|amusement|pleasure club)'),
    ('entertainment & assembly', 'hall / lodge', r'\b(hall\b|lodge|council no|conclave|castle no|assembly hall|club\b)'),
    ('institutional & religious', '', r'\b(church|parochial|school|fir\S* dept|fire (dept|house|engine)|firehouse|engine co|police|post office|library|mission|temple|chapel|rectory|parish|town hall)\b'),
    ('food & drink', 'bar / tavern', r'\b(saloon|tavern|near beer|cocktail|lounge|bar\b|bartndr|beer|liquor|rectifier)\b'),
    ('food & drink', 'restaurant / lunch', r'\b(lunch|restaurant|cafe|café|diner|carry.?out|eat|coffee|soda fountain|ice cream|sandwich|pizza|chicken|grill)\b'),
    ('food & drink', 'food retail', r'\b(grocer\w*|gro\b|xrocer|srocer|meats?\b|market|confr|eonfr|cohfr|confx|confectio\w*|candy|bak(er|ery)|butter and eggs|oysters|sea food|fish\b|dairy|soft.?drinks|soda water|delicatessen|deli\b|produce|prod\b|poultry|flour)'),
    ('automotive', '', r'\b(garage|auto\w*|motorists?|livery|stable|filling station|gas(oline)? station|service station|used car|tire|retread|car wash|motor\b|express\b|wagon)\b'),
    ('personal services', '', r'\b(barber|tailor|shoemkr|sboemkr|slioemkr|shoe ?repair|laund\w*|dressmkr|beauty|hair\w*|cleaner|dyer|photo\w*|dentist|ph[yv]s\w*|chemist|optic\w*|undertaker|funeral|dog hospital|animal hospital|veterin\w*|vet surg|pressing|valet|pawn|loan office|finance co|cash|seamstress)\b'),
    ('retail goods', '', r'\b(hardware|hdwe?\b|hdw\b|dry ?g(oo)?ds|drygds|shoes|boots|furn(iture|gs|s)\b|fu[mr]n?gs?|turns\b|fnriigs|notions|milliner|jewel\w*|jwlr|florist|drugs?\b|druggist|cigars?|tobacco|pianos?|musical|5 ?(&|and) ?10|5c|gen\w* mdse|hat shop|clothing|apparel|men.?s (wear|furn\w*)|stoves|paints|bicycles?|cycle co|store\b|stores\b|shop\b|retail|sales|showroom|toy)'),
    ('production & light industry', '', r'\b(mn?fg|mnfr|manufact\w*|bottl\w*|printing|plumb\w*|plmbr|tinner|sheet metal|metalwkr|contr\w*|lumber|cabtmkr|upholst\w*|uphlstr|coal|feed\b|warehouse|factory|plant|shop for|welder|pipef\w*|metalwk\w*|r[ae]+talwkr|bldr|marblewkr|horseshoer|harnessmkr|blksmith|milling)\b'),
    ('office', '', r'\b(real est\w*|bldg (assn|&|and)|building (assn|association|and loan)|loan assn|savings|sav (and|&) loan|notary|insurance|office|realty|bank|trust co\w*|lawyer|attorney|solr|solicitor)\b'),
    ('residential', '', r'\b(dwellings?|apartments?|apts?\b|rowhouses?|residence|living quarters)\b'),
]
RULES_C = [(c, s, re.compile(rx, re.I)) for c, s, rx in RULES]

# Sanborn sheets print short use labels on the footprint
SANBORN = [
    (r'^\s*D\b|dwelling', 'residential', 'dwelling (Sanborn)'),
    (r'^\s*F\b|\bflats?\b', 'residential', 'flats (Sanborn)'),
    (r'^\s*S\b|\bstore', 'retail goods', 'store building (generic)'),
    (r'vacant|^\s*V\b', 'vacant', 'vacant (Sanborn)'),
]


GENERIC = {'store', 'stores', 'shop', 'sales', 'retail'}


def classify(text):
    """Return (category, subcategory, matched keyword) or ('', '', '').

    A bare 'store' or 'shop' names a building type, not a use: it is coded retail goods with the
    subcategory 'store building (generic)' so that it can be told apart from a stated trade."""
    t = text or ''
    for c, s, rx in RULES_C:
        m = rx.search(t)
        if m:
            if c == 'retail goods' and m.group(0).lower() in GENERIC:
                return c, 'store building (generic)', m.group(0)
            return c, s, m.group(0)
    return '', '', ''


def classify_sanborn(label, expanded=''):
    """Specific words first (saloon, garage, pictures), then the generic Sanborn letters."""
    c = classify(f"{label or ''} {expanded or ''}")
    if c[0] and c[1] not in ('dwelling (stated)', 'store building (generic)'):
        return c
    for rx, cat, sub in SANBORN:
        if re.search(rx, label or '', re.I) or re.search(rx, expanded or '', re.I):
            return cat, sub, (label or expanded)[:20]
    return c
