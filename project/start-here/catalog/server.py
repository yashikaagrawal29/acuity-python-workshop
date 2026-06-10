"""FastAPI server — Day 2 Lab 4: typed with Pydantic.

Day 1 shipped raw `dict` request/response shapes. Now the same routes take
and return Pydantic models, so FastAPI validates the body (422 on bad input)
and renders the schema into `/docs` automatically. Fill every `# TODO`.

The catalog is booted once at import time (unchanged from Day 1).

Run:  uvicorn catalog.server:app --reload
Done-signal: a bad POST → 422 with field-level errors; PATCH updates a field
(README → Expected output).
Concepts: codealong/module-4.ipynb (§"FastAPI + Pydantic free /docs").
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from .models import (
    CatalogError,
    Product,
    ProductCatalog,
    ProductCreate,
    ProductUpdate,
)
from .storage import seed_products

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Product Catalog", version="0.2.0")
catalog = ProductCatalog(list(seed_products()))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "count": len(catalog)}


# TODO: add `response_model=Product` so responses are serialised THROUGH the
#       read model (extra fields stripped, schema shown in /docs).
@app.get("/products", response_model=list[Product])
def list_products() -> list[Product]:
    return catalog.list_all()


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int) -> Product:
    try:
        return catalog.get(product_id)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/products", status_code=201, response_model=Product)
def create_product(payload: ProductCreate) -> Product:
    # TODO: FastAPI already validated `payload` against ProductCreate (422 on
    #       bad input — no manual parsing!). Build a Product and add it.
    #   try: return catalog.add(Product(**payload.model_dump()))
    #   except CatalogError as exc: raise HTTPException(status_code=409, detail=str(exc))
    try:
        return catalog.add(Product(**payload.model_dump()))
    except CatalogError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.patch("/products/{product_id}", response_model=Product)
def update_product(product_id: int, patch: ProductUpdate) -> Product:
    # TODO: apply a partial update via the catalog (404 if the id is missing).
    #   try: return catalog.update(product_id, patch)
    #   except CatalogError as exc: raise HTTPException(status_code=404, detail=str(exc))
    try:
        return catalog.update(product_id, patch)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int) -> None:
    try:
        catalog.delete(product_id)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
