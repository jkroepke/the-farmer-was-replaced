# sciencejiho/TFWR-Solutions

## Upstream

- URL: https://github.com/sciencejiho/TFWR-Solutions
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `master`
- Revision: `e0f22263d8de76691407bbcb314c0b41c3eea82e`
- Revision date: 2026-09-16
- Snapshot files: 23
- Snapshot size: 110473 bytes
- License metadata: no repository license is declared upstream
- Snapshot status: complete pinned repository mirrored unchanged under `source/`
- Snapshot verification: all 23 local source blobs match the upstream Git blob SHAs

This is a particularly useful current reference because the code was updated only days before this review and its drone architecture already assumes the modern TFWR model: jobs and state passed to spawned drones are copied, results return through `wait_for()`, and coordination is performed by the controller through immutable job descriptions and returned observations rather than shared mutable Python memory.

## Executive summary

The strongest ideas in this repository are:

- inventory-ratio based strategy selection
- persistent strategy state across cycles
- asynchronous long-lived column lanes for Polyculture
- explicit controller/worker separation compatible with isolated drone memory
- sparse revisit-only repair for Pumpkin and Cactus
- phase-separated parallel Cactus sorting
- persistent Maze passage graphs
- parallel Maze mapping with merged worker results
- deterministic station ownership for relocated Treasure
- bounded FIFO companion-request scheduling
- finish/drain hooks before changing field mode

Unlike many historical Megafarm references, none of the interesting multi-drone mechanisms depend on a shared `wait_for(source)` object.

That makes this repo unusually relevant to current production design.

## Repository structure

The project is intentionally flat.

Key files:

- `main.py` — top-level entry
- `strategy_control.py` — multi-mode inventory scheduler
- `strategy_polyculture.py` — asynchronous column lanes and companion orchestration
- `strategy_pumpkin.py` — Pumpkin strategy with Carrot fallback
- `strategy_cactus.py` — Cactus production/sort lifecycle
- `strategy_maze.py` — persistent Maze farming and station swarm
- `strategy_carrot.py` — standalone Carrot strategy
- `drone_control.py` — generic copied-job execution
- `pumpkin_field.py` — parallel scan + sparse revisit
- `cactus_field.py` — parallel scan + row/column sort
- `polyculture_field.py` — controller-owned crop/request state
- `polyculture_tile.py` — stateless physical tile/request operations
- `maze_solver.py` — persistent graph, BFS routing, station planning
- `inventory.py` — target/reserve policy
- `crop_care.py`, `planter.py`, `movement.py` — shared primitive services

The bundled `__builtins__.py` is an editor/API reference snapshot.

## Current-memory compatibility

This repository lines up very well with the 2026-09-19 drone-memory probe in this project.

That probe established:

```text
spawn arguments -> copied
globals / closures -> isolated per drone
wait_for(worker) -> returns data
wait_for(completed source) -> fresh mutable copy per call
```

sciencejiho's architecture does not try to defeat that model.

Instead, worker jobs are copied intentionally and workers return results to a controller that merges them.

This is the most important architectural distinction from historical nql1314-style shared-memory code.

## `drone_control.run_jobs()`

The generic job runner is simple and useful.

It:

1. allocates a result array in job order
2. calculates free drone slots with `max_drones() - num_drones()`
3. spawns as many copied jobs as capacity permits
4. has the controller execute one job itself when work remains
5. waits for spawned handles
6. writes results back to their original indices
7. repeats until all jobs are complete

The result ordering is preserved even though jobs run concurrently.

### Strong point

The parent/controller does useful work instead of idling after filling child slots.

### Strong point

No worker needs to mutate shared coordinator state.

### Setup caveat

`spawn_at()` first moves the controller to a requested start position and then spawns the child there.

For many spatial jobs this is convenient, but controller repositioning becomes part of setup cost.

Benchmark worker creation plus positioning together rather than counting only the 200-tick spawn action.

## Inventory policy

`inventory.py` defines absolute targets for:

- Hay
- Wood
- Carrot
- Pumpkin
- Weird Substance
- Power
- Cactus
- Gold

and reserves for:

- Water
- Fertilizer

Strategies compare:

```text
current inventory / target inventory
```

rather than following a fixed crop cycle.

This gives one generic notion of resource urgency.

`REFILL_RATIO = 0.8` adds a second threshold used to preempt Maze farming when another resource becomes meaningfully low.

This is a lightweight hysteresis-like policy that avoids reacting only at the exact target boundary.

## Strategy controller

`strategy_control.py` maintains one persistent state object per mode:

- Cactus
- Maze
- Polyculture
- Pumpkin

The scheduler selects the mode associated with the most underfilled target resource.

### Persistent mode state

State is not rebuilt every outer iteration.

A strategy can therefore retain:

- active workers
- field knowledge
- request queues
- Maze graph data

until the mode actually changes.

### Explicit finish hooks

Before changing modes, the controller calls the active strategy's `finish()`.

This is a strong lifecycle pattern.

Examples:

- Polyculture drains outstanding child handles.
- Maze attempts to collect the active Treasure before the field is cleared.
- Pumpkin drains its supporting Polyculture work.

Only after finishing does the controller call `clear()` and initialize fresh state for the next strategy.

This avoids silently abandoning active child work when changing farm modes.

## Asynchronous Polyculture lanes

`strategy_polyculture.py` is one of the most relevant files for current Megafarm design.

It creates:

```text
lane_count = min(max_drones(), world_size)
```

One lane belongs to the controller.

The remaining lanes have persistent scheduling records:

```text
{
    handle,
    lane,
    next_x,
    x
}
```

Each lane owns a sequence of columns:

```text
lane
lane + lane_count
lane + 2 * lane_count
...
```

### Important difference from spawn-per-pass designs

Workers are not globally synchronized after every column.

The controller loop:

1. collects only workers that have finished
2. processes companion requests that are safe to touch
3. launches new work into currently idle lanes
4. processes one controller-owned column itself

This creates asynchronous continuous utilization without needing mutable cross-drone state.

### Why this is important

This is a concrete modern answer to the problem previously solved with historical shared worker pools:

> keep scheduler state in one controller, send immutable snapshots/jobs to workers, and merge returned observations.

That pattern is directly reusable.

## Copied column jobs

Before spawning a worker, the controller constructs a complete per-tile job snapshot:

```text
(x, y, expected_crop, waiting_for_companion, selected_primary)
```

The worker operates only on this copied list and returns observations.

This deliberately accepts temporary staleness.

The controller then merges:

- actual entity
- newly discovered companion request

back into its canonical field state.

This is essentially optimistic distributed work with reconciliation.

For TFWR's cooperative single-world state, this can be more efficient than attempting fine-grained synchronization.

## Avoiding physical races

The controller tracks columns currently owned by active workers.

Companion requests are deferred when either:

- the source column is active
- the target column is active

This is important because Python memory is isolated but the physical farm is globally shared.

The architecture correctly distinguishes:

- Python-state isolation
- shared game-world mutation

Workers can safely operate independently only if their physical worksets do not conflict.

## Polyculture request model

`polyculture_field.py` keeps controller-owned state for every coordinate.

It tracks:

- current crop
- whether crop work is scheduled
- outstanding source -> target relation
- FIFO request queues per target
- retry counts
- scheduled target work

### Snapshot passes

`begin_request_pass()` extracts a fixed set of currently scheduled targets.

Requests created while processing that pass wait until the next pass.

That makes each controller iteration bounded.

This is a useful anti-feedback-loop pattern.

### FIFO collisions

Multiple source plants can request the same companion target.

The target maintains a queue.

Only the oldest request is processed.

Blocked requests can be:

- waited
- deferred
- completed/removed

with bounded attempts.

This is much more robust than one global coordinate -> request dictionary that silently overwrites collisions.

### Current performance caveat

`queue.pop(0)` is used when completing a request.

Flekay's tick research indicates front removal can scale with list length.

Companion queues are likely short, so this may be fine. If collision-heavy benchmarks show long queues, an index/cursor representation may be cheaper.

## Pumpkin sparse repair

`pumpkin_field.scan_world()` parallelizes the initial whole-field pass by column.

Each column worker returns:

- readiness state
- pending coordinates

After that, the strategy does **not** repeatedly rescan the full farm.

`revisit_pending()`:

1. groups remaining coordinates by column
2. sends only those groups as jobs
3. revisits unresolved coordinates
4. returns a smaller unresolved set

This independently confirms the strong community pattern:

> pay one complete scan, then revisit only failures.

The strategy caps revisits at:

```text
world_size * world_size
```

so a pathological crop state cannot loop forever.

## Pumpkin resource fallback

`strategy_pumpkin.grow_world()` first checks Carrot inventory.

If Carrot is below target, it runs the Polyculture strategy instead.

Only after the reserve recovers does it drain Polyculture child workers and resume giant-Pumpkin work.

This is a clean example of strategy composition rather than duplicating supply logic inside Pumpkin code.

## Cactus readiness + sorting

`cactus_field.py` uses the same two-stage readiness model as Pumpkin:

- parallel full-column scan
- sparse pending-coordinate revisits

Once ready, sorting is explicitly phase-separated:

1. all rows
2. wait for all row jobs
3. all columns
4. wait for all column jobs

Each line uses bubble-style passes with early exit.

### Current correctness benefit

Rows never race with columns.

This matches the safest Cactus concurrency invariant already identified in other references.

### Optimization caveat

Each row/column worker repeatedly calls `movement.move_to()`, `measure()`, and `swap()`.

The architecture is sound, but the exact sorter still needs benchmark comparison against current local Cactus implementations.

## Maze: persistent graph

`maze_solver.new_state()` stores:

- a 4-direction connection bitmap per coordinate
- whether the Maze has been mapped
- world size

Unlike wall-state models that try to remember dynamic closed edges, this structure records known open passages.

## Parallel Maze mapping

`map_maze()` checks currently open directions from the starting position.

It then creates up to:

```text
min(max_drones(), size * size)
```

mapping jobs.

Workers differ in:

- initial open branch
- direction exploration offset

Each worker performs DFS-like mapping in its own copied graph and returns that graph.

The controller OR-merges all discovered connections.

### Useful property

Duplicate mapping work is tolerated.

No shared visited structure is required.

This is another good current-memory design:

> independent redundant exploration + deterministic merge.

Whether multiple mapping drones repay their duplicated movement cost is a benchmark question.

## Maze BFS representation

Routing uses a queue plus index cursor:

```text
queue = [...]
queue_index = 0
...
node = queue[queue_index]
queue_index += 1
```

This avoids `pop(0)`.

Parents are stored separately and the path is reconstructed at the end.

That is materially better than BFS implementations that copy the entire path list for every queued state.

### Remaining reconstruction caveat

`_build_path()` uses:

```text
path.insert(0, direction)
```

while walking parents backward.

Since paths are bounded by board size this may be acceptable, but reverse-append + reverse traversal would be worth benchmarking if Maze computation is hot.

## Maze station swarm

After mapping, the strategy does not send every drone racing directly to the Treasure.

It creates stationary responsibility regions.

### Initial station placement

`create_station_plan()` places one station at the anchor and repeatedly chooses the coordinate farthest from all already selected stations.

This approximates a farthest-point distribution over graph distance.

For each station it precomputes a full distance map.

### Treasure ownership

When a Treasure coordinate is measured:

```text
owner = closest_station(plan, target)
```

Every worker has a copied but identical immutable plan.

Therefore every worker independently computes the same owner index without communication.

This is a very strong current-runtime pattern:

> use deterministic computation over copied immutable state as synchronization.

### Dynamic spreading

For every Treasure, the swarm computes a new station plan anchored at the Treasure.

The selected owner gets station index `owner`, ensuring it is assigned directly to the Treasure while the rest spread through the Maze.

Only the owner harvests/reuses Treasure.

The others reposition for the next relocation.

### Potential cost

Every worker independently computes `spread_station_plan()`, including multiple BFS distance maps.

Because workers run concurrently, wall-clock cost can overlap, but interpreter ticks still matter per drone and simulator speed may be affected.

A cheaper deterministic station transform could outperform repeated all-worker replanning.

This is worth benchmarking.

## Maze reuse and resource preemption

The Maze strategy keeps reusing Treasure only if:

- Gold remains below target
- no other farmed item has fallen below its refill threshold
- Weird Substance can be spent while preserving its configured reserve

This makes long-lived Maze farming interruptible by resource pressure.

The controller can therefore retain the throughput benefit of reuse without starving the rest of the economy indefinitely.

## Current-code vs README progression badges

The upstream README badges say Maze and Megafarm are locked in the displayed save progression, yet the pinned repository contains substantial Maze and multi-drone code.

Treat the badges as save/progression presentation, not proof that each committed strategy was exercised at that exact revision.

The code itself is still valuable as an algorithm reference.

Current in-game benchmark validation remains necessary.

## Strongest reusable findings

### Very high priority

1. asynchronous persistent column lanes
2. controller-owned canonical state + copied worker snapshots
3. merge returned observations instead of cross-worker shared memory
4. explicit active-column conflict avoidance
5. sparse Pumpkin/Cactus revisit lists
6. phase-separated Cactus row/column sorting
7. ordered generic job runner with parent participation
8. persistent Maze passage graph
9. independent parallel map + merge
10. deterministic station ownership over copied immutable state
11. strategy `finish()` hooks before field transitions
12. inventory-ratio scheduling with refill thresholds

### Worth benchmarking

1. asynchronous lanes vs full-pass barriers in normal farming
2. map-Maze with 1, 4, 16, 32 workers
3. station swarm vs direct nearest-worker race
4. repeated per-worker station replanning cost
5. sparse pending grouping by columns
6. generic `run_jobs()` controller positioning overhead
7. FIFO companion queues under collision-heavy layouts

## Relationship to current local research

### Drone memory

This repository is one of the best references found so far for designing around the current isolated-memory model rather than historical exploits.

### Normal farm

Its asynchronous column lanes are a strong candidate for the current persistent-worker/farm benchmark.

Unlike fixed forever-workers, child jobs terminate and are recycled, while lane scheduling state persists in the controller.

That gives a middle ground between:

- spawn every whole-field pass
- immortal persistent workers

### Pumpkin

The sparse revisit pattern independently confirms the architecture already seen in multiple strong references.

### Cactus

The explicit row barrier before column sorting agrees with the current safer design direction.

### Maze

The graph representation and station swarm are sufficiently different from current Zapakh/reference-tree modes to justify a source-near benchmark candidate.

## Snapshot contents

The complete pinned upstream repository is mirrored unchanged under `source/`.

It contains:

- 23 files
- 110,473 bytes

Revision:

`e0f22263d8de76691407bbcb314c0b41c3eea82e`

All mirrored source blob SHAs match upstream.
