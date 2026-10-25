# Extractor v1 validation against the reference timelines

Reference: `team/week1/out/use_timelines.md`, built by hand from the sponsor records in week 1. A reference row counts as recalled when the extractor has at least one record of the same use category at that property within its years (one year either side). Category agreement is the share of the extractor's coded records that fall inside a reference row's years and carry a category that row has.

Targets from the research plan: recall 90% or more, category agreement 85% or more.

| Scope | Reference rows | Recalled | Recall | Recall where the source covers those years | Records scored | Category agreement |
|---|---|---|---|---|---|---|
| all sources | 32 | 25 | 78% | 96% | 135 | 88% |
| new sources only (not used to build the references) | 32 | 9 | 28% | 82% | 28 | 89% |

The "all sources" row is not an independent test: the references were built from the sponsor records the extractor also reads. The "new sources only" row is the independent one. The four blind reference timelines in the research plan, built by a team member without looking at this output, are still needed.

## Reference rows and whether each was found (all sources)

| Property | Period | Use | Category | Found |
|---|---|---|---|---|
| 3117 Greenmount Ave | 1886-1908 | Livery stable | automotive | yes |
| 3117 Greenmount Ave | 1915-1917 | Livery stable | automotive | yes |
| 3117 Greenmount Ave | 1926-1926 | Auto service | automotive | yes |
| 3117 Greenmount Ave | 1928-1932 | Furniture showroom | retail goods | yes |
| 3117 Greenmount Ave | 1933-1935 | Furniture and appliances | retail goods | yes |
| 3117 Greenmount Ave | 1935-1936 | Furniture | retail goods | yes |
| 3117 Greenmount Ave | 1936-1955 | Auto accessories, sporting goods | automotive | yes |
| 3117 Greenmount Ave | 1957-1962 | Toys and hobby | retail goods | yes |
| 3117 Greenmount Ave | 1972-1989 | Furniture | retail goods | yes |
| 3117 Greenmount Ave | 1990-1999 | Apparel | retail goods | yes |
| 3200 Greenmount Ave | 1901-1922 | Corner saloon | food & drink | yes |
| 3200 Greenmount Ave | 1928-1928 | Soft-drinks store | food & drink | yes |
| 3200 Greenmount Ave | 1929-1929 | Offered for lease | vacant | no |
| 3200 Greenmount Ave | 1931-1936 | Drugstore with soda fountain | food & drink | yes |
| 3200 Greenmount Ave | 1936-1963 | 24-hour restaurant | food & drink | yes |
| 3200 Greenmount Ave | 1955-1955 | Beauty salon (upper floor) | personal services | yes |
| 3200 Greenmount Ave | 1978-1978 | Restaurant and carryout | food & drink | yes |
| 3200 Greenmount Ave | 1980-1980 | Indian restaurant | food & drink | yes |
| 3200 Greenmount Ave | 2015-2015 | Carryout | food & drink | yes |
| 3224 Greenmount Ave | 1901-1929 | Laundry | personal services | yes |
| 3224 Greenmount Ave | 1906-1906 | Dwelling for rent | vacant | no |
| 3224 Greenmount Ave | 1921-1932 | Laundry | personal services | yes |
| 3224 Greenmount Ave | 1930-1932 | Auto parts and hardware | automotive | yes |
| 3224 Greenmount Ave | 1937-1937 | Laundry | personal services | yes |
| 3224 Greenmount Ave | 1935-1955 | Shoes and women's fashion | retail goods | yes |
| 3224 Greenmount Ave | 1955-1964 | Shoes | retail goods | yes |
| 3224 Greenmount Ave | 1967-1967 | Restaurant | food & drink | yes |
| 401 E 30th St | 1915-1944 | Professional ballpark | entertainment & assembly | no |
| 401 E 30th St | 1944-1944 | Use ends | entertainment & assembly | no |
| 401 E 30th St | 1954-1969 | Bottling plant | production & light industry | no |
| 401 E 30th St | 1987-1987 | Bottling | production & light industry | no |
| 401 E 30th St | 2018-2021 | Grocery | food & drink | no |

## Second test: the reference occupants from the week-2 report

`reference/reference_occupants.csv` lists 30 named occupants on the four reference properties; 24 are on frontage parcels (the others are at 401 E 30th St). An occupant counts as found when a record at its parcel, within its years (one year either side), names it by one of its aliases.

| Scope | Occupants | Found | Recall |
|---|---|---|---|
| all sources | 24 | 24 | 100% |
| new sources only | 24 | 6 | 25% |

| Property | Occupant | Years | Found (all sources) | Found in new sources |
|---|---|---|---|---|
| 3117 Greenmount Ave | Dentry & Zoll / Zoll livery | 1886-1908 | yes | polk_directory |
| 3117 Greenmount Ave | W. C. Childs & Son livery | 1915-1917 | yes | polk_directory |
| 3117 Greenmount Ave | United Garage Co. | 1926-1926 | yes | no |
| 3117 Greenmount Ave | Miller Brothers Furniture | 1928-1932 | yes | no |
| 3117 Greenmount Ave | Century Furniture Co. | 1933-1935 | yes | no |
| 3117 Greenmount Ave | Hecht's Furniture House | 1935-1936 | yes | no |
| 3117 Greenmount Ave | Joe the Motorist's Friend | 1936-1955 | yes | nr_inventory |
| 3117 Greenmount Ave | Engelman's Kiddieland | 1957-1962 | yes | no |
| 3117 Greenmount Ave | Moses Zalis Furniture | 1972-1989 | yes | no |
| 3117 Greenmount Ave | New York Fashions, Inc. | 1990-1990 | yes | no |
| 3200 Greenmount Ave | Reilley/Muller saloon | 1901-1908 | yes | polk_directory |
| 3200 Greenmount Ave | Samstag saloon and soft drinks | 1918-1928 | yes | nr_inventory, polk_directory |
| 3200 Greenmount Ave | White Coffee Pot | 1936-1963 | yes | no |
| 3200 Greenmount Ave | Adolphe Beauty Salon | 1955-1955 | yes | no |
| 3200 Greenmount Ave | Hotspot restaurant and carryout | 1978-1978 | yes | no |
| 3200 Greenmount Ave | Shalimar | 1980-1980 | yes | no |
| 3200 Greenmount Ave | Green's Carryout | 2015-2015 | yes | no |
| 3224 Greenmount Ave | Sam Lee Laundry | 1901-1937 | yes | polk_directory |
| 3224 Greenmount Ave | Wick Wo laundry | 1901-1929 | yes | no |
| 3224 Greenmount Ave | Taubman's | 1930-1932 | yes | no |
| 3224 Greenmount Ave | Wyman Shoe Co. | 1935-1955 | yes | no |
| 3224 Greenmount Ave | Jason Shoes | 1955-1955 | yes | no |
| 3224 Greenmount Ave | Anderson's Restaurant | 1967-1967 | yes | no |
| 3224 Greenmount Ave | The Kove Home Furnishings Center | 1976-1976 | yes | no |
