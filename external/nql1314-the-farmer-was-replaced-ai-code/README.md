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

Some files claim mutable Python data can be shared between drones through `wait_for()`. That conflicts with the current game model used by this project, where drones have independent memory and arguments are copied.

The repository is therefore an algorithm/data-structure reference, not an authoritative mechanics source.

A full source mirror is intentionally absent until redistribution permission is established.
