"""Lab 1 spec — the `Product` dataclass + `ProductCatalog` core.

This is your target. Run it and watch it fail, then make it green:

    pytest tests/test_lab01.py -v

Until you create `catalog/models.py` the whole module *skips* (not fails).
"""

from __future__ import annotations

import dataclasses

import pytest

pytest.importorskip("catalog.models")
from catalog.models import CatalogError, Product, ProductCatalog


class TestProduct:
    def test_is_a_dataclass_with_expected_fields(self):
        names = {f.name for f in dataclasses.fields(Product)}
        assert {"id", "name", "category", "price", "in_stock", "tags"} <= names

    def test_in_stock_defaults_true_and_tags_default_empty(self):
        p = Product(1, "X", "c", 10.0)
        assert p.in_stock is True
        assert p.tags == []

    def test_tags_are_not_shared_between_instances(self):
        # field(default_factory=list), NOT tags: list = []
        a, b = Product(1, "A", "c", 1.0), Product(2, "B", "c", 1.0)
        a.tags.append("x")
        assert b.tags == []


class TestProductCatalog:
    def test_starts_empty(self):
        c = ProductCatalog()
        assert len(c) == 0
        assert c.list_all() == []

    def test_add_and_get(self, seeded_catalog):
        assert seeded_catalog.get(10).name == "Cable"

    def test_len_counts_items(self, seeded_catalog):
        assert len(seeded_catalog) == 3

    def test_add_rejects_duplicate_id(self, seeded_catalog):
        with pytest.raises(CatalogError, match="already exists"):
            seeded_catalog.add(Product(10, "dup", "x", 1.0))

    def test_add_rejects_negative_price(self):
        with pytest.raises(CatalogError):
            ProductCatalog().add(Product(1, "X", "c", -1.0))

    def test_get_missing_raises(self, seeded_catalog):
        with pytest.raises(CatalogError, match="not found"):
            seeded_catalog.get(999)

    def test_delete_returns_removed_and_shrinks(self, seeded_catalog):
        assert seeded_catalog.delete(10).id == 10
        assert len(seeded_catalog) == 2

    def test_delete_missing_raises(self, seeded_catalog):
        with pytest.raises(CatalogError):
            seeded_catalog.delete(999)
