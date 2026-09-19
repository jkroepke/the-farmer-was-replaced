# Leaderboards

## Scope

Durable reference for the current leaderboard challenge modes and their exact success conditions.

Source for this snapshot: current in-game leaderboard descriptions supplied by the user on 2026-09-19.

Verification status: the values below are transcribed from that supplied game text. They have not yet been independently cross-checked against the wiki or a fresh game build by this repository.

## General execution rule

Repository execution-speed defaults:

- ordinary `simulate()` benchmark runners request speedup `10000`
- real `leaderboard_run()` launchers request speedup `256`
- changing a benchmark speedup requires a `BENCH_VERSION` bump
- historical results retain the speedup they were actually measured with

Leaderboard runs use:

```python
leaderboard_run(leaderboard, filename, speedup)
```

Repository speed policy:

- simulation-only benchmarks use `simulate(..., speedup=10000)`
- actual leaderboard submissions use `leaderboard_run(..., speedup=256)`

The higher benchmark speedup is only for reducing wall-clock benchmark time; real leaderboard launchers intentionally stay at 256.

A run is not finished merely because the target inventory/unlock condition becomes true. The submitted program must terminate after reaching the target.

This makes termination latency part of every leaderboard implementation. Production loops written for normal endless farming are not valid leaderboard submissions unless wrapped with an explicit target check and exit path.

## Main-run / leaderboard split

Repository runtime policy:

- `main.py` is the adaptive normal-production entry point
- normal mechanic modules keep progression/resource safety
- `lb_<mechanic>.py` is a finite challenge-specific implementation
- `lb_<mechanic>_run.py` is the small `leaderboard_run(...)` launcher

Leaderboard code should specialize aggressively for the exact measured start
state. Main-run checks are not automatically copied into LB code.

Safe-to-remove LB checks, once verified for that exact leaderboard, include:

- affordability checks for guaranteed-free/covered actions
- repeated inventory guards for challenge inputs supplied in enormous amounts
- prerequisite/resource-planner logic
- world-size/drone-count fallback branches when the mode fixes them
- production stockpile/reserve policy
- restore-normal-farm logic

Checks that remain:

- exact target and prompt program termination
- mechanic-boundary checks whose return value carries meaning
- entity/state checks needed for legal actions
- synchronization/race-prevention checks

Maze is the clearest example:

- Main Maze must check Weird Substance reserve, Bush affordability, available
  drones/world size, and return to production planning when inputs are missing
- Maze LB starts with `1_000_000_000` Weird Substance and
  `1_000_000_000` Power, so repeated resource-availability checks are hot-path
  overhead
- Maze LB must still retain any `use_item()` result used to detect the
  300-reuse boundary and must terminate at exactly
  `num_items(Items.Gold) >= 9863168`

Do not generalize the Maze resource guarantee to other leaderboards. Use each
mode's probe evidence before deleting checks.

## Fastest Reset

Leaderboard:

```python
Leaderboards.Fastest_Reset
```

Goal: fully automate progression from a single starting farm tile until `Unlocks.Leaderboard` is unlocked again.

The run does not need to unlock everything. The only success condition is:

```python
num_unlocked(Unlocks.Leaderboard) > 0
```

The supplied equivalent simulation is:

```python
unlocks = {}
items = {}
globals = {}
seed = -1
simulate(filename, unlocks, items, globals, seed, speedup)
```

A negative seed means a random seed.

Useful dynamic progression primitives called out by the game description:

- `num_unlocked(unlock) > 0` to test whether an unlock is available
- `get_cost(unlock)` to read the current cost of an unlock

This mode therefore strongly favors a progression controller that continuously evaluates the live unlock frontier and farms only resources needed to reach `Unlocks.Leaderboard`.

Repository relevance:

- `main.py`, `unlocks.py`, and `production.py` already implement dynamic unlock-cost-driven progression and are the natural starting point for a Fastest Reset specialization.
- `docs/UNLOCKS.md` contains the existing unlock/progression research.
- External Fastest Reset references already exist under `external/msmith93-full-reset/` and `external/j4lc-the-farmer-was-replaced/`.

Do not assume that the normal production policy is leaderboard-optimal. Fastest Reset should be benchmarked as its own finite workload.

## Maze

Current dedicated launcher:

```python
leaderboard_run(Leaderboards.Maze, "lb_maze", 256)
```

The dedicated Maze leaderboard launcher uses speedup 256. This is intentionally lower than the 10000 used by simulation-only benchmarks.

Files:

- `lb_maze_run.py` — leaderboard launcher
- `lb_maze.py` — finite Maze leaderboard implementation

The current implementation uses the strongest measured long-run candidate so far,
uniform 5x5 map+BFS reuse300, and exits at the exact 9863168-Gold target. The
exact-target cold-start finalist benchmark remains the final selection criterion.

Leaderboard:

```python
Leaderboards.Maze
```

Starting state from the supplied game text:

```python
unlocks = Unlocks
items = {
    Items.Weird_Substance: 1000000000,
    Items.Power: 1000000000,
}
globals = {}
seed = -1
simulate(filename, unlocks, items, globals, seed, speedup)
```

Success condition:

```python
num_items(Items.Gold) >= 9863168
```

The description states that 9,863,168 Gold is exactly the amount earned by solving a 32x32 Maze 300 times.

This target is materially different from the repository's earlier small Gold benchmarks. Future Maze leaderboard benchmarks should therefore measure complete time-to-9,863,168-Gold and terminate immediately after the threshold is reached.

See `memory/maze.md` and `docs/MAZE.md` for the current Maze architecture and benchmark history.

## Dinosaur

Leaderboard:

```python
Leaderboards.Dinosaur
```

Starting state from the supplied game text:

```python
unlocks = Unlocks
items = {
    Items.Cactus: 1000000000,
    Items.Power: 1000000000,
}
globals = {}
seed = -1
simulate(filename, unlocks, items, globals, seed, speedup)
```

Success condition:

```python
num_items(Items.Bone) >= 33488928
```

The description states that 33,488,928 Bone is exactly the amount produced by filling a 32x32 area with the Dinosaur tail.

See `docs/DINOSAUR.md` and the Dinosaur benchmark modules for current research.

## Resource leaderboards

The supplied game description says that every plant/resource has its own leaderboard.

General properties explicitly stated:

- start with all unlocks
- start with the resources needed to grow the target plant
- start with a large amount of Power
- farm a fixed target amount
- terminate the program once the target has been reached

The supplied text does not list the exact starting inventory for each resource leaderboard, so do not invent those values. Use `leaderboard_run()` or inspect the current game data when a benchmark needs the exact starting inventory.

### Cactus

```python
leaderboard_run(Leaderboards.Cactus, filename, speedup)
```

Success condition:

```python
num_items(Items.Cactus) >= 33554432
```

Target: 33,554,432 Cactus.

This matches the full-chain 32x32 Cactus yield already used by the repository's Cactus benchmark validity checks.

### Sunflowers

```python
leaderboard_run(Leaderboards.Sunflowers, filename, speedup)
```

Success condition:

```python
num_items(Items.Power) >= 100000
```

Target: 100,000 Power.

### Pumpkins

```python
leaderboard_run(Leaderboards.Pumpkins, filename, speedup)
```

Success condition:

```python
num_items(Items.Pumpkin) >= 200000000
```

Target: 200,000,000 Pumpkin.

### Wood

```python
leaderboard_run(Leaderboards.Wood, filename, speedup)
```

Success condition:

```python
num_items(Items.Wood) >= 10000000000
```

Target: 10,000,000,000 Wood.

### Carrots

```python
leaderboard_run(Leaderboards.Carrots, filename, speedup)
```

Success condition:

```python
num_items(Items.Carrot) >= 2000000000
```

Target: 2,000,000,000 Carrot.

### Hay

```python
leaderboard_run(Leaderboards.Hay, filename, speedup)
```

Success condition:

```python
num_items(Items.Hay) >= 2000000000
```

Target: 2,000,000,000 Hay.

## Single-drone leaderboards

The supplied game description explicitly states that these modes provide:

- exactly one drone
- an 8x8 farm
- a fixed target resource amount
- the same requirement that the program must terminate after satisfying the target

### Maze Single

```python
leaderboard_run(Leaderboards.Maze_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Gold) >= 616448
```

Target: 616,448 Gold.

### Cactus Single

```python
leaderboard_run(Leaderboards.Cactus_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Cactus) >= 131072
```

Target: 131,072 Cactus.

### Sunflowers Single

```python
leaderboard_run(Leaderboards.Sunflowers_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Power) >= 10000
```

Target: 10,000 Power.

### Pumpkins Single

```python
leaderboard_run(Leaderboards.Pumpkins_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Pumpkin) >= 10000000
```

Target: 10,000,000 Pumpkin.

### Wood Single

```python
leaderboard_run(Leaderboards.Wood_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Wood) >= 500000000
```

Target: 500,000,000 Wood.

### Carrots Single

```python
leaderboard_run(Leaderboards.Carrots_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Carrot) >= 100000000
```

Target: 100,000,000 Carrot.

### Hay Single

```python
leaderboard_run(Leaderboards.Hay_Single, filename, speedup)
```

Success condition:

```python
num_items(Items.Hay) >= 100000000
```

Target: 100,000,000 Hay.

## Target summary

| Leaderboard | Target |
| --- | ---: |
| Fastest Reset | `num_unlocked(Unlocks.Leaderboard) > 0` |
| Maze | 9,863,168 Gold |
| Dinosaur | 33,488,928 Bone |
| Cactus | 33,554,432 Cactus |
| Sunflowers | 100,000 Power |
| Pumpkins | 200,000,000 Pumpkin |
| Wood | 10,000,000,000 Wood |
| Carrots | 2,000,000,000 Carrot |
| Hay | 2,000,000,000 Hay |
| Maze Single | 616,448 Gold |
| Cactus Single | 131,072 Cactus |
| Sunflowers Single | 10,000 Power |
| Pumpkins Single | 10,000,000 Pumpkin |
| Wood Single | 500,000,000 Wood |
| Carrots Single | 100,000,000 Carrot |
| Hay Single | 100,000,000 Hay |

## Research implications

Future leaderboard work should keep two benchmark families separate:

1. multi-drone/all-unlocks resource leaderboards, where throughput and parallel layout dominate
2. single-drone 8x8 leaderboards, where movement locality, action count, and avoiding setup overhead dominate

Fastest Reset is a third distinct workload because resource production, unlock selection, farm expansion, and producer unlock prerequisites all interact.

For all leaderboard candidates:

- benchmark end-to-end wall-clock simulation time, not only per-cycle crop time
- include setup and teardown/termination cost
- use the real leaderboard target instead of extrapolating from one small cycle
- confirm that the program terminates after reaching the target
- use multiple random seeds for strategies whose runtime depends on random crop/entity behavior
- keep benchmark provenance according to the repository's commit-SHA rules

## Pending reset planner benchmark (2026-09-19)

`bench_reset.py` / `bench_reset_run.py` compare three Fastest Reset planner policies from empty unlock/item state to `Unlocks.Leaderboard`, all using the same current production backend: dynamic frontier, Agude-inspired sticky bounded target, and the pinned msmith93 static unlock order with live cost resampling. Runner version: `reset-v1`; seeds 1/2/3; action watchdog 10000. No result has been measured yet.

`bench_ticks.py` / `bench_ticks_run.py` re-measure Flekay-inspired interpreter hot-path claims (dict key shape, membership structures, queue front-pop vs cursor, append vs concatenation). Runner version: `ticks-v1`. Treat upstream January 2026 tick values as hypotheses until this current-runtime suite is run.


## Main farm vs Resource-LB execution policy

Wood/Carrots/Hay leaderboards should use dedicated finite implementations rather than the normal endless production farm.

Reason:

- the official Resource-LB environment starts with all unlocks and lots of Power
- normal Main-Run code must bootstrap and preserve Power itself
- normal Main-Run Fertilizer usage is partly motivated by Weird Substance production, while infected plants lose half of their target-resource yield
- normal Main-Run affordability/state checks may be unnecessary overhead in a fixed LB environment

Default LB hypotheses to benchmark:

1. no Sunflower workers or tiles
2. full target-crop farm area
3. lean planting without repeated affordability checks when the measured start inventory proves this safe
4. water-policy ablation
5. fertilizer off by default; only explicit ablation
6. explicit finite target checks and worker termination

Before writing the final LB simulator, run `lb_probe.py` to capture the exact Wood/Carrots/Hay starting inventories because the public leaderboard description does not publish those amounts.


## Measured Wood resource-leaderboard start state

Measured 2026-09-19 with the repository's diagnostic `lb_probe.py`.

### Exact observed start state

| Property | Value |
| --- | ---: |
| World size | 32 |
| Max drones | 32 |
| Water level | 0 |
| Starting entity | `Entities.Grass` |
| Starting ground | `Grounds.Grassland` |
| Power | 1,000,000,000 |
| Water inventory | 0 |
| Fertilizer inventory | 0 |
| Hay | 0 |
| Wood | 0 |
| Carrot | 0 |
| Weird Substance | 0 |

Other listed resources were also zero at start.

Measured unlock levels:

| Unlock | Level |
| --- | ---: |
| Speed | 5 |
| Watering | 9 |
| Fertilizer | 4 |
| Sunflowers | 1 |
| Trees | 10 |
| Carrots | 10 |
| Grass | 10 |
| Megafarm | 5 |
| Polyculture | 5 |

Measured entity costs:

| Entity | Cost |
| --- | --- |
| Carrot | `{Items.Hay: 512, Items.Wood: 512}` |
| Tree | `{}` |
| Bush | `{}` |
| Sunflower | `{Items.Carrot: 1}` |

### Consequences for Wood leaderboard research

The previously documented general statement "resources needed to grow the plant and lots of Power" is now concretely resolved for Wood:

- Power starts at exactly `1_000_000_000`
- Tree and Bush planting costs are empty at this upgrade level
- Water and Fertilizer start at zero
- the run starts on an empty/default Grass tile on Grassland
- all 32 drones and the full 32x32 farm are available

Therefore the Wood leaderboard should not use the normal Main-Run Sunflower economy or Tree affordability checks.

The leading Wood-LB hypothesis is:

```text
32x32
32 drones
0 sunflower workers
0 sunflower tiles
full Wood layout
direct/free Tree planting
lean steady-state checks
finite 10,000,000,000 Wood termination
```

Water and Fertilizer remain benchmark questions because their inventories start at zero but the measured Watering/Fertilizer upgrade levels may replenish them over time.

Do not assume that the Carrots or Hay leaderboard has the same starting inventory. Probe and record those modes separately.


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

The current v1 runner uses Power=1,000,000,000 as a provisional hypothesis copied from the measured Wood-LB environment. Do not treat this as measured Hay state until `lb_probe.py` is run.

### Carrot v1

Screen target: 50,000,000 Carrot.

Final target: exact leaderboard target 2,000,000,000 Carrot across seeds 1/2/3.

Modes compare lean direct harvest/replant, water thresholds 0.25/0.50/0.75, Fertilizer, Water+Fertilizer, and a defensive safe control with affordability checks.

No mode uses Sunflowers.

The Carrot start inventory has not yet been measured. `bench_lb_car_run.py` intentionally supplies 10,000,000,000 Hay and 10,000,000,000 Wood as synthetic support so v1 measures hot-path behavior rather than starvation. This is not a claim about the real Carrot leaderboard start state.

### Probe launchers

A real `leaderboard_run()` does not continue to subsequent leaderboard calls in the same launcher. The original combined probe therefore produced only Wood.

Use separate launchers:

- `lb_probe.py`
- `lb_probe.py`

Both run the shared `lb_probe.py` diagnostic inside the respective real leaderboard environment.

After those are measured, bump the affected benchmark version before replacing provisional/synthetic start-state inputs.


## Universal leaderboard start-state probe

There is exactly one leaderboard probe file:

```text
lb_probe.py
```

Probe version: `lbprobe-v3`.

`lb_probe.py` is the payload for every leaderboard environment. It intentionally does not call `leaderboard_run()` itself, because starting another leaderboard from inside the probe would recurse.

Run the desired leaderboard with `lb_probe` as its filename, for example:

```python
leaderboard_run(Leaderboards.Wood, "lb_probe", 256)
leaderboard_run(Leaderboards.Carrots, "lb_probe", 256)
leaderboard_run(Leaderboards.Hay, "lb_probe", 256)
leaderboard_run(Leaderboards.Wood_Single, "lb_probe", 256)
```

The same pattern applies to every other known leaderboard:

- Fastest_Reset
- Maze
- Dinosaur
- Cactus
- Sunflowers
- Pumpkins
- Wood
- Carrots
- Hay
- Maze_Single
- Cactus_Single
- Sunflowers_Single
- Pumpkins_Single
- Wood_Single
- Carrots_Single
- Hay_Single

The probe prints:

- world size
- max drones
- initial water level
- initial entity and ground
- every item inventory value
- every unlock level
- planting costs for Grass, Bush, Tree, Carrot, Sunflower, Pumpkin, and Cactus

The probe intentionally terminates immediately and therefore fails the leaderboard target. Its only purpose is to record the exact initial environment.

Do not generalize one leaderboard's measured start state to another leaderboard before probing it.

