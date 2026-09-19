# AGENTS.md

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

For generic community implementation lookups across all mechanics, also consult:

`docs/REFERENCES.md`

That file contains reusable external codebases that may provide alternative algorithms, data structures, and benchmark candidates. Treat them as idea/reference sources, not as authoritative game documentation.

### External reference snapshot policy

Every external reference used for research must also have a local provenance entry under:

`external/<name>/`

Required layout:

```text
external/<name>/
├── README.md
└── source/
```

`README.md` must contain:

- canonical upstream URL
- source type (GitHub, GitLab, Pastebin, Steam, Reddit, website, etc.)
- retrieval/review date
- upstream revision/commit when one exists
- license/redistribution status when known
- a concise summary of the useful ideas and any known validity warnings

`source/` is reserved for the **unchanged upstream snapshot**. Never clean up, reformat, translate, or mix local modifications into the snapshot.

Copy the upstream source verbatim when redistribution is permitted by an applicable license/permission or when the user supplied the source content directly. Preserve the upstream license and attribution files with the snapshot.

When a complete verbatim snapshot cannot legally be redistributed, or the source cannot currently be retrieved, still create the directory and add `source/UPSTREAM.md` containing provenance, revision information, and the reason the body was not mirrored. Do not invent missing source.

Local analysis, corrections, benchmark notes, and warnings belong in `external/<name>/README.md`, never inside the mirrored `source/` tree.

When a reference materially influences production code or a benchmark, prefer linking the corresponding local `external/<name>/` entry from the mechanic-specific documentation.


## Conversation memory

Long-running ChatGPT/agent conversations can exceed their useful context window. Persist durable project knowledge in the repository instead of relying on chat history.

Use:

`memory/<topic>.md`

Rules:

- `<topic>` must be a single word, for example `maze.md`, `carrots.md`, `drones.md`, or `pumpkins.md`.
- Prefer updating an existing topic file instead of creating another file for closely related knowledge.
- Keep the number of memory files small. Group related findings under the same stable topic.
- Persist conclusions that are useful for future work: confirmed mechanics, design decisions, rejected approaches and why they failed, important assumptions, and open research questions. Benchmark measurements themselves belong in `bench/<item>.md`.
- Do not use memory files as raw chat transcripts. Summarize the durable knowledge needed to continue the work later.
- Clearly distinguish verified facts, benchmark-derived conclusions, hypotheses, and unresolved questions. Keep the measurements that support those conclusions in `bench/<item>.md`.
- When a benchmark changes a durable decision, summarize the takeaway in memory and link to the canonical `bench/<item>.md`; do not copy the result table into memory.
- When a conclusion belongs in a canonical mechanic document such as `docs/MAZE.md` or `docs/NORMAL_FARM.md`, update that document as well. Memory is a compact continuation aid, not a replacement for canonical documentation.
- Update the relevant memory topic during substantial research/optimization work whenever new durable knowledge appears, especially before a long conversation is likely to lose context.
- Do not store credentials, tokens, private data, or other secrets in `memory/`.

## Repository architecture

Keep the existing modular design.

- `main.py`: upgrade-driven orchestration.
- `config.py`: tuning knobs and scheduling constants.
- `farm.py`: normal mixed farming, companions, watering, fertilizer, sunflowers, and energy.
- `workers.py`: multi-drone worker pool and chunking; generic workers deliberately avoid cosmetic hat changes.
- `pumpkin.py`: pumpkin planting, patching, readiness checks, and harvest.
- `cactus.py`: cactus planting, readiness checks, sorting, and harvest.
- `maze.py`: persistent Maze reuse using the reference tree-rebalancing strategy.
- `utils.py`: shared movement, affordability, watering, and world-size helpers.
- `unlocks.py`: upgrade target selection, cost analysis, resource focus, and unlock actions.
- `production.py`: maps required resources to normal/special production jobs and resolves producer prerequisites.
- `bench_farm.py`: normal-farm, Sunflower, and external-reference benchmark implementations/modes.
- `bench_farm_run.py`: normal-farm benchmark matrix, seeds, simulation profiles, and aggregation.
- `bench_transition.py`: persistent Carrot -> Hay -> Wood -> Carrot transition implementations.
- `bench_transition_run.py`: transition benchmark profiles, seeds, simulation calls, and aggregation.
- `bench_persist.py`: full-Megafarm sync-respawn vs persistent-worker implementations.
- `bench_persist_run.py`: persistent-worker benchmark seeds, simulation calls, and aggregation.
- `bench_ticks.py`: current-runtime interpreter/tick microbenchmark modes derived from measured external claims.
- `bench_ticks_run.py`: tick microbenchmark matrix and simulation orchestration.
- `bench_reset.py`: Fastest Reset planner-policy implementations ending at `Unlocks.Leaderboard`.
- `bench_reset_run.py`: empty-state reset simulations, seeds, watchdog, and aggregation.
- `bench_maze.py`: all Maze benchmark implementations/modes.
- `bench_maze_run.py`: Maze simulation matrix and benchmark orchestration.
- `bench_spawn.py`: drone spawn/locality/topology benchmark implementations.
- `bench_spawn_run.py`: spawn topology benchmark orchestration.
- `bench_move.py`: wrapped movement implementation benchmark modes.
- `bench_move_run.py`: cold/warm 32x32 movement benchmark orchestration.
- `bench_dinosaur.py`: Dinosaur benchmark implementations/modes.
- `bench_dinosaur_run.py`: Dinosaur simulation matrix and benchmark orchestration.
- `bench_pumpkin.py` / `bench_pumpkin_run.py`: Pumpkin benchmark modes and orchestration.
- `bench_cactus.py` / `bench_cactus_run.py`: Cactus benchmark modes and orchestration.
- `bench_sunflower.py` / `bench_sunflower_run.py`: Sunflower leaderboard benchmark modes and orchestration.
- `bench_lb_wood.py` / `bench_lb_wood_run.py`: dedicated Wood leaderboard benchmark.
- `bench_lb_carrot.py` / `bench_lb_car_run.py`: dedicated Carrot leaderboard benchmark.
- `bench_lb_hay.py` / `bench_lb_hay_run.py`: dedicated Hay leaderboard benchmark.
- `bench/example.md`: required benchmark documentation template.
- `bench/farm.md`: canonical Farm, transition, persistent-worker, and Polyculture benchmark record.
- `bench/pumpkin.md`: canonical Pumpkin benchmark record.
- `bench/cactus.md`: canonical Cactus benchmark record.
- `bench/maze.md`: canonical Maze benchmark record.
- `bench/dinosaurs.md`: canonical Dinosaur benchmark record.
- `bench/runtime.md`: canonical runtime, drone-memory, spawn, movement, and tick benchmark record.
- `bench/sunflower.md`: canonical Sunflower leaderboard benchmark record.
- `bench/wood.md`: canonical Wood leaderboard benchmark record.
- `bench/carrot.md`: canonical Carrot leaderboard benchmark record.
- `bench/hay.md`: canonical Hay leaderboard benchmark record.
- `bench/reset.md`: canonical Fastest Reset benchmark record.
- `docs/NORMAL_FARM.md`: canonical Hay/Wood/Carrot, Sunflower/Power, worker-layout, references, and benchmark methodology.
- `docs/UNLOCKS.md`: canonical automatic unlock frontier, priorities, endgame goals, and reset-strategy references.
- `docs/PUMPKIN.md`: canonical Pumpkin mechanics, multi-drone strategy, references, and optimization notes.
- `docs/MAZE.md`: canonical Maze mechanics, production design, sources, and optimization notes.
- `docs/DINOSAUR.md`: canonical Dinosaur mechanics, external strategy research, and optimization notes.

Prefer extending an existing module over adding logic to `main.py`.

Do not duplicate movement, affordability, watering, or worker-pool logic when an existing helper already covers the same behavior.

## Repository code conventions

- Use `import module`, not `from module import ...`.
- Code that should execute only when a file is run directly must be guarded by `if __name__ == "__main__":`.
- Game-facing Python files must use names of at most 20 characters including `.py`.
- Keep repository-wide rules here; mechanic-specific findings belong in `memory/` or the appropriate `docs/` file.

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

The worker pool in `workers.py` intentionally avoids cosmetic hat changes and uses as many drones as available. Preserve that behavior.

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

Maze/Gold resource handling is documented in `docs/MAZE.md`.

## Upgrade-driven production

The repository no longer schedules Pumpkin/Cactus/Dinosaur/Maze from fixed cycle counters.

The main loop must remain driven by the next upgrade's live `get_cost()` requirements.

### Upgrade frontier

`config.UNLOCK_PLANS` defines progression order. `unlocks.next_target()` may consider all already-started upgrade lines plus the first never-unlocked entry, but must not jump beyond that frontier.

Within the candidate set, compare priority-weighted remaining cost. Higher-priority core progression may beat a somewhat cheaper lower-priority target, while the frontier prevents jumping past the first never-unlocked goal. Endgame goals remain in the plan with lower priority instead of disappearing from automation.

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

Gold/Maze has a persistent production lifecycle that differs from the other full-field jobs. Read `docs/MAZE.md` before changing it.

After a full-field special job, restore the normal farm only when normal production is actually needed. Consecutive special-focus runs must not rebuild normal crops merely to clear them again.

If an `Unlocks.Expand` purchase changes `get_world_size()`, rebuild the entire normal layout and sunflower cache because edge coordinates changed.

Detailed planner rationale lives in `docs/UNLOCKS.md` and durable continuation notes live in `memory/`.

## Sunflowers and power

Sunflower harvesting has special rules.

- `measure()` returns the sunflower's petal count.
- If at least 10 sunflowers exist, harvesting a sunflower with the current maximum petal count gives the large power bonus.
- Harvesting a lower-petal sunflower can lose that bonus opportunity.
- After every harvest, recompute the current maximum before harvesting another sunflower.
- Power speeds drone execution.

Production no longer uses the legacy L. Below full Megafarm (`max_drones() < world_size`) production uses the best previously measured non-L fallback: one dedicated max-petal Sunflower column plus crop chunks. At full Megafarm (`max_drones() == world_size`) production currently uses synchronous column ownership with the final two columns reserved for simple Sunflowers. Persistent-worker variants are under benchmark; see `docs/NORMAL_FARM.md` and its benchmark commit references before changing normal farming or Sunflower placement.

Do not assume the current global petal-cache/L design is optimal. Benchmark modes intentionally test integrated Sunflower rows/columns and dedicated workers without shared memory. Production changes must follow measured results from `bench_farm_run.py`.

The permanent left/top sunflower L uses a petal cache:

- rebuild workers return `[x, y, petals]` records
- the caller merges those return values into `_sunflower_petals`
- `refresh_energy()` determines the maximum from the cache without rescanning the whole L
- only cached positions at the current maximum are visited
- after harvesting, replant immediately, call `measure()`, update that cache entry, and recompute the maximum
- if the current maximum is not ready, do not harvest a lower petal count
- keep 7-petal sunflowers in the cache

If the cache no longer matches the farm, rebuild it through `rebuild_sunflowers()` rather than trying to synchronize globals across drones.

Sunflower strategy references and durable conclusions live in `docs/NORMAL_FARM.md` and `memory/farm.md`; measured results live in `bench/farm.md`.

## Pumpkins

Pumpkins need correctness before aggressive optimization.

Relevant mechanics:

- Pumpkins require soil.
- Fully grown pumpkins can merge into a giant pumpkin when the square is complete.
- A grown pumpkin can die and become `Entities.Dead_Pumpkin`.
- Planting a new pumpkin on a dead pumpkin replaces it; harvesting the dead pumpkin first is unnecessary.
- `can_harvest()` is false on dead pumpkins.
- Current `builtins.py` states that mega-Pumpkin harvest yield grows cubically with mega-Pumpkin size. Do not assume a 6x6 yield cap; compare patch sizes with measured throughput.

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

Maze mechanics, production invariants, sources, and durable optimization notes live in `docs/MAZE.md` and `memory/maze.md`.

Measured Maze and spawn-locality results live in `bench/maze.md`.

Read those files before modifying `maze.py`, Maze-related Gold production, or Maze benchmarks. Do not duplicate Maze result tables in this file.

## Main-run vs leaderboard-run architecture

Treat normal production and leaderboard submissions as different runtime
profiles. Do not force both through one defensive hot path.

### Main run

`main.py` is the normal production entry point.

Main-run implementations must remain adaptive and safe across progression:

- resources may be scarce
- unlock levels may be partial
- world size may change
- fewer than the maximum number of drones may be available
- producer prerequisites may need to be farmed first
- special jobs must return control to the upgrade-driven production loop
- affordability and state checks are required where they prevent invalid or
  wasteful actions

Normal mechanic modules such as `maze.py`, `pumpkin.py`, `cactus.py`, and
`dinosaur.py` are production implementations unless explicitly documented
otherwise.

### Leaderboard run

Leaderboard implementations are finite, challenge-specific programs.

Use this naming pattern:

```text
lb_<mechanic>.py       # optimized leaderboard implementation
lb_<mechanic>_run.py   # tiny leaderboard_run(...) launcher
```

A leaderboard implementation may and should exploit start-state guarantees
that have been verified for that exact leaderboard. Examples include:

- fixed world size
- fixed drone count
- all required unlocks already available
- very large challenge-input inventories
- fixed success target
- no requirement to return to the normal production farm

Do not carry Main-run checks into a leaderboard hot path merely for reuse.
Once a start-state property has been measured/proven for that leaderboard,
remove checks that cannot affect correctness, for example:

- `utils.can_afford()` for a cost that is guaranteed empty/covered
- repeated `num_items()` availability guards for effectively unlimited
  challenge input
- `get_cost()` / prerequisite planning
- adaptive world-size or drone-count fallbacks
- normal-farm restoration
- production stockpile/reserve logic
- configuration branches for partially unlocked progression

Keep checks that are part of the algorithm or leaderboard correctness. For
example:

- the exact leaderboard success condition and prompt termination
- a `use_item()` result when failure is used to detect a mechanic boundary
  such as Maze reuse exhaustion
- entity/state checks needed to decide the next legal action
- synchronization conditions required to avoid races

Do not assume every leaderboard has "infinite resources". Start inventories
differ by leaderboard. Use the leaderboard-specific probe/evidence in
`memory/leaderboards.md`; only specialize away a check after the relevant
start-state assumption is verified for that exact mode.

### Sharing code

Prefer sharing pure, already-measured helpers only when they do not add
production checks or abstraction overhead to the leaderboard hot path.

It is acceptable for Main and LB implementations to duplicate a small hot
loop when the LB version intentionally removes defensive branches. Optimize
leaderboard code for the fixed challenge contract, not for general reuse.

Benchmark the specialized LB implementation end-to-end at the exact
leaderboard target before promoting it.

## Benchmark execution speed

Use the highest standard acceleration for benchmark and leaderboard runners unless the benchmark explicitly studies speedup behavior itself.

Repository defaults:

- `simulate(..., speedup)` benchmarks: use `10000`
- `leaderboard_run(..., speedup)`: use `256`

Rationale:

- `simulate()` may internally fail to reach the requested acceleration when the workload is CPU-heavy, uses many drones, or contains tight wait loops, but a higher requested value minimizes unnecessary wall-clock waiting.
- `leaderboard_run()` uses the documented leaderboard-run maximum of `256`.
- Speedup is an execution/measurement input, not a strategy parameter. Do not reduce it to make an implementation look faster or slower relative to another candidate.

Rules:

- all candidates within one benchmark comparison must use the same requested speedup
- changing benchmark speedup is a material benchmark-input change and requires a `BENCH_VERSION` bump
- record the requested speedup alongside benchmark provenance when documenting results
- historical benchmark results keep the speedup they were actually measured with; never rewrite old results as if they had used the new default
- external reference snapshots keep their upstream speedup values unchanged
- only use a different speedup when there is a specific benchmark reason, and document that exception explicitly

## Benchmark output version

Every benchmark runner must define a manually bumped `BENCH_VERSION` and print it as the first benchmark output line:

```text
BENCHMARK VERSION <suite>-v<N>
```

Rules:

- bump the version whenever benchmark modes, setup, targets, seeds, simulation inputs, stopping conditions, or measured implementation behavior changes
- documentation supplied with benchmark output must record both the printed benchmark version and the benchmark commit SHA when available
- never reuse a version identifier for materially different benchmark code
- historical output without a version must be explicitly labeled unversioned and tied to its benchmark commit before drawing conclusions


## Benchmark documentation

Measured benchmark results belong only in `bench/<item>.md`. Do not store numeric result tables in `AGENTS.md`, `memory/`, or mechanic documentation.

`bench/example.md` is the mandatory documentation schema. Every benchmark document must use these top-level sections in this order:

1. `Scope`
2. `Benchmark index`
3. `Results`
4. `Interpretation`
5. `Reproduction`
6. `Notes`

Rules:

- Every benchmark runner must have a canonical home under `bench/`. Closely related runners may share one topic document, for example Farm/Persist/Polyculture in `bench/farm.md` or Spawn/Move/Ticks in `bench/runtime.md`.
- Each measured result group under `Results` must contain a provenance table with the **full Git commit SHA** of the source state that produced it.
- The source SHA must pin both runner and implementation under test. Do not substitute a later docs-only commit.
- If historical output has no recorded source SHA, label it `Unknown / not recorded` and treat it as historical/non-canonical. Never infer or guess provenance.
- Record benchmark/version, world/profile, drone count where relevant, requested simulation speedup, seeds, target/cycles, and validity condition.
- Split result groups from different source commits or materially different setups with a Markdown horizontal rule written as `-----`.
- All measured elapsed times, ticks, gains, throughput values, min/max values, and direct numeric comparisons must be presented in Markdown tables. Do not store benchmark timings in bullet lists or code blocks.
- Tables must have a header row and separator row and must keep a consistent column count.
- Keep measured facts in `Results` and derived decisions in `Interpretation`. Do not mix conclusions into raw measurement tables.
- Prefer tables in `Interpretation` and `Notes` for conclusions, rejected approaches, caveats, and open questions.
- `memory/<topic>.md` may keep durable takeaways, rejected approaches, and open questions, but it must link to the relevant `bench/<item>.md` instead of duplicating measurements.
- Mechanic docs may explain benchmark methodology, but numeric run history stays in `bench/`.
- Use stable topic filenames such as `bench/farm.md`, `bench/maze.md`, or `bench/runtime.md`; update an existing topic instead of creating one file per run.
- Whenever a benchmark suite changes materially, update its `Benchmark index` even if no new measurement exists yet.

## Benchmark layout

For every benchmark topic, use exactly:

- `bench_<name>.py` for all implementations/modes being compared
- `bench_<name>_run.py` for matrices, seeds, globals, `simulate()` calls, and result aggregation

Do not create one benchmark file per variant. Add variants as modes to the shared `bench_<name>.py`.

**Always include a source-near reference mode when a benchmark is based on an external/community implementation.** The reference may adapt setup and stopping conditions for fair measurement, but preserve the source algorithm's core path, state, and decision rules. This prevents benchmarking only our own interpretation against another one of our own interpretations.

## Dinosaurs

Dinosaur mechanics, production invariants, and external strategy research live in `docs/DINOSAUR.md` and `memory/dinosaurs.md`.

Measured Dinosaur results live in `bench/dinosaurs.md`.

Read those files before modifying `dinosaur.py`, Bone production, or Dinosaur benchmarks.

## Spawn locality

`spawn_drone(task, *args)` creates the child at the caller's current tile. Successful `move()` and successful `spawn_drone()` are both expensive physical actions, so worker placement is part of parallel setup cost.

Do not assume spawning every worker from `(0,0)` is neutral. For spatial jobs, benchmark these alternatives when setup movement is material:

- child self-positioning after all workers are spawned
- controller/parent moving to each worker start and spawning there
- spawning workers while the parent traverses an efficient route through worker starts
- hierarchical/distributed spawning when workers can safely spawn descendants

Because normal farm movement wraps at the edges, the geometric center is not inherently closer to uniformly distributed farm coordinates than any other fixed tile. Optimize against the actual worker-start set, not against visual distance from a corner.

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
