# Flekay/The-Farmer-Was-Replaced

## Upstream

- URL: https://github.com/Flekay/The-Farmer-Was-Replaced
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `567e0ab6f96305cd6c9a05fd5eea2917449c2407`
- Revision date: 2026-01-28
- Snapshot files: 283
- Snapshot size: 689580 bytes
- License: GPL-3.0
- Snapshot status: complete pinned repository mirrored unchanged under `source/`
- Snapshot verification: the local `source/` tree SHA is exactly the upstream tree SHA `a93f3be4986e6c198228cf94bc2be26c218c7995`

This is one of the most useful broad TFWR references reviewed so far. It is not a single save or one author's production farm. It is a community strategy collection with deliberately interchangeable algorithms, benchmark tables, language/tick-cost experiments, utility libraries, and many historical/experimental implementations.

The complete source mirror is preserved verbatim. Analysis and current-runtime caveats belong in this README.

## Executive summary

The repository is valuable in two distinct ways.

### 1. Strategy reference

It contains multiple implementations for the same mechanic:

- Cactus sorting
- Dinosaur/Bone
- Maze
- Pumpkin
- Sunflower/Power
- Polyculture
- movement/pathfinding
- ordinary resource farming

That makes it especially useful for generating benchmark candidates rather than copying one "best" implementation.

### 2. Interpreter/tick-cost reference

The `General/tests/` suite and `Tick Overview.md` measure the cost of:

- arithmetic and comparisons
- list/dict/set operations
- key types
- membership tests
- function indirection
- module access
- slicing/indexing
- control flow
- game API calls

This matters because TFWR optimization is not normal Python optimization.

A data structure that is asymptotically elegant can still lose because:

- tuple-key dict access costs more than integer-key access
- list front insertion/removal is expensive
- list membership is linear in ticks
- set/dict membership is cheap
- indirect/module-stored user-function calls can add tick overhead
- collection construction/copying itself consumes ticks

These measurements should be treated as benchmark evidence from the pinned upstream revision, not timeless engine constants. Re-run critical claims when a hot-path decision depends on them.

## Repository structure

Major areas include:

- `Beginner Scripts/`
- `Cactus/`
- `Dinosaur/`
- `General/`
- `Libraries/`
- `Maze/`
- `Movement/`
- `Polyculture Balanced/`
- `Polyculture Carrots/`
- `Polyculture Hay/`
- `Polyculture Wood/`
- `Pumpkins/`
- `Sunflowers/`
- `Weird Substance/`

Top-level research files include:

- `Tick Overview.md`
- `Leaderboards.md`
- `Unlock Order.md`
- `Style.md`
- `__builtins__.py`

The `Libraries/` files bundle utility implementations from the more granular `General/` tree.

## Tick-cost research

`Tick Overview.md` is a particularly strong reference because many entries are backed by dedicated files under `General/tests/`.

Examples recorded by the upstream revision include:

- numeric arithmetic: usually 1 tick
- `list.append()`: 1 tick
- list `insert(idx)`: proportional to shifted elements
- list `remove()`: proportional to list length
- list `pop(idx)`: proportional to elements after the index
- set membership: 1 tick
- dict membership: 1 tick
- list/tuple membership: linear
- integer dict key access: 1 tick
- tuple dict key access: proportional to tuple length
- long string dict keys: increasing cost
- direct user-function calls: no extra call tick in the documented model
- indirect/stored user-function calls: can add 1 tick
- `get_tick_count()`, `get_time()`, and `quick_print()`: documented as zero-tick
- successful `move()`, `plant()`, `harvest()`, `swap()`, `till()`: large action costs relative to ordinary computation

### Direct implications for this project

Several current coding choices can be evaluated against this data.

#### Prefer compact integer state identifiers in hot maps

If a per-tile structure can use:

```text
index = y * size + x
```

instead of:

```text
(x, y)
```

as a dict key, Flekay's measurements predict lower lookup cost.

This needs source-near benchmarking because converting coordinates to an integer also costs arithmetic ticks.

#### Avoid front-of-list queues

Algorithms using:

```text
queue.pop(0)
```

or:

```text
path = path + [direction]
```

can incur substantial interpreter cost.

Prefer:

- index cursors over queue lists
- append/pop at the end when ordering permits
- predecessor maps instead of copying full BFS paths
- fixed arrays/tables when dimensions are known

This reinforces concerns already identified in several external Maze and Dinosaur references.

#### Set/dict membership can be worth the memory

Using a dict/set for visited-state membership may beat repeated `item in list` even when the collection is fairly small.

Again, the actual full algorithm should be measured rather than optimizing one operation in isolation.

## Sorting research

`General/sorting/` contains implementations and operation-count results for:

- bubble sort
- bucket sort
- cocktail sort
- comb sort
- counting sort
- gnome sort
- heap sort
- insertion sort
- merge sort
- quick sort
- radix sort
- selection sort
- shell sort
- Tim sort

For large random/reverse-list tests in the recorded upstream benchmark, quick sort, bucket sort, radix sort, shell sort, merge sort, and comb sort are dramatically cheaper than quadratic naive sorts.

However, generic list sorting performance does not directly identify the fastest Cactus strategy.

Cactus sorting cost is dominated by physical:

- movement
- `measure()`
- `swap()`

and by the spatial constraints of the 2D field.

Therefore generic sorting results are useful for helper structures, but Cactus must be benchmarked with actual field movement.

## Cactus

The repository provides multiple single-drone Cactus algorithms:

- gradient bubble sort
- insertion sort
- heapify
- naive 4-way bubble sort
- naive cocktail sort
- shear sort
- naive bubble sort
- "oneshot" replant-to-uniform strategy

The upstream 10x10 comparison intentionally uses the same simple planting routine so it measures raw sorting differences more fairly.

Recorded average times at that revision include approximately:

- gradient bubble sort: 12.99 s
- insertion sort: 13.38 s
- heapify: 14.22 s
- naive 4-way bubble: 14.59 s
- cocktail: 14.61 s
- shear sort: 16.42 s
- naive bubble: 16.79 s
- oneshot: 25.66 s

These are upstream measurements, not current local benchmark results.

### Useful lesson

A theoretically sophisticated sort is not automatically faster in TFWR.

Movement geometry and the number/location of actual swaps matter more than generic asymptotics.

### Benchmark candidates

The strongest source-near candidates for this project are:

1. gradient bubble sort
2. insertion sort
3. shear sort
4. 4-way relaxation/bubble
5. heapify

Compare them against the current phase-separated multi-drone row/column strategy under the same field size, seed set, and planting phase.

## Maze: shared vector flow field

`Maze/Single Drone/Shared_Vector_Flow_Field.py` is especially relevant.

The strategy attributed to the Vehn/Zapakh line of work:

1. generates a Maze
2. recursively maps the initial Maze
3. stores wall sets per coordinate
4. builds a BFS distance/vector field toward a fixed base
5. for each relocated Treasure, computes:
   - current drone -> base path
   - Treasure -> base path
6. removes their shared suffix
7. travels only the remaining branches
8. when a formerly known wall disappears, updates the graph and recomputes affected flow-field distances

This is conceptually close to the persistent-reference-tree family already benchmarked in this project.

### Intersection stitching

The valuable idea is not simply "BFS".

The fixed base lets both endpoints reuse one shared routing structure.

Paths from the current drone and target are stitched at their common route toward the base.

That avoids solving every pairwise shortest path from scratch.

### Dynamic wall removal

`move_and_break_walls()` explicitly probes walls that were previously present.

When a wall has disappeared after Treasure relocation, it:

- removes the wall from both cells
- updates the distance field

That provides a concrete reference for incremental Maze topology repair.

### Benchmark evidence

The upstream README reports, on its 10x10 single-drone benchmark:

- 20 Treasures: ~9.67 s average
- 100 Treasures: ~25.98 s average
- 300 Treasures: ~54.26 s average

Do not compare those numbers directly with this project's 16/32-wide benchmarks or different game revisions.

The algorithm itself is highly relevant and should be cross-checked against the current Zapakh/reference-tree variants already present locally.

## Historical zero-tick Maze experiment

`zero_tick_maze_runner.py` is a historical curiosity with real research value.

It encodes logic using functions as boolean gates and large generated function structures, attempting to exploit old interpreter cost behavior.

The upstream README explicitly says the technique was patched and is no longer free.

This is a useful reminder that community leaderboard code can depend on interpreter quirks that later disappear.

Do not adapt this script to production without independently re-measuring every assumed zero-cost primitive.

## Dinosaur strategy collection

The Dinosaur folder contains several strategies:

- greedy
- A*
- random
- simple one-Apple restart
- circle/Hamiltonian-like patterns
- shortcut variants
- staged hybrid strategies

The upstream benchmark table records successful leaderboard-capable variants such as:

- `drone.py`
- `circle/`
- `timon.py`
- `almighty.py`

while several direct/shortcut strategies have less than 100% success.

### Strong lesson: success rate is part of performance

A strategy with better nominal item throughput but occasional death is not equivalent to a leaderboard-safe strategy.

This supports keeping separate metrics for:

- successful-run throughput
- completion rate
- sustained expected throughput including failures/restarts

### Circle strategy

The `circle/` implementation is highly specialized.

It uses:

- position -> transition-function dispatch
- a hand-coded cycle
- local shortcut/extension logic based on Apple measurements
- an explicit switch from growth/shortcut phase into a deterministic full-cycle phase

The main research value is the same pattern now seen across multiple strong Dinosaur references:

> direct/shortcut routing is useful early, but a deterministic cycle becomes safer as occupancy increases.

That corroborates the crossover measured locally between skysdottir's shortcut-heavy strategy and plain Hamiltonian near full occupancy.

### Caveat

The exact 10x10 layouts/functions are heavily hard-coded.

Treat the design as a policy reference, not a reusable generic implementation.

## Pumpkin multi-drone strategies

The repository includes several named architectures:

- `tiny_line.py`
- `mega_line.py`
- `mega_chunk.py`
- `mega_swarm.py`
- `jarvan.py`
- `devil.py`

Not all files are fully implemented at the pinned revision.

### `mega_line.py`

The field is partitioned into lines with many synchronized drones.

Workers:

1. plant their line
2. collect dead/unready Pumpkin positions
3. repeatedly revisit only the remaining bad positions
4. aggressively finish the final few using Water/Fertilizer
5. wait for a synchronization condition
6. one worker harvests the combined giant Pumpkin

This reinforces the "only revisit failures" pattern from other references.

### Synchronization caveat

The script uses game-state busy waits such as:

```text
while get_entity_type():
    pass
```

and synchronization/race workarounds.

These may be valid as game-state communication, unlike historical Python shared-memory tricks, but they can consume interpreter effort or reduce simulation speed.

Benchmark them rather than assuming the synchronization is cheap.

### `jarvan.py`

This strategy uses fixed 5x5-ish region starts on a 29x29 field and a hierarchical spawning pattern.

The spawning routine attempts power-of-two fan-out rather than having one coordinator sequentially spawn every worker.

That is an interesting setup-time optimization candidate:

> distribute spawn work through the spawn tree itself.

Its actual setup benefit should be measured because every spawned drone still pays the game's spawn action cost and scheduling may overlap those costs.

## Sunflowers

The Sunflower folder compares several approaches.

The most relevant is `power-path.py`.

It:

1. groups coordinates into petal-count buckets
2. processes buckets from high petals to low
3. uses nearest-neighbor selection inside each bucket
4. uses precomputed wrapped movement tables
5. fertilizes/waits at the target immediately before harvest when needed

This independently corroborates the strongest msmith93 Sunflower lesson:

> petal ordering determines the coarse harvest order; local nearest-neighbor routing should optimize movement within equal-petal groups.

The upstream file itself comments that nearest-neighbor pathing improves over a simpler coordinate-navigation approach.

This should become a source-near benchmark candidate against the existing simulator-derived msmith93 variants.

## Movement and pathfinding

The repository contains generic movement algorithms including:

- nearest neighbor
- 2-opt improvement
- insertion variants
- Christofides-named approximation
- precomputed wrapped shortest-path tables
- generated movement tables

### Important naming caveat

Files named after known TSP algorithms are community approximations/implementations, not necessarily mathematically complete textbook versions.

For example, `christofides_approx.py` is actually a cheapest-insertion style heuristic rather than a full Christofides algorithm with MST, odd-degree matching, Euler tour, and shortcutting.

Use behavior/source, not filenames, when classifying algorithms.

### TFWR-specific tradeoff

A path optimizer must save enough physical movement to repay its interpreter computation cost.

For small buckets, brute-force or nearest-neighbor may outperform more expensive improvement passes.

For large coordinate sets, precomputed distance tables can reduce repeated arithmetic.

This is particularly relevant to Sunflowers, companion-request routing, and dead-Pumpkin repair lists.

## Polyculture

There are separate strategy collections for:

- balanced Polyculture
- Carrot-focused
- Hay-focused
- Wood-focused

This is useful because it treats companion farming as a production-objective problem rather than one generic layout.

Potential benchmark direction:

- compare static companion layouts
- dynamic request following
- crop-specific companion strategies
- objective-weighted layouts

Current multi-drone memory semantics must still be respected; no Python-state sharing assumption should be introduced when parallelizing them.

## Unlock / reset research

The repository contains:

- `Unlock Order.md`
- `Leaderboards.md`

The leaderboard definitions are useful as a dated source for target quantities and categories.

The unlock-order material is another independent reference for Fastest Reset research.

As with all reset references, use live `get_cost()` values and current unlock availability rather than hard-coding an old tech tree solely from this file.

## General libraries

The repository implements many conveniences absent from the game's language:

- math
- string helpers
- list functions
- random helpers
- typing-like helpers
- dict helpers
- sorting
- basic scipy/sympy-inspired helpers

These are not directly production optimizations.

Their value is that they provide:

- tested language idioms
- reusable benchmark utilities
- examples of what operations are expensive in the custom interpreter

Avoid importing a general helper solely for elegance if a hot loop can use a simpler specialized operation.

## Strongest reusable findings

### Very high priority

1. measured interpreter/tick-cost tests
2. shared vector flow field / intersection stitching for Maze
3. incremental Maze wall-removal repair
4. Dinosaur early-shortcut -> safe-cycle phase transition
5. petal bins + nearest-neighbor Sunflower routing
6. revisit-only-failed Pumpkin repair
7. generic movement/path heuristic collection
8. Cactus strategy comparison under a controlled planting baseline

### Worth benchmarking

1. hierarchical/power-of-two drone spawning
2. integer-index dict keys vs coordinate tuples
3. set/dict visited structures vs lists
4. precomputed wrapped navigation tables
5. nearest-neighbor vs 2-opt/insertion for small coordinate buckets
6. function/module indirection cost in current hot loops

### Historical / revalidate before reuse

1. zero-tick logic/function tricks
2. old leaderboard/tick constants
3. fixed 10x10 Dinosaur geometry
4. hard-coded fixed-size Pumpkin layouts
5. any behavior relying on interpreter quirks rather than documented game mechanics

## Relationship to current local research

### Maze

This repository strongly reinforces the Zapakh/reference-tree direction already being benchmarked locally.

The most interesting delta is its explicit flow-field representation and incremental removal of walls that disappear after Treasure relocation.

### Dinosaur

Its benchmark table and circle strategy independently support the occupancy-dependent strategy switch already visible in local measurements:

- aggressive routing is strongest earlier
- safe deterministic cycles dominate near full occupancy

### Sunflowers

Its coordinate-binned nearest-neighbor approach independently converges on the same idea as the msmith93 simulator series.

That increases confidence that nearest-neighbor within petal groups is worth testing in current local code.

### Pumpkin

The dead-position revisit loop is consistent with several other strong community implementations.

This pattern now has enough independent support to be considered a primary benchmark architecture.

## Snapshot contents

The complete upstream repository is mirrored under `source/`.

It contains 283 files totaling 689,580 bytes.

Revision:

`567e0ab6f96305cd6c9a05fd5eea2917449c2407`

Tree:

`a93f3be4986e6c198228cf94bc2be26c218c7995`

The source tree is byte-identical/Git-tree-identical to upstream.
