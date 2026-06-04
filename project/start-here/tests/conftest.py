"""Shared fixtures for the Day-1 lab specs.

The import is done lazily inside the fixture so that this conftest stays
importable even before `catalog/models.py` exists — tests that need the
catalog simply *skip* until you build it, rather than erroring the session.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def seeded_catalog():
    """A 3-product catalog: ids 10/20/30, two Electronics + one Fitness."""
    pytest.importorskip("catalog.models")
    from catalog.models import Product, ProductCatalog

    return ProductCatalog(
        [
            Product(10, "Cable", "Electronics", 499.0, True, ["usb"]),
            Product(20, "Keyboard", "Electronics", 5499.0, True, ["mech"]),
            Product(30, "Yoga Mat", "Fitness", 1299.0, False, ["yoga"]),
        ]
    )
