# Lab 10 — Natural-Language Query → Catalog Filter

**Duration:** ~80 min · **Day:** 4 · **Module:** 1 (LLM Fundamentals + Structured Outputs)

## Goal
Take a free-form question — *"show me electronics under ₹5000 in stock"* —
and use an LLM to convert it into a **Pydantic-validated** `CatalogQuery`
object that your code can execute against the `APIClient`. No agent loop
yet, no tools. One LLM call. The lesson: **make the LLM speak your schema,
not English you have to re-parse.**

## You start with
- `project/checkpoints/day-4-start/` (Day 3 end-state) OR your own Lab 9 folder
- An OpenAI-compatible API key (set `OPENAI_API_KEY`)

## You'll end with
- `CatalogQuery` Pydantic schema in `catalog/agent.py`
- `parse_nl_query(prompt) -> CatalogQuery` that calls the LLM with `response_format={"type":"json_object"}`
- `apply_query(query, api)` that runs the filter against your `APIClient`
- A REPL session where typing a question returns the right products

## Steps

1. **Define the schema** in `catalog/agent.py`:

   ```python
   class CatalogQuery(BaseModel):
       category: Optional[str] = Field(default=None,
           description="Restrict to this category, or null for all.")
       max_price: Optional[float] = Field(default=None, ge=0)
       in_stock_only: bool = False
       name_contains: Optional[str] = None
   ```

   The `description=` on each field is **not decorative** — the LLM reads
   it. Be precise.

2. **Write the parser.** Force JSON mode and validate with Pydantic:

   ```python
   def parse_nl_query(prompt: str, llm_client=None,
                      *, model="gpt-4o-mini") -> CatalogQuery:
       client = llm_client or OpenAI()
       response = client.chat.completions.create(
           model=model,
           messages=[
               {"role": "system", "content": NL_QUERY_SYSTEM},
               {"role": "user", "content": prompt},
           ],
           response_format={"type": "json_object"},
       )
       raw = response.choices[0].message.content or "{}"
       return CatalogQuery.model_validate_json(raw)
   ```

3. **Write `apply_query`** — pure Python, no LLM. Take the query and the API client, return matching products:

   ```python
   def apply_query(query: CatalogQuery, api: APIClient) -> list[dict]:
       items = api.list_products()
       if query.category:
           items = [p for p in items if p.category.lower() == query.category.lower()]
       if query.max_price is not None:
           items = [p for p in items if p.price <= query.max_price]
       ...
       return [p.model_dump() for p in items]
   ```

4. **Drive it from a REPL** (with the server running):

   ```python
   from catalog.agent import parse_nl_query, apply_query
   from catalog.client import APIClient

   q = parse_nl_query("show me electronics under 5000 that are in stock")
   print(q)
   for row in apply_query(q, APIClient()):
       print(row["id"], row["name"], row["price"])
   ```

5. **Watch the schema work for you.** Ask the LLM a nonsense question
   (*"give me products that taste like pizza"*) and confirm the parser
   either returns an empty/null-filled `CatalogQuery` or raises a clean
   `ValidationError`. Either is acceptable — silently lying isn't.

## Expected output

```python
>>> q = parse_nl_query("show me electronics under 5000 that are in stock")
CatalogQuery(category='Electronics', max_price=5000.0, in_stock_only=True, name_contains=None)

>>> for row in apply_query(q, APIClient()):
...     print(row["id"], row["name"], row["price"])
1   USB-C Cable          499.0
3   Bluetooth Speaker   2499.0
```

## Common pitfalls
- Forgetting `response_format={"type": "json_object"}` — the LLM returns prose, validation explodes.
- Vague `description=` fields. *"Filter the category"* doesn't tell the model what valid values look like. Better: *"Restrict to this category (e.g. 'Electronics'), or null for all."*
- Trusting the LLM's JSON without `model_validate_json`. **Always** parse through Pydantic — that's the contract.
- Using positional examples (`["Electronics"]`) in the prompt. The model will quote you literally. Prefer abstract descriptions.

## Stretch (optional)
- Add a `sort: Optional[Literal["price_asc", "price_desc", "name"]] = None` field.
- Use `instructor` (the library) — it wraps OpenAI calls and validates against your Pydantic model with retries on validation failures.
- Compare cost vs. accuracy of `gpt-4o-mini` vs `gpt-4o` on five tricky prompts.
