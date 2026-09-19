# Reddit 32-square Maze packing reference

## Upstream

- Reddit thread:
  https://www.reddit.com/r/TheFarmerWasReplaced/comments/1wjxxhx/my_best_attempt_at_mazes_524_leaderboard_as_of/
- Relevant date: 2026-09-18
- Steam layout diagram linked from the comments:
  https://steamcommunity.com/sharedfiles/filedetails/?id=3803693955
- Reviewed: 2026-09-19

## Relevant ideas

The Reddit author uses one independent square Maze per drone on a 32x32 farm.

The fresh-Maze solver is described as a heuristic depth-first/backtracking search:

1. continue through forced corridors
2. at an intersection, prefer the direction most aligned with the measured Treasure
3. remember branch movement
4. on a dead end, backtrack to the prior intersection and try another branch

The author explicitly says this version is intended for non-reused Mazes.

A comment corrects the original claim about average Maze size and points out that
all 32 sub-Mazes together always cover the same total area when the 32x32 field
is completely tiled. The useful optimization target is instead the distribution
of individual Maze sizes / maximum Maze size because smaller searches tend to
finish faster.

The same comment describes a full 32x32 tiling by exactly 32 integer-sided
squares with side lengths between 4 and 7 and links a diagram. The original
poster reports that using the alternative layout improved their leaderboard
position from #524 to #514.

Another useful comment suggests handling loops in reused Mazes by treating
already-visited cells as blocked for the duration of one solve. The repository's
zapakh-style iterative DFS already has this property through its per-solve
`visited` set.

## Independent exact-cover reconstruction

The repository independently reconstructed a valid 32-square exact cover from
the public constraints. The size distribution is:

- 12 x 4x4
- 4 x 5x5
- 4 x 6x6
- 12 x 7x7

Area check:

```text
12 * 16 + 4 * 25 + 4 * 36 + 12 * 49 = 1024
```

The concrete lower-left coordinates are stored in
`bench_maze.py::SPEC_PACKED_32`.

The layout was programmatically checked to cover every one of the 1024 cells
exactly once with no overlap.

## Benchmark use

Two candidates are added:

- `packed-4to7-fresh`
  - full 32-square packing
  - one drone per square
  - fresh Maze after every Treasure
  - closest to the Reddit author's stated no-reuse assumption

- `packed-4to7-reuse`
  - identical packing
  - repository zapakh-style visited-set DFS
  - reuses each Maze
  - tests whether the loop-safe visited-set behavior can combine the better
    packing geometry with Maze reuse

These are benchmark candidates only until measured in-game.
