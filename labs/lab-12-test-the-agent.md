# Lab 12 — Test the Agent ⭐

**Duration:** ~80 min · **Day:** 4 · **Module:** 3 (Testing & Validating AI)

## Goal
**This is the spine module.** AI systems look different on the outside —
non-deterministic, hard to reason about — but the discipline is the same
one you built on Day 3. You will write **four classes of tests** for the
agent, none of which require an OpenAI API key:

1. **Tool tests** — each agent tool is just a Python function. Test it deterministically (Day 3).
2. **Schema tests** — LLM JSON outputs must validate against the Pydantic schema from Lab 10 (Day 2).
3. **Loop tests with mocked LLM** — same `MagicMock` pattern Day 3 used for `requests`. Assert tools are called in the right order with the right arguments.
4. **Golden evals** — a JSON file of `{prompt, expected_tool_calls, expected_answer_contains}` cases that locks in agent behaviour.

After this lab you can ship the agent to a real codebase with the same
confidence you'd ship anything else with tests behind it.

## You start with
- Lab 11 end-state — `CatalogAgent` working with a real LLM.

## You'll end with
- `tests/test_agent.py` with four `class TestXxx:` blocks
- `tests/evals/golden_queries.json` with ~6 cases
- `pytest -q` green **without** `OPENAI_API_KEY` set
- The agent tests added to `.github/workflows/tests.yml` (already covered by your "run pytest" step)

## Steps

1. **Build a fake `APIClient`** for the tests:

   ```python
   def _fake_api(products):
       api = MagicMock(spec=APIClient)
       state = {p.id: p for p in products}
       api.list_products.side_effect = lambda: list(state.values())
       api.count_by_category.side_effect = lambda: _count(state)
       api.update_product.side_effect = _make_updater(state)
       return api
   ```

   `spec=APIClient` keeps typos honest (Day 3 lesson).

2. **Tool tests — deterministic Python.** Each tool function is reachable via `agent.registry.get("name").fn`:

   ```python
   class TestTools:
       def test_search_products_is_case_insensitive(self):
           agent = _make_agent()
           result = agent.registry.get("search_products").fn(term="KEYBOARD")
           assert result[0]["id"] == 2

       def test_count_by_category(self):
           agent = _make_agent()
           assert agent.registry.get("count_by_category").fn() == {
               "Electronics": 3, "Fitness": 1,
           }
   ```

3. **Schema tests — Pydantic validation of LLM outputs.** Use the same patterns from Day 3:

   ```python
   class TestCatalogQuerySchema:
       def test_rejects_negative_price(self):
           with pytest.raises(ValidationError):
               CatalogQuery(max_price=-5.0)

       def test_apply_query_filters(self):
           api = _fake_api(SAMPLE_PRODUCTS)
           q = CatalogQuery(category="Electronics", max_price=1000.0)
           assert {p["id"] for p in apply_query(q, api)} == {1}
   ```

4. **Loop tests — mock the LLM.** Build helpers that match OpenAI's response shape:

   ```python
   def _llm_message(content=None, tool_calls=None):
       msg = MagicMock(); msg.content = content; msg.tool_calls = tool_calls or None
       return msg

   def _tool_call(call_id, name, **arguments):
       c = MagicMock(); c.id = call_id
       c.function = MagicMock()
       c.function.name = name; c.function.arguments = json.dumps(arguments)
       return c

   def _llm_response(message):
       r = MagicMock(); r.choices = [MagicMock(message=message)]; return r
   ```

   Then script the LLM via `side_effect`:

   ```python
   class TestAgentLoop:
       def test_single_tool_call_then_answer(self):
           agent = _make_agent()
           agent.llm.chat.completions.create.side_effect = [
               _llm_response(_llm_message(
                   tool_calls=[_tool_call("c1", "count_by_category")])),
               _llm_response(_llm_message(content="We have 3 Electronics.")),
           ]
           r = agent.ask("how many electronics?")
           assert [c.tool for c in r.tool_calls] == ["count_by_category"]
           assert r.steps == 2

       def test_max_steps_hit_raises(self):
           agent = _make_agent()
           agent.llm.chat.completions.create.return_value = _llm_response(
               _llm_message(tool_calls=[_tool_call("c1", "count_by_category")]))
           with pytest.raises(AgentError, match="did not converge"):
               agent.ask("loop forever")
   ```

   Same `side_effect` pattern as Day 3's retry test. The mocking technique scales straight from `requests` to OpenAI.

5. **Golden evals — JSON-driven cases.** Create `tests/evals/golden_queries.json`:

   ```json
   [
     {
       "id": "eval-01",
       "prompt": "How many products are in the Electronics category?",
       "expected_tool_calls": ["count_by_category"],
       "expected_answer_contains": ["Electronics"]
     },
     ...
   ]
   ```

   Then parametrize over the file:

   ```python
   @pytest.mark.eval
   class TestGoldenQueries:
       @pytest.mark.parametrize("case", _golden_cases(),
                                ids=[c["id"] for c in _golden_cases()])
       def test_case_runs_expected_tools(self, case):
           agent = _make_agent()
           # Script the LLM: one tool call per expected tool, then an answer
           # containing every required substring.
           scripted = [...]
           agent.llm.chat.completions.create.side_effect = scripted

           result = agent.ask(case["prompt"])

           assert [c.tool for c in result.tool_calls] == case["expected_tool_calls"]
           for needle in case["expected_answer_contains"]:
               assert needle in result.answer
   ```

   When you discover a new failure mode, add a case to the JSON and the regression is locked.

6. **Register the marker** in `pyproject.toml` (so `--strict-markers` doesn't reject it):

   ```toml
   markers = [
       "integration: tests that hit a live FastAPI server (slow)",
       "eval: golden-prompt evaluation cases (Day 4)",
   ]
   ```

7. **Run it all — without an API key.**

   ```bash
   unset OPENAI_API_KEY
   pytest -q
   pytest -q -m eval                  # just the golden cases
   pytest -q -m "not integration"     # CI-fast subset
   ```

## Expected output

```
$ unset OPENAI_API_KEY && pytest -q
.....................................................                    [100%]
53 passed in 0.9s

$ pytest -q -m eval
......                                                                   [100%]
6 passed in 0.05s
```

## Common pitfalls
- Asserting on the LLM's **exact** answer wording. LLMs paraphrase. Assert on **substrings**, **tool calls**, and **schemas** — not prose.
- Forgetting `unset OPENAI_API_KEY` in CI and getting bills from a "test" run. The agent test setup must never construct a real client.
- Putting `OpenAI()` at the top of `agent.py`. It tries to grab the key at import — kills tests on machines without one. Construct lazily inside `default_openai_client()`.
- Writing 20 golden cases on day one. Start with 3-6 high-signal cases. Add a case **every time a real bug ships**.
- Testing "the LLM is smart". You can't. You can test that **your code reacts correctly** to a class of LLM behaviours. Stay on that side of the line.

## Stretch (optional)
- Add an **actual LLM-backed eval run** as a *separate* pytest marker (`@pytest.mark.live_llm`) that's skipped in CI but you can run manually. Use it to spot-check the mocked golden cases reflect reality.
- Use `pytest-recording` / `vcrpy` to record real OpenAI responses once, then replay them deterministically.
- Add a **cost ceiling** test that asserts a single agent loop doesn't exceed N tool calls (proxy for runaway-cost regressions).

---

**End of Day 4 — and the workshop.** Your `my-catalog/` project now contains:

- ✅ A Python catalog with classes, decorators, type hints (Day 1)
- ✅ A FastAPI server + Pydantic-typed `APIClient` (Days 1-2)
- ✅ A CSV → API bulk-import workflow (Day 2)
- ✅ A `pytest` suite with mocks, parametrization, HTML reports, CI (Day 3)
- ✅ An LLM-powered `CatalogAgent` with tools and an agent loop (Day 4)
- ✅ A test suite validating the agent's tools and LLM outputs (Day 4)

**One project. Four days. Tested. Agentic. Done.**
