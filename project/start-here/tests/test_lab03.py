"""Lab 3 spec — the `@retry` / `@log_calls` decorators + the FastAPI server.

    pytest tests/test_lab03.py -v

The server tests drive the app in-process with FastAPI's TestClient (no
uvicorn, no curl). Decorator tests skip until `catalog/decorators.py` exists;
server tests skip until `catalog/server.py` exists.
"""

from __future__ import annotations

import pytest


class TestDecorators:
    def test_retry_succeeds_after_transient_failures(self):
        dec = pytest.importorskip("catalog.decorators")
        calls = {"n": 0}

        @dec.retry(times=3, delay=0.0)
        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ValueError("boom")
            return "ok"

        assert flaky() == "ok"
        assert calls["n"] == 3

    def test_retry_reraises_after_exhausting_attempts(self):
        dec = pytest.importorskip("catalog.decorators")

        @dec.retry(times=2, delay=0.0)
        def always_fails():
            raise ValueError("nope")

        with pytest.raises(ValueError):
            always_fails()

    def test_log_calls_preserves_function_identity(self):
        dec = pytest.importorskip("catalog.decorators")

        @dec.log_calls
        def add(a, b):
            return a + b

        assert add.__name__ == "add"  # proves functools.wraps was used
        assert add(2, 3) == 5


class TestServer:
    @pytest.fixture
    def client(self):
        pytest.importorskip("catalog.server")
        testclient = pytest.importorskip("fastapi.testclient")
        from catalog.server import app

        return testclient.TestClient(app)

    def test_health_reports_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_list_returns_seeded_products(self, client):
        r = client.get("/products")
        assert r.status_code == 200
        assert len(r.json()) == 5

    def test_get_missing_id_is_404(self, client):
        assert client.get("/products/999").status_code == 404

    def test_create_then_duplicate_is_409(self, client):
        payload = {"id": 99, "name": "Test", "category": "Misc", "price": 42.0}
        assert client.post("/products", json=payload).status_code == 201
        assert client.post("/products", json=payload).status_code == 409
