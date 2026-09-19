# Runtime, spawn, and movement benchmarks

This file is the canonical home for measured benchmark results for this topic.

| Field | Value |
| --- | --- |
| Migrated from | `memory/flekay.md` |
| Result rule | Every canonical run must name the full Git source commit that pins runner and implementation. |
| Separation | Use `-----` between runs produced from different code states or materially different setups. |
| Interpretation | Keep measured facts separate from conclusions and open questions. |

## Referenced commits in migrated history

| Referenced commit | `cba75a7c26fd11da30408c8706deb8d8bf09d66a` |
| Referenced commit | `f309a1a6ab4423d22f9be26e41539ee8eed3aa21` |

A referenced commit is not automatically a benchmark source commit. Each result block must explicitly identify which commit produced it. If an older block lacks that mapping, treat it as historical/non-canonical and rerun it before using it for a production decision.

-----
## Current benchmark implementation status

### spawn-v5 ready

`bench_spawn.py` / `bench_spawn_run.py` now contain a topology-only shootout
using the same `CURRENT_ORIGINS` target set and the same root/parent target
(`CURRENT_ORIGINS[0]`) for every candidate:

- serial control: `origin00-parent-near`
- dual-spawner
- Flekay precomputed powers-of-two fan-out
- Jarvan dynamic powers-of-two fan-out
- local balanced binary tree

This deliberately excludes `binary-tree-nearest-origin00` from the topology
comparison because that mode changes both topology and target geometry.

Benchmark version: `spawn-v5`
Requested speedup: `10000`
Benchmark code state: `cba75a7c26fd11da30408c8706deb8d8bf09d66a`.

### move-v2 ready

New files:

- `bench_move.py`
- `bench_move_run.py`

32x32 movement modes:

- current `utils.move_to()` arithmetic control
- static signed-delta table
- static direction/count table
- runtime-built dict lookup
- runtime-built list lookup
- static delta table while carrying known current coordinates, avoiding
  `get_pos_x()/get_pos_y()` in the hot route loop

Cold counts:

- 1
- 10
- 100 targets

Warm counts:

- 10
- 100
- 1000 targets

For warm comparisons, use the internal `run ticks` from `MOVE RESULT`.
The outer `simulate()` time still includes table setup because every
simulation starts from a fresh file execution.

Benchmark version: `move-v2`
Requested speedup: `10000`
Benchmark code state: `f309a1a6ab4423d22f9be26e41539ee8eed3aa21`.
