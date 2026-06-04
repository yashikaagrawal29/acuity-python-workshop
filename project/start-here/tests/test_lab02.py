"""Lab 2 spec — comprehension queries, dict (de)serialization, persistence.

    pytest tests/test_lab02.py -v

Note the split: `to_dict` is the JSON shape (tags stay a list); `from_dict`
parses a CSV-style row (tags are a `|`-joined string). They are NOT inverses
of each other — JSON round-trips via `Product(**row)`, CSV via `from_dict`.
"""

from __future__ import annotations

import pytest

pytest.importorskip("catalog.models")
from catalog.models import Product


class TestQueries:
    def test_search_by_name_is_case_insensitive(self, seeded_catalog):
        assert {p.id for p in seeded_catalog.search_by_name("CABLE")} == {10}

    def test_filter_by_price(self, seeded_catalog):
        assert {p.id for p in seeded_catalog.filter_by_price(1000.0)} == {10}

    def test_group_by_category(self, seeded_catalog):
        groups = seeded_catalog.group_by_category()
        assert set(groups) == {"Electronics", "Fitness"}
        assert len(groups["Electronics"]) == 2


class TestSerialization:
    def test_to_dict_is_a_plain_dict(self):
        d = Product(1, "X", "c", 10.0, True, ["a", "b"]).to_dict()
        assert d["id"] == 1 and d["tags"] == ["a", "b"]

    def test_from_dict_parses_a_csv_row(self):
        p = Product.from_dict(
            {"id": "5", "name": "Y", "category": "c",
             "price": "9.5", "in_stock": "true", "tags": "a|b|c"}
        )
        assert p.id == 5 and p.in_stock is True and p.tags == ["a", "b", "c"]


class TestStorage:
    def test_json_roundtrip(self, tmp_path, seeded_catalog):
        storage = pytest.importorskip("catalog.storage")
        path = tmp_path / "catalog.json"
        storage.save_json(seeded_catalog, path)
        loaded = storage.load_json(path)
        assert {p.id for p in loaded.list_all()} == {10, 20, 30}

    def test_load_missing_file_returns_empty_catalog(self, tmp_path):
        storage = pytest.importorskip("catalog.storage")
        assert len(storage.load_json(tmp_path / "nope.json")) == 0

    def test_csv_roundtrip_preserves_pipe_tags(self, tmp_path, seeded_catalog):
        storage = pytest.importorskip("catalog.storage")
        path = tmp_path / "catalog.csv"
        storage.save_csv(seeded_catalog, path)
        loaded = storage.load_csv(path)
        assert loaded.get(10).tags == seeded_catalog.get(10).tags
