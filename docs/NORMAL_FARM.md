# Normal Farm Design and Benchmark Notes

This document is the canonical reference for normal Hay/Wood/Carrot farming, Sunflower/Power support, multi-drone layout decisions, and the benchmark suite.

Read this file before changing:

- `farm.py`
- normal-farm handling in `production.py`
- `bench_farm.py`
- `bench_farm_run.py`

## Why the current layout is under review

The current production design reserves:

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

Do not remove the current layout until the benchmark data supports a replacement.

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
| `current-l-production` | exact current production baseline |
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

The runner performs all crop profiles, then the dedicated Power suite.

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
