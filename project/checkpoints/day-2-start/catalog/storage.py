"""CSV + JSON persistence for the catalog (Day 1 Lab 2)."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from .models import Product, ProductCatalog

logger = logging.getLogger(__name__)


# ---- JSON ----

def save_json(catalog: ProductCatalog, path: str | Path) -> None:
    path = Path(path)
    payload = [p.to_dict() for p in catalog.list_all()]
    path.write_text(json.dumps(payload, indent=2))
    logger.info("saved %d products to %s", len(payload), path)


def load_json(path: str | Path) -> ProductCatalog:
    path = Path(path)
    if not path.exists():
        logger.warning("no catalog file at %s, starting empty", path)
        return ProductCatalog()
    raw = json.loads(path.read_text())
    products = [Product(**row) for row in raw]
    logger.info("loaded %d products from %s", len(products), path)
    return ProductCatalog(products)


# ---- CSV ----

CSV_FIELDS = ["id", "name", "category", "price", "in_stock", "tags"]


def save_csv(catalog: ProductCatalog, path: str | Path) -> None:
    path = Path(path)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for p in catalog.list_all():
            row = p.to_dict()
            row["tags"] = "|".join(row.get("tags") or [])
            writer.writerow(row)
    logger.info("saved %d products to %s", len(catalog), path)


def load_csv(path: str | Path) -> ProductCatalog:
    path = Path(path)
    if not path.exists():
        logger.warning("no csv file at %s, starting empty", path)
        return ProductCatalog()
    with path.open() as fh:
        reader = csv.DictReader(fh)
        products = [Product.from_dict(row) for row in reader]
    logger.info("loaded %d products from %s", len(products), path)
    return ProductCatalog(products)


# ---- seed data ----

def seed_products() -> Iterable[Product]:
    """Demo data used to boot the server with something visible."""
    return [
        Product(1, "USB-C Cable", "Electronics", 499.0, True, ["cable", "usb-c"]),
        Product(2, "Mechanical Keyboard", "Electronics", 5499.0, True, ["keyboard", "mech"]),
        Product(3, "Steel Water Bottle", "Home", 899.0, True, ["bottle", "steel"]),
        Product(4, "Yoga Mat", "Fitness", 1299.0, False, ["mat", "yoga"]),
        Product(5, "Bluetooth Speaker", "Electronics", 2499.0, True, ["speaker", "bt"]),
    ]
