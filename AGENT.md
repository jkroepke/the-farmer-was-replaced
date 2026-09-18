# AGENT.md

This repository contains automation scripts for **The Farmer Was Replaced**.

Agents working in this repository must optimize for the game's actual interpreter and game mechanics, not for normal CPython style.

## Source priority

Use these sources when changing game logic:

1. **Wiki Tooltips Code** — primary reference for available built-ins, return values, and tick costs:
   https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips_Code
2. **The Farmer Was Replaced Wiki mechanics pages** — primary reference for crop and unlock mechanics:
   https://thefarmerwasreplaced.wiki.gg/
3. **thefarmerwasreplaced.com** — secondary source for strategies and examples:
   https://thefarmerwasreplaced.com/
4. **Steam community discussions** — useful for optimization ideas, but treat them as community observations rather than API guarantees:
   https://steamcommunity.com/app/2060160/discussions/0/601918052458758357

If sources disagree, prefer the current in-game behavior and current Tooltips Code documentation. Do not copy a community optimization into production logic without checking whether the assumption is safe.

## Repository architecture

Keep the existing modular design.

- `main.py`: upgrade-driven orchestration.
- `config.py`: tuning knobs and scheduling constants.
- `farm.py`: normal mixed farming, companions, watering, fertilizer, sunflowers, and energy.
- `workers.py`: multi-drone worker pool, chunking, and hats.
- `pumpkin.py`: pumpkin planting, patching, readiness checks, and harvest.
- `cactus.py`: cactus planting, readiness checks, sorting, and harvest.
- `maze.py`: persistent Maze reuse using the reference tree-rebalancing strategy.
- `utils.py`: shared movement, affordability, watering, and world-size helpers.
- `unlocks.py`: upgrade target selection, cost analysis, resource focus, and unlock actions.
- `production.py`: maps required resources to normal/special production jobs and resolves producer prerequisites.
- `bench_maze.py`: all Maze benchmark implementations/modes.
- `bench_maze_run.py`: Maze simulation matrix and benchmark orchestration.

Prefer extending an existing module over adding logic to `main.py`.

Do not duplicate movement, affordability, watering, or worker-pool logic when an existing helper already covers the same behavior.

## The language is not CPython

The game uses a custom Python-like interpreter.

Do not introduce normal Python features just because they work in CPython.

Avoid unsupported or risky constructs such as:

- classes
- lambdas
- comprehensions
- generators
- `async` / `await`
- decorators
- ternary expressions
- named arguments
- user-defined `*args` or `**kwargs`
- standard-library dependencies
- string/list/dict/set methods that are not documented by the current game tooltips

Prefer the simple language already used by this repository:

- `def`
- `if` / `elif` / `else`
- `for`
- `while`
- `range`
- tuples
- lists
- dictionaries
- sets
- basic arithmetic and comparisons

Imports between game files are already part of this repository's design. Preserve the current import structure unless there is a concrete reason to change it.

## Performance model

Game performance is primarily about **ticks and movement**, not source-code line count.

According to the Tooltips Code documentation, many physical actions cost about 200 ticks when they succeed, including operations such as:

- `move()`
- `plant()`
- `harvest()`
- `till()`
- `swap()`
- `change_hat()`
- `spawn_drone()`

Many observations such as `measure()`, `can_harvest()`, `get_entity_type()`, `get_ground_type()`, and position checks cost only about 1 tick.

Therefore:

- Prefer a cheap check when it can avoid an unnecessary expensive action.
- Avoid unnecessary repositioning.
- Keep work spatially local where possible.
- Use snake/chunk traversal instead of repeatedly returning to the origin.
- Do not call `change_hat()`, `clear()`, or `spawn_drone()` more often than useful.
- Do not optimize for fewer Python statements if it causes more movement or game actions.
- Use `quick_print()` for diagnostics instead of `print()` when smoke output is not needed.

When making a performance change, prefer measuring with `get_tick_count()`, `get_time()`, or `simulate()` instead of assuming that the shorter implementation is faster.

## Multi-drone rules

Use multi-drone execution aggressively when the work can be split safely.

Important repository rule:

**Do not limit parallelism by the number of different hats.**

Hats may be reused. `max_drones()` determines the useful upper bound.

The worker pool in `workers.py` intentionally cycles through hats and uses as many drones as available. Preserve that behavior.

Other drone rules:

- All drones are equal; there is no special main drone from the game's perspective.
- A drone spawned with `spawn_drone()` starts at the spawning drone's current position.
- Drones do not collide with each other.
- Each drone has its own memory.
- Globals are not shared between drones.
- Arguments passed to another drone are copied.
- Use return values plus `wait_for()` when data must come back to the caller.
- Avoid having several drones mutate the same tile unless the operation is intentionally race-safe.
- Spawning a drone itself costs time, so do not spawn one for tiny operations.
- If work is already divided into independent chunks, use all useful drones up to `max_drones()`.

Prefer chunk ownership, as currently used by `farm.py`, over multiple drones repeatedly visiting the same area.

## World movement

Outside special mechanics, moving past a farm edge wraps to the opposite side.

`utils.move_to()` intentionally uses the shortest wrap-around route.

Do not replace it with naive coordinate walking unless the mechanic requires it.

Exception: while wearing `Hats.Dinosaur_Hat`, edge wrapping is disabled. A dinosaur implementation must not assume that `utils.move_to()` is safe without adapting the movement logic.

Always remember:

- X starts at 0 in the west and increases eastward.
- Y starts at 0 in the south and increases northward.
- `till()` toggles between grassland and soil, so check the current ground before calling it.
- `harvest()` can destroy an entity that is not ready, so use `can_harvest()` unless destruction is intentional.
- `set_world_size()` clears the farm and resets position.

## Resource handling

Before planting or unlocking expensive things, use the existing affordability helpers.

Prefer:

`utils.can_afford(thing)`

over open-coded inventory checks when the game exposes the cost through `get_cost()`.

Do not assume costs are constant across upgrades.

Do not spend reserved resources without considering the configuration in `config.py`.

In particular, preserve the existing relationship between fertilizer and Weird Substance stockpiling for mazes unless intentionally redesigning it.

## Upgrade-driven production

The repository no longer schedules Pumpkin/Cactus/Dinosaur/Maze from fixed cycle counters.

The main loop must remain driven by the next upgrade's live `get_cost()` requirements.

### Upgrade frontier

`config.AUTO_UNLOCKS` defines progression order. `unlocks.next_target()` may consider all already-started upgrade lines plus the first never-unlocked entry, but must not jump beyond that frontier.

Within the candidate set, prefer the smallest remaining total resource cost. This lets cheap current levels compete without maxing one line before progressing to the next feature.

Treat `{}` from `get_cost(unlock)` as maxed. Keep compatibility with `None` where older game behavior may still surface it.

Do not cache unlock costs globally; upgrade costs are level-dependent.

### Resource focus

`config.RESOURCE_PLANS` intentionally follows the resource order/priorities from:

https://github.com/Thorrdu/the-farmer-was-replaced/blob/main/parameters.py

The resource score is based on Thorrdu's `priority_crop()` concept:

`score = (current / required) / priority`

but `required` must come from the selected upgrade's current `get_cost()` dictionary, not from static stockpile targets.

Lower score means higher production focus. Preserve `RESOURCE_PLANS` order as the deterministic tie-breaker.

`production.py` owns dispatch:

- Power/Hay/Wood/Carrot -> normal farm focus
- Pumpkin -> Pumpkin full-field job
- Cactus -> Cactus full-field job
- Bone -> Dinosaur job
- Gold -> Maze job

Before starting a producer, inspect `get_cost(producer)` and farm missing producer inputs first. Full-field Pumpkin/Cactus requirements must account for the number of tiles they need to plant.

Gold is special: when the Maze cannot start because Weird Substance is missing, keep running fertilized normal farming until `maze.can_start()` is true.

After Pumpkin, Cactus, or Dinosaur full-field jobs, restore the permanent sunflower edges immediately. Gold/Maze is the exception: do not rebuild sunflowers between consecutive Gold-focused Maze runs.

If an `Unlocks.Expand` purchase changes `get_world_size()`, rebuild the entire normal layout and sunflower cache because edge coordinates changed.

Detailed rationale and source references live in `AGENT_NOTES.md`.

## Sunflowers and power

Sunflower harvesting has special rules.

- `measure()` returns the sunflower's petal count.
- If at least 10 sunflowers exist, harvesting a sunflower with the current maximum petal count gives the large power bonus.
- Harvesting a lower-petal sunflower can lose that bonus opportunity.
- After every harvest, recompute the current maximum before harvesting another sunflower.
- Power speeds drone execution.

The current design keeps sunflower harvesting centralized in `farm.refresh_energy()`.

Do not make normal tile farming harvest or replant sunflowers independently. Worker drones do not share globals, so they cannot safely maintain the caller's petal cache.

The permanent left/top sunflower L uses a petal cache:

- rebuild workers return `[x, y, petals]` records
- the caller merges those return values into `_sunflower_petals`
- `refresh_energy()` determines the maximum from the cache without rescanning the whole L
- only cached positions at the current maximum are visited
- after harvesting, replant immediately, call `measure()`, update that cache entry, and recompute the maximum
- if the current maximum is not ready, do not harvest a lower petal count
- keep 7-petal sunflowers in the cache

If the cache no longer matches the farm, rebuild it through `rebuild_sunflowers()` rather than trying to synchronize globals across drones.

Sunflower strategy references are documented in `AGENT_NOTES.md`.

## Pumpkins

Pumpkins need correctness before aggressive optimization.

Relevant mechanics:

- Pumpkins require soil.
- Fully grown pumpkins can merge into a giant pumpkin when the square is complete.
- A grown pumpkin can die and become `Entities.Dead_Pumpkin`.
- Planting a new pumpkin on a dead pumpkin replaces it; harvesting the dead pumpkin first is unnecessary.
- `can_harvest()` is false on dead pumpkins.
- Giant pumpkin yield improves with size, with the full multiplier reached at size 6 and above.

The current implementation scans and patches the field until every required tile is ready, then harvests.

Preserve the patch-and-wait behavior unless the replacement has equivalent correctness.

### Pumpkin `measure()` optimization

The Tooltips documentation describes `measure()` on pumpkins as returning a mysterious number.

A Steam community discussion reports that equal values can be used as a fast indication that distant tiles belong to the same merged pumpkin, including with directional `measure(direction)` and normal farm wrap-around.

However, the same discussion notes that the value should not be treated as a mathematically guaranteed globally unique ID.

Therefore:

- it is acceptable as an optimization or fast-path
- do not make correctness depend solely on uniqueness unless the failure mode is acceptable
- retain a robust fallback when practical

## Cactus

Cactus logic depends on ordering.

- Cactus sizes are 0 through 9.
- `measure()` reads the current cactus size.
- `measure(direction)` reads a neighboring cactus.
- `swap(direction)` swaps adjacent entities.
- For a cactus to be sorted, north/east neighbors must be greater than or equal and south/west neighbors must be less than or equal.
- A harvest can recursively spread through a fully grown sorted field.
- Harvesting `n` cacti together yields `n ** 2` cactus.

The current code sorts rows and columns separately using adjacent swaps. Keep sorting phases race-free: parallel row workers may own different rows, and parallel column workers may own different columns, but do not run row and column mutation phases concurrently.

## Mazes

Production `maze.py` uses a persistent reference-style tree-rebalancing strategy, based on:

https://pastebin.com/KzGvn6nc

Important rules:

- The first Gold-focused run creates and fully maps one fresh loop-free Maze.
- Consecutive Gold runs reuse the same Maze and in-memory tree.
- Do not rebuild sunflowers between Gold -> Gold iterations.
- When leaving Gold, call `maze.reset()` before clearing/rebuilding the normal farm.
- Farm expansion invalidates the Maze tree and must reset it.
- After the configured reuse limit, route to the final Treasure, harvest, reset, and create a new Maze next time.
- Greedy shortcuts and tree rebalancing are enabled according to the constants in `config.py`.
- Node dictionaries are cyclic through parent/child references. Never compare whole nodes with `==` or `!=`; compare coordinates or other scalar identifiers.

Benchmark naming convention for every future benchmark topic:

- `bench_<name>.py` contains every implementation/mode being compared.
- `bench_<name>_run.py` owns simulation matrices, seeds, globals, `simulate()` calls, and aggregation.

For Maze benchmarks use only:

- `bench_maze.py`
- `bench_maze_run.py`

Do not split one strategy into a separate benchmark file. Add it as another mode in the shared benchmark implementation file.

The reference architecture was promoted to production because it was the fastest tested strategy across all completed 8x8 workloads and the completed 16x16/25 workload. Detailed measurements are recorded in `AGENT_NOTES.md`.

## Dinosaurs

Only add or change dinosaur logic with the special movement rules in mind.

- Equip with `change_hat(Hats.Dinosaur_Hat)`.
- Only one drone can wear the Dinosaur Hat.
- Apples consume cactus automatically.
- Moving away from an apple eats it and grows the tail.
- `measure()` on an apple returns the next apple coordinates.
- The dinosaur cannot wrap across farm edges.
- Moving into the tail can fail.
- Unequipping the hat harvests the tail.
- A tail of length `n` yields `n ** 2` bones.

Because dinosaur movement differs from normal farm movement, do not blindly reuse wrap-aware movement helpers.

## Concurrency safety

Before parallelizing a loop, identify what each drone reads and writes.

Good candidates:

- independent columns
- independent rows
- disjoint X chunks
- read-only scans that return results
- planting/harvesting where every worker owns a distinct region

Risky candidates:

- workers watering or fertilizing the same tile
- workers harvesting the same entity
- concurrent row and column cactus sorting
- multiple workers modifying a shared companion target
- algorithms that expect shared globals

If a job cannot be made race-safe, prefer a smaller number of larger chunks or keep the critical phase serial.

## Code style

Match the existing code.

- Use descriptive snake_case names.
- Keep functions small and game-purpose-specific.
- Keep configuration in `config.py`.
- Keep reusable game helpers in `utils.py`.
- Keep worker orchestration in `workers.py`.
- Use comments for game-mechanic reasons, not for obvious syntax.
- Avoid clever CPython idioms.
- Prefer explicit control flow that is easy to inspect while the game is running.
- Preserve `if __name__ == "__main__":` entry points where used.

Do not refactor unrelated modules while implementing a focused change.

## Validation

Normal CPython execution cannot validate game behavior because the game provides custom built-ins such as `Entities`, `Items`, `move()`, and `spawn_drone()`.

When available, use:

`python -m py_compile *.py`

only as a syntax check. Passing it does **not** prove that the code is supported by the game interpreter.

For behavior changes, validate in the game or with the game's `simulate()` functionality.

For performance changes, compare ticks or simulation time before and after.

At minimum, reason through these cases for any changed farming job:

- insufficient resources
- partially unlocked game state
- minimum useful world size
- current maximum world size
- one drone available
- several drones available
- a worker spawn returning `None`
- empty tile
- wrong entity on a tile
- unripe entity
- dead pumpkin where applicable
- farm expansion during a long-running program

Do not cache `get_world_size()` globally. The farm can expand while the program is running.

## Change checklist

Before finishing a change:

1. Read the relevant existing module before editing it.
2. Check the current Tooltips Code API for every new game built-in used.
3. Check the relevant crop/mechanic documentation.
4. Do not introduce unsupported CPython features.
5. Preserve module boundaries unless the architecture itself is being changed.
6. Use `max_drones()` where safe parallelism is useful; never cap workers by unique hats.
7. Verify that workers do not rely on shared memory.
8. Verify that workers do not race on the same tiles.
9. Avoid unnecessary 200-tick actions.
10. Re-check resource costs and unlock-dependent behavior.
11. Run a syntax check if possible.
12. Prefer an in-game or `simulate()` validation for behavior.
13. For optimization work, compare measured ticks/time.
14. Update documentation if the repository architecture or assumptions change.
