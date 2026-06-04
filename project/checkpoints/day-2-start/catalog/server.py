"""FastAPI server exposing the Product Catalog (Day 1 Lab 3).

Day 1 ships with raw dict request/response shapes. On Day 2, these are
replaced with typed Pydantic models (Product, ProductCreate, ProductUpdate)
so the same routes get validation and OpenAPI docs for free.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException

from .models import CatalogError, Product, ProductCatalog
from .storage import seed_products

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Product Catalog", version="0.1.0")
catalog = ProductCatalog(list(seed_products()))


@app.get("/products")
def list_products() -> list[dict]:
    return [p.to_dict() for p in catalog.list_all()]


@app.get("/products/{product_id}")
def get_product(product_id: int) -> dict:
    try:
        return catalog.get(product_id).to_dict()
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/products", status_code=201)
def create_product(payload: dict) -> dict:
    try:
        product = Product(
            id=int(payload["id"]),
            name=str(payload["name"]),
            category=str(payload["category"]),
            price=float(payload["price"]),
            in_stock=bool(payload.get("in_stock", True)),
            tags=list(payload.get("tags") or []),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid product payload: {exc}")

    try:
        catalog.add(product)
    except CatalogError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return product.to_dict()


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int) -> None:
    try:
        catalog.delete(product_id)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "count": len(catalog)}
