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

The full-field exact cover is now used as a geometry axis across several solver
families.

Source-described candidate:

- `desc-reddit-packed-fresh`
  - forced corridors
  - record intersections
  - choose the branch most aligned with the Treasure
  - rewind recorded movement on dead ends
  - no reuse, matching the Reddit author's stated assumption

Repository mutations include:

- zapakh ranked DFS, fresh and reused
- reuse-cap sweep 1 / 2 / 4 / 8 / 16 / 300
- Reddit intersection solver plus a visited set for loop-safe reuse
- unranked DFS, fresh and reused
- right-hand map + BFS, fresh and reused

Uniform 4x4 and 5x5 layouts are benchmarked alongside the exact cover so the
effect of geometry can be separated from the solver.

The extended benchmark code state is:

`b51873132eec90ee623e513f5b8479b1e86f0997`

These candidates remain unmeasured until an in-game benchmark run is recorded.
