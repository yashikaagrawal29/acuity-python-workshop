"""LLM-powered Catalog Agent (Day 4).

The agent's whole job is to take a natural-language question about the
catalog and answer it, using a small set of **tools** — which are just
Python functions wrapping the Day-2 `APIClient`.

## The Tool/Agent loop

    user prompt
        │
        ▼
    LLM(messages, tools)
        │
        ├── tool_calls? ──> run each tool, append observation, loop
        │
        └── final answer  ──> return AgentResult

## Why the LLM client is injected

`CatalogAgent(api_client, llm_client=...)` accepts any object that quacks
like `openai.OpenAI` (i.e. has `.chat.completions.create(...)`). That's the
seam tests use to mock the LLM — exactly the same pattern Day 3 used to
mock `requests.Session`.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

from pydantic import BaseModel, Field, ValidationError

from .client import APIClient

logger = logging.getLogger(__name__)


# ============================================================
# Structured outputs (used by Lab 10 + as a sanity check by Lab 11)
# ============================================================

class CatalogQuery(BaseModel):
    """Pydantic schema the LLM must return for NL → query parsing (Lab 10)."""

    category: Optional[str] = Field(
        default=None,
        description="Restrict to this category (e.g. 'Electronics'), or null for all.",
    )
    max_price: Optional[float] = Field(
        default=None, ge=0,
        description="Upper price bound in INR, or null for no bound.",
    )
    in_stock_only: bool = Field(
        default=False,
        description="If true, only return products currently in stock.",
    )
    name_contains: Optional[str] = Field(
        default=None,
        description="Substring (case-insensitive) the product name must contain.",
    )


# ============================================================
# Tool registration
# ============================================================

@dataclass
class ToolSpec:
    name: str
    description: str
    parameters_schema: dict
    fn: Callable[..., Any]

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }


class ToolRegistry:
    """Collects ToolSpecs declared with `@registry.tool(...)`."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def tool(self, *, name: str, description: str, parameters: dict):
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self._tools[name] = ToolSpec(
                name=name,
                description=description,
                parameters_schema=parameters,
                fn=fn,
            )
            return fn
        return decorator

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"tool {name!r} not registered")
        return self._tools[name]

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def openai_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]


# ============================================================
# LLM client protocol (so tests can pass any duck-typed mock)
# ============================================================

class LLMClient(Protocol):
    """Minimal slice of the OpenAI client interface this agent needs."""
    chat: Any


def default_openai_client() -> LLMClient:
    """Construct a real OpenAI client. Requires OPENAI_API_KEY in env."""
    from openai import OpenAI  # local import — only needed when we run real
    return OpenAI()


# ============================================================
# Agent result objects
# ============================================================

class AgentError(Exception):
    """Raised when the agent loop hits a hard failure (max steps, bad tool name…)."""


@dataclass
class ToolCallRecord:
    tool: str
    arguments: dict
    result: Any


@dataclass
class AgentResult:
    answer: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    steps: int = 0


# ============================================================
# CatalogAgent
# ============================================================

SYSTEM_PROMPT = (
    "You are a helpful assistant for a small product catalog. "
    "You have access to tools that let you list, search, count, add, and "
    "update products. Use them to answer the user's question. "
    "Prefer a single accurate tool call over multiple speculative ones. "
    "When you have enough information, respond in plain language."
)


class CatalogAgent:
    def __init__(
        self,
        api_client: APIClient,
        llm_client: Optional[LLMClient] = None,
        *,
        model: str = "gpt-4o-mini",
        max_steps: int = 5,
    ) -> None:
        self.api = api_client
        self.llm = llm_client or default_openai_client()
        self.model = model
        self.max_steps = max_steps
        self.registry = self._build_registry()

    # -------- tool implementations (each is just Python on top of APIClient) --------

    def _build_registry(self) -> ToolRegistry:
        registry = ToolRegistry()

        @registry.tool(
            name="list_products",
            description="Return every product in the catalog as a list of dicts.",
            parameters={"type": "object", "properties": {}, "additionalProperties": False},
        )
        def list_products() -> list[dict]:
            return [p.model_dump() for p in self.api.list_products()]

        @registry.tool(
            name="search_products",
            description="Find products whose name contains the given substring (case-insensitive).",
            parameters={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Substring to search for."},
                },
                "required": ["term"],
                "additionalProperties": False,
            },
        )
        def search_products(term: str) -> list[dict]:
            term_lower = term.lower()
            return [
                p.model_dump() for p in self.api.list_products()
                if term_lower in p.name.lower()
            ]

        @registry.tool(
            name="count_by_category",
            description="Return a dict mapping each category to its product count.",
            parameters={"type": "object", "properties": {}, "additionalProperties": False},
        )
        def count_by_category() -> dict[str, int]:
            return self.api.count_by_category()

        @registry.tool(
            name="update_price",
            description="Set a product's price. Returns the updated product.",
            parameters={
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "new_price": {"type": "number", "minimum": 0},
                },
                "required": ["product_id", "new_price"],
                "additionalProperties": False,
            },
        )
        def update_price(product_id: int, new_price: float) -> dict:
            from .models import ProductUpdate
            return self.api.update_product(
                product_id, ProductUpdate(price=new_price)
            ).model_dump()

        return registry

    # -------- the loop --------

    def ask(self, user_prompt: str) -> AgentResult:
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        tool_call_log: list[ToolCallRecord] = []

        for step in range(1, self.max_steps + 1):
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.registry.openai_schemas(),
            )
            choice = response.choices[0]
            msg = choice.message

            tool_calls = getattr(msg, "tool_calls", None) or []

            if not tool_calls:
                return AgentResult(
                    answer=(msg.content or "").strip(),
                    tool_calls=tool_call_log,
                    steps=step,
                )

            # Record assistant message verbatim so subsequent tool messages chain correctly.
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            })

            for call in tool_calls:
                result = self._invoke_tool(
                    call.function.name, call.function.arguments
                )
                tool_call_log.append(ToolCallRecord(
                    tool=call.function.name,
                    arguments=_parse_args(call.function.arguments),
                    result=result,
                ))
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": json.dumps(result, default=str),
                })

        raise AgentError(
            f"agent did not converge in {self.max_steps} steps "
            f"(last tool call: {tool_call_log[-1].tool if tool_call_log else 'none'})"
        )

    def _invoke_tool(self, name: str, arguments_json: str) -> Any:
        spec = self.registry.get(name)
        kwargs = _parse_args(arguments_json)
        logger.info("tool call: %s(%s)", name, kwargs)
        try:
            return spec.fn(**kwargs)
        except Exception as exc:
            logger.warning("tool %s raised %s", name, exc)
            return {"error": f"{type(exc).__name__}: {exc}"}


def _parse_args(arguments_json: str) -> dict:
    if not arguments_json:
        return {}
    try:
        return json.loads(arguments_json)
    except json.JSONDecodeError:
        return {}


# ============================================================
# Lab 10: NL query → CatalogQuery (single shot, no agent loop)
# ============================================================

NL_QUERY_SYSTEM = (
    "You convert natural-language product-catalog queries into a structured "
    "filter. Always respond with a JSON object matching the CatalogQuery schema. "
    "Use null for fields the user did not mention."
)


def parse_nl_query(prompt: str, llm_client: Optional[LLMClient] = None,
                   *, model: str = "gpt-4o-mini") -> CatalogQuery:
    """Lab 10: convert a free-form question into a validated CatalogQuery."""
    client = llm_client or default_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": NL_QUERY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    try:
        return CatalogQuery.model_validate_json(raw)
    except ValidationError:
        # Surface the raw output for debugging.
        logger.warning("LLM returned invalid CatalogQuery: %s", raw)
        raise


def apply_query(query: CatalogQuery, api: APIClient) -> list[dict]:
    """Translate a CatalogQuery into APIClient calls (Lab 10)."""
    items = api.list_products()
    if query.category:
        items = [p for p in items if p.category.lower() == query.category.lower()]
    if query.max_price is not None:
        items = [p for p in items if p.price <= query.max_price]
    if query.in_stock_only:
        items = [p for p in items if p.in_stock]
    if query.name_contains:
        needle = query.name_contains.lower()
        items = [p for p in items if needle in p.name.lower()]
    return [p.model_dump() for p in items]
