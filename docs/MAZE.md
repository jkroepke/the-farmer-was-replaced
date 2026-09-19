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

## Benchmarks

Measured Maze and spawn-locality results are maintained in `bench/maze.md`.

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
