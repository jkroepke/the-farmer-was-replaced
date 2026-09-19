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
