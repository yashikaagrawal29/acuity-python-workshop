from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

import catalog.import_csv as import_csv_module
from catalog.client import APIError
from catalog.models import Product


def _write_csv(path, rows: list[str]) -> None:
    path.write_text(
        "id,name,category,price,in_stock,tags\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def test_import_csv_tracks_created_validation_and_api_errors(tmp_path):
    csv_path = tmp_path / "products.csv"
    _write_csv(
        csv_path,
        [
            "101,Keyboard,Electronics,5499,true,keyboard|mech",
            "102,BadPrice,Electronics,-10,true,broken",
            "103,Duplicate,Electronics,100,true,dup",
        ],
    )

    client = MagicMock()
    client.create_product.side_effect = [
        Product(id=101, name="Keyboard", category="Electronics", price=5499.0),
        APIError(409, "already exists"),
    ]

    report = import_csv_module.import_csv(csv_path, client)

    assert report["summary"] == {
        "rows_read": 3,
        "created": 1,
        "validation_errors": 1,
        "api_errors": 1,
    }
    assert client.create_product.call_count == 2
    assert report["api_errors"][0]["status"] == 409


def test_main_returns_2_when_server_unreachable(tmp_path, monkeypatch):
    csv_path = tmp_path / "products.csv"
    _write_csv(csv_path, [])

    class FailingClient:
        def __init__(self, base_url):
            self.base_url = base_url

        def health(self):
            raise RuntimeError("down")

    monkeypatch.setattr(import_csv_module, "APIClient", FailingClient)
    code = import_csv_module.main([str(csv_path)])
    assert code == 2


def test_main_writes_report_and_returns_0(tmp_path, monkeypatch):
    csv_path = tmp_path / "products.csv"
    report_path = tmp_path / "report.json"
    _write_csv(csv_path, [])

    fake_client = MagicMock()
    fake_client.health.return_value = {"status": "ok"}

    monkeypatch.setattr(import_csv_module, "APIClient", lambda base_url: fake_client)
    monkeypatch.setattr(
        import_csv_module,
        "import_csv",
        lambda csv, client: {
            "source": str(csv),
            "summary": {"rows_read": 0, "created": 0, "validation_errors": 0, "api_errors": 0},
            "created": [],
            "validation_errors": [],
            "api_errors": [],
        },
    )

    code = import_csv_module.main([str(csv_path), "--report", str(report_path)])
    assert code == 0
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved["summary"]["created"] == 0
