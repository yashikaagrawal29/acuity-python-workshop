"""Module 2 — Data Structures, Files & Modules · CODE-ALONG

Covers every Module-2 slide. Most concepts are shown two ways — a SIMPLE way,
then the idiomatic upgrade — so the jump is the lesson. Run it, or copy a block
per slide:    python3 codealong/module-2.py
§1-§6 = base slides 13-18 · §7-§10 = senior-track. Stdlib only.
"""
import csv, io, json, logging, os
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path

products = [
    {"id": 1, "name": "Cable",    "category": "Electronics", "price": 499},
    {"id": 2, "name": "Keyboard", "category": "Electronics", "price": 5499},
    {"id": 3, "name": "Yoga Mat", "category": "Fitness",     "price": 1299},
]

# §1  list / tuple / set / dict — pick by access pattern    (slide 13)
names = ["Cable", "Cable"]                  # list  — ordered, dupes OK, O(n) to search
dims  = (30, 10, 2)                         # tuple — fixed shape, immutable, hashable
cats  = {p["category"] for p in products}   # set   — unique membership
by_id = {p["id"]: p for p in products}      # dict  — O(1) lookup by key (the catalog's core)
print("§1 set:", cats, "| dict lookup:", by_id[2]["name"])

# §2  dict — go deep                                        (slide 14)
print("§2 safe get:", by_id.get(99, "missing"))    # .get(key, default) — no KeyError
prices = {p["id"]: p["price"] for p in products}
for pid in list(prices):                           # copy keys FIRST — mutating mid-iteration raises RuntimeError
    if prices[pid] < 1000:
        del prices[pid]
print("§2 kept >=1000:", sorted(prices))

# §3  keep the cheap product names                          (slide 15)
# simple: build the list with a loop
cheap_loop = []
for p in products:
    if p["price"] < 1500:
        cheap_loop.append(p["name"])
# advanced: the same list in one line. Read it left to right:
#   [ keep this   for each item   if condition ]
cheap = [p["name"] for p in products if p["price"] < 1500]
print("§3 cheap:", cheap_loop, "==", cheap)

# §4  serialize data: JSON & CSV                            (slide 16)
row = {"id": 1, "name": "Cable", "tags": ["usb", "cable"]}
# JSON — dump to text, load back. Shapes survive: the tags list stays a list.
text = json.dumps(row)
print("§4 json      :", text)
print("§4 json back :", json.loads(text)["tags"], "(still a list)")
# CSV — flat text only. csv handles quoting; a list you must flatten yourself.
csv_bad = f'{row["id"]},{row["name"]},{row["tags"]}'        # hand-rolled: list -> "['usb', 'cable']" garbage
buf = io.StringIO()
writer = csv.DictWriter(buf, fieldnames=["id", "name", "tags"])
writer.writeheader()
writer.writerow({**row, "tags": "|".join(row["tags"])})    # csv module + flatten the list -> "usb|cable"
print("§4 csv bad   :", csv_bad)
print("§4 csv good  :", buf.getvalue().splitlines()[1])

# §5  modules & __name__                                    (slide 17)
print("§5 __name__ =", __name__)   # '__main__' when run directly; the module's name when imported
# A package = a folder with __init__.py. `pip install -e .` makes `import catalog` work anywhere.
# CLIs end with  if __name__ == "__main__": main()  — runs only when executed, not when imported.

# §6  report an event                                       (slide 18)
print("§6 print: added id=1")                       # simple: print — no level/source, always on
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.info("added id=%s", 1)                      # advanced: logging — levels + %s lazy formatting

# §7  group + count by category          (senior: collections — builds Lab 2's group_by_category)
simple = {}
for p in products:                          # simple: manual dict-of-lists
    simple.setdefault(p["category"], []).append(p["name"])
groups = defaultdict(list)
for p in products:                          # advanced: defaultdict — no setdefault, no KeyError
    groups[p["category"]].append(p["name"])
print("§7 group:", dict(groups), "| count:", Counter(p["category"] for p in products))   # Counter = count in one line

# §8  total price of all products                           (senior: generator vs list)
total_list = sum([p["price"] for p in products])   # simple: builds the whole list first
total_gen  = sum(p["price"] for p in products)      # advanced: generator — () not [], one pass
print("§8 sum:", total_list, "==", total_gen)

# §9  guaranteed cleanup                                    (senior: context managers)
print(" open")                              # simple: try/finally by hand
try:
    print(" ...writing...")
finally:
    print(" close")
@contextmanager
def saving(name):                           # advanced: a context manager hides the try/finally
    print(" open", name)
    try:
        yield
    finally:
        print(" close", name)
with saving("catalog.json"):                # real use: atomic_write (write tmp, then os.replace)
    print(" ...writing...")

# §10  build a file path                                    (senior: pathlib)
simple = os.path.join("data", "products.csv")     # simple: string join
advanced = Path("data") / "products.csv"           # advanced: pathlib, compose with /
print("§10 path:", simple, "==", str(advanced), "| suffix:", advanced.suffix)
