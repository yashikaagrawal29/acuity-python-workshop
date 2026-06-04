# Lab 3 — Decorators + Local API Server

**Duration:** ~80 min · **Day:** 1 · **Module:** 3 (OOP, Decorators, Type Hints, FastAPI)

> **Concepts used:** decorators (`@log_calls`, `@retry`) & the FastAPI `@app.get` route pattern → `codealong/module-3.ipynb`; the `Product` class & `.to_dict()` it serves → `catalog/models.py` from Labs 1–2.
> This lab applies the module's `BankAccount` decorator/route concepts to the course's `Product` domain — same patterns, different thing (the deliberate concept-vs-lab seam).

## Goal
**Decorators** are the real concept of Module 3 — a function that wraps another function
and returns a new one. Write two you'll reuse all week (`@retry`, `@log_calls`). Then meet
the payoff: **FastAPI is the same idea** — `@app.get("/products")` *registers* a function as
a route just like your decorators *wrap* one. With that, you stand up a real HTTP API
(`GET`/`POST`/`DELETE /products`, `GET /health`).

The decorator pattern returns on Day 3 (pytest fixtures) and Day 4 (agent tools); the
server is the artifact your agent will call.

## You start with
- Your Lab 2 working folder (`my-catalog/`) — `models.py` + `storage.py` already built.

## You'll end with
- `catalog/decorators.py` with `@retry(times, delay, exceptions)` and `@log_calls`
- `catalog/server.py` defining a FastAPI `app`
- A server running at `http://localhost:8000` that responds to curl

## Starter files

`starter/` holds the two new files for this lab. Copy them into your `catalog/` package and fill the `# TODO`s:

```bash
cp ../labs/lab-03-local-api-server/starter/*.py catalog/   # run from my-catalog/
```

| File | You write |
|---|---|
| `starter/decorators.py` | the `log_calls` + `retry` wrapper bodies (`functools.wraps` is already there — Day-3 tests assert `__name__` survives) |
| `starter/server.py` | the five route bodies; map `CatalogError` → 404 (missing) / 409 (duplicate) / 400 (bad payload) |

> Routes return `.to_dict()`, **not** the `Product` dataclass — FastAPI can't serialize a dataclass directly on Day 1. Day 2 fixes this by making `Product` a Pydantic model.

## Hints (from `codealong/module-3.ipynb`)

- **A decorator is just** `greet = log_calls(greet)` — take a function, wrap it, return the wrapper (*what a decorator is* section).
- **`@log_calls`** → `def wrapper(*args, **kwargs): ...; return func(*args, **kwargs)`; add `@functools.wraps(func)` so `__name__` survives (*what a decorator is* section).
- **`@retry`** → it's a decorator *with config*: loop `for attempt in range(1, times + 1)`, `try` the call, re-raise on the last attempt (*`@retry(times=3)`* section).
- **`@app.get("/products")`** → the **same pattern**: it *registers* the function as a route, exactly like the tiny `routes = {}` demo (*FastAPI is decorators in action* section). Return a `dict`/`list` and FastAPI makes it JSON.
- **Errors** → wrap the catalog call in `try/except CatalogError` and `raise HTTPException(status_code=...)`.

## Steps

1. **Create `catalog/decorators.py`.** Two decorators. Use `functools.wraps` so
   wrapped function metadata is preserved (pytest fixtures on Day 3 depend on this).

   ```python
   def retry(times: int = 3, delay: float = 0.1,
             exceptions: tuple[type[BaseException], ...] = (Exception,)):
       def decorator(func):
           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               last_exc = None
               for attempt in range(1, times + 1):
                   try:
                       return func(*args, **kwargs)
                   except exceptions as exc:
                       last_exc = exc
                       logger.warning("%s attempt %d/%d failed: %s",
                                      func.__name__, attempt, times, exc)
                       if attempt < times:
                           time.sleep(delay)
               raise last_exc
           return wrapper
       return decorator
   ```

   `@log_calls` is simpler: log the call, run it, log the return (or exception).

2. **Quick sanity check the decorators** before touching FastAPI:

   ```python
   @retry(times=3, delay=0.01)
   def flaky():
       ...  # raise twice, succeed on third
   ```

3. **Create `catalog/server.py`.** Boot one shared `ProductCatalog` from `seed_products()` at import time. Then declare routes:

   ```python
   app = FastAPI(title="Product Catalog", version="0.1.0")
   catalog = ProductCatalog(list(seed_products()))

   @app.get("/products")
   def list_products() -> list[dict]:
       return [p.to_dict() for p in catalog.list_all()]
   ```

4. **Map `CatalogError` to HTTP codes.** Missing id → 404, duplicate id → 409, bad payload → 400. Wrap each route's mutation in a `try/except CatalogError` and raise `HTTPException`.

5. **Run the server.**
   ```bash
   uvicorn catalog.server:app --reload
   ```

   Then in another terminal:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/products
   curl -X POST http://localhost:8000/products \
        -H 'Content-Type: application/json' \
        -d '{"id":99,"name":"Test","category":"Misc","price":42.0}'
   curl -X DELETE http://localhost:8000/products/99
   ```

6. **Visit `http://localhost:8000/docs`** — FastAPI generated this Swagger UI from your type hints. That's the "decorators are FastAPI" lesson made visible.

## Expected output

```
$ curl http://localhost:8000/health
{"status":"ok","count":5}

$ curl http://localhost:8000/products/2
{"id":2,"name":"Mechanical Keyboard","category":"Electronics","price":5499.0,"in_stock":true,"tags":["keyboard","mech"]}

$ curl -X POST http://localhost:8000/products \
       -H 'Content-Type: application/json' \
       -d '{"id":99,"name":"Test","category":"Misc","price":42.0}'
{"id":99,"name":"Test","category":"Misc","price":42.0,"in_stock":true,"tags":[]}
```

Duplicate POST and missing GET:

```
$ curl -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/products \
       -H 'Content-Type: application/json' \
       -d '{"id":99,"name":"Dup","category":"X","price":1.0}'
409
$ curl -o /dev/null -w '%{http_code}\n' http://localhost:8000/products/999
404
```

## Make it pass

```bash
pytest tests/test_lab03.py -v
```

`TestServer` uses FastAPI's `TestClient` — it drives `app` in-process, so the spec runs without uvicorn or curl. Target: `TestDecorators` + `TestServer` green. Then run the **whole day** green at once:

```bash
pytest -v        # all 26 Day-1 specs across lab 01–03
```

## Common pitfalls
- Port already in use — change with `--port 8001` or kill the previous uvicorn.
- Returning a `Product` (dataclass) directly from a route — FastAPI will
  fail to serialize. Either call `.to_dict()` (Day 1) or use Pydantic (Day 2).
- Forgetting `--reload` and wondering why edits don't take effect.
- Not catching `CatalogError`: a duplicate POST will return 500 instead of 409.

## Stretch (optional)
- Add `PATCH /products/{id}/price` that takes `{"price": float}` and updates the existing product.
- Decorate one of the routes with `@log_calls` and watch every request show up in logs.

---

**End of Day 1.** Your working folder is now the input for Day 2 — your
checkpoint matches `project/checkpoints/day-2-start/`.
