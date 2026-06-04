"""Shared pytest fixtures.

Three fixtures everyone uses:

- `sample_product`    — one fully-valid Product
- `seeded_catalog`    — a ProductCatalog with 3 deterministic products
- `live_server`       — boots uvicorn on a free port for integration tests
                        (only used by tests marked `integration`)
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from contextlib import closing

import pytest
import requests

from catalog.models import Product, ProductCatalog


@pytest.fixture
def sample_product() -> Product:
    return Product(
        id=1,
        name="Sample",
        category="Misc",
        price=99.0,
        in_stock=True,
        tags=["sample"],
    )


@pytest.fixture
def seeded_catalog() -> ProductCatalog:
    return ProductCatalog([
        Product(id=10, name="Cable",   category="Electronics", price=499.0,  in_stock=True),
        Product(id=11, name="Speaker", category="Electronics", price=2499.0, in_stock=True),
        Product(id=12, name="Mat",     category="Fitness",     price=1299.0, in_stock=False),
    ])


# ---- integration helpers ----

def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    """Spin up uvicorn on a free port for the duration of the test session."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn",
         "catalog.server:app", "--port", str(port), "--log-level", "warning"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            if requests.get(f"{base_url}/health", timeout=0.5).ok:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.fail("live_server did not become ready within 10 s")

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
