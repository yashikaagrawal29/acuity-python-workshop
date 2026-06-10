"""CSV + JSON persistence for the catalog."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from .models import Product, ProductCatalog

logger = logging.getLogger(__name__)


CSV_FIELDS = ["id", "name", "category", "price", "in_stock", "tags"]


def save_json(catalog: ProductCatalog, path: str | Path) -> None:
    path = Path(path)
    payload = [p.to_dict() for p in catalog.list_all()]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("saved %d products to %s", len(payload), path)


def load_json(path: str | Path) -> ProductCatalog:
    path = Path(path)
    if not path.exists():
        logger.warning("no catalog file at %s, starting empty", path)
        return ProductCatalog()
    raw = json.loads(path.read_text(encoding="utf-8"))
    products = [Product(**row) for row in raw]
    logger.info("loaded %d products from %s", len(products), path)
    return ProductCatalog(products)


def save_csv(catalog: ProductCatalog, path: str | Path) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8", newline="") as fh:
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
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        products = [Product.from_dict(row) for row in reader]
    logger.info("loaded %d products from %s", len(products), path)
    return ProductCatalog(products)


def seed_products() -> Iterable[Product]:
    """Demo data used to boot the server with something visible."""
    return [
        Product(
            id=1,
            name="USB-C Cable",
            category="Electronics",
            price=499.0,
            in_stock=True,
            tags=["cable", "usb-c"],
        ),
        Product(
            id=2,
            name="Mechanical Keyboard",
            category="Electronics",
            price=5499.0,
            in_stock=True,
            tags=["keyboard", "mech"],
        ),
        Product(
            id=3,
            name="Steel Water Bottle",
            category="Home",
            price=899.0,
            in_stock=True,
            tags=["bottle", "steel"],
        ),
        Product(
            id=4,
            name="Yoga Mat",
            category="Fitness",
            price=1299.0,
            in_stock=False,
            tags=["mat", "yoga"],
        ),
        Product(
            id=5,
            name="Bluetooth Speaker",
            category="Electronics",
            price=2499.0,
            in_stock=True,
            tags=["speaker", "bt"],
        ),
    ]
