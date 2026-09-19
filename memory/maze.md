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

Measured benchmark code state:
`c045c3da2a015b77491532199fc3f0735cc2a640`.

The rebuild smoke test for packed Zapakh reuse=1 passed after the local-return
fix: 100000 Gold target, 126368 Gold gained, 27392 Weird Substance, 93546
ticks, runtime 15.98.

200000-Gold / 3-seed highlights:

- uniform4 map+BFS reuse300: 13.29 avg (13.24..13.32) — fastest raw runtime
- ref zapakh uniform4 reuse300: 13.92 avg
- uniform4 zapakh reuse8: 13.98 avg
- uniform5 zapakh reuse300: 15.92 avg
- Reddit5 map+BFS reuse300: 16.09 avg
- packed Reddit visited reuse300: 16.19 avg
- packed unranked reuse300: 18.62 avg
- packed Zapakh reuse-cap sweep:
  - reuse1 19.78
  - reuse2 19.35
  - reuse4 19.09
  - reuse8 19.56
  - reuse16 19.84
  - reuse300 19.59
- fresh variants are materially slower.

1000000-Gold / 2-seed sustained highlights:

- Reddit5 map+BFS reuse300: 31.72 avg — fastest measured sustained mode
- packed map+BFS reuse300: 33.65
- packed Reddit visited reuse300: 34.20
- ref zapakh uniform4 reuse300: 38.40
- packed unranked reuse300: 43.12
- packed Zapakh reuse300: 43.20
- packed Zapakh reuse8: 44.68
- described Reddit packed fresh: 48.69

Sustained normalized throughput/resource findings:

- Reddit5 map+BFS is about 21% faster than uniform4 Zapakh at 1M after
  normalizing Gold overshoot.
- approximate Weird Substance / Gold:
  - uniform4 Zapakh reuse300: 0.254
  - uniform5 map+BFS reuse300: 0.205
  - packed map+BFS reuse300: 0.197
- packed map+BFS is slightly slower than uniform5 map+BFS at 1M but more
  substance-efficient.
- ranking toward the Treasure is not universally helpful: packed unranked
  reuse300 beat packed ranked Zapakh reuse300.
- the full-field 4..7 packing is not automatically faster than uniform layouts.

Cold-start vs sustained behavior:

- short 200k strongly favors low setup cost
- map+BFS amortizes its initial mapping cost and improves sharply at 1M
- rough two-point estimate:
  - uniform4 Zapakh ~30.8 s per additional 1M Gold after setup
  - uniform5 map+BFS ~19.6 s per additional 1M
  - packed map+BFS ~18.8 s per additional 1M
- this is only an interpolation; the real leaderboard workload must decide.

Legacy source-near msmith93 full32 fresh completed all three seeds:
40.26 avg, 32.77 min, 51.33 max.

Critical missing comparison:

- uniform4 map+BFS reuse300 won the 200k screen but was omitted from the
  original 1M sustained set.
- do not replace production solely from the 200k result.
- next benchmark must include uniform4 map+BFS at 1M and then use the exact Maze
  leaderboard target 9863168 Gold, end-to-end including setup and termination.

## Maze leaderboard decision rule

For the Maze leaderboard, ignore shorter benchmark winners when selecting the
final algorithm. The only decisive metric is cold-start end-to-end runtime
until:

```python
num_items(Items.Gold) >= 9863168
```

Every candidate/seed must start in its own fresh `simulate()` run. Include all
setup, drone spawning/positioning, initial Maze creation, map/index building,
reuse, rebuilds, and termination in the measured runtime.

200k and 1M results are diagnostic/ablation evidence only.

Current exact-target cold-start runner commit:
`15b81ee34fe9c8366cae17d70d3a27eac7d98053`.

It tests 5 finalist architectures over seeds 1/2/3.

## Leaderboard implementation

Dedicated leaderboard files now exist:

- `lb_maze.py`
  - finite Maze leaderboard program
  - target: `num_items(Items.Gold) >= 9863168`
  - current long-run candidate: 32 independent 5x5 Mazes
  - right-hand map each fresh Maze
  - BFS to Treasure
  - learn newly opened walls during reuse
  - reuse limit 300
  - one Maze per drone
  - explicit termination after target
- `lb_maze_run.py`
  - calls `leaderboard_run(Leaderboards.Maze, "lb_maze", 64)`

Implementation commit: `916b8e7e62131ac25747fbb0f9855311f3434fe3`.
Runner commit: `84456a348c51eaca597ae6400e8673bdd8865b7f`.

Important: the exact 9863168-Gold cold-start finalist benchmark still decides whether
this 5x5 map+BFS implementation remains the final leaderboard architecture.

## Spawn-position optimization

`spawn_drone(task, *args)` creates the child at the caller's current position.
This creates a cold-start optimization opportunity.

Important finding:

- simply moving the parent from `(0,0)` to the geometric middle before spawning
  is probably counterproductive
- on the current uniform 5x5 layout, moving to about `(12,12)` costs ~24
  serial parent moves before any child exists, while reducing the slowest
  child's initial trip only from about 30 to about 25 moves
- because children move concurrently, serial parent movement is much more
  expensive than a few saved child moves

Stronger mutation:

- parent follows one snake route through all final Maze origins
- at each child origin, spawn the child directly on its final tile
- wait locally until that child has planted its ready Bush
- continue to the next origin
- the final route endpoint belongs to the parent, which creates the release Maze
- child positioning cost becomes zero
- the old second full parent readiness scan disappears

Approximate serial parent movement:

- current uniform5 launcher: ~194 moves
- route-spawn uniform5 launcher: ~162 moves
- current uniform4 launcher: ~140 moves
- route-spawn uniform4 launcher: ~128 moves

Benchmark modes:

- mode 32: uniform5 map+BFS reuse300 + route spawn
- mode 33: uniform4 map+BFS reuse300 + route spawn

Exact-target cold-start runner commit:
`c0ec1a179bae7d73372be428f20954682e8c0e21`.

Do not update `lb_maze.py` to route spawning until the exact 9863168-Gold
cold benchmark confirms the gain.

## Open questions

- Run exact-target cold-start runner commit `15b81ee34fe9c8366cae17d70d3a27eac7d98053` and select by average time to 9863168 Gold.
- Promote a new production geometry/solver only after both 200k and sustained
  results are known.
- Benchmark adaptive 3x3 zapakh production and reduced-drone layouts separately.
- Revisit `MAZE_PARALLEL_RELOCATIONS = 25` after the reuse-cap sweep identifies
  the best lifecycle.


## Spawn locality research

Verified game/API behavior:

- `clear()` moves the controlling drone to `(0,0)`.
- `spawn_drone(task, *args)` creates the child on the caller's current tile.
- successful `move()` costs about 200 ticks.
- successful `spawn_drone()` costs about 200 ticks.

Current `maze_parallel.run()` does:

1. `clear()`, leaving the parent at `(0,0)`
2. spawn every child at that same tile
3. each child independently calls `utils.move_to(origin_x, origin_y)`
4. parent later moves to its own Maze origin

This makes spawn position a real setup variable.

Important geometry correction:

Because normal movement wraps, the visual center of the 32x32 farm is not inherently a globally better fixed spawn point. A useful spawn anchor must be chosen against the actual worker-origin set.

For the current 32-worker uniform 4x4 production layout, the first 32 row-major block centers occupy only part of the 64 possible 4x4 slots. Therefore `(0,0)`, `(16,16)`, and a band-centered anchor such as `(0,8)` are meaningfully different for this exact origin set even though the full toroidal farm has no privileged center.

Potential setup optimizations to benchmark:

- one common anchor, then children self-position
- choose a better 32-slot subset from the 64 possible 4x4 blocks
- spawn the farthest children first so their travel overlaps later spawn calls
- reserve the nearest Maze origin for the parent because it only starts its own positioning after child launch
- controller `spawn_at`: move parent to each origin, spawn there, then continue
- hierarchical spawning if a later benchmark shows sequential parent spawning is the bottleneck

ScienceJiho's current-memory-compatible reference already contains a generic `spawn_at()` helper that moves the controller to a worker start before spawning. Its own documentation warns that controller repositioning becomes setup cost, so this must be measured rather than assumed faster.

### Spawn locality microbenchmark

Benchmark version: `spawn-v1`

Benchmark commit: `c15c9f3ea47970cbbc6a4677bf5301a3a831b15e`

Files:

- `bench_spawn.py`
- `bench_spawn_run.py`

The benchmark isolates the 32-worker / 4x4-Maze setup and compares:

```text
baseline-origin00-rowmajor
center-anchor-rowmajor
band-anchor-rowmajor
band-anchor-farthest-parent-near
nearest-slots-origin00
nearest-slots-farthest-parent-near
spawn-at-rowmajor-origins
```

It deliberately does not run a Maze solver. Every worker only reaches its assigned origin and plants its initial Bush. This establishes whether spawn geometry has enough effect to justify adding the best topology as a mode to the expensive exact-9863168-Gold leaderboard benchmark.

Run:

`bench_spawn_run.py`

Do not change `maze_parallel.py` production spawn topology until this microbenchmark is measured and the promising candidate is validated end-to-end in the Maze benchmark.


## Spawn locality benchmark results

### spawn-v1

Benchmark version: `spawn-v1`

Benchmark commit: `c15c9f3ea47970cbbc6a4677bf5301a3a831b15e`

Measured 32x32 / 32-drone setup-only results, identical across seeds 1/2/3:

```text
baseline-origin00-rowmajor                   2.10 s / 12146 ticks
center-anchor-rowmajor                      2.85 s / 16613 ticks
band-anchor-rowmajor                        2.10 s / 12140 ticks
band-anchor-farthest-parent-near            3.39 s / 20011 ticks
nearest-slots-origin00                      6.91 s / 41374 ticks
nearest-slots-farthest-parent-near          8.24 s / 49419 ticks
spawn-at-rowmajor-origins                   5.98 s / 35671 ticks
```

Durable conclusions:

- moving the parent to the visual farm center before spawning is worse than the current `(0,0)` baseline
- a simple `(0,8)` band anchor ties the baseline almost exactly, so reducing average child travel alone does not improve wall-clock setup
- moving the parent to every child origin and spawning in place is decisively worse
- child travel is heavily overlapped with the serial spawn chain, so the critical path is not the sum of all child distances
- the v1 nearest/farthest modes are not valid locality comparisons because their O(n²) runtime planning is inside the timed section and dominates their results
- the identical outputs across all three seeds show this setup benchmark is deterministic

The main architectural hypothesis after v1 is therefore hierarchical spawning: reduce the serial 31-spawn chain itself rather than merely shortening independently parallel child travel.

### spawn-v3 follow-up

Current benchmark version: `spawn-v3`

Current benchmark commit: `2a217d6b4a42ea403c292fbc2e19428fd561b25b`

`spawn-v3` replaces runtime nearest/farthest planning with precomputed origin tables and adds binary-tree spawning.

Modes:

```text
baseline-origin00-rowmajor
origin00-parent-near
band-anchor-rowmajor
band-precomputed-farthest-parent-near
nearest-slots-precomputed-rowmajor
nearest-slots-precomputed-farthest-parent-near
binary-tree-rowmajor-origin00
binary-tree-nearest-origin00
```

The binary tree recursively splits a fixed worker range. Each branch spawns one child branch while continuing the other branch itself, reducing the dependency depth toward log2(worker_count). Only integer layout/start/count arguments are passed so copied spawn arguments do not include the full origin table.

Run `bench_spawn_run.py` and require the first line to be:

```text
BENCHMARK VERSION spawn-v3
```

Do not promote spawn topology to production from the setup microbenchmark alone. If a v3 mode materially beats the 2.10-second baseline, add that exact topology to the full cold Maze leaderboard benchmark at 9863168 Gold before changing production.
