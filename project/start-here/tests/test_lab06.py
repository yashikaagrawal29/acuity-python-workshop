"""Lab 6 spec — the CSV → API bulk-import workflow + report.

    pytest tests/test_lab06.py -v

Your self-check for Lab 6. Skips until `catalog/import_csv.py` exists. A fake
client stands in for the server; validation errors come from the *real*
Pydantic `ProductCreate`, so the three report buckets are exercised for real.
"""

from __future__ import annotations

import textwrap

import pytest


class _FakeClient:
    """Stand-in for APIClient: accepts creates, raises APIError on a dup id."""

    def __init__(self, dup_ids=()):
        self._dup = set(dup_ids)
        self.created = []

    def health(self):
        return {"status": "ok"}

    def create_product(self, payload):
        from catalog.client import APIError

        if payload.id in self._dup:
            raise APIError(409, f"Product id {payload.id} already exists")
        self.created.append(payload)
        return payload  # import_csv only needs .model_dump() off the result


CSV = textwrap.dedent("""\
    id,name,category,price,in_stock,tags
    100,Mouse,Electronics,1299,true,mouse|wireless
    101,Lamp,Home,999,true,lamp
    1,Dup,Misc,10,true,dup
    102,,Misc,500,true,noname
    103,Bad,Misc,-50,true,negative
""")


class TestImportCsv:
    @pytest.fixture
    def csv_path(self, tmp_path):
        p = tmp_path / "products.csv"
        p.write_text(CSV)
        return p

    def test_three_buckets_are_separated(self, csv_path):
        mod = pytest.importorskip("catalog.import_csv")
        pytest.importorskip("catalog.client")
        report = mod.import_csv(csv_path, _FakeClient(dup_ids={1}))
        s = report["summary"]
        assert s["created"] == 2            # rows 100, 101
        assert s["validation_errors"] == 2  # empty name + negative price
        assert s["api_errors"] == 1         # id 1 is a duplicate
        assert s["rows_read"] == 5

    def test_validation_error_records_row_and_field(self, csv_path):
        mod = pytest.importorskip("catalog.import_csv")
        pytest.importorskip("catalog.client")
        report = mod.import_csv(csv_path, _FakeClient(dup_ids={1}))
        first = report["validation_errors"][0]
        assert "row" in first and "errors" in first  # operator can find the bad row

    def test_api_error_bucket_records_status(self, csv_path):
        mod = pytest.importorskip("catalog.import_csv")
        pytest.importorskip("catalog.client")
        report = mod.import_csv(csv_path, _FakeClient(dup_ids={1}))
        assert report["api_errors"][0]["status"] == 409
