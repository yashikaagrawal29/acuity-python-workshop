# Acuity Workshop — Trainer's Guide

**Python, Automation Testing, JSON & Generative AI with Agentic AI**
4 days · 24 hours · one connected project (`project/`)

This folder contains everything needed to deliver the workshop:

| Path | Purpose |
|---|---|
| `deck/day-N.md` | Marp slides (4 decks, one per day) |
| `labs/lab-NN-*/` | 12 lab guides, in order. **Days 1–2** (labs 01–06) are folders: `README.md` guide + `starter/` ready-to-fill `.py` scaffolds. Days 3–4 (labs 07–12) are still flat `lab-NN-*.md` |
| `project/start-here/` | Day-1 baseline — the empty `catalog/` package students copy and build on all week |
| `project/checkpoints/day-N-start/` | Catch-up baselines: what the project looks like at the **start** of Days 2–4 |
| `project/solution/` | Reference solution — the **end-state** of all 4 days |
| `deck/day-1-senior.md` + `labs/lab-0N-*/README-senior.md` | **Day-1 Senior Track** (optional) — deeper concepts + harder lab variants for experienced rooms |

The source-of-truth course outline is `../trainer_docs/outline_v4.1-24hrs.md`. Every slide, lab, and code file traces back to it.

---

## How to deliver each day

Each 6-hour day = **3 modules × (~40 min concept + ~80 min lab)** plus breaks.

1. Before the session: `cd project/solution && uv sync` (or `pip install -e .`). Smoke-test the day's commands listed in each lab's "Expected output".
2. Open the deck: `marp deck/day-1.md --preview` (or render PDF with `--pdf`, PPTX with `--pptx`).
3. For each module: present concept slides → land on the "Lab handoff" slide → participants open the matching lab guide.
4. Anyone behind can copy `project/checkpoints/day-N-start/` over their working folder and rejoin.

---

## Trainer setup (do once)

```bash
# 1. Python 3.10+
python --version

# 2. Install Marp CLI for slide rendering (Node 18+ required)
npm install -g @marp-team/marp-cli

# 3. Install workshop dependencies
cd project/solution
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 4. Smoke-test the reference solution
uvicorn catalog.server:app --reload &
curl http://localhost:8000/products
pytest
```

---

## Participant setup (Day 1)

Participants clone this repo and build their project in one working folder for the whole week — a copy of the Day-1 baseline (`project/start-here/`), so the catch-up `project/checkpoints/` stay pristine.

```bash
git clone <repo-url> acuity-workshop && cd acuity-workshop/client_docs
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
cp -r project/start-here my-catalog                    # your folder for the week
cd my-catalog
pip install -e ".[dev]"
pytest -q          # all specs SKIP (nothing built yet) — this is your scoreboard
```

Then per lab (working from `my-catalog/`): copy the lab's `starter/` files into `catalog/`, fill the `# TODO`s, and run that lab's test (`pytest tests/test_lab01.py`). Fell behind? Copy the next `project/checkpoints/day-N-start/` over your folder to rejoin.

---

## Renderable artifacts

> Run these from `client_docs/`. The custom `acuity` theme auto-loads via `.marprc.yml` (no `--theme-set` needed). Requires Marp CLI + Node 18+; PDF/PPTX export needs Chrome installed.

```bash
# Slides → PDF
marp deck/day-1.md --pdf -o out/day-1.pdf
marp deck/day-2.md --pdf -o out/day-2.pdf
marp deck/day-3.md --pdf -o out/day-3.pdf
marp deck/day-4.md --pdf -o out/day-4.pdf

# Slides → PowerPoint (editable in PPT)
marp deck/day-1.md --pptx -o out/day-1.pptx

# Lab guides → PDF (optional, for handouts)
# Any markdown-to-PDF tool works; pandoc example:
pandoc labs/lab-01-product-foundation/README.md -o out/lab-01.pdf
```

---

## Module + Lab map

| Day | M1 | Lab 1 | M2 | Lab 2 | M3 | Lab 3 |
|---|---|---|---|---|---|---|
| 1 | Python core | `lab-01-product-foundation` | Data structures + files | `lab-02-persistent-catalog` | OOP + decorators + FastAPI | `lab-03-local-api-server` |
| 2 | JSON + Pydantic | `lab-04-pydantic-models` | REST + requests | `lab-05-api-client` | Data-driven patterns | `lab-06-bulk-import` |
| 3 | pytest + fixtures | `lab-07-unit-tests` | Parametrize + mocking | `lab-08-test-apiclient` | Reports + CI | `lab-09-reports-ci` |
| 4 | LLM + structured outputs | `lab-10-nl-query-filter` | Tools + agent loop | `lab-11-catalog-agent` | **Testing AI** | `lab-12-test-the-agent` |

End state: a tested, agentic Python project — one repo, four days.

---

## Day-1 Senior Track (optional)

Day 1 fundamentals run light for senior engineers. When the room is ahead, pull in the senior material instead of letting fast finishers idle.

| Base module | Senior slides | Senior lab (replaces base lab + stretch) |
|---|---|---|
| M1 Python core | `deck/day-1-senior.md` (M1) | `labs/lab-01-product-foundation/README-senior.md` — frozen/hashable/orderable `Product`, EAFP, `Counter` summary |
| M2 Data structures + files | `deck/day-1-senior.md` (M2) | `labs/lab-02-persistent-catalog/README-senior.md` — atomic writes, generator-streamed CSV, `pathlib`, `defaultdict`/`Counter` |
| M3 OOP + decorators + FastAPI | `deck/day-1-senior.md` (M3) | `labs/lab-03-local-api-server/README-senior.md` — `Depends` DI, exponential-backoff `@retry`, `@property`, `Protocol` |

**How to run it:** interleave each senior slide block after the matching base module, then send fast finishers to the senior lab variant. Render: `marp deck/day-1-senior.md --pdf -o out/day-1-senior.pdf`.

**Safe by design:** the senior path is a *deeper route to the same `day-2-start` baseline*, not a fork. Anyone can copy `project/checkpoints/day-2-start/` to rejoin the canonical Day 2 — nothing built on the senior track is wasted.
