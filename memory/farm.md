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
