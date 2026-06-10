"""Catalog data model — Day 2 Lab 4: dataclass → Pydantic v2.

Yesterday `Product` was a `@dataclass` (free `__init__`/`__repr__`, but NO
validation). Today it becomes a Pydantic model so the FastAPI server gets
input validation + a rich `/docs` for free. Fill every `# TODO`.

Four models, one resource (module-4, §"Multiple models, one resource"):
  ProductBase    — fields shared by all three
  ProductCreate  — POST body (caller also supplies `id`)
  ProductUpdate  — PATCH body (every field optional, `extra="forbid"`)
  Product        — read / storage model (has `id`, `to_dict`/`from_dict`)

Done-signal: a deliberately bad POST returns 422 with field-level errors,
and `PATCH /products/{id}` works (README → Expected output).
Concepts: codealong/module-4.ipynb (Pydantic models, Field constraints,
coercion, @field_validator).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class CatalogError(Exception):
    """Raised when a catalog operation fails (duplicate id, missing id, etc.)."""


class ProductBase(BaseModel):
    """Shared fields between create / update / read."""

    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=60)
    price: float = Field(ge=0)  # ge allows 0; gt would forbid free items
    in_stock: bool = True
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def _split_csv_tags(cls, v: object) -> object:
        if isinstance(v, str):
            return [t.strip() for t in v.split("|") if t.strip()]
        return v


class ProductCreate(ProductBase):
    """Payload for POST /products — caller must supply an id."""

    id: int = Field(ge=1)


class ProductUpdate(BaseModel):
    """Payload for PATCH /products/{id} — every field optional."""

    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category: Optional[str] = Field(default=None, min_length=1, max_length=60)
    price: Optional[float] = Field(default=None, ge=0)
    in_stock: Optional[bool] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)

class Product(ProductBase):
    """Catalog read model — includes the id."""

    id: int = Field(ge=1)

    def to_dict(self) -> dict:
        # hint (module-4): Pydantic v2 uses model_dump(), NOT the old v1 .dict()
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        # hint (module-4): cls.model_validate(data)  (replaces v1 parse_obj)
        return cls.model_validate(data)


class ProductCatalog:
    """In-memory product catalog keyed by product id. (Unchanged from Day 1
    except the new `update()` method below — it now holds Pydantic instances.)"""

    def __init__(self, products: Optional[list[Product]] = None) -> None:
        self._items: dict[int, Product] = {}
        for p in products or []:
            self.add(p)

    # ---- mutation ----

    def add(self, product: Product) -> Product:
        if product.id in self._items:
            raise CatalogError(f"Product id {product.id} already exists")
        self._items[product.id] = product
        logger.info("added product id=%s name=%r", product.id, product.name)
        return product

    def delete(self, product_id: int) -> Product:
        if product_id not in self._items:
            raise CatalogError(f"Product id {product_id} not found")
        removed = self._items.pop(product_id)
        logger.info("deleted product id=%s", product_id)
        return removed

    def update(self, product_id: int, patch: ProductUpdate) -> Product:
        existing = self.get(product_id)
        merged = existing.model_copy(update=patch.model_dump(exclude_unset=True))
        self._items[product_id] = merged
        return merged

    # ---- read ----

    def get(self, product_id: int) -> Product:
        if product_id not in self._items:
            raise CatalogError(f"Product id {product_id} not found")
        return self._items[product_id]

    def list_all(self) -> list[Product]:
        return list(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    # ---- comprehension-driven queries (from Day 1) ----

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
