# The project

One Python project, built across 4 days. Three folders, three jobs — all the **same project at different points in time**:

| Folder | What it is | What you do with it |
|---|---|---|
| `start-here/` | The Day-1 baseline: empty `catalog/` package + the `tests/` scoreboard | **Copy it once, build here all week** |
| `checkpoints/` | The project frozen at the start of Days 2 / 3 / 4 | **Fell behind? Reset from here** to rejoin |
| `solution/` | The finished reference answer (Day-4 end state) | **Peek when stuck — don't edit** |

## Start (Day 1)
```bash
cp -r project/start-here my-catalog && cd my-catalog     # run from client_docs/
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest -q          # all specs SKIP — that's your scoreboard
```
Then per lab: copy the lab's `starter/` files into `catalog/`, fill the `# TODO`s, run that lab's check.

## Fell behind?
```bash
cd my-catalog
rm -rf catalog data .github          # keep tests/ — your lab graders live there
cp -r ../project/checkpoints/day-N-start/. .
pip install -e ".[dev]"
```
