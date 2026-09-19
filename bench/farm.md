# Benchmark: Farm

## Scope

| Field | Value |
| --- | --- |
| Topic | Farm |
| Purpose | Compare normal Hay/Wood/Carrot layouts, Sunflower/Power support, persistent worker lifecycles, Polyculture variants, and focus transitions. |
| Implementation | `bench_farm.py`, `bench_transition.py`, `bench_persist.py`, `bench_poly.py` |
| Runner | `bench_farm_run.py`, `bench_transition_run.py`, `bench_persist_run.py`, `bench_poly_run.py` |
| Primary metric | Elapsed simulation time to target/return; throughput where explicitly recorded. |
| Success condition | Requested resource target reached with valid crop/Power behavior. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| Cold start | `610e0e082d110c30a42d4ef900ef8a68efdb7405` | 32x32; 8 and 32 drones | Measured |
| Persistent transition | `a359f8b3fbbad02a26ebe10a9450b7296405e8c3` | Carrot → Hay → Wood → Carrot | Measured |
| Persistent workers | `af03aa2f40a43d7efeb563a54e5b8660178b7da2` | Lifecycle comparison | Suite/design recorded |
| Persistent Polyculture maximum | `d1956d30d2e1aa98da49bbccecf8c087b7b72828` | 32x32 maximum Megafarm | Suite/design recorded |
| `persist-v2` | Unknown / not recorded | sciencejiho asynchronous lanes | Pending |
| `farmx-v3` | Unknown / not recorded | Flekay seven-petal ablation | Pending/historical |
| `farmx-v4` | `b38fd2bd47c58a1211be8e59209c584f8cc96207` | Mixed + max crop focus | Measured |
| `farmx-v5` | `25aacb7719da11c5f39c1f54cd3ecf695f8c7baa` | Longer pure-crop focus + row/column modes | Pending |

## Results

### Cold-start benchmark results

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `610e0e082d110c30a42d4ef900ef8a68efdb7405` |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | 1, 2, 3 |
| Canonical status | Source state recorded |

#### Measurements and observations

Benchmark commit: `610e0e082d110c30a42d4ef900ef8a68efdb7405`

The production decision is based on the completed 32x32 benchmark with:

```text
start Power: 0
seeds: 1, 2, 3
Hay target gain:    +10,000,000
Wood target gain:   +20,000,000
Carrot target gain: +10,000,000
```

The earlier run with 1,000 starting Power is retained only as a warm-start observation. It is not used for the production-layout decision because short runs could consume the preloaded Power buffer without proving that their own Sunflower layout was sustainable.

#### Partial Megafarm: 8 drones

Average time to return after reaching/overshooting the requested target:

| Mode | Hay | Wood | Carrot |
| --- | ---: | ---: | ---: |
| legacy L | 71.48 s | 105.23 s | 121.93 s |
| pure crop columns | 33.27 s | 115.33 s | 106.81 s |
| one dumb Sunflower row | 33.44 s | 101.18 s | 96.47 s |
| one dumb Sunflower column | 33.28 s | 108.23 s | 108.36 s |
| two dumb Sunflower columns | 33.55 s | 91.64 s | 93.36 s |
| one max-petal Sunflower column | **25.09 s** | **76.02 s** | **63.11 s** |

Measured conclusion:

- one dedicated max-petal Sunflower worker wins all three target-oriented crop cases
- compared with the legacy L, time-to-target/return improves by about 65% for Hay, 28% for Wood, and 48% for Carrot
- the legacy L can still show high raw crop/sec because one `farm.run_legacy()` call overshoots targets heavily; this is not the same metric as planner responsiveness
- at this benchmark stage, one dedicated max-petal Sunflower column was the leading **candidate** for `max_drones() < world_size`; the later persistent transition benchmark superseded this as a production decision

#### Maximum Megafarm: 32 drones

Average time to return:

| Mode | Hay | Wood | Carrot |
| --- | ---: | ---: | ---: |
| legacy L | 28.82 s | 67.65 s | 61.77 s |
| pure crop columns | 14.00 s | 37.71 s | 37.07 s |
| one dumb Sunflower row | **13.98 s** | 29.81 s | 31.60 s |
| one dumb Sunflower column | 14.02 s | 31.93 s | **29.23 s** |
| two dumb Sunflower columns | 14.38 s | **29.69 s** | 29.63 s |
| one max-petal Sunflower column | 14.00 s | 33.66 s | 33.48 s |

Measured conclusion:

- the legacy L is roughly twice as slow as column ownership in all three target cases
- there is no single per-crop winner:
  - Hay narrowly favors one Sunflower row / pure crop
  - Wood favors two Sunflower columns
  - Carrot favors one Sunflower column
- two dumb Sunflower columns are selected as the robust persistent production layout
- best measured Wood time

| Crop | Gap behind best (s) |
| --- | ---: |
| Carrot | 0.40 |
| Hay | 0.40 |
- avoiding layout changes between planner focus switches is expected to be more valuable than chasing those very small isolated per-crop differences

Candidate selection after this isolated cold-start benchmark:

```text
max_drones() < world_size:
    one max-petal Sunflower column candidate

max_drones() == world_size:
    two dumb Sunflower columns candidate
```

This was not the final production decision. The persistent transition benchmark below takes precedence for production behavior.

#### Reference smoke results

The source-near juritox single-drone crop reference was intentionally kept unchanged and only smoke-tested:

| Scenario | Mode / metric | Time (s) | Ticks | Notes |
| --- | --- | ---: | ---: | --- |
| — | `Hay:` | 276.40 | — | for ~1M |
| — | `Wood:` | 494.26 | — | for the smoke target |
| — | `Carrot` | 898.16 | — | for ~1M |

These modes remain as historical/reference implementations but are no longer useful as regular default-suite candidates.


-----

### Persistent transition benchmark

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `a359f8b3fbbad02a26ebe10a9450b7296405e8c3` |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Source state recorded |

#### Measurements and observations

Benchmark commit: `a359f8b3fbbad02a26ebe10a9450b7296405e8c3`

Workload:

```text
Carrot -> Hay -> Wood -> Carrot
```

No `clear()` and no Power reset occurred between phases.

Average total simulated runtime:

| Profile | legacy-l | adaptive-production | Relative result |
| --- | ---: | ---: | ---: |
| partial Megafarm, 8 drones | 358.48 s | 361.39 s | adaptive ~0.8% slower |
| max Megafarm, 32 drones | 128.63 s | 63.88 s | adaptive ~50.3% faster |

Interpretation:

- at 8 drones, the production-shaped max-petal candidate was effectively tied with the legacy L in the persistent workload
- at 32 drones, the adaptive two-Sunflower-column layout was decisively faster
- the 8-drone difference was small enough that it does not justify preserving the legacy L as production architecture

Current production therefore uses:

```text
max_drones() < world_size
    one max-petal Sunflower column
    synchronous crop chunks

max_drones() == world_size
    two dumb Sunflower columns
    synchronous column passes
```

The legacy L is retained only for benchmark reproduction.


-----

### FarmX v4 measured results

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `b38fd2bd47c58a1211be8e59209c584f8cc96207` |
| Benchmark/version | `farmx-v4` |
| Requested speedup | 10000 |
| Seeds | See recorded setup |
| Canonical status | Source state recorded |

#### Measurements and observations

Measured `farmx-v4` at benchmark source commit `b38fd2bd47c58a1211be8e59209c584f8cc96207`, requested simulation speedup 10000.

Mixed sustained finals:

| Scenario | Mode / metric | Time (s) | Ticks | Notes |
| --- | --- | ---: | ---: | --- |
| partial Megafarm level 3 | `sync-selected` | 224.09 | — | — |
| partial Megafarm level 3 | `current-two-sun-pairs` | 94.93 | — | — |
| partial Megafarm level 3 | `poly-two-sun-pairs` | 155.71 | — | — |
| max Megafarm | `sync-selected` | 46.98 | — | — |
| max Megafarm | `current-two-sun-stride` | 38.83 | — | — |
| max Megafarm | `poly-two-sun-chunks` | 53.70 | — | — |

Pure max-Megafarm focus finals:

| Scenario | Mode / metric | Time (s) | Ticks | Notes |
| --- | --- | ---: | ---: | --- |
| max-carrot | `sync-selected` | 36.06 | — | — |
| max-carrot | `current-two-sun-chunks` | 29.62 | — | — |
| max-carrot | `poly-two-sun-stride` | 50.82 | — | — |
| max-grass | `sync-selected` | 17.89 | — | — |
| max-grass | `current-one-max-pairs` | 23.26 | — | — |
| max-grass | `poly-two-sun-chunks` | 50.31 | — | — |
| max-wood | `sync-selected` | 39.32 | — | — |
| max-wood | `current-two-sun-chunks` | 34.28 | — | — |
| max-wood | `poly-two-sun-chunks` | 49.50 | — | — |

Derived observations:

- partial mixed: current persistent winner is about 57.6% faster than sync-selected; Poly is about 64.0% slower than the current winner
- max mixed: current winner is about 17.3% faster than sync-selected
- max Carrot: current-two-sun-chunks is about 17.9% faster than sync-selected
- max Wood: current-two-sun-chunks is about 12.8% faster than sync-selected
- max Grass is different: sync-selected wins the three-seed average, while current-one-max-pairs is more stable

| Max-Grass mode | Seed range (s) | Observation |
| --- | ---: | --- |
| `sync-selected` | 14.77–23.85 | Fastest three-seed average, high spread |
| `current-one-max-pairs` | 22.46–24.34 | Slower average, much tighter spread |
- pure-crop architecture is therefore crop-specific; do not choose one architecture from the mixed transition benchmark alone
- the Flekay-inspired one-column seven-petal modes are not competitive at the measured horizons and should not remain in the default screen
- Poly is not competitive in any of the three pure-focus scenarios and can be removed from future pure-crop screens while remaining in the mixed research suite

Next missing persistent layouts:

- one-row-dumb
- one-col-dumb

Both already exist in `bench_persist.py` and were strong in the older broad `bench_farm` baseline, but `bench_poly` did not expose them. They must be compared before finalizing per-crop production layouts.

Because max-Grass still has high seed variance at the 10M target, the next pure-focus validation should use a longer sustained target rather than interpreting the v4 Grass average as final.

-----

## Interpretation

### Production selection after cold-start benchmark

Benchmark commit: `610e0e082d110c30a42d4ef900ef8a68efdb7405`

The isolated cold-start benchmark selected these non-L candidates:

```text
max_drones() < world_size
    one dedicated max-petal Sunflower column

max_drones() == world_size
    two simple Sunflower columns
```

The legacy L remains available only as a historical benchmark implementation.

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out the source commit listed for the result group. |
| 2 | Run the matching Farm benchmark runner. |
| 3 | Preserve complete output and update this file without changing historical values. |

## Notes

### Persistent worker benchmark

Benchmark commit: `af03aa2f40a43d7efeb563a54e5b8660178b7da2`

Files:

- `bench_persist.py`
- `bench_persist_run.py`

#### Motivation

The synchronous normal-farm routes still have two avoidable costs:

1. every pass repeatedly pays successful `spawn_drone()` cost
2. every pass has a barrier because the caller waits for every worker before the next pass starts

A worker that finishes early therefore becomes idle while slower workers finish, and all worker drones disappear before the next normal-farm pass.

#### Persistent-worker reference research

##### MateusMarochi: persistent two-column workers

Reference:

- `external/mateusmarochi-the-farmer-was-replaced-codes/source/polyculture_farm_paralel.py`

Its worker owns a fixed pair of columns and loops forever. The final two columns are Sunflowers. There is no per-round respawn and no global column barrier.

This is directly relevant to the current normal-farm design.

##### MateusMarochi: main drone also works

Upstream references reviewed:

- `pumpkin_farm.py`
- `cactus_farm.py`

These implementations spawn only the additional workers and let the caller execute worker 0 itself.

That is important at `max_drones() == world_size`: reserving the caller as a pure scheduler wastes one useful worker slot.

##### nql1314: persistent region pool

Reference:

- `external/nql1314-the-farmer-was-replaced-ai-code/`

The repository correctly identifies repeated `spawn_drone()` plus barrier waiting as overhead and uses long-lived workers over stable regions.

Its original dynamic priority/companion communication relied on the historical shared-`wait_for()` bug and is invalid in the current runtime.

The valid reusable idea is therefore:

```text
spawn persistent worker once
assign stable region/columns
derive current focus from globally visible game state
keep working without a round barrier
```

#### Layouts under test

Persistent execution can change which Sunflower geometry wins, so all surviving non-L layout families are re-tested:

```text
pure-crop
one-row-dumb
one-col-dumb
two-col-dumb
one-col-max
```

The synchronous currently selected production route is retained as the baseline:

```text
sync-selected
```

#### Worker architectures under test

Each layout independently screens:

```text
main-stride
main-chunks
main-pairs
scheduler-chunks
```

Meanings:

- `main-stride`: caller is worker 0; workers repeatedly service columns by stride
- `main-chunks`: caller is worker 0; workers own contiguous chunks
- `main-pairs`: persistent pair-of-columns pattern inspired by Mateus
- `scheduler-chunks`: caller only schedules; all farm work is done by spawned drones

The architecture screen is intentionally performed **per layout**. A worker geometry that wins for two Sunflower columns is not assumed to also win for one row or max-petal.

#### Benchmark stages

For each profile:

1. each layout × each worker architecture runs a short seed-1 screen
2. the best architecture for that layout is retained
3. every layout winner runs the full workload over seeds 1, 2, and 3
4. `sync-selected` runs alongside them

Profiles:

```text
partial-megafarm-level-3
max-megafarm
```

Full persistent workload:

```text
Carrot +5M
-> Hay +5M
-> Wood +10M
-> Carrot +5M
```

No shared Python memory is used. Focus changes are derived from globally visible item counts.

Run:

```text
bench_persist_run.py
```

Do not replace the synchronous full-Megafarm production route until this benchmark completes and the results are documented with the benchmark commit above.

### Persistent Polyculture maximum benchmark

Benchmark code state: `d1956d30d2e1aa98da49bbccecf8c087b7b72828`.

Files:

- `bench_poly.py`
- `bench_poly_run.py`

This benchmark extends the earlier persistent-worker work instead of replacing its historical results.

#### Why this benchmark exists

The current production farm still pays repeated spawn/barrier costs because `farm.run()` creates a new worker set for each planner pass. Successful `spawn_drone()` is a physical action, so the cost is especially relevant for short planner windows.

Long-lived workers are not enough by themselves. The current same-column companion-following strategy also leaves Polyculture throughput on the table because independent drones cannot share a companion request map.

The new candidate therefore combines three ideas from the mirrored/community references:

1. persistent workers with stable column ownership
2. a permanent all-Soil checkerboard of Bush companion tiles
3. rerolling Grass/Tree/Carrot until `get_companion()` requests Bush on an even-parity companion tile

The checkerboard has two useful properties:

- every accepted even-parity coordinate is a known Bush companion
- odd-parity Tree positions are never orthogonally adjacent

No Python memory is shared between drones. Workers coordinate only through global item counts and the shared farm state.

#### Candidate matrix

The benchmark screens:

```text
sync-selected

current one-max sunflower:
  stride
  chunks
  pairs

current two dumb sunflower columns:
  stride
  chunks
  pairs

polyculture checkerboard + one max-petal sunflower column:
  stride
  chunks
  pairs

polyculture checkerboard + two dumb sunflower columns:
  stride
  chunks
  pairs
```

The "current" persistent candidates reuse the existing crop logic from `bench_persist.py`. The "poly" candidates use a static Bush checkerboard plus rerolling and keep the companion field across Carrot -> Hay -> Wood -> Carrot transitions.

#### Setup cost is part of the result

Every simulation starts from a cold normal-farm state with zero Power. Timing starts before `clear()`, so field reset, layout construction, temporary setup workers, persistent worker creation, Sunflower construction, and production all count.

The poly candidates additionally print:

```text
FARMX POLY PREP
FARMX POLY LAUNCH
```

These expose the explicit all-Soil/Bush preparation and persistent-worker launch portions, but total `simulate()` runtime remains the primary comparison because worker startup and useful production can overlap.

#### Workload horizons

The runner deliberately uses multiple horizons so setup-heavy designs are not selected only from a long steady-state benchmark.

```text
cold-short:
  Carrot +100k
  Hay    +100k
  Wood   +200k
  Carrot +100k

cold-medium:
  Carrot +1M
  Hay    +1M
  Wood   +2M
  Carrot +1M

sustained:
  Carrot +5M
  Hay    +5M
  Wood   +10M
  Carrot +5M
```

For each partial/max Megafarm profile:

1. all modes run the cold-short screen with seed 1
2. all modes run the cold-medium screen with seed 1
3. the fastest current-persistent mode and fastest rerolling mode are selected from the medium screen
4. `sync-selected`, the current finalist, and the rerolling finalist run the sustained workload over seeds 1, 2, and 3

This keeps the suite broad enough to find setup break-even behavior without running every losing architecture through the expensive three-seed sustained matrix.

#### References carried into the benchmark

- `external/msmith93-thefarmerwasreplaced/source/multidrone.py`: static persistent worker lifetime
- `external/msmith93-thefarmerwasreplaced/source/multidrone/carrot.py`: persistent Carrot workers with companion rerolling
- `external/msmith93-thefarmerwasreplaced/source/multidrone/wood.py`: persistent Tree workers with companion rerolling
- `external/msmith93-thefarmerwasreplaced/source/multi_drone_hay_leaderboard.py`: long-lived Hay workers and static companion geometry
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/polyculture_farm_paralel.py`: persistent fixed-column/pair workers plus dedicated Sunflower area
- `external/nql1314-the-farmer-was-replaced-ai-code/source/resource_farm_mega.py`: persistent region-pool concept only; its historical shared-memory coordination is not valid in the current runtime

Community rerolling references remain supporting hypotheses rather than benchmark proof. Production must not switch to the new layout until the benchmark completes.

#### Run

```text
bench_poly_run.py
```

Paste the complete `FARMX ...` output back into the research session. Record measured conclusions only against benchmark commit `d1956d30d2e1aa98da49bbccecf8c087b7b72828`.

### sciencejiho asynchronous-lane benchmark

The persistent-worker suite now includes an architecture-only port of:

- `external/sciencejiho-tfwr-solutions/source/strategy_polyculture.py`
- `external/sciencejiho-tfwr-solutions/source/drone_control.py`

Benchmark architecture name:

```text
science-async-lanes
```

The candidate preserves the source architecture rather than its crop policy:

1. the controller owns persistent lane scheduler state
2. each child receives one copied column job
3. child jobs terminate after one column
4. the controller polls `has_finished()`, merges completion, and immediately relaunches idle lanes
5. one lane stays on the controller and performs useful column work
6. no mutable Python object is shared between drones

Crop servicing, Sunflower layouts, targets, profiles, and inventory conditions remain the same as the other `bench_persist.py` modes. This isolates the worker-lifecycle question:

> Is asynchronous one-column recycling fast enough to beat long-lived stride/chunk/pair workers once repeated spawn cost and controller polling are included?

The benchmark deliberately includes both:

- partial Megafarm
- maximum Megafarm

At full 32x32 Megafarm, a lane may own only one column, so the async implementation repeatedly respawns a worker for that same column. That is expected source-like behavior and must not be optimized away before measurement.

Run:

```text
bench_persist_run.py
```

Benchmark version:

```text
persist-v2
```

No performance conclusion is recorded until an in-game/simulation run is supplied.

### Flekay seven-petal Sunflower ablation

Farm-only follow-up after reviewing `Flekay/The-Farmer-Was-Replaced`.

The next `bench_poly_run.py` suite is `farmx-v3`.

New current-farm candidates:

```text
current-one-seven-stride
current-one-seven-chunks
current-one-seven-pairs
```

These keep the existing persistent crop architectures unchanged and replace the dedicated Sunflower worker with a source-near equal-petal strategy:

1. dedicate one full 32-tile column to Sunflowers
2. reroll each Sunflower until it has exactly 7 petals
3. rejected rolls are destroyed with `harvest()` and immediately replanted
4. only the accepted 7-petal roll is watered
5. during steady state, mature Sunflowers are harvested and immediately rerolled back to 7 petals

Because all 32 dedicated Sunflowers are fixed to the same petal count, every mature Sunflower is tied for the global maximum and there are more than the required 10 Sunflowers for the max-petal bonus.

Why this belongs in `farmx`:

- initial reroll setup is intentionally expensive
- steady-state service is much simpler than maintaining a max-petal list
- `cold-short`, `cold-medium`, and `sustained` directly expose the amortization crossover
- stride/chunks/pairs isolates whether worker architecture changes the result

Relevant commits:

- `1eadbaa5cf42db6dfdd6e34b0dfad7c8e3422f08` initial seven-petal worker
- `63638f712ba989786ee072b4e4b97edc225683cf` FarmX modes
- `e4e838c1829afe241b2e9c602c7497c3df0d73fb` `farmx-v3` runner
- `25ec285ed0736a17db73e7d94a10d265ec7a235f` source-near reroll correction: do not water rejected rolls

Do not change production `farm.py` from this benchmark alone. First compare the seven-petal modes against the existing one-max and two-dumb Sunflower layouts in both partial and max Megafarm profiles.

### FarmX max-crop focus modes

`farmx-v4` adds three pure max-Megafarm throughput scenarios in addition to the mixed Carrot -> Hay -> Wood -> Carrot sequence:

```text
max-carrot
max-grass
max-wood
```

Targets are aligned with the broad `bench_farm` max-Megafarm baseline:

```text
max-carrot 10M total Carrot gain
max-grass  10M Hay gain
max-wood   20M Wood gain
```

Carrot is internally split into the two existing Carrot phases, so `BENCH_CARROT_GAIN=5M` produces 10M total Carrot.

Each max-crop scenario:

1. runs only with the fully unlocked/max-Megafarm profile
2. screens all FarmX modes with seed 1
3. selects the best current mode and best poly mode for that crop
4. compares `sync-selected`, best current, and best poly across seeds 1/2/3

This isolates pure crop throughput from transition performance and allows the winning architecture/layout to differ for Grass, Wood, and Carrot.

Relevant commits:

- `ab4f1fb8e47edee8e567632bc7aacea7e0f8e887` scenario labels in `bench_poly.py`
- `b38fd2bd47c58a1211be8e59209c584f8cc96207` `farmx-v4` max-crop focus runner

### Migration note

| Kind | Statement | Evidence |
| --- | --- | --- |
| Historical | The old `FARMX unversioned benchmark results` section was not migrated as canonical data. | It had no exact source commit. |
| Action | Rerun any still-useful FARMX comparison from a committed code state. | Repository provenance rule. |

-----
