# nql1314/The-Farmer-Was-Replaced-AI-Code

## Upstream

- URL: https://github.com/nql1314/The-Farmer-Was-Replaced-AI-Code
- Type: GitHub repository
- Reviewed: 2026-09-19
- Upstream revision: 688325db004607563e59535a15ce94fad092ff9f
- Default branch: main
- License/redistribution status: no redistribution license was established during review

## Summary

Broad TFWR implementation repository containing experiments for multiple mechanics.

Notable reusable ideas:

- precomputed traversal/path tables
- stable spatial worker partitioning
- separate parallel Cactus row and column phases
- phase-level tick measurement
- persistent-worker-loop experiments
- specialized Pumpkin layouts
- Maze map caching and BFS
- Dinosaur Hamiltonian/safe-target and A* experiments

## Validity warnings

The repository contains a historically real but now outdated shared-memory technique based on repeatedly calling `wait_for()` on the same completed source drone.

Evidence and timeline:

- upstream revision reviewed here: `688325db004607563e59535a15ce94fad092ff9f`, dated 2025-11-01
- upstream `docs/DRONE_SHARED_MEMORY_DISCOVERY.md` records an experiment from 2025-10-23 where multiple drones call `wait_for(source)` and observe cumulative mutations of the returned list
- the current game documentation explicitly states that drones have separate memory and that `spawn_drone(function, *args)` copies arguments
- the game's 2025-12-04 update says: "Fixed shared memory bugs."
- the game's 2026-02-17 update is even more specific: "Fixed another bug that allowed you to get shared memory between multiple drones."

Current authoritative references:

- https://thefarmerwasreplaced.wiki.gg/wiki/Megafarm
- https://steamcommunity.com/app/2060160/announcements/
- https://steamdb.info/patchnotes/21969917/

Therefore the nql1314 shared-`wait_for()` architecture should be treated as a **historical engine exploit/bug that may have worked on the 2025 game build**, not as a valid current game mechanic.

This distinction matters: the upstream repository was not necessarily wrong when the experiment was recorded. The game semantics changed afterward.

A local runtime probe is provided in this repository as `probe_drone_memory.py` / `probe_drone_memory_run.py` to verify the current behavior directly. Probe runner commit: `058e4040733fb75715def99f1a7a036d8d254406`.

The repository remains useful as an algorithm/data-structure reference, but mechanics assumptions must be checked against the current game version.

A full source mirror is intentionally absent until redistribution permission is established.
