"""Typed HTTP client for the catalog API (Day 2 Lab 5).

Drives the FastAPI server from `server.py` end-to-end. Every method returns
a Pydantic `Product` (or list of them), so callers stay typed all the way
down — no raw dicts leak out of this module.

The class wears the Day-1 `@retry` decorator so transient network failures
don't kill a bulk-import run. On Day 4, the agent's tools will literally
*be* these methods.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from .decorators import retry
from .models import Product, ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0
DEFAULT_BASE_URL = "http://localhost:8000"


class APIError(Exception):
    """Raised when the catalog API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"{status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class APIClient:
    """CRUD client for the catalog API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    # ---- low-level ----

    @retry(times=3, delay=0.2, exceptions=(requests.ConnectionError, requests.Timeout))
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        logger.debug("HTTP %s %s", method, url)
        response = self._session.request(method, url, **kwargs)
        if not response.ok:
            detail = self._extract_detail(response)
            raise APIError(response.status_code, detail)
        return response

    @staticmethod
    def _extract_detail(response: requests.Response) -> str:
        try:
            return response.json().get("detail", response.text)
        except ValueError:
            return response.text or response.reason

    # ---- typed CRUD ----

    def health(self) -> dict:
        return self._request("GET", "/health").json()

    def list_products(self) -> list[Product]:
        data = self._request("GET", "/products").json()
        return [Product.model_validate(row) for row in data]

    def get_product(self, product_id: int) -> Product:
        data = self._request("GET", f"/products/{product_id}").json()
        return Product.model_validate(data)

    def create_product(self, payload: ProductCreate) -> Product:
        data = self._request(
            "POST", "/products", json=payload.model_dump()
        ).json()
        return Product.model_validate(data)

    def update_product(self, product_id: int, patch: ProductUpdate) -> Product:
        data = self._request(
            "PATCH",
            f"/products/{product_id}",
            json=patch.model_dump(exclude_unset=True),
        ).json()
        return Product.model_validate(data)

    def delete_product(self, product_id: int) -> None:
        self._request("DELETE", f"/products/{product_id}")

    # ---- agent-friendly helpers (used on Day 4) ----

    def count_by_category(self) -> dict[str, int]:
        products = self.list_products()
        counts: dict[str, int] = {}
        for p in products:
            counts[p.category] = counts.get(p.category, 0) + 1
        return counts
