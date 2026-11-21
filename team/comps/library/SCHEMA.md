# Shared schema for comps research (all three researchers)

Formats (use these format_id values exactly):
- cafe: cafe or sit-down restaurant (seating, 800-4,000 sq ft)
- counter: take-away counter (coffee, ice cream, 250-1,500 sq ft)
- foodmaker: food maker with a shop (bakery, coffee roaster, ice-cream maker, 1,000-6,000 sq ft)
- shop: small independent shop (gift, apparel, books, 400-2,500 sq ft)
- showroom: showroom or large shop (furniture, home goods, makers' store, 2,500-12,000 sq ft)
- bike: bike shop with repairs (800-4,000 sq ft)
- services: barber, hair or nail salon, other personal services (400-2,000 sq ft)
- fitness: boutique fitness or yoga studio (1,500-6,000 sq ft)
- studio: arts studio, gallery or rehearsal space (400-8,000 sq ft)
- venue: small performance, event or cinema venue (2,000-15,000 sq ft)
- office: small office or coworking (300-10,000 sq ft)
- workshop: maker workshop with a counter (woodwork, ceramics, repair; 500-6,000 sq ft)
- community: community, health or nonprofit space (1,000-10,000 sq ft)
- housing: upper-floor or rowhouse apartment (rent per unit per month, and per sq ft if stated)
- mixed: a multi-tenant building's average rent, where the source does not give rents by tenant (rents.csv only; the engine gives it no use multiplier)

geo_tier values: waverly (Greenmount Ave E 25th-E 35th St or Waverly), baltimore_corridor (other Baltimore neighbourhood main streets), other_city (comparable neighbourhood corridors in other US cities), national (industry-wide figures).

Comparable corridors in other cities (from the team's case library; prefer these): Philadelphia East Passyunk Ave and Germantown Ave; Detroit Livernois Ave (Avenue of Fashion) and McNichols (Live6); New Orleans O.C. Haley Blvd; Washington DC H Street NE and Anacostia (MLK Jr Ave SE); Pittsburgh Penn Ave (East Liberty, Garfield) and Butler St (Lawrenceville); Chicago 53rd St (Hyde Park) and Bronzeville (47th St).
Baltimore corridors: Waverly/Greenmount, Charles Village (St Paul St), Hampden (W 36th St), Remington, Station North (North Ave, Charles St), Hamilton-Lauraville (Harford Rd), Highlandtown (Eastern Ave), Pigtown (Washington Blvd), Belair-Edison (Belair Rd), Fells Point (Broadway), Mount Vernon.


Traceability (non-negotiable): every row needs source_url, source_title, accessed_on (YYYY-MM-DD), figure_year, figure_type (asking | reported | estimated | calculated), and evidence_quote: the exact short phrase from the source that states the figure (under 25 words). If you divide or multiply, figure_type = calculated and notes must show the arithmetic with the inputs. Never estimate a missing number; leave it blank. A figure you could not open and read yourself does not go in.

Columns added on 21 November 2026 (sponsor's review, 17 November 2026):
- rent_kind (rents.csv): asking (a rent a listing asks), in place (a rent a tenant is paying, usually from a for-sale listing), or reference (a figure kept for context that the engine does not read).
- verified_by, verified_on (all three files): the initials of the person who opened the source and checked the row against it, and the date (YYYY-MM-DD). Blank means nobody has. A row collected with AI assistance is not verified until a person fills these.
