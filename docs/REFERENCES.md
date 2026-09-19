# External Community Reference Repositories

Use these repositories as generic lookup references when researching or optimizing any game mechanic in this project.

They are not authoritative API documentation. Treat them as implementation examples, optimization ideas, data-structure references, and sources for benchmark candidates.

Always validate assumptions against:

1. current in-game behavior
2. current Tooltips Code documentation
3. relevant current Wiki mechanics pages

## Generic lookup references

- https://github.com/MateusMarochi/the-farmer-was-replaced-codes
- https://github.com/juritox/the-farmer-was-replaced
- https://github.com/ketrab2004/the-farmer-was-replaced
  - original Dinosaur implementation: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/dinosaur.py
  - pathfinding helpers: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/pathfind.py
  - queue implementation: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/queue.py
  - tail data structure: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/tail.py
- https://github.com/jdeokkim/tfwr
- https://g.j4.lc/general-stuff/the-farmer-was-replaced
  - collection of highly optimized community scripts; use as a generic implementation/benchmark reference
- https://pastebin.com/raw/i9kVXysm
- https://pastebin.com/raw/ugCFADtN
- https://pastebin.com/raw/ZkBRZv3P
  - raw community source references; inspect the actual source before deriving assumptions from them
- https://github.com/nql1314/The-Farmer-Was-Replaced-AI-Code
  - broad implementation repository covering multiple mechanics; useful for alternative algorithms, data structures, and optimization ideas

When looking for an optimization:

- search these repositories for the relevant mechanic, entity, item, or API call
- compare multiple independent implementations before assuming one pattern is optimal
- prefer measured behavior over shorter or more elegant code
- preserve a source-near benchmark mode when adapting an external implementation
- do not copy outdated assumptions about tick costs or game mechanics without re-checking them
