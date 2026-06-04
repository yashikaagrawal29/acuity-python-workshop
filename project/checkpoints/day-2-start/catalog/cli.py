"""Tiny CLI for the catalog (Day 1 Lab 1 / Lab 2).

Usage:
    python -m catalog.cli list
    python -m catalog.cli add 10 "Notebook" Stationery 199
    python -m catalog.cli search keyboard
    python -m catalog.cli save catalog.json
    python -m catalog.cli load catalog.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .models import CatalogError, Product, ProductCatalog
from .storage import load_json, save_json, seed_products

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DEFAULT_PATH = Path("catalog.json")


def _load() -> ProductCatalog:
    if DEFAULT_PATH.exists():
        return load_json(DEFAULT_PATH)
    return ProductCatalog(list(seed_products()))


def _save(catalog: ProductCatalog) -> None:
    save_json(catalog, DEFAULT_PATH)


def cmd_list(_: argparse.Namespace) -> int:
    catalog = _load()
    for p in catalog.list_all():
        print(f"  {p.id:>3}  {p.name:<28} {p.category:<14} ₹{p.price:>8.2f}  "
              f"{'in stock' if p.in_stock else 'OOS'}")
    print(f"\n{len(catalog)} products")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    catalog = _load()
    try:
        catalog.add(Product(args.id, args.name, args.category, args.price))
    except CatalogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    _save(catalog)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    catalog = _load()
    hits = catalog.search_by_name(args.term)
    print(json.dumps([p.to_dict() for p in hits], indent=2))
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    catalog = _load()
    save_json(catalog, args.path)
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    catalog = load_json(args.path)
    print(f"loaded {len(catalog)} products")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="catalog")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(fn=cmd_list)

    p_add = sub.add_parser("add")
    p_add.add_argument("id", type=int)
    p_add.add_argument("name")
    p_add.add_argument("category")
    p_add.add_argument("price", type=float)
    p_add.set_defaults(fn=cmd_add)

    p_search = sub.add_parser("search")
    p_search.add_argument("term")
    p_search.set_defaults(fn=cmd_search)

    p_save = sub.add_parser("save")
    p_save.add_argument("path")
    p_save.set_defaults(fn=cmd_save)

    p_load = sub.add_parser("load")
    p_load.add_argument("path")
    p_load.set_defaults(fn=cmd_load)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
