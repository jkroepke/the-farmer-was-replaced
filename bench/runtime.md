# Benchmark: Runtime / Spawn / Movement

## Scope

| Field | Value |
| --- | --- |
| Topic | Runtime / Spawn / Movement |
| Purpose | Measure runtime semantics and reusable low-level costs for drone memory, spawn topology, movement, and interpreter-sensitive hot paths. |
| Implementation | `drone_mem_probe.py`, `bench_spawn.py`, `bench_move.py`, `bench_ticks.py` |
| Runner | `drone_mem_run.py`, `bench_spawn_run.py`, `bench_move_run.py`, `bench_ticks_run.py` |
| Primary metric | Ticks and elapsed simulation time; semantic PASS/FAIL for memory probes. |
| Success condition | Runtime probes must pass; performance candidates must preserve equivalent work and setup. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| Drone memory semantics | `2fc84603c5566ecf17ea6ee8135ad394d1cfceb0` | Mutable-state isolation | Measured 12/12 PASS |
| `spawn-v5` | `cba75a7c26fd11da30408c8706deb8d8bf09d66a` | 32-worker topology | Measured |
| `move-v2` | `f309a1a6ab4423d22f9be26e41539ee8eed3aa21` | 32x32 movement | Measured |
| `ticks-v1` | Unknown / not recorded | Interpreter hot-path microbenchmarks | Pending |

## Results

### drone memory semantics 2026-09-19

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `2fc84603c5566ecf17ea6ee8135ad394d1cfceb0` |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Source state recorded |

#### Measurements and observations

| Field | Value |
| --- | --- |
| Source commit | `2fc84603c5566ecf17ea6ee8135ad394d1cfceb0` |
| Probe | `drone_mem_probe.py` |
| Runner | `drone_mem_run.py` |
| Purpose | Verify mutable state and `wait_for()` isolation semantics across drones. |
| Validity | 12/12 checks passed in the recorded in-game run. |


-----

### Verified current-runtime result

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

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


-----

### move-v2 and spawn-v5 2026-09-19

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | `move-v2`, `spawn-v5` |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Suite | Source commit | Requested speedup |
| --- | --- | ---: |
| `spawn-v5` | `cba75a7c26fd11da30408c8706deb8d8bf09d66a` | 10000 |
| `move-v2` | `f309a1a6ab4423d22f9be26e41539ee8eed3aa21` | 10000 |


-----

### Measured current-runtime results

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | `move-v2`, `spawn-v5` |
| Requested speedup | 10000 |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

#### move-v2 measured

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

#### spawn-v5 measured

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

| Mode | Time (s) | Ticks |
| --- | ---: | ---: |
| `binary-tree-nearest-origin00` | 0.90 | 4,498 |

That improvement comes mainly from combining hierarchical spawning with better
target locality, not from choosing a particular hierarchical dependency graph.

Durable conclusion:

- retain balanced binary as the generic spawn topology
- optimize worker origin/locality before micro-optimizing binary vs powers-of-two
- use hard-coded Flekay fan-out only if a domain benchmark shows a real
  end-to-end advantage, not from the 6-tick setup microbenchmark alone

-----

### Historical spawn locality: spawn-v1

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `c15c9f3ea47970cbbc6a4677bf5301a3a831b15e` |
| Benchmark/version | `spawn-v1` |
| World/profile | 32x32 / 32 drones / setup-only |
| Seeds | 1, 2, 3 |
| Validity | Deterministic setup comparison; all three seeds identical |

#### Measurements and observations

| Mode | Time (s) | Ticks |
| --- | ---: | ---: |
| `baseline-origin00-rowmajor` | 2.10 | 12,146 |
| `center-anchor-rowmajor` | 2.85 | 16,613 |
| `band-anchor-rowmajor` | 2.10 | 12,140 |
| `band-anchor-farthest-parent-near` | 3.39 | 20,011 |
| `nearest-slots-origin00` | 6.91 | 41,374 |
| `nearest-slots-farthest-parent-near` | 8.24 | 49,419 |
| `spawn-at-rowmajor-origins` | 5.98 | 35,671 |

| Kind | Statement |
| --- | --- |
| Measured | Moving the parent to the visual center was slower than the origin baseline. |
| Measured | Moving the parent to every child origin was decisively slower. |
| Caveat | The v1 nearest/farthest modes included O(n²) runtime planning in the timed section, so they are not clean locality comparisons. |
| Conclusion | Hierarchical spawning became the next hypothesis because child travel overlapped with the serial spawn chain. |

-----

### Historical spawn locality: spawn-v4

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `7c66b8422554d109e90220705e3841ea49081eca` |
| Structural commit | `2a217d6b4a42ea403c292fbc2e19428fd561b25b` |
| Benchmark/version | `spawn-v4` |
| World/profile | 32x32 / 32 drones / setup-only |
| Requested speedup | 10000 |
| Seeds | 1, 2, 3 |
| Validity | All three seeds identical |

#### Measurements and observations

| Mode | Time (s) | Ticks |
| --- | ---: | ---: |
| `baseline-origin00-rowmajor` | 2.10 | 11,832 |
| `origin00-parent-near` | 2.07 | 11,662 |
| `band-anchor-rowmajor` | 2.10 | 11,836 |
| `band-precomputed-farthest-parent-near` | 1.68 | 9,201 |
| `nearest-slots-precomputed-rowmajor` | 1.56 | 8,671 |
| `nearest-slots-precomputed-farthest-parent-near` | 1.40 | 7,605 |
| `binary-tree-rowmajor-origin00` | 1.29 | 6,892 |
| `binary-tree-nearest-origin00` | **0.90** | **4,498** |

| Kind | Statement | Evidence |
| --- | --- | --- |
| Measured | `binary-tree-nearest-origin00` reduced runtime by about 57.1%. | 2.10 s → 0.90 s |
| Measured | Tick count fell by about 62.0%. | 11,832 → 4,498 ticks |
| Conclusion | Binary spawning provides most of the gain; locality adds another measurable improvement. | 1.29 s binary-rowmajor vs 0.90 s binary-nearest |
| Conclusion | Visual center placement remains disproven for this workload. | v1/v4 comparison |

The exact Maze-target follow-up was tracked separately as `maze-v3`; setup-only spawn results must not be promoted directly into Maze production.

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Open question | No separate interpretation section was present in the migrated record. | Review result groups and Notes. |

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out the source commit listed for the result group. |
| 2 | Run the matching benchmark runner from Scope. |
| 3 | Preserve complete output and update this file without changing historical values. |

## Notes

### Current benchmark implementation status

#### spawn-v5 ready

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

#### move-v2 ready

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

### Expanded probe suite

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
