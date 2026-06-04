# Catch-up baselines

Each `day-N-start/` is the **start** state for Day N. Fell behind? Copy one over your working folder (`my-catalog/`) and rejoin:

```bash
cd my-catalog
rm -rf catalog data .github          # keep tests/ — your lab graders live there
cp -r ../project/checkpoints/day-N-start/. .
pip install -e ".[dev]"
```

| Folder | = state after | Contents |
|---|---|---|
| `day-2-start/` | Day 1 | `Product`, `ProductCatalog`, storage, decorators, FastAPI server |
| `day-3-start/` | Day 2 | + Pydantic models, `APIClient`, CSV bulk-import |
| `day-4-start/` | Day 3 | + full pytest suite, coverage, GitHub Actions |

- **The beginning** (Day-1 baseline) lives in `../start-here`, not here.
- **The finished answer** (Day-4 end state) is `../solution`.
- **Your lab self-check graders** (`tests/test_lab*.py`) come from `../start-here` and live in your `my-catalog/tests/`. Checkpoints carry only project code, and the reset above **keeps `tests/`**, so your graders survive a reset.
