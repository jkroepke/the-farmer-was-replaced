# Leaderboards

## Scope

Durable reference for the current leaderboard challenge modes and their exact success conditions.

Source for this snapshot: current in-game leaderboard descriptions supplied by the user on 2026-09-19.

Verification status: the values below are transcribed from that supplied game text. They have not yet been independently cross-checked against the wiki or a fresh game build by this repository.

## General execution rule

Leaderboard runs use:

```python
leaderboard_run(leaderboard, filename, speedup)
```

A run is not finished merely because the target inventory/unlock condition becomes true. The submitted program must terminate after reaching the target.

This makes termination latency part of every leaderboard implementation. Production loops written for normal endless farming are not valid leaderboard submissions unless wrapped with an explicit target check and exit path.

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
leaderboard_run(Leaderboards.Maze, "lb_maze", 64)
```

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
