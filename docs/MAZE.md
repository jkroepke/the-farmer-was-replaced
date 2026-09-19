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

Gold production now has two paths.

### Primary path: adaptive parallel small Mazes

New Gold phases use `maze_parallel.py` whenever the current farm can place at least two independent small Mazes.

The planner evaluates 4x4 and 3x3 layouts:

- capacity is `floor(world_size / maze_size) ** 2`
- active workers are `min(max_drones(), capacity)`
- the heuristic score is `workers * maze_size * maze_size`
- 4x4 wins ties

This makes the production layout adapt automatically to both farm size and available drones.

Examples:

- 32x32 / 32 drones -> 32 independent 4x4 Mazes
- 16x16 / 16 drones -> 16 independent 4x4 Mazes
- 8x8 / >=4 drones -> 4 independent 4x4 Mazes
- 6x6 / >=4 drones -> 4 independent 3x3 Mazes
- only one usable small-Maze worker -> fall back to the reference single-Maze strategy

The 32x32 / 32-drone 4x4 choice is benchmarked. The adaptive 3x3 choice for smaller intermediate farm states is currently a heuristic and is not yet independently benchmarked.

Each parallel worker uses the zapakh-style ranked iterative DFS from the winning benchmark mode.

### Parallel lifecycle

A production burst is fully funded before it starts.

`config.MAZE_PARALLEL_RELOCATIONS = 25` is the minimum start threshold. If more Weird Substance is already available, production automatically raises the relocation budget for all workers, capped at `MAZE_REUSE_LIMIT`. The minimum reserve funds:

1. one Maze creation
2. 25 Treasure relocations
3. the final Treasure harvest, which needs no Weird Substance

The required stockpile is therefore:

```text
maze_size
* 2 ** (maze_level - 1)
* worker_count
* (MAZE_PARALLEL_RELOCATIONS + 1)
```

At 32x32, 32 drones, 4x4 Mazes, and the full x32 Maze multiplier:

```text
4 * 32 * 32 * 26 = 106496 Weird Substance
```

The minimum 25-relocation burst produces approximately:

```text
16 * 32 * 32 * 26 = 425984 Gold
```

The normal farm keeps fertilizing until this complete Weird-Substance budget is available. This deliberately prevents a parallel Gold job from starving while dozens of drones are already inside their Mazes.

Workers use the tested start barrier:

1. children move to their assigned origins
2. each child plants a Bush and waits
3. the parent confirms every child Bush
4. the parent creates its own Maze
5. the guaranteed Weird-Substance inventory change releases all children
6. every worker creates and solves its own Maze
7. the parent waits for all spawned workers before returning to the main loop

Production prints the chosen dynamic budget, minimum reserve, and currently available stock. With exactly the minimum reserve this is approximately:

```text
MAZE PARALLEL 4 workers 32 relocations 25 minimum substance 106496 available substance 106496
```

With about 186000 Weird Substance on the same 32x4x4 plan, the dynamic budget is about 44 relocations per worker, consuming about 184320 substance and producing roughly 737280 Gold before final harvest completion.

If Gold production cannot start, `production.py` prints `MAZE WAIT bushes ...` or `MAZE WAIT substance ...` so the blocking prerequisite is visible.

### Fallback path: reference full Maze

If fewer than two independent small Mazes can be placed, `maze.py` keeps the previous persistent reference tree-rebalancing strategy.

An already-active reference Maze is never switched to the parallel strategy mid-lifecycle.

The legacy fallback still uses:

```text
MAZE_STOCKPILE = 5
MAZE_REUSE_LIMIT = 300
MAZE_GREEDY_AFTER = 30
MAZE_REROOT_AT = 40
MAZE_REBALANCE_FROM = 40
MAZE_REBALANCE_ACTIVE_UNTIL = 80
MAZE_REBALANCE_UNTIL = 140
```

### Gold planner interaction

`production.py` treats Gold specially:

- before parallel Gold production:
  - require the complete Weird-Substance burst reserve
  - require enough resources for one Bush per planned worker
- Gold -> Gold:
  - do not rebuild the normal farm unnecessarily
- if the next Gold burst is not yet funded:
  - restore the normal farm once
  - run high-throughput Hay/fertilizer production until the full reserve is available
- Gold -> non-Gold:
  - reset Maze state and restore the normal farm once
- farm expansion:
  - reset Maze state before using the new coordinates

The benchmark that selected 32x4x4 zapakh production is commit `55734c855dd464dd846deef280d8a65d9f2c3bf7`.

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

Coverage workers detect the 300-relocation limit from a failed Weird-Substance `use_item()` call. `measure()` continues to return the Treasure position at the cap, so it must not be used as the cap signal. The Treasure is then harvested and the fixed-root creator recreates the small Maze.

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

### Reddit 32-square full-field packing follow-up

A September 2026 Reddit thread adds a new geometry optimization:

https://www.reddit.com/r/TheFarmerWasReplaced/comments/1wjxxhx/my_best_attempt_at_mazes_524_leaderboard_as_of/

The author runs one square Maze per drone and reports that lowering the maximum
individual Maze size improves leaderboard performance. A comment points out
that a complete 32-square tiling of the 32x32 field exists with integer side
lengths from 4 through 7. The author tried the linked alternative layout and
reported improving from leaderboard position #524 to #514.

The repository independently reconstructed and verified a full exact cover:

```text
12 x 4x4
 4 x 5x5
 4 x 6x6
12 x 7x7
```

The 32 squares cover all 1024 cells exactly once. The concrete coordinates are
stored in `bench_maze.py::SPEC_PACKED_32`.

This geometry is interesting because the current measured
`zapakh-32x4x4` strategy only occupies 32 * 16 = 512 cells of the farm.
A full packed solve covers 1024 cells while still using exactly 32 drones.

The thread also suggests handling loops in reused Mazes by treating a
currently-visited cell as blocked for the rest of that solve. The repository's
zapakh DFS already does this through its per-solve `visited` set, so reuse is
a meaningful extension even though the Reddit author describes a fresh-only
solver.

### Extended reference + mutation matrix

The Packed follow-up has been expanded into a deliberate ablation matrix.

Reference/source-near families:

- mode 10 — `ref-zapakh-4-reuse300`
  - current measured winner/control
  - source-near ranked iterative DFS
- mode 11 — `ref-steam-4-reuse300`
  - January 2026 route/map/path-search architecture
- mode 14 — `ref-msmith93-full32-fresh`
  - source-near port of the archived multi-drone full-Maze implementation
  - deliberately kept last in the run because its original shared-world
    synchronization is the riskiest
- mode 15 — `ref-reddit5-map-bfs-reuse300`
  - source-described February 2026 architecture
  - 32 independent 5x5 Mazes
  - right-hand fresh-Maze map
  - BFS routing
  - learn newly opened walls during reuse
  - reuse 300 then remap
- mode 16 — `desc-reddit-packed-fresh`
  - source-described September 2026 fresh-Maze solver
  - forced corridors
  - record intersections
  - choose the branch best aligned with the Treasure vector
  - backtrack recorded movement on dead ends
  - no reuse, matching the author's stated assumption

No source code is available for the two Reddit descriptions. They are behavioral
reconstructions, not byte-for-byte ports.

Mutation/ablation modes:

| Mode | Name | Question |
| ---: | --- | --- |
| 12 | `mut-packed-zapakh-fresh` | Full 4..7 packing without reuse |
| 13 | `mut-packed-zapakh-reuse300` | Full packing + current ranked DFS + max reuse |
| 17 | `mut-reddit-packed-visited-reuse300` | Can the Reddit branch solver be made loop-safe with a visited set? |
| 18 | `mut-packed-zapakh-reuse1` | Reuse-cap sweep |
| 19 | `mut-packed-zapakh-reuse2` | Reuse-cap sweep |
| 20 | `mut-packed-zapakh-reuse4` | Reuse-cap sweep |
| 21 | `mut-packed-zapakh-reuse8` | Reuse-cap sweep |
| 22 | `mut-packed-zapakh-reuse16` | Reuse-cap sweep |
| 23 | `mut-packed-unranked-fresh` | Does Treasure-direction ranking help on fresh Mazes? |
| 24 | `mut-packed-unranked-reuse300` | Does ranking still matter after walls open? |
| 25 | `mut-uniform4-zapakh-fresh` | Isolate fresh-vs-reuse on the old 4x4 geometry |
| 26 | `mut-uniform5-zapakh-reuse300` | Isolate 5x5 geometry from map+BFS |
| 27 | `mut-uniform5-zapakh-fresh` | Uniform 5x5 fresh control |
| 28 | `mut-packed-map-bfs-reuse300` | Put February map+BFS on the 4..7 full-field packing |
| 29 | `mut-packed-map-bfs-fresh` | Mapping overhead without reuse |
| 30 | `mut-uniform4-map-bfs-reuse300` | Isolate map+BFS solver from 5x5 geometry |
| 31 | `mut-uniform4-zapakh-reuse8` | Reuse-cap control on the existing uniform 4x4 layout |

The runner is split into four groups so an unsafe historical reference cannot
hide all newer results:

1. `MAZE CORE` — fast ranked/unranked/Reddit/pacing ablations
2. `MAZE MAP` — Steam and map+BFS families
3. `MAZE SUSTAINED` — selected architectures at a 1,000,000 Gold target
4. `MAZE LEGACY REF` — msmith93 last

Short-screen configuration:

```text
Gold target: 200000
Seeds: 1, 2, 3
Speedup: 64
```

Sustained configuration:

```text
Gold target: 1000000
Seeds: 1, 2
Speedup: 64
```

Every special result now reports:

- Gold gained
- fixed Gold target
- Weird Substance consumed
- tick count
- PASS/FAIL

This makes runtime and resource efficiency independently comparable.

Extended benchmark code state: `c045c3da2a015b77491532199fc3f0735cc2a640`.

Local provenance:

- `external/reddit-32-square-maze/README.md`
- `external/reddit-5x5-bfs/README.md`
- `external/zapakh-maze-dfs/README.md`
- `external/steam-32x4x4/README.md`
- `external/msmith93-thefarmerwasreplaced/source/multidrone/maze_leaderboard.py`

A first extended run exposed a lifecycle bug in the benchmark harness: the
post-harvest helper returned to a Maze origin by moving only East and then
North. For short reuse caps this could wrap almost the entire world and become
blocked by a neighboring active Maze. That run stalled at
`mut-packed-zapakh-reuse1` after `PACKED REUSE READY 31`.

The helper now chooses the shortest toroidal direction on each axis and returns
failure if the path is blocked. Rebuild lifecycle callers propagate that
failure instead of creating a new Maze at the wrong location.

The runner also starts with a 100000-Gold
`MAZE REBUILD SMOKE` using `mut-packed-zapakh-reuse1` before executing the
full matrix.

Partial timings collected before this fix are diagnostic only and must not be
mixed into the final matrix.

Results for this extended matrix are intentionally pending an in-game run.
The last measured winner remains `zapakh-32x4x4` from benchmark commit
`55734c855dd464dd846deef280d8a65d9f2c3bf7`.

### Extended 2026-09-19 benchmark results

Measured against benchmark code commit
`c045c3da2a015b77491532199fc3f0735cc2a640`.

The rebuild smoke test passed:

| Mode | Target | Runtime | Gold | Substance | Ticks |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mut-packed-zapakh-reuse1` | 100000 | 15.98 | 126368 | 27392 | 93546 |

This confirms that the short-reuse lifecycle hang was fixed before the full
matrix.

#### 200000-Gold core screen

| Mode | Avg | Min | Max |
| --- | ---: | ---: | ---: |
| `ref-zapakh-4-reuse300` | 13.92 | 13.70 | 14.06 |
| `mut-packed-zapakh-fresh` | 21.97 | 21.60 | 22.60 |
| `mut-packed-zapakh-reuse300` | 19.59 | 18.98 | 20.10 |
| `desc-reddit-packed-fresh` | 19.91 | 19.10 | 20.54 |
| `mut-reddit-packed-visited-reuse300` | 16.19 | 15.70 | 16.87 |
| `mut-packed-zapakh-reuse1` | 19.78 | 18.67 | 20.51 |
| `mut-packed-zapakh-reuse2` | 19.35 | 19.00 | 20.04 |
| `mut-packed-zapakh-reuse4` | 19.09 | 18.20 | 20.39 |
| `mut-packed-zapakh-reuse8` | 19.56 | 19.13 | 20.16 |
| `mut-packed-zapakh-reuse16` | 19.84 | 18.98 | 20.39 |
| `mut-packed-unranked-fresh` | 22.30 | 21.80 | 22.60 |
| `mut-packed-unranked-reuse300` | 18.62 | 18.24 | 19.26 |
| `mut-uniform4-zapakh-fresh` | 16.91 | 16.80 | 16.99 |
| `mut-uniform5-zapakh-reuse300` | 15.92 | 15.27 | 16.50 |
| `mut-uniform5-zapakh-fresh` | 19.09 | 18.94 | 19.22 |
| `mut-uniform4-zapakh-reuse8` | 13.98 | 13.63 | 14.49 |

The packed Zapakh reuse-cap sweep is comparatively flat. Reuse=4 is the best
of those packed Zapakh caps at 19.09 average, but still much slower than the
uniform 4x4 control.

#### 200000-Gold map/BFS screen

| Mode | Avg | Min | Max |
| --- | ---: | ---: | ---: |
| `ref-steam-4-reuse300` | 21.08 | 21.00 | 21.13 |
| `ref-reddit5-map-bfs-reuse300` | 16.09 | 15.74 | 16.29 |
| `mut-packed-map-bfs-reuse300` | 18.74 | 18.40 | 19.06 |
| `mut-packed-map-bfs-fresh` | 41.29 | 40.43 | 41.80 |
| **`mut-uniform4-map-bfs-reuse300`** | **13.29** | **13.24** | **13.32** |

For the short 200000-Gold workload, uniform 4x4 map+BFS is the fastest raw
simulation-time result in the full extended matrix.

After normalizing each run for its discrete Gold overshoot, its advantage over
`ref-zapakh-4-reuse300` is only about 2.6%, so these two short-workload
strategies are effectively close. Their normalized tick counts are also almost
identical; do not treat the short-screen result alone as sufficient evidence
for a production change.

#### 1000000-Gold sustained screen

| Mode | Avg | Min | Max |
| --- | ---: | ---: | ---: |
| `ref-zapakh-4-reuse300` | 38.40 | 38.40 | 38.40 |
| `mut-packed-zapakh-reuse300` | 43.20 | 42.30 | 44.10 |
| `desc-reddit-packed-fresh` | 48.69 | 48.48 | 48.90 |
| `mut-reddit-packed-visited-reuse300` | 34.20 | 33.80 | 34.60 |
| **`ref-reddit5-map-bfs-reuse300`** | **31.72** | **31.64** | **31.80** |
| `mut-packed-unranked-reuse300` | 43.12 | 43.00 | 43.24 |
| `mut-packed-map-bfs-reuse300` | 33.65 | 33.63 | 33.67 |
| `mut-packed-zapakh-reuse8` | 44.68 | 44.57 | 44.78 |

The 5x5 map+BFS reference is the measured sustained winner in this set. After
normalizing the small Gold overshoot, it is about 21% faster than the current
4x4 Zapakh reference at 1M Gold.

Resource efficiency also shifts strongly in favor of the larger/map-based
layouts:

- 4x4 Zapakh: about 0.254 Weird Substance / Gold
- 5x5 map+BFS: about 0.205 Weird Substance / Gold
- packed map+BFS: about 0.197 Weird Substance / Gold

The packed map+BFS layout is slightly slower than 5x5 at 1M but consumes even
less Weird Substance per Gold.

A simple two-point cold-start/steady-state estimate using the 200k and 1M
measurements suggests:

- 4x4 Zapakh: low setup cost, roughly 30.8 seconds per additional 1M Gold
- 5x5 map+BFS: higher setup cost, roughly 19.6 seconds per additional 1M Gold
- packed map+BFS: highest setup cost of these three, roughly 18.8 seconds per
  additional 1M Gold

This is only an interpolation from two workloads, not a replacement for the
real leaderboard benchmark, but it explains why the ranking changes as the
target grows.

#### Legacy full-Maze source reference

`ref-msmith93-full32-fresh` completed all three seeds:

| Avg | Min | Max |
| ---: | ---: | ---: |
| 40.26 | 32.77 | 51.33 |

It is both slower and much more seed-sensitive than the small-Maze strategies.

#### Durable conclusions from the extended matrix

- Fresh-only strategies are consistently poor for sustained Gold.
- Reuse is essential.
- Full-field 4..7 packing is not automatically faster than uniform layouts.
- Treasure-vector direction ranking is not universally beneficial; packed
  unranked reuse300 beat packed ranked Zapakh reuse300.
- map+BFS has substantial setup cost but much better sustained behavior.
- uniform 5x5 is a strong sustained geometry.
- uniform 4x4 map+BFS is the short-workload winner, but it was accidentally
  omitted from the 1M sustained set and must be measured there before replacing
  production.
- the next decisive benchmark must use the real Maze leaderboard target,
  9863168 Gold, because repository leaderboard rules require end-to-end runtime
  including setup and termination.

### Results

Final 200000-Gold special benchmark, tested against code commit `55734c855dd464dd846deef280d8a65d9f2c3bf7`.

All 18 runs passed their internal Gold-target assertion.

| Mode | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `current-reference-32` | 121.29 | 117.42 | 129.17 | 122.63 | 117.42 | 129.17 |
| `cover-3x3` | 35.27 | 33.20 | 31.84 | 33.44 | 31.84 | 35.27 |
| `cover-4x4` | 28.20 | 28.28 | 28.12 | 28.20 | 28.12 | 28.28 |
| `cover-2x4x4` | 22.54 | 21.40 | 21.09 | 21.68 | 21.09 | 22.54 |
| **`zapakh-32x4x4`** | **13.87** | **13.27** | **13.40** | **13.51** | **13.27** | **13.87** |
| `steam-32x4x4` | 22.07 | 22.03 | 22.11 | 22.07 | 22.03 | 22.11 |

Gold gained per run:

| Mode | Seed 1 | Seed 2 | Seed 3 | Average |
| --- | ---: | ---: | ---: | ---: |
| `current-reference-32` | 229376 | 229376 | 229376 | 229376 |
| `cover-3x3` | 200160 | 200160 | 200160 | 200160 |
| `cover-4x4` | 200192 | 200192 | 200192 | 200192 |
| `cover-2x4x4` | 200192 | 200192 | 200192 | 200192 |
| `zapakh-32x4x4` | 211968 | 210432 | 212992 | 211797 |
| `steam-32x4x4` | 202752 | 205312 | 208384 | 205483 |

Because Treasure rewards are discrete, modes overshoot the 200000 target by different amounts. Raw runtime-to-target therefore slightly favors modes with smaller overshoot. Normalizing each run to exactly 200000 Gold gives these approximate equivalent runtimes:

| Mode | Normalized 200k runtime | Speedup vs current |
| --- | ---: | ---: |
| `current-reference-32` | 106.92 | 1.00x |
| `cover-3x3` | 33.41 | 3.20x |
| `cover-4x4` | 28.17 | 3.80x |
| `cover-2x4x4` | 21.66 | 4.94x |
| **`zapakh-32x4x4`** | **12.76** | **8.38x** |
| `steam-32x4x4` | 21.48 | 4.98x |

Raw average runtime-to-target gives `zapakh-32x4x4` a 9.08x speedup over `current-reference-32`. The Gold-normalized comparison is the more conservative figure and still shows an 8.38x throughput improvement.

The benchmark therefore establishes `zapakh-32x4x4` as the current performance candidate for production Gold farming on a 32x32 farm with 32 drones.

The suite runs through `simulate()`. Gold earned inside a simulation is isolated from the real farm inventory; only the runtime is returned to the caller. Every special mode prints an internal `MAZE SPECIAL RESULT` line with Gold gained, target, and PASS/FAIL before the simulation exits.

Current benchmark implementation commit: `55734c855dd464dd846deef280d8a65d9f2c3bf7`

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
