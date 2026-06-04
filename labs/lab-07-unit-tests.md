# Lab 7 — Unit Tests for the Catalog Core

**Duration:** ~80 min · **Day:** 3 · **Module:** 1 (pytest basics + fixtures)

## Goal
Write the first real test suite for the catalog. Cover both the Pydantic
models from Day 2 *and* the `ProductCatalog` collection class. Use
**fixtures** to share setup, **classes** to group related tests,
**`pytest.raises`** to assert errors. By the end, `pytest -q` should
print green and you should be confident future edits won't silently
break Day 1/2 behaviour.

## You start with
- `project/checkpoints/day-3-start/` (Day 2 end-state) OR your own Lab 6 folder

## You'll end with
- `tests/conftest.py` with `sample_product` + `seeded_catalog` fixtures
- `tests/test_models.py` covering Product / ProductCreate / ProductUpdate
- `tests/test_catalog.py` covering add / get / delete / update / queries
- `pytest -q` green

## Steps

1. **Create `tests/__init__.py`** (empty) so pytest finds the package, and `tests/conftest.py` for shared fixtures:

   ```python
   import pytest
   from catalog.models import Product, ProductCatalog

   @pytest.fixture
   def sample_product() -> Product:
       return Product(id=1, name="Sample", category="Misc",
                      price=99.0, in_stock=True, tags=["sample"])

   @pytest.fixture
   def seeded_catalog() -> ProductCatalog:
       return ProductCatalog([
           Product(id=10, name="Cable",   category="Electronics", price=499.0),
           Product(id=11, name="Speaker", category="Electronics", price=2499.0),
           Product(id=12, name="Mat",     category="Fitness",     price=1299.0),
       ])
   ```

   Fixtures are **decorated functions that return values**. Pytest matches the function-name to the parameter-name and injects the return value.

2. **Write `tests/test_models.py`** with two classes:

   ```python
   class TestProductValidation:
       def test_valid_payload(self):
           p = Product(id=1, name="X", category="c", price=10.0)
           assert p.id == 1

       @pytest.mark.parametrize("field,value,err_substring", [
           ("name", "",  "at least 1 character"),
           ("price", -1, "greater than or equal to 0"),
           ("id",   0,   "greater than or equal to 1"),
       ])
       def test_rejects_invalid(self, field, value, err_substring):
           base = dict(id=1, name="X", category="c", price=10.0)
           base[field] = value
           with pytest.raises(ValidationError) as exc:
               Product(**base)
           assert err_substring in str(exc.value)
   ```

3. **Write `tests/test_catalog.py`** using the `seeded_catalog` fixture:

   ```python
   class TestProductCatalog:
       def test_add_rejects_duplicate_id(self, seeded_catalog):
           dup = Product(id=10, name="dup", category="x", price=1.0)
           with pytest.raises(CatalogError, match="already exists"):
               seeded_catalog.add(dup)

       def test_search_by_name_is_case_insensitive(self, seeded_catalog):
           hits = seeded_catalog.search_by_name("CABLE")
           assert {p.id for p in hits} == {10}
   ```

4. **Run it.**
   ```bash
   pytest -q
   pytest -v tests/test_models.py::TestProductValidation::test_rejects_invalid
   ```

5. **Notice fixture isolation.** Each test gets a *fresh* `seeded_catalog` — fixtures default to function scope. If you delete a product in one test it doesn't bleed into the next.

## Expected output

```
$ pytest -q
.................                                                        [100%]
17 passed in 0.5s

$ pytest -v tests/test_models.py
tests/test_models.py::TestProductValidation::test_valid_payload PASSED
tests/test_models.py::TestProductValidation::test_rejects_invalid[name-...] PASSED
tests/test_models.py::TestProductValidation::test_rejects_invalid[price--1-...] PASSED
...
```

## Common pitfalls
- Forgetting `tests/__init__.py` — works on some setups, blows up on others. Always include it.
- Sharing mutable state between tests via a module-level variable. Use fixtures.
- `pytest.raises(Exception)` catches *everything*, including `AssertionError`. Always pick the narrowest type.
- Forgetting `match=` on `pytest.raises` — your test passes even when the wrong error fires.
- Writing one test method that asserts five different things. Split them — one assertion per test gives precise failure messages.

## Stretch (optional)
- Add a `pytest-randomly` plugin and re-run. Any test that depends on order surfaces immediately.
- Add `tests/test_storage.py` that round-trips a catalog through JSON and back, asserting equality.
