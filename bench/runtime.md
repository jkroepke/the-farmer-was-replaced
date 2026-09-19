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

-----

## Run: drone memory semantics 2026-09-19

### Provenance

| Field | Value |
| --- | --- |
| Source commit | `2fc84603c5566ecf17ea6ee8135ad394d1cfceb0` |
| Probe | `drone_mem_probe.py` |
| Runner | `drone_mem_run.py` |
| Purpose | Verify mutable state and `wait_for()` isolation semantics across drones. |
| Validity | 12/12 checks passed in the recorded in-game run. |

## Expanded probe suite

`drone_mem_probe.py` now tests the semantics independently:

- global mutation isolation
- mutable list arguments passed to spawned drones
- nested mutable argument copying
- closure-captured list isolation
- normal worker return-value communication
- repeated `wait_for(source)` calls in the parent
- repeated `wait_for(source)` calls inside one worker
- parent mutation -> worker visibility
- worker mutation -> parent visibility
- worker mutation -> later worker visibility
- nested source-return isolation
- the historical producer/consumer queue pattern

The cross-worker tests are intentionally sequential. That removes scheduler races and makes any cumulative mutable state evidence much stronger.

The parent/worker repeated-wait tests accept and report either `copy-per-wait` or `same-drone-alias` for calls made by the same drone. The critical invariant is cross-drone isolation.

## Verified current-runtime result

Executed in-game on 2026-09-19 via `drone_mem_run.py`.

Simulation runtime reported: `1.5` seconds.

Complete result:

```text
DRONE_MEMORY RUN START
DRONE_MEMORY SUITE START
DRONE_MEMORY global PASS worker-mutates-parent-stays-zero
DRONE_MEMORY spawn-arg-list PASS copied
DRONE_MEMORY spawn-arg-nested PASS deep-copied
DRONE_MEMORY closure-list PASS isolated
DRONE_MEMORY return-value PASS worker-to-caller
DRONE_MEMORY source-parent-repeat PASS copy-per-wait
DRONE_MEMORY source-worker-repeat PASS copy-per-wait
DRONE_MEMORY source-parent-worker PASS parent-mutation-not-visible
DRONE_MEMORY source-worker-parent PASS worker-mutation-not-visible
DRONE_MEMORY source-worker-worker PASS historical-exploit-isolated
DRONE_MEMORY source-nested PASS deep-isolation
DRONE_MEMORY source-queue PASS historical-producer-consumer-isolated
DRONE_MEMORY SUMMARY 12 12
DRONE_MEMORY RESULT PASS
DRONE_MEMORY RUN DONE 1.5
```

-----

## Run: move-v2 and spawn-v5 2026-09-19

### Provenance

| Suite | Source commit | Requested speedup |
| --- | --- | ---: |
| `spawn-v5` | `cba75a7c26fd11da30408c8706deb8d8bf09d66a` | 10000 |
| `move-v2` | `f309a1a6ab4423d22f9be26e41539ee8eed3aa21` | 10000 |

## Measured current-runtime results

### move-v2 measured

Measured on 32x32 with requested simulation speedup 10000.

Key warm result at 1000 targets:

| Mode | Run ticks | Outer sim time |
| --- | ---: | ---: |
| `utils-arithmetic` | 4,415,004 | 1453.75 |
| `delta-static` | 4,416,320 | 1454.18 |
| `direction-static` | 4,420,320 | 1455.50 |
| `dict-runtime` | 4,422,320 | 1456.25 |
| `list-runtime` | 4,422,320 | 1456.25 |
| `delta-known-current` | **4,412,322** | **1452.89** |

Cold behavior tells the same story:

- current arithmetic helper and static delta are effectively tied at low counts
- runtime-built dict/list lookup pays about 197-199 setup ticks and never
  recovers that cost in this workload
- direction/count lookup is slower than arithmetic
- carrying known current coordinates is the only measured improvement

At 1000 targets, `delta-known-current` saves only 2,682 ticks versus
`utils-arithmetic`, about 0.061% of total run ticks.

Durable conclusion:

- keep `utils.move_to()` as the generic repository helper
- do not replace it with precomputed delta/list/dict navigation
- only use the known-current-coordinate specialization inside a hot algorithm
  that already has authoritative current coordinates for other reasons
- Flekay's historical 10x10 navigation ranking does not transfer materially to
  the current 32x32 runtime

### spawn-v5 measured

Topology-only comparison on the same 32 row-major origins and the same parent
target:

| Topology | Outer runtime | Internal ticks |
| --- | ---: | ---: |
| serial parent | 2.07 | 11,662 |
| dual spawner | 1.56 | 8,546 |
| **Flekay powers-of-two** | **1.29** | **6,886** |
| Jarvan powers-of-two | 1.30 | 6,977 |
| balanced binary | **1.29** | 6,892 |

All three seeds were identical.

Interpretation:

- serial -> dual gives a large improvement
- deeper hierarchical fan-out gives another large improvement
- Flekay powers-of-two and local balanced binary are effectively tied
- Flekay is only 6 ticks cheaper than balanced binary (~0.087%)
- Jarvan's dynamic power calculation costs 91 ticks versus Flekay and 85 ticks
  versus balanced binary
- the tiny Flekay edge does not justify replacing the generic balanced binary
  helper with a hard-coded 32-worker dependency graph

The previously measured `binary-tree-nearest-origin00` result remains the
strongest complete spawn+locality setup:

```text
0.90 s / 4498 ticks
```

That improvement comes mainly from combining hierarchical spawning with better
target locality, not from choosing a particular hierarchical dependency graph.

Durable conclusion:

- retain balanced binary as the generic spawn topology
- optimize worker origin/locality before micro-optimizing binary vs powers-of-two
- use hard-coded Flekay fan-out only if a domain benchmark shows a real
  end-to-end advantage, not from the 6-tick setup microbenchmark alone
