"""Lab 5 spec — the typed `APIClient` over an injected session.

    pytest tests/test_lab05.py -v

Your self-check for Lab 5. Skips until `catalog/client.py` exists. Uses a
tiny fake session — the same dependency-injection seam your client is built
around — so no live server is needed (Day 3 turns this into real mocking).
"""

from __future__ import annotations

import pytest


class _FakeResponse:
    """Mimics the bits of requests.Response the client touches."""

    def __init__(self, status_code: int, json_body):
        self.status_code = status_code
        self._json = json_body
        self.text = str(json_body)
        self.reason = "fake"

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def json(self):
        return self._json


class _FakeSession:
    """Returns queued outcomes in order; an Exception in the queue is raised
    (lets us simulate a transient network failure for the @retry check)."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.headers = {}
        self.calls = 0

    def request(self, method, url, **kwargs):
        self.calls += 1
        item = self._outcomes.pop(0) if len(self._outcomes) > 1 else self._outcomes[0]
        if isinstance(item, Exception):
            raise item
        return item


PRODUCTS = [
    {"id": 1, "name": "Cable", "category": "Electronics",
     "price": 499.0, "in_stock": True, "tags": ["usb"]},
    {"id": 2, "name": "Keyboard", "category": "Electronics",
     "price": 5499.0, "in_stock": True, "tags": ["mech"]},
]


class TestAPIClient:
    def test_apierror_exposes_status_and_detail(self):
        c = pytest.importorskip("catalog.client")
        err = c.APIError(404, "not found")
        assert err.status_code == 404 and err.detail == "not found"

    def test_list_products_returns_typed_models(self):
        c = pytest.importorskip("catalog.client")
        models = pytest.importorskip("catalog.models")
        client = c.APIClient(session=_FakeSession([_FakeResponse(200, PRODUCTS)]))
        result = client.list_products()
        assert all(isinstance(p, models.Product) for p in result)  # not raw dicts
        assert [p.id for p in result] == [1, 2]

    def test_non_2xx_raises_apierror(self):
        c = pytest.importorskip("catalog.client")
        client = c.APIClient(session=_FakeSession([_FakeResponse(409, {"detail": "dup"})]))
        with pytest.raises(c.APIError) as excinfo:
            client.list_products()
        assert excinfo.value.status_code == 409

    def test_retry_recovers_from_transient_error(self):
        c = pytest.importorskip("catalog.client")
        pytest.importorskip("catalog.models")
        import requests

        session = _FakeSession(
            [
                requests.ConnectionError("boom"),
                requests.ConnectionError("boom"),
                _FakeResponse(200, PRODUCTS),
            ]
        )
        result = c.APIClient(session=session).list_products()
        assert len(result) == 2
        assert session.calls == 3  # proves @retry wraps _request (2 fails + 1 ok)
