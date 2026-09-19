# msmith93/thefarmerwasreplaced

## Upstream

- URL: https://github.com/msmith93/thefarmerwasreplaced
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `7fef7c327e8d0b6ef34af2fafc3e5aeaf0b89823`
- Snapshot files: 59
- Snapshot size: 377432 bytes
- License metadata: no repository license is declared upstream
- Snapshot status: complete upstream file tree at the pinned revision is mirrored unchanged under `source/`

This archive intentionally preserves the source as an external reference. Local interpretation and validity notes belong in this README; files under `source/` should remain unchanged.

## Executive summary

The repository is a mixed TFWR research/workbench repository rather than one cohesive farming framework.

The most useful areas for this project are:

- single-crop leaderboard implementations for Cactus, Pumpkin, Sunflower, Tree/Wood, Hay, Carrot, Maze/Gold, and Dinosaur/Bone
- a `multidrone/` collection with several independent Megafarm/parallelization patterns
- threshold-driven "farm whatever is currently low" planners
- a ten-step, simulator-backed `Sunflowers_Single` optimization series under `claude/`
- concrete experiments showing when spatial traversal, route planning, and worker lifetime matter more than code simplicity

The repository also contains drawing/choreography scripts. Those are useful demonstrations of movement and orchestration APIs, but they are not farming-performance references.

## Repository map

### General/resource planners

- `everything.py`
- `scalable_minimum_thresholds.py`

Both files implement inventory-driven mode switching.

`everything.py` uses fixed minimum inventory thresholds and stays in a selected mode for multiple iterations before reconsidering. It covers Power, Hay, Wood, Carrot, Pumpkin, Cactus, and Dinosaur/Bone.

`scalable_minimum_thresholds.py` generalizes the same idea: it chooses the first resource below a current minimum, farms Hay, Wood, Carrot, Pumpkin, Cactus, Bone, or Gold, and doubles the minimum when all tracked resources satisfy it.

Useful idea:

> Resource production can be treated as a scheduler: choose a resource from live inventory state, prepare the field only when changing modes, and amortize setup over several farming cycles.

The implementations are older/single-drone-oriented and frequently use `clear()`, whole-field preparation, or full-field scans, so their exact hot paths should not be treated as production-optimal.

### Single-crop / leaderboard scripts

#### Cactus

`cactus_sort.py`:

1. clears and plants a fixed 6x6 Cactus field
2. bubble-sorts every row using `measure(East)` + `swap(East)`
3. bubble-sorts every column using `measure(North)` + `swap(North)`
4. harvests after the field is sorted

The reusable pattern is the familiar two-dimensional row-then-column sorting structure. The implementation itself is serial and hard-codes a 6x6 board.

#### Pumpkin

`pumpkin_leaderboard.py` tracks dead/not-ready Pumpkin coordinates after the first field scan. It revisits only those coordinates, replants dead Pumpkins, optionally uses Water/Fertilizer when inventory is sufficient, and probes adjacent Pumpkin IDs at field edges to detect a merged harvestable patch early.

Useful ideas:

- track failed cells instead of rescanning every healthy cell repeatedly
- make expensive growth acceleration conditional on available resources
- use patch identity to terminate repair work as soon as the giant Pumpkin has formed

#### Sunflower

`sunflower_leaderboard.py` bins Sunflower coordinates by petal count and harvests from 15 petals downward. Movement is wrap-aware and chooses the shorter direction per axis. It also:

- waters only above a configured petal threshold
- waits briefly before the harvest phase
- uses Fertilizer while a selected target is not harvestable
- stops a harvest batch before fewer than 10 Sunflowers remain, preserving the bonus condition

The later `claude/iterations/` series explores this strategy much more systematically; see the dedicated section below.

#### Tree/Wood and companions

`tree_leaderboard.py` maintains two coordinate maps:

- Tree tile -> requested companion coordinate
- companion coordinate -> required companion entity

A Tree is replanted and its requested companion is reserved when the position is compatible. Non-tree tiles either fulfill a reserved companion or fall back to Bush.

The notable idea is not the exact checkerboard layout; it is treating companion requests as spatial reservations so multiple Tree requests do not blindly overwrite one another.

#### Maze/Gold

`treasure_hunt.py` uses recursive DFS with physical backtracking:

- try each cardinal direction
- recurse after successful movement
- stop when Treasure is found
- walk the opposite direction while unwinding unsuccessful branches

This is a straightforward fresh-maze search reference. It does not cache a discovered graph between Treasure relocations.

#### Dinosaur/Bone

`improved_dino.py` follows a repeated serpentine/Hamiltonian-like board route and resets the Dinosaur hat when movement fails.

`dino_leaderboard.py` is more ambitious: it has an aggressive Apple-targeting stage, tracks columns/regions that become unsafe, transitions between top/bottom routing stages, and later falls back to a full-board route.

Caveat: `dino_leaderboard.py` contains visible source-level rough edges, including mixed indentation around `transition_to_route()`. It should be treated as an algorithm reference and validated before use as a benchmark candidate.

### Multi-drone / Megafarm experiments

The repository contains several different concurrency models rather than one consistent worker architecture.

#### Static persistent workers

Top-level `multidrone.py` is the clearest persistent-worker example.

Drone 0:

1. prepares the farm
2. spawns up to `max_drones() - 1` copies of the same file
3. every drone derives a horizontal offset from `get_drone_id()`
4. each drone remains alive in an infinite harvesting loop

This is directly relevant to persistent-worker benchmarking because spawn cost is paid once and each worker keeps a stable spatial assignment.

#### Cactus: synchronized phases

`multidrone/cacti.py` parallelizes Cactus work by phase:

1. spawn one planting worker per column
2. `wait_for()` all planting workers
3. spawn column-sort workers and wait
4. spawn row-sort workers and wait
5. harvest once

This reinforces a useful structural rule:

> Parallelize independent rows with rows and independent columns with columns, but synchronize between the column and row mutation phases.

The file uses `wait_for()` only as task synchronization; it does not rely on the historical shared-return-value memory exploit found in some other community repositories.

#### Carrot/Wood: long-lived harvesting workers + companion filtering

`multidrone/carrot.py` and `multidrone/wood.py` initialize columns, then start long-lived worker loops. Each worker repeatedly:

- harvests/replants its current column
- applies Water
- requests a companion
- rejects/replants until the companion satisfies the expected Bush/checkerboard condition

This is a stronger persistent-worker reference than the spawn-per-phase files because workers do not intentionally exit between cycles.

Both files contain environment-specific constants, especially the 31-worker cap, so the scheduling pattern is more reusable than the literal limits.

#### Companion side-task offload

`multi_carrot_leaderboard.py` uses a different model.

It keeps a per-row structure describing the companion entity and a reference count for the companion column. When the requested companion is not already present but the position is free, it starts a child drone specifically to move there and plant it.

This is an interesting candidate for benchmarking:

> Keep the main harvesting worker on its hot path and offload a spatial side task to an otherwise idle drone.

The implementation hard-codes column 31 as the wrap-around predecessor for column 0, so it assumes a 32-wide world and must be generalized before reuse.

#### Hay

`multidrone/hay.py` repeatedly spawns short-lived column harvesters and waits for drone capacity to free up.

`multi_drone_hay_leaderboard.py` instead creates long-lived `harvest_action()` workers which continue until the Hay target is reached.

These two files provide a useful source-near comparison candidate for spawn-per-job versus persistent harvesting workers.

#### Pumpkin and Sunflower

`multidrone/pumpkin.py` and `multidrone/sunflowers.py` use phase workers:

- parallel planting/growth work
- explicit `wait_for()` synchronization
- repeated next phase

They are parallel, but they are not persistent-worker pools because phase workers return and are spawned again.

#### Maze

`multidrone/maze_leaderboard.py` runs multiple DFS-style searchers. Each spawned drone receives a different copied value of `drone_id` and mutates its local direction preference so searchers explore in different orders.

There is no shared Python-memory coordination between those searchers. They interact only through the shared game world.

The parent attempts `range(max_drones())` spawns and then calls `search()` itself; since failed `spawn_drone()` results are not checked, the exact active worker count should be verified before using the file as a benchmark oracle.

### Sunflowers_Single optimization research

The most thoroughly measured material in the repository is under `claude/`.

`claude/sunflowers_simulator.py` is a standalone Python simulator for an 8x8 single-drone Sunflowers leaderboard run to 10,000 Power. It models:

- randomized Sunflower growth
- petal values and bonus behavior
- movement/action tick costs
- Power consumption
- Water production/decay/growth acceleration
- Fertilizer production and growth reduction
- an explicit timeout and per-run statistics

The simulator states that its effective tick rates were calibrated to an observed game build: approximately 3037 ticks/s unpowered and 6030 ticks/s powered, rather than the documented nominal 3200/6400 values.

These are upstream simulator assumptions/results, not current-runtime measurements from this repository.

#### Iteration results

The upstream `iteration_tracker.json` records 50 simulator runs per iteration:

| Iteration | Main change | Mean simulated time |
| --- | --- | ---: |
| 1 | baseline full traversal | 1037.970323 s |
| 2 | water every tile | 1096.049652 s |
| 3 | descending petal bins + Water/Fertilizer + point routing | 361.631035 s |
| 4 | repeated serpentine harvest passes | 775.974933 s |
| 5 | nearest-neighbor routing inside each petal group | 347.383634 s |
| 6 | water only new plants + larger harvest batch | 340.812005 s |
| 7 | tighter control flow / micro-optimization | 337.940689 s |
| 8 | merge initial till into normal pass + shrinking NN lists | 328.757684 s |
| 9 | serpentine combined plant/measure traversal | 322.102984 s |
| 10 | split x/y arrays + manual position tracking + adjacent-target early exit | 320.009315 s |

The tracker describes iteration 10 as about 3.24x faster than its own baseline.

The important algorithmic lessons are more useful than the absolute time:

1. Watering everything can lose when action overhead is larger than the growth benefit.
2. Petal-order harvesting is the major step change because it protects the Sunflower bonus.
3. Repeated full-field serpentine harvest passes are much worse than targeted routing.
4. Nearest-neighbor ordering reduces travel within equal-petal groups.
5. A serpentine traversal is still useful for the one required whole-field plant/measure phase because it removes wrap-around movement.
6. Merging setup into the normal hot path avoids a separate first-pass traversal.
7. Maintaining `cx/cy` locally avoids repeated position queries.
8. Shrinking candidate arrays and stopping nearest-neighbor search when an adjacent tile is found reduce interpreter work.

`iteration_7_no_scan_pass.py` is also useful as a rejected/alternative experiment: it tries to carry petal bins forward by immediately replanting and remeasuring harvested positions instead of performing the normal full scan each batch.

Keeping these failed or regressing iterations in the mirror is valuable because they show which intuitive optimizations were actually worse in the upstream model.

## Environment-specific assumptions and validity notes

Several scripts are tied to the author's game state or an older leaderboard setup.

Examples observed in the source:

- `multi_carrot_leaderboard.py` explicitly uses column `31`
- `multidrone/carrot.py` and `multidrone/wood.py` cap their child list at 31
- several `multidrone/` scripts call `set_world_size(max_drones() - 1)`
- some scripts use fixed target inventories such as two billion resources
- some loops intentionally busy-wait on `can_harvest()`, drone capacity, or inventory
- some files use infinite loops because they are intended as standalone in-game programs
- `cactus_sort.py` is fixed to 6x6
- `pumpkin_leaderboard.py` defaults movement helpers to world size 8

Therefore source-near benchmark variants should preserve these assumptions first, then a separate generalized variant can remove hard-coded world/drone constants.

Do not silently "clean up" the mirrored files; that would destroy their value as upstream references.

## Drawing and choreography

`dancing/` and `draw2/` are primarily visual/creative experiments.

They include:

- coordinate-based choreography
- hat/costume changes
- drawing letters with crop placement
- image/GIF-oriented generated movement data
- repeated `simulate()` runs for drawing scripts

They are not direct farming throughput candidates, although some movement/data-precomputation techniques may still be useful as implementation examples.

## Relevance to this repository

The strongest candidates to carry into this project's benchmark matrix are:

1. **Persistent static workers** from top-level `multidrone.py`
2. **Persistent Carrot/Wood column workers** from `multidrone/carrot.py` and `multidrone/wood.py`
3. **Spawn-per-job Hay vs persistent Hay workers** using `multidrone/hay.py` and `multi_drone_hay_leaderboard.py`
4. **Phase-separated parallel Cactus** from `multidrone/cacti.py`
5. **Companion side-task offload** from `multi_carrot_leaderboard.py`
6. **Sunflower nearest-neighbor/petal-bin routing** from the later `claude/iterations/` files

The repository is especially useful because it contains both successful and unsuccessful optimization attempts. Use it as a source of benchmark candidates, not as proof that a specific implementation is fastest in the current game.

## Snapshot contents

The complete pinned upstream file tree is under `source/`, including:

- root-level farming/leaderboard scripts
- `multidrone/`
- `claude/iterations/` and all recorded JSON results
- `claude/sunflowers_simulator.py`
- `dancing/`
- `draw2/`
- upstream `README.md`

Revision: `7fef7c327e8d0b6ef34af2fafc3e5aeaf0b89823`.
