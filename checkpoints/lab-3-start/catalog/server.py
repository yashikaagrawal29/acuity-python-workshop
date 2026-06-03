"""FastAPI server exposing the Product Catalog (Day 1 Lab 3).

One shared catalog is booted at import time. Each route maps CatalogError to an
HTTP code: missing id -> 404, duplicate id -> 409, bad payload -> 400. Routes
return `.to_dict()`, NOT the Product dataclass — FastAPI can't serialize a
dataclass directly on Day 1 (Day 2 fixes this with Pydantic).

Run:  uvicorn catalog.server:app --reload
Done-signal: the TestServer class in `tests/test_lab03.py`.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from .models import CatalogError, Product, ProductCatalog
from .storage import seed_products

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Product Catalog", version="0.1.0")
catalog = ProductCatalog(list(seed_products()))

# hint (notebook §10): @app.get(path) REGISTERS this function as a route — same idea as the
#                      tiny routes={} demo. Return a dict/list and FastAPI turns it into JSON.


@app.get("/health")
def health() -> dict:
    # TODO: {"status": "ok", "count": <how many products>}
    ...


@app.get("/products")
def list_products() -> list[dict]:
    # TODO: every product as a dict
    ...


@app.get("/products/{product_id}")
def get_product(product_id: int) -> dict:
    # TODO: return it, or HTTPException(404) on CatalogError
    # hint: try: return catalog.get(product_id).to_dict()  except CatalogError as e: raise HTTPException(404, str(e))
    ...


@app.post("/products", status_code=201)
def create_product(payload: dict) -> dict:
    # TODO: build a Product from payload (400 on bad payload),
    #       catalog.add (409 on duplicate), return the new product
    # hint: Product(**payload) (bad payload -> HTTPException(400)); catalog.add (CatalogError -> 409)
    ...


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int) -> None:
    # TODO: catalog.delete, or HTTPException(404)
    ...
