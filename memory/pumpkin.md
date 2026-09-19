# Pumpkin

## Durable mechanics

- The repository's `builtins.py` is the game's `__builtins__.py` reference under a repository-friendly name.
- Successful `move()`, `plant()`, `harvest()`, `till()`, `use_item()`, and `spawn_drone()` calls cost about 200 ticks in the current tooltip model. Cheap observations such as `get_entity_type()`, `can_harvest()`, `measure()`, and coordinate reads are about 1 tick.
- Pumpkins grow on Soil. About one in five dies when it finishes growing.
- A dead Pumpkin can be replaced directly by planting another Pumpkin; harvesting the dead entity first is unnecessary.
- `measure()` returns a Pumpkin ID. Equal IDs are useful as a merge fast-path, but production correctness should not rely on global uniqueness alone.
- Drone memory is isolated. Persistent-worker designs must keep their unresolved-position state inside each worker or return it with `wait_for()`.

## Current production baseline

The 32x32 / 32-drone fast path in `pumpkin.py` assigns one worker per column.

Each worker already persists for the full Pumpkin cycle and caches rows once they are observed as live and harvestable.

The important remaining cost is physical movement: even when only one row remains unresolved, the current worker still performs a complete 32-step North loop to revisit it. At 200 ticks per successful move, the ready-row cache saves cheap observations but not the dominant movement cost.

The worker pool also spawns all 31 child workers from the same caller position. Spawn itself is expensive, so launcher topology is worth measuring separately.

## Reference findings

### MateusMarochi

`external/mateusmarochi-the-farmer-was-replaced-codes/source/pumpkin_farm.py`:

- keeps column workers alive indefinitely
- gives each worker stable spatial ownership
- tracks tile state locally
- repeatedly repairs only its assigned area

Its column traversal walks North and then South, so the local production North-wrap loop is cheaper for a complete scan.

`pumpkin_farm_2.py` is evidence for fixed small-region ownership rather than only full columns.

### msmith93

`external/msmith93-thefarmerwasreplaced/source/multidrone/pumpkin.py`:

- uses one drone per column
- exploits North-only wrap traversal
- keeps repairing a column until merge detection succeeds
- uses Fertilizer aggressively while waiting on failures

`pumpkin_leaderboard.py` independently uses a sparse dead-position list and revisits only those coordinates.

### Flekay

`external/flekay-the-farmer-was-replaced/source/Pumpkins/Multi Drone/mega_line.py`:

- plants a line
- collects dead/unready positions
- revisits only that shrinking list
- when at most three failures remain, uses Water/Fertilizer aggressively
- waits for the combined Pumpkin before harvest

The Flekay multi-drone README also describes `mega_chunk.py` as 32 workers with one 8x4 chunk each on a 32x32 field. The pinned file itself is empty, so only the documented architecture is usable as a reference.

`jarvan.py` demonstrates hierarchical power-of-two-style drone spawning. The exact fixed 29x29 layout is not reusable, but distributed spawning is worth benchmarking because `spawn_drone()` itself is a 200-tick action.

## Benchmark added 2026-09-19

Files:

- `bench_pumpkin.py`
- `bench_pumpkin_run.py`

The benchmark does not change production yet. It compares the current implementation against persistent sparse workers under identical 32x32 simulations.

Primary three-seed modes:

- `current-production`
- `sparse-1x32-tail`
- `sparse-4x8-tail`
- `sparse-8x4-tail`
- `tree-1x32-tail`
- `tree-4x8-tail`
- `tree-8x4-tail`

One-seed architecture/control smoke modes:

- `legacy-patch-wait`
- `sparse-1x32`
- `sparse-2x16`
- `sparse-4x8`
- `sparse-8x4`
- `sparse-16x2`

### Sparse worker design

Each worker owns exactly 32 tiles on a 32x32 / 32-drone farm.

After the initial plant pass it keeps only unresolved positions in a local list. A finished tile is never physically revisited. When only one tile remains, the worker stays on that tile instead of paying for another full line/chunk lap.

This is the main hypothesis to test.

### Tail boost

The `*-tail` modes adapt the strongest reusable part of Flekay's `mega_line.py`: when a worker has at most three unresolved positions, it waters and uses Fertilizer while repairing any Pumpkin that dies during accelerated growth.

The result output records Carrot, Water, and Fertilizer consumption so a faster mode can be rejected later if its resource cost is unacceptable.

### Spawn-tree experiment

The `tree-*` modes use the same region worker as the ordinary sparse modes. Only launcher topology changes.

Instead of one caller paying 31 sequential `spawn_drone()` calls, each worker recursively spawns up to two children and waits for them. This preserves finite worker lifetimes and gives the root a complete success result while allowing spawn actions to overlap across drones.

### Benchmark validity

Every candidate waits until all owned tiles have been observed live and harvestable, then uses the existing full-map Pumpkin ID check before harvesting. If the merge check is not yet conclusive, the benchmark falls back to the repository's robust collect/patch path.

The benchmark prints:

- simulation runtime
- in-simulation elapsed time
- ticks
- Pumpkin gain
- Carrot used
- Water used
- Fertilizer used
- success / valid

No winner is recorded yet. Production must not be changed from benchmark inspection alone.

## Next decision

Run `bench_pumpkin_run.py` in-game and keep only modes that report `valid True` and a full giant-Pumpkin gain.

Compare runtime first, then resource consumption. After measured results exist:

1. promote the measured winner into `pumpkin.py`
2. record the full 40-character benchmark commit SHA together with the measured numbers
3. update `docs/PUMPKIN.md`
4. re-run a smaller-world / fewer-drone smoke if the winning architecture is generalized beyond 32x32 / 32 drones


## Multi-cycle persistent extension 2026-09-19

The first benchmark commit measured one full-map harvest per simulation. That is necessary for cold-start comparison, but it does not answer whether worker setup should be amortized across consecutive Pumpkin production cycles.

The benchmark now also has a three-cycle `PUMPKIN AMORTIZED` matrix.

Fresh-per-cycle controls:

- `current-production`
- `sparse-1x32-tail`
- `sparse-4x8-tail`
- `sparse-8x4-tail`

True persistent modes:

- `persistent-1x32-tail`
- `persistent-4x8-tail`
- `persistent-8x4-tail`
- `persistent-tree-4x8-tail`
- `persistent-tree-8x4-tail`

The persistent modes call `clear()` and create their worker topology exactly once. Every worker then executes the same fixed number of full-map cycles.

No shared mutable Python state is required. Synchronization uses globally observable farm state:

1. each worker finishes its local region
2. worker 0 waits for the full-map Pumpkin-ID merge and harvests it
3. non-root workers wait for the Pumpkin at their region origin to disappear
4. that disappearance is the start signal for the next cycle

This directly tests the user's setup-cost concern: a candidate can lose the one-cycle cold benchmark but still win after three cycles if spawn/layout setup is sufficiently expensive.

The result line now includes:

- `completed`
- requested `cycles`
- total Pumpkin `gain`
- per-cycle `cycle gain`

A multi-cycle result is valid only if all requested cycles completed and every cycle produced the same positive gain.

The current decision rule is therefore:

1. use `PUMPKIN PRIMARY` to understand cold one-cycle behavior
2. use `PUMPKIN AMORTIZED` for the production architecture decision
3. reject any mode with `valid False`
4. do not promote production until the in-game results are measured


## Sparse benchmark bug found from in-game run 2026-09-19

Measured user run on 32x32 / 32 drones exposed a correctness failure in every sparse-region candidate.

Valid controls:

- `current-production`: 3,145,728 Pumpkin per cycle on seeds 1, 2, and 3
- `legacy-patch-wait`: 3,145,728 Pumpkin on the smoke run

Invalid sparse modes:

- `sparse-1x32-tail`
- `sparse-4x8-tail`
- `sparse-8x4-tail`
- all three corresponding tree-spawn modes
- all non-tail shape-smoke sparse modes

Every invalid sparse mode reached roughly 10-12 simulated seconds but produced zero Pumpkin and reported `valid False`.

### Root cause

The sparse worker treated this state as permanently finished:

`get_entity_type() == Entities.Pumpkin and can_harvest()`

That predicate is valid for a single mature Pumpkin, but it is also true for an already merged smaller Giant Pumpkin.

Sparse local repair makes some spatial regions complete much earlier than others. Those regions merge into smaller Giant Pumpkins. Once that happens, the worker removes the covered coordinates from its unresolved list.

The field can therefore end as a mosaic of harvestable partial Giant Pumpkins. There may be no dead, missing, or immature Pumpkin left for `collect_problem_positions()` to report, while opposite-corner Pumpkin IDs still differ.

This explains the observed combination:

- local workers report completion
- `collect_problem_positions()` eventually returns no useful repair work
- full-map ID check never succeeds
- gain remains zero

The supplied screenshot visually confirms the partial-Giant mosaic state.

### Consequence

Sparse coordinate elimination is not a safe Pumpkin optimization when it allows spatial regions to finish independently.

Modes 13..17, the first persistent-sparse experiment, are now explicitly rejected by the benchmark runner so they cannot enter the previous unbounded full-map merge wait.

The invalid sparse modes remain in the file as research history but are no longer part of the active candidate matrix.

## Replacement benchmark axis

The active benchmark now preserves the known-good North-only column-ring repair semantics and isolates only lifecycle/setup changes.

New modes:

- `ring-reuse`
  - fresh worker wave per cycle
  - clear only before cycle 1
  - preserves post-harvest Soil on later cycles
  - isolates field-reset/till cost from worker persistence

- `persistent-ring`
  - one column worker per column
  - same worker wave remains alive for all benchmark cycles
  - same North-only ring semantics as current production

- `persistent-tree-ring`
  - same persistent ring algorithm
  - distributed binary-tree worker spawning
  - tests spawn topology without changing Pumpkin repair semantics

The new matrices are:

Cold / one cycle:

- `current-production`
- `persistent-ring`
- `persistent-tree-ring`

Amortized / three cycles:

- `current-production`
- `ring-reuse`
- `persistent-ring`
- `persistent-tree-ring`

`legacy-patch-wait` remains a one-seed control.

## Stronger validity invariant

The supplied valid current-production logs produced exactly 3,145,728 Pumpkin on every full 32x32 harvest.

The benchmark now requires every cycle to equal exactly:

`3_145_728`

A merely positive Pumpkin gain is no longer sufficient for `valid True`.

This prevents partial Giant harvests or other accidental positive-gain states from being selected as benchmark winners.


## Spawn locality benchmark extension 2026-09-19

The active Pumpkin benchmark now also isolates the documented same-position spawn behavior.

New modes:

- `persistent-placed-ring`
  - direct version of the locality hypothesis
  - launcher walks East one column at a time
  - each child is spawned directly on its owned column
  - measures whether eliminating child positioning outweighs the launcher's serialized movement

- `persistent-spatial-tree-ring`
  - worker 0 remains at column 0 as merge/harvest coordinator
  - the remaining 31 columns are split into two arcs
  - first-level workers move to the midpoint of their arc
  - they spawn children only after reaching that local midpoint
  - recursion continues until every column has one persistent worker

For a 32-wide farm, the first spatial children target approximately columns 8 and 24, then 4/12 and 20/28, and so on.

This differs from the prior `persistent-tree-ring`, which parallelizes spawn calls but spawns descendants before moving to their own column. The old tree tests spawn topology only; the spatial tree tests topology + locality.

The one-cycle and three-cycle matrices now compare both variants against current production and the prior persistent ring controls.

Benchmark version:

`pumpkin-v4-spawn-locality`


## Measured ring benchmark baseline: pumpkin-v1

User-supplied in-game results on 2026-09-19, 32x32, 32 drones.

All listed candidates were valid and produced exactly 3,145,728 Pumpkin per cycle.

### Cold one-cycle averages

- `current-production`: 12.78 s
- `persistent-ring`: 14.06 s
- `persistent-tree-ring`: 13.65 s
- `legacy-patch-wait` control: 22.58 s (seed 1 only)

Cold-start conclusion:

- current production remains the fastest one-cycle path in this matrix
- persistence has setup overhead and should not be selected from a one-cycle benchmark

### Three-cycle amortized averages

- `current-production`: 39.10 s
- `ring-reuse`: 34.52 s
- `persistent-ring`: 33.88 s
- `persistent-tree-ring`: 31.51 s

Measured relative improvements of `persistent-tree-ring`:

- 19.4% faster than `current-production`
- 8.7% faster than `ring-reuse`
- 7.0% faster than `persistent-ring`

Additional decomposition:

- `ring-reuse` is 11.7% faster than current production, so avoiding repeated clear/re-till/rebuild cost is a major part of the total gain
- `persistent-ring` adds only about 1.9% over `ring-reuse` in this three-cycle matrix
- distributed tree spawning/lifetime improves further and is the measured v1 winner

### Interpretation

The benchmark supports persistent workers for repeated Pumpkin-focused production, but not for isolated single harvests.

The strongest measured v1 architecture is `persistent-tree-ring`.

Do not promote it yet because the current repository benchmark is newer than the supplied log and now includes spawn-locality candidates:

- `persistent-placed-ring`
- `persistent-spatial-tree-ring`

The supplied output begins with `BENCHMARK VERSION pumpkin-v1`; the current follow-up benchmark is `pumpkin-v3-spawn-locality`.

The next production decision must compare the v1 winner against those locality variants under the same three-cycle amortized matrix.


## Simulation speedup policy 2026-09-19

The active Pumpkin benchmark uses:

`BENCH_SPEEDUP = 10000`

This is an execution acceleration for `simulate()`; benchmark comparisons continue to use the simulation's returned elapsed time and in-simulation tick counters.

The high speedup is intentional so multi-seed and multi-cycle matrices finish much faster in wall-clock time. The game documentation notes that simulations may run below the requested speedup when computation, busy loops, or multiple drones become the limiting factor.

Benchmark version:

`pumpkin-v4-spawn-locality`
