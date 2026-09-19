# Normal Farm Design and Benchmark Notes

This document is the canonical reference for normal Hay/Wood/Carrot farming, Sunflower/Power support, multi-drone layout decisions, and the benchmark suite.

Read this file before changing:

- `farm.py`
- normal-farm handling in `production.py`
- `bench_farm.py`
- `bench_farm_run.py`

## Legacy layout and why it was replaced

The legacy production design reserved:

- a permanent Sunflower L on the left/top edge
- a permanent Carrot support L directly inside it
- the remaining area for the selected focus crop

That layout predates the current 32x32 / 32-drone endgame state.

At 32x32, a one-tile Sunflower L consumes:

```text
32 + 32 - 1 = 63 tiles
```

or about 6.15% of the field.

More importantly, it cuts across the natural row/column ownership model for Megafarm workers and requires:

- special protected-position checks
- a global Sunflower petal cache
- explicit Sunflower rebuilds after full-field special jobs
- dedicated movement to maintain the L

The benchmark exists to determine whether that complexity still pays for itself.

The cold-start benchmark supported replacing this layout; it remains only as a reproducible legacy benchmark path.

## Current mechanics relevant to the benchmark

Authoritative documentation:

- https://thefarmerwasreplaced.wiki.gg/wiki/Sunflowers
- https://thefarmerwasreplaced.wiki.gg/wiki/Polyculture
- https://thefarmerwasreplaced.wiki.gg/wiki/Megafarm
- https://thefarmerwasreplaced.wiki.gg/wiki/Trees
- https://thefarmerwasreplaced.wiki.gg/wiki/Simulation
- https://thefarmerwasreplaced.wiki.gg/wiki/Leaderboard

Important mechanics:

- normal movement wraps at farm edges
- all drones count toward `max_drones()`; there is no special main drone
- drones do not share Python/global memory
- Power doubles execution speed while available
- Power is consumed by actions over time
- Sunflowers have 7..15 petals
- if at least 10 Sunflowers exist, harvesting a current maximum-petal Sunflower gives the large Power multiplier
- harvesting a lower-petal Sunflower can forfeit that ordered-harvest bonus opportunity
- Grass, Bush, Tree, and Carrot participate in Polyculture
- Trees grow slower for each orthogonally adjacent Tree
- Tree/Bush checkerboards therefore remain a useful Wood baseline

## Two worker regimes

The benchmark intentionally treats these as separate cases.

### max_drones() == world_size

On a fully upgraded 32x32 Megafarm, one worker can own one complete column.

A natural traversal is:

```text
one worker -> one column
move North only
wrap from y=31 to y=0
```

This avoids:

- vertical return movement
- repeated cross-field repositioning
- overlapping worker ownership

### max_drones() < world_size

When fewer workers are available, each worker owns a contiguous chunk of columns.

The benchmark candidate traverses each assigned column with North-only wrapping and bounces horizontally between neighboring columns.

The same production layout does not have to win in both regimes.

## Sunflower placement candidates

The suite currently compares the following placement ideas.

### Current L

Production implementation exactly as it exists now.

This is the control. Do not modify this mode when experimenting.

### No Sunflowers

All tiles are used for the focus crop.

This is intentionally unsustainable once the initial Power buffer is exhausted, but it gives an upper-bound/control for the field area cost of Power support.

### One Sunflower row

The top row is Sunflowers and every worker encounters one Sunflower tile during its own column loop.

On 32x32 this uses 32 Sunflowers and 31 focus tiles per column.

This tests the hypothesis that Sunflowers should be ordinary tiles in the normal traversal instead of a dedicated geometric structure.

### One Sunflower column

One complete column is reserved for Sunflowers.

With 32 workers this becomes one dedicated Power worker plus 31 focus-crop workers.

This keeps max-petal ordering local to one worker if desired.

### Two Sunflower columns

Two full columns are reserved.

This mirrors the broad idea found in the local MateusMarochi parallel polyculture reference, which reserves dedicated Sunflower columns.

It trades more crop area for more Power production.

### One max-petal Sunflower column

One dedicated worker owns all 32 Sunflowers and tracks their petal counts.

Because every Sunflower is owned by the same worker:

- no shared memory is required
- the worker can recompute the maximum locally
- lower-petal Sunflowers are not harvested while a higher-petal Sunflower exists

This is our candidate, not a verbatim external reference.

## Reference-integrity rule

Past optimization work showed that apparently obvious improvements can benchmark worse.

Therefore:

> Never edit a source-near reference mode to include our optimizations.

If a reference looks inefficient, keep it and add a second candidate.

Examples in this suite:

### MateusMarochi Sunflower reference

Local unchanged upstream snapshot:

- `external/mateusmarochi-the-farmer-was-replaced-codes/source/sunflower_farm.py`
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/plantacoes.py`

The benchmark mode:

```text
mateus-reference-fullfield-dumb
```

preserves the important source behavior:

- one worker per column
- simple harvest/replant
- explicit move back to row 0 after each North scan
- no max-petal ordering

The benchmark adapts only termination to a fixed Power target.

The separate mode:

```text
fullfield-dumb-north-only
```

tests our proposed wrap optimization.

### juritox crop references

Local unchanged upstream snapshot:

- `external/juritox-the-farmer-was-replaced/source/scripts/hay_harvest.py`
- `external/juritox-the-farmer-was-replaced/source/scripts/wood_harvest.py`
- `external/juritox-the-farmer-was-replaced/source/scripts/carrot_harvest.py`

The benchmark keeps their single-drone full-field traversal and crop logic source-near.

It is intentionally not converted to 32 drones.

### juritox Power reference

Local source:

- `external/juritox-the-farmer-was-replaced/source/scripts/power_harvest.py`

The mode:

```text
juritox-reference-max-petal
```

retains:

- repeated full-field planting/scanning
- ordered petal harvesting
- the 15-petal fast path
- the source-style list/remove/max algorithm

It is intentionally not replaced by our petal cache.

## Community research

Provenance:

- `external/reddit-normal-farm-sunflower-research/`

Useful competing observations:

- one community experiment reported that a simple 32-drone Sunflower harvest/replant farm beat that author's ordered-petal implementation substantially
- another approach uses synchronized 4x8 chunks for ordered petal harvesting
- recent Megafarm discussions repeatedly recommend treating one drone or one drone per row/column as distinct optimization regimes
- Polyculture leaderboard discussion describes rerolling as a high-end strategy rather than simple cross-field companion servicing

These are benchmark ideas, not mechanics guarantees.

The benchmark therefore contains both dumb and ordered Sunflower strategies.

## Crop modes

`bench_farm.py` currently defines:

| Mode | Purpose |
| --- | --- |
| `current-l-production` | legacy L production baseline |
| `current-l-no-polyculture` | isolates current L without Polyculture benefit/overhead |
| `columns-pure-current-crop` | no Sunflowers; current crop logic in column ownership |
| `columns-one-sunflower-row-dumb` | 32 integrated Sunflower tiles spread across columns |
| `columns-one-sunflower-column-dumb` | one dedicated/simple Sunflower column |
| `columns-two-sunflower-columns-dumb` | two dedicated/simple Sunflower columns |
| `columns-one-sunflower-column-max-petal` | one ordered/max-petal Power worker |
| `columns-one-sunflower-column-simple-crop` | simple crop hot path + one dumb Sunflower column |
| `juritox-reference-single-drone` | source-near external crop reference |

The simple Wood candidate uses Tree/Bush checkerboard.

The current-crop candidates reuse `farm.farm_resource()`, including the current crop logic and Polyculture attempt, but constrain companion mutation to the current column. This avoids cross-worker writes without pretending that the existing companion algorithm is valid across independent drone memories.

## Power modes

The dedicated Power benchmark compares:

| Mode | Purpose |
| --- | --- |
| `current-l-power` | current production Power behavior |
| `mateus-reference-fullfield-dumb` | source-near 32-column simple reference |
| `fullfield-dumb-north-only` | our wrap-only adaptation |
| `juritox-reference-max-petal` | source-near ordered-petal reference |

The initial target was +100,000 Power. The current suite uses +20,000 Power for each of three seeds; this is still large enough to amortize setup while keeping all source-near reference modes practical.

## Crop benchmark targets

The first screening run used +20M Hay / +100M Wood / +20M Carrot. That was intentionally conservative, but the 8-drone Hay results already exposed two order-of-magnitude losers.

The current finalist matrix therefore uses:

```text
Hay:    +10,000,000
Wood:   +20,000,000
Carrot: +10,000,000
```

Source-near crop references use a smaller one-seed smoke target:

```text
Hay:    +1,000,000
Wood:   +2,000,000
Carrot: +1,000,000
```

This keeps reference implementations intact without allowing an intentionally old/single-drone implementation to dominate suite runtime.

All runs use:

```text
world size: 32
seeds: 1, 2, 3
speedup: 64
```

## Power starting condition

Crop simulations now deliberately start with:

```text
0 Power
```

The original screening started with 1,000 Power. The first Hay results showed that this biased short runs: even the no-Sunflower control finished before exhausting the preloaded buffer, so it effectively received the execution-speed benefit without having to produce Power itself.

Cold start makes the layout responsible for its own acceleration:

- no-Sunflower is a true unpowered control
- integrated Sunflower layouts must earn any speed advantage
- a layout that can sustain Power will show that benefit in total crop runtime

The benchmark output includes:

```text
start-power
end-power
power-delta
```

for every simulation.

With the current cold-start profile, `start-power` should be 0. `end-power` alone is not a complete Power-production metric because generated Power may be consumed immediately while accelerating the run; crop throughput remains the primary metric.

## Partial vs maximum Megafarm profile

The runner executes every crop case twice:

1. `partial-megafarm-level-3`
2. `max-megafarm`

The simulation prints the actual:

```text
max_drones()
```

inside each `FARM RESULT`.

This is deliberate. If the game's Megafarm-level mapping changes, we do not want a label such as "16 drones" to silently become false.

The maximum profile uses fully upgraded `Unlocks` and is expected to produce 32 drones on the 32x32 field.

## Metrics

Because every mode in one crop case targets the same resource gain, primary comparison is:

```text
lower simulate() runtime is better
```

The simulated worker additionally prints:

```text
elapsed
gain
gain / elapsed
power-delta
max_drones
```

The actual gain may overshoot slightly because parallel workers finish their current local traversal before terminating.

For production selection use:

1. runtime / resource throughput
2. Power sustainability
3. correctness
4. variance across seeds

Do not select a mode from source-code elegance.

## Running the suite

Execute:

```text
bench_farm_run.py
```

The runner performs all crop profiles. The dedicated Power suite is optional and disabled by default.

After:

```text
FARM BENCH SUITE DONE
```

it automatically calls:

```python
main.main()
```

so normal automation resumes without manual intervention.

## Next research stage: Polyculture

The first suite primarily answers layout and Power-support questions.

Do not conflate that with the final Polyculture algorithm.

The current high-end community idea worth benchmarking separately is rerolling:

1. preplant a known companion crop
2. repeatedly replant/reroll the focus crop
3. inspect `get_companion()`
4. accept only a crop whose requested companion matches the already-present companion layout

This avoids cross-drone companion writes and may preserve the very large Polyculture multiplier.

It should become a new benchmark mode after the first layout suite establishes which Sunflower placement and worker geometry are worth keeping.

Do not silently add rerolling to an existing mode.


## First screening prune

Benchmark commit: `c2518979299857284b44fdd2dc87ce00e1f5e05c`

The first completed 32x32 / 8-drone Hay screening produced:

```text
current-l-production                         avg 44.56 s
current-l-no-polyculture                     avg 298.71 s
columns-pure-current-crop                    avg 29.82 s
columns-one-sunflower-row-dumb               avg 29.64 s
columns-one-sunflower-column-dumb            avg 30.31 s
columns-two-sunflower-columns-dumb           avg 30.53 s
columns-one-sunflower-column-max-petal       avg 31.63 s
columns-one-sunflower-column-simple-crop     avg 436.96 s
```

Therefore:

- `current-l-no-polyculture` is removed from the expensive finalist matrix
- `columns-one-sunflower-column-simple-crop` is removed from the expensive finalist matrix
- both implementations remain in `bench_farm.py` for reproducibility
- source-near external references remain unchanged and run as smaller smoke tests

This is intentional benchmark pruning, not deletion of inconvenient results.


## Polyculture soil research

This question is intentionally deferred to the dedicated Polyculture benchmark rather than mixed into the first Sunflower/layout suite.

### Current mechanics

Current wiki documentation supports an all-Soil candidate:

- Grass can be explicitly planted on Soil.
- Grass grows automatically on Grassland.
- Trees, like Bushes, can be planted on either Grassland or Soil.
- Carrots require Soil.
- Polyculture companions are Grass, Bush, Tree, or Carrot; companion selection is per individual plant and independent of a fixed crop type layout.

Relevant sources:

- https://thefarmerwasreplaced.wiki.gg/wiki/Grass
- https://thefarmerwasreplaced.wiki.gg/wiki/Tree
- https://thefarmerwasreplaced.wiki.gg/wiki/Polyculture
- https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips

The important trade-off is therefore measurable rather than purely mechanical:

- Grassland Grass avoids an explicit `plant(Entities.Grass)` after each harvest because Grass regrows automatically.
- All-Soil avoids repeated `till()` transitions when switching among Grass/Carrot/Tree/Bush-heavy production layouts.
- Both `plant()` and `till()` are expensive physical actions, so short focus windows may favor avoiding ground conversion while long pure-Hay windows may favor automatic Grass regrowth.

### Local external references

The MateusMarochi Polyculture reference is deliberately **not** all-Soil.

Files:

- `external/mateusmarochi-the-farmer-was-replaced-codes/source/polyculture_farm.py`
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/polyculture_farm_paralel.py`
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/plantacoes.py`

Its planting helpers force:

```text
Grass  -> Grassland
Tree   -> Grassland
Bush   -> Grassland
Carrot -> Soil
Sunflower -> Soil
```

Preserve this behavior in any source-near benchmark mode. Do not silently convert it to all-Soil.

Its Polyculture algorithm uses a pending-request list:

1. plant a probe crop
2. call `get_companion()`
3. store requested coordinate/type
4. service the request when traversal reaches that coordinate

The parallel variant assigns pairs of columns and reserves the final two columns for Sunflowers.

This is useful as a classic companion-request baseline, but its mutable global request list cannot be assumed to synchronize across drones under current independent-drone memory semantics.

### Community rerolling strategy

Recent Reddit discussion describes a different high-end approach for Hay and suggests adapting it to the other base crops:

1. preplant the field with one chosen companion crop
2. give workers stable positions/regions with minimal overlap
3. repeatedly plant/reroll the target crop
4. call `get_companion()`
5. accept the target only when its requested companion matches the already-present companion crop

References:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1v6mnwx/i_need_help_to_optimize/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1ofhmi8/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1oe5ykd/so_is_polyculture_a_thing/

This avoids cross-drone writes to requested companion coordinates, at the cost of repeated reroll actions.

The community also points out that companion harvesting order matters: removing a companion before harvesting the plant that depends on it loses that plant's bonus. That is another reason to benchmark static companion layouts/rerolling separately from request-following algorithms.

### Planned Polyculture benchmark matrix

After the current normal-farm/Sunflower suite selects a worker geometry, benchmark at least:

```text
A. classic Grassland companion/request strategy
B. all-Soil companion/request strategy
C. all-Soil static companion + rerolling
D. no-Polyculture control
```

Run both steady-state and transition workloads.

Steady-state:

```text
Hay
Wood
Carrot
```

Transition workload:

```text
Carrot -> Hay -> Wood -> Carrot
```

The transition workload is essential because an isolated Hay benchmark cannot measure the value of avoiding Soil/Grassland conversions.

Keep source-near external modes unchanged. Add all-Soil and rerolling as separate modes.




## Cold-start benchmark results

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

### Partial Megafarm: 8 drones

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

### Maximum Megafarm: 32 drones

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
- two dumb Sunflower columns are selected as the robust persistent production layout:
  - best measured Wood time
  - only about 0.40 s behind the best Carrot time
  - only about 0.40 s behind the best Hay time
- avoiding layout changes between planner focus switches is expected to be more valuable than chasing those very small isolated per-crop differences

Candidate selection after this isolated cold-start benchmark:

```text
max_drones() < world_size:
    one max-petal Sunflower column candidate

max_drones() == world_size:
    two dumb Sunflower columns candidate
```

This was not the final production decision. The persistent transition benchmark below takes precedence for production behavior.

### Reference smoke results

The source-near juritox single-drone crop reference was intentionally kept unchanged and only smoke-tested:

```text
Hay:    276.40 s for ~1M
Wood:   494.26 s for the smoke target
Carrot: 898.16 s for ~1M
```

These modes remain as historical/reference implementations but are no longer useful as regular default-suite candidates.


## Production selection after cold-start benchmark

Benchmark commit: `610e0e082d110c30a42d4ef900ef8a68efdb7405`

The isolated cold-start benchmark selected these non-L candidates:

```text
max_drones() < world_size
    one dedicated max-petal Sunflower column

max_drones() == world_size
    two simple Sunflower columns
```

The legacy L remains available only as a historical benchmark implementation.

## Persistent transition benchmark

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

## Persistent worker benchmark

Benchmark commit: `af03aa2f40a43d7efeb563a54e5b8660178b7da2`

Files:

- `bench_persist.py`
- `bench_persist_run.py`

### Motivation

The synchronous normal-farm routes still have two avoidable costs:

1. every pass repeatedly pays successful `spawn_drone()` cost
2. every pass has a barrier because the caller waits for every worker before the next pass starts

A worker that finishes early therefore becomes idle while slower workers finish, and all worker drones disappear before the next normal-farm pass.

### Persistent-worker reference research

#### MateusMarochi: persistent two-column workers

Reference:

- `external/mateusmarochi-the-farmer-was-replaced-codes/source/polyculture_farm_paralel.py`

Its worker owns a fixed pair of columns and loops forever. The final two columns are Sunflowers. There is no per-round respawn and no global column barrier.

This is directly relevant to the current normal-farm design.

#### MateusMarochi: main drone also works

Upstream references reviewed:

- `pumpkin_farm.py`
- `cactus_farm.py`

These implementations spawn only the additional workers and let the caller execute worker 0 itself.

That is important at `max_drones() == world_size`: reserving the caller as a pure scheduler wastes one useful worker slot.

#### nql1314: persistent region pool

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

### Layouts under test

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

### Worker architectures under test

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

### Benchmark stages

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


## Persistent Polyculture maximum benchmark

Benchmark code state: `d1956d30d2e1aa98da49bbccecf8c087b7b72828`.

Files:

- `bench_poly.py`
- `bench_poly_run.py`

This benchmark extends the earlier persistent-worker work instead of replacing its historical results.

### Why this benchmark exists

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

### Candidate matrix

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

### Setup cost is part of the result

Every simulation starts from a cold normal-farm state with zero Power. Timing starts before `clear()`, so field reset, layout construction, temporary setup workers, persistent worker creation, Sunflower construction, and production all count.

The poly candidates additionally print:

```text
FARMX POLY PREP
FARMX POLY LAUNCH
```

These expose the explicit all-Soil/Bush preparation and persistent-worker launch portions, but total `simulate()` runtime remains the primary comparison because worker startup and useful production can overlap.

### Workload horizons

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

### References carried into the benchmark

- `external/msmith93-thefarmerwasreplaced/source/multidrone.py`: static persistent worker lifetime
- `external/msmith93-thefarmerwasreplaced/source/multidrone/carrot.py`: persistent Carrot workers with companion rerolling
- `external/msmith93-thefarmerwasreplaced/source/multidrone/wood.py`: persistent Tree workers with companion rerolling
- `external/msmith93-thefarmerwasreplaced/source/multi_drone_hay_leaderboard.py`: long-lived Hay workers and static companion geometry
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/polyculture_farm_paralel.py`: persistent fixed-column/pair workers plus dedicated Sunflower area
- `external/nql1314-the-farmer-was-replaced-ai-code/source/resource_farm_mega.py`: persistent region-pool concept only; its historical shared-memory coordination is not valid in the current runtime

Community rerolling references remain supporting hypotheses rather than benchmark proof. Production must not switch to the new layout until the benchmark completes.

### Run

```text
bench_poly_run.py
```

Paste the complete `FARMX ...` output back into the research session. Record measured conclusions only against benchmark commit `d1956d30d2e1aa98da49bbccecf8c087b7b72828`.


## FARMX unversioned benchmark results

Benchmark version: `unversioned-legacy`

Benchmark commit: `d1956d30d2e1aa98da49bbccecf8c087b7b72828`

The supplied run completed both profiles and all three sustained seeds.

Sustained summaries:

```text
partial Megafarm / 8 drones:
  sync-selected          avg 224.17
  current-two-sun-pairs  avg  94.96
  poly-two-sun-pairs     avg 156.49

max Megafarm / 32 drones:
  sync-selected           avg 47.16
  current-two-sun-stride  avg 38.18
  poly-two-sun-stride     avg 52.39
```

Measured conclusions for this benchmark state:

- persistent current crop logic is much faster than synchronous production in both profiles
- at 8 drones, `current-two-sun-pairs` reduced average sustained runtime by about 57.6% versus `sync-selected`
- at 32 drones, `current-two-sun-stride` reduced average sustained runtime by about 19.0% versus `sync-selected`
- the static all-Soil Bush-checkerboard/rerolling candidate did not beat the best persistent current-crop candidate
- at 32 drones the rerolling finalist was slower than even synchronous production
- do not promote a final Farm layout from this run because Sunflower placement is now being challenged independently

This result set predates the benchmark-version header rule. Future runs must include `BENCHMARK VERSION ...` as their first output line.

## sciencejiho asynchronous-lane benchmark

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
