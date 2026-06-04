# Lab 1 — The `Product` Foundation

**Duration:** ~80 min · **Day:** 1 · **Module:** 1 (Python Core)

> **Concepts used:** classes, `self` & `@dataclass` → `codealong/module-3.ipynb`; dict storage, functions & exceptions → `codealong/module-1.ipynb`.
> This lab applies the module's `BankAccount` concepts to the course's `Product` domain — same patterns, different thing (the deliberate concept-vs-lab seam).

## Goal
Build the in-memory core of the catalog: a `Product` representation and a
`ProductCatalog` collection you can add to, search, and list from a CLI.
Make it fail gracefully on bad input and log every operation. This is the
class that every Day 2/3/4 lab will extend — not throwaway code.

## You start with
- An empty `catalog/` package (just `__init__.py`)
- `pyproject.toml` already in place — `pip install -e ".[dev]"`

## You'll end with
- `catalog/models.py` defining `Product` (dataclass) and `ProductCatalog`
- `catalog/cli.py` exposing `list` and `add` subcommands (`search`/`save`/`load` arrive in Lab 2)
- Working `python -m catalog.cli list` printing seeded products

## Starter files

`starter/` holds the two files you build this lab. Copy them into your working `catalog/` package, then fill the bodies marked `# TODO` — the signatures, docstrings, and argparse wiring are given. The shape is decided; the logic is yours.

```bash
cp ../labs/lab-01-product-foundation/starter/*.py catalog/   # run from my-catalog/
```

| File | You write |
|---|---|
| `starter/models.py` | `Product` dataclass fields + the `ProductCatalog` method bodies (`add`/`get`/`delete`/`list_all`/`__len__`) |
| `starter/cli.py` | the `cmd_list` / `cmd_add` bodies |

## Steps

1. **Create `catalog/models.py`.** Add a `CatalogError` exception and a `Product` dataclass with fields `id: int`, `name: str`, `category: str`, `price: float`, `in_stock: bool = True`, `tags: list[str] = field(default_factory=list)`.

2. **Add `ProductCatalog` to the same file.** Keep products in `self._items: dict[int, Product]`. Implement:
   - `add(product)` — raise `CatalogError` on duplicate id or negative price; log success.
   - `delete(product_id)` / `get(product_id)` — raise `CatalogError` if missing.
   - `list_all()` — return a list copy of values.
   - `__len__` for `len(catalog)`.

   ```python
   def add(self, product: Product) -> Product:
       if product.id in self._items:
           raise CatalogError(f"Product id {product.id} already exists")
       if product.price < 0:
           raise CatalogError(f"Price must be non-negative (got {product.price})")
       self._items[product.id] = product
       logger.info("added product id=%s name=%r", product.id, product.name)
       return product
   ```

3. **Create `catalog/cli.py`.** Use `argparse` with subparsers. Seed the catalog with 5 demo products so `list` shows something on first run. Hook each subcommand to a `cmd_xxx(args)` function that returns an int exit code.

4. **Wire `if __name__ == "__main__": raise SystemExit(main())`** so `python -m catalog.cli list` works.

5. **Run it.** Try `list`, then add an invalid product (negative price) and observe the error.

## Expected output

```
$ python -m catalog.cli list
INFO: added product id=1 name='USB-C Cable'
INFO: added product id=2 name='Mechanical Keyboard'
INFO: added product id=3 name='Steel Water Bottle'
INFO: added product id=4 name='Yoga Mat'
INFO: added product id=5 name='Bluetooth Speaker'
    1  USB-C Cable                  Electronics    ₹  499.00  in stock
    2  Mechanical Keyboard          Electronics    ₹ 5499.00  in stock
    3  Steel Water Bottle           Home           ₹  899.00  in stock
    4  Yoga Mat                     Fitness        ₹ 1299.00  OOS
    5  Bluetooth Speaker            Electronics    ₹ 2499.00  in stock

5 products
```

## Make it pass

Your real done-signal is the spec test — the visual output above is the warm-up.

```bash
pytest tests/test_lab01.py -v
```

It **skips** until `catalog/models.py` exists, then goes red until your bodies are right, then green. Target: all of `TestProduct` + `TestProductCatalog` green. (`test_tags_are_not_shared_between_instances` is the mutable-default trap from the pitfalls below — it stays red if you write `tags: list = []`.)

## Common pitfalls
- Using a `list` instead of a `dict` for storage — every lookup becomes O(n) and the duplicate-id check gets clunky.
- Mutable default args: `tags: list[str] = []` on a dataclass field will share the list across instances. Use `field(default_factory=list)`.
- Not configuring logging — calling `logger.info(...)` without `logging.basicConfig(...)` prints nothing.

## Stretch (optional)
- Add a `summary()` method that returns `{"count": int, "total_value": float, "categories": int}`.
- Make `Product` immutable with `@dataclass(frozen=True)` and see what breaks in `ProductCatalog`.
