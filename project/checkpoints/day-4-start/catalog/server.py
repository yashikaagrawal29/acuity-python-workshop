"""FastAPI server exposing the Product Catalog.

Day 1 shipped with raw `dict` payloads. Day 2 (here) replaces them with
Pydantic models — same routes, but now FastAPI validates inputs against
the schema, generates richer OpenAPI docs, and returns typed JSON.
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
    # ProductCreate has already been validated by FastAPI.
    product = Product(**payload.model_dump())
    try:
        return catalog.add(product)
    except CatalogError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.patch("/products/{product_id}", response_model=Product)
def update_product(product_id: int, patch: ProductUpdate) -> Product:
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "count": len(catalog)}
