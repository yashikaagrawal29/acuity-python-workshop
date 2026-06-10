from __future__ import annotations

from catalog.storage import load_csv, load_json, save_csv, save_json, seed_products


def test_json_roundtrip(tmp_path, seeded_catalog):
    path = tmp_path / "catalog.json"
    save_json(seeded_catalog, path)
    loaded = load_json(path)
    assert [p.model_dump() for p in loaded.list_all()] == [
        p.model_dump() for p in seeded_catalog.list_all()
    ]


def test_load_json_missing_file_returns_empty(tmp_path):
    loaded = load_json(tmp_path / "missing.json")
    assert len(loaded) == 0


def test_csv_roundtrip(tmp_path, seeded_catalog):
    path = tmp_path / "catalog.csv"
    save_csv(seeded_catalog, path)
    loaded = load_csv(path)
    assert [p.model_dump() for p in loaded.list_all()] == [
        p.model_dump() for p in seeded_catalog.list_all()
    ]


def test_load_csv_missing_file_returns_empty(tmp_path):
    loaded = load_csv(tmp_path / "missing.csv")
    assert len(loaded) == 0


def test_seed_products_has_unique_ids():
    products = list(seed_products())
    ids = [p.id for p in products]
    assert len(products) > 0
    assert len(ids) == len(set(ids))
