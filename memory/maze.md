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

The default target is 200000 Gold, seeds 1/2/3, speedup 64. Results are pending an in-game run.

- `simulate()` uses an isolated copy of the inventory. Gold earned by a benchmark does not change the real farm inventory, and `simulate()` returns only runtime.
- Special Maze modes print `MAZE SPECIAL RESULT <mode> gold gained <value> target <target> PASS|FAIL` inside the simulation so target completion can be verified independently from runtime.

Benchmark implementation commit: `600b4e061deaa6b2b64a7282289a07337330b5a3`.

## Stationary coverage design

For `cover-*`, do not assume which absolute cells a small Maze occupies. Create the Maze first, DFS through its actual reachable cells, and leave a worker on each visited cell. Workers use only shared game-world state; no Python memory is shared between drones.

The root worker is the fixed Maze creator. After the final Treasure is harvested and the Maze disappears, the root worker recreates the Maze at the same root using the same amount-based size. This prevents the Maze from drifting to the last Treasure coordinate.

## External references

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

## Open questions

- Measure the new suite before changing production `maze.py`.
- If a small-Maze mode wins, measure Weird Substance efficiency as a second axis; the first suite intentionally measures runtime to a fixed Gold target with oversized resources.
- Only promote finalists to broader target sizes/seeds after the first 200000-Gold comparison.
