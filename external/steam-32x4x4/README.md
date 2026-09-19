# Steam 32x4x4 Maze reference

## Upstream

- URL: https://steamcommunity.com/app/2060160/discussions/0/810218160537152525/
- Type: Steam community discussion
- Relevant post date: 2026-01-20
- Reviewed: 2026-09-19
- License/redistribution status: no explicit redistribution license identified
- Snapshot status: provenance only; forum code is not mirrored verbatim

## Algorithm

The relevant community post reports a 32-drone strategy where every drone owns an independent 4x4 Maze on the same 32x32 farm.

The posted solver:

1. creates a 4x4 Maze with `4 * 2**(maze_level - 1)` Weird Substance
2. walks a deterministic route to map all 16 cells and local connectivity
3. performs repeated route sweeps, collecting Treasures encountered on the route
4. refreshes connectivity as Maze walls disappear
5. later uses the discovered graph plus iterative-deepening path search to the measured Treasure

The post reports more than 2M Gold/min for its environment. That number is community-reported historical data, not a result verified by this repository.

## Benchmark use

`bench_maze.py` mode `steam-32x4x4` keeps the route/map/path architecture but adds:

- the repository's fixed-Gold benchmark stop condition
- current API usage
- safe handling when the Maze reuse limit is reached

These changes are benchmark harness adaptations; the core search architecture remains source-near.

The launcher also preserves the correction posted later in the same thread: the parent moves to `(14, 30)`, attempts the original 8x8 grid of 4x4 origins, and then owns the 32nd Maze itself when further spawns fail at the 32-drone limit. Workers move to their assigned origins themselves, preserving parallel positioning, and keep the source's initial `do_a_flip()`.
