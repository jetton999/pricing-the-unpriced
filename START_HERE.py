# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Pricing the Unpriced: Starter Notebook
# **NYU CUSP Capstone 2026–2027 · Sponsor: BNBD / Oxcart Assembly**
#
# This notebook loads the corridor knowledge base, shows how the tables join, and leaves you
# with a per-property starter table for each of the two project ideas in `README.md`:
#
# - **Idea 1.** Heritage-anchored highest and best use: what each address *was*, and what it could be.
# - **Idea 2.** Tenant-owned exit: a lease that starts a business as a tenant and ends with it owning the building.
#
# Sections 1–3 are the data tour everyone needs. Section 4 is for Idea 1, section 5 for Idea 2,
# section 6 is the starting line for both. The `map/` app shows the same data on a map, one
# property at a time, and is the quickest way to look at any address this notebook names.
#
# Put this file in the same folder as the CSVs and run top to bottom.
# Requires: `pandas`, `matplotlib`, `networkx`.
#
# `START_HERE.py` and `START_HERE.ipynb` are the same notebook (jupytext pairing). The `.py`
# is the source of truth: edit it, or have your coding agent edit it, then run
# `uvx jupytext --sync START_HERE.py` to refresh the `.ipynb`. Opening either file in
# VS Code, Cursor, or JupyterLab gives you the notebook view. Outputs are never committed.
#

# %%
import pandas as pd, matplotlib.pyplot as plt, networkx as nx, collections
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 40)

props   = pd.read_csv("properties.csv", low_memory=False)
inc     = pd.read_csv("property_incidents.csv", low_memory=False)
subj    = pd.read_csv("subjects.csv", low_memory=False)
isub    = pd.read_csv("incident_subjects.csv", low_memory=False)
ilink   = pd.read_csv("incident_links.csv", low_memory=False)
rips    = pd.read_csv("registered_ips.csv", low_memory=False)
parcels = pd.read_csv("property_parcels.csv", low_memory=False)
grants  = pd.read_csv("grant_program_matches.csv", low_memory=False)
base    = pd.read_csv("baseline_snapshots.csv", low_memory=False)

for name, df in [("properties",props),("incidents",inc),("subjects",subj),
                 ("incident_subjects",isub),("incident_links",ilink),
                 ("registered_ips",rips),("parcels",parcels),("grant_matches",grants),
                 ("baseline_snapshots",base)]:
    print(f"{name:<20} {len(df):>7,} rows   {len(df.columns):>3} cols")

# %% [markdown]
# ## 1. The first thing you need to know
#
# The incident table is **not** 20,308 pieces of curated history. Most of it is
# machine-ingested administrative data: 311 complaints, permits, assessments, crime.
# The curated archival layer is much smaller and much older.
#
# Separating the two is the first job for either idea. An analysis that rewards whichever
# property generated the most paperwork has learned nothing about what the address was.
#

# %%
ADMIN_PREFIXES = ("baltimore:",)
ADMIN_EXACT = {"sdat_assessments", "sdat:owner"}
def is_admin(s):
    s = str(s)
    return s.startswith(ADMIN_PREFIXES) or s in ADMIN_EXACT

inc["layer"] = inc["source"].map(lambda s: "administrative" if is_admin(s) else "curated")
inc["year"] = pd.to_numeric(inc["occurred_at"].astype(str).str[:4], errors="coerce")
cur = inc[inc.layer == "curated"]
print(inc["layer"].value_counts(), "\n")
print("Curated sources:")
print(cur["source"].value_counts().head(15))

# %% [markdown]
# ## 2. Evidence grading: every row is a claim
#
# Every incident is a *claim*, not a fact. The schema carries `evidence_status`,
# `date_precision`, `sensitivity`, and `rights`. Coverage is partial and uneven.
# Rows with a `sensitivity` flag exist so a use proposal or a public narrative does not
# surface a terrible event with no framing. Never drop them silently; see `LICENSE.md`.
#

# %%
print("evidence_status:\n", cur["evidence_status"].fillna("(ungraded)").value_counts(), "\n")
print("date_precision:\n", cur["date_precision"].fillna("(unset)").value_counts(), "\n")
print("sensitivity flags:\n", inc["sensitivity"].dropna().value_counts(), "\n")
print("incident-to-incident link types (the record already encodes disagreement):")
print(ilink["link_type"].value_counts())

# %% [markdown]
# ## 3. Where the depth is, and when
#
# Documentation is concentrated. A handful of properties carry deep archival research;
# most carry only administrative traces. For Idea 1, the deep properties are where a use
# history can be read. For Idea 2, they are the buildings whose story a tenant inherits.
# Sparse documentation is not evidence of no history; treat it as unmeasured.
#

# %%
depth = (cur.groupby("property_id").size().rename("curated_incidents")
           .reset_index().merge(props[["id","address","year_built","zoning_code"]],
                                left_on="property_id", right_on="id", how="left")
           .drop(columns="id").sort_values("curated_incidents", ascending=False))
print(f"properties with >=1 curated incident: {len(depth):,}")
print(f"  >=10: {(depth.curated_incidents>=10).sum():,}    >=25: {(depth.curated_incidents>=25).sum():,}")
print("\nDeepest-documented properties:")
print(depth.head(12).to_string(index=False))

d = inc[(inc.year >= 1650) & (inc.year <= 2029)].copy()
d["decade"] = (d.year // 10 * 10).astype(int)
piv = d.pivot_table(index="decade", columns="layer", values="id", aggfunc="count").fillna(0)
ax = piv.plot(kind="bar", stacked=True, figsize=(14,4.5), width=.85,
              color={"administrative":"#8a8377","curated":"#e8a82d"})
ax.set_yscale("symlog", linthresh=10); ax.set_xlabel(""); ax.set_ylabel("incidents")
ax.set_title("Documented incidents by decade: curated vs administrative")
plt.tight_layout(); plt.show()
print("earliest dated record:", int(d.year.min()), " | pre-1950:", int((d.year < 1950).sum()))

# %% [markdown]
# ## 4. Idea 1: reading what an address was
#
# Idea 1 starts from a documented historic use as the prior for a future use. The curated
# layer carries use in three places: Sanborn maps and Polk directories describe the building
# and the business at it; newspaper clippings describe what happened there; `operated_at`
# links name the business outright.
#
# ### 4a. One property's use history
#

# %%
USE_SOURCES = {"sanborn", "polk", "newspapers_com", "nrhp", "whitepaper"}
uses = (isub[isub.relationship == "operated_at"]
          .merge(inc[["id", "property_id", "year", "source"]],
                 left_on="property_incident_id", right_on="id")
          .merge(subj[["id", "name", "subject_type"]], left_on="subject_id", right_on="id",
                 suffixes=("", "_subj")))
print(f"operated_at links across the corpus: {len(uses):,} "
      f"at {uses.property_id.nunique():,} properties\n")
top = int(uses.property_id.value_counts().index[0])   # most business links
addr = props.set_index("id")["address"].to_dict()

mine = uses[uses.property_id == top].sort_values("year")
print(f"Businesses that operated at property {top} ({addr[top]}):")
print(mine[["year", "name", "subject_type", "source"]].drop_duplicates("name").to_string(index=False))

hist = cur[(cur.property_id == top) & (cur.source.isin(USE_SOURCES))]
print(f"\nUse-bearing curated records at property {top}: {len(hist):,}")
print(hist.sort_values("year")[["year", "source", "summary"]].head(10).to_string(index=False, max_colwidth=90))

# %% [markdown]
# ### 4b. Which properties have a use history worth extracting
#
# A use-history timeline needs more than one business and more than one source. This ranks
# properties by distinct businesses and by use-bearing records, then attaches the present-state
# fields a candidate-use generator would read next: zoning, size, age, vacancy, whether
# something is trading there today, and the market typology of the surrounding area.
#

# %%
biz_count = (uses[uses.subject_type == "business"]
               .groupby("property_id")["name"].nunique().rename("distinct_businesses"))
use_recs = cur[cur.source.isin(USE_SOURCES)].groupby("property_id").size().rename("use_records")
span = uses.groupby("property_id")["year"].agg(first_use="min", last_use="max")

idea1 = (props[["id","address","block_side_id","zoning_code","year_built","structure_sqft",
                "vacancy_indicator","has_active_business","market_typology","main_street_district"]]
           .rename(columns={"id":"property_id"})
           .merge(biz_count, left_on="property_id", right_index=True, how="left")
           .merge(use_recs, left_on="property_id", right_index=True, how="left")
           .merge(span, left_on="property_id", right_index=True, how="left")
           .fillna({"distinct_businesses":0, "use_records":0}))
idea1["zoning_code"] = idea1["zoning_code"].str.strip()

ready = idea1[(idea1.distinct_businesses >= 3) & (idea1.use_records >= 5)]
print(f"properties with >=3 distinct businesses and >=5 use-bearing records: {len(ready):,}\n")
print(ready.sort_values("distinct_businesses", ascending=False)
           .head(15)[["address","zoning_code","year_built","structure_sqft","vacancy_indicator",
                      "has_active_business","market_typology","distinct_businesses","use_records","first_use","last_use"]]
           .to_string(index=False))

# %% [markdown]
# ### 4c. The assemblage unit and the saturation baseline
#
# The export has no acquisition groupings. `block_side_id` is the default unit of analysis
# until the sponsor names specific assemblages. For each block side this shows how many
# properties it holds, how many have a use history, how many are vacant, and how many have a
# business trading today. That is the crude baseline for the optimizer's saturation
# constraint: three of the same thing on one block side is the failure case.
#
# One gap to know about: the `nearby_restaurants`, `nearby_shops`, and `walk_score` columns
# are empty in this export. The current business mix has to come from the `operated_at`
# links with recent years, or from an outside source such as Open Baltimore liquor licenses.
#

# %%
bs = (idea1.groupby("block_side_id")
        .agg(properties=("property_id","size"),
             with_use_history=("distinct_businesses", lambda s: int((s > 0).sum())),
             vacant=("vacancy_indicator", lambda s: int((s == True).sum())),
             active_business=("has_active_business", lambda s: int((s == True).sum())),
             main_street=("main_street_district", lambda s: int((s == True).sum())),
             typology=("market_typology", lambda s: s.mode().iat[0] if s.notna().any() else None))
        .sort_values("with_use_history", ascending=False))
print(f"block sides: {len(bs):,}\n")
print(bs.head(12).to_string())

# Shared history inside a block side: property pairs on the same side that share a person,
# family, or business. An assemblage with shared history is a different proposition from a
# row of unrelated lots.
edges = (isub.merge(inc[["id","property_id"]], left_on="property_incident_id", right_on="id")
             .merge(subj[["id","name","subject_type"]], left_on="subject_id", right_on="id",
                    suffixes=("_inc","_subj")))
side = props.set_index("id")["block_side_id"].to_dict()
subj_to_props = collections.defaultdict(set)
for _, r in edges.iterrows():
    subj_to_props[r.subject_id].add(r.property_id)
pair = collections.Counter()
for sid, ps in subj_to_props.items():
    ps = sorted(ps)
    for i in range(len(ps)):
        for j in range(i+1, len(ps)):
            if side.get(ps[i]) is not None and side.get(ps[i]) == side.get(ps[j]):
                pair[(ps[i], ps[j])] += 1
print(f"\nsame-block-side property pairs sharing >=1 subject: {len(pair):,}")
for (a, b), n in pair.most_common(8):
    print(f"  {n:>3} shared subjects   {addr.get(a,a)}  <->  {addr.get(b,b)}")

# %% [markdown]
# ## 5. Idea 2: the numbers a lease has to work with
#
# Idea 2 designs a lease that starts a business as an ordinary tenant and ends with it owning
# the building. The export carries the property side of that: what buildings last sold for,
# what they are assessed at, and the fair market rent in the ZIP. The tenant side (sales and
# P&L for the operating restaurant at 2731 Greenmount) and the deal side (which buildings the
# trust holds, investor targets) come from the sponsor under NDA.
#
# ### 5a. What commercial buildings on the corridor cost
#

# %%
fin = props[["id","address","block_side_id","zoning_code","structure_sqft","year_built",
             "last_sale_price","last_sale_date","assessed_value","fair_market_rent_2br",
             "ground_rent","vacancy_indicator","has_active_business"]].copy()
fin["zoning_code"] = fin["zoning_code"].str.strip()
fin["commercial"] = fin.zoning_code.fillna("").str.match(r"^(C|PC)")
arm = fin[fin.commercial & (fin.last_sale_price > 10_000)]   # drop nominal transfers
arm = arm.assign(price_per_sqft=arm.last_sale_price / arm.structure_sqft)

print(f"commercial-zoned properties: {int(fin.commercial.sum()):,}; "
      f"with an arm's-length sale on record: {len(arm):,}\n")
print("last sale price (commercial, > $10k):")
print(arm.last_sale_price.describe(percentiles=[.25,.5,.75]).round(0).to_string(), "\n")
print("price per structure sqft:")
ppsf = arm.price_per_sqft[(arm.structure_sqft > 0)]
print(ppsf.describe(percentiles=[.25,.5,.75]).round(0).to_string(), "\n")
assessed = arm[arm.assessed_value > 0]
print(f"assessed value vs last sale, {len(assessed):,} rows with an assessment on file "
      "(assessed is administrative, not a market price):")
print((assessed.assessed_value / assessed.last_sale_price).describe(percentiles=[.25,.5,.75]).round(2).to_string())
print("\nnote: avm_estimate is empty in this export; fair_market_rent_2br is a residential ZIP figure, "
      "useful only as an order-of-magnitude anchor.")

# %% [markdown]
# ### 5b. The baseline: what was known on two days in July 2026
#
# `baseline_snapshots.csv` freezes each property on a capture date across 29 fields, including
# `incident_count` and `registered_ip_count`, the documentation depth at that moment. A lease
# that credits a tenant for improving a building needs a before line; this is it.
#

# %%
print(base.captured_on.value_counts().sort_index(), "\n")
snap = base.sort_values("captured_on").drop_duplicates("property_id", keep="last")
print("fields frozen per property:", len(base.columns) - 3)
print(snap[["property_id","captured_on","assessed_value","last_sale_price","vacancy_indicator",
            "incident_count","registered_ip_count"]].head(8).to_string(index=False))


# %% [markdown]
# ### 5c. A first lease-to-own calculator
#
# The crudest possible version of the mechanism, with every assumption in the arguments.
# A tenant pays rent; a share of it accrues as equity credit; when the credits reach the down
# payment the option becomes exercisable and the tenant finances the rest. This is a toy for
# seeing which levers matter, not an appraisal or an offer. The eleven real cases in
# `docs/worker-owned-exits.md` say what the financing actually looked like.
#

# %%
def lease_to_own(price, rent_month, credit_share=0.25, ltv=0.75, rate=0.07, term_years=25):
    """Years of rent until equity credits cover the down payment, and what the mortgage
    costs per month once the option is exercised."""
    down = price * (1 - ltv)
    credit_year = rent_month * 12 * credit_share
    years_to_option = down / credit_year
    r = rate / 12; n = term_years * 12
    mortgage_month = price * ltv * r / (1 - (1 + r) ** -n)
    return dict(price=price, rent_month=rent_month, down_payment=round(down),
                years_to_option=round(years_to_option, 1),
                mortgage_month=round(mortgage_month),
                rent_vs_mortgage=round(mortgage_month / rent_month, 2))

example = arm.sort_values("last_sale_date", ascending=False).iloc[0]
price = float(example.last_sale_price)
print(f"example: {example.address}  last sold {example.last_sale_date} for ${price:,.0f}\n")
rows = [lease_to_own(price, rent) for rent in (1500, 2500, 3500, 5000)]
print(pd.DataFrame(rows).to_string(index=False))
print("\nrent_vs_mortgage > 1 means the building costs the tenant more to own than to rent at that price.")

# %% [markdown]
# ## 6. Your starting line
#
# What exists: the evidence layer, the people–place–event links, the parcel linkage, program
# matches, the per-property market and eligibility fields, the sale and assessment fields, and
# the July 2026 baseline.
#
# What the two ideas need that is not here yet:
#
# 1. **A use-history timeline per property**, extracted from the curated layer (Idea 1). Section 4b lists where to start.
# 2. **Comparable operating examples** for each candidate use, from outside the export (Idea 1).
# 3. **Tenant financials and deal terms** from the sponsor under NDA (Idea 2). Section 5c shows the shape of the model they plug into.
#
# One caution to hold from day one: **archival abundance is not significance.** Never treat
# sparse documentation as "no history."
#

# %%
start = (idea1.merge(fin[["id","last_sale_price","last_sale_date","assessed_value","commercial"]],
                     left_on="property_id", right_on="id", how="left").drop(columns="id")
              .merge(cur.groupby("property_id").size().rename("curated_incidents"),
                     left_on="property_id", right_index=True, how="left")
              .fillna({"curated_incidents":0}))
cols = ["property_id","address","block_side_id","zoning_code","commercial","year_built","structure_sqft",
        "vacancy_indicator","has_active_business","curated_incidents","distinct_businesses",
        "use_records","first_use","last_use","last_sale_price","last_sale_date","assessed_value"]
start = start[cols].sort_values("curated_incidents", ascending=False)
print("Starter table, one row per property, for both ideas:")
print(start.head(10).to_string(index=False))
print(f"\nrows: {len(start):,} | commercial: {int(start.commercial.sum()):,} | "
      f"with a use history: {int((start.distinct_businesses > 0).sum()):,} | "
      f"with a sale price: {start.last_sale_price.notna().sum():,}")
# start.to_csv("starter_table.csv", index=False)   # uncomment to keep it
