# External Community Reference Repositories

Use these repositories as generic lookup references when researching or optimizing any game mechanic in this project.

They are not authoritative API documentation. Treat them as implementation examples, optimization ideas, data-structure references, and sources for benchmark candidates.

Every reference should also have a provenance/snapshot entry under `external/<name>/`. The external directory is the canonical local archive/index; this document is the cross-reference and review summary.

Always validate assumptions against:

1. current in-game behavior
2. current Tooltips Code documentation
3. relevant current Wiki mechanics pages

## Generic lookup references

- https://github.com/MateusMarochi/the-farmer-was-replaced-codes
  - broad MIT-licensed farming reference with persistent column workers, fixed Pumpkin region layouts, parallel Maze wall-followers, Cactus sorting, Polyculture, and Dinosaur restart behavior
  - complete pinned snapshot and detailed review: `external/mateusmarochi-the-farmer-was-replaced-codes/`
- https://github.com/juritox/the-farmer-was-replaced
  - older single-drone baseline collection for resource scheduling, descending-petal Sunflowers, Pumpkin hole detection, Cactus relaxation sorting, Maze wall-following, and Dinosaur sweeps
  - pinned source/text snapshot and detailed review: `external/juritox-the-farmer-was-replaced/`
- https://github.com/ketrab2004/the-farmer-was-replaced
  - original Dinosaur implementation: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/dinosaur.py
  - pathfinding helpers: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/pathfind.py
  - queue implementation: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/queue.py
  - tail data structure: https://github.com/ketrab2004/the-farmer-was-replaced/blob/main/tail.py
- https://github.com/jdeokkim/tfwr
- https://g.j4.lc/general-stuff/the-farmer-was-replaced
  - collection of highly optimized community scripts; use as a generic implementation/benchmark reference
- https://pastebin.com/raw/i9kVXysm
- https://pastebin.com/raw/ugCFADtN
- https://pastebin.com/raw/ZkBRZv3P
  - raw community source references; inspect the actual source before deriving assumptions from them
- https://github.com/skysdottir/tfwr
  - focused Dinosaur/Snake research with indexed Hamiltonian cycles, safe shortcutting, tail-history accounting, and multiple cycle generators
  - complete pinned snapshot and detailed review: `external/skysdottir-tfwr/`
- https://github.com/nql1314/The-Farmer-Was-Replaced-AI-Code
  - broad implementation repository covering multiple mechanics; useful for alternative algorithms, data structures, and optimization ideas
  - complete pinned snapshot and detailed review: `external/nql1314-the-farmer-was-replaced-ai-code/`
- https://github.com/Flekay/The-Farmer-Was-Replaced
  - large GPL-3.0 strategy/benchmark collection with measured TFWR tick costs, reusable movement libraries, Cactus sort comparisons, Maze flow-field research, Dinosaur strategy benchmarks, Pumpkin multi-drone layouts, and Sunflower pathing experiments
  - complete pinned snapshot and detailed review: `external/flekay-the-farmer-was-replaced/`
- https://github.com/guiteixeira-io/the-farmer-was-replaced
  - small educational/classroom repository; useful mainly as provenance and simple beginner baselines rather than an optimization source
  - complete pinned snapshot and review: `external/guiteixeira-io-the-farmer-was-replaced/`
- https://github.com/sciencejiho/TFWR-Solutions
  - current September 2026 strategy architecture with isolated copied drone jobs, asynchronous persistent column lanes, sparse Pumpkin/Cactus revisits, inventory-relative scheduling, and persistent Maze graph/station planning
  - complete pinned snapshot and detailed review: `external/sciencejiho-tfwr-solutions/`
- https://github.com/msmith93/thefarmerwasreplaced
  - broad main-branch reference covering single-drone leaderboards, Megafarm/multi-drone experiments, resource planners, and a simulator-backed Sunflowers_Single optimization series
  - complete pinned snapshot and detailed review: `external/msmith93-thefarmerwasreplaced/`
- https://github.com/msmith93/thefarmerwasreplaced/tree/full_reset/full_reset
  - Fastest Reset reference with an explicit static unlock sequence and composable per-resource harvest functions

When looking for an optimization:

- search these repositories for the relevant mechanic, entity, item, or API call
- compare multiple independent implementations before assuming one pattern is optimal
- prefer measured behavior over shorter or more elegant code
- preserve a source-near benchmark mode when adapting an external implementation
- do not copy outdated assumptions about tick costs or game mechanics without re-checking them


## Review notes for newer generic references

### g.j4.lc optimized-script collection

Reference:

- https://g.j4.lc/general-stuff/the-farmer-was-replaced

Status:

- local snapshot supplied by the user and archived under `external/j4lc-the-farmer-was-replaced/source/`
- archive SHA-256: `6918c9718f9ef2b1d1ef38918e521a33103adb2ea7b16afea46718d44f7da0d0`
- contains a Fastest Reset / Zero-to-Hero implementation plus generic farming, Cactus, Maze, Pumpkin/replant, movement and farming helpers
- the upstream README explicitly says the scripts are not claimed to be optimal, so treat them as implementation references rather than a performance oracle

### Pastebin source references

References:

- https://pastebin.com/raw/i9kVXysm
- https://pastebin.com/raw/ugCFADtN
- https://pastebin.com/raw/ZkBRZv3P

Status:

- registered as generic source references
- the current research environment could not retrieve the raw Pastebin contents
- keep them as lookup sources, but do not document behavioral claims until their code has actually been read

### nql1314/The-Farmer-Was-Replaced-AI-Code

Reference:

- https://github.com/nql1314/The-Farmer-Was-Replaced-AI-Code

This repository is broad and contains useful optimization experiments for multiple mechanics, including:

- precomputed traversal/path tables
- fixed-region and grid-based drone partitioning
- parallel row/column Cactus sorting
- repeated phase-level tick measurement with `get_tick_count()`
- persistent worker-loop experiments
- Pumpkin region specialization
- Maze map caching + BFS
- Dinosaur Hamiltonian/safe-target and A* experiments

Useful files include:

- `cactus_farm_mega.py`
- `resource_farm_mega.py`
- `sunflower_farm_mega.py`
- `pumpkin_v10.py`
- `rank/pumpkin_v*.py`
- `maze_solver_ultra.py`
- `snakeV2.py`
- `.cursor/rules/dinosaur_farm_astar.py`
- `docs/PERSISTENT_DRONE_POOL.md`

#### Important validity warning: drone memory

Do **not** copy the repository's "shared memory through `wait_for()`" architecture into current production code.

The upstream repository contains evidence that this technique **did work historically**:

- reviewed upstream revision: `688325db004607563e59535a15ce94fad092ff9f` from 2025-11-01
- `docs/DRONE_SHARED_MEMORY_DISCOVERY.md` records a 2025-10-23 experiment where multiple drones call `wait_for()` on the same source drone and observe cumulative mutations of the returned list
- `archived/ref_test.py` contains the minimal reproducer used for that claim

However, current game semantics no longer support treating this as a valid mechanic:

- current Megafarm documentation says drones have separate memory
- `spawn_drone(function, *args)` operates on copies of passed arguments
- the 2025-12-04 game update explicitly says "Fixed shared memory bugs."
- the 2026-02-17 update explicitly says "Fixed another bug that allowed you to get shared memory between multiple drones."

Current references:

- https://thefarmerwasreplaced.wiki.gg/wiki/Megafarm
- https://steamcommunity.com/app/2060160/announcements/
- https://steamdb.info/patchnotes/21969917/

Therefore the nql1314 technique should be classified as a **historical engine exploit/bug**, not merely as an incorrect community assumption.

This also resolves the apparent contradiction inside the upstream repository: its ordinary globals/closure tests correctly show isolated drone memory, while its later `wait_for(source)` trick exploited a separate return-value sharing bug that the game subsequently fixed.

Treat synchronization such as:

```text
shared = wait_for(shared_source)
shared["priority"] = ...
```

as invalid for current production code.

Use `drone_mem_probe.py` / `drone_mem_run.py` when re-validating the mechanic against a future game version. Probe runner commit: `9aa2d72459e692033901e8de7569f54ae4d77af1`.


### Current runtime verification

Probe commit: `9aa2d72459e692033901e8de7569f54ae4d77af1`

Observed on 2026-09-19 with `drone_mem_run.py`:

```text
DRONE MEMORY PROBE initial []
DRONE MEMORY STEP 1 worker [1] source [] initial-view []
DRONE MEMORY STEP 2 worker [2] source [] initial-view []
DRONE MEMORY STEP 3 worker [3] source [] initial-view []
DRONE MEMORY RESULT isolated
```

This directly reproduces the historical nql1314 pattern with a source drone returning a mutable list and multiple worker drones calling `wait_for(source)`.

The current runtime result is the opposite of the historical exploit:

- each worker sees only its own mutation
- the source result remains `[]`
- mutations from one worker are not visible to later workers
- the parent-side value obtained from the same source handle remains unchanged

Therefore the historical shared-`wait_for()` behavior is **proven not to work in the current runtime for mutable list return values**.

Do not generalize this probe beyond what it tested: it directly disproves the historical list-sharing mechanism. It does not independently test every possible mutable type or every future game version.

The **persistent-worker idea itself** is still worth benchmarking. A long-lived drone can avoid repeated `spawn_drone()` cost, but any dynamic coordination must be redesigned around actual shared game state, independent worker decisions, or explicit task lifetimes rather than shared Python objects.

#### Cactus

`cactus_farm_mega.py` independently reinforces a pattern already used by this repository:

1. parallelize rows only with other rows
2. wait for the row phase to finish
3. parallelize columns only with other columns
4. trigger one chain harvest afterward

This is useful corroboration for phase-separated Cactus mutation. It does not justify running row and column swaps concurrently.

The implementation uses repeated bubble passes and substantial movement/debug output, so keep it as a structural reference rather than assuming its exact implementation is optimal.

#### Resource farming

`resource_farm_mega.py` has two useful general ideas:

- partition the farm into stable spatial regions so workers keep good locality
- keep workers alive for repeated work instead of paying `spawn_drone()` every cycle

Its dynamic priority broadcast and cross-worker companion map rely on the invalid shared-memory assumption, so those portions are not directly reusable.

A valid version of persistent workers would need workers to derive their own current priority from globally visible game state such as inventory, or use a deliberately static assignment during their lifetime.

#### Pumpkin

The repository contains many increasingly specialized Pumpkin variants, including hand-partitioned 32x32 layouts and precomputed 6x6/8x8 traversal paths.

The reusable optimization idea is:

> trade code/data size for lower hot-path computation and less repositioning.

This is especially relevant to the custom interpreter because precomputed direction tables can be cheaper than repeatedly deriving routes.

However, several variants also rely on mutable data supposedly shared between drones. Preserve the path/layout ideas separately from their synchronization mechanism.

#### Maze

`maze_solver_ultra.py` maintains a discovered wall/passability map, uses BFS over known passages, and falls back to greedy DFS-style exploration when the cached route fails.

This is a useful generic map-caching reference, but it is not a better production baseline than the separately benchmarked Maze tree-rebalancing strategy in this repository.

It also copies complete path lists during BFS (`path + [direction]`), which is expensive in the game's tick model. Use it as an algorithmic reference, not a performance reference.

#### Dinosaur

The repository contains at least two distinct Dinosaur references:

- `snakeV2.py`: Hamiltonian-index/safe-target approach with custom direct path construction
- `.cursor/rules/dinosaur_farm_astar.py`: A* + tail-following/survivability checks

Potentially useful concepts:

- precompute coordinate -> Hamiltonian index
- derive safe target positions from body length
- target an Apple directly only when cycle/body ordering permits it
- fall back toward the moving tail when a direct Apple route is unsafe

But the implementations should not be copied directly:

- the A* material assumes shared mutable drone state
- its documented Manhattan heuristic includes farm-edge wrapping, which is not valid while wearing the Dinosaur Hat
- generic A* decision cost can dominate physical movement
- `snakeV2.py` performs costly front insertion/body-list maintenance and contains source-level rough edges, so benchmark the idea rather than treating the file as an optimized oracle

For Dinosaur production, source-near benchmark modes remain mandatory before adopting any of these ideas.

## General lesson from these references

External code labeled "optimized", "mega", "ultra", or leaderboard-oriented is still only a candidate.

When reviewing a community implementation, separate:

1. the algorithmic idea
2. the data structure
3. assumptions about current game mechanics
4. interpreter/tick cost
5. actual measured throughput

Prefer a complex algorithm when it measures faster, but never assume complexity or a performance-oriented filename implies better runtime.

## Local external archive

- `external/j4lc-the-farmer-was-replaced/` — user-supplied source snapshot archived on 2026-09-19; archive SHA-256 `6918c9718f9ef2b1d1ef38918e521a33103adb2ea7b16afea46718d44f7da0d0`

- `external/mateusmarochi-the-farmer-was-replaced-codes/` — complete 21-file MIT-licensed snapshot and detailed algorithm review at `d303d81d6a3eb59887eff75ed0454a6d8f4ff5ad`
- `external/juritox-the-farmer-was-replaced/` — 15/15 upstream source/text blobs mirrored at `544bb832ffcec00aacf2c8dd5278bdb534ab674b`; 9 large media blobs are provenance-manifested because connector transfer is unavailable
- `external/skysdottir-tfwr/` — complete 8-file source snapshot and Dinosaur analysis at `e15968982e957045c5239e580e2d040a9ac73a52`; source-near behavior is benchmarked locally
- `external/ketrab2004-the-farmer-was-replaced/` — provenance and analysis at `cdbbcf32ca100237cdfc3b78783cee77722a96fd`; no redistribution license found
- `external/msmith93-thefarmerwasreplaced/` — complete main-branch source snapshot at `7fef7c327e8d0b6ef34af2fafc3e5aeaf0b89823`; includes the Sunflowers_Single simulator/iteration series and multi-drone reference implementations
- `external/nql1314-the-farmer-was-replaced-ai-code/` — complete 78-file source snapshot at `688325db004607563e59535a15ce94fad092ff9f`; detailed review distinguishes reusable algorithms from the historical shared-`wait_for()` exploit
- `external/flekay-the-farmer-was-replaced/` — complete 283-file GPL-3.0 snapshot at `567e0ab6f96305cd6c9a05fd5eea2917449c2407`; includes tick-cost tests, benchmark tables, movement libraries, and strategy variants across major mechanics
- `external/guiteixeira-io-the-farmer-was-replaced/` — complete 12-file educational snapshot at `58bd5c5ba928548bc21035006551ca93854f16b9`; only two non-empty game scripts, both minimal harvest loops
- `external/sciencejiho-tfwr-solutions/` — complete 23-file snapshot at `e0f22263d8de76691407bbcb314c0b41c3eea82e`; current-runtime architecture designed around copied drone jobs rather than shared Python memory


### msmith93/thefarmerwasreplaced full_reset

Local provenance:

- `external/msmith93-full-reset/`
- branch: `full_reset`
- revision: `28544222a2b1531c915b0646f8eb74971f4cc615`

The worked `full_reset_solution.py` uses a deliberately explicit `unlock_order` and repeatedly buys selected levels of Speed, Expand, Watering, Fertilizer, crop upgrades, Mazes, Megafarm and Dinosaurs before finishing with `Unlocks.Leaderboard`.

Reusable idea:

> Unlock progression is a strategy input, not merely a loop over every `Unlocks` enum value.

Our normal-game planner adapts that concept with a dependency frontier plus static relative priorities while continuing to use live `get_cost()` values.

Do not copy the exact upstream order as a current complete-tech-tree definition. The reference does not include newer/current hidden endgame nodes such as `Unlocks.Top_Hat` and `Unlocks.The_Farmers_Remains`.
