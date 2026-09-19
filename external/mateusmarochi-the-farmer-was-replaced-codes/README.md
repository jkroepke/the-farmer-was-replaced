# MateusMarochi/the-farmer-was-replaced-codes

## Upstream

- URL: https://github.com/MateusMarochi/the-farmer-was-replaced-codes
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `d303d81d6a3eb59887eff75ed0454a6d8f4ff5ad`
- Snapshot files: 21
- Snapshot size: 68908 bytes
- License: MIT
- Snapshot status: complete upstream tree mirrored unchanged under `source/`
- Snapshot verification: local `source/` tree SHA is identical to the upstream commit tree SHA `9e4fd00380b76d74cd18f8144a4124c265611959`

This archive preserves the upstream source verbatim. Analysis and current-runtime caveats belong in this README; files under `source/` should not be edited.

## Executive summary

This repository is a collection of relatively independent TFWR strategies rather than one unified farming engine.

The strongest reference areas for this project are:

- persistent column workers for Sunflower and Pumpkin farming
- a fixed spatial Pumpkin layout using specialized long-lived drones
- parallel Maze search through deliberately diversified wall-followers
- a multi-worker Cactus sorter
- companion-request handling for Polyculture
- a simple Hamiltonian Dinosaur loop with collision-triggered harvest/restart
- helper planting functions that centralize soil/water preparation

Several of the multi-drone files are especially useful because they provide concrete source-near candidates for the persistent-worker benchmark work in this repository.

However, some algorithms assume coordination through mutable module state or allow independent workers to mutate the same global structure without a phase barrier. Those assumptions must be checked against current drone-memory semantics and actual race behavior before reuse.

## Repository map

### Farming implementations

- `bone_farm.py` — Dinosaur/Bone production
- `cactus_farm.py` — multi-drone Cactus planting/sorting/harvesting
- `maze_farm.py` — 8-worker diversified Maze wall-following
- `maze_farm_2.py` — 16-worker version of the same idea
- `maze_farm_3.py` — 8-worker variant with additional heading/turn diversity
- `polyculture_farm.py` — single-drone companion-request queue
- `polyculture_farm_paralel.py` — pair-of-columns worker version
- `pumpkin_farm.py` — persistent column workers with local per-tile state
- `pumpkin_farm_2.py` — explicit 16/32-drone region-specialized Pumpkin layout
- `sunflower_farm.py` — persistent one-worker-per-column Sunflower farm

### Helpers / metadata

- `plantacoes.py` — crop-specific planting/soil/water helpers
- `global.py` — normal-Python API stubs, not a game simulator
- `docs/` — Portuguese design notes
- `AGENTS.md`
- upstream `README.md`
- MIT `LICENSE`

## Persistent worker pattern

The clearest reusable architecture appears in `sunflower_farm.py` and `pumpkin_farm.py`.

Instead of repeatedly spawning one short-lived job per pass, the parent:

1. determines the number of active workers
2. spawns workers for stable column assignments
3. runs one assignment itself
4. every worker stays alive indefinitely

This directly avoids repeated `spawn_drone()` overhead.

### Sunflower columns

`sunflower_farm.py` assumes a 32x32 field and up to 32 drones.

Each worker owns one column and repeatedly:

1. returns to row 0
2. walks North through the column
3. harvests a mature Sunflower if present
4. replants via `plantacoes.plant_sunflower()`
5. returns to row 0 and repeats

Worker 0 is executed by the parent, while columns 1..31 are spawned as child workers.

This is a clean persistent-worker reference because:

- ownership is static
- workers do not need cross-worker Python memory
- each worker has excellent locality
- spawn cost is paid only during setup

### Sunflower limitation

The worker does not measure petal counts and does not coordinate harvest order across columns.

For normal Power farming this may still be useful as a throughput baseline, but it should not be assumed to preserve the maximum-petal Sunflower bonus or to be leaderboard-optimal.

For this project the important benchmark question is therefore:

> How much does persistent one-column ownership save versus a phase/spawn-based Sunflower implementation when both use the same harvest policy?

Do not compare it directly against a petal-aware implementation and attribute the difference only to worker lifetime.

## Pumpkin strategies

The repository contains two substantially different Pumpkin designs.

### `pumpkin_farm.py`: persistent generic column workers

Workers are assigned columns using:

```text
start_column + k * stride
```

where `stride` is the number of active workers.

Each worker maintains a private nested tracker:

```text
column -> row -> {
    last_size,
    stable_count
}
```

For each tile it:

- removes/replants a dead Pumpkin
- replants if no Pumpkin exists
- records repeated `measure()` values
- harvests only after the measured patch size is at least `TARGET_PATCH_SIZE` and remains stable for `STABLE_MEASUREMENTS` observations

This is a good example of **worker-local persistent state**.

Unlike designs that try to broadcast mutable dictionaries across drones, every worker owns and updates only its own tracker. That is compatible with isolated drone memory.

Potential benchmark idea:

> Compare persistent column-local repair state against whole-field repeated rescanning.

The source's exact measurement heuristic still needs current-runtime validation before being considered semantically optimal.

### `pumpkin_farm_2.py`: fixed region specialization

This file is more architectural.

For the 32-drone layout it creates different long-lived roles:

- 6x6 Pumpkin patch workers
- 4x4 mini-patch workers
- vertical Sunflower strip workers
- horizontal Sunflower strip workers
- preparation workers

The patch workers measure two selected points and harvest when those measurements agree and the patch is harvestable.

The compact mode targets 16 drones and explicitly lays out:

- 8 large patch roles
- 2 horizontal roles
- 2 vertical roles
- 3 mini roles
- the parent as the final worker

The major reusable idea is:

> A Megafarm does not need homogeneous workers. Static specialized regions can trade flexibility for very low coordination overhead.

This aligns with the broader observation in other references that precomputed spatial layouts can outperform dynamic schedulers in the game's interpreter.

Caveats:

- the full layout is hard-coded for 32x32
- compact mode only accepts 22x22 or 32x32
- role coordinates and patch dimensions are manually encoded
- the layout mixes Pumpkin and Sunflower production, so its result cannot be compared fairly with a pure-Pumpkin benchmark without accounting for the Power support role

## Cactus: `cactus_farm.py`

The file selects a worker count, preferring 32 and then 16.

Each persistent worker repeatedly performs:

1. a set of vertical Cactus passes
2. a set of horizontal Cactus passes
3. a chain-harvest attempt
4. several `pet_the_piggy()` calls

The sorting primitive compares both directions around the current tile and swaps when local ordering is wrong.

### Useful idea

Static `start_index + stride` ownership is simple and avoids rebuilding work queues.

### Important concurrency caveat

Every worker independently executes **both** the vertical and horizontal phases.

There is no global barrier ensuring all vertical mutations finish before horizontal mutations begin.

That means row-oriented and column-oriented swaps from different workers can overlap in time.

This is materially different from the safer phase-separated Cactus pattern used elsewhere in this repository:

1. all row workers
2. barrier
3. all column workers
4. barrier
5. one harvest

For benchmarking, keep MateusMarochi's implementation as a source-near candidate, but do not infer that concurrent row/column mutation is equivalent to phase-separated sorting.

### `ACTIVE_STRIDE` caveat

The code attempts to reduce `ACTIVE_STRIDE` when a spawn fails.

Under current isolated drone memory, workers already spawned cannot receive a later mutation of the parent's module global.

Normally the initial target is selected below/equal to available capacity, so the fallback may never matter. But the dynamic "shrink stride after partial spawn" behavior is not a robust current coordination mechanism.

## Maze variants

The three Maze files use a different philosophy from graph-building/BFS/reference-tree approaches.

They run several independent wall-followers and intentionally diversify them.

### `maze_farm.py`

Eight workers vary:

- initial direction
- clockwise vs counter-clockwise wall preference
- warm-up distance

A worker keeps trying movement and rotates its heading differently depending on whether the previous move succeeded.

The parent polls `has_finished()`; the first worker that reaches and harvests Treasure wins.

### `maze_farm_2.py`

Same algorithm, increased to 16 workers.

This is useful as a clean scaling comparison:

> same search policy, more independent searchers.

### `maze_farm_3.py`

Adds more diversity:

- initial heading rotation
- different straight-line lengths before complementary turns
- immediate post-block movement attempt

This explores search-policy diversity rather than simply increasing worker count.

### Major Maze caveat: losing workers remain alive

When one worker returns success, the coordinator immediately returns and the outer loop creates a new Maze.

It does not explicitly wait for all other search workers to terminate.

Those other workers are infinite loops and can therefore continue operating while the next Maze is generated.

That creates potential cross-generation interference and also consumes drone slots.

For a current benchmark adaptation, losing workers need an explicit task-lifetime strategy. Because drones cannot be externally cancelled through a shared Python flag, a safer design needs bounded worker work, natural termination, or a generation structure that does not start the next round until obsolete workers are gone.

### Relevance to this project's Maze work

The useful concept is **search diversity across independent drones**.

The source does not maintain:

- a persistent graph
- discovered wall state
- a reusable reference tree
- shortest-path routing between known points

So it should be compared as a simple multi-search baseline, not as an alternative persistent-map architecture.

## Polyculture

### Single drone

`polyculture_farm.py` maintains a `pedidos` list of requested companion placements:

```text
(x, y, entity)
```

At each tile it first checks whether the tile satisfies a pending request. Otherwise it plants one of Grass/Tree/Carrot/Bush in a rotating probe cycle and records the returned companion request.

It suppresses duplicate requests by coordinate.

Useful concepts:

- represent companion needs as explicit spatial jobs
- deduplicate by target coordinate
- separate "fulfill an existing request" from "probe for a new request"

This is conceptually similar to reservation/map approaches in other community implementations.

### Parallel two-column workers

`polyculture_farm_paralel.py` assigns each worker a pair of columns and traverses them in opposite directions.

The last two columns are reserved for Sunflowers.

The major current-semantic issue is that `pedidos` is Python memory.

Each drone receives/creates its own isolated copy of module state. A request discovered by one worker is therefore not a shared global job visible to another worker.

Within one worker's two-column region, local requests can still be useful. But a companion request targeting a different worker's region cannot be coordinated through this list.

Therefore the file is a useful **spatial-worker** reference but not a valid cross-worker shared-request architecture under current game semantics.

## Dinosaur: `bone_farm.py`

The path is a straightforward skyscraper/Hamiltonian-style sweep:

- alternate vertical columns
- keep row 0 as the return lane
- return West to x=0
- repeat

It does not use `measure()` to target Apples or track the tail explicitly.

The interesting behavior is `dinosaur_safe_move()`:

```text
if can_move(direction):
    move(direction)
else:
    change_hat(non-dinosaur)
    change_hat(Dinosaur_Hat)
```

Changing away from the Dinosaur Hat harvests the current tail. Changing back starts a new Dinosaur.

So this should be interpreted as:

> collision-triggered harvest + immediate restart

rather than as a pathfinding workaround.

This idea is already incorporated into this project's Dinosaur research as motivation for sustained multi-cycle throughput benchmarking.

One source detail remains important: the East move between columns is not wrapped by `dinosaur_safe_move()`. The strategy assumes the chosen Hamiltonian geometry keeps those transitions safe.

## Helper layer: `plantacoes.py`

This file centralizes crop setup rules:

- Grass -> Grassland
- Carrot/Pumpkin/Cactus/Sunflower -> Soil
- Tree -> Grassland
- conditional Water for Tree/Sunflower
- direct helpers for Pumpkin/Cactus/Apple

The main architectural benefit is reducing duplicated soil/water checks in worker hot paths.

Its exact thresholds are strategy choices, not authoritative game constants.

## `global.py` is not a simulator

`global.py` exposes Python enums and stub functions with approximate signatures so repository files can be imported/executed by normal Python without immediately failing on undefined game names.

The functions return placeholder values and emit warnings.

Do not use this file for performance or mechanics validation. It does not emulate:

- movement
- crop growth
- drone execution
- inventory
- tick cost
- Maze/Dinosaur behavior

## Strongest benchmark candidates for this project

1. **Persistent one-column Sunflower workers**
2. **Persistent Pumpkin column workers with private local state**
3. **Static heterogeneous Pumpkin regions**
4. **8-vs-16 diversified Maze wall-followers**
5. **Maze policy-diversity variant from `maze_farm_3.py`**
6. **Single-drone companion request/reservation queue**
7. **Source-near concurrent Cactus sorter**, specifically to compare against phase-separated sorting
8. **Collision-triggered Dinosaur restart** as a sustained-production policy

## Current-runtime validity summary

Safe/reusable architectural ideas:

- persistent workers with static spatial ownership
- parent acting as one worker
- worker-private persistent state
- heterogeneous fixed-region specialization
- independent Maze search diversity
- local companion-request queues
- collision-triggered Dinosaur harvest/restart

Needs rework or explicit benchmark validation:

- Cactus workers concurrently mixing row/column mutation
- changing parent globals after workers have spawned
- parallel Polyculture assuming a shared `pedidos` list
- Maze rounds that leave losing workers alive
- arbitrary Sunflower harvest without petal-order coordination
- hard-coded 22/32 layouts and fixed drone counts

## Snapshot contents

The complete pinned upstream repository is mirrored under `source/`.

It contains 21 files totaling 68,908 bytes, including the MIT license, documentation, all strategy scripts, and Python API stubs.

Revision: `d303d81d6a3eb59887eff75ed0454a6d8f4ff5ad`.
