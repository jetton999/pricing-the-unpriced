# Piece 1: Scaffold, Loaders, Audit, Protocol — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `provenance` package with typed loaders, the frozen `protocol/v1.yaml`, and a `prov audit` command that writes `data/derived/audit.json` and `docs/data_readiness.md` for both the synthetic fixture and the real export.

**Architecture:** A `src/provenance/` package where `io.py` is the only module that reads CSVs, `protocol.py` is the only module that interprets the YAML, `audit.py` computes a nested dict of readiness numbers, `audit_report.py` renders that dict to markdown, and `cli.py` exposes it all as `prov`. Tests run against a checked-in synthetic corpus under `tests/fixtures/data/`; one test module runs against the real CSVs when present.

**Tech Stack:** Python ≥ 3.12, `uv`, pandas 3, pyarrow, PyYAML, Typer, pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-piece1-audit-protocol-design.md` (parent roadmap: `docs/superpowers/specs/2026-09-01-provenance-engine-roadmap-design.md`)

## Global Constraints

- Python `>=3.12`; environment managed by `uv`; run everything through `.venv/bin/...` or `uv run`.
- Dependencies for this piece are exactly `pandas`, `pyarrow`, `pyyaml`, `typer`; dev group adds `pytest` plus the notebook's `jupyter`, `matplotlib`, `networkx` so `START_HERE.ipynb` keeps working in the same venv.
- Outcome columns (`last_sale_price`, `last_sale_date`, `assessed_value`, `avm_estimate`, `sale_count`, `market_median_sale_price`, `hpi_value`, `hpi_yoy_change`, `hmda_median_value`) are read only by `audit.py` and only to count coverage. Nothing joins them to claims.
- Every datetime column is parsed with `pd.to_datetime(col, errors="coerce", utc=True, format="mixed")`. Calendar dates are taken as the UTC date. (The export writes UTC midnight in local offset, e.g. `2026-02-09 19:00:00 -0500` means 2026-02-10.)
- `prov audit` must fail with `ProtocolError` if any `source` or `category` in the data is missing from the protocol.
- All commits on branch `capstone-engine`. Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Never modify the sponsor's CSVs, `README.md`, `START_HERE.ipynb`, or `verify_claims.py`.

## File Structure

| Path | Responsibility |
|---|---|
| `pyproject.toml` | package metadata, deps, `prov` script, pytest config |
| `src/provenance/__init__.py` | version string only |
| `src/provenance/errors.py` | `SchemaError`, `ProtocolError` |
| `src/provenance/io.py` | CSV loaders, required-column lists, `OUTCOME_COLUMNS`, `normalize_address` |
| `src/provenance/protocol.py` | `Protocol` class, `load_protocol`, hash |
| `src/provenance/audit.py` | `run_audit(data_dir, protocol) -> dict`, `write_audit_json` |
| `src/provenance/audit_report.py` | `render_report(result) -> str` |
| `src/provenance/cli.py` | Typer app: `audit`, `protocol-hash`, `all` |
| `protocol/v1.yaml` | the frozen protocol |
| `tests/conftest.py` | `fixture_dir`, `protocol` fixtures |
| `tests/fixtures/make_fixture.py` | deterministic generator for `tests/fixtures/data/*.csv` |
| `tests/test_io.py`, `test_protocol.py`, `test_audit.py`, `test_cli.py`, `test_real_data.py` | tests |
| `docs/data_readiness.md` | generated report, committed |

---

### Task 1: Package scaffold and CLI skeleton

**Files:**
- Create: `pyproject.toml`, `src/provenance/__init__.py`, `src/provenance/errors.py`, `src/provenance/cli.py`, `tests/__init__.py`, `tests/test_cli.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `provenance.cli.app` (Typer app); `provenance.errors.SchemaError(table: str, missing: list[str])`; `provenance.errors.ProtocolError(msg)`.

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "provenance"
version = "0.1.0"
description = "Provenance engine for the Pricing the Unpriced capstone"
requires-python = ">=3.12"
dependencies = [
  "pandas>=3.0",
  "pyarrow>=15",
  "pyyaml>=6",
  "typer>=0.12",
]

[project.scripts]
prov = "provenance.cli:app"

[dependency-groups]
dev = ["pytest>=8", "jupyter", "matplotlib", "networkx"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/provenance"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Append to .gitignore**

```
data/derived/
*.egg-info/
.pytest_cache/
uv.lock.bak
```

- [ ] **Step 3: Write the package files**

`src/provenance/__init__.py`:
```python
__version__ = "0.1.0"
```

`src/provenance/errors.py`:
```python
class SchemaError(Exception):
    """A sponsor CSV is missing columns the pipeline requires."""

    def __init__(self, table: str, missing: list[str]):
        self.table = table
        self.missing = list(missing)
        super().__init__(f"{table}.csv is missing required columns: {', '.join(self.missing)}")


class ProtocolError(Exception):
    """The protocol file is invalid, or the data contains values the protocol does not cover."""
```

`src/provenance/cli.py`:
```python
import typer

from provenance import __version__

app = typer.Typer(help="Provenance engine pipeline for Pricing the Unpriced.", no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)
```

`tests/__init__.py`: empty file.

- [ ] **Step 4: Write the failing CLI test**

`tests/test_cli.py`:
```python
from typer.testing import CliRunner

from provenance.cli import app

runner = CliRunner()


def test_version_command_prints_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"
```

- [ ] **Step 5: Install and run the test**

Run: `uv sync` then `.venv/bin/pytest tests/test_cli.py -v`
Expected: PASS. (`uv sync` installs the package in editable mode plus the dev group into the existing `.venv`.) Also confirm the notebook deps survived: `.venv/bin/python -c "import notebook, networkx"` prints nothing.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore src tests
git commit -m "Scaffold provenance package and prov CLI

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Synthetic fixture corpus

**Files:**
- Create: `tests/fixtures/make_fixture.py`, `tests/fixtures/data/*.csv` (generated, committed), `tests/conftest.py`, `tests/test_fixture.py`

**Interfaces:**
- Produces: `tests/fixtures/data/` containing the ten CSVs with the same headers as the real export; `conftest.fixture_dir` (Path) fixture.
- The fixture encodes these cases by property id: 1 administrative-only; 2 deeply documented (six curated sources incl. nrhp); 3 ungraded curated claim; 4 contested claim; 5 sensitivity-flagged claim; 2 and 6 share near-duplicate subjects "John A. Smith" / "Smith, John A"; 7 has a $1 sale; 8 is city-owned with a real sale; 9 sold 2019-06-01 and carries a `whitepaper` claim with `occurred_at` 1920 (leakage case); 10 sold 2025-03-01; 11 has no parcel match; 12–20 filler, of which 12–16 have arm's-length sales and 17–20 have no sale. Block side 1 holds ids 1–10, block side 2 holds 11–20. One 1735 claim on property 2 exercises pre-1677 parsing.

- [ ] **Step 1: Write the generator**

`tests/fixtures/make_fixture.py`:
```python
"""Deterministic synthetic corpus with the real export's headers. Run: python tests/fixtures/make_fixture.py"""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "data"

PROPERTY_COLUMNS = [
    "id", "address", "block_side_id", "created_at", "latitude", "longitude", "owner_name", "owner_type",
    "updated_at", "blocklot", "assessed_value", "vacancy_indicator", "year_built", "zoning_code",
    "last_sale_price", "last_sale_date", "lot_polygon", "building_polygons", "city_owned", "alias",
    "has_active_business", "opportunity_zone", "flood_zone", "historic_district", "enterprise_zone",
    "incidents_12mo_count", "violations_12mo_count", "census_tract", "environmental_flag",
    "fair_market_rent_2br", "median_household_income", "vacant_notice_status", "active_permit_count",
    "receivership_status", "roof_damage_risk", "tax_certificate_active", "market_typology",
    "crimes_12mo_count", "cdbg_eligible", "inspire_eligible", "arts_district", "healthy_neighborhood",
    "lincs_corridor", "main_street_district", "niif_area", "sustainable_community", "food_desert",
    "public_investment_total", "walkability_index", "transit_distance_m", "jobs_transit_45min",
    "lihtc_nearby_count", "hud_reo", "qualified_census_tract", "difficult_development_area",
    "cdbg_investment_total", "hmda_loan_count", "hmda_median_value", "hmda_denial_rate", "hpi_value",
    "hpi_yoy_change", "ground_rent", "dwelling_units", "structure_sqft", "building_condition",
    "building_quality", "num_stories", "has_basement", "has_central_ac", "market_median_sale_price",
    "market_median_dom", "market_inventory", "walk_score", "transit_score", "bike_score",
    "nearby_restaurants", "nearby_shops", "nearby_amenities_total", "irs_agi_per_return",
    "irs_homeowner_pct", "avm_estimate", "sale_count", "zip_code", "block_plat_url",
    "tax_certificate_status", "tax_certificate_sold_on", "receivership_filed_on",
]

NOW = "2026-04-07 03:10:20 -0400"


def polygon(i: int) -> str:
    x, y = -76.6100 + i * 0.0002, 39.3200 + i * 0.0001
    return json.dumps({"rings": [[[x, y], [x + 0.0003, y], [x + 0.0003, y + 0.0002], [x, y + 0.0002], [x, y]]]})


def properties() -> pd.DataFrame:
    rows = []
    sales = {  # id -> (price, date)
        2: (250000, "2021-08-15"), 3: (120000, "2022-01-10"), 4: (90000, "2020-05-05"),
        5: (180000, "2023-09-30"), 6: (60000, "2018-03-03"), 7: (1, "2016-07-07"),
        8: (75000, "2022-11-11"), 9: (140000, "2019-06-01"), 10: (300000, "2025-03-01"),
        12: (50000, "2015-02-02"), 13: (210000, "2024-04-04"), 14: (99000, "2021-01-01"),
        15: (130000, "2023-06-06"), 16: (45000, "2017-08-08"),
    }
    for i in range(1, 21):
        price, date = sales.get(i, (None, None))
        row = {c: None for c in PROPERTY_COLUMNS}
        row.update({
            "id": i,
            "address": f"{2600 + i} Greenmount Ave, Baltimore, MD",
            "block_side_id": 1 if i <= 10 else 2,
            "created_at": NOW, "updated_at": NOW,
            "latitude": 39.3200 + i * 0.0001, "longitude": -76.6100 + i * 0.0002,
            "owner_name": "CITY OF BALTIMORE" if i == 8 else f"OWNER {i} LLC",
            "owner_type": "city" if i == 8 else ("unknown" if i % 3 == 0 else None),
            "blocklot": f"3900 {i:03d}",
            "assessed_value": 100000 + i * 1000 if i != 17 else None,
            "vacancy_indicator": i in (1, 12, 17),
            "year_built": 1900 + i if i != 18 else None,
            "zoning_code": "C-1" if i % 2 else "R-8",
            "last_sale_price": price, "last_sale_date": date,
            "lot_polygon": polygon(i) if i != 19 else None,
            "building_polygons": None,
            "city_owned": i == 8,
            "census_tract": "090400" if i <= 10 else "090300",
            "market_typology": "Middle" if i % 2 else "Stressed",
            "dwelling_units": 1 if i % 4 else None,
            "structure_sqft": 1500 + i * 10 if i != 20 else None,
            "avm_estimate": 110000 + i * 1000,
            "sale_count": 1 if price else 0,
            "market_median_sale_price": 150000,
            "hpi_value": 200.0, "hpi_yoy_change": 0.03, "hmda_median_value": 175000,
            "zip_code": "21218",
        })
        rows.append(row)
    return pd.DataFrame(rows, columns=PROPERTY_COLUMNS)


def incidents_and_subjects():
    inc, isub, subj = [], [], []
    iid = [0]

    def claim(pid, source, category, occurred, status="verified", precision="exact", sensitivity=None,
              rights=None, data=None, summary="claim"):
        iid[0] += 1
        inc.append({
            "id": iid[0], "property_id": pid, "source": source, "source_id": f"{source}-{iid[0]}",
            "category": category, "occurred_at": f"{occurred} 00:00:00 -0500", "summary": summary,
            "data": json.dumps(data or {}), "created_at": NOW, "evidence_status": status,
            "occurred_at_end": None, "date_precision": precision, "sensitivity": sensitivity, "rights": rights,
        })
        return iid[0]

    def subject(sid, name, stype):
        subj.append({"id": sid, "name": name, "subject_type": stype, "slug": name.lower().replace(" ", "-"),
                     "data": "{}", "created_at": NOW, "updated_at": NOW})

    def link(cid, sid, rel):
        isub.append({"id": len(isub) + 1, "property_incident_id": cid, "subject_id": sid, "relationship": rel,
                     "data": "{}", "created_at": NOW, "updated_at": NOW})

    # 1: administrative only
    for k in range(3):
        claim(1, "baltimore:311", "complaint", f"2024-0{k + 1}-01", status=None, precision=None)
    claim(1, "baltimore:permits", "permit", "2023-05-05", status=None, precision=None)
    # 2: deeply documented, six curated sources
    subject(1, "John A. Smith", "person")
    subject(2, "Smith, John A", "person")
    subject(3, "Waverly Grocers Inc", "business")
    c = claim(2, "newspapers_com", "news", "1939-10-01", summary="block anchors a championship season")
    link(c, 1, "mentioned_in")
    c = claim(2, "mdlandrec", "sale", "1912-04-01"); link(c, 1, "purchased")
    c = claim(2, "sanborn", "map", "1914-01-01")
    c = claim(2, "polk", "directory", "1920-01-01"); link(c, 3, "operated_at")
    c = claim(2, "whitepaper", "civic", "1950-01-01", data={"publication_date": "2026-05-15"})
    c = claim(2, "nrhp", "designation", "2013-12-31")
    c = claim(2, "mdlandrec", "land", "1735-06-01", precision="year", summary="colonial land grant")
    claim(2, "baltimore:311", "complaint", "2025-01-01", status=None, precision=None)
    # 3: ungraded curated claim
    claim(3, "newspapers_com", "advertisement", "1925-03-03", status=None, precision="year")
    # 4: contested
    claim(4, "web_research", "news", "1960-01-01", status="contested", precision="circa")
    # 5: sensitivity flagged
    claim(5, "newspapers_com", "obituary", "1948-02-02", sensitivity="trauma", rights="public")
    # 6: shares near-duplicate subject with 2
    c = claim(6, "mdlandrec", "sale", "1930-05-05"); link(c, 2, "sold")
    # 9: leakage case — whitepaper about 1920 attached to a property sold 2019
    claim(9, "whitepaper", "commerce", "1920-06-01", status="probable")
    # 10: recent sale with an interment record
    subject(4, "Mary Jones", "person")
    c = claim(10, "stjohns_interments", "interment", "1890-09-09", status="possible"); link(c, 4, "interred_at")
    # 12–16 filler admin rows
    for pid in range(12, 17):
        claim(pid, "baltimore:permits", "permit", "2022-02-02", status=None, precision=None)
    # 13 gets one curated claim so block side 2 has some coverage
    claim(13, "hopkins_atlas_1876", "map", "1876-01-01")
    return pd.DataFrame(inc), pd.DataFrame(isub), pd.DataFrame(subj)


def incident_links() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": 1, "property_incident_id": 5, "related_incident_id": 6, "link_type": "supports", "note": None,
         "created_at": NOW, "updated_at": NOW},
        {"id": 2, "property_incident_id": 9, "related_incident_id": 13, "link_type": "contradicts",
         "note": "dates disagree", "created_at": NOW, "updated_at": NOW},
    ])


def registered_ips() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": 1, "address_of_record": "2602 Greenmount Ave", "created_at": NOW, "data": "{}",
         "filing_date": "1993-01-01", "grant_date": "1994-01-01", "ip_type": "trademark",
         "match_confidence": "high", "number": "TM1", "owner_name": "Waverly Grocers Inc", "property_id": 2,
         "source": "uspto", "status": "live", "title": "WAVERLY GROCERS", "updated_at": NOW},
        {"id": 2, "address_of_record": "2610 Greenmount Ave", "created_at": NOW, "data": "{}",
         "filing_date": "2001-01-01", "grant_date": None, "ip_type": "patent", "match_confidence": "medium",
         "number": "P1", "owner_name": "OWNER 10 LLC", "property_id": 10, "source": "uspto", "status": "dead",
         "title": "Bottle cap", "updated_at": NOW},
    ])


def parcels() -> pd.DataFrame:
    rows = []
    n = 0
    for i in range(1, 21):
        if i == 11:
            continue  # no parcel match for property 11
        n += 1
        rows.append({"id": n, "source": "sdat", "source_id": f"S{n}", "blocklot": f"3900 {i:03d}",
                     "address": f"{2600 + i} GREENMOUNT AVE", "normalized_address": f"{2600 + i} GREENMOUNT AVE",
                     "sqft": 1500, "land_use": "C", "owner": f"OWNER {i} LLC",
                     "matched_property_id": i if i <= 5 else None, "created_at": NOW, "updated_at": NOW,
                     "lot_sqft": 2000 + i})
    for j in range(5):
        n += 1
        rows.append({"id": n, "source": "sdat", "source_id": f"S{n}", "blocklot": f"3901 {j:03d}",
                     "address": f"{2001 + j} W NORTH AVE", "normalized_address": f"{2001 + j} W NORTH AVE",
                     "sqft": 1200, "land_use": "R", "owner": "SOMEONE", "matched_property_id": None,
                     "created_at": NOW, "updated_at": NOW, "lot_sqft": 1800})
    return pd.DataFrame(rows)


def programs() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": k, "property_id": pid, "program_key": key, "program_name": name, "category": "facade",
         "amount_cap": "$10,000", "summary": "s", "matched_reason": "in corridor", "created_at": NOW, "updated_at": NOW}
        for k, (pid, key, name) in enumerate([(2, "facade", "Facade Grant"), (9, "facade", "Facade Grant"),
                                              (12, "vacants", "Vacants to Value")], start=1)
    ])


def neighborhoods() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": 1, "bounds": json.dumps({"rings": []}), "created_at": NOW, "name": "Waverly", "updated_at": NOW},
        {"id": 2, "bounds": None, "created_at": NOW, "name": "Harwood", "updated_at": NOW},
    ])


def baselines(props: pd.DataFrame) -> pd.DataFrame:
    cols = ["property_id", "captured_on", "active_permit_count", "assessed_value", "avm_estimate", "building_condition",
            "captured_at", "cdbg_investment_total", "city_owned", "dwelling_units", "fair_market_rent_2br", "ground_rent",
            "has_active_business", "hmda_denial_rate", "hmda_loan_count", "hmda_median_value", "incident_count",
            "last_sale_date", "last_sale_price", "market_median_sale_price", "market_typology", "owner_name",
            "owner_type", "public_investment_total", "receivership_status", "registered_ip_count", "sale_count",
            "tax_certificate_active", "vacancy_indicator", "vacant_notice_status", "violations_12mo_count"]
    rows = []
    for pid in (2, 9, 10):
        p = props.set_index("id").loc[pid]
        row = {c: None for c in cols}
        row.update({"property_id": pid, "captured_on": "2026-07-13", "captured_at": "2026-07-13 12:00:00 -0400",
                    "assessed_value": p.assessed_value, "last_sale_price": p.last_sale_price,
                    "last_sale_date": p.last_sale_date, "incident_count": 3, "registered_ip_count": 1,
                    "owner_name": p.owner_name, "market_typology": p.market_typology})
        rows.append(row)
    return pd.DataFrame(rows, columns=cols)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    props = properties()
    inc, isub, subj = incidents_and_subjects()
    tables = {
        "properties": props, "property_incidents": inc, "subjects": subj, "incident_subjects": isub,
        "incident_links": incident_links(), "registered_ips": registered_ips(), "property_parcels": parcels(),
        "grant_program_matches": programs(), "neighborhoods": neighborhoods(), "baseline_snapshots": baselines(props),
    }
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write conftest and the fixture test**

`tests/conftest.py`:
```python
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "data"
REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = REPO_ROOT / "protocol" / "v1.yaml"


@pytest.fixture
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
```

`tests/test_fixture.py`:
```python
import pandas as pd

from tests.fixtures.make_fixture import main

TABLES = ["properties", "property_incidents", "subjects", "incident_subjects", "incident_links",
          "registered_ips", "property_parcels", "grant_program_matches", "neighborhoods", "baseline_snapshots"]


def test_generator_is_deterministic_and_complete(fixture_dir, tmp_path, monkeypatch):
    import tests.fixtures.make_fixture as mf
    monkeypatch.setattr(mf, "OUT", tmp_path)
    main()
    for t in TABLES:
        fresh = pd.read_csv(tmp_path / f"{t}.csv")
        committed = pd.read_csv(fixture_dir / f"{t}.csv")
        pd.testing.assert_frame_equal(fresh, committed)


def test_fixture_encodes_required_cases(fixture_dir):
    props = pd.read_csv(fixture_dir / "properties.csv")
    inc = pd.read_csv(fixture_dir / "property_incidents.csv")
    assert len(props) == 20
    assert props.set_index("id").loc[7, "last_sale_price"] == 1
    assert props.set_index("id").loc[8, "owner_type"] == "city"
    assert inc[inc.property_id == 1].source.str.startswith("baltimore:").all()
    assert (inc[inc.property_id == 9].source == "whitepaper").any()
    assert inc[inc.property_id == 5].sensitivity.notna().any()
    assert inc.occurred_at.str.startswith("1735").any()
```

- [ ] **Step 3: Generate the fixture and run the tests**

Run: `.venv/bin/python tests/fixtures/make_fixture.py && .venv/bin/pytest tests/test_fixture.py -v`
Expected: both PASS. `ls tests/fixtures/data` shows ten CSVs.

- [ ] **Step 4: Commit**

```bash
git add tests
git commit -m "Add deterministic synthetic fixture corpus

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Loaders (`io.py`)

**Files:**
- Create: `src/provenance/io.py`, `tests/test_io.py`

**Interfaces:**
- Produces:
  - `OUTCOME_COLUMNS: tuple[str, ...]`
  - `TABLES: tuple[str, ...]` (the ten table names)
  - `load_properties(data_dir: Path, *, outcome_blind: bool) -> pd.DataFrame`
  - `load_incidents(data_dir) -> pd.DataFrame` with `occurred_at`, `occurred_at_end`, `created_at` as tz-aware datetimes and `data` as dicts
  - `load_subjects`, `load_incident_subjects`, `load_incident_links`, `load_registered_ips`, `load_parcels`, `load_programs`, `load_neighborhoods`, `load_baselines` (each `(data_dir) -> pd.DataFrame`)
  - `normalize_address(addr: str | None) -> str`
  - `read_row_counts(data_dir) -> dict[str, int] | None`

- [ ] **Step 1: Write the failing tests**

`tests/test_io.py`:
```python
import datetime as dt
import shutil

import pandas as pd
import pytest

from provenance import io
from provenance.errors import SchemaError


def test_blind_loader_drops_every_outcome_column(fixture_dir):
    df = io.load_properties(fixture_dir, outcome_blind=True)
    assert not set(io.OUTCOME_COLUMNS) & set(df.columns)
    assert "year_built" in df.columns


def test_unblinded_loader_keeps_outcomes_and_parses_types(fixture_dir):
    df = io.load_properties(fixture_dir, outcome_blind=False)
    assert set(io.OUTCOME_COLUMNS) <= set(df.columns)
    assert str(df["last_sale_date"].dtype).startswith("datetime64")
    assert isinstance(df.set_index("id").loc[1, "lot_polygon"], dict)
    assert pd.isna(df.set_index("id").loc[19, "lot_polygon"])
    assert df["city_owned"].dtype == bool


def test_incidents_parse_dates_json_and_survive_1735(fixture_dir):
    inc = io.load_incidents(fixture_dir)
    assert inc["occurred_at"].dt.tz is not None
    row = inc[inc.summary == "colonial land grant"].iloc[0]
    assert row.occurred_at.date() == dt.date(1735, 6, 1)
    wp = inc[(inc.property_id == 2) & (inc.source == "whitepaper")].iloc[0]
    assert wp.data == {"publication_date": "2026-05-15"}


def test_every_table_loads(fixture_dir):
    for name in io.TABLES:
        df = io.LOADERS[name](fixture_dir)
        assert len(df) > 0, name


def test_schema_error_names_missing_columns(fixture_dir, tmp_path):
    for f in fixture_dir.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    pd.read_csv(tmp_path / "subjects.csv").drop(columns=["subject_type"]).to_csv(tmp_path / "subjects.csv", index=False)
    with pytest.raises(SchemaError) as e:
        io.load_subjects(tmp_path)
    assert e.value.table == "subjects"
    assert e.value.missing == ["subject_type"]


@pytest.mark.parametrize("raw,expected", [
    ("2602 Greenmount Ave, Baltimore, MD", "2602 GREENMOUNT AVE"),
    ("2602 GREENMOUNT AVENUE", "2602 GREENMOUNT AVE"),
    ("  401 E. 30th Street ", "401 E 30TH ST"),
    ("2045 W NORTH AVE", "2045 W NORTH AVE"),
    (None, ""),
])
def test_normalize_address(raw, expected):
    assert io.normalize_address(raw) == expected


def test_read_row_counts_missing_returns_none(fixture_dir):
    assert io.read_row_counts(fixture_dir) is None


def test_read_row_counts_parses_file(tmp_path):
    (tmp_path / "row_counts.txt").write_text("properties: 1874\nsubjects: 3103\n")
    assert io.read_row_counts(tmp_path) == {"properties": 1874, "subjects": 3103}
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_io.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'provenance.io'`.

- [ ] **Step 3: Write io.py**

`src/provenance/io.py`:
```python
"""The only module that reads the sponsor's CSVs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

import pandas as pd

from provenance.errors import SchemaError

TABLES = (
    "properties", "property_incidents", "subjects", "incident_subjects", "incident_links",
    "registered_ips", "property_parcels", "grant_program_matches", "neighborhoods", "baseline_snapshots",
)

OUTCOME_COLUMNS = (
    "last_sale_price", "last_sale_date", "assessed_value", "avm_estimate", "sale_count",
    "market_median_sale_price", "hpi_value", "hpi_yoy_change", "hmda_median_value",
)

REQUIRED: dict[str, list[str]] = {
    "properties": [
        "id", "address", "block_side_id", "latitude", "longitude", "owner_name", "owner_type", "blocklot",
        "vacancy_indicator", "year_built", "zoning_code", "lot_polygon", "building_polygons", "city_owned",
        "historic_district", "census_tract", "market_typology", "dwelling_units", "structure_sqft", *OUTCOME_COLUMNS,
    ],
    "property_incidents": [
        "id", "property_id", "source", "source_id", "category", "occurred_at", "summary", "data", "created_at",
        "evidence_status", "occurred_at_end", "date_precision", "sensitivity", "rights",
    ],
    "subjects": ["id", "name", "subject_type", "slug", "data", "created_at"],
    "incident_subjects": ["id", "property_incident_id", "subject_id", "relationship", "data"],
    "incident_links": ["id", "property_incident_id", "related_incident_id", "link_type", "note"],
    "registered_ips": ["id", "address_of_record", "data", "filing_date", "grant_date", "ip_type", "match_confidence",
                       "number", "owner_name", "property_id", "source", "status", "title"],
    "property_parcels": ["id", "source", "source_id", "blocklot", "address", "normalized_address", "sqft", "land_use",
                         "owner", "matched_property_id", "lot_sqft"],
    "grant_program_matches": ["id", "property_id", "program_key", "program_name", "category", "amount_cap", "summary",
                              "matched_reason"],
    "neighborhoods": ["id", "bounds", "name"],
    "baseline_snapshots": ["property_id", "captured_on", "captured_at", "assessed_value", "last_sale_price",
                           "last_sale_date", "incident_count", "registered_ip_count"],
}

DATETIME_COLUMNS: dict[str, list[str]] = {
    "properties": ["last_sale_date", "created_at", "updated_at"],
    "property_incidents": ["occurred_at", "occurred_at_end", "created_at"],
    "subjects": ["created_at", "updated_at"],
    "incident_subjects": ["created_at", "updated_at"],
    "incident_links": ["created_at", "updated_at"],
    "registered_ips": ["filing_date", "grant_date", "created_at", "updated_at"],
    "property_parcels": ["created_at", "updated_at"],
    "grant_program_matches": ["created_at", "updated_at"],
    "neighborhoods": ["created_at", "updated_at"],
    "baseline_snapshots": ["captured_on", "captured_at", "last_sale_date"],
}

JSON_COLUMNS: dict[str, list[str]] = {
    "properties": ["lot_polygon", "building_polygons"],
    "property_incidents": ["data"],
    "subjects": ["data"],
    "incident_subjects": ["data"],
    "registered_ips": ["data"],
    "neighborhoods": ["bounds"],
}

BOOL_COLUMNS: dict[str, list[str]] = {
    "properties": ["vacancy_indicator", "city_owned"],
}


def _parse_json(value):
    if isinstance(value, str) and value.strip():
        return json.loads(value)
    return pd.NA


def _to_bool(series: pd.Series) -> pd.Series:
    return series.map(lambda v: str(v).strip().lower() in ("true", "t", "1", "yes")).astype(bool)


def _load(table: str, data_dir: Path) -> pd.DataFrame:
    path = Path(data_dir) / f"{table}.csv"
    df = pd.read_csv(path, low_memory=False)
    missing = [c for c in REQUIRED[table] if c not in df.columns]
    if missing:
        raise SchemaError(table, missing)
    for col in DATETIME_COLUMNS.get(table, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True, format="mixed")
    for col in JSON_COLUMNS.get(table, []):
        df[col] = df[col].map(_parse_json)
    for col in BOOL_COLUMNS.get(table, []):
        df[col] = _to_bool(df[col])
    return df


def load_properties(data_dir: Path, *, outcome_blind: bool) -> pd.DataFrame:
    df = _load("properties", data_dir)
    if outcome_blind:
        df = df.drop(columns=list(OUTCOME_COLUMNS))
    return df


def load_incidents(data_dir: Path) -> pd.DataFrame:
    return _load("property_incidents", data_dir)


def load_subjects(data_dir: Path) -> pd.DataFrame:
    return _load("subjects", data_dir)


def load_incident_subjects(data_dir: Path) -> pd.DataFrame:
    return _load("incident_subjects", data_dir)


def load_incident_links(data_dir: Path) -> pd.DataFrame:
    return _load("incident_links", data_dir)


def load_registered_ips(data_dir: Path) -> pd.DataFrame:
    return _load("registered_ips", data_dir)


def load_parcels(data_dir: Path) -> pd.DataFrame:
    return _load("property_parcels", data_dir)


def load_programs(data_dir: Path) -> pd.DataFrame:
    return _load("grant_program_matches", data_dir)


def load_neighborhoods(data_dir: Path) -> pd.DataFrame:
    return _load("neighborhoods", data_dir)


def load_baselines(data_dir: Path) -> pd.DataFrame:
    return _load("baseline_snapshots", data_dir)


LOADERS: dict[str, Callable[[Path], pd.DataFrame]] = {
    "properties": lambda d: load_properties(d, outcome_blind=True),
    "property_incidents": load_incidents,
    "subjects": load_subjects,
    "incident_subjects": load_incident_subjects,
    "incident_links": load_incident_links,
    "registered_ips": load_registered_ips,
    "property_parcels": load_parcels,
    "grant_program_matches": load_programs,
    "neighborhoods": load_neighborhoods,
    "baseline_snapshots": load_baselines,
}

_SUFFIXES = {
    "AVENUE": "AVE", "AV": "AVE", "STREET": "ST", "ROAD": "RD", "BOULEVARD": "BLVD", "PLACE": "PL",
    "LANE": "LN", "DRIVE": "DR", "COURT": "CT", "TERRACE": "TER", "PARKWAY": "PKWY",
}


def normalize_address(addr: str | None) -> str:
    """Upper-case house number + street, suffix abbreviated, city/state dropped, punctuation removed."""
    if not isinstance(addr, str):
        return ""
    head = addr.split(",")[0].upper()
    head = re.sub(r"[^\w\s]", " ", head)
    return " ".join(_SUFFIXES.get(tok, tok) for tok in head.split())


def read_row_counts(data_dir: Path) -> dict[str, int] | None:
    path = Path(data_dir) / "row_counts.txt"
    if not path.exists():
        return None
    out: dict[str, int] = {}
    for line in path.read_text().splitlines():
        if ":" in line:
            name, n = line.split(":", 1)
            out[name.strip()] = int(n.strip())
    return out
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/pytest tests/test_io.py -v`
Expected: all PASS. If `test_unblinded_loader_keeps_outcomes_and_parses_types` fails on the `pd.isna(...)` of a missing polygon, confirm `_parse_json` returns `pd.NA` for the empty cell (pandas reads an empty CSV cell as `NaN`, which is not a `str`, so the branch returns `pd.NA`).

- [ ] **Step 5: Commit**

```bash
git add src/provenance/io.py tests/test_io.py
git commit -m "Add typed CSV loaders with outcome-blind mode and address normalization

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Protocol file and `protocol.py`

**Files:**
- Create: `protocol/v1.yaml`, `src/provenance/protocol.py`, `tests/test_protocol.py`

**Interfaces:**
- Produces:
  - `load_protocol(path: Path) -> Protocol`
  - `Protocol.version: int`, `Protocol.hash: str` (sha256 hex), `Protocol.raw: dict`
  - `Protocol.layer_of(source: str) -> str` (`"administrative"` | `"curated"`)
  - `Protocol.evidence_weight(status: str | None) -> float`
  - `Protocol.relationship_weight(rel: str) -> float`
  - `Protocol.salience(category: str) -> float` (raises `ProtocolError` on unknown)
  - `Protocol.knowability_rule(source: str) -> str` (`"at_occurrence"` | `"at_publication"` | `"fixed"`; raises on unknown)
  - `Protocol.knowable_from(source: str, occurred_at, data: dict | None) -> datetime.date | None`
  - `Protocol.is_arms_length(price, owner_type) -> bool`
  - `Protocol.known_sources() -> set[str]`, `Protocol.known_categories() -> set[str]`
  - Convenience accessors: `Protocol.block_min_sources: int`, `Protocol.temporal_holdout_start: date`, `Protocol.validation: dict`

- [ ] **Step 1: Write protocol/v1.yaml**

Copy the YAML block from spec §5 verbatim into `protocol/v1.yaml`. It begins `version: 1` and ends with the `validation:` block whose last key is `connectivity_beyond_proximity: true`. Do not edit any value; the spec is the source of truth.

- [ ] **Step 2: Write the failing tests**

`tests/test_protocol.py`:
```python
import datetime as dt

import pytest
import yaml

from provenance import io
from provenance.errors import ProtocolError
from provenance.protocol import load_protocol
from tests.conftest import PROTOCOL_PATH


@pytest.fixture
def protocol():
    return load_protocol(PROTOCOL_PATH)


def test_hash_is_stable_across_key_order_and_whitespace(tmp_path, protocol):
    raw = yaml.safe_load(PROTOCOL_PATH.read_text())
    reordered = dict(reversed(list(raw.items())))
    p = tmp_path / "p.yaml"
    p.write_text(yaml.safe_dump(reordered, sort_keys=False, indent=4))
    assert load_protocol(p).hash == protocol.hash
    assert len(protocol.hash) == 64


def test_hash_changes_when_a_value_changes(tmp_path, protocol):
    raw = yaml.safe_load(PROTOCOL_PATH.read_text())
    raw["index"]["beta"] = 0.75
    p = tmp_path / "p.yaml"
    p.write_text(yaml.safe_dump(raw))
    assert load_protocol(p).hash != protocol.hash


def test_layer_of(protocol):
    assert protocol.layer_of("baltimore:311") == "administrative"
    assert protocol.layer_of("sdat_assessments") == "administrative"
    assert protocol.layer_of("sdat:owner") == "administrative"
    assert protocol.layer_of("newspapers_com") == "curated"
    assert protocol.layer_of("hud:cdbg") == "curated"


def test_evidence_weight(protocol):
    assert protocol.evidence_weight("verified") == 1.0
    assert protocol.evidence_weight("contested") == 0.15
    assert protocol.evidence_weight(None) == 0.5
    assert protocol.evidence_weight(float("nan")) == 0.5


def test_relationship_weight_groups_and_default(protocol):
    assert protocol.relationship_weight("owned") == 1.0
    assert protocol.relationship_weight("played_at") == 0.7
    assert protocol.relationship_weight("mentioned_in") == 0.4
    assert protocol.relationship_weight("struck_out_by_lefty_russell") == 0.5


def test_salience_known_and_unknown(protocol):
    assert protocol.salience("designation") == 1.0
    assert protocol.salience("complaint") == 0.0
    with pytest.raises(ProtocolError):
        protocol.salience("not_a_category")


def test_every_fixture_source_and_category_resolves(fixture_dir, protocol):
    inc = io.load_incidents(fixture_dir)
    for s in inc.source.unique():
        protocol.knowability_rule(s)
    for c in inc.category.unique():
        protocol.salience(c)


def test_knowability_rule_unknown_source_raises(protocol):
    with pytest.raises(ProtocolError) as e:
        protocol.knowability_rule("brand_new_feed")
    assert "brand_new_feed" in str(e.value)


def test_knowable_from_rules(protocol):
    occurred = dt.datetime(1939, 10, 1, tzinfo=dt.timezone.utc)
    assert protocol.knowable_from("newspapers_com", occurred, {}) == dt.date(1939, 10, 1)
    assert protocol.knowable_from("whitepaper", occurred, {}) == dt.date(2026, 1, 1)
    assert protocol.knowable_from("whitepaper", occurred, {"publication_date": "2026-05-15"}) == dt.date(2026, 5, 15)
    assert protocol.knowable_from("nrhp", occurred, None) == dt.date(2013, 12, 31)
    assert protocol.knowable_from("newspapers_com", None, {}) is None


def test_arms_length(protocol):
    assert protocol.is_arms_length(250000, None)
    assert protocol.is_arms_length(10000, "unknown")
    assert not protocol.is_arms_length(1, None)
    assert not protocol.is_arms_length(9999, None)
    assert not protocol.is_arms_length(75000, "city")
    assert not protocol.is_arms_length(None, None)
    assert not protocol.is_arms_length(float("nan"), None)


def test_invalid_protocol_rejected(tmp_path):
    raw = yaml.safe_load(PROTOCOL_PATH.read_text())
    raw["evidence_weights"]["verified"] = 1.5
    p = tmp_path / "p.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(ProtocolError):
        load_protocol(p)


def test_convenience_accessors(protocol):
    assert protocol.version == 1
    assert protocol.block_min_sources == 3
    assert protocol.temporal_holdout_start == dt.date(2024, 1, 1)
    assert protocol.validation["min_panel_rows"] == 300
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/pytest tests/test_protocol.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'provenance.protocol'`.

- [ ] **Step 4: Write protocol.py**

`src/provenance/protocol.py`:
```python
"""Load, validate, and hash the frozen coding protocol. The only module that interprets protocol YAML."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import pandas as pd
import yaml

from provenance.errors import ProtocolError

EVIDENCE_STATUSES = ("verified", "probable", "possible", "contested", "ungraded")
RULES = ("at_occurrence", "at_publication", "fixed")


def _is_missing(v) -> bool:
    if v is None:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _to_date(v) -> dt.date | None:
    if _is_missing(v):
        return None
    if isinstance(v, dt.datetime):
        return v.astimezone(dt.timezone.utc).date() if v.tzinfo else v.date()
    if isinstance(v, dt.date):
        return v
    parsed = pd.to_datetime(str(v), errors="coerce", utc=True)
    return None if pd.isna(parsed) else parsed.date()


def _unit(name: str, value) -> float:
    if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
        raise ProtocolError(f"{name} must be a number in [0, 1], got {value!r}")
    return float(value)


class Protocol:
    def __init__(self, raw: dict):
        self.raw = raw
        self._validate()
        canonical = json.dumps(raw, sort_keys=True, default=str, separators=(",", ":"))
        self.hash = hashlib.sha256(canonical.encode()).hexdigest()

    # ---- validation -------------------------------------------------------
    def _validate(self) -> None:
        r = self.raw
        for key in ("version", "layers", "evidence_weights", "index", "relationship_weights", "salience",
                    "knowability", "coverage", "outcome", "validation"):
            if key not in r:
                raise ProtocolError(f"protocol is missing top-level key {key!r}")
        if not isinstance(r["version"], int):
            raise ProtocolError("version must be an integer")
        for s in EVIDENCE_STATUSES:
            _unit(f"evidence_weights.{s}", r["evidence_weights"].get(s))
        for k in ("beta", "gamma"):
            v = r["index"].get(k)
            if not isinstance(v, (int, float)) or v <= 0:
                raise ProtocolError(f"index.{k} must be a positive number")
        rw = r["relationship_weights"]
        _unit("relationship_weights.default", rw.get("default"))
        for g, w in rw["groups"].items():
            _unit(f"relationship_weights.groups.{g}", w)
            if g not in rw["members"]:
                raise ProtocolError(f"relationship group {g!r} has no members list")
        for c, w in r["salience"].items():
            _unit(f"salience.{c}", w)
        kn = r["knowability"]["sources"]
        for src, cfg in kn.get("at_publication", {}).items():
            if _to_date(cfg.get("fallback_date")) is None:
                raise ProtocolError(f"knowability.at_publication.{src} needs a fallback_date")
        for src, d in kn.get("fixed", {}).items():
            if _to_date(d) is None:
                raise ProtocolError(f"knowability.fixed.{src} must be a date")
        if not isinstance(r["coverage"].get("block_min_sources"), int):
            raise ProtocolError("coverage.block_min_sources must be an integer")
        if _to_date(r["outcome"].get("temporal_holdout_start")) is None:
            raise ProtocolError("outcome.temporal_holdout_start must be a date")

    # ---- accessors ---------------------------------------------------------
    @property
    def version(self) -> int:
        return self.raw["version"]

    @property
    def block_min_sources(self) -> int:
        return self.raw["coverage"]["block_min_sources"]

    @property
    def temporal_holdout_start(self) -> dt.date:
        return _to_date(self.raw["outcome"]["temporal_holdout_start"])

    @property
    def validation(self) -> dict:
        return self.raw["validation"]

    def layer_of(self, source: str) -> str:
        layers = self.raw["layers"]
        s = str(source)
        if s in layers["administrative_exact"] or any(s.startswith(p) for p in layers["administrative_prefixes"]):
            return "administrative"
        return "curated"

    def evidence_weight(self, status) -> float:
        key = "ungraded" if _is_missing(status) else str(status)
        try:
            return float(self.raw["evidence_weights"][key])
        except KeyError:
            raise ProtocolError(f"unknown evidence_status {status!r}") from None

    def relationship_weight(self, rel: str) -> float:
        rw = self.raw["relationship_weights"]
        for group, members in rw["members"].items():
            if rel in members:
                return float(rw["groups"][group])
        return float(rw["default"])

    def salience(self, category) -> float:
        try:
            return float(self.raw["salience"][str(category)])
        except KeyError:
            raise ProtocolError(f"category {category!r} is not in the protocol salience map") from None

    def known_categories(self) -> set[str]:
        return set(self.raw["salience"])

    def _knowability_index(self) -> dict[str, str]:
        kn = self.raw["knowability"]["sources"]
        index: dict[str, str] = {}
        for s in kn.get("at_occurrence", []):
            index[str(s)] = "at_occurrence"
        for s in kn.get("at_publication", {}):
            index[str(s)] = "at_publication"
        for s in kn.get("fixed", {}):
            index[str(s)] = "fixed"
        return index

    def known_sources(self) -> set[str]:
        return set(self._knowability_index())

    def knowability_rule(self, source: str) -> str:
        try:
            return self._knowability_index()[str(source)]
        except KeyError:
            raise ProtocolError(f"source {source!r} is not in the protocol knowability map") from None

    def knowable_from(self, source: str, occurred_at, data) -> dt.date | None:
        rule = self.knowability_rule(source)
        kn = self.raw["knowability"]
        if rule == "at_occurrence":
            return _to_date(occurred_at)
        if rule == "fixed":
            return _to_date(kn["sources"]["fixed"][source])
        key = kn.get("publication_date_key", "publication_date")
        explicit = data.get(key) if isinstance(data, dict) else None
        return _to_date(explicit) or _to_date(kn["sources"]["at_publication"][source]["fallback_date"])

    def is_arms_length(self, price, owner_type) -> bool:
        cfg = self.raw["outcome"]["arms_length"]
        if _is_missing(price) or (isinstance(price, float) and math.isnan(price)):
            return False
        if float(price) < float(cfg["min_price"]):
            return False
        if not _is_missing(owner_type) and str(owner_type) in cfg.get("exclude_owner_types", []):
            return False
        return True


def load_protocol(path: Path) -> Protocol:
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ProtocolError(f"{path} did not parse to a mapping")
    return Protocol(raw)
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/pytest tests/test_protocol.py -v`
Expected: all PASS. If `test_hash_is_stable_across_key_order_and_whitespace` fails, check that `yaml.safe_dump` preserved date types (PyYAML emits `2026-01-01` unquoted, which round-trips as a `date`); `default=str` makes dates hash identically either way.

- [ ] **Step 6: Commit**

```bash
git add protocol/v1.yaml src/provenance/protocol.py tests/test_protocol.py
git commit -m "Add frozen protocol v1 and protocol loader with content hash

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Audit computation (`audit.py`)

**Files:**
- Create: `src/provenance/audit.py`, `tests/test_audit.py`

**Interfaces:**
- Consumes: `io.*` loaders, `io.normalize_address`, `io.read_row_counts`, `Protocol` methods from Task 4.
- Produces:
  - `run_audit(data_dir: Path, protocol: Protocol) -> dict` — keys: `protocol`, `row_counts`, `layers`, `evidence`, `knowability`, `outcome`, `covariates`, `linkage`, `depth`, `sensitivity`, `vocabulary`, `thresholds`, `generated_at`.
  - `write_audit_json(result: dict, out_dir: Path) -> Path` (writes `<out_dir>/audit.json`).
  - Raises `ProtocolError` before computing anything if any source or category is unknown to the protocol.

- [ ] **Step 1: Write the failing tests**

`tests/test_audit.py`:
```python
import json
import shutil

import pandas as pd
import pytest

from provenance import audit
from provenance.errors import ProtocolError
from provenance.protocol import load_protocol
from tests.conftest import PROTOCOL_PATH


@pytest.fixture
def protocol():
    return load_protocol(PROTOCOL_PATH)


@pytest.fixture
def result(fixture_dir, protocol):
    return audit.run_audit(fixture_dir, protocol)


def test_layers_split(result):
    assert result["layers"]["totals"] == {"administrative": 10, "curated": 14}
    assert result["layers"]["by_source"]["baltimore:311"] == {"layer": "administrative", "rows": 4}


def test_evidence_section(result):
    ev = result["evidence"]
    assert ev["curated"]["graded"] == 13
    assert ev["curated"]["total"] == 14
    assert ev["curated"]["evidence_status"]["contested"] == 1
    assert ev["curated"]["evidence_status"]["(ungraded)"] == 1
    assert ev["administrative"]["evidence_status"]["(ungraded)"] == 10


def test_knowability_section(result):
    kn = result["knowability"]
    assert kn["whitepaper"] == {"rule": "at_publication", "rows": 2, "explicit_publication_date": 1, "fallback": 1}
    assert kn["nrhp"]["rule"] == "fixed"
    assert kn["newspapers_com"]["rule"] == "at_occurrence"


def test_outcome_section(result):
    oc = result["outcome"]
    assert oc["properties"] == 20
    assert oc["with_sale_date"] == 14
    assert oc["price_positive"] == 14
    assert oc["arms_length"] == 12          # drops the $1 sale and the city sale
    assert oc["transaction_coverage"] == pytest.approx(0.6)
    assert oc["sale_year_hist"]["2025"] == 1
    assert oc["with_assessed_value"] == 19
    assert oc["arms_length_before_holdout"] == 10


def test_covariates_section(result):
    cov = result["covariates"]
    assert cov["year_built"] == pytest.approx(19 / 20)
    assert cov["lot_polygon"] == pytest.approx(19 / 20)
    assert cov["block_side_id"] == 1.0


def test_linkage_section(result):
    ln = result["linkage"]
    assert ln["parcels"] == 24
    assert ln["parcels_with_matched_property_id"] == pytest.approx(5 / 24)
    assert ln["properties_with_exact_parcel_match"] == pytest.approx(19 / 20)


def test_depth_section(result):
    d = result["depth"]
    assert d["properties_with_curated"] == {"ge1": 8, "ge10": 0, "ge25": 0}
    assert d["top"][0] == {"property_id": 2, "curated_claims": 7, "sources": 6}
    assert d["archival_silence"] == {"total": 12, "searched": 3, "unsearched": 9}


def test_sensitivity_section(result):
    assert result["sensitivity"]["sensitivity"] == {"trauma": 1}
    assert result["sensitivity"]["rights"] == {"public": 1}


def test_thresholds_fail_on_small_fixture(result):
    th = result["thresholds"]
    assert th["min_panel_rows"] == {"required": 300, "actual": 12, "pass": False}
    assert th["min_transaction_coverage"] == {"required": 0.5, "actual": pytest.approx(0.6), "pass": True}
    assert result["vocabulary"] == {"unknown_sources": [], "unknown_categories": [], "ok": True}


def test_row_counts_without_file(result):
    assert result["row_counts"]["properties"] == {"actual": 20, "expected": None, "match": None}


def test_row_counts_with_file(fixture_dir, protocol, tmp_path):
    for f in fixture_dir.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    (tmp_path / "row_counts.txt").write_text("properties: 20\nsubjects: 99\n")
    rc = audit.run_audit(tmp_path, protocol)["row_counts"]
    assert rc["properties"]["match"] is True
    assert rc["subjects"] == {"actual": 4, "expected": 99, "match": False}


def test_unknown_source_aborts(fixture_dir, protocol, tmp_path):
    for f in fixture_dir.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    inc = pd.read_csv(tmp_path / "property_incidents.csv")
    inc.loc[0, "source"] = "brand_new_feed"
    inc.to_csv(tmp_path / "property_incidents.csv", index=False)
    with pytest.raises(ProtocolError) as e:
        audit.run_audit(tmp_path, protocol)
    assert "brand_new_feed" in str(e.value)


def test_write_audit_json_round_trips(result, tmp_path):
    path = audit.write_audit_json(result, tmp_path)
    assert path == tmp_path / "audit.json"
    assert json.loads(path.read_text())["protocol"]["version"] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_audit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'provenance.audit'`.

- [ ] **Step 3: Write audit.py**

`src/provenance/audit.py`:
```python
"""Stage 1: data-readiness audit. The only stage that reads outcome columns, and only to count coverage."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from provenance import io
from provenance.errors import ProtocolError
from provenance.protocol import Protocol

COVARIATES = ("year_built", "structure_sqft", "lot_polygon", "dwelling_units", "zoning_code", "latitude",
              "longitude", "census_tract", "market_typology", "vacancy_indicator", "block_side_id")

UNGRADED = "(ungraded)"


def _counts(series: pd.Series, fill: str = UNGRADED) -> dict[str, int]:
    vc = series.fillna(fill).astype(str).value_counts()
    return {k: int(v) for k, v in vc.items()}


def _check_vocabulary(inc: pd.DataFrame, protocol: Protocol) -> dict:
    unknown_sources = sorted(set(inc["source"].astype(str)) - protocol.known_sources())
    unknown_categories = sorted(set(inc["category"].dropna().astype(str)) - protocol.known_categories())
    return {"unknown_sources": unknown_sources, "unknown_categories": unknown_categories,
            "ok": not unknown_sources and not unknown_categories}


def _row_counts(tables: dict[str, pd.DataFrame], data_dir: Path) -> dict:
    expected = io.read_row_counts(data_dir) or {}
    out = {}
    for name, df in tables.items():
        exp = expected.get(name)
        out[name] = {"actual": int(len(df)), "expected": exp, "match": None if exp is None else exp == len(df)}
    return out


def _layers(inc: pd.DataFrame) -> dict:
    by_source = {}
    for source, grp in inc.groupby("source", sort=True):
        by_source[str(source)] = {"layer": str(grp["layer"].iloc[0]), "rows": int(len(grp))}
    totals = {k: int(v) for k, v in inc["layer"].value_counts().items()}
    totals.setdefault("administrative", 0)
    totals.setdefault("curated", 0)
    return {"totals": totals, "by_source": by_source}


def _evidence(inc: pd.DataFrame) -> dict:
    out = {}
    for layer in ("curated", "administrative"):
        sub = inc[inc["layer"] == layer]
        out[layer] = {
            "total": int(len(sub)),
            "graded": int(sub["evidence_status"].notna().sum()),
            "evidence_status": _counts(sub["evidence_status"]),
            "date_precision": _counts(sub["date_precision"], "(unset)"),
        }
    return out


def _knowability(inc: pd.DataFrame, protocol: Protocol) -> dict:
    key = protocol.raw["knowability"].get("publication_date_key", "publication_date")
    out = {}
    for source, grp in inc.groupby("source", sort=True):
        rule = protocol.knowability_rule(str(source))
        entry = {"rule": rule, "rows": int(len(grp))}
        if rule == "at_publication":
            explicit = int(grp["data"].map(lambda d: isinstance(d, dict) and bool(d.get(key))).sum())
            entry["explicit_publication_date"] = explicit
            entry["fallback"] = int(len(grp)) - explicit
        out[str(source)] = entry
    return out


def _outcome(props: pd.DataFrame, protocol: Protocol) -> dict:
    price = pd.to_numeric(props["last_sale_price"], errors="coerce")
    date = props["last_sale_date"]
    arms = pd.Series([protocol.is_arms_length(p, o) for p, o in zip(price, props["owner_type"])], index=props.index)
    arms &= date.notna()
    years = date.dt.year.dropna().astype(int)
    holdout = pd.Timestamp(protocol.temporal_holdout_start, tz="UTC")
    n = len(props)
    return {
        "properties": int(n),
        "with_sale_date": int(date.notna().sum()),
        "price_positive": int((price > 0).sum()),
        "arms_length": int(arms.sum()),
        "transaction_coverage": float(arms.sum() / n) if n else 0.0,
        "sale_year_hist": {str(k): int(v) for k, v in years.value_counts().sort_index().items()},
        "with_assessed_value": int(pd.to_numeric(props["assessed_value"], errors="coerce").notna().sum()),
        "arms_length_before_holdout": int((arms & (date < holdout)).sum()),
        "primary_outcome": protocol.raw["outcome"]["primary"],
        "secondary_outcome": protocol.raw["outcome"]["secondary"],
    }


def _covariates(props: pd.DataFrame) -> dict:
    n = len(props)
    return {c: float(props[c].notna().sum() / n) if n else 0.0 for c in COVARIATES}


def _linkage(props: pd.DataFrame, parcels: pd.DataFrame) -> dict:
    parcel_keys = set(parcels["normalized_address"].map(io.normalize_address))
    prop_keys = props["address"].map(io.normalize_address)
    n_parcels = len(parcels)
    return {
        "parcels": int(n_parcels),
        "parcels_with_matched_property_id": float(parcels["matched_property_id"].notna().sum() / n_parcels) if n_parcels else 0.0,
        "properties_with_exact_parcel_match": float(prop_keys.isin(parcel_keys).sum() / len(props)) if len(props) else 0.0,
    }


def _depth(props: pd.DataFrame, inc: pd.DataFrame, protocol: Protocol) -> dict:
    cur = inc[inc["layer"] == "curated"]
    per_prop = cur.groupby("property_id").agg(curated_claims=("id", "size"), sources=("source", "nunique"))
    counts = per_prop["curated_claims"]
    top = (per_prop.sort_values("curated_claims", ascending=False).head(25).reset_index())
    block_sources = (cur.merge(props[["id", "block_side_id"]], left_on="property_id", right_on="id", how="left")
                     .groupby("block_side_id")["source"].nunique())
    silent = props[~props["id"].isin(per_prop.index)]
    searched = silent["block_side_id"].map(block_sources).fillna(0) >= protocol.block_min_sources
    source_hist = {str(k): int(v) for k, v in per_prop["sources"].value_counts().sort_index().items()}
    return {
        "properties_with_curated": {"ge1": int((counts >= 1).sum()), "ge10": int((counts >= 10).sum()),
                                    "ge25": int((counts >= 25).sum())},
        "top": [{"property_id": int(r.property_id), "curated_claims": int(r.curated_claims), "sources": int(r.sources)}
                for r in top.itertuples()],
        "sources_per_property_hist": source_hist,
        "archival_silence": {"total": int(len(silent)), "searched": int(searched.sum()),
                             "unsearched": int((~searched).sum())},
    }


def _sensitivity(inc: pd.DataFrame) -> dict:
    return {
        "sensitivity": {k: int(v) for k, v in inc["sensitivity"].dropna().value_counts().items()},
        "rights": {k: int(v) for k, v in inc["rights"].dropna().value_counts().items()},
    }


def _thresholds(outcome: dict, protocol: Protocol) -> dict:
    v = protocol.validation
    return {
        "min_panel_rows": {"required": int(v["min_panel_rows"]), "actual": outcome["arms_length"],
                           "pass": outcome["arms_length"] >= int(v["min_panel_rows"])},
        "min_transaction_coverage": {"required": float(v["min_transaction_coverage"]),
                                     "actual": outcome["transaction_coverage"],
                                     "pass": outcome["transaction_coverage"] >= float(v["min_transaction_coverage"])},
    }


def run_audit(data_dir: Path, protocol: Protocol) -> dict:
    data_dir = Path(data_dir)
    tables = {name: io.LOADERS[name](data_dir) for name in io.TABLES}
    props = io.load_properties(data_dir, outcome_blind=False)
    tables["properties"] = props
    inc = tables["property_incidents"].copy()

    vocabulary = _check_vocabulary(inc, protocol)
    if not vocabulary["ok"]:
        raise ProtocolError(
            "protocol does not cover the data: "
            f"unknown sources {vocabulary['unknown_sources']}, unknown categories {vocabulary['unknown_categories']}"
        )
    inc["layer"] = inc["source"].map(protocol.layer_of)

    outcome = _outcome(props, protocol)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "protocol": {"version": protocol.version, "hash": protocol.hash},
        "row_counts": _row_counts(tables, data_dir),
        "layers": _layers(inc),
        "evidence": _evidence(inc),
        "knowability": _knowability(inc, protocol),
        "outcome": outcome,
        "covariates": _covariates(props),
        "linkage": _linkage(props, tables["property_parcels"]),
        "depth": _depth(props, inc, protocol),
        "sensitivity": _sensitivity(inc),
        "vocabulary": vocabulary,
        "thresholds": _thresholds(outcome, protocol),
    }


def write_audit_json(result: dict, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "audit.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True))
    return path
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/pytest tests/test_audit.py -v`
Expected: all PASS. Expected fixture numbers, for checking failures: 24 incidents (10 administrative: 3+1 on property 1, 1 on property 2, 5 permits on 12–16; 14 curated: 7 on property 2 and one each on 3, 4, 5, 6, 9, 10, 13); curated graded 13 (only property 3's claim is ungraded); 8 properties with ≥1 curated claim (2, 3, 4, 5, 6, 9, 10, 13); 12 silent, of which block side 1 (ids 1, 7, 8) is "searched" because block side 1 has ≥3 curated sources and block side 2 (ids 11, 12, 14–20) is "unsearched" because it has only one curated source. Arm's-length sales: 14 with a date minus the $1 sale (7) and the city sale (8) = 12; before 2024: 12 minus 2025 (10) and 2024 (13) = 10.

- [ ] **Step 5: Commit**

```bash
git add src/provenance/audit.py tests/test_audit.py
git commit -m "Add data-readiness audit computation

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Markdown report and CLI wiring

**Files:**
- Create: `src/provenance/audit_report.py`, `tests/test_audit_report.py`
- Modify: `src/provenance/cli.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `audit.run_audit`, `audit.write_audit_json`, `load_protocol`.
- Produces: `render_report(result: dict) -> str`; CLI commands `prov audit`, `prov protocol-hash`, `prov all`.

- [ ] **Step 1: Write the failing report test**

`tests/test_audit_report.py`:
```python
from provenance import audit
from provenance.audit_report import render_report
from provenance.protocol import load_protocol
from tests.conftest import PROTOCOL_PATH


def test_report_has_every_section_and_key_numbers(fixture_dir):
    result = audit.run_audit(fixture_dir, load_protocol(PROTOCOL_PATH))
    md = render_report(result)
    for heading in ["## 1. Row counts", "## 2. Layer split", "## 3. Evidence grading", "## 4. Knowability",
                    "## 5. Outcome coverage", "## 6. Covariate missingness", "## 7. Linkage readiness",
                    "## 8. Documentation depth", "## 9. Sensitivity and rights", "## 10. Thresholds",
                    "## 11. Protocol"]:
        assert heading in md, heading
    assert "| curated | 14 |" in md
    assert "| min_panel_rows | 300 | 12 | FAIL |" in md
    assert result["protocol"]["hash"] in md
    assert "whitepaper" in md and "at_publication" in md
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_audit_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'provenance.audit_report'`.

- [ ] **Step 3: Write audit_report.py**

`src/provenance/audit_report.py`:
```python
"""Render the audit dict to markdown. No computation happens here."""
from __future__ import annotations


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def render_report(result: dict) -> str:
    p = result["protocol"]
    s: list[str] = [
        "# Data-Readiness Audit",
        "",
        f"Generated {result['generated_at']} under protocol v{p['version']} (`{p['hash'][:12]}…`). "
        "This report is produced by `prov audit`; edit the pipeline, not this file.",
        "",
        "## 1. Row counts",
        "",
        _table(["table", "rows", "expected", "match"],
               [[t, v["actual"], "—" if v["expected"] is None else v["expected"],
                 "—" if v["match"] is None else ("yes" if v["match"] else "NO")]
                for t, v in result["row_counts"].items()]),
        "",
        "## 2. Layer split",
        "",
        _table(["layer", "rows"], [[k, v] for k, v in sorted(result["layers"]["totals"].items())]),
        "",
        _table(["source", "layer", "rows"],
               [[src, v["layer"], v["rows"]]
                for src, v in sorted(result["layers"]["by_source"].items(), key=lambda kv: -kv[1]["rows"])]),
        "",
        "## 3. Evidence grading",
        "",
    ]
    for layer in ("curated", "administrative"):
        ev = result["evidence"][layer]
        s += [f"**{layer}** — {ev['graded']} of {ev['total']} rows graded.", "",
              _table(["evidence_status", "rows"], [[k, v] for k, v in sorted(ev["evidence_status"].items())]), "",
              _table(["date_precision", "rows"], [[k, v] for k, v in sorted(ev["date_precision"].items())]), ""]
    s += [
        "## 4. Knowability",
        "",
        "Rule applied per source to date when a claim became knowable to the market.",
        "",
        _table(["source", "rule", "rows", "explicit publication date", "fallback"],
               [[src, v["rule"], v["rows"], v.get("explicit_publication_date", "—"), v.get("fallback", "—")]
                for src, v in sorted(result["knowability"].items(), key=lambda kv: -kv[1]["rows"])]),
        "",
        "## 5. Outcome coverage",
        "",
    ]
    oc = result["outcome"]
    s += [
        f"Primary outcome `{oc['primary_outcome']}` (modelled as log price); secondary `{oc['secondary_outcome']}` "
        "is administrative and never displayed as a market value.",
        "",
        _table(["measure", "value"], [
            ["properties", oc["properties"]],
            ["with sale date", oc["with_sale_date"]],
            ["price > 0", oc["price_positive"]],
            ["arm's-length sales", oc["arms_length"]],
            ["transaction coverage", _pct(oc["transaction_coverage"])],
            ["arm's-length sales before temporal holdout", oc["arms_length_before_holdout"]],
            ["with assessed value", oc["with_assessed_value"]],
        ]),
        "",
        _table(["sale year", "count"], [[y, n] for y, n in oc["sale_year_hist"].items()]),
        "",
        "## 6. Covariate missingness",
        "",
        _table(["column", "non-null"], [[c, _pct(v)] for c, v in result["covariates"].items()]),
        "",
        "## 7. Linkage readiness",
        "",
    ]
    ln = result["linkage"]
    s += [
        _table(["measure", "value"], [
            ["parcel rows", ln["parcels"]],
            ["parcels with matched_property_id", _pct(ln["parcels_with_matched_property_id"])],
            ["properties with exact normalized-address parcel match", _pct(ln["properties_with_exact_parcel_match"])],
        ]),
        "",
        "## 8. Documentation depth",
        "",
    ]
    d = result["depth"]
    s += [
        _table(["curated claims", "properties"], [["≥ 1", d["properties_with_curated"]["ge1"]],
                                                   ["≥ 10", d["properties_with_curated"]["ge10"]],
                                                   ["≥ 25", d["properties_with_curated"]["ge25"]]]),
        "",
        _table(["property_id", "curated claims", "distinct sources"],
               [[t["property_id"], t["curated_claims"], t["sources"]] for t in d["top"][:10]]),
        "",
        _table(["distinct curated sources", "properties"], [[k, v] for k, v in d["sources_per_property_hist"].items()]),
        "",
        f"Archival silence (zero curated claims): {d['archival_silence']['total']} properties — "
        f"{d['archival_silence']['searched']} on searched block sides, "
        f"{d['archival_silence']['unsearched']} on unsearched block sides. "
        "Silence is unmeasured history, not absence of history.",
        "",
        "## 9. Sensitivity and rights",
        "",
        _table(["sensitivity", "rows"], [[k, v] for k, v in sorted(result["sensitivity"]["sensitivity"].items())] or [["(none)", 0]]),
        "",
        _table(["rights", "rows"], [[k, v] for k, v in sorted(result["sensitivity"]["rights"].items())] or [["(none)", 0]]),
        "",
        "## 10. Thresholds",
        "",
        _table(["threshold", "required", "actual", "result"],
               [[k, v["required"], v["actual"] if isinstance(v["actual"], int) else f"{v['actual']:.3f}",
                 "PASS" if v["pass"] else "FAIL"] for k, v in result["thresholds"].items()]),
        "",
        f"Vocabulary check: {'all sources and categories are covered by the protocol' if result['vocabulary']['ok'] else 'UNCOVERED VALUES PRESENT'}.",
        "",
        "## 11. Protocol",
        "",
        f"Version {p['version']}, SHA-256 `{p['hash']}`.",
        "",
    ]
    return "\n".join(s)
```

- [ ] **Step 4: Run the report test**

Run: `.venv/bin/pytest tests/test_audit_report.py -v`
Expected: PASS.

- [ ] **Step 5: Write the failing CLI tests**

Append to `tests/test_cli.py`:
```python
import json

from tests.conftest import PROTOCOL_PATH


def test_audit_command_writes_json_and_report(fixture_dir, tmp_path):
    out, report = tmp_path / "derived", tmp_path / "readiness.md"
    result = runner.invoke(app, ["audit", "--data-dir", str(fixture_dir), "--protocol", str(PROTOCOL_PATH),
                                 "--out", str(out), "--report", str(report)])
    assert result.exit_code == 0, result.output
    assert json.loads((out / "audit.json").read_text())["outcome"]["arms_length"] == 12
    assert "# Data-Readiness Audit" in report.read_text()
    assert "min_panel_rows" in result.output and "FAIL" in result.output


def test_protocol_hash_command():
    result = runner.invoke(app, ["protocol-hash", "--protocol", str(PROTOCOL_PATH)])
    assert result.exit_code == 0
    assert len(result.output.strip()) == 64


def test_all_runs_audit(fixture_dir, tmp_path):
    result = runner.invoke(app, ["all", "--data-dir", str(fixture_dir), "--protocol", str(PROTOCOL_PATH),
                                 "--out", str(tmp_path / "d"), "--report", str(tmp_path / "r.md")])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "d" / "audit.json").exists()


def test_audit_reports_protocol_error_cleanly(fixture_dir, tmp_path):
    import shutil
    import pandas as pd
    for f in fixture_dir.glob("*.csv"):
        shutil.copy(f, tmp_path / f.name)
    inc = pd.read_csv(tmp_path / "property_incidents.csv")
    inc.loc[0, "source"] = "brand_new_feed"
    inc.to_csv(tmp_path / "property_incidents.csv", index=False)
    result = runner.invoke(app, ["audit", "--data-dir", str(tmp_path), "--protocol", str(PROTOCOL_PATH),
                                 "--out", str(tmp_path / "d"), "--report", str(tmp_path / "r.md")])
    assert result.exit_code == 2
    assert "brand_new_feed" in result.output
```

- [ ] **Step 6: Run to verify failure**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: the three new tests FAIL with "No such command 'audit'" (Typer exit code 2 and usage text), and `test_audit_reports_protocol_error_cleanly` fails on the missing-command output not containing `brand_new_feed`.

- [ ] **Step 7: Rewrite cli.py**

`src/provenance/cli.py`:
```python
from pathlib import Path

import typer

from provenance import __version__
from provenance.errors import ProtocolError, SchemaError

app = typer.Typer(help="Provenance engine pipeline for Pricing the Unpriced.", no_args_is_help=True)

ROOT = Path.cwd()
DataDir = typer.Option(ROOT, "--data-dir", help="Folder holding the sponsor CSVs.")
ProtocolOpt = typer.Option(ROOT / "protocol" / "v1.yaml", "--protocol", help="Protocol YAML.")
OutDir = typer.Option(ROOT / "data" / "derived", "--out", help="Stage output folder.")
ReportPath = typer.Option(ROOT / "docs" / "data_readiness.md", "--report", help="Markdown report path.")


def _fail(exc: Exception) -> None:
    typer.secho(f"error: {exc}", fg=typer.colors.RED, err=False)
    raise typer.Exit(code=2)


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command("protocol-hash")
def protocol_hash(protocol: Path = ProtocolOpt) -> None:
    """Print the SHA-256 content hash of the protocol file."""
    from provenance.protocol import load_protocol

    try:
        typer.echo(load_protocol(protocol).hash)
    except ProtocolError as e:
        _fail(e)


def _run_audit(data_dir: Path, protocol: Path, out: Path, report: Path) -> None:
    from provenance import audit
    from provenance.audit_report import render_report
    from provenance.protocol import load_protocol

    try:
        proto = load_protocol(protocol)
        result = audit.run_audit(data_dir, proto)
    except (ProtocolError, SchemaError, FileNotFoundError) as e:
        _fail(e)
        return
    json_path = audit.write_audit_json(result, out)
    report = Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(result))
    typer.echo(f"audit: wrote {json_path} and {report}")
    for name, t in result["thresholds"].items():
        typer.echo(f"  {name}: {'PASS' if t['pass'] else 'FAIL'} (required {t['required']}, actual {t['actual']})")


@app.command()
def audit(data_dir: Path = DataDir, protocol: Path = ProtocolOpt, out: Path = OutDir, report: Path = ReportPath) -> None:
    """Stage 1: data-readiness audit → audit.json + markdown report."""
    _run_audit(data_dir, protocol, out, report)


@app.command("all")
def run_all(data_dir: Path = DataDir, protocol: Path = ProtocolOpt, out: Path = OutDir, report: Path = ReportPath) -> None:
    """Run every implemented stage in order."""
    _run_audit(data_dir, protocol, out, report)
```

- [ ] **Step 8: Run the whole suite**

Run: `.venv/bin/pytest -v`
Expected: every test in `test_cli.py`, `test_io.py`, `test_protocol.py`, `test_audit.py`, `test_audit_report.py`, `test_fixture.py` PASSES.

- [ ] **Step 9: Commit**

```bash
git add src/provenance/audit_report.py src/provenance/cli.py tests/test_audit_report.py tests/test_cli.py
git commit -m "Render data-readiness report and wire prov audit / protocol-hash / all

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Real-data test and the committed readiness report

**Files:**
- Create: `tests/test_real_data.py`, `docs/data_readiness.md` (generated)

**Interfaces:**
- Consumes: everything above. Runs against the sponsor CSVs in the repo root.

- [ ] **Step 1: Write the real-data test**

`tests/test_real_data.py`:
```python
"""Runs only when the sponsor's real export is present in the repo root."""
import pytest

from provenance import audit
from provenance.protocol import load_protocol
from tests.conftest import PROTOCOL_PATH, REPO_ROOT

pytestmark = pytest.mark.skipif(not (REPO_ROOT / "property_incidents.csv").exists(), reason="real export not present")


@pytest.fixture(scope="module")
def result():
    return audit.run_audit(REPO_ROOT, load_protocol(PROTOCOL_PATH))


def test_curated_count_matches_readme(result):
    assert result["layers"]["totals"]["curated"] == 3602
    assert result["layers"]["totals"]["administrative"] == 16706


def test_vocabulary_is_fully_covered(result):
    assert result["vocabulary"]["ok"]


def test_row_counts_match_export(result):
    assert all(v["match"] for v in result["row_counts"].values())


def test_depth_matches_readme(result):
    assert result["depth"]["properties_with_curated"] == {"ge1": 316, "ge10": 68, "ge25": 22}
    assert result["depth"]["top"][0]["property_id"] == 2376


def test_thresholds_pass_on_real_data(result):
    assert result["thresholds"]["min_panel_rows"]["pass"]
    assert result["thresholds"]["min_transaction_coverage"]["pass"]
```

- [ ] **Step 2: Run it**

Run: `.venv/bin/pytest tests/test_real_data.py -v`
Expected: PASS. If `test_thresholds_pass_on_real_data` fails on coverage, read the actual value from the failure: about 1,309 sales are ≥ $10,000 and 19 properties are city-owned, so coverage should be roughly 0.69 against a 0.50 requirement. If a source or category is reported unknown, the export changed since the spec was written; stop and report rather than editing the protocol silently.

- [ ] **Step 3: Generate the committed report**

Run: `.venv/bin/prov audit`
Expected output begins `audit: wrote data/derived/audit.json and docs/data_readiness.md`, followed by `min_panel_rows: PASS` and `min_transaction_coverage: PASS`. Open `docs/data_readiness.md` and check section 2 shows `| curated | 3602 |` and section 4 shows `whitepaper | at_publication | 1138`.

- [ ] **Step 4: Confirm nothing outside the plan changed**

Run: `git status --short`
Expected: only `tests/test_real_data.py` and `docs/data_readiness.md` are new. `data/derived/` must not appear (gitignored). The sponsor's CSVs, README, notebook, and `verify_claims.py` are unmodified.

- [ ] **Step 5: Commit**

```bash
git add tests/test_real_data.py docs/data_readiness.md
git commit -m "Add real-data audit test and commit the data-readiness report

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage.** §2 deliverables 1–6 → Tasks 1, 3, 4, 5–6, 2/7, 1. §3 loaders and `SchemaError` → Task 3. §4 every `Protocol` method → Task 4. §5 YAML → Task 4 Step 1 (verbatim copy). §6 all eleven report sections → Task 5 computes, Task 6 renders, with headings matched by the report test. §7 CLI with `audit`, `protocol-hash`, `all` → Task 6. §8 fixture cases → Task 2 (each case is listed in the Interfaces block and asserted in `test_fixture.py`). §9 tests → Tasks 3–7; the spec's "row-count comparison tolerates a missing `row_counts.txt`" is `test_row_counts_without_file`. §10 out of scope respected: no resolution, graph, score, model, polygon area, or notebooks.

**Placeholder scan.** None. Task 4 Step 1 points at the spec's YAML block rather than repeating 120 lines; the spec is the source of truth and is committed alongside.

**Type consistency.** `run_audit(data_dir, protocol)` and `write_audit_json(result, out_dir)` are used identically in Tasks 5, 6, 7. `Protocol.knowability_rule`, `known_sources`, `known_categories`, `salience`, `is_arms_length`, `block_min_sources`, `temporal_holdout_start`, `validation` are defined in Task 4 and consumed by name in Task 5. `io.LOADERS`, `io.TABLES`, `io.normalize_address`, `io.read_row_counts` are defined in Task 3 and consumed in Task 5.
