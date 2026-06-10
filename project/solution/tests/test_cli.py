from __future__ import annotations

import argparse
from unittest.mock import MagicMock

from catalog.cli import (
    build_parser,
    cmd_add,
    cmd_list,
    cmd_load,
    cmd_save,
    cmd_search,
    main,
)
from catalog.models import Product, ProductCatalog


def _catalog_with_one_product() -> ProductCatalog:
    return ProductCatalog(
        [Product(id=7, name="Notebook", category="Stationery", price=199.0)]
    )


def test_cmd_list_prints_rows_and_count(monkeypatch, capsys):
    monkeypatch.setattr("catalog.cli._load", _catalog_with_one_product)
    code = cmd_list(argparse.Namespace())
    out = capsys.readouterr().out
    assert code == 0
    assert "Notebook" in out
    assert "1 products" in out


def test_cmd_add_success_saves_catalog(monkeypatch):
    catalog = ProductCatalog()
    save_mock = MagicMock()
    monkeypatch.setattr("catalog.cli._load", lambda: catalog)
    monkeypatch.setattr("catalog.cli._save", save_mock)
    args = argparse.Namespace(id=8, name="Pen", category="Stationery", price=20.0)
    code = cmd_add(args)
    assert code == 0
    assert catalog.get(8).name == "Pen"
    save_mock.assert_called_once()


def test_cmd_search_prints_json(monkeypatch, capsys):
    monkeypatch.setattr("catalog.cli._load", _catalog_with_one_product)
    code = cmd_search(argparse.Namespace(term="note"))
    out = capsys.readouterr().out
    assert code == 0
    assert "Notebook" in out


def test_cmd_save_and_cmd_load_delegate_storage(monkeypatch, capsys):
    save_mock = MagicMock()
    load_mock = MagicMock(return_value=_catalog_with_one_product())
    monkeypatch.setattr("catalog.cli._load", _catalog_with_one_product)
    monkeypatch.setattr("catalog.cli.save_json", save_mock)
    monkeypatch.setattr("catalog.cli.load_json", load_mock)

    assert cmd_save(argparse.Namespace(path="x.json")) == 0
    save_mock.assert_called_once()

    assert cmd_load(argparse.Namespace(path="x.json")) == 0
    assert "loaded 1 products" in capsys.readouterr().out


def test_build_parser_add_command_maps_to_cmd_add():
    args = build_parser().parse_args(["add", "10", "Mouse", "Electronics", "999"])
    assert args.id == 10
    assert args.fn.__name__ == "cmd_add"


def test_main_dispatches_to_selected_subcommand(monkeypatch):
    parser = MagicMock()
    parser.parse_args.return_value = argparse.Namespace(fn=lambda _: 7)
    monkeypatch.setattr("catalog.cli.build_parser", lambda: parser)
    assert main([]) == 7
