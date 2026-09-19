# zapakh / do_maze.py Gist

## Upstream

- URL: https://gist.github.com/zapakh/9a9b39a07964bbd27ab8cbd05ca35501
- Type: GitHub Gist
- File: `do_maze.py`
- Created: 2024-05-22
- Reviewed: 2026-09-19
- Revisions visible during review: 1
- License/redistribution status: no explicit license was visible on the Gist page during review
- Snapshot status: provenance only; source body is not mirrored because no redistribution license was identified

## Algorithm

The Gist implements an iterative, in-situ depth-first search:

- the drone's physical position is the DFS cursor
- a stack stores remaining directions plus the direction used for backtracking
- a visited set prevents revisiting cells
- candidate directions are ranked toward a measured Treasure coordinate
- the ranking intentionally appends less-favored directions first so `pop()` selects the preferred direction

This is interesting for very small Mazes because the repeated DFS has little state-management overhead when the graph contains only 16 cells.

## Current-game validity warning

The 2024 source uses `Items.Fertilizer` to create/recycle the Maze. Current game mechanics use `Items.Weird_Substance`, with Maze side length controlled by the amount passed to `use_item()`.

`bench_maze.py` therefore keeps the search algorithm source-near but adapts Maze creation and Treasure relocation to the current Weird-Substance API. Treat benchmark mode `zapakh-32x4x4` as a source-near algorithm port, not a byte-for-byte execution of the old script.
