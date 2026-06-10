"""Bulk-import CSV → catalog API — Day 2 Lab 6.

The whole workflow:

    CSV row  --validate-->  ProductCreate  --POST-->  Product  --record-->  report

Three classes of outcome are tracked SEPARATELY so the report tells the
operator exactly what to fix (module-6, §"The report is the product"):

- validation_errors — the row never reached the API; Pydantic rejected it
- api_errors        — the API said no (e.g. 409 duplicate id)
- created           — the row was accepted

Fill every `# TODO`. The report shape and the CLI scaffold are given.

Run (server in another terminal):  python -m catalog.import_csv data/products.csv
Done-signal: an `import_report.json` whose summary mirrors stdout, with the
three buckets populated (README → Expected output). This report is the
system-under-test for Day 3.
Concepts: codealong/module-6.ipynb (CSV→API, the three buckets, the report).
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .client import APIClient, APIError
from .models import ProductCreate

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def import_csv(csv_path: str | Path, client: APIClient) -> dict[str, Any]:
    """Read `csv_path`, POST each row, return a structured report."""
    csv_path = Path(csv_path)
    created: list[dict] = []
    validation_errors: list[dict] = []
    api_errors: list[dict] = []

    with csv_path.open() as fh:
        reader = csv.DictReader(fh)
        for row_no, row in enumerate(reader, start=2):  # row 1 is the header
            try:
                payload = ProductCreate.model_validate(row)
            except ValidationError as exc:
                validation_errors.append(
                    {"row": row_no, "input": row, "errors": exc.errors()}
                )
                continue

            try:
                product = client.create_product(payload)
            except APIError as exc:
                api_errors.append(
                    {
                        "row": row_no,
                        "input": row,
                        "status": exc.status_code,
                        "detail": exc.detail,
                    }
                )
                continue

            created.append(product.model_dump())

    return {
        "source": str(csv_path),
        "summary": {
            "rows_read": len(created) + len(validation_errors) + len(api_errors),
            "created": len(created),
            "validation_errors": len(validation_errors),
            "api_errors": len(api_errors),
        },
        "created": created,
        "validation_errors": validation_errors,
        "api_errors": api_errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="catalog.import_csv")
    parser.add_argument("csv", help="path to CSV file (e.g. data/products.csv)")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--report", default="import_report.json")
    args = parser.parse_args(argv)

    client = APIClient(base_url=args.base_url)

    try:
        client.health()
    except Exception as exc:
        logger.exception("catalog API unreachable at %s: %s", args.base_url, exc)
        return 2

    report = import_csv(args.csv, client)
    Path(args.report).write_text(json.dumps(report, indent=2))

    s = report["summary"]
    print(
        f"\n{s['rows_read']} rows  |  "
        f"created {s['created']}  ·  "
        f"validation errors {s['validation_errors']}  ·  "
        f"API errors {s['api_errors']}"
    )
    print(f"report → {args.report}")
    return 0 if s["validation_errors"] == 0 and s["api_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
