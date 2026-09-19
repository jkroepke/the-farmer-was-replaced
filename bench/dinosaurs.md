# Benchmark: Dinosaur

## Scope

| Field | Value |
| --- | --- |
| Topic | Dinosaur |
| Purpose | Compare Dinosaur path geometry, shortcut policies, field setup, tail targets, and exact leaderboard Bone throughput. |
| Implementation | `bench_dinosaur.py` |
| Runner | `bench_dinosaur_run.py` |
| Primary metric | Bone throughput plus elapsed time at the same tail target; exact Bone gain for validity. |
| Success condition | Candidate must reach the requested tail target, emit `DINOSAUR BENCH VALID`, and match the exact expected Bone gain. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| Historical initial matrix | Unknown / not recorded | 8x8 / 16x16 / 32x32 target sweeps | Measured historical |
| Near-full production sweep | Unknown / not recorded | 95 / 97 / 99 / board-1 | Measured historical |
| v3 matrix | `7e51103180c4484ef68e91c974fcca5b05f94af9` | 32x32 / leaderboard-shaped matrix | Superseded before final measurement |
| `dinosaur-v4` | Unknown / not recorded | Flekay diagnostics + Reddit candidates | Preview invalid due accounting bug |
| `dinosaur-v5` | `cd3070188dce3da68a5c065fb16caafa5917c7f1` | Corrected head/tail accounting | Superseded |
| `dinosaur-v6` | `7081dc129241652273e6793d3352db487faf3fdf` | Corrected Reddit phase translation | Superseded |
| `dinosaur-v7` | `ed6bc455c7705cbd501798470fd3095f65b4f823` | Boolean move-check fix | Current; pending full run |

## Results

### 8x8

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Target | Hamiltonian | Annealed 50 | Hard 25 | Hard 50 | skysdottir reference |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25% | 17.06 | 15.18 | 14.60 | 14.60 | **11.57** |
| 50% | 25.90 | **24.03** | 25.14 | 25.70 | 25.38 |
| 75% | 30.04 | **29.00** | 30.37 | 31.43 | 30.14 |
| 95% | 31.14 | **30.34** | 31.81 | 32.99 | 31.51 |

Observations:

- At only 25% fill, the reference is about 32% faster than the baseline.
- At larger 8x8 targets the simple annealed skyscraper shortcut mode is slightly fastest.
- The advantage becomes small near a full board.
- Hard cutoff at 50% is consistently unattractive late in the run.


-----

### 16x16

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Target | Hamiltonian | Annealed 50 | Hard 25 | Hard 50 | skysdottir reference |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25% | 173.85 | 146.28 | 142.07 | 142.07 | **93.11** |
| 50% | 215.90 | 245.25 | 202.12 | 254.54 | **187.03** |
| 75% | 234.76 | 277.65 | 234.27 | 287.50 | **220.16** |
| 95% | 241.43 | 287.95 | 245.12 | 298.10 | **230.92** |

Observations:

- The skysdottir reference wins all completed 16x16 cases.
- Relative to the baseline, its improvement is approximately:
  - 46% at 25% fill
  - 13% at 50% fill
  - 6% at 75% fill
  - 4% at 95% fill
- Hard-25 is much better than Hard-50 once the target exceeds 25%.
- Continuing to evaluate shortcuts too long can be slower than simply following the Hamiltonian cycle.
- The source-like annealed skyscraper mode also becomes slower than baseline after 25% on 16x16.
- This strongly supports an early-shortcut / late-Hamiltonian hybrid, but the path geometry matters: the Hilbert-based reference still outperforms our skyscraper adaptation on 16x16 despite earlier community reports that Hilbert can be slower.


-----

### 32x32, 25% tail target

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | 1 |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hamiltonian | 1172.46 | 1295.70 | 1344.10 | 1270.75 | 1172.46 | 1344.10 |
| Annealed 50 | 1369.73 | 1617.97 | 1569.37 | 1519.02 | 1369.73 | 1617.97 |
| Hard 25 | 1449.68 | 1600.50 | 1621.25 | 1557.14 | 1449.68 | 1621.25 |
| Hard 50 | 1449.68 | 1600.50 | 1621.25 | 1557.14 | 1449.68 | 1621.25 |
| **skysdottir reference** | **673.48** | **693.09** | **688.40** | **684.99** | **673.48** | **693.09** |

This is a very strong result.

At 25% tail occupancy on the production-relevant 32x32 board:

- the skysdottir reference is about **46% faster** than the plain Hamiltonian baseline
- our annealed skyscraper shortcut adaptation is about **20% slower** than baseline
- our hard-cutoff skyscraper variants are about **23% slower** than baseline

This cleanly separates two ideas:

> Shortcutting itself is not the problem. Our skyscraper shortcut implementation/path interaction is the problem.

The source-near Hilbert/reference algorithm scales much better in the early run.


-----

### 32x32, 50% tail target

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | 1 |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average |
| --- | ---: | ---: | ---: | ---: |
| Hamiltonian | 1717.07 | 1815.90 | 1864.77 | 1799.24 |
| Annealed 50 | 2830.86 | 3247.93 | 3194.96 | 3091.25 |
| Hard 25 | 2293.98 | 2445.27 | 2495.80 | 2411.68 |
| Hard 50 | 3255.35 | 3447.38 | 3452.73 | 3385.16 |
| skysdottir reference | 1881.48 | 1779.06 | 1815.69 | 1825.41 |

At a 50% target on 32x32:

- target tail length: 512
- expected harvest: 262,144 Bones
- Hamiltonian throughput: about **145.70 Bones/s**
- skysdottir reference throughput: about **143.61 Bones/s**

The difference is only about 1.5% in favor of Hamiltonian.

This is very different from the 25% target:

- Hamiltonian: about **51.57 Bones/s**
- skysdottir reference: about **95.67 Bones/s**

So the reference nearly doubles throughput early, but by 50% the two whole-run strategies are essentially tied.

The source reference changes character around half-board because shortcutting disappears and the remaining run becomes mostly Hilbert traversal.

That suggests a path-geometry tradeoff:

- Hilbert/reference: excellent early shortcut opportunities
- skyscraper: potentially cheaper pure traversal once shortcut value has disappeared

A mid-run switch from one unrelated Hamiltonian cycle to another is **not automatically safe**, because the existing tail occupies positions according to the old path/history. Do not switch from a Hilbert body directly onto the skyscraper cycle without proving tail safety.

Safer optimization directions are:

1. tune the reference shortcut cutoff earlier
2. keep Hilbert but stop expensive shortcut evaluation earlier
3. benchmark full-run throughput at 75% and 95%
4. select the whole-run strategy based on requested Bone target if the later throughput diverges


-----

### 32x32, 75% tail target

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Strategy | Average runtime | Bones/s | Bones/min |
| --- | ---: | ---: | ---: |
| **Hamiltonian skyscraper** | **2110.43** | **279.48** | **16,768.86** |
| Annealed 50 | 3598.76 | 163.90 | 9,833.78 |
| Hard 25 | 2915.91 | 202.28 | 12,136.65 |
| Hard 50 | 3892.07 | 151.55 | 9,092.70 |
| skysdottir reference | 2314.80 | 254.81 | 15,288.32 |

At 75%, plain Hamiltonian is about **9.7% higher throughput** than the reference.


-----

### 32x32, 95% tail target

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

| Strategy | Average runtime | Bones/s | Bones/min |
| --- | ---: | ---: | ---: |
| **Hamiltonian skyscraper** | **2214.39** | **426.66** | **25,599.42** |
| Annealed 50 | 3759.81 | 251.29 | 15,077.10 |
| Hard 25 | 3079.88 | 306.76 | 18,405.58 |
| Hard 50 | 4055.29 | 232.98 | 13,978.54 |
| skysdottir reference | 2475.46 | 381.66 | 22,899.64 |

At 95%, plain Hamiltonian is about **11.8% higher throughput** than the reference.

More importantly, Hamiltonian throughput still rises sharply with target tail size:

| Target | Hamiltonian Bones/s | Reference Bones/s |
| ---: | ---: | ---: |
| 25% | 51.57 | **95.68** |
| 50% | **145.70** | 143.61 |
| 75% | **279.48** | 254.81 |
| 95% | **426.66** | 381.66 |

From 75% to 95%, Hamiltonian throughput increases by about **52.7%**. Therefore 95% cannot yet be treated as the throughput optimum; it is simply the highest tested target.

The next throughput search should concentrate near full occupancy rather than re-running dominated shortcut modes. Candidate targets:

```text
95%, 97%, 99%, 100%/board-1
```

For this sweep, compare only:

- `hamiltonian-skyscraper`
- `skysdottir-tfwr-reference`

A natural collision/end-of-run harvest is also worth measuring because production currently behaves closer to that than to an arbitrary 95% cutoff.


-----

### Sustained-throughput results

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The three-cycle benchmark confirms that repeated harvest/restart does not change the broad strategy ranking.

#### Sustained 25%

| Strategy | Average runtime | Bones/s | Bones/min |
| --- | ---: | ---: | ---: |
| Hamiltonian skyscraper | 4030.07 | 48.79 | 2,927.11 |
| **skysdottir reference** | **2108.50** | **93.25** | **5,594.72** |

At 25%, the reference provides about **91% more sustained Bone throughput** than Hamiltonian.

#### Sustained 50%

| Strategy | Average runtime | Bones/s | Bones/min |
| --- | ---: | ---: | ---: |
| **Hamiltonian skyscraper** | **5559.11** | **141.47** | **8,488.03** |
| skysdottir reference | 5596.54 | 140.52 | 8,431.27 |

At 50%, the two strategies are effectively tied. Hamiltonian is only about **0.7% higher throughput**.

This mirrors the single-run result and shows that restart/setup overhead is not responsible for the crossover.

#### Sustained 75% — partial

The supplied output currently contains Hamiltonian seed 1:

| Metric | Value |
| --- | ---: |
| Runtime (s) | 6403.10 |
| Bones/s | 276.35 |
| Bones/min | 16,580.77 |

That is very close to the single-run 75% Hamiltonian result of 279.48 Bones/s, suggesting restart overhead becomes negligible for long-tail runs.

Finish the remaining sustained 75% and 95% cases before making the final production choice.


-----

### Final near-full benchmark results

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The production-focused near-full sweep compared only the two remaining candidates on 32x32.

#### Single-run throughput

| Target | Tail | Hamiltonian Bones/s | Reference Bones/s |
| ---: | ---: | ---: | ---: |
| 95% | 972 | **426.66** | 381.66 |
| 97% | 993 | **444.66** | 397.55 |
| 99% | 1013 | **462.43** | 413.33 |
| 100% / board - 1 | 1023 | **464.86** | 417.96 |

Single-run Hamiltonian throughput continues increasing up to the maximum safe target.

#### Sustained throughput, 3 cycles

| Target | Hamiltonian Bones/s | Hamiltonian Bones/min | Reference Bones/s | Reference Bones/min |
| ---: | ---: | ---: | ---: | ---: |
| 95% | **410.13** | **24,607.87** | 376.21 | 22,572.82 |
| 97% | **434.59** | **26,075.21** | 390.80 | 23,448.29 |
| 99% | **447.85** | **26,870.79** | 405.28 | 24,316.92 |
| 100% / board - 1 | **453.57** | **27,214.07** | 415.31 | 24,918.30 |

The sustained winner is therefore:

```text
strategy: hamiltonian-skyscraper
target: board - 1
tail: 1023 on 32x32
throughput: 453.57 Bones/s
throughput: 27,214.07 Bones/min
```

At the same target, Hamiltonian is about **9.2% higher sustained throughput** than the skysdottir reference.

The 100% benchmark is not a literal full 1024-cell tail. The benchmark clamps the target to `board - 1`, so on 32x32 it stops at tail length 1023.

The near-full sweep also resolves the target question: throughput did not peak at 95%, 97%, or 99%; the highest tested sustained throughput is at the maximum safe target.

For steady-state Bone production, the current benchmark evidence therefore favors:

> **plain Hamiltonian skyscraper, harvested at board - 1**

The skysdottir reference remains useful only for short targeted runs, where its early shortcut phase is substantially faster.


-----

### Flekay deep-dive findings (2026-09-19)

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The current upstream `Flekay/The-Farmer-Was-Replaced` still points at revision `567e0ab6f96305cd6c9a05fd5eea2917449c2407` from 2026-01-28, so the local mirror is current as of this review.

#### Historical Dinosaur benchmark caveat

Flekay's Dinosaur README reports:

| Upstream mode | Time (s) |
| --- | ---: |
| `drone.py` | 18.741 |
| `circle.py` | 23.924 |
| `timon.py` | 27.889 |
| `almighty.py` | 42.221 |

Do not treat these times as measurements of the files currently present on `main`.

The README was last changed in the 2025-10-05 clean-upload history, while `drone.py` was changed later by commit `d3a0fc555d5e78466fd1eb39e608b9ef0627b6b6` ("Simplify drone's dino movement logic") on 2025-10-18.

That later commit replaced a complete implementation with a three-phase skeleton whose `phase_two()` deliberately contains an unimplemented placeholder. Therefore the published 18.741-second result necessarily refers to an earlier implementation, not the current `drone.py`.

The pre-change `drone.py` is still available through Git history at parent revision `fe4df71ae877a484b091c2fa276cae0a6f0e2039`.

Its useful architecture is:

1. aggressively chase early Apples with parity-based two-direction rules
2. stop the early phase after 50 collected Apples
3. derive a deterministic "almighty" route from the current head/body state
4. follow that route until blocked

The old implementation also contains hard-coded `100`-cell assumptions. Other Flekay Dino files reinforce that historical geometry:

- `circle.py` has explicit coordinate maps for `0..9` and switches around length 38
- `timon.py` has forbidden cells `(1,1)..(1,9)` and reports length 34 as its tuned transition
- `hybrid.py` switches greedy -> stack around length 18 and stack -> almighty around 34

These are useful **phase-ratio ideas**, not current 32x32 constants. The v4 diagnostic benchmark therefore tests 10%, 18%, 25%, 34%, and 50% occupancy rather than blindly reusing absolute lengths 18/34/50.

#### Failed moves as cheap branch probes

Flekay's early Dinosaur scripts frequently use:

```text
if not move(preferred):
    move(fallback)
```

instead of:

```text
if can_move(preferred):
    move(preferred)
```

Current Flekay tick research records both `can_move()` and a failed `move()` as one tick, while a successful Dinosaur move is the physical action we wanted anyway.

This makes optimistic "try preferred, fall back on failure" a useful early-phase policy when either successful direction is safe. It cannot replace the stronger cycle-order safety checks used by arbitrary Hamiltonian shortcuts.

#### Cleanup spawn topology

Flekay's historical `Movement/line_formation` benchmark reports:

```text
for_all.py                  25006 runtime ticks
for_all_dual.py             16224 runtime ticks
for_all_sync_col/row.py     16224 runtime ticks
```

The important reusable idea is parallelizing the **spawn chain itself**, not only the field work.

The v4 Dinosaur setup sweep now includes:

- Flekay-style sequential line spawning
- Flekay-style dual-spawner fan-out

in addition to the existing serial/current/skysdottir preparation modes.

These upstream tick numbers are historical evidence only; the local 32x32 setup sweep is the decision source.

#### Interpreter hot-path implications

Flekay's measured tick model records, among other things:

- `get_pos_x()`: 1 tick
- `get_pos_y()`: 1 tick
- `measure()`: 1 tick
- `random()`: 1 tick
- tuple-key dictionary lookup: tuple length in ticks (2 ticks for `(x,y)`)
- integer-key dictionary lookup: 1 tick
- list/set/dict construction and mutation are not free
- list `pop(0)` scales with the list length
- set/dict membership is 1 tick
- list/tuple membership is linear
- `pass`: 1 tick
- `continue`: 0 ticks

This supports the existing ring-buffer design and suggests a later ablation for the safe-shortcut implementation:

- tuple-key path dictionary vs compact integer/nested-list representation
- per-step temporary list allocation vs two fixed shortcut candidates
- annealing/random gate vs fixed early cutoff
- current coordinate API reads vs explicitly tracked head coordinates

Do not optimize these before the route-level v4 results identify which shortcut family is worth keeping.

#### Path precomputation

Flekay's loop-around benchmark shows that precomputed direction sequences can reduce repeated traversal decision overhead after setup.

This suggests a small future Dinosaur ablation:

- current structured skyscraper loops
- one precomputed skyscraper direction list reused for every cycle
- indexed path lookup

However, the current plain Hamiltonian baseline is already extremely simple, so this is lower priority than route policy and harvest target.

#### Generic pathfinding break-even

Flekay's pathfinding benchmark reinforces that more planning can cost more ticks than it saves.

Historical totals:

```text
5 points:
  unordered        5702
  nearest-neighbor 5030

20 points:
  unordered        11802
  nearest-neighbor 10155

60 points:
  unordered        21602
  nearest-neighbor 30855
```

The same README contains `divinepath` result rows, but the pinned/current `benchmark.py` does not import such an implementation and no corresponding source file exists in the directory. Treat those rows as non-reproducible.

For Dinosaur, generic A*/TSP-style planning remains a control experiment rather than a primary production candidate.

#### All-pairs non-wrapping route precomputation

Flekay reports:

| Upstream mode | Setup time (s) | Ticks / benchmark |
| --- | ---: | ---: |
| `goto.py` | 0.0002 | 7,590 |
| `runto_local.py` | 7.7344 | 7,470 |

The tiny warm-path saving does not justify the very large precomputation for changing random Apple targets. Do not add an all-pairs Dino routing table based on this evidence.


-----

### Dinosaur benchmark v5 accounting correction

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | `dinosaur-v4`, `dinosaur-v5` |
| Requested speedup | Not recorded |
| Seeds | 1 |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The first live `dinosaur-v4` preview exposed a benchmark accounting bug.

Observed at the nominal 25% target:

```text
reported tail: 256
actual harvested Bones: 2,080,800
runner expected Bones:  2,097,152
```

The observed reward is exactly:

```text
255 * 255 * 32 = 2,080,800
```

This proved that the child benchmark's `CURRENT_TAIL_LENGTH` / `REF_ACTUAL_TAIL_LENGTH` counters represented **occupied Dinosaur length = head + tail segments**, while the Bone reward formula uses **tail segments only**.

Consequences for v4:

- every nominal target stopped one Apple too early
- a nominal 25% / 256-tail run actually harvested a 255-segment tail
- a nominal board-1 / 1023-tail run would actually harvest 1022 segments
- `1022 * 1022 * 32 = 33,423,488`, below the real leaderboard target
- therefore v4 results must be treated as preview/diagnostic only and not as final benchmark data

v5 fixes this by separating:

- reward tail target: `target_tail_length()`
- occupied/head+tail termination target: `target_snake_length() = target_tail_length() + 1`

The 32x32 board-1 case now targets:

```text
tail segments: 1023
occupied cells: 1024
expected Bones: 1023 * 1023 * 32 = 33,488,928
```

Every successful cycle additionally validates its exact observed Bone gain against:

```text
target_tail_length() ** 2 * 32
```

A mismatch emits `DINOSAUR BENCH INVALID bone-gain ...`.

Implementation:

- `7febc4bd1238a54e9ae4456ab3621d9d0625241d` — fix head/tail accounting and per-cycle Bone validation
- `cd3070188dce3da68a5c065fb16caafa5917c7f1` — bump runner to `dinosaur-v5`

#### v4 preview signal

The incomplete v4 Seed 1 / 25% preview is not valid final benchmark data because of the one-Apple-short target, but its relative route signal is useful:

| Scenario | Mode / metric | Time (s) | Ticks | Notes |
| --- | --- | ---: | ---: | --- |
| — | `hamiltonian-skyscraper` | 1176.76 | — | — |
| — | `skysdottir-hilbert-reference` | 677.80 | — | — |
| — | `heartbeat-shortcuts-annealed50` | 999.26 | — | — |
| — | `heartbeat-fastlane-annealed50` | 1133.28 | — | — |

Relative to the Hamiltonian preview:

- skysdottir reference: ~42.4% faster
- heartbeat annealed shortcuts: ~15.1% faster
- heartbeat fast-lane annealed: ~3.7% faster

The tested skyscraper shortcut / fast-lane variants were ~46% to ~59% slower than the plain Hamiltonian preview.

Do not promote any of these based on v4. Re-run `bench_dinosaur_run.py` with `BENCH_VERSION = "dinosaur-v5"`.

## Interpretation

### Throughput reinterpretation

The initial benchmark discussion focused too much on raw runtime. For production, Bone throughput is the more important metric.

Because:

```text
Bones = tail_length ** 2
```

larger tail targets can dominate throughput even when they take longer.

Example from the completed 16x16 data:

| Target | Tail | Bones | Reference runtime | Reference Bones/s | Hamiltonian Bones/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25% | 64 | 4096 | 93.11 | 43.99 | 23.56 |
| 50% | 128 | 16384 | 187.03 | 87.60 | 75.89 |
| 75% | 192 | 36864 | 220.16 | 167.44 | 157.03 |
| 95% | 243 | 59049 | 230.92 | **255.71** | 244.58 |

So the 95% reference run has almost 6x the Bone throughput of the 25% reference run, despite taking much longer.

The same effect already appears in partial 32x32 data:

| Target | Sample | Tail | Bones | Reference time (s) | Hamiltonian Bones/s | Reference Bones/s |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 25% | average | 256 | 65,536 | 684.99 | — | 95.67 |
| 50% | seed 1 | 512 | 262,144 | — | 152.67 | 139.33 |

Therefore:

> The fastest algorithm to a short tail is not automatically the best Bone producer.

For production, the likely optimum may be a long 75-95% run even if its wall-clock duration is higher.

### Plausibility check

For a 25% target, `safe-shortcuts-hard-25` and `safe-shortcuts-hard-50` are identical for every shown seed.

That is expected: both modes use identical shortcut behavior until 25% fill, and the benchmark stops there. This is a useful confirmation that the cutoff plumbing behaves as intended.

### Current benchmark conclusion

Do not promote the current skyscraper shortcut variants.

For short 32x32 runs, the source-near reference is best, but the final near-full sweep resolves steady-state production in favor of plain Hamiltonian skyscraper. At board - 1, Hamiltonian reaches 453.57 sustained Bones/s versus 415.31 for the reference.

This makes target-aware Bone production more important: if the planner needs only a modest Bone amount, stopping around a short tail target can exploit the reference algorithm's strongest phase instead of paying for a long late-game traversal.

## Reproduction

### Benchmark convention

Use the repository-wide convention:

- `bench_dinosaur.py` — all Dinosaur benchmark modes
- `bench_dinosaur_run.py` — matrix, seeds, `simulate()`, and result aggregation

Do not create one benchmark file per strategy.

### Suggested benchmark workflow

Dinosaur full-board 32x32 runs can be expensive.

Use staged benchmarking:

1. 8x8 for correctness/debugging
2. 16x16 for tuning
3. 32x32 only for promising finalists
4. one seed during early iteration
5. three seeds for final comparisons

When tuning shortcut cutoff, compare only the current best path and candidate cutoff values rather than rerunning every historical mode.

## Notes

### Implemented initial benchmark modes

The first benchmark now exists in:

- `bench_dinosaur.py`
- `bench_dinosaur_run.py`

Current modes:

| Mode | Strategy | Purpose |
| ---: | --- | --- |
| 0 | `hamiltonian-skyscraper` | current production-style baseline |
| 1 | `safe-shortcuts-annealed-50` | source-like shortcut probability that fades toward 50% fill |
| 2 | `safe-shortcuts-hard-25` | always evaluate safe shortcuts until 25% fill, then pure Hamiltonian |
| 3 | `safe-shortcuts-hard-50` | always evaluate safe shortcuts until 50% fill, then pure Hamiltonian |
| 4 | `skysdottir-tfwr-reference` | source-near behavioral port of `dinos3.py` + `hilbert.py`: Hilbert cycle, source tail queue semantics, annealing, 50% cutoff |

Modes 1-3 deliberately use the same skyscraper/Hamiltonian geometry as production. This isolates shortcut value from path-shape changes.

Mode 4 is intentionally different: it preserves the current `skysdottir/tfwr` reference path and control flow closely enough to detect performance lost in our adaptations. The benchmark still stops at the same actual consumed-Apple/tail target so runtime remains comparable.

Future modes can add edge-wave, Moore, Hilbert, and the Pastebin implementations after the current benchmark establishes a shortcut baseline.

Do not replace production `dinosaur.py` until a candidate wins deterministic simulation benchmarks.

### Benchmark dimensions

For production selection, the runner now focuses on:

```text
world size: 32
target tail occupancy: 95%, 97%, 99%, 100% (clamped to board - 1)
seeds: 1, 2, 3
speedup: 10000
strategies:
- hamiltonian-skyscraper
- skysdottir-tfwr-reference
```

8x8 and 16x16 remain useful as historical/debugging data, but they should not decide the production algorithm when the real production farm is 32x32.

The benchmark stops at fixed tail occupancy rather than only filling the board. This remains useful because shortcut value is concentrated in the early/middle run and because the optimal cutoff may be 25% rather than 50%.

The benchmark prints `DINOSAUR BENCH INVALID` if a strategy encounters a failed `move()` before reaching its requested tail target. Treat such a result as invalid even if the returned runtime looks fast.

For each run, start from:

- empty field
- same world size
- same simulation seed
- oversized Cactus inventory
- same unlock state

#### Primary production metric: Bone throughput

Runtime is only directly comparable **between strategies at the same tail target**, because those runs produce the same Bone amount.

Across different target tail lengths, the primary metric is:

```text
Bones per second = tail_length ** 2 / runtime
Bones per minute = Bones per second * 60
```

The runner now prints:

- runtime
- target tail length
- expected Bones
- Bones/second
- Bones/minute

This distinction is critical because Bone yield grows quadratically with tail length. A 95% run can be much slower in absolute time and still produce far more Bones per unit time than a 25% run.

Useful verbose diagnostics:

- ending `get_tick_count()`
- successful moves
- Apples collected
- shortcut attempts
- shortcuts taken
- moves saved by shortcuts
- tail length at completion

### Current benchmark v3

The old sustained-throughput results above remain useful historical evidence, but the next comparison is now explicitly leaderboard-shaped.

Implementation commits:

- `bench_dinosaur.py` strategy expansion: `624827d0520ca183353c0102562dfdc253d6fab1`
- setup/accounting fix: `92e420f70a8c76c498caf0d5beb2e06425456300`
- explicit valid-run marker: `1ecfb09d2cdfd8078c182f7b5e7f48d291316e55`
- `bench_dinosaur_run.py` leaderboard matrix: `1f65a3663e6322d07b80496b71ea5bd84b4c2544`
- raw-summary warning: `7e51103180c4484ef68e91c974fcca5b05f94af9`

The runner uses:

```text
world size: 32
targets: 25%, 50%, 75%, 95%, board-1
seeds: 1, 2, 3
simulate speedup: 10000
starting items: 1e9 Cactus + 1e9 Power
unlocks: all
leaderboard target: 33,488,928 Bone
```

The board-1 case means tail length 1023. With the max Dinosaur yield multiplier this is exactly:

```text
1023 * 1023 * 32 = 33,488,928 Bone
```

#### Algorithm matrix

The v3 matrix contains 20 modes:

- plain skyscraper Hamiltonian
- existing skyscraper shortcut variants
- skysdottir Hilbert source-near reference
- skyscraper fast-lane shortcut variants
- heartbeat Hamiltonian
- heartbeat shortcut / fast-lane variants
- Hilbert without shortcuts
- Reddit coil/strike with 33%, 50%, and 66% safe-transition points

The fast-lane modes implement the useful dormant ideas visible in the skysdottir source: use a cheap path-specific lane toward the cycle's return corridor before normal greedy Apple-direction shortcuts.

#### Field preparation / cleanup benchmark

The second Reddit/skysdottir reference performs preparation in parallel with multiple drones before starting the Dinosaur:

- harvest tiles
- convert them to Soil
- wait for all preparation workers
- return to the origin
- equip the Dinosaur Hat

The Reddit author explicitly says they had not checked whether removing Grass was necessary for Dinosaurs.

Current game documentation makes this worth measuring: Apples cannot spawn on occupied tiles, and Grass can grow automatically on Grassland. Therefore preparation may prevent later Apple blockage, but its startup cost may also be wasted on a fresh leaderboard field.

The v3 runner separately compares six preparation modes:

1. no cleanup
2. `clear()`
3. serial harvest + Soil conversion
4. parallel harvest only
5. parallel harvest + Soil conversion
6. source-style Sunflower-Hat + parallel harvest + Soil conversion

The main algorithm matrix currently uses parallel harvest + Soil conversion so route comparisons share the same field condition.

#### Result validity

`simulate()` returns elapsed time, not a child-script success flag. Every successful child run therefore emits:

```text
DINOSAUR BENCH VALID ...
```

Failures emit:

```text
DINOSAUR BENCH INVALID ...
```

At the 32x32 board-1 target, the child also checks the real leaderboard threshold `num_items(Items.Bone) >= 33488928`.

Runner summaries are intentionally labeled `RAW`. Never treat a fast summary row as a winner when any corresponding seed emitted `INVALID`.

No v3 performance result has been measured yet. Do not change production `dinosaur.py` until the v3 output has been collected and all candidate winners are valid across the compared seeds.

### Local upstream archive

The reviewed skysdottir reference is indexed locally at:

`external/skysdottir-tfwr/`

The source-near benchmark should remain tied to the upstream revision recorded there.

### Dinosaur benchmark v4

Flekay-derived additions were implemented after the v3 matrix:

- `be91a2d6ad846490130bea03cb965d48d86f085a` — Flekay early-phase diagnostics, dual/line cleanup topologies, repeated Bone-target support
- `4ed309863c7199b3d3a9bf08bfd1137a7b57093a` — v4 runner matrix

New algorithm diagnostic modes:

- mode 20: simple axis-greedy
- mode 21: parity-greedy based on Flekay `drone.py` phase one

These are intentionally early-phase diagnostics and are not assumed to survive near-full occupancy.

New setup modes:

- mode 6: Flekay line-spawn Soil cleanup
- mode 7: Flekay dual-spawner Soil cleanup

New exact leaderboard experiment:

For selected route families, repeatedly harvest at tail targets:

```text
25%, 33%, 50%, 66%, 75%, 95%, board-1
```

and restart until:

```text
num_items(Items.Bone) >= 33488928
```

This directly tests the leaderboard objective instead of assuming one maximum tail is optimal.

The v4 runner contains:

```text
main algorithm matrix:       20 * 5 * 3 = 300 simulations
setup sweep:                  3 * 8 * 3 = 72 simulations
Flekay early diagnostics:     2 * 5 * 3 = 30 simulations
leaderboard harvest sweep:    3 * 7 * 3 = 63 simulations
total:                                      465 simulations
```

As with v3, runtime correctness and performance are not verified until the in-game simulation output is collected. Reject any candidate/seed that emits `DINOSAUR BENCH INVALID`.

### Dinosaur benchmark v6 Reddit coil/strike correction

A live screenshot from the first v4 run showed the next candidate after mode 9 building several vertical lanes on the west side while an Apple remained visible on the east side.

The screenshot was taken before mode 10 emitted a result, so the active candidate was `reddit-coil-strike-safe33`.

Important distinction:

- initially ignoring an east-side Apple while building the **coil** is intended by the published Reddit algorithm
- the algorithm explicitly has four phases: coil -> strike -> pre-return -> return
- the coil phase establishes a known safe tail shape before direct east-side Apple strikes

However, direct comparison against the published Pastebin found two real translation errors in the local mode 10/11/12 implementation:

1. after consuming an Apple on the current column, local `path_progress` used the Y coordinate from before reaching that Apple; the source computes progress from the newly reached Apple position toward the newly measured next Apple
2. the local coil -> strike transition omitted the source's north-edge alignment and persistent `fixFlag1` behavior

These errors can keep the local coil phase mis-sized and leave the head in a different strike-entry geometry from the source.

v6 fixes both issues while preserving the benchmark-specific target termination.

It also prints a line before every `simulate()` call:

```text
DINOSAUR RUN START <name> mode <n> setup <name> target <percent> seed <n> bone_target <n>
```

This makes visual hangs attributable to the currently executing candidate rather than the last completed result.

Implementation:

- `1e47c5201207fac0d6cf35b23f8fd56c2483c477` — correct source-near Reddit phase transitions
- `7081dc129241652273e6793d3352db487faf3fdf` — bump runner to `dinosaur-v6` and print run-start markers

The previous v4 run should not be continued:

- v4 has the head/tail accounting bug fixed in v5
- modes 10/11/12 additionally have the Reddit translation errors fixed in v6

Re-run from the beginning and require the first line to report `BENCHMARK VERSION dinosaur-v6`.

### Current v7 runner state

| Field | Value |
| --- | --- |
| Benchmark/version | `dinosaur-v7` |
| Source commit | `ed6bc455c7705cbd501798470fd3095f65b4f823` |
| Change | Boolean-returning movement helpers are checked as booleans instead of integer return codes. |
| Validity | A full v7 matrix is still required; earlier invalid v4 previews must not be promoted. |
