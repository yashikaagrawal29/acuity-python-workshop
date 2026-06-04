"""Tests for `catalog.client.APIClient`.

Two flavours of tests live here:

- Unit tests — `requests` is mocked via `pytest-mock`. Fast, no network.
- Integration tests — marked `@pytest.mark.integration`; they hit a real
  uvicorn process spun up by the `live_server` fixture.

Run only unit tests:        `pytest -m "not integration"`
Run only integration tests: `pytest -m integration`
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from catalog.client import APIClient, APIError
from catalog.models import Product, ProductCreate, ProductUpdate


# ============================================================
# Unit tests — `requests` is mocked
# ============================================================

@pytest.fixture
def client_with_mock_session() -> tuple[APIClient, MagicMock]:
    session = MagicMock(spec=requests.Session)
    client = APIClient(base_url="http://test.local", session=session)
    return client, session


def _mock_response(status: int, payload) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.ok = 200 <= status < 300
    resp.status_code = status
    resp.json.return_value = payload
    resp.text = str(payload)
    resp.reason = "OK" if resp.ok else "ERR"
    return resp


class TestSuccessfulCalls:
    def test_list_products_returns_typed_objects(self, client_with_mock_session):
        client, session = client_with_mock_session
        session.request.return_value = _mock_response(
            200,
            [{"id": 1, "name": "X", "category": "c", "price": 1.0,
              "in_stock": True, "tags": []}],
        )
        result = client.list_products()
        assert isinstance(result[0], Product)
        assert result[0].id == 1

    def test_create_product_sends_json_body(self, client_with_mock_session):
        client, session = client_with_mock_session
        session.request.return_value = _mock_response(
            201,
            {"id": 5, "name": "Y", "category": "c",
             "price": 9.5, "in_stock": True, "tags": []},
        )
        payload = ProductCreate(id=5, name="Y", category="c", price=9.5)
        client.create_product(payload)
        call = session.request.call_args
        assert call.args[0] == "POST"
        assert call.args[1].endswith("/products")
        assert call.kwargs["json"]["id"] == 5

    def test_update_product_only_sends_set_fields(self, client_with_mock_session):
        client, session = client_with_mock_session
        session.request.return_value = _mock_response(
            200,
            {"id": 5, "name": "Y", "category": "c",
             "price": 12.0, "in_stock": True, "tags": []},
        )
        client.update_product(5, ProductUpdate(price=12.0))
        sent_body = session.request.call_args.kwargs["json"]
        assert sent_body == {"price": 12.0}  # name/category/etc NOT sent


# ============================================================
# Error mapping — parametrized
# ============================================================

class TestErrorMapping:
    @pytest.mark.parametrize(
        "status,expected_substr",
        [
            (400, "400"),
            (404, "404"),
            (409, "409"),
            (422, "422"),
            (500, "500"),
        ],
    )
    def test_non_2xx_raises_api_error(self, client_with_mock_session,
                                       status, expected_substr):
        client, session = client_with_mock_session
        session.request.return_value = _mock_response(status, {"detail": "boom"})
        with pytest.raises(APIError) as exc:
            client.list_products()
        assert str(status) in str(exc.value)
        assert exc.value.status_code == status

    def test_retries_then_succeeds_on_network_blip(
        self, client_with_mock_session
    ):
        client, session = client_with_mock_session
        success = _mock_response(200, [])
        session.request.side_effect = [
            requests.ConnectionError("blip 1"),
            requests.ConnectionError("blip 2"),
            success,
        ]
        result = client.list_products()
        assert result == []
        assert session.request.call_count == 3

    def test_does_not_retry_on_4xx(self, client_with_mock_session):
        client, session = client_with_mock_session
        session.request.return_value = _mock_response(409, {"detail": "dup"})
        with pytest.raises(APIError):
            client.list_products()
        assert session.request.call_count == 1


# ============================================================
# Integration tests — talk to a real uvicorn process
# ============================================================

@pytest.mark.integration
class TestLiveServer:
    def test_health(self, live_server):
        client = APIClient(base_url=live_server)
        result = client.health()
        assert result["status"] == "ok"

    def test_full_crud_roundtrip(self, live_server):
        client = APIClient(base_url=live_server)
        new = ProductCreate(id=9001, name="IntegTest", category="QA", price=42.0)
        created = client.create_product(new)
        assert created.id == 9001

        patched = client.update_product(9001, ProductUpdate(price=99.0))
        assert patched.price == 99.0

        fetched = client.get_product(9001)
        assert fetched.price == 99.0

        client.delete_product(9001)
        with pytest.raises(APIError) as exc:
            client.get_product(9001)
        assert exc.value.status_code == 404
