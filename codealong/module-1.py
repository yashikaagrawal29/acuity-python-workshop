"""Module 1 — Python Core · CODE-ALONG

Most concepts shown two ways — a SIMPLE way, then the idiomatic upgrade — so the
jump is the lesson. Run it, or copy a block per slide:
    python3 codealong/module-1.py
Covers base slides 6-9. Stdlib only.
"""

# §1  variables, types, operators                          (slide 6)
name: str = "Cable"          # annotations are for readers/tools — NOT enforced at runtime
price = 499                  # int; Python is dynamically typed
in_stock = True              # bool
print("§1", name, price, in_stock, "| price * 3 =", price * 3)

# §2  truthiness & None                                     (slide 7)
tags = []
print("§2 simple  :", "has" if len(tags) > 0 else "empty")   # measure the length
print("§2 advanced:", "has" if tags else "empty")            # [] is falsy — just test it
x = None
print("§2 None: use 'is', not '==' ->", x is None)

# §3  pass arguments to a function                          (slide 8)
catalog = {1: "Cable", 2: "Keyboard"}
def add_simple(catalog, id, name, category, price):          # simple: all positional — easy to mis-order
    catalog[id] = name
def add(catalog, name, *, category="Misc", price=0.0):       # advanced: keyword-only after * = clear calls
    new_id = max(catalog) + 1
    catalog[new_id] = name
    return new_id
add_simple(catalog, 3, "Mat", "Fitness", 1299)              # which arg was which?
new_id = add(catalog, "Speaker", category="Electronics", price=2499)   # reads like its meaning
print("§3 added id:", new_id, "->", catalog[new_id])

# §4  handle a missing product                              (slide 9)
# simple (bad): swallow everything — hides real bugs
try:
    name = catalog[99]
except Exception:
    name = None                              # what actually failed? you'll never know
# advanced: your own exception, caught narrowly
class CatalogError(Exception):
    ...
def get(pid):
    if pid not in catalog:
        raise CatalogError(f"id {pid} not found")
    return catalog[pid]
try:
    get(99)
except CatalogError as e:                    # specific + meaningful; never `except: pass`
    print("§4 handled:", e)
