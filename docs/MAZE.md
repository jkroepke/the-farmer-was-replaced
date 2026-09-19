# Maze Design, Benchmarks, and Optimization Notes

This document is the canonical reference for Maze behavior, production strategy, benchmarks, and future optimization work in this repository.

Read this file before changing:

- `maze.py`
- Maze-related logic in `production.py`
- `bench_maze.py`
- `bench_maze_run.py`
- Maze-related constants in `config.py`

## Sources

Primary game/API reference:

- Tooltips Code: https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips_Code

Reference tree-rebalancing implementation:

- "maze single - tree rebalancing": https://pastebin.com/KzGvn6nc

The production implementation is a behavioral adaptation of that reference, adjusted for this repository's upgrade-driven resource planner and persistent Gold production.

---

## Game mechanics used by the implementation

A fresh Maze is created by:

1. planting a Bush
2. applying the required Weird Substance

The amount of Weird Substance is:

```text
world_size * 2 ** (maze_level - 1)
```

Relevant behavior:

- A fresh Maze has no loops.
- `can_move(direction)` checks whether a wall blocks a direction.
- `measure()` while in a Maze exposes the current Treasure coordinates.
- Applying Weird Substance on a Treasure relocates the Treasure and causes Maze walls to disappear over time.
- Reusing a Maze therefore gradually turns the original tree-shaped Maze into a graph with shortcuts/loops.
- Harvesting the final Treasure ends the Maze and produces the Gold reward.
- Clearing or replacing the farm invalidates both the physical Maze and every in-memory path/tree structure.

---

## Production strategy

`maze.py` uses a persistent reference-style tree-rebalancing strategy.

### Lifecycle

The Maze is reused across consecutive Gold-focused planner iterations.

1. The first `maze.run()`:
   - clears the field
   - creates one fresh Maze
   - maps the full fresh Maze with DFS
   - builds an ordered tree
   - may already encounter and relocate Treasures while mapping
2. Later `maze.run()` calls:
   - keep the same Maze
   - keep the same in-memory tree
   - route to the current Treasure
   - relocate it using Weird Substance
3. After the configured relocation limit:
   - route to the final Treasure
   - harvest it
   - reset the Maze state
4. The next Gold request starts a fresh Maze.

The important optimization is that a Gold -> Gold transition does **not** rebuild the normal farm or sunflower edges.

### Gold planner interaction

`production.py` treats Maze/Gold specially:

- Gold -> Gold:
  - preserve the Maze
  - preserve the tree
  - do not rebuild sunflowers
- Gold -> non-Gold:
  - call `maze.reset()`
  - clear/rebuild the normal farm exactly once
- active Maze but insufficient Weird Substance:
  - the Maze may be abandoned
  - restore normal farming so Weird Substance can be produced
- farm expansion:
  - coordinates change
  - the Maze tree is invalid
  - `production.reset_state()` must reset Maze state before the expanded farm is rebuilt

### Current production thresholds

Defined in `config.py`:

`MAZE_STOCKPILE = 5` controls how many Maze-cost equivalents of Weird Substance normal farming tries to keep available before Gold production needs it.

The routing/reuse thresholds are:

```text
MAZE_REUSE_LIMIT = 300
MAZE_GREEDY_AFTER = 30
MAZE_REROOT_AT = 40
MAZE_REBALANCE_FROM = 40
MAZE_REBALANCE_ACTIVE_UNTIL = 80
MAZE_REBALANCE_UNTIL = 140
```

These values were inherited from / aligned with the reference strategy and should be treated as benchmarkable tuning parameters, not permanent truths.

---

## Tree representation

Each node stores approximately:

```text
val
max_val
level
coord
dir
parent
left
forward
right
root_extra
```

The initial loop-free Maze is mapped into an ordered DFS tree.

`val` and `max_val` describe a contiguous DFS subtree range. This lets routing determine whether the target lies:

- inside the current subtree -> descend to the appropriate child
- outside the current subtree -> walk toward the parent

This avoids running BFS for every Treasure.

### Critical interpreter rule: cyclic dictionaries

Nodes reference parents and children, so node dictionaries are cyclic.

Never do:

```python
node == other_node
node != other_node
```

The game interpreter recursively compares dictionaries and can fail with maximum comparison depth.

Compare stable scalar data instead:

```python
node["coord"] == other_node["coord"]
```

This bug was encountered during the benchmark port and is important to preserve as a documented constraint.

---

## Initial mapping

Fresh Mazes contain no loops, so DFS can map the Maze and build a spanning tree without generic graph pathfinding.

A major advantage of the reference implementation is that Treasure collection can happen **during the initial map traversal**.

If DFS happens to reach the current Treasure:

1. relocate it immediately
2. update the target
3. continue mapping

This overlaps the one-time mapping cost with useful Gold production.

This is one likely reason the reference implementation already beats the simpler tree implementation at only 25 relocations, before later shortcut/rebalancing behavior has much opportunity to matter.

---

## Routing phases

### Initial tree routing

Before Greedy behavior becomes relevant, routing uses the ordered `val/max_val` tree directly.

Benchmark evidence strongly suggests this representation is better than our earlier generic parent-tree path construction.

### Greedy shortcut discovery

After `MAZE_GREEDY_AFTER`, the solver attempts movements that reduce coordinate distance toward the Treasure.

Important properties:

- only try a Greedy direction when `can_move()` succeeds
- avoid retrying the same route point repeatedly within one solve
- if Greedy cannot continue, fall back to the guaranteed tree route
- newly opened walls are discovered naturally while traversing the Maze

The Maze changes after Treasure relocation, so continuously probing for new direct routes is valuable.

### Reroot

Around `MAZE_REROOT_AT`, the reference algorithm moves the logical tree root toward a more central point.

The intent is to reduce average parent-chain distance in the original DFS tree.

This should be isolated in a future ablation benchmark to quantify its actual contribution.

### Tree rebalancing

When a newly opened wall connects the current branch to a substantially shallower node, the branch can be rotated under the better parent.

Current heuristic:

```text
current.level > neighbor.level + 2
```

The tree is then reindexed so `val`, `max_val`, and `level` remain valid.

The reference algorithm only performs aggressive tree updates in part of the run rather than continuously.

---

## Benchmark file convention

All benchmark topics use:

```text
bench_<name>.py
bench_<name>_run.py
```

For Mazes:

- `bench_maze.py`
  - contains all implementations/modes
- `bench_maze_run.py`
  - owns world sizes
  - solve counts
  - seeds
  - simulation inventory
  - simulation globals
  - `simulate()` calls
  - result aggregation

Do not create separate files for individual Maze strategies.

Add new strategies as additional modes in `bench_maze.py`.

---

## Historical benchmark modes (preserved results)

| Mode | Name | Description |
| ---: | --- | --- |
| 0 | `fresh-right-hand` | Create a new Maze every time and solve with right-hand wall following |
| 1 | `reuse-bfs` | Reuse one Maze and repeatedly BFS over the updated graph |
| 2 | `reuse-tree-greedy` | Reuse initial generic tree plus Greedy shortcuts |
| 3 | `reuse-tree-greedy-lazy-rebalance` | Generic tree plus Greedy plus lightweight reparenting |
| 4 | `reuse-tree-greedy-full-reindex` | Generic tree plus Greedy/reparenting and approximate full reindex |
| 5 | `reference-tree-rebalancing` | Behavioral port of the Pastebin reference implementation |

Historical benchmark matrix:

```text
world sizes: 8, 16, 32
relocations: 25, 100, 300
seeds: 1, 2, 3
speedup: 64
```

Each reuse workload performs the requested number of Treasure relocations and then the final Treasure harvest.

The benchmark intentionally starts with oversized resources so pathing/algorithm cost is measured rather than resource acquisition.

---

## Amount-based 32x32 special benchmark

The active Maze benchmark runner now focuses only on the small-Maze / multi-drone question. The historical 8x8, 16x16, and 32x32 matrix above remains preserved as prior evidence, but `bench_maze_run.py` no longer reruns it by default.

Critical benchmark rule:

> Keep the farm at its real 32x32 size. Do not create 3x3 or 4x4 cases with `set_world_size()`. Create smaller Mazes only by changing the amount passed to `use_item(Items.Weird_Substance, amount)`.

Current Maze mechanics document that, before the Maze-upgrade multiplier, using `n` Weird Substance on a Bush creates an `n x n` Maze. With Maze upgrades the amount used by the benchmark is:

```text
maze_size * 2 ** (num_unlocked(Unlocks.Mazes) - 1)
```

The runner requires a 32x32 world and 32 available drones. Every mode starts with oversized benchmark resources and is measured against the same fixed Gold target, `200000` by default, using seeds 1, 2, and 3 at simulation speedup 64.

| Mode | Name | Description |
| ---: | --- | --- |
| 6 | `current-reference-32` | Current single-drone reference tree-rebalancing strategy on one full 32x32 Maze, created by Weird-Substance amount only |
| 7 | `cover-3x3` | One 3x3 Maze; DFS distributes one stationary drone onto every Maze cell so Treasure lookup becomes movement-free |
| 8 | `cover-4x4` | One 4x4 Maze with one stationary drone per Maze cell |
| 9 | `cover-2x4x4` | Two independent 4x4 Mazes, each fully covered by 16 stationary drones |
| 10 | `zapakh-32x4x4` | 32 independent 4x4 Mazes using a source-near port of zapakh's ranked in-situ DFS |
| 11 | `steam-32x4x4` | 32 independent 4x4 Mazes using the January 2026 Steam route-map / path-search implementation |

The coverage modes deliberately distribute drones by traversing the actual freshly-created Maze rather than assuming which absolute world coordinates a small Maze occupies.

### zapakh Gist reference

Source:

- https://gist.github.com/zapakh/9a9b39a07964bbd27ab8cbd05ca35501
- created 2024-05-22
- local provenance: `external/zapakh-maze-dfs/`

The Gist uses an iterative in-situ DFS. Each stack entry stores remaining directions plus the backtracking direction, and later direction choices are ranked toward the measured Treasure position.

The source predates the current Weird-Substance Maze API and uses Fertilizer to create/recycle Mazes. The benchmark preserves the DFS/search behavior but adapts Maze creation and Treasure relocation to the current `Items.Weird_Substance` API. It is therefore a source-near algorithm benchmark, not a byte-for-byte execution of the 2024 script.

### January 2026 32x4x4 Steam reference

Source:

- https://steamcommunity.com/app/2060160/discussions/0/810218160537152525/
- relevant post: 2026-01-20
- local provenance: `external/steam-32x4x4/`

The posted implementation runs one independent 4x4 Maze per drone. It first records a route and local connectivity, performs repeated route sweeps while walls open, then uses the discovered graph for path search to the measured Treasure.

The benchmark keeps that architecture while adding the repository's fixed-Gold stopping condition and safe current-API handling.

### Results

Results are intentionally pending until this amount-based suite is run in-game. Do not infer a winner from the historical full-world benchmarks or community throughput claims.

Benchmark implementation commit: `8fc91cd127cac271cd63e8a5fe1304c50c77d822`

---

# Benchmark results

Lower is better. Values are simulation runtime returned by `simulate()`.

## 8x8, 25 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 60.74 | 65.98 | 60.08 | 62.27 | 60.08 | 65.98 |
| reuse-bfs | 39.96 | 35.86 | 39.76 | 38.53 | 35.86 | 39.96 |
| reuse-tree-greedy | 26.95 | 24.20 | 26.99 | 26.05 | 24.20 | 26.99 |
| reuse-tree-greedy-lazy-rebalance | 26.95 | 24.22 | 26.99 | 26.05 | 24.22 | 26.99 |
| reuse-tree-greedy-full-reindex | 26.95 | 24.22 | 26.99 | 26.05 | 24.22 | 26.99 |
| **reference-tree-rebalancing** | **22.03** | **20.43** | **23.28** | **21.91** | **20.43** | **23.28** |

## 8x8, 100 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 235.98 | 232.10 | 226.45 | 231.51 | 226.45 | 235.98 |
| reuse-bfs | 110.74 | 110.62 | 109.65 | 110.34 | 109.65 | 110.74 |
| reuse-tree-greedy | 97.77 | 90.23 | 101.60 | 96.54 | 90.23 | 101.60 |
| reuse-tree-greedy-lazy-rebalance | 98.55 | 89.88 | 97.62 | 95.35 | 89.88 | 98.55 |
| reuse-tree-greedy-full-reindex | 107.77 | 92.07 | 103.44 | 101.09 | 92.07 | 107.77 |
| **reference-tree-rebalancing** | **73.50** | **73.70** | **77.10** | **74.77** | **73.50** | **77.10** |

## 8x8, 300 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 729.40 | 694.34 | 638.83 | 687.52 | 638.83 | 729.40 |
| reuse-bfs | 258.63 | 259.50 | 248.71 | 255.61 | 248.71 | 259.50 |
| reuse-tree-greedy | 271.95 | 256.17 | 273.12 | 267.08 | 256.17 | 273.12 |
| reuse-tree-greedy-lazy-rebalance | 231.45 | 250.59 | 247.80 | 243.28 | 231.45 | 250.59 |
| reuse-tree-greedy-full-reindex | 242.58 | 256.84 | 254.92 | 251.45 | 242.58 | 256.84 |
| **reference-tree-rebalancing** | **170.50** | **177.73** | **175.59** | **174.61** | **170.50** | **177.73** |

## 16x16, 25 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 228.32 | 262.07 | 172.15 | 220.85 | 172.15 | 262.07 |
| reuse-bfs | 122.89 | 113.90 | 141.48 | 126.09 | 113.90 | 141.48 |
| reuse-tree-greedy | 80.80 | 82.70 | 93.12 | 85.54 | 80.80 | 93.12 |
| reuse-tree-greedy-lazy-rebalance | 80.82 | 82.73 | 93.16 | 85.57 | 80.82 | 93.16 |
| reuse-tree-greedy-full-reindex | 80.82 | 82.73 | 93.16 | 85.57 | 80.82 | 93.16 |
| **reference-tree-rebalancing** | **70.39** | **72.30** | **84.30** | **75.66** | **70.39** | **84.30** |

## 16x16, 100 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 808.67 | 973.40 | 886.80 | 889.62 | 808.67 | 973.40 |
| reuse-bfs | 292.11 | 304.06 | 326.09 | 307.42 | 292.11 | 326.09 |
| reuse-tree-greedy | 366.87 | 437.15 | 454.84 | 419.62 | 366.87 | 454.84 |
| reuse-tree-greedy-lazy-rebalance | 277.19 | 385.94 | 350.04 | 337.72 | 277.19 | 385.94 |
| reuse-tree-greedy-full-reindex | 424.37 | 631.48 | 615.90 | 557.25 | 424.37 | 631.48 |
| **reference-tree-rebalancing** | **269.60** | **258.00** | **279.92** | **269.17** | **258.00** | **279.92** |

## 16x16, 300 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 2728.86 | 2694.53 | 2739.30 | 2720.90 | 2694.53 | 2739.30 |
| reuse-bfs | 694.40 | 750.70 | 744.06 | 729.72 | 694.40 | 750.70 |
| reuse-tree-greedy | 1072.23 | 1252.62 | 1567.85 | 1297.56 | 1072.23 | 1567.85 |
| reuse-tree-greedy-lazy-rebalance | 800.94 | 1105.90 | 955.93 | 954.26 | 800.94 | 1105.90 |
| reuse-tree-greedy-full-reindex | 1016.56 | 1391.60 | 1310.80 | 1239.65 | 1016.56 | 1391.60 |
| **reference-tree-rebalancing** | **604.06** | **564.65** | **577.93** | **582.21** | **564.65** | **604.06** |

## 32x32, 25 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 818.24 | 968.79 | 932.42 | 906.48 | 818.24 | 968.79 |
| reuse-bfs | 403.36 | 410.55 | 390.00 | 401.30 | 390.00 | 410.55 |
| reuse-tree-greedy | 257.85 | 313.90 | 311.91 | 294.56 | 257.85 | 313.90 |
| reuse-tree-greedy-lazy-rebalance | 257.85 | 313.90 | 311.95 | 294.57 | 257.85 | 313.90 |
| reuse-tree-greedy-full-reindex | 257.85 | 313.90 | 311.95 | 294.57 | 257.85 | 313.90 |
| **reference-tree-rebalancing** | **221.29** | **270.30** | **273.24** | **254.94** | **221.29** | **273.24** |

## 32x32, 100 relocations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh-right-hand | 3588.08 | 3580.60 | 3640.59 | 3603.09 | 3580.60 | 3640.59 |
| reuse-bfs | 1078.71 | 910.70 | 1022.18 | 1003.86 | 910.70 | 1078.71 |
| reuse-tree-greedy | 2270.39 | 2087.10 | 2012.77 | 2123.42 | 2012.77 | 2270.39 |
| reuse-tree-greedy-lazy-rebalance | 1113.70 | 1625.50 | 1411.72 | 1383.64 | 1113.70 | 1625.50 |
| reuse-tree-greedy-full-reindex | 8627.46 | 9923.28 | 11679.18 | 10076.64 | 8627.46 | 11679.18 |
| **reference-tree-rebalancing** | **975.35** | **930.96** | **945.66** | **950.66** | **930.96** | **975.35** |

This completed case is particularly informative:

- the reference strategy remains the fastest
- BFS becomes very competitive at this size, but still loses to the reference
- the old static generic tree scales badly
- lazy rebalancing helps substantially but remains slower than BFS/reference
- the generic full-reindex strategy becomes catastrophically expensive

## 32x32, 300 relocations — partial run

The benchmark was intentionally stopped because the runtime cost was no longer justified after the trend was already clear.

Available values:

| Strategy | Seed 1 |
| --- | ---: |
| fresh-right-hand | 10685.27 |
| reuse-bfs | 2611.09 |
| reuse-tree-greedy | not completed |
| reuse-tree-greedy-lazy-rebalance | not completed |
| reuse-tree-greedy-full-reindex | not completed |
| reference-tree-rebalancing | not completed |

Do not infer missing values from smaller cases. This is intentionally partial benchmark data.

---

# Interpretation and conclusions

## 1. Fresh Maze recreation is decisively inefficient

Repeatedly creating a fresh Maze is the worst tested strategy at every completed size/horizon.

The one-time mapping cost of reuse is quickly amortized.

Examples:

- 8x8 / 25:
  - fresh 62.27
  - reference 21.91
- 16x16 / 300:
  - fresh 2720.90
  - reference 582.21
- 32x32 / 25:
  - fresh 906.48
  - reference 254.94

Therefore production should continue to reuse Mazes.

## 2. The reference strategy wins before rebalancing matters

At 25 relocations, the generic tree variants are effectively identical because later Greedy/rebalancing phases have barely or not yet activated.

Yet the reference implementation is already clearly faster:

- 8x8 / 25:
  - generic tree 26.05
  - reference 21.91
- 16x16 / 25:
  - generic tree 85.54
  - reference 75.66
- 32x32 / 25:
  - generic tree 294.56
  - reference 254.94

This is strong evidence that the advantage is not only tree rebalancing.

Likely contributors:

- better initial ordered tree representation
- direct `val/max_val` subtree routing
- lower path-construction overhead
- useful Treasure relocations while the initial DFS map is still being built

Future optimization should use the reference implementation as the baseline rather than the older generic tree modes.

## 3. A static historical tree gets worse as the Maze opens

The reused Maze becomes increasingly unlike the initial tree because walls disappear.

The static generic tree therefore becomes a poor representation of available paths.

At long horizons it can even lose to BFS.

8x8 / 300:

- BFS: 255.61
- static tree+greedy: 267.08

16x16 / 300:

- BFS: 729.72
- static tree+greedy: 1297.56

This effect becomes much worse as world size grows.

## 4. Rebalancing matters more with longer runs and larger Mazes

At 25 relocations, the generic tree variants are almost identical.

At longer horizons, lazy rebalancing becomes substantially better than the static generic tree.

16x16 / 300:

- static tree: 1297.56
- lazy rebalance: 954.26

That is a meaningful improvement, but still much slower than the reference at 582.21.

Conclusion: adapting the tree to newly opened Maze edges is important, but our old generic rebalancing design is not sufficient.

## 5. Naive full reindexing becomes catastrophically expensive on large Mazes

The generic `reuse-tree-greedy-full-reindex` mode scales extremely poorly.

16x16 / 100:

- lazy rebalance: 337.72
- generic full reindex: 557.25

The completed 32x32 / 100 run is the strongest warning:

- generic full reindex average: **10076.64**
- reference average: **950.66**

The generic full-reindex mode is therefore more than 10x slower than the reference in this case.

This does **not** prove that full reindexing itself must be removed from the reference strategy.

The reference also reindexes, yet it remains the fastest implementation.

The lesson is narrower:

> Full-tree maintenance is only acceptable when the surrounding tree representation, rotation frequency, and routing strategy make the benefit worth the cost.

Do not transplant the old generic full-reindex design into production.

## 6. BFS is a surprisingly strong fallback at larger sizes

BFS is not competitive with the reference in completed tests, but it scales much more predictably than the old generic tree.

16x16 / 100:

- BFS: 307.42
- static generic tree: 419.62
- reference: 269.17

16x16 / 300:

- BFS: 729.72
- static generic tree: 1297.56
- reference: 582.21

For future experiments, BFS remains a useful correctness/performance baseline.

## 7. The reference strategy is currently the production baseline

The reference implementation is the fastest tested strategy in every completed benchmark case:

- 8x8 / 25
- 8x8 / 100
- 8x8 / 300
- 16x16 / 25
- 16x16 / 100
- 16x16 / 300
- 32x32 / 25
- 32x32 / 100

This is strong evidence to keep the reference architecture in production. The 32x32 / 300 case was stopped early only because the runtime cost of the remaining historical baselines was no longer worth it.

---

# Recommended next optimization work

Do not restart from BFS or the old generic tree.

Use `reference-tree-rebalancing` as the baseline and perform ablation tests.

## High-value ablation modes

Add reference-derived modes to `bench_maze.py` such as:

1. reference without reroot
2. reference without Greedy
3. reference without rotations/rebalancing
4. reference without both Greedy and rebalancing
5. reference with rebalancing but incremental/local metadata updates instead of full reindex
6. reference with different rebalancing depth threshold
7. reference with different Greedy start point
8. reference with different reroot timing
9. reference with world-size-dependent thresholds

These experiments will tell us which parts of the reference actually create its advantage.

## Especially important question: why is the reference faster at 25?

Because the reference already wins before the later optimization phases dominate, isolate the initial behavior first.

A useful benchmark sequence would be:

```text
reference full
reference initial-tree only
generic tree using reference val/max_val representation
reference mapping without Treasure relocation during DFS
```

This can separate:

- mapping overhead
- routing representation
- incidental Treasure collection during mapping

## Investigate local/incremental reindexing

The generic full-reindex benchmark shows that whole-tree work can explode on 32x32.

Possible improvement:

- rotate one branch
- update only the affected branch/subtree
- propagate `max_val` changes only through impacted ancestors
- avoid walking unrelated nodes

But correctness of subtree ranges is essential. A faster broken tree is not useful.

Benchmark this against the unchanged reference using identical seeds.

## Consider world-size-dependent tuning

A constant threshold optimized for 8x8 may not be optimal for 32x32.

Candidates:

```text
MAZE_GREEDY_AFTER
MAZE_REROOT_AT
MAZE_REBALANCE_FROM
MAZE_REBALANCE_ACTIVE_UNTIL
MAZE_REBALANCE_UNTIL
MAZE_REUSE_LIMIT
```

The 32x32 data suggests algorithmic overhead grows much faster than on small maps, so adaptive values may be beneficial.

## Benchmark only where information value justifies runtime

The 32x32 runs are expensive.

Do not automatically rerun the entire 6-strategy matrix for every change.

Recommended workflow:

1. benchmark new reference-derived variant against the current reference only
2. use 8x8 and 16x16 first
3. promote only promising variants to 32x32
4. use one or two fixed seeds initially
5. run the full seed matrix only for finalists

The old strategies can remain in `bench_maze.py` as historical baselines, but they do not need to run in every optimization iteration.

---

# Production invariants for future agents

Before changing `maze.py`, preserve these unless a benchmarked replacement explicitly supersedes them:

- Gold -> Gold must not rebuild the normal farm.
- Maze state must be reset when leaving Gold.
- Farm expansion invalidates Maze coordinates/state.
- Initial fresh Maze has no loops; reused Maze can have loops.
- Tree nodes contain cyclic parent/child references; never compare complete node dictionaries.
- The final Treasure must still be harvested after the relocation limit.
- Insufficient Weird Substance must not leave the main planner stuck forever in an unusable Maze state.
- Changes should be measured with `simulate()`, not judged by source-code simplicity.
- The current reference strategy is the performance baseline.
