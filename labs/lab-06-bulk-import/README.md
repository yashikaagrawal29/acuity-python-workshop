# Lab 6 — Bulk-Import Workflow

**Duration:** ~80 min · **Day:** 2 · **Module:** 3 (Data-Driven Patterns)

> **Concepts used:** CSV → validate → API workflow and the structured import report → `codealong/module-6.ipynb` (leans on `@retry` from Day-1 `codealong/module-3.ipynb` via the `APIClient`).
> This lab applies the module's `BankAccount` import workflow to the course's `Product` domain — same patterns, different thing (the deliberate concept-vs-lab seam).

## Goal
Wire the pieces together. Read `data/products.csv`, validate each row with
`ProductCreate`, push valid rows through `APIClient.create_product()`, and
write a structured `import_report.json` that tells the operator **exactly
what failed and why**. This complete workflow becomes the
**system-under-test** for Day 3.

## You start with
- Lab 5 end-state — server + Pydantic models + working `APIClient`.

## You'll end with
- `data/products.csv` with intentionally bad rows mixed in
- `catalog/import_csv.py` runnable as `python -m catalog.import_csv data/products.csv`
- An `import_report.json` with three sections: `created`, `validation_errors`, `api_errors`

## Starter files

`starter/` gives you the import scaffold and a ready-made CSV. Copy them in, then fill the three `# TODO`s in the loop (validate → create → record) and the health-check in `main()`. The report shape and CLI are decided; the loop logic is yours.

```bash
cp ../labs/lab-06-bulk-import/starter/import_csv.py catalog/   # run from my-catalog/
cp ../labs/lab-06-bulk-import/starter/products.csv  data/      # the CSV lives under data/
```

| File | You write |
|---|---|
| `starter/import_csv.py` | the three loop bodies (validate / create / record) + the `health()` fail-fast in `main()` |
| `starter/products.csv` | 16 clean rows (ids 100–115) + 3 deliberately-bad rows (18–20) — extend it if you like |

## Steps

1. **Author `data/products.csv`.** Include ~20 rows: most clean, a few intentionally bad. The starter CSV already mixes the bad ones in to test all three failure paths:
   - row with empty name → validation error
   - row with `price = -50` → validation error
   - row with `price = not-a-number` → validation error (type coercion fails)
   - (optional) a row with an `id` that duplicates the seed → API error 409

2. **Write `catalog/import_csv.py`.** The shape:

   ```python
   def import_csv(csv_path, client: APIClient) -> dict[str, Any]:
       created, validation_errors, api_errors = [], [], []

       with open(csv_path) as fh:
           for row_no, row in enumerate(csv.DictReader(fh), start=2):
               try:
                   payload = ProductCreate.model_validate(row)
               except ValidationError as exc:
                   validation_errors.append(
                       {"row": row_no, "input": row, "errors": exc.errors()})
                   continue
               try:
                   product = client.create_product(payload)
               except APIError as exc:
                   api_errors.append(
                       {"row": row_no, "input": row,
                        "status": exc.status_code, "detail": exc.detail})
                   continue
               created.append(product.model_dump())

       return {
           "source": str(csv_path),
           "summary": {
               "rows_read": len(created)+len(validation_errors)+len(api_errors),
               "created": len(created),
               "validation_errors": len(validation_errors),
               "api_errors": len(api_errors),
           },
           "created": created,
           "validation_errors": validation_errors,
           "api_errors": api_errors,
       }
   ```

   The three lists are **separate** on purpose. Validation failures and API failures need different fixes — never collapse them into a single "errors" bucket.

3. **Wrap it in a CLI.** `argparse` with `csv_path`, `--base-url`, `--report`. On startup, ping `client.health()` and exit 2 if the server is unreachable — a sane early-fail signal.

4. **Run it.**
   ```bash
   # terminal 1
   uvicorn catalog.server:app --reload

   # terminal 2
   python -m catalog.import_csv data/products.csv
   cat import_report.json | head -30
   ```

5. **Read the report.** The `summary` should mirror what you saw in stdout. The `validation_errors[0].errors[0]` should pinpoint the offending field — that's Pydantic earning its keep.

## Expected output

```
$ python -m catalog.import_csv data/products.csv
INFO catalog.models: added product id=100 name='Wireless Mouse'
...
INFO catalog.models: added product id=115 name='Trail Running Shoes'
WARNING __main__: row 18 failed validation
WARNING __main__: row 19 failed validation
WARNING __main__: row 20 failed validation

19 rows  |  created 16  ·  validation errors 3  ·  API errors 0
report → import_report.json
```

```json
// import_report.json (excerpt)
{
  "summary": { "rows_read": 19, "created": 16,
                "validation_errors": 3, "api_errors": 0 },
  "validation_errors": [
    { "row": 18, "input": {"name": "", ...},
      "errors": [{"loc": ["name"],
                  "msg": "String should have at least 1 character"}] }
  ]
}
```

## Make it pass

Your done-signal is the spec — the stdout/report above is the warm-up. It **skips** until `import_csv.py` exists, then goes red → green.

```bash
pytest tests/test_lab06.py -v
```

Target: all of `TestImportCsv` green — the three buckets (`created` / `validation_errors` / `api_errors`) stay separated (a fake client stands in for the server).

## Common pitfalls
- `csv.DictReader` returns *every* value as a string. Pydantic v2 coerces `"true"` → `True` and `"1299"` → `1299` for you, but `"not-a-number"` won't coerce and will surface a clean error. **Don't pre-clean rows** — let Pydantic be the bouncer.
- Forgetting `start=2` on `enumerate` — your "row number" in the report becomes wrong by one because the header is row 1.
- Catching `Exception` instead of `ValidationError` / `APIError` will mask real bugs in your code.
- Writing the report inside the `with open` block — fine for small files, but if Pydantic raises and you forget `continue`, you might write a half-built report.

## Stretch (optional)
- Read CSV in chunks via `itertools.islice` if you ever need to import 100k rows.
- Print a per-category summary at the end (`created` grouped by category) using `Counter`.
- Add an `--update` flag: on duplicate id (409), retry with PATCH instead of giving up.

---

**End of Day 2.** Your working folder is now the input for Day 3 — your
checkpoint matches `project/checkpoints/day-3-start/`.
