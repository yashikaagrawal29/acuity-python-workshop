# Lab 4 — Pydantic Models for the Catalog

**Duration:** ~80 min · **Day:** 2 · **Module:** 1 (JSON + Pydantic)

> **Concepts used:** JSON round-trips, Pydantic v2 models & field validators → `codealong/module-4.ipynb`.
> This lab applies the module's `BankAccount` models to the course's `Product` domain — same patterns, different thing (the deliberate concept-vs-lab seam).

## Goal
Replace the raw `dict` payloads in your Day 1 FastAPI server with three
**Pydantic models** — `ProductCreate`, `ProductUpdate`, and a `Product`
read model. Same routes, same shapes, but now FastAPI validates inputs,
auto-generates a richer `/docs`, and returns typed JSON.

## You start with
- `project/checkpoints/day-2-start/` (Day 1 end-state) OR your own Lab 3 folder

## You'll end with
- `Product`, `ProductBase`, `ProductCreate`, `ProductUpdate` Pydantic models in `catalog/models.py`
- `server.py` routes annotated with `response_model=Product`
- A `PATCH /products/{id}` route powered by `ProductUpdate`
- Invalid POST returns **422** with a structured error body

## Starter files

`starter/` holds the two files you upgrade this lab. Copy them over your working `catalog/` package, then fill the bodies marked `# TODO` — the imports, model skeletons, and route wiring are given. The shape is decided; the logic is yours.

```bash
cp ../labs/lab-04-pydantic-models/starter/*.py catalog/   # run from my-catalog/
```

| File | You write |
|---|---|
| `starter/models.py` | the `ProductBase` fields + `@field_validator`, `ProductCreate.id`, the optional `ProductUpdate`, `Product.to_dict/from_dict`, and `ProductCatalog.update()` |
| `starter/server.py` | the `create_product` (POST) and `update_product` (PATCH) bodies |

## Steps

1. **Replace the dataclass `Product`.** In `catalog/models.py`, swap to Pydantic v2:

   ```python
   from pydantic import BaseModel, ConfigDict, Field, field_validator

   class ProductBase(BaseModel):
       name: str = Field(min_length=1, max_length=120)
       category: str = Field(min_length=1, max_length=60)
       price: float = Field(ge=0)
       in_stock: bool = True
       tags: list[str] = Field(default_factory=list)

   class ProductCreate(ProductBase):
       id: int = Field(ge=1)

   class Product(ProductBase):
       id: int = Field(ge=1)
   ```

2. **Add `ProductUpdate` with all fields optional.** Set `model_config = ConfigDict(extra="forbid")` so typos in the JSON body get rejected instead of silently ignored.

3. **Normalize CSV-style tags.** Bulk-import (Lab 6) will send `"a|b|c"` as a string. A `@field_validator("tags", mode="before")` turns it into a list:

   ```python
   @field_validator("tags", mode="before")
   @classmethod
   def _split_csv_tags(cls, v):
       if isinstance(v, str):
           return [t.strip() for t in v.split("|") if t.strip()]
       return v
   ```

4. **Fix every `Product(...)` call site** in `storage.py` and `cli.py`. Pydantic only accepts keyword args:

   ```python
   # before (dataclass)
   Product(1, "USB-C Cable", "Electronics", 499.0, True, ["cable", "usb-c"])
   # after (Pydantic)
   Product(id=1, name="USB-C Cable", category="Electronics", price=499.0,
           in_stock=True, tags=["cable", "usb-c"])
   ```

5. **Add an `.update()` method to `ProductCatalog`** that takes a `ProductUpdate` and applies it with `model_copy(update=patch.model_dump(exclude_unset=True))`.

6. **Annotate the FastAPI routes.**

   ```python
   @app.post("/products", status_code=201, response_model=Product)
   def create_product(payload: ProductCreate) -> Product:
       try:
           return catalog.add(Product(**payload.model_dump()))
       except CatalogError as exc:
           raise HTTPException(status_code=409, detail=str(exc))

   @app.patch("/products/{product_id}", response_model=Product)
   def update_product(product_id: int, patch: ProductUpdate) -> Product:
       try:
           return catalog.update(product_id, patch)
       except CatalogError as exc:
           raise HTTPException(status_code=404, detail=str(exc))
   ```

7. **Run the server and probe `/docs`.** The schema sidebar now shows three rich models with constraints. Try a deliberately bad POST.

## Expected output

```
$ curl -X POST http://localhost:8000/products \
       -H 'Content-Type: application/json' \
       -d '{"id":51,"name":"","category":"x","price":-1}'
HTTP/1.1 422 Unprocessable Entity
{
  "detail": [
    {"loc": ["body", "name"],  "msg": "String should have at least 1 character", ...},
    {"loc": ["body", "price"], "msg": "Input should be greater than or equal to 0", ...}
  ]
}
```

```
$ curl -X PATCH http://localhost:8000/products/2 \
       -H 'Content-Type: application/json' -d '{"price":4999.0}'
{"name":"Mechanical Keyboard","category":"Electronics","price":4999.0,"in_stock":true,"tags":["keyboard","mech"],"id":2}
```

## Make it pass

Your done-signal is the spec — the curl output above is the warm-up. It **skips** until you build the models, then goes red → green.

```bash
pytest tests/test_lab04.py -v
```

Target: all of `TestModels` + `TestServer` green (runs the API in-process — no server needed).

## Common pitfalls
- Pydantic v2 syntax differs from v1. Use `model_dump()` (not `.dict()`), `model_validate()` (not `.parse_obj()`), `model_copy(update=...)`.
- Forgetting to drop `from dataclasses import ...` leaves stale imports lingering.
- `Field(ge=0)` vs `Field(gt=0)` — `ge` allows zero. Pick consciously for `price`.
- A `@field_validator(..., mode="before")` runs **before** type coercion. Use `mode="after"` if you want to validate a parsed value.

## Stretch (optional)
- Add a `currency: str = "INR"` field with `pattern=r"^[A-Z]{3}$"`.
- Reject products whose `name` is `category` mis-typed as the name (e.g. name == "Electronics") using a `@model_validator(mode="after")`.
