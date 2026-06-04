"""Unit tests for Product / ProductCreate / ProductUpdate Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from catalog.models import Product, ProductCreate, ProductUpdate


class TestProductValidation:
    def test_valid_payload(self):
        p = Product(
            id=1, name="X", category="c", price=10.0,
            in_stock=True, tags=["a"],
        )
        assert p.id == 1
        assert p.tags == ["a"]

    @pytest.mark.parametrize(
        "field,value,err_substring",
        [
            ("name", "",  "at least 1 character"),
            ("price", -1, "greater than or equal to 0"),
            ("id",   0,   "greater than or equal to 1"),
            ("category", "", "at least 1 character"),
        ],
    )
    def test_rejects_invalid(self, field, value, err_substring):
        base = dict(id=1, name="X", category="c", price=10.0)
        base[field] = value
        with pytest.raises(ValidationError) as exc:
            Product(**base)
        assert err_substring in str(exc.value)

    def test_coerces_string_bools_and_pipe_tags(self):
        p = Product.model_validate(
            {"id": "5", "name": "Y", "category": "c",
             "price": "9.5", "in_stock": "true", "tags": "a|b|c"}
        )
        assert p.id == 5
        assert p.in_stock is True
        assert p.tags == ["a", "b", "c"]

    def test_to_dict_roundtrip(self):
        p = Product(id=1, name="X", category="c", price=10.0)
        assert Product.from_dict(p.to_dict()) == p


class TestProductUpdate:
    def test_all_fields_optional(self):
        assert ProductUpdate().model_dump(exclude_unset=True) == {}

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            ProductUpdate(price=9.99, unknown_field="oops")

    def test_partial_update(self):
        patch = ProductUpdate(price=12.5)
        assert patch.model_dump(exclude_unset=True) == {"price": 12.5}
