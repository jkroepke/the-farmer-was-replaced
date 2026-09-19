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

## Benchmark suite

Files:

- `bench_cactus.py`
- `bench_cactus_run.py`

Modes:

0. `current-production`
1. `two-wave-bubble-reset`
2. `two-wave-insertion-reset`
3. `two-wave-insertion-reuse`
4. `two-wave-insertion-reroll-reuse`
5. `tstambaugh-reference-32`
6. `nql1314-reference`

The candidate matrix runs modes 0..4 on seeds 1, 2, and 3 at 32x32 for three complete Cactus cycles.

The two source-near references run as one-seed smoke tests until they prove competitive.

Generalization smoke tests also run the insertion candidates on 6x6 and 16x16 worlds plus a 32x32 run with Megafarm level 3, so workers must process multiple lines via `index += worker_count`.

Important comparison axes:

- fused row lifecycle vs separate planting/readiness/sort waves
- bubble vs cached insertion sorting
- resetting every cycle vs reusing post-harvest field state
- reroll cost vs reduced inversion/swap cost
- source-near 32x32 leaderboard implementation vs generalized candidate

## Production decision

Do not replace `cactus.py` from source inspection alone.

Run `bench_cactus_run.py` in-game and compare:

- simulation runtime
- `CACTUS RESULT ... completed`
- `gain`
- ticks

A mode that is faster but does not complete all requested cycles or produces materially less Cactus is invalid.

After a winner is measured, promote only the winning generalized architecture to `cactus.py`. Keep 32x32 specialization only when the benchmark proves it useful.
