# Maze

## Durable rules

- The research farm is currently 32x32 and the small-Maze benchmark must keep that world size unchanged.
- Do **not** use `set_world_size()` to create 3x3 or 4x4 benchmark Mazes.
- Maze side length is controlled by the amount passed to `use_item(Items.Weird_Substance, amount)`.
- Use `maze_size * 2 ** (num_unlocked(Unlocks.Mazes) - 1)` Weird Substance for an `maze_size x maze_size` Maze.
- `builtins.py` in this repository represents the game's `__builtins.py`/built-in API reference and is named differently only for repository usability.

## Historical baseline

The historical 8/16/32 benchmarks established `reference-tree-rebalancing` as the best completed single-drone full-Maze baseline. Those old matrices are documented in `docs/MAZE.md` and should not be rerun automatically during small-Maze experiments.

## Current experiment

`bench_maze_run.py` now targets a fixed amount of Gold on a real 32x32 farm and compares only the current baseline plus new small-Maze/multi-drone variants:

- `current-reference-32`: current full 32x32 tree-rebalancing strategy
- `cover-3x3`: one 3x3 Maze with 9 stationary drones, one per Maze cell
- `cover-4x4`: one 4x4 Maze with 16 stationary drones
- `cover-2x4x4`: two 4x4 Mazes with 16 stationary drones each
- `zapakh-32x4x4`: 32 independent 4x4 Mazes using zapakh's ranked iterative DFS
- `steam-32x4x4`: 32 independent 4x4 Mazes using the January 2026 route/map/path community algorithm

The default target is 200000 Gold, seeds 1/2/3, speedup 64. The full suite has now been measured; see the final benchmark section below.

- `simulate()` uses an isolated copy of the inventory. Gold earned by a benchmark does not change the real farm inventory, and `simulate()` returns only runtime.
- Special Maze modes print `MAZE SPECIAL RESULT <mode> gold gained <value> target <target> PASS|FAIL` inside the simulation so target completion can be verified independently from runtime.

Current benchmark implementation commit: `55734c855dd464dd846deef280d8a65d9f2c3bf7`.

## Stationary coverage design

- A 3x3 Maze at full Maze upgrades yields 9 * 32 = 288 Gold per collected Treasure, so a 200000-Gold benchmark necessarily crosses the 300-relocation reuse cap and must recreate at least once.
- `measure()` is not a reuse-cap signal: it continues to return the Treasure position after the cap. Detect the cap from failed `use_item(Items.Weird_Substance, amount)` instead, then `harvest()` so the fixed-root creator can recreate the Maze.

- Never start stationary Treasure workers while the Maze topology is still being mapped. A worker can relocate Treasure immediately, opening walls and invalidating the DFS that is still discovering cells.
- Coverage setup is therefore two-phase: map and harvest a temporary small Maze with one drone, place workers on the discovered cells while the field is open, then create the actual benchmark Maze at the same root.
- `bench_maze_run.py` prints `RUN <mode>` before each simulation so a stalled mode is directly identifiable.

For `cover-*`, do not assume which absolute cells a small Maze occupies. Create the Maze first, DFS through its actual reachable cells, and leave a worker on each visited cell. Workers use only shared game-world state; no Python memory is shared between drones.

The root worker is the fixed Maze creator. After the final Treasure is harvested and the Maze disappears, the root worker recreates the Maze at the same root using the same amount-based size. This prevents the Maze from drifting to the last Treasure coordinate.

## External references

- September 2026 Reddit 32-square packing:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1wjxxhx/my_best_attempt_at_mazes_524_leaderboard_as_of/
  - one square Maze per drone
  - comment identifies a complete 32x32 tiling with 32 squares sized 4..7
  - OP reports the alternative layout improved leaderboard position #524 -> #514
  - repository independently reconstructed a valid exact cover: 12x4, 4x5, 4x6, 12x7
  - exact layout is `bench_maze.py::SPEC_PACKED_32`
  - loop-handling comment matches the zapakh per-solve `visited` behavior
  - provenance in `external/reddit-32-square-maze/README.md`
- February 2026 Reddit 32x5x5 map+BFS:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1ra25ta/my_solution_for_the_maze_33mil_goldmin/
  - source-described 32 independent 5x5 Mazes
  - right-hand mapping of each fresh Maze
  - BFS to measured Treasure
  - update graph when reuse opens walls
  - reuse 300, harvest, remap
  - no code published; benchmark is behavioral reconstruction
  - provenance in `external/reddit-5x5-bfs/README.md`
- zapakh Gist: https://gist.github.com/zapakh/9a9b39a07964bbd27ab8cbd05ca35501
  - created 2024-05-22
  - iterative in-situ DFS with target-directed direction ranking
  - old source uses Fertilizer for Maze creation/recycling; current benchmark adapts only this API/mechanic to Weird Substance
  - archived as provenance under `external/zapakh-maze-dfs/`
- January 2026 Steam 32x4x4 discussion: https://steamcommunity.com/app/2060160/discussions/0/810218160537152525/
  - proposes 32 independent 4x4 Mazes, one per drone
  - source builds a route/connectivity map, performs route sweeps, then graph path search
  - archived as provenance under `external/steam-32x4x4/`
- Existing local references remain relevant, especially `external/msmith93-thefarmerwasreplaced/source/multidrone/maze_leaderboard.py` and the prior Pastebin tree-rebalancing reference.

## Final 200000-Gold benchmark

Tested against code commit `55734c855dd464dd846deef280d8a65d9f2c3bf7`, seeds 1/2/3, speedup 64. All runs passed the internal Gold assertion.

| Mode | Average runtime | Min | Max |
| --- | ---: | ---: | ---: |
| current-reference-32 | 122.63 | 117.42 | 129.17 |
| cover-3x3 | 33.44 | 31.84 | 35.27 |
| cover-4x4 | 28.20 | 28.12 | 28.28 |
| cover-2x4x4 | 21.68 | 21.09 | 22.54 |
| zapakh-32x4x4 | 13.51 | 13.27 | 13.87 |
| steam-32x4x4 | 22.07 | 22.03 | 22.11 |

Raw runtime-to-target: zapakh is 9.08x faster than current-reference-32.

Because Gold overshoot differs by mode, also compare normalized runtime per exactly 200000 Gold:

- current-reference-32: 106.92
- cover-3x3: 33.41
- cover-4x4: 28.17
- cover-2x4x4: 21.66
- zapakh-32x4x4: 12.76
- steam-32x4x4: 21.48

Gold-normalized result: zapakh is 8.38x faster than the current reference and is the current production candidate for 32x32 / 32-drone Gold farming.

## 32x4x4 launcher barrier

A screenshot from the in-game benchmark showed mode 10 stalled with drones distributed but no 4x4 Mazes created. This proved the hang occurred before the zapakh DFS.

Root cause: the launcher used a change in `num_items(Items.Water)` as a start signal. `use_item(Items.Water)` is not a guaranteed inventory-changing action on an arbitrary tile, so all workers can wait forever if the parent's Water use fails.

Current design:

- each child moves to its assigned 4x4 origin
- each child plants a Bush and waits without creating a Maze
- the parent visits all 31 child origins and waits until the Bush is visible
- after all 31 are confirmed, the parent moves to the 32nd origin
- the parent creates its own 4x4 Maze; the guaranteed Weird-Substance consumption is the shared start signal
- children then turn their already-planted Bushes into 4x4 Mazes
- the runner prints `ZAPAKH READY 31` / `STEAM READY 31` after the readiness scan

This avoids both the failed-Water deadlock and the earlier risk of creating Mazes while other workers are still moving through the open field.

## Production integration

The winning `zapakh-32x4x4` strategy is now integrated into the main production path through `maze_parallel.py`.

Current production rules:

- use adaptive parallel small Mazes when at least two independent small-Maze workers fit
- evaluate 4x4 and 3x3 layouts by `workers * maze_size * maze_size`; prefer 4x4 on ties
- 32x32 / 32 drones selects 32 independent 4x4 Mazes
- fewer drones reduce worker count automatically
- smaller farms reduce spatial capacity automatically
- if only one small-Maze worker is usable, fall back to the existing reference full-Maze solver
- 3x3 adaptive selection is functional but not yet separately benchmarked
- 25 relocations per worker is only the minimum start threshold
- if more Weird Substance is already available, use as many synchronized relocation rounds as the stock can safely fund, capped at 300
- stock at least the full minimum Weird-Substance budget before starting any worker
- at full 32x32 / 32-drone / x32 Maze multiplier, required stockpile is 106496 Weird Substance
- that burst yields approximately 425984 Gold
- production also requires one affordable Bush per planned worker
- the tested Bush/Weird-Substance barrier is reused; never use Water as the launch signal
- parent waits for every spawned worker before returning to the main loop
- production prints the chosen dynamic relocation count plus minimum/available substance
- if Gold cannot start, print `MAZE WAIT bushes ...` or `MAZE WAIT substance ...` to expose the blocker

Production integration commits begin at `b07d95a870252df2f093c250137b909557183f4c`; benchmark provenance remains `55734c855dd464dd846deef280d8a65d9f2c3bf7`.

## Extended Maze benchmark

Current unmeasured benchmark code state:
`c045c3da2a015b77491532199fc3f0735cc2a640`.

The extended matrix contains 22 modes:

- code/source-near controls: zapakh, Steam, msmith93
- source-described Reddit controls: September packed fresh intersection solver,
  February 32x5x5 right-hand map+BFS reuse
- exact-cover packed 4..7 geometry
- reuse-cap sweep: 0/fresh, 1, 2, 4, 8, 16, 300
- ranked vs unranked DFS
- Reddit branch solver with visited-set reuse mutation
- uniform 4x4 and 5x5 geometry controls
- map+BFS on uniform4, uniform5, and packed geometry

Benchmark groups:

- MAZE CORE: 200k Gold, seeds 1/2/3
- MAZE MAP: 200k Gold, seeds 1/2/3
- MAZE SUSTAINED: 1M Gold, seeds 1/2
- MAZE LEGACY REF: msmith93 last, 200k Gold, seeds 1/2/3

Every result prints Gold gained, Weird Substance used, tick count, target, and
PASS/FAIL.


Short-reuse lifecycle finding:

- the initial extended run stalled at packed zapakh reuse=1
- screenshot showed some packed Maze slots already harvested/open while others remained active
- root cause in the benchmark harness: `spec_move_to()` always moved East then North after harvest
- if the local origin was West/South of the Treasure, the worker could wrap around the world and hit a neighboring active Maze boundary forever
- `spec_move_to()` now chooses the shortest toroidal direction and returns `False` on a blocked move
- lifecycle callers abort that worker path on failure instead of rebuilding at the wrong coordinate
- runner now executes a 100k reuse1 rebuild smoke test before the full matrix
- partial extended timings from the pre-fix run are diagnostic only

Keep the old measured result separate: `zapakh-32x4x4` at 13.51 average
belongs to benchmark commit `55734c855dd464dd846deef280d8a65d9f2c3bf7`.

## Open questions

- Run the extended matrix and record only results from code state `c045c3da2a015b77491532199fc3f0735cc2a640`.
- Promote a new production geometry/solver only after both 200k and sustained
  results are known.
- Benchmark adaptive 3x3 zapakh production and reduced-drone layouts separately.
- Revisit `MAZE_PARALLEL_RELOCATIONS = 25` after the reuse-cap sweep identifies
  the best lifecycle.
