# Pumpkin Design and Optimization Notes

This document is the canonical reference for Pumpkin mechanics, production strategy, external references, and optimization rationale.

Read this file before changing:

- `pumpkin.py`
- Pumpkin handling in `production.py`
- future Pumpkin benchmarks

## Current production strategy

The implementation has two paths.

### Megafarm fast path

When:

```text
max_drones() >= get_world_size()
```

the farm assigns exactly one worker to every column.

For the production-relevant 32x32 farm with 32 available drones this means:

```text
drone 0  -> column 0
drone 1  -> column 1
...
drone 31 -> column 31
```

Each worker:

1. moves to its assigned column once
2. scans only that column
3. moves only `North`
4. relies on farm-edge wrapping to return from the top to y=0
5. replants dead/missing Pumpkins
6. remembers rows that are already fully grown and alive
7. exits only after every tile in its column is known-good

After all column workers return, the main drone verifies the full-map Pumpkin using the existing opposite-corner Pumpkin-ID check and harvests it.

If the full merge has not happened yet, the existing Patch & Wait logic remains as a robustness fallback.

### Patch & Wait fallback

If there are fewer drones than columns, the previous strategy remains active:

1. plant the complete field in chunks
2. wait briefly
3. collect only dead/missing/unripe coordinates
4. revisit only those problem positions
5. verify the final merge using Pumpkin IDs
6. harvest

This prevents the 32-drone optimization from degrading earlier progression.

## Why one worker per column

The game documents that moving across an edge wraps to the opposite side.

Therefore a worker that only executes:

```python
move(North)
```

needs exactly `world_size` physical moves for one complete column loop.

On a 32x32 farm:

```text
North-only loop: 32 moves
North + South return: about 62 moves
```

There is no reason to reverse direction at the top of the column.

The official movement examples also demonstrate systematic field traversal using repeated North moves plus edge wrapping.

## Why finished rows are cached

A Pumpkin has a chance to die when it becomes fully grown.

Once a worker observes:

```python
get_entity_type() == Entities.Pumpkin
and can_harvest()
```

that row is considered complete for the current production cycle and is not inspected again by that worker.

The drone still physically passes the row because the column loop is fixed, but it avoids redundant entity/readiness checks.

This is safe under the documented Pumpkin mechanic: the death event occurs when the Pumpkin finishes growing, not later after it has already survived and become harvestable.

## Dead Pumpkin handling

The official Pumpkin documentation states that planting a new plant on a dead Pumpkin removes/replaces the dead Pumpkin automatically.

Therefore the fast path intentionally does not harvest `Entities.Dead_Pumpkin` first.

It simply plants a replacement.

## Full-map completion check

`measure()` returns a Pumpkin ID.

Merged Pumpkin tiles share the same ID, so the implementation compares opposite corners of the square field.

The existing helper:

```python
is_full_map_pumpkin()
```

is retained as the final authority before harvesting.

This gives the fast path two levels of correctness:

1. every column worker has observed every tile as fully grown and alive
2. the opposite-corner ID check confirms that the full-map merge actually happened

## Production-state optimization

Consecutive Pumpkin-focused production cycles intentionally do not rebuild the normal Sunflower farm between runs.

`production.py` tracks `_pumpkin_active`.

A successful Pumpkin run leaves the field in its post-harvest state. If the planner asks for Pumpkin again, the next `pumpkin.run()` starts directly and clears the field itself.

The normal farm is rebuilt only when the production focus changes away from Pumpkin.

This avoids:

```text
build Sunflowers
-> immediately clear them for Pumpkin
-> build Sunflowers
-> immediately clear them for Pumpkin
...
```

## References

### Official mechanics

The Farmer Was Replaced Wiki:

- Pumpkins:
  https://thefarmerwasreplaced.wiki.gg/wiki/Pumpkins
- Move / edge wrapping:
  https://thefarmerwasreplaced.wiki.gg/wiki/Move
- Tooltips / `measure()` and `move()`:
  https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips

Relevant documented facts:

- farm movement wraps across map edges
- a dead Pumpkin can be replaced directly by planting
- dead Pumpkins are not harvestable
- fully grown square Pumpkin regions merge
- `measure()` on Pumpkins returns an ID

### Local external reference: MateusMarochi

Snapshot:

- `external/mateusmarochi-the-farmer-was-replaced-codes/source/pumpkin_farm.py`
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/pumpkin_farm_2.py`

`pumpkin_farm.py` distributes workers by columns and repeatedly monitors each assigned column.

Important difference from our implementation:

- the reference explicitly walks South again after scanning North
- our worker uses the documented world wrap and continues North only

So the **column ownership** idea is externally corroborated, while the **North-only loop** is our optimization of that design.

`pumpkin_farm_2.py` demonstrates an alternative 32-drone strategy based on smaller 6x6 / 4x4 zones and dedicated lanes.

We retain it as an alternative strategy, not as the current production choice.

### Community comparisons

Reddit discussions:

- one drone per column / North-only suggestion:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1ohszgq/
- 4x8 zones vs single row/column loops:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1pz3nlc/
- full-map Pumpkin and one-drone-per-column discussion:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1oerhg0/
- coordinate-list Patch & Wait approach:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1tru4ys/

These are community observations, not authoritative mechanics.

The useful themes are:

- one worker per row/column becomes attractive when drone count matches world size
- North-only loops exploit edge wrapping
- small rectangular zones can reduce distance between sparse failed Pumpkins
- coordinate-list tracking is effective with fewer workers

Our implementation preserves both major approaches:

- enough drones: one persistent column worker per column
- fewer drones: coordinate-based Patch & Wait

## Why the 32-drone path is expected to scale well

For 32x32 with 32 drones, each worker owns only 32 tiles.

The expensive physical movement is parallelized across all columns.

The main worker no longer needs to:

- collect one global 1024-tile problem list repeatedly
- redistribute sparse problem coordinates among new worker batches
- send workers between unrelated coordinates across the map

Instead, each worker repeatedly traverses a deterministic 32-move ring.

Movement dominates observation cost, so avoiding return paths and cross-field repositioning is more important than saving a few `get_entity_type()` calls.

## Traceability

Production code:

- `pumpkin.py::can_use_column_workers()`
- `pumpkin.py::_service_column_pumpkin()`
- `pumpkin.py::_make_column_worker()`
- `pumpkin.py::run_column_workers()`
- `pumpkin.py::run()`

Normal-farm lifecycle:

- `production.py::_pumpkin_active`
- `production.py::run_pumpkin()`
- `production.py::run()`

Fallback implementation retained in:

- `pumpkin.py::plant_full_field()`
- `pumpkin.py::collect_problem_positions()`
- `pumpkin.py::patch_problem_positions()`

## Future benchmark

The next useful Pumpkin benchmark should compare:

```text
32x32
32 drones
same seed
same Pumpkin/Carrot/Water inventory

A: persistent one-column-per-drone, North-only
B: 4x8 or similar fixed zones with dead-tile tracking
C: legacy global Patch & Wait
```

Primary metric:

```text
Pumpkins / simulated second
```

Also record:

- time to full-map merge
- physical moves
- number of replants
- number of full-field observations
- setup/restart cost over several consecutive production cycles

Do not replace the column strategy based only on fewer source-code lines or theoretical path length. Use simulated production throughput.


## Implemented benchmark matrix 2026-09-19

The planned Pumpkin benchmark is implemented in:

- `bench_pumpkin.py`
- `bench_pumpkin_run.py`

It now has two distinct decision layers.

### Cold one-cycle comparison

`PUMPKIN PRIMARY` compares the current production path against sparse local-repair shapes and distributed spawn-tree variants.

This answers which algorithm reaches one valid full-map harvest fastest when all setup cost is paid from scratch.

### Three-cycle amortized comparison

`PUMPKIN AMORTIZED` explicitly measures the setup/restart concern.

Fresh-per-cycle controls recreate their workers for each harvest. Persistent variants create the topology once and keep the same workers alive for all three harvest cycles.

The persistent modes are:

- `persistent-1x32-tail`
- `persistent-4x8-tail`
- `persistent-8x4-tail`
- `persistent-tree-4x8-tail`
- `persistent-tree-8x4-tail`

Drone-memory isolation prevents a normal shared Python barrier. The persistent benchmark instead uses the farm as synchronization state:

1. all workers complete their local Pumpkin region
2. worker 0 waits for the full-map Pumpkin-ID merge
3. worker 0 harvests
4. other workers observe their merged Pumpkin disappearing
5. all workers immediately begin the next cycle

Every simulation reports completed cycles, total gain, per-cycle gain, ticks, runtime, and resource consumption. A mode is valid only when every requested cycle completes and every cycle has the same positive Pumpkin gain.

Production must remain unchanged until the in-game benchmark log establishes a measured winner. For the production decision, the three-cycle amortized result is more important than the one-cycle cold result.


## Sparse-repair benchmark failure and corrected matrix

The first sparse-region benchmark run exposed a Pumpkin-specific correctness trap.

Measured valid controls on 32x32 / 32 drones:

- current production: 3,145,728 Pumpkin per full-map cycle on seeds 1, 2, and 3
- legacy Patch & Wait: 3,145,728 Pumpkin on the smoke run

All sparse local-repair shapes finished their local work faster but produced no full-map harvest.

The failure is caused by partial Giant Pumpkins.

A sparse worker previously treated:

`Entities.Pumpkin + can_harvest()`

as proof that a coordinate was finished. That is also true when the coordinate belongs to an already merged smaller Giant Pumpkin. Independent local completion therefore allowed the field to fragment into a mosaic of harvestable Giant Pumpkins with different IDs.

At that point there may be no dead/missing/unripe coordinate left to repair, but the opposite-corner IDs never become equal.

Therefore sparse coordinate elimination is rejected for full-map Pumpkin production in its current form.

The active benchmark now preserves the known-good North-only column-ring semantics and measures only lifecycle/setup changes:

- `current-production`
- `ring-reuse`
- `persistent-ring`
- `persistent-tree-ring`

`ring-reuse` isolates the cost of clearing/re-tilling the field between cycles. The two persistent modes additionally amortize worker creation across cycles; the tree variant isolates distributed spawn topology.

The fully-upgraded 32x32 validity check is now exact: every cycle must yield 3,145,728 Pumpkin.
