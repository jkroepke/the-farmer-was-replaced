# The Farmer Was Replaced — Agent Notes

## Current architecture

The automation is split into modules:

- `main.py` — upgrade-driven orchestration
- `config.py` — tuning knobs
- `utils.py` — movement, affordability, water helpers
- `workers.py` — multi-drone worker pool and hats
- `farm.py` — normal mixed farm, sunflowers, carrots, resources, polyculture
- `maze.py` — persistent Maze reuse using the reference tree-rebalancing strategy
- `pumpkin.py` — full-field giant pumpkin job
- `cactus.py` — full-field cactus job
- `unlocks.py` — upgrade selection, cost analysis, resource focus, unlock purchases
- `production.py` — resource-to-production dispatcher and prerequisite resolution
- `bench_maze.py` — all Maze benchmark strategies, including the reference port
- `bench_maze_run.py` — Maze simulation matrix, seeds, `simulate()` calls, and result aggregation
- `bench_dinosaur.py` — Dinosaur benchmark implementations/modes
- `bench_dinosaur_run.py` — Dinosaur simulation matrix, seeds, `simulate()` calls, and aggregation
- `bench_transition.py` — persistent normal-farm transition workload
- `bench_transition_run.py` — transition matrix for partial/max Megafarm
- `bench_persist.py` — full-Megafarm persistent-worker candidate
- `bench_persist_run.py` — persistent-worker benchmark runner
- `docs/NORMAL_FARM.md` — canonical normal-farm/Sunflower design, references, and benchmark notes
- `docs/UNLOCKS.md` — canonical automatic unlock priorities and endgame progression
- `docs/PUMPKIN.md` — canonical Pumpkin strategy, references, and multi-drone optimization notes
- `docs/MAZE.md` — canonical Maze design, benchmark results, and optimization notes

Always use `import module`, not `from module import ...`.

All code that should only run when the file itself is executed should be behind:

```python
if __name__ == "__main__":
    ...
```

## Benchmark provenance

Every benchmark result recorded in documentation must reference the full commit SHA of the benchmark state that produced it.

Use the SHA that pins both the runner and the tested implementation. Do not replace it with the SHA of a later docs-only commit.

## Multi-drone rules

Use as many drones as `max_drones()` permits when useful.

Do NOT limit drone count to the number of available hats.

Generic workers intentionally keep their current/default hat. `change_hat()` costs 200 ticks; do not add cosmetic hat cycling. `workers.set_main_hat()` is reserved for explicit state changes such as leaving the Dinosaur Hat.

Prefer **contiguous chunks** of the map rather than one tiny task per column/tile. This avoids drones spending most of their time flying to and from their assigned work.

## Normal farm

Normal-farm code must remain dynamic, but current endgame benchmarking focuses on 32x32.

Production no longer uses the legacy L.

Current normal-farm regimes:

- `max_drones() < world_size`: one dedicated max-petal Sunflower column plus crop chunks; selected as the strongest previously measured non-L fallback
- `max_drones() == world_size`: synchronous one-worker-per-column passes with the final two columns reserved for simple Sunflower harvest/replant

Persistent-worker layouts are being re-benchmarked across the previous non-L Sunflower candidates. See `docs/NORMAL_FARM.md` for benchmark commit SHAs.

Water production is high (~3.2/s) and fertilizer production is high (~0.8/s), so both may be used aggressively.

## Upgrade and resource planner

The main loop is **not cycle-driven anymore**. Do not reintroduce fixed counters such as `PUMPKIN_EVERY`, `CACTUS_EVERY`, or `DINOSAUR_EVERY`.

The current planner works in two stages.

### 1. Choose the next unlock

`config.UNLOCK_PLANS` defines both progression order and relative priority.

The list is a hard frontier:

- all already-reached upgrade lines may compete
- plus the first never-unlocked entry
- nothing after that first never-unlocked entry is considered yet

Within that candidate set, `unlocks.next_target()` compares weighted remaining cost:

```text
remaining_cost / priority
```

The implementation uses cross multiplication instead of division.

The plan includes the normal production/progression unlocks and lower-priority mandatory endgame goals:

```text
... -> Mazes -> Megafarm -> Dinosaurs -> Hats
    -> Leaderboard -> Top_Hat -> The_Farmers_Remains
```

This fixes the previous state where `PLAN goal None focus None` could appear even though endgame unlocks were still missing.

Current game costs and unlock state are always read with `get_cost()` / `num_unlocked()`; do not hard-code resource amounts into the planner.

See `docs/UNLOCKS.md` for the full table and reference rationale.

### 2. Choose which resource to produce

`config.RESOURCE_PLANS` is based on the plant/item order and priority values in Thorrdu's `parameters.py`:

| Output | Producer | Priority |
| --- | --- | ---: |
| `Items.Power` | `Entities.Sunflower` | 7 |
| `Items.Hay` | `Entities.Grass` | 5 |
| `Items.Wood` | `Entities.Tree` | 5 |
| `Items.Carrot` | `Entities.Carrot` | 5 |
| `Items.Pumpkin` | `Entities.Pumpkin` | 4 |
| `Items.Cactus` | `Entities.Cactus` | 4 |
| `Items.Bone` | Dinosaur job | 3 |
| `Items.Gold` | Maze job | 3 |

For all missing items in the selected unlock's real `get_cost()` dictionary, `unlocks.choose_focus_from_cost()` computes:

`score = (current_amount / required_amount) / priority`

The lowest score is farmed first. `RESOURCE_PLANS` order is the deterministic tie-breaker.

Unlike the source repository, this project does **not** use huge static inventory targets. Required amounts always come from the current unlock's `get_cost()`.

### Production dispatch

`production.py` maps the selected output to the correct strategy:

- Power/Hay/Wood/Carrot → normal chunked farm with the resource area biased toward that output
- Pumpkin → full-field Pumpkin job
- Cactus → full-field Cactus job
- Bone → Dinosaur job
- Gold → Maze job

Before expensive full-field crops, the dispatcher also checks the producer's own `get_cost(entity)` and recursively farms missing seed/input resources. For example, if Pumpkin is the needed unlock resource but there are not enough resources to plant the Pumpkin field, the planner first produces the Pumpkin plant's missing input.

Gold/Maze has a persistent lifecycle and Weird Substance handling that differs from the other producers. See `docs/MAZE.md`.

After destructive full-field jobs, clear/reset normal-farm state only when normal farming is needed again. The adaptive layout rebuilds lazily on the next `farm.run()`.

If `Unlocks.Expand` changes `get_world_size()`, clear/reset the normal farm; do not rebuild the legacy L.

### Planner sources

- **Thorrdu — `parameters.py`**  
  https://github.com/Thorrdu/the-farmer-was-replaced/blob/main/parameters.py  
  Source for the plant → item mapping, resource ordering, and priority values.

- **Thorrdu — `tools.py` / `priority_crop()`**  
  https://github.com/Thorrdu/the-farmer-was-replaced/blob/main/tools.py  
  Source for the `progressRatio / priority` resource-selection idea. Our implementation replaces static targets with live `get_cost()` requirements.

- **Tooltips Code / game API**  
  https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips_Code  
  Primary reference for `get_cost()`, `num_items()`, `num_unlocked()`, and `unlock()` behavior.

## Pumpkin rules

Documented game rules:

- Pumpkins grow on soil.
- Planting pumpkins costs carrots.
- A grown pumpkin has a ~20% chance to die.
- Dead pumpkins are `Entities.Dead_Pumpkin`.
- Planting over a dead pumpkin removes/replaces it.
- A full square of grown pumpkins merges into a giant pumpkin.
- A giant pumpkin is still reported as `Entities.Pumpkin`.
- `can_harvest()` is True on the harvestable giant pumpkin.

### Community-observed / reverse-engineered behavior

`measure()` on a Pumpkin returns a Pumpkin ID.

Observed behavior:

- the ID does not change with pumpkin size
- when pumpkins merge, the merged pumpkin keeps the ID of the first pumpkin involved in the merge
- therefore, if opposite corners of a full-map pumpkin have the same ID, the entire map belongs to the same merged pumpkin

Cheap full-map test:

```python
utils.move_to(0, 0)
first_id = measure()

move(West)
move(South)

opposite_id = measure()

full = first_id == opposite_id
```

The implementation also checks `Entities.Pumpkin` and `can_harvest()`.

## Pumpkin strategy: Patch & Wait

Do NOT continuously rescan all 256 fields.

Current intended algorithm:

1. Till/plant the full field once.
2. Wait for initial growth.
3. Run one full scan and record positions that are:
   - empty
   - dead
   - still unripe
4. Revisit only those recorded positions.
5. Replace dead/empty pumpkins.
6. Keep only positions that remain unresolved.
7. Use the very cheap corner-ID check between patch rounds.
8. Once the problem list is empty, check the corner IDs again.
9. Only do another full scan as a fallback if the merge still has not completed.

This is based on the observation that a live fully-grown pumpkin has already survived its one-time death roll, so it does not need to be checked repeatedly.

## Pumpkin performance

`get_tick_count()` and `quick_print()` cost 0 ticks. `get_time()` costs 1 tick in the current operation-cost documentation.

Use `get_time()` for wait intervals instead of repeatedly moving over the whole field.

Current tuning lives in `config.py`:

- `PUMPKIN_ID_CHECK_INTERVAL`
- `PUMPKIN_INITIAL_WAIT`
- `PUMPKIN_PATCH_INTERVAL`

## Sunflowers

Energy matters a lot because active energy doubles drone speed.

Sunflowers are permanent and live on the left and top farm edges. They should be rebuilt immediately after destructive full-field jobs such as:

- Pumpkin
- Cactus
- Dinosaur

Maze/Gold is intentionally different because an active Maze is reused; see `docs/MAZE.md`.

Do not harvest arbitrary sunflowers.

With at least 10 sunflowers, harvest only a sunflower with the **current maximum petal count**. After every harvest, determine the maximum again before harvesting another flower.

### Petal cache

The current implementation does **not** rescan the full sunflower L during every energy refresh.

Instead:

1. `rebuild_sunflowers()` plants/repairs the permanent sunflower edges.
2. Each rebuild worker measures its sunflowers and returns `[x, y, petals]` records.
3. The calling drone merges those results into `_sunflower_petals`.
4. `refresh_energy()` computes the current maximum from that in-memory cache.
5. It visits only cached positions with that maximum.
6. After harvesting, it immediately replants the sunflower, calls `measure()` once, updates that cache entry, and recomputes the maximum.
7. If the current maximum exists but is not mature yet, lower-petal sunflowers are **not** harvested.

This design is especially useful with only two drones: the second drone is useful for rebuilding the two sunflower edges, but repeatedly spawning/using drones just to rescan ~31 permanent sunflowers creates unnecessary movement.

Drone memory is not shared. Do not let worker drones mutate the caller's sunflower cache. Workers must return their measurements through `wait_for()` / `workers.run()`, and the caller must rebuild the cache from those return values.

Do not drop 7-petal sunflowers from the cache. The external community example below filters `> 7`, but our implementation keeps every measured sunflower because the current documented/common petal range includes 7.

### Sunflower sources

- **The Farmer Was Replaced — “Sunflower Code — Harvest Max Petals Only”**  
  https://thefarmerwasreplaced.com/codes/sunflower-code/  
  Key rules used here: harvest only the current maximum petal count, then determine the maximum again; the page reports sunflower petal counts commonly ranging from 7 to 15.

- **Thorrdu/the-farmer-was-replaced — `sunflowerModule.py`**  
  https://github.com/Thorrdu/the-farmer-was-replaced/blob/main/sunflowerModule.py  
  Community implementation that measures a sunflower immediately after planting and stores `[x, y, petals]`. This inspired the persistent petal-cache optimization. We intentionally do not copy its `petalNbr > 7` filter.

- **Tooltips Code**  
  https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips_Code  
  Use as the primary reference for the current `measure()`, movement, and tick-cost API when changing this logic.

## Maze

All Maze mechanics, persistent Gold lifecycle, production thresholds, reference-source notes, benchmark data, benchmark interpretation, and future optimization ideas are maintained in:

`docs/MAZE.md`

Do not duplicate Maze benchmark tables or strategy notes here.

## Future optimization ideas

- Measure job timings with `get_tick_count()` and `get_time()`.
- Tune pumpkin initial/patch waits empirically.
- Consider using fertilizer during Cactus jobs.


## Dinosaur

All Dinosaur mechanics, current strategy, external algorithm research, and benchmark methodology are maintained in:

`docs/DINOSAUR.md`

Do not duplicate Dinosaur benchmark tables or strategy notes here.


## Game file-name limit

Game-facing Python files must use names of at most 20 characters including `.py`. Keep benchmark, probe, and runner names short enough to be created directly in the in-game editor.

