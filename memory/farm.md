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


## Main farm vs resource leaderboard specialization

Resource leaderboards are a different workload from the normal progression farm.

Official leaderboard description:

- all unlocks are available
- resources required to grow the target plant are provided
- the run starts with lots of Power
- the program must terminate after the target is reached
- exact starting inventory for the resource leaderboards is not documented in the public leaderboard text

Do not reuse Main-Run safety policy unchanged for Wood/Carrots/Hay leaderboards.

### Main Run policy

The normal farm must remain robust across progression:

- Power may start at zero and may need active Sunflower production
- Water and Fertilizer inventories are not assumed
- planting affordability must be checked where depletion is possible
- unlock/state transitions may happen during execution
- Fertilizer also serves the Main-Run Weird Substance / Maze economy
- defensive entity/ground repair is appropriate because other production jobs can mutate the farm

### Resource leaderboard hypothesis

For Wood/Carrots/Hay:

- start with no dedicated Sunflower production unless measurement proves the supplied Power can run out
- use the entire available farm/drone budget for the target resource
- benchmark removal of repeated `utils.can_afford()`, `num_unlocked()`, entity-type, and ground-type checks after deterministic initialization
- keep only correctness-critical checks such as maturity unless a schedule guarantees maturity
- check the target inventory less frequently than every tile if termination overshoot stays small
- terminate all workers as soon as the leaderboard target is satisfied

Power is consumed by normal actions and speeds execution, so layout rankings measured with `Power=0` are not automatically valid for a Resource LB.

### Water

Watering is a throughput accelerator and should be benchmarked separately.

Current Main Run:

```python
if get_water() < WATER_LIMIT:
    if num_items(Items.Water) > 0:
        use_item(Items.Water)
```

LB candidates should compare at least:

- no watering
- water threshold 0.25
- water threshold 0.50
- water threshold 0.75
- a lean threshold version without the repeated `num_items(Water)` check if the true LB start/replenishment makes that safe

Do not assume the Main-Run 0.75 threshold is LB-optimal.

### Fertilizer

Fertilizer removes 2 seconds of remaining grow time but infects the plant. Infected harvests convert half of the normal yield into Weird Substance.

Therefore Main Run and Resource LB have opposite incentives:

- Main Run can intentionally value Weird Substance
- Wood/Carrot/Hay LB values only the target resource, so infection directly reduces useful yield

Do not enable fertilizer in LB by default. Benchmark it as an ablation only, especially for Carrot and Tree. Grass has a very short base grow time and is the lowest-priority fertilizer candidate.

### Sunflowers

Resource LB starts with lots of Power, therefore the default LB hypothesis is zero Sunflower tiles/workers.

This recovers:

- one or two crop columns from the measured Main-Run layouts
- one or two drones
- all Sunflower plant/measure/harvest actions
- petal-order bookkeeping

Only reintroduce Sunflowers if an actual leaderboard start-state probe shows that supplied Power is insufficient for the full target workload.

### Pending exact start-state probe

Files:

- `lb_res_probe.py`
- `lb_probe_run.py`

`lb_probe_run.py` executes failed/diagnostic Wood, Carrots, and Hay leaderboard runs. The probe prints:

- initial item inventory including Power, Water, Fertilizer, and Weird Substance
- world size and max drones
- starting water/ground/entity state
- relevant unlock levels
- current Carrot/Tree/Bush/Sunflower planting costs

Use these measured values before creating a simulated Resource-LB benchmark. Do not invent undocumented Water/Fertilizer start quantities.


## Measured Wood leaderboard start state

Measured directly with `lb_res_probe.py` / `leaderboard_run(Leaderboards.Wood, ...)` on 2026-09-19.

This section is measured game state, not an inferred simulation setup.

### Farm/runtime

```text
world size: 32
max drones: 32
initial water level: 0
initial entity: Entities.Grass
initial ground: Grounds.Grassland
```

### Initial inventory

```text
Hay              0
Wood             0
Carrot           0
Pumpkin          0
Cactus           0
Bone             0
Weird_Substance  0
Gold             0
Water            0
Fertilizer       0
Power            1000000000
Piggy            0
```

Critical implications:

- Wood LB really does start with a huge Power reserve: `1_000_000_000`
- it does **not** start with Water inventory
- it does **not** start with Fertilizer inventory
- dedicated Sunflower production is therefore unnecessary at startup for Wood LB
- Water/Fertilizer strategies must account for passive replenishment during the run rather than assuming a starting stockpile

Do not silently copy Main-Run `simulation_items()` values into Wood-LB benchmarks. The measured leaderboard state is materially different.

### Measured unlock levels

```text
Speed        5
Watering     9
Fertilizer   4
Sunflowers   1
Trees       10
Carrots     10
Grass       10
Megafarm     5
Polyculture  5
```

This confirms a fully developed 32x32 / 32-drone resource-farming environment, but the exact upgrade levels should be preserved when reproducing the real Wood leaderboard.

### Measured planting costs

```text
Carrot     {Items.Hay: 512, Items.Wood: 512}
Tree       {}
Bush       {}
Sunflower  {Items.Carrot: 1}
```

Wood-specific implications:

- `Entities.Tree` is free to plant at this leaderboard state
- `Entities.Bush` is free to plant
- repeated `utils.can_afford(Entities.Tree)` checks are pure defensive overhead in a dedicated Wood-LB implementation
- the Wood-LB hot path can benchmark direct `plant(Entities.Tree)` after deterministic setup/recovery
- Carrots are expensive enough that using Sunflowers would introduce an unnecessary dependency chain (Carrot -> Sunflower) despite the already huge Power reserve

### Wood-LB optimization direction

The primary Wood-LB benchmark family should be separate from Main Run and start from these measured assumptions:

1. no Sunflower columns/workers
2. all 32 drones available for Wood production
3. full 32x32 farm available for Wood layout
4. no Tree affordability checks in the steady-state hot path
5. benchmark Water use despite starting at zero, because Watering level 9 may replenish Water during the run
6. benchmark Fertilizer only as a measured passive-resource strategy; starting inventory is zero
7. explicit finite termination at `num_items(Items.Wood) >= 10_000_000_000`

Do not generalize the Wood initial inventory to Carrots or Hay until their leaderboard probes are measured separately.


## Dedicated Wood / Carrot / Hay leaderboard benchmark suites

Resource leaderboard research is split by target resource. Do not create or use a generic `bench_lb_farm.py`.

Files:

| Resource | Benchmark | Runner | Version | Start-state status |
| --- | --- | --- | --- | --- |
| Wood | `bench_lb_wood.py` | `bench_lb_wood_run.py` | `lbwood-v1` | measured Wood-LB inventory |
| Carrot | `bench_lb_carrot.py` | `bench_lb_car_run.py` | `lbcar-v1` | synthetic support inventory until Carrot probe |
| Hay | `bench_lb_hay.py` | `bench_lb_hay_run.py` | `lbhay-v1` | Wood Power start used provisionally until Hay probe |

All benchmark runners request simulation speedup 10000.

### Wood v1

Measured Wood-LB state is used directly:

- 32x32
- 32 drones
- Power 1,000,000,000
- Water 0
- Fertilizer 0
- all target/support resource inventories 0

Screen target: 100,000,000 Wood.

Final target: exact leaderboard target 10,000,000,000 Wood across seeds 1/2/3 for the three fastest screen modes.

Modes:

- checkerboard Tree/Grass lean
- checkerboard Tree/Bush lean
- water-0.75 variants
- Fertilizer variants
- Water+Fertilizer
- full-Tree controls
- defensive/safe control including affordability checks

No mode uses Sunflowers.

### Hay v1

Screen target: 50,000,000 Hay.

Final target: exact leaderboard target 2,000,000,000 Hay across seeds 1/2/3.

Modes compare lean Grass harvesting, water thresholds 0.25/0.50/0.75, Fertilizer, Water+Fertilizer, and a defensive safe control.

No mode uses Sunflowers or planting.

The current v1 runner uses Power=1,000,000,000 as a provisional hypothesis copied from the measured Wood-LB environment. Do not treat this as measured Hay state until `lb_hay_probe.py` is run.

### Carrot v1

Screen target: 50,000,000 Carrot.

Final target: exact leaderboard target 2,000,000,000 Carrot across seeds 1/2/3.

Modes compare lean direct harvest/replant, water thresholds 0.25/0.50/0.75, Fertilizer, Water+Fertilizer, and a defensive safe control with affordability checks.

No mode uses Sunflowers.

The Carrot start inventory has not yet been measured. `bench_lb_car_run.py` intentionally supplies 10,000,000,000 Hay and 10,000,000,000 Wood as synthetic support so v1 measures hot-path behavior rather than starvation. This is not a claim about the real Carrot leaderboard start state.

### Probe launchers

A real `leaderboard_run()` does not continue to subsequent leaderboard calls in the same launcher. The original combined probe therefore produced only Wood.

Use separate launchers:

- `lb_car_probe.py`
- `lb_hay_probe.py`

Both run the shared `lb_res_probe.py` diagnostic inside the respective real leaderboard environment.

After those are measured, bump the affected benchmark version before replacing provisional/synthetic start-state inputs.
