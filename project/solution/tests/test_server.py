from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import catalog.server as server_module
from catalog.models import Product, ProductCatalog, ProductUpdate


def _seeded_for_api() -> ProductCatalog:
    return ProductCatalog(
        [
            Product(id=1, name="Cable", category="Electronics", price=499.0),
            Product(id=2, name="Mat", category="Fitness", price=1299.0, in_stock=False),
        ]
    )


def _client_with_fresh_catalog(monkeypatch) -> TestClient:
    monkeypatch.setattr(server_module, "catalog", _seeded_for_api())
    return TestClient(server_module.app)


def test_health_endpoint(monkeypatch):
    client = _client_with_fresh_catalog(monkeypatch)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["count"] == 2


def test_create_duplicate_returns_409(monkeypatch):
    client = _client_with_fresh_catalog(monkeypatch)
    resp = client.post(
        "/products",
        json={"id": 1, "name": "Dup", "category": "Electronics", "price": 100.0},
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


def test_create_invalid_payload_returns_422(monkeypatch):
    client = _client_with_fresh_catalog(monkeypatch)
    resp = client.post(
        "/products",
        json={"id": 99, "name": "", "category": "Electronics", "price": -1},
    )
    assert resp.status_code == 422


def test_update_and_delete_roundtrip(monkeypatch):
    client = _client_with_fresh_catalog(monkeypatch)

    patch = ProductUpdate(price=999.0).model_dump(exclude_unset=True)
    updated = client.patch("/products/1", json=patch)
    assert updated.status_code == 200
    assert updated.json()["price"] == pytest.approx(999.0)

    deleted = client.delete("/products/1")
    assert deleted.status_code == 204

    missing = client.get("/products/1")
    assert missing.status_code == 404
