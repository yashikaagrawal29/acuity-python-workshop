"""Unit tests for the ProductCatalog collection class."""

from __future__ import annotations

import pytest

from catalog.models import CatalogError, Product, ProductCatalog, ProductUpdate


class TestProductCatalog:
    def test_starts_empty(self):
        c = ProductCatalog()
        assert len(c) == 0
        assert c.list_all() == []

    def test_add_and_get(self, seeded_catalog: ProductCatalog):
        got = seeded_catalog.get(10)
        assert got.name == "Cable"

    def test_add_rejects_duplicate_id(self, seeded_catalog: ProductCatalog):
        dup = Product(id=10, name="dup", category="x", price=1.0)
        with pytest.raises(CatalogError, match="already exists"):
            seeded_catalog.add(dup)

    def test_get_missing_raises(self, seeded_catalog: ProductCatalog):
        with pytest.raises(CatalogError, match="not found"):
            seeded_catalog.get(999)

    def test_delete(self, seeded_catalog: ProductCatalog):
        removed = seeded_catalog.delete(10)
        assert removed.id == 10
        assert len(seeded_catalog) == 2

    def test_delete_missing_raises(self, seeded_catalog: ProductCatalog):
        with pytest.raises(CatalogError):
            seeded_catalog.delete(999)


class TestQueries:
    def test_search_by_name_is_case_insensitive(self, seeded_catalog):
        hits = seeded_catalog.search_by_name("CABLE")
        assert {p.id for p in hits} == {10}

    def test_filter_by_price(self, seeded_catalog):
        cheap = seeded_catalog.filter_by_price(1000.0)
        assert {p.id for p in cheap} == {10}

    def test_group_by_category(self, seeded_catalog):
        groups = seeded_catalog.group_by_category()
        assert set(groups.keys()) == {"Electronics", "Fitness"}
        assert len(groups["Electronics"]) == 2


class TestUpdate:
    def test_partial_update_changes_only_supplied_fields(self, seeded_catalog):
        before = seeded_catalog.get(10)
        seeded_catalog.update(10, ProductUpdate(price=9.99))
        after = seeded_catalog.get(10)
        assert after.price == 9.99
        assert after.name == before.name
        assert after.category == before.category

    def test_update_missing_id_raises(self, seeded_catalog):
        with pytest.raises(CatalogError):
            seeded_catalog.update(999, ProductUpdate(price=1.0))
