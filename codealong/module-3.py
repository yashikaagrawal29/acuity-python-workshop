"""Module 3 — OOP, Decorators, Type Hints, FastAPI · CODE-ALONG

Each concept TWICE: a SIMPLE way, then the idiomatic upgrade.
    python3 codealong/module-3.py
Covers base slides 21-27. Stdlib only — FastAPI's idea is demoed with a 5-line
router; the real thing is a comment.
"""
import functools
import time
from dataclasses import dataclass


# §1  model a product                                     (slides 21-22)
class ProductPlain:                          # simple: write __init__ + __repr__ yourself
    def __init__(self, id, name, price):
        self.id, self.name, self.price = id, name, price
    def __repr__(self):
        return f"ProductPlain(id={self.id}, name={self.name!r}, price={self.price})"

@dataclass                                   # advanced: __init__/__repr__/__eq__ generated free
class Product:
    id: int
    name: str
    price: float

print("§1 plain    :", ProductPlain(1, "Cable", 499))
print("§1 dataclass :", Product(1, "Cable", 499),
      "| eq:", Product(1, "Cable", 499) == Product(1, "Cable", 499))

# §2  type hints are data tools can read                  (slide 23)
def price_with_tax(price: float) -> float:
    return round(price * 1.18, 2)
print("§2 annotations:", price_with_tax.__annotations__)   # editors/mypy/FastAPI/Pydantic read these

# §3  wrap a function with logging                        (slide 24)
def add(a, b):
    return a + b
def log_call(func, *args):                   # simple: call a wrapper explicitly each time
    print("  calling", func.__name__)
    return func(*args)
print("§3 simple:", log_call(add, 2, 3))

def log_calls(func):                         # advanced: a decorator wraps it once, at definition
    @functools.wraps(func)                   # keeps __name__ so tools/tests can introspect
    def wrapper(*args, **kwargs):
        print("  calling", func.__name__)
        return func(*args, **kwargs)
    return wrapper
@log_calls
def multiply(a, b):
    return a * b
print("§3 advanced:", multiply(2, 3), "| name kept:", multiply.__name__)

# §4  retry on failure                                    (slide 25)
def retry3(func):                            # simple: a fixed decorator (always 3 tries)
    @functools.wraps(func)
    def wrapper(*a, **k):
        for _ in range(3):
            try:
                return func(*a, **k)
            except Exception:
                pass
        raise
    return wrapper

def retry(times=3, delay=0.0):               # advanced: a decorator FACTORY — takes arguments
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **k):
            for attempt in range(1, times + 1):
                try:
                    return func(*a, **k)
                except Exception:
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

calls = {"n": 0}
@retry(times=3)
def flaky():
    calls["n"] += 1
    if calls["n"] < 3:
        raise ValueError("boom")
    return "ok"
print("§4 retry:", flaky(), "after", calls["n"], "tries")

# §5  "FastAPI is decorators"                             (slides 26-27)
routes = {}
def route(path):                             # simple: a 5-line router shows what @app.get DOES
    def register(func):
        routes[path] = func
        return func
    return register
@route("/products")
def list_products():
    return [{"id": 1, "name": "Cable"}]
print("§5 routes:", list(routes), "->", routes["/products"]())

# advanced: real FastAPI is the same decorator pattern + type hints -> auto /docs
#   from fastapi import FastAPI
#   app = FastAPI()
#   @app.get("/products")
#   def list_products() -> list[dict]: return [...]
#   $ uvicorn catalog.server:app --reload      # Swagger UI generated at /docs
