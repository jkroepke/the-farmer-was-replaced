# j4.lc TFWR source snapshot

## Upstream

- URL: https://g.j4.lc/general-stuff/the-farmer-was-replaced
- Type: website / source collection
- Snapshot supplied by: repository user
- Archived: 2026-09-19
- Upstream revision: not exposed by the source URL
- Supplied archive SHA-256: `6918c9718f9ef2b1d1ef38918e521a33103adb2ea7b16afea46718d44f7da0d0`
- License/redistribution status: snapshot was directly supplied by the user
- Snapshot status: complete contents of the supplied archive are mirrored unchanged under `source/`

## Snapshot contents

- `FarmingChecks.py`
- `FarmingUtils.py`
- `Helpers.py`
- `Main.py`
- `README.md`
- `ZeroToHero.py`
- `cactus.py`
- `maze.py`
- `replant.py`

## Summary

This snapshot is centered around a `Leaderboards.Fastest_Reset` / `ZeroToHero` run.

Notable areas:

- upgrade selection based on approximate total resource cost
- generic resource dispatch for Wood, Carrot, Pumpkin, Power, Cactus, Bone, Gold and Weird Substance
- a Dinosaur/Bone route embedded in `ZeroToHero.py`
- Cactus neighbor-swap sorting
- Maze wall-following plus an alternative explicit search implementation
- Pumpkin patch/replant tracking
- wrap-aware coordinate movement helpers

The upstream README explicitly states that the scripts are **not claimed to be optimal** and that some scripts were taken from other places. Treat this as a useful implementation/reference snapshot, not as an authoritative or proven fastest implementation.

Files under `source/` are preserved unchanged from the user-supplied archive. Local analysis belongs in this README.


## Maze review

The supplied `maze.py` contains two different solvers:

### `solveMaze()`

This is the production path used by `startMaze()`.

It repeatedly attempts one direction, rotates after each attempt, and changes the rotation differently after a blocked move. Conceptually this is a simple wall-following solver for a fresh Maze.

It does **not** reuse the Maze graph/tree between Treasures. After the Treasure is harvested, the next `startMaze()` creates another Maze.

That architecture is already represented by this project's historical `fresh-right-hand` benchmark class and is substantially slower than the persistent reference-tree strategy at larger worlds.

For example, the existing 32x32 benchmark data shows:

- 25 relocations:
  - fresh wall-following baseline: 906.48 average runtime
  - reference-tree-rebalancing: 254.94
- 100 relocations:
  - fresh wall-following baseline: 3603.09
  - reference-tree-rebalancing: 950.66

So the j4lc production Maze solver is useful corroboration for the simple fresh-Maze baseline, but it is not a promising production replacement.

### `findTreasure()`

The file also contains a more explicit DFS-style search that tracks `been` and `path`.

Its `getBranching()` discovers neighbors by physically attempting all four moves and walking back after successful probes. It also checks path/visited membership with repeated linear list scans.

Those choices are expensive in the TFWR tick/interpreter model compared with:

- cheap `can_move()` observations
- coordinate-keyed sets/dictionaries
- the persistent ordered tree already used by this project

`findTreasure()` is not called by `startMaze()` in the supplied snapshot.

### Useful lifecycle idea: pre-produce Weird Substance

The more interesting reusable idea is outside pathfinding.

`substanceAbuse(count)` explicitly farms Weird Substance until a requested amount is available before continuing Maze work.

This reinforces an important production concern for this project:

> Do not throw away an already mapped/reused Maze merely because the next relocation runs out of Weird Substance if that starvation can be avoided by stocking enough resource before entering the Gold phase.

This project already has `MAZE_STOCKPILE`, currently measured in Maze-cost equivalents. The j4lc snapshot is a reason to benchmark stockpile policy separately from pathfinding, especially for long Gold runs where preserving the mapped Maze may be worth carrying a larger Weird Substance reserve.

Do not copy j4lc's exact `useSubstance()` cost calculation: it hard-codes `world_size * 1` and therefore does not model the current unlock-level-dependent Maze cost used by this project.
