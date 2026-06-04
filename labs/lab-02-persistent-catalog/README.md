# Lab 2 — Persistent Catalog

**Duration:** ~80 min · **Day:** 1 · **Module:** 2 (Data Structures, Files & Modules)

> **Concepts used:** containers & comprehensions, JSON/CSV persistence, modules → `codealong/module-2.ipynb`.
> This lab applies the module's `BankAccount` concepts to the course's `Product` domain — same patterns, different thing (the deliberate concept-vs-lab seam).

## Goal
Make the catalog survive process restart. Save it to CSV and JSON, load it
on startup, and add comprehension-driven queries (`search_by_name`,
`filter_by_price`, `group_by_category`). Split the code into modules so
storage doesn't bleed into models.

## You start with
- Your Lab 1 working folder (`catalog/models.py`, `catalog/cli.py`).

## You'll end with
- `catalog/storage.py` with `save_json`, `load_json`, `save_csv`, `load_csv`, `seed_products`
- New query methods on `ProductCatalog`: `search_by_name`, `filter_by_price`, `group_by_category`
- A `catalog.json` that persists across CLI invocations

## Starter files

You're **extending your Lab 1 folder**, not starting fresh.

**New file** — copy `starter/storage.py` into your `catalog/` package and fill the `# TODO`s:

```bash
cp ../labs/lab-02-persistent-catalog/starter/storage.py catalog/   # run from my-catalog/
```

**Edits to your existing `models.py`** — there's no starter for these (they go *inside* classes you already wrote). Add and fill these stubs:

```python
# on Product — the object⇄row boundary:
    def to_dict(self) -> dict:
        ...                       # TODO: a plain dict of all fields (dataclasses.asdict)

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        ...                       # TODO: parse a CSV-style row — values may be str;
                                  #       tags are "a|b|c", in_stock is "true"/"1"/"yes"

# on ProductCatalog — comprehension queries (one-liners):
    def search_by_name(self, term: str) -> list[Product]: ...   # case-insensitive substring
    def filter_by_price(self, max_price: float) -> list[Product]: ...   # price <= max
    def group_by_category(self) -> dict[str, list[Product]]: ...   # defaultdict(list)
```

Then update `cli.py`: swap the inline `SEED` for `seed_products()` and add `save` / `load` / `search` subcommands.

> **Why `to_dict` and `from_dict` aren't inverses:** JSON keeps `tags` as a list and reloads via `Product(**row)`; CSV flattens `tags` to a pipe-string and reloads via `from_dict`. Two formats, two paths — the spec test pins both.

## Hints (from `codealong/module-2.ipynb`)

- **`to_dict()`** → a dict of the fields (see the *JSON* section).
- **`from_dict(row)`** → CSV values are strings: `int(row["id"])`, `float(row["price"])`, `row["tags"].split("|")` (*CSV — rows in, rows out* section).
- **`save_json`** → `Path(path).write_text(json.dumps(rows, indent=2))` (*JSON* section).
- **`load_json`** → `json.loads(Path(path).read_text())` (*JSON* section).
- **`save_csv`** → `csv.DictWriter` + `writeheader()` + `writerow()`; open with `newline=""`.
- **`load_csv`** → `csv.DictReader` → `Product.from_dict(row)` (*CSV* section).
- **queries** → list comprehension with an `if`; `group_by_category` uses `defaultdict(list)`.

## Steps

1. **Add the comprehension queries to `ProductCatalog`.** Keep them tiny — that's the point.

   ```python
   def search_by_name(self, term: str) -> list[Product]:
       needle = term.lower()
       return [p for p in self._items.values() if needle in p.name.lower()]

   def filter_by_price(self, max_price: float) -> list[Product]:
       return [p for p in self._items.values() if p.price <= max_price]

   def group_by_category(self) -> dict[str, list[Product]]:
       groups: dict[str, list[Product]] = defaultdict(list)
       for p in self._items.values():
           groups[p.category].append(p)
       return dict(groups)
   ```

2. **Add `to_dict` / `from_dict` to `Product`.** These are the boundary between Python objects and JSON/CSV rows. CSV stores `tags` as a `|`-joined string; JSON keeps the list.

3. **Create `catalog/storage.py`.** Functions:
   - `save_json(catalog, path)` → write `[p.to_dict() for p in catalog.list_all()]` with `indent=2`.
   - `load_json(path)` → if file missing, log a warning and return an empty `ProductCatalog`. Otherwise read and rebuild.
   - `save_csv` / `load_csv` using `csv.DictWriter` / `csv.DictReader`.
   - `seed_products()` returning the 5 demo products from Lab 1 (move them out of `cli.py`).

4. **Update `cli.py`.** Replace the inline seed list with `seed_products()`. Add `save` and `load` subcommands. On startup, prefer `load_json(DEFAULT_PATH)` over the seed when the file exists.

5. **Try it.**
   ```bash
   python -m catalog.cli list             # seeds + saves catalog.json
   python -m catalog.cli add 10 "Notebook" Stationery 199
   python -m catalog.cli list             # 6 products now
   rm catalog.json
   python -m catalog.cli list             # back to 5 seeded
   ```

## Expected output

```
$ python -m catalog.cli list
INFO: added product id=1 name='USB-C Cable'
...
    5  Bluetooth Speaker            Electronics    ₹ 2499.00  in stock

5 products
```

After `add 10 "Notebook" Stationery 199`:

```
INFO: saved 6 products to catalog.json
```

## Make it pass

```bash
pytest tests/test_lab02.py -v
```

Target: `TestQueries`, `TestSerialization`, and `TestStorage` all green. `test_csv_roundtrip_preserves_pipe_tags` is the one that catches a `from_dict` that forgets to split on `|`.

## Common pitfalls
- Forgetting `from __future__ import annotations` (or `Optional[...]`) on Python 3.9 — `list[Product]` is a runtime error pre-3.10.
- Writing CSV without `newline=""` produces blank lines between rows on Windows.
- Forgetting `defaultdict(list)` and getting `KeyError` on first category.
- Saving on every `cli list` call accidentally overwrites a hand-edited file — only save after mutation (`add`, `delete`).

## Stretch (optional)
- Add `--format csv|json` flag to `save`/`load`.
- Implement `update_price(id, new_price)` and persist it.
