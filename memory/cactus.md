# Cactus

## Scope

Cactus optimization research for `cactus.py`, especially the 32x32 / max-Megafarm case while keeping production candidates valid for arbitrary world sizes and lower drone counts.

## Current production baseline

`cactus.py` currently uses four distinct synchronization stages:

1. parallel planting by column
2. repeated parallel full-field readiness scans
3. parallel row bubble-sort
4. parallel column bubble-sort
5. one chain harvest

`workers.run()` already lets the caller execute one task itself, so `max_drones() == world_size` does not waste a scheduler slot.

The expensive architectural issue is worker lifetime: every stage builds a new task list and spawns a new set of drones. Readiness may spawn multiple additional waves while cacti are growing.

## Current mechanics relevant to optimization

From the repository's current `builtins.py`:

- Cactus values are integers 0 through 9.
- A fully sorted field has nondecreasing values West -> East and South -> North.
- Harvest recursively follows adjacent sorted cacti.
- Cactus yield is the square of the number of cacti harvested.
- `measure()` and other observations are cheap compared with physical actions.
- successful `move()`, `plant()`, `swap()`, `till()`, `use_item()`, and `spawn_drone()` are physical actions with roughly 200-tick costs.
- `clear()` itself costs 200 ticks.
- Cactus average growth time is 1 second.
- `spawn_drone()` arguments are copied.

Current runtime drone-memory probes in `memory/drones.md` show that mutable state cannot be shared between workers through `wait_for()`.

## Reference review

### nql1314

Local snapshot:

`external/nql1314-the-farmer-was-replaced-ai-code/source/cactus_farm_mega.py`

Useful invariant:

- plant in parallel
- rows only with rows
- barrier
- columns only with columns
- barrier
- one harvest

Its literal hot path is not a production oracle: it performs repeated full bubble passes, repeated `goto()` calls, and debug output.

### MateusMarochi

Local snapshot:

`external/mateusmarochi-the-farmer-was-replaced-codes/source/cactus_farm.py`

Useful idea:

- long-lived workers own stable row/column indices
- worker 0 is the caller
- assignment scales with `max_drones()`

Caveat:

The source loops vertical and horizontal phases inside every persistent worker without a safe current-runtime barrier. Running row and column mutations concurrently is not adopted.

### tstambaugh92

Current external source reviewed at commit:

`057d780385e10580241b6646ac5de9667d98d544`

Relevant files:

- `harvester.py::harvest_cactus_leaderboard`
- `libfarm.py::insert_sort`

The 32x32 leaderboard implementation combines:

- one worker per row
- immediate measurement into a worker-local list
- quadrant-based value rerolling
- insertion sorting rows using cached values
- barrier
- insertion sorting columns using cached values
- one harvest

The reroll thresholds are:

- lower-left quadrant: reject values >= 5
- upper-right quadrant: reject values < 5
- off-diagonal quadrants: reject values outside 2..7

This biases the random field toward the final 2D gradient before paying adjacent-swap cost.

The source waits for a cactus to mature before destroying/replanting it. This is important because current game behavior does not provide a new random cactus value from repeatedly replanting the same immature cactus.

## Persistent-worker conclusion

A truly permanent pool spanning planting -> row sort -> column sort needs a barrier that all still-running workers can observe.

The historical shared-`wait_for()` mechanism is no longer available. Running row and column swaps concurrently is unsafe.

The benchmark therefore tests a **two-wave persistent architecture**:

1. row workers stay alive for their assigned rows and perform plant -> optional reroll -> sort -> readiness locally
2. `wait_for()` is the row/column barrier
3. column workers stay alive for all of their assigned columns and sort them
4. caller participates as worker 0 in both waves

For 32x32 with 32 drones this means two worker waves. With fewer drones, each worker keeps processing `index += worker_count`, so the same code works for arbitrary world sizes and drone counts.

## Benchmark record

Measured Cactus comparisons, worker experiments, and leaderboard benchmark history are maintained in `bench/cactus.md`.


## cactus-v3 measured result and production promotion 2026-09-19

Benchmark commit: `05ee0dbd2ff6483dec93c1707a0e957b25185c5f`.

The user ran the full `cactus-v3` suite in-game.

### Exact cold leaderboard workload

All candidates completed one 32x32 cycle with the exact expected gain of
33,554,432 Cactus on all three seeds.

Measured averages:

- `current-production`: 42.04 s
- `tstambaugh-reference-32`: 39.49 s
- `tstambaugh-placed-generalized`: 40.70 s
- `adaptive-placed-pool`: 40.64 s
- `adaptive-binary-spawn`: 40.62 s
- `adaptive-flekay-powers`: 38.93 s
- `current-production-fresh`: 42.37 s

Therefore `adaptive-flekay-powers` is the measured cold-target winner:

- about 7.4% faster than current production
- about 4.2% faster than `adaptive-placed-pool`
- about 1.4% faster than the source-near Tstambaugh reference

Skipping the extra `clear()` did not improve the measured result and is not
promoted.

### Three-cycle production workload

All finalists completed all three cycles with the exact expected total gain of
100,663,296 Cactus on every seed.

Measured averages:

- `adaptive-placed-pool`: 123.18 s
- `adaptive-binary-spawn`: 118.91 s
- `adaptive-flekay-powers`: 114.93 s

The powers-of-two topology is about 6.7% faster than the previous production
architecture on this measured workload.

### Production decision

Promote the powers-of-two distributed spawn topology only for the exact
measured production case:

- world size 32
- at least 32 available drones

Keep the existing placed/batched architecture for:

- smaller worlds
- 32x32 with fewer than 32 drones

This preserves the already measured 6x6, 16x16, and 32x32/8-drone behavior
instead of extrapolating the new spawn topology beyond its benchmark evidence.

The dedicated `lb_cactus.py` automatically uses the new production path on
the full 32x32 leaderboard setup because it calls `cactus.run()`.
