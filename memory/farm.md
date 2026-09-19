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

## Pending sciencejiho lane benchmark (2026-09-19)

`bench_persist.py` now includes `science-async-lanes`, an architecture-only port of sciencejiho's current-memory-safe scheduler: copied one-column jobs, controller-owned lane state, `has_finished()` collection, immediate relaunch, and one controller lane doing useful work. Existing crop servicing/layouts are unchanged so the test isolates worker lifecycle. Benchmark runner version: `persist-v2`. Results are not yet measured.

## Benchmark record

Measured Farm and Sunflower results are maintained in `bench/farm.md`. Keep only durable strategy decisions and open research questions in this memory file.

## FarmX v5 follow-up

After the measured v4 run, the next FarmX suite is `farmx-v5`.

Changes:

- adds persistent `one-row-dumb` variants:
  - `current-one-row-stride`
  - `current-one-row-chunks`
  - `current-one-row-pairs`
- adds persistent `one-col-dumb` variants:
  - `current-one-col-stride`
  - `current-one-col-chunks`
  - `current-one-col-pairs`
- keeps the seven-petal implementations for reproducibility but removes them from default screening after their v4 losses
- keeps Poly in the mixed FarmX research suite, but removes Poly from pure max-crop screening after losing max-Carrot, max-Grass, and max-Wood in v4
- pure max-crop screening selects the three fastest current layouts on seed 1, then validates all three plus `sync-selected` across seeds 1/2/3
- lengthens pure-focus targets to reduce setup domination and Grass seed variance:
  - max-Carrot: 50M total Carrot
  - max-Grass: 50M Hay
  - max-Wood: 100M Wood

Relevant commits:

- `cf836e64e4c3cb6e0f241d11f8c67f9f021d817f` exposes persistent row/column dumb layouts in `bench_poly.py`
- `25aacb7719da11c5f39c1f54cd3ecf695f8c7baa` creates the `farmx-v5` runner
