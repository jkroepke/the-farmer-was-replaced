# nql1314/The-Farmer-Was-Replaced-AI-Code

## Upstream

- URL: https://github.com/nql1314/The-Farmer-Was-Replaced-AI-Code
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `688325db004607563e59535a15ce94fad092ff9f`
- Snapshot files: 78
- Snapshot size: 750854 bytes
- License metadata: no repository license is declared upstream
- Snapshot status: complete pinned source tree mirrored unchanged under `source/`

This repository is unusually valuable as a research archive because it contains not only final scripts, but multiple generations of experiments, benchmark-oriented variants, design documents, archived failures, and the author's own reasoning about drone coordination.

The mirror intentionally preserves all of that material unchanged. Current-game interpretation belongs in this README.

## Executive summary

The repository explores almost every performance-sensitive TFWR mechanic:

- multi-drone resource farming
- persistent worker pools
- companion-map coordination
- parallel Cactus sorting
- specialized Pumpkin region layouts
- Sunflower petal-order harvesting
- Maze map caching + BFS
- Dinosaur Hamiltonian routing and A*
- traversal precomputation
- tick-level instrumentation
- custom queue/data-structure patterns

The most important validity split is:

### Still useful today

- persistent workers
- stable spatial partitioning
- row/column phase separation for Cactus
- precomputed movement tables
- worker-local state
- specialized Pumpkin layouts
- petal-aware Sunflower harvesting
- Maze map caching
- Hamiltonian indexing
- tail-aware Dinosaur safety ideas
- explicit `get_tick_count()` measurements

### Historically real but invalid now

A large part of the later multi-drone architecture relies on a historical engine bug where multiple drones could call `wait_for()` on one completed source drone and receive references to the same mutable returned object.

The upstream repository contains direct evidence that this behavior existed in October 2025.

The current game no longer behaves this way.

This project's runtime probe on 2026-09-19 reproduces the upstream pattern and observes isolated mutable lists instead of shared state.

Therefore:

> Keep the algorithms and worker-lifetime ideas, but remove any coordination that depends on shared mutable Python objects across drones.

## Repository structure

### Current/primary scripts

- `cactus_farm_mega.py`
- `resource_farm_mega.py`
- `sunflower_farm_mega.py`
- `maze_solver_ultra.py`
- `pumpkin_6x6.py`
- `pumpkin_v10.py`
- `snakeV2.py`
- `farm_utils.py`
- `utilsFarm.py`

### Pumpkin evolution

- `rank/pumpkin_v1.py` through `rank/pumpkin_v9.py`
- `pumpkin_v10.py`
- `pumpkin_6x6.py`
- `pumpkin_single_v1.py`

### Archived experiments

The `archived/` directory contains earlier Cactus, Pumpkin, Sunflower, Maze, resource-farm, communication, and drone-memory experiments.

This is important because some archived files are more useful as mechanic evidence than the final files.

### Design/research documentation

`docs/` contains extensive notes for:

- persistent workers
- shared-memory discovery
- drone-memory tests
- resource farming
- Cactus/Pumpkin/Sunflower optimization
- Maze
- Dinosaur A*
- dynamic task queues
- fertilizer experiments

### Cursor research material

`.cursor/rules/` contains AI-oriented project rules plus a separate Dinosaur A* prototype.

## Historical shared-memory discovery

The key reproducer is:

`archived/ref_test.py`

It:

1. spawns one source drone that returns `[]`
2. spawns multiple worker drones
3. every worker calls `wait_for(source)`
4. every worker appends its own value
5. historical output shows cumulative mutations

`docs/DRONE_SHARED_MEMORY_DISCOVERY.md` records the experiment date as 2025-10-23 and explicitly distinguishes this behavior from ordinary globals/closures, which were already known to be copied.

The upstream interpretation was:

```text
wait_for(source) -> same mutable object reference
```

This enabled architectures containing:

- shared task queues
- shared companion maps
- shared worker statistics
- parent-controlled priority values
- cross-worker stop flags
- synchronization flags

### Current-game invalidation

Current Megafarm semantics state that drones have separate memory and passed arguments are copied.

The game subsequently shipped fixes explicitly mentioning shared-memory bugs.

This project's local probe:

- `drone_mem_probe.py`
- `drone_mem_run.py`

observed on 2026-09-19:

```text
DRONE MEMORY PROBE initial []
DRONE MEMORY STEP 1 worker [1] source [] initial-view []
DRONE MEMORY STEP 2 worker [2] source [] initial-view []
DRONE MEMORY STEP 3 worker [3] source [] initial-view []
DRONE MEMORY RESULT isolated
```

So the historical result should not be dismissed as a bad assumption; it was apparently a real engine behavior that was later removed.

For current production code, however, it is invalid.

## Persistent drone pool

`docs/PERSISTENT_DRONE_POOL.md` and `resource_farm_mega.py` contain one of the strongest architectural ideas in the repository.

The intended pattern is:

1. partition the field once
2. spawn long-lived workers once
3. every worker loops forever in its assigned region
4. avoid repeated `spawn_drone()` cost
5. let the parent perform only monitoring/coordination

That worker-lifetime model remains valid and highly relevant.

### What must be removed

The implementation uses shared state for:

- `priority`
- `should_stop`
- `companion_map`
- cross-worker statistics

Those fields are obtained from the historical shared-`wait_for()` object and therefore do not provide current cross-drone coordination.

### What remains reusable

`calculate_regions()` chooses stable spatial regions:

- 4x4 grid for 16+ drone capacity
- 3x3 for 9+
- 2x2 for 4+
- two horizontal halves for 2+
- one full-field worker otherwise

Each worker snake-traverses its region continuously.

That combination is still a strong current candidate:

> persistent workers + static spatial ownership + independent decisions derived from globally visible game state.

A current implementation can replace shared `priority` with each worker independently reading `num_items()`.

Cross-region companion requests require a different design.

## Resource farming

`resource_farm_mega.py` balances:

- Hay
- Wood
- Carrot

using target ratios.

It deliberately uses multiplication instead of division in the priority comparison.

Worker crop selection changes density according to priority:

- more Trees during Wood priority
- more Carrots during Carrot priority
- otherwise more Grass

It also tries to maintain a global companion coordinate map.

### Reusable parts

- inventory-driven priority
- static regional locality
- long-lived workers
- serpentine traversal
- avoiding repeated setup
- keeping worker statistics local

### Invalid current parts

- global mutable companion map
- parent broadcast of priority through shared Python state
- shared stats dictionary
- stop flag broadcast

The generic scheduler concept is still useful, but coordination must use current mechanics.

## Cactus

`cactus_farm_mega.py` is structurally stronger than many community Cactus scripts.

Its cycle is explicitly phase-separated:

1. parallel planting
2. parallel sort of all rows
3. wait for row workers
4. parallel sort of all columns
5. wait for column workers
6. single chain-harvest attempt

This is a good concurrency invariant.

Rows do not race with columns.

Each row/column worker repeatedly bubble-sorts until no swaps occur.

### Useful features

- worker groups scale from `max_drones()`
- parent performs one task instead of spawning every slot
- phase-level `get_tick_count()` measurements
- swap counters
- explicit expected chain-yield check
- fallback harvesting when chain harvest is incomplete

### Performance caveat

The implementation is intentionally verbose:

- repeated `quick_print()`
- printing whole grids
- repeated `goto()`
- bubble sorting to local convergence

Use the architecture as a reference, not the literal hot path as an optimized production implementation.

The strongest reusable rule is:

> rows with rows, barrier, columns with columns, barrier, one harvest.

## Pumpkin research

Pumpkin is the deepest optimization area in the repository.

The mirror includes:

- generic archived versions
- 12x12 and 16x16 variants
- mega variants
- `rank/pumpkin_v1.py` ... `v9.py`
- `pumpkin_v10.py`
- `pumpkin_6x6.py`

The sequence shows a progression from generic scanning toward increasingly static layouts and precomputed routes.

## Pumpkin design direction

The later versions trade flexibility for lower runtime overhead:

- fixed region placement
- dedicated workers
- 6x6/8x8 regions
- precomputed traversal paths
- split left/right workers
- reduced route computation
- targeted lists of unverified/dead cells
- localized watering/repair
- synchronized harvesting

This is a good example of an important TFWR optimization principle:

> spend code/data size to remove decisions and path computation from the hot loop.

### Shared-memory caveat in later variants

Some advanced Pumpkin variants coordinate worker pairs through structures obtained from a shared source drone.

Examples include:

- `ready`
- `help_flag`
- `unverified_left`
- `unverified_right`

Under current game semantics those cross-drone mutable structures are not a valid synchronization mechanism.

The spatial layouts and precomputed paths remain useful independently.

### Candidate extraction strategy

When adapting a Pumpkin version:

1. preserve its exact static region geometry
2. preserve precomputed traversal
3. remove shared-object synchronization
4. give each worker an independently completable region, or synchronize only through actual task completion/game state
5. benchmark the resulting source-near layout before further cleanup

## Sunflower

`sunflower_farm_mega.py` tries to maximize Power bonus by classifying flowers by petal count.

The intended pipeline is:

1. parallel plant/water batches
2. wait for growth
3. parallel scan
4. immediately harvest 15-petal flowers
5. place lower petal counts into per-value queues
6. harvest remaining queues in descending petal order

This is algorithmically much stronger than blind mature-Sunflower harvesting.

### Dynamic queue concept

Workers pop positions from one shared per-petal list until the list reaches a small sentinel size.

This is intended to provide:

- automatic load balancing
- no static assignment for harvest
- tolerance when another worker already harvested a position

The sentinel entries are used to reduce empty-list/race handling.

### Current validity

The dynamic queue itself depends on historical shared mutable `wait_for()` state.

So current workers cannot safely share/pop one Python list this way.

The useful current concepts are:

- petal bins
- descending harvest order
- parallel scanning
- static snake batches
- separate plant/scan/harvest phases

A current implementation should statically partition known positions or keep each worker's queue private.

## Maze

`maze_solver_ultra.py` uses a persistent discovered map:

```text
(x, y) -> {
    direction -> passable?
}
```

It combines:

- greedy exploration toward Treasure
- physical DFS-style backtracking
- cached wall/passability knowledge
- BFS through the known graph
- reuse of the same Maze by relocating Treasure

### Hybrid navigation

The solver first asks BFS for a route through known passages.

If the cached path fails because a wall changed, it records the failure and switches back to exploration.

This is a useful architecture for repeated Treasure relocation.

### Reuse policy

When Treasure is relocated, the solver keeps known passable information while dropping stale wall assumptions.

That is a reasonable attempt to reuse partial knowledge after Maze mutation.

### Performance caveat

The BFS queue stores full path lists:

```text
(x, y, path)
```

and creates:

```text
new_path = path + [direction]
```

for child states.

That produces repeated list copies and can be expensive in the game's interpreter.

The map-caching idea is stronger than this specific BFS representation.

For current Maze work, use this as an algorithm/data-structure reference rather than a faster-than-measured production claim.

## Dinosaur: `snakeV2.py`

`snakeV2.py` builds a skyscraper/Hamiltonian cycle for even world sizes.

It precomputes:

- ordered Hamiltonian positions
- coordinate -> Hamiltonian index

For each Apple it derives a "safe target" based on current snake length and nominal cycle order.

It then tries to construct a direct route toward that target; otherwise it advances on the Hamiltonian cycle.

### Useful ideas

- coordinate -> cycle index dictionary
- nominal safe target from body length
- direct Apple routing only when cycle ordering looks safe
- deterministic Hamiltonian fallback

### Caveats

The implementation performs expensive list maintenance such as:

```text
snakeList.insert(0, ...)
snakeList.pop()
```

The source also contains rough/unfinished branches, for example `path.add(goal)`.

Treat the algorithmic concepts separately from the literal implementation.

## Dinosaur A* prototype

`.cursor/rules/dinosaur_farm_astar.py` explores a different strategy:

- A* toward Apple
- virtual safety check
- path-to-tail test after hypothetical Apple consumption
- follow-tail fallback
- ignore current tail-end cell because it may move away
- arbitrary-safe-move fallback

These are useful safety concepts.

### Source-level problems

The pinned A* prototype should not be treated as a working production implementation.

Notable issues include:

- shared mutable data is framed around the historical shared-memory architecture even though this particular call chain is mostly local
- the documentation and pinned code are not perfectly synchronized
- the source code's Manhattan heuristic does **not** wrap, while the accompanying README shows an older/wrapped heuristic example
- Dinosaur movement itself does not wrap, so the non-wrapped source implementation is the relevant geometry
- `current_length` is initialized but not correctly advanced through the shown main loop
- Apple-consumption/body-growth accounting is incomplete
- generic A* decision cost can dominate physical movement on large worlds
- virtual safety simulation does not fully model time-indexed release of every body segment along a multi-step candidate route

Use it for:

- follow-tail intuition
- moving-tail safety
- explicit body state
- survivability checks

not for performance claims.

## Historical documentation drift

The repository contains extensive AI/project documentation.

Some documents describe intended or earlier behavior rather than the exact pinned source.

Examples:

- A* heuristic details differ between docs and code
- shared-memory documents describe an engine behavior that no longer exists
- performance multipliers in design docs are estimates/claims rather than current locally reproduced benchmarks

Therefore every optimization claim should be tied to one of:

1. executable source at the pinned revision
2. documented historical experiment
3. current game documentation
4. a current local benchmark

Do not merge those evidence classes together.

## Precomputation

Several files precompute path structures rather than deriving moves repeatedly.

This appears in:

- Pumpkin fixed paths
- Hamiltonian Dinosaur maps
- snake traversals
- specialized region layouts

This is particularly appropriate for TFWR because interpreter computation itself consumes ticks.

A larger static source file can be faster than elegant dynamic routing.

That principle is worth preserving in benchmark variants.

## Tick instrumentation

The repository makes unusually heavy use of `get_tick_count()`.

Examples include:

- Cactus phase timing
- optimization comparisons
- farm-cycle timing
- Dinosaur statistics

This is one of the best habits to copy.

Avoid declaring an implementation "optimized" from source shape alone.

Measure:

- setup ticks
- spawn cost
- movement
- decision overhead
- throughput per resource
- sustained multi-cycle throughput where relevant

## Strongest reusable candidates

### High priority

1. persistent worker lifetime
2. stable spatial partitioning
3. phase-separated Cactus sorting
4. precomputed Pumpkin paths/layouts
5. private/local worker state
6. petal-bin Sunflower ordering
7. Maze map caching
8. Hamiltonian cycle indexing
9. tail-following Dinosaur fallback
10. phase-level tick instrumentation

### Requires redesign

1. shared companion maps
2. shared mutable work queues
3. parent-to-worker dynamic priority broadcast
4. shared stop flags
5. cross-worker Pumpkin flags/lists
6. cross-worker statistics through mutable Python objects

## Current runtime proof against shared mutable lists

This project's probe intentionally mirrors the upstream mechanism.

Observed result:

```text
DRONE MEMORY RESULT isolated
```

Specifically:

- each worker sees only its own mutation
- later workers do not inherit previous worker mutations
- the source result remains unchanged
- the parent view remains unchanged

That is enough to invalidate the upstream list-sharing mechanism for the current runtime tested.

It does not prove behavior for every future version or every imaginable type, so keep the probe available for regression testing.

## Snapshot contents

The complete pinned source tree is mirrored under `source/`.

It includes:

- 78 files
- 750,854 bytes
- current scripts
- all archived experiments
- all documentation
- Cursor rules/research material
- Pumpkin rank versions
- builtins/API reference material
- save/simulation support files

Revision: `688325db004607563e59535a15ce94fad092ff9f`.
