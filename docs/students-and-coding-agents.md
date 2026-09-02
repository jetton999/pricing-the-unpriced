# Plan: setting up the repo so students and their coding agents can work in it

Written 2026-09-02. Status: proposed, not yet implemented.

## The problem

CUSP students will arrive with a coding agent: Claude Code, Cursor, VS Code Copilot,
Codex, or Gemini CLI. Today the repo's entry point is a `.ipynb` file. Every one of those
agents handles notebook JSON worse than it handles plain Python: cells get replaced
wholesale, required fields get stripped, edits land in the wrong cell, and the agent
cannot see the kernel's state. The tools that do execute cells natively (VS Code Copilot
agent mode, Jupyter AI v3, marimo) each assume one specific editor.

The fix is not to abandon notebooks. It is to make plain `.py` files the source of truth,
generate the notebook view from them, and give the agent one file that tells it how the
repo works and one command that tells it whether it broke anything.

## What to do, in order

### Phase 1: the agent can orient itself and check its work (half a day)

1. **`AGENTS.md` at the repo root, and a one-line `CLAUDE.md` containing `@AGENTS.md`.**
   Codex, Gemini, Cursor, Copilot, and VS Code read `AGENTS.md`; Claude Code reads
   `CLAUDE.md`. Contents, in this order:
   - What the repo is: the two project ideas, one paragraph each, linking to `README.md`.
   - The layer rule: a source is administrative if it starts with `baltimore:` or is
     `sdat_assessments` or `sdat:owner`; everything else is curated. Give the counts.
   - Commands: `python3 verify_claims.py`, `python3 map/app.py --check`, and the notebook
     execution command below. Say "run these before you say you are done."
   - Where things are: `DATA_DICTIONARY.md` for columns, `docs/worker-owned-exits.md` for
     idea 2 cases, `LICENSE.md` for the sensitivity rule.
   - Rules: edit `notebooks/*.py`, never the `.ipynb`; never commit outputs; never drop
     rows with a `sensitivity` flag; assessed value is not a market price; `avm_estimate`,
     `nearby_*`, `walk_score`, and `building_condition` are empty in this export.
   - The team's disclosure policy for agent-written code, once faculty agree it.

2. **`pyproject.toml` managed by `uv`.** Dependencies: pandas, matplotlib, networkx,
   jupytext, ipykernel, nbconvert, pytest. Then `uv sync` gives every student and every
   agent the same environment with no install instructions. Keep a one-line pip fallback
   in the README for students without `uv`.

3. **`bin/check`**, a shell script the agent can run:
   ```
   python3 verify_claims.py
   python3 map/app.py --check
   uv run jupytext --sync notebooks/*.py
   uv run jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 \
     START_HERE.ipynb --output-dir /tmp/nb-check
   ```
   Exit nonzero on any failure. Name it in `AGENTS.md`.

4. **Pair the notebook with a percent script.** `uv run jupytext --set-formats
   ipynb,py:percent START_HERE.ipynb` creates `START_HERE.py`. Commit both. Add
   `.gitattributes` with `*.ipynb filter=nbstripout` and a pre-commit config running
   `nbstripout` and `jupytext --sync`, so the `.ipynb` in git never carries outputs and
   never drifts from the `.py`. Students open either file in their editor; agents edit
   the `.py`.

### Phase 2: one testable surface for the data (one day)

5. **A loader module, `greenmount.py`, at the repo root.** Functions: `load_tables()`,
   `is_admin(source)`, `curated(inc)`, `use_history(property_id)`, `block_sides()`,
   `commercial_sales()`. The notebook imports these instead of repeating the joins. An
   agent asked to "add a column to the starter table" then edits one function with a
   test, not a notebook cell. Keep it pandas-only; `map/app.py` stays stdlib.

6. **`tests/test_greenmount.py`** with pytest: row counts, the 3,602 / 16,706 split, the
   316 / 68 / 22 depth tiers, 678 `operated_at` links, and one use-history spot check
   (3313 Greenmount has 15 distinct businesses). Add `uv run pytest -q` to `bin/check`.

7. **Split the notebook by idea.** `notebooks/00_data_tour.py` (sections 1–3),
   `notebooks/idea1_use_history.py` (section 4), `notebooks/idea2_lease_model.py`
   (section 5). `START_HERE.ipynb` becomes a short index that links to the three. A team
   working on one idea, or an agent asked about one idea, then opens one focused file.

### Phase 3: the student-facing guide (an hour, plus a faculty conversation)

8. **`docs/working-with-a-coding-agent.md`**, ten lines: clone, `uv sync`, open in your
   editor, tell the agent to read `AGENTS.md`, ask it to run `bin/check` first, edit the
   `.py` files, run `bin/check` before every commit, cite sources for any historical
   claim it writes into a use history, and how to disclose agent-written work.

9. **Agree the disclosure policy with the faculty lead** and put it in `AGENTS.md`. The
   2026 syllabi found in research either ban agents on graded work or say nothing. A
   capstone with a sponsor is different: the sponsor wants the work done well, and the
   agent is a tool. Write down what the team commits: agent-written code is reviewed and
   tested by a human before it is merged; historical claims are traced to a source row.

## What not to do

- Do not switch the whole project to marimo or Quarto. marimo has the best agent
  ergonomics on paper but is a second notebook dialect, and its `.ipynb` interchange is
  lossy. Quarto has no agent cell tooling. Either is fine for one final report.
- Do not standardize on a single editor. VS Code Copilot agent mode and Jupyter AI v3 are
  the only tools that execute cells natively, but students will bring what they have. The
  percent-script layout works in all of them.
- Do not let an agent edit `map/app.py` into a framework. It is stdlib on purpose so that
  a student with a bare Python install can run it.

## How each agent handles notebooks today

| Agent | Notebook support | Caveat |
|---|---|---|
| Claude Code | Edits one cell at a time by id; runs code in the kernel only from the VS Code extension after a prompt | No `.py`-first workflow built in; a request for one was closed "not planned" in Jan 2026 |
| Cursor | Agent and inline edit work in `.ipynb`; execution via the Jupyter extension | Known bug since Feb 2026 strips required fields from `.ipynb` on save; no fix date |
| VS Code Copilot agent mode | Edits across cells, runs cells, reads outputs, references kernel variables | Whole-cell replacement; wrong-cell edits and corruption reported on long cells |
| Codex CLI | No notebook tool; an official skill scaffolds notebooks from templates to avoid raw JSON | Community reports invalid JSON and lost markdown; users move to `.py` |
| Gemini CLI | No notebook tool; generic file rewrite | Corruption and deletion reported; no notebook tool in 2026 changelogs |
| Jupyter AI v3 | Hosts Claude, Codex, Copilot, Gemini, and others inside JupyterLab; server-side cell execution since v3.1 | Newest and heaviest; JupyterLab 4.6+ only |
| marimo | Notebooks are plain `.py`; `marimo check` lints; `marimo pair` gives the agent a live session | Different runtime model; outputs not stored; lossy `.ipynb` round trip |

Sources: code.claude.com/docs/en/tools; cursor.com/docs/cookbook/data-science and the Cursor
forum thread on EditNotebook; code.visualstudio.com/docs/agents/guides/notebooks-with-ai;
github.com/openai/skills jupyter-notebook skill; github.com/google-gemini/gemini-cli issue
6930; github.com/jupyterlab/jupyter-ai v3.1 release notes; docs.marimo.io. Convention
sources: agents.md; docs.astral.sh/uv/guides/integration/jupyter; jupytext pre-commit
docs; github.com/kynan/nbstripout; cookiecutter-data-science.

Not verified: whether Cursor has since fixed the field-stripping bug; any NYU CUSP policy
on coding agents in capstones.
