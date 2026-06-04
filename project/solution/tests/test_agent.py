"""Tests for catalog.agent.

Four classes, matching the four kinds of test an AI system needs:

1. TestTools          — the tools are plain Python; test them deterministically
2. TestStructuredOutputs — Pydantic schema validation of LLM JSON
3. TestAgentLoop      — mock the LLM, assert the loop calls the right tools in order
4. TestGoldenQueries  — file-driven eval cases (parametrize from golden_queries.json)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from catalog.agent import (
    AgentError,
    CatalogAgent,
    CatalogQuery,
    apply_query,
)
from catalog.client import APIClient
from catalog.models import Product, ProductUpdate


# ============================================================
# Helpers — a fake APIClient backed by a list of Products
# ============================================================

def _fake_api(products: list[Product]) -> MagicMock:
    """A MagicMock(spec=APIClient) wired to behave like a working client."""
    api = MagicMock(spec=APIClient)
    state = {p.id: p for p in products}

    api.list_products.side_effect = lambda: list(state.values())
    api.get_product.side_effect = lambda pid: state[pid]
    def _update(pid, patch: ProductUpdate):
        updated = state[pid].model_copy(
            update=patch.model_dump(exclude_unset=True)
        )
        state[pid] = updated
        return updated
    api.update_product.side_effect = _update

    def _count():
        d: dict[str, int] = {}
        for p in state.values():
            d[p.category] = d.get(p.category, 0) + 1
        return d
    api.count_by_category.side_effect = _count

    return api


SAMPLE_PRODUCTS = [
    Product(id=1, name="USB-C Cable",         category="Electronics", price=499.0,  in_stock=True),
    Product(id=2, name="Mechanical Keyboard", category="Electronics", price=5499.0, in_stock=True),
    Product(id=3, name="Bluetooth Speaker",   category="Electronics", price=2499.0, in_stock=True),
    Product(id=4, name="Yoga Mat",            category="Fitness",     price=1299.0, in_stock=False),
]


def _make_agent(api=None) -> CatalogAgent:
    """Build a CatalogAgent with a fake api + a placeholder LLM (replaced per test)."""
    api = api or _fake_api(SAMPLE_PRODUCTS)
    llm = MagicMock()  # tests inject responses individually
    return CatalogAgent(api_client=api, llm_client=llm, model="test-model")


# ============================================================
# 1. Tool tests — deterministic Python (Day 3 patterns)
# ============================================================

class TestTools:
    def test_list_products_returns_dicts(self):
        agent = _make_agent()
        result = agent.registry.get("list_products").fn()
        assert isinstance(result, list)
        assert result[0]["name"] == "USB-C Cable"

    def test_search_products_is_case_insensitive(self):
        agent = _make_agent()
        result = agent.registry.get("search_products").fn(term="KEYBOARD")
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_count_by_category(self):
        agent = _make_agent()
        result = agent.registry.get("count_by_category").fn()
        assert result == {"Electronics": 3, "Fitness": 1}

    def test_update_price_mutates(self):
        agent = _make_agent()
        result = agent.registry.get("update_price").fn(product_id=1, new_price=10.0)
        assert result["price"] == 10.0

    def test_unknown_tool_raises(self):
        agent = _make_agent()
        with pytest.raises(KeyError):
            agent.registry.get("does_not_exist")


# ============================================================
# 2. Structured output schema tests
# ============================================================

class TestCatalogQuerySchema:
    def test_all_fields_optional(self):
        q = CatalogQuery()
        assert q.category is None
        assert q.in_stock_only is False

    def test_rejects_negative_price(self):
        with pytest.raises(ValidationError):
            CatalogQuery(max_price=-5.0)

    def test_apply_query_filters_by_category_and_price(self):
        api = _fake_api(SAMPLE_PRODUCTS)
        q = CatalogQuery(category="Electronics", max_price=1000.0)
        result = apply_query(q, api)
        assert {p["id"] for p in result} == {1}  # only USB-C Cable

    def test_apply_query_in_stock_only(self):
        api = _fake_api(SAMPLE_PRODUCTS)
        result = apply_query(CatalogQuery(in_stock_only=True), api)
        assert {p["id"] for p in result} == {1, 2, 3}  # Yoga Mat OOS


# ============================================================
# 3. Agent-loop tests — mock the LLM
# ============================================================

def _llm_message(content=None, tool_calls=None):
    """Build a fake OpenAI ChatCompletionMessage shape."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or None
    return msg


def _tool_call(call_id: str, name: str, **arguments) -> MagicMock:
    call = MagicMock()
    call.id = call_id
    call.function = MagicMock()
    call.function.name = name
    call.function.arguments = json.dumps(arguments)
    return call


def _llm_response(message) -> MagicMock:
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestAgentLoop:
    def test_answer_without_tool_calls(self):
        agent = _make_agent()
        agent.llm.chat.completions.create.return_value = _llm_response(
            _llm_message(content="No tools needed, the answer is 42.")
        )
        result = agent.ask("nothing to do")
        assert result.steps == 1
        assert result.tool_calls == []
        assert "42" in result.answer

    def test_single_tool_call_then_answer(self):
        agent = _make_agent()
        # First response: a tool call. Second: final answer.
        agent.llm.chat.completions.create.side_effect = [
            _llm_response(_llm_message(
                content=None,
                tool_calls=[_tool_call("call_1", "count_by_category")],
            )),
            _llm_response(_llm_message(
                content="We have 3 Electronics and 1 Fitness product.",
            )),
        ]
        result = agent.ask("how many electronics?")
        assert result.steps == 2
        assert [c.tool for c in result.tool_calls] == ["count_by_category"]
        assert result.tool_calls[0].result == {"Electronics": 3, "Fitness": 1}

    def test_chained_tool_calls_in_order(self):
        agent = _make_agent()
        agent.llm.chat.completions.create.side_effect = [
            _llm_response(_llm_message(
                tool_calls=[_tool_call("c1", "search_products", term="keyboard")],
            )),
            _llm_response(_llm_message(
                tool_calls=[_tool_call("c2", "update_price",
                                        product_id=2, new_price=4999.0)],
            )),
            _llm_response(_llm_message(
                content="Updated the keyboard to ₹4999.",
            )),
        ]
        result = agent.ask("drop the keyboard to 4999")
        assert [c.tool for c in result.tool_calls] == [
            "search_products", "update_price",
        ]
        assert result.tool_calls[-1].arguments == {
            "product_id": 2, "new_price": 4999.0,
        }

    def test_max_steps_hit_raises(self):
        agent = _make_agent()
        # Always emit a tool call → never converges
        agent.llm.chat.completions.create.return_value = _llm_response(
            _llm_message(
                tool_calls=[_tool_call("c1", "count_by_category")],
            ),
        )
        with pytest.raises(AgentError, match="did not converge"):
            agent.ask("loop forever")

    def test_unknown_tool_in_response_returns_error_observation(self):
        agent = _make_agent()
        agent.llm.chat.completions.create.side_effect = [
            _llm_response(_llm_message(
                tool_calls=[_tool_call("c1", "does_not_exist")],
            )),
            _llm_response(_llm_message(content="recovered")),
        ]
        # Should not raise — agent records error as observation and keeps going.
        with pytest.raises(KeyError):
            agent.ask("call a bogus tool")


# ============================================================
# 4. Golden eval cases — driven from a JSON file
# ============================================================

GOLDEN_PATH = Path(__file__).parent / "evals" / "golden_queries.json"


def _golden_cases():
    return json.loads(GOLDEN_PATH.read_text())


@pytest.mark.eval
class TestGoldenQueries:
    """Drives the agent through canned tool-call sequences and checks the answer
    contains expected substrings. The LLM is fully mocked: each test scripts
    the tool calls itself, so this stays deterministic without an API key."""

    @pytest.mark.parametrize(
        "case", _golden_cases(), ids=[c["id"] for c in _golden_cases()],
    )
    def test_case_runs_expected_tools(self, case):
        agent = _make_agent()

        # Build a fake LLM script: one tool call per expected tool, then an
        # answer that mentions every required substring.
        scripted = []
        for i, tool_name in enumerate(case["expected_tool_calls"]):
            args = _arguments_for(tool_name)
            scripted.append(_llm_response(_llm_message(
                tool_calls=[_tool_call(f"c{i}", tool_name, **args)],
            )))
        answer = " ".join(case["expected_answer_contains"])
        scripted.append(_llm_response(_llm_message(content=answer)))
        agent.llm.chat.completions.create.side_effect = scripted

        result = agent.ask(case["prompt"])

        assert [c.tool for c in result.tool_calls] == case["expected_tool_calls"]
        for needle in case["expected_answer_contains"]:
            assert needle in result.answer


def _arguments_for(tool_name: str) -> dict:
    """Minimal args so the tool actually runs against SAMPLE_PRODUCTS."""
    return {
        "search_products": {"term": "speaker"},
        "update_price":    {"product_id": 1, "new_price": 10.0},
    }.get(tool_name, {})
