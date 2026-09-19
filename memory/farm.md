# Farm

## Current production state

The normal Farm covers Hay/Grass, Wood/Tree, Carrot, and permanent Sunflower Power support.

Current production in `farm.py` is still synchronous:

- partial Megafarm: crop chunks plus one dedicated max-petal Sunflower column
- max Megafarm / 32 drones: one crop worker per column plus two dumb Sunflower columns
- `farm.run()` respawns workers for every planner pass

The legacy Sunflower L remains benchmark-only.

## Durable worker finding

Persistent workers are a strong candidate because successful `spawn_drone()` is a physical action and synchronous `workers.run()` also creates a barrier after each pass.

Reusable reference ideas:

- msmith93 `multidrone.py`: static long-lived workers with stable spatial ownership
- msmith93 `multidrone/carrot.py` and `multidrone/wood.py`: persistent crop workers and companion rerolling
- msmith93 `multi_drone_hay_leaderboard.py`: long-lived Hay workers with static companion geometry
- MateusMarochi `polyculture_farm_paralel.py`: persistent fixed column pairs plus dedicated Sunflowers
- nql1314 `resource_farm_mega.py`: persistent region pool is relevant, but its shared-memory communication is historical/invalid under current drone-memory semantics

Do not reintroduce shared Python state between drones. Current probes show spawned drones have isolated mutable memory.

## Polyculture maximum hypothesis

The next high-end candidate is an all-Soil checkerboard:

- even parity: permanent `Entities.Bush` companion tiles
- odd parity: current target crop, one of Grass/Tree/Carrot
- target crop is rerolled until `get_companion()` asks for Bush on an even-parity coordinate
- reject companion coordinates that land in the dedicated Sunflower columns

Benefits to measure:

- accepted companion location is already known to contain Bush, so no remote cross-drone companion writes are needed
- Tree targets on odd parity are not orthogonally adjacent
- the Bush layout can survive Carrot -> Hay -> Wood -> Carrot focus changes
- all-Soil avoids repeated Soil/Grassland transitions, at the cost of explicitly replanting Grass

This is a benchmark hypothesis, not a measured production conclusion.

## Setup-cost rule

Do not select a Farm algorithm from steady-state throughput alone.

A cold benchmark must include:

- `clear()`
- Soil conversion
- static companion layout construction
- temporary setup-worker spawn cost
- persistent-worker spawn cost
- Sunflower construction
- zero-Power startup

Persistent workers may have a larger one-time setup but lower repeated pass overhead. Measure at multiple workload horizons to determine whether/when the setup amortizes.

## Current maximum benchmark

Benchmark code state:

`d1956d30d2e1aa98da49bbccecf8c087b7b72828`

Files:

- `bench_poly.py`
- `bench_poly_run.py`

Profiles:

- partial Megafarm level 3
- max Megafarm

Modes screen current and static-rerolling implementations across:

- one max-petal Sunflower column
- two dumb Sunflower columns
- stride workers
- contiguous chunks
- column pairs

Horizons:

- cold-short: +100k Carrot -> +100k Hay -> +200k Wood -> +100k Carrot
- cold-medium: +1M Carrot -> +1M Hay -> +2M Wood -> +1M Carrot
- sustained: +5M Carrot -> +5M Hay -> +10M Wood -> +5M Carrot

All candidates run cold-short and cold-medium with seed 1. The best current persistent candidate and best static-rerolling candidate from the medium screen then run against synchronous production over seeds 1, 2, and 3 on the sustained workload.

The poly modes print explicit `FARMX POLY PREP` and `FARMX POLY LAUNCH` metrics. Primary comparison remains total `simulate()` runtime, because setup and useful worker activity can overlap.

Run:

`bench_poly_run.py`

No production switch has been made yet. Paste the complete `FARMX ...` output back and only record measured conclusions against the benchmark SHA above.


## Sunflower placement challenge

Verified reference finding: there is no source-backed reason to reserve Sunflowers at a farm edge. Normal farm movement wraps, so coordinates at an apparent edge are not topologically special. The meaningful choices are concentration vs distribution, crop-area loss, worker ownership, Sunflower servicing overhead, and whether max-petal ordering repays its coordination/movement cost.

Relevant references:

- `external/sciencejiho-tfwr-solutions/source/strategy_polyculture.py`
  - treats `Items.Power -> Entities.Sunflower` as a normal primary crop selected by inventory ratio
  - Sunflowers can therefore be placed by the asynchronous Polyculture lanes instead of being isolated at an edge
- `external/mateusmarochi-the-farmer-was-replaced-codes/source/sunflower_farm.py`
  - uses the whole 32x32 field with one persistent worker per column
  - demonstrates that Sunflower maintenance itself has no edge requirement
- `external/msmith93-thefarmerwasreplaced/source/multidrone/sunflowers.py`
  - plants/harvests Sunflowers across the complete field with parallel column workers
- `external/flekay-the-farmer-was-replaced/source/Sunflowers/`
  - compares full-field/simple spam, immediate replant, petal maps, and nearest-neighbor routing
  - its recorded single-drone results show simple strategies can beat more elaborate ordered/pathing strategies in that upstream environment; treat this as candidate evidence, not current-runtime proof
- `external/reddit-normal-farm-sunflower-research/README.md`
  - records community candidates including one worker per row/column and smaller fixed rectangles such as synchronized 4x8 chunks
- current local `bench_farm_run.py`
  - already measured one integrated Sunflower row as highly competitive at full Megafarm; this is direct evidence that reserving dedicated Sunflower columns is not automatically optimal

New benchmark hypotheses:

1. **embedded diagonal, 32 Sunflowers**
   - one Sunflower per column
   - use `y = (x + 1) % size` so every Sunflower occupies odd parity
   - preserves the even-parity Bush checkerboard used by the static Polyculture candidate
   - no dedicated Sunflower worker is required if each crop worker services its local Sunflower during normal traversal

2. **embedded sparse grid, 16 Sunflowers**
   - evenly distribute 16 Sunflowers across the toroidal field
   - place only on odd-parity crop cells so Bush companion cells remain intact
   - halves Sunflower tile cost relative to a 32-tile row/diagonal and uses only 1.56% of a 32x32 field
   - must prove that 16 flowers sustain enough Power from cold start

3. **compact 4x4 or 4x8 block**
   - inspired by the smaller fixed-rectangle community references
   - allows a dedicated max-petal worker to exploit locality without consuming an entire 32-tile column or two 32-tile columns
   - 4x8 keeps 32 Sunflowers; 4x4 uses 16

4. **dynamic integrated Power**
   - ScienceJiho-style inventory-ratio selection can make Sunflower a normal lane crop only while Power is deficient
   - potentially avoids permanently reserving any geometry
   - setup/transition churn must be measured

Do not frame this as "edge vs center": because movement wraps, the real benchmark dimensions are **dedicated vs embedded**, **compact vs distributed**, **Sunflower count**, **worker allocation**, and **ordered vs dumb harvesting**.

The existing `bench_poly_run.py` does not yet cover these placement families. Extend or add a placement screen before making a production decision.


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
