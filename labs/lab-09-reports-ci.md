# Lab 9 — Reports + GitHub Actions

**Duration:** ~80 min · **Day:** 3 · **Module:** 3 (Reporting + CI/CD)

## Goal
Make the test suite *visible*. Add coverage. Generate an HTML report.
Wire it all into GitHub Actions so every push runs the suite across
Python 3.10/3.11/3.12 and uploads the HTML report as an artifact.

When this lab ends, your repo has a real CI badge that goes green on push.

## You start with
- Lab 8 end-state — 25+ tests passing locally, including an integration class.

## You'll end with
- `pytest --cov --html=report.html` producing a self-contained HTML file
- `.github/workflows/tests.yml` running on push + PR
- Pushing a commit shows ✅ on GitHub

## Steps

1. **Configure pytest in `pyproject.toml`.** Tell it where the tests live, what markers exist, and what to cover:

   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   addopts = "-ra --strict-markers"
   markers = [
       "integration: tests that hit a live FastAPI server (slow)",
   ]

   [tool.coverage.run]
   source = ["catalog"]
   branch = true
   ```

2. **Generate the HTML report locally.**

   ```bash
   pytest --cov --cov-report=term-missing --html=report.html --self-contained-html
   open report.html        # macOS — xdg-open on Linux, start on Windows
   ```

   `--self-contained-html` inlines CSS/JS so the file works when emailed.

3. **Create `.github/workflows/tests.yml`.** Minimal viable shape:

   ```yaml
   name: tests

   on:
     push:
       branches: [main]
     pull_request:
     workflow_dispatch:

   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         fail-fast: false
         matrix:
           python-version: ["3.10", "3.11", "3.12"]
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: ${{ matrix.python-version }}
             cache: pip
         - run: |
             python -m pip install --upgrade pip
             pip install -e ".[dev]"
         - run: |
             pytest --cov --cov-report=xml \
                    --html=report.html --self-contained-html \
                    --junitxml=junit.xml
         - if: always()
           uses: actions/upload-artifact@v4
           with:
             name: pytest-report-${{ matrix.python-version }}
             path: |
               report.html
               coverage.xml
               junit.xml
   ```

   `fail-fast: false` makes Python 3.11 *not* cancel just because 3.10 failed. `if: always()` uploads the report even when tests fail — the times you need it most.

4. **Append a coverage summary to the GH Actions UI.** A two-line block at the end of the workflow makes the run page show coverage without digging into artifacts:

   ```yaml
   - if: always()
     run: |
       echo "### Coverage" >> $GITHUB_STEP_SUMMARY
       python -c "import xml.etree.ElementTree as ET; \
         r = ET.parse('coverage.xml').getroot(); \
         print(f\"Line: {float(r.get('line-rate'))*100:.1f}%\")" \
         >> $GITHUB_STEP_SUMMARY
   ```

5. **Push and watch.** Create a GitHub repo (private is fine), push, open the Actions tab.

   ```bash
   git init
   git add .
   git commit -m "Day 3 — tests + CI"
   gh repo create my-acuity-catalog --private --source=. --push   # if you have gh CLI
   ```

6. **Add a status badge to `README.md`** (optional but a nice flex):

   ```markdown
   ![tests](https://github.com/<user>/<repo>/actions/workflows/tests.yml/badge.svg)
   ```

## Expected output

```
$ pytest --cov --cov-report=term-missing --html=report.html --self-contained-html
.................................                                        [100%]
================================ tests coverage ================================
Name                    Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------
catalog/client.py          57      7      4      0    85%   ...
catalog/models.py          76      0     12      0   100%
...
33 passed in 1.0s
```

GitHub Actions:

```
✓ test (3.10)   1m 28s
✓ test (3.11)   1m 24s
✓ test (3.12)   1m 19s
```

Artifacts: `pytest-report-3.10/report.html` (etc.) downloadable from the run page.

## Common pitfalls
- Forgetting `--strict-markers` — typo'd marker (`@pytest.mark.integraton`) silently runs nothing.
- Setting `fail-fast: true` (the default) cancels everything when 3.10 fails — you lose 3.11 + 3.12 signal.
- Uploading `report.html` *only* on success: the failing run is exactly when you need it. Use `if: always()`.
- Caching `pip` by `python-version` is automatic in `setup-python@v5` only when you pass `cache: pip`. Without it, every run reinstalls everything.
- Pushing `import_report.json` / `catalog.json` to the repo by accident. Your `.gitignore` should cover them.

## Stretch (optional)
- Add a **coverage gate**: `pytest --cov --cov-fail-under=80` fails CI if line coverage drops.
- Add a `lint` job in the workflow that runs `ruff check` and `mypy catalog/`.
- Add a `concurrency:` group so a new push cancels in-progress runs on the same branch.

---

**End of Day 3.** Your working folder is now the input for Day 4 — your
checkpoint matches `project/checkpoints/day-4-start/`.
