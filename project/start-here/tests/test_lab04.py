"""Lab 4 spec — Pydantic models + the typed FastAPI server.

    pytest tests/test_lab04.py -v

Your self-check for Lab 4. Tests **skip** until you build the Pydantic
models / upgrade the server, then go red → green. The server tests run the
app in-process with FastAPI's TestClient — no uvicorn, no curl.
"""

from __future__ import annotations

import pytest


def _models():
    """catalog.models once the Lab-4 Pydantic models exist, else skip."""
    m = pytest.importorskip("catalog.models")
    if not all(hasattr(m, n) for n in ("ProductCreate", "ProductUpdate")):
        pytest.skip("Pydantic models not built yet (Lab 4 steps 1–2)")
    return m


class TestModels:
    def test_coerces_string_numbers(self):
        m = _models()
        p = m.ProductCreate.model_validate(
            {"id": "1", "name": "Widget", "category": "Misc", "price": "9.50"}
        )
        assert p.id == 1 and p.price == 9.5  # CSV-style strings get coerced

    def test_rejects_empty_name_and_negative_price(self):
        m = _models()
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            m.ProductCreate.model_validate(
                {"id": 1, "name": "", "category": "x", "price": -5}
            )

    def test_tags_split_from_pipe_string(self):
        m = _models()
        p = m.ProductCreate.model_validate(
            {"id": 1, "name": "X", "category": "C", "price": 1, "tags": "a|b|c"}
        )
        assert p.tags == ["a", "b", "c"]  # @field_validator splits the CSV string

    def test_update_rejects_unknown_field(self):
        m = _models()
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            m.ProductUpdate.model_validate({"nope": 1})  # ConfigDict(extra="forbid")

    def test_update_is_partial(self):
        m = _models()
        patch = m.ProductUpdate.model_validate({"price": 12.0})
        # only the field the caller set is emitted — the rest stay untouched
        assert patch.model_dump(exclude_unset=True) == {"price": 12.0}

    def test_catalog_update_applies_patch(self):
        m = _models()
        cat = m.ProductCatalog([m.Product(id=1, name="A", category="C", price=10.0)])
        updated = cat.update(1, m.ProductUpdate(price=99.0))
        assert updated.price == 99.0 and updated.name == "A"  # merged, not replaced


class TestServer:
    @pytest.fixture
    def client(self):
        _models()  # skip the whole class until Lab-4 models are built
        pytest.importorskip("catalog.server")
        testclient = pytest.importorskip("fastapi.testclient")
        from catalog.server import app

        return testclient.TestClient(app)

    def test_bad_post_is_422(self, client):
        r = client.post(
            "/products",
            json={"id": 51, "name": "", "category": "x", "price": -1},
        )
        assert r.status_code == 422  # Pydantic rejects bad input at the boundary

    def test_patch_updates_one_field(self, client):
        r = client.patch("/products/1", json={"price": 4999.0})
        assert r.status_code == 200
        assert r.json()["price"] == 4999.0

    def test_patch_missing_id_is_404(self, client):
        assert client.patch("/products/999", json={"price": 1.0}).status_code == 404
