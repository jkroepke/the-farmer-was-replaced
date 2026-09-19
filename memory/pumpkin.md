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

## Benchmark record

Measured Pumpkin runs, validity failures, and benchmark-derived comparisons are maintained in `bench/pumpkin.md`.

| Kind | Statement | Evidence |
| --- | --- | --- |
| Open question | Continue tuning initial and patch waits empirically instead of assuming fixed values are optimal. | Durable research note retained during the 2026-09-19 documentation consolidation. |
