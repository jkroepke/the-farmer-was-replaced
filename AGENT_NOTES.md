# The Farmer Was Replaced — Agent Notes

## Current architecture

The automation is split into modules:

- `main.py` — upgrade-driven orchestration
- `config.py` — tuning knobs
- `utils.py` — movement, affordability, water helpers
- `workers.py` — multi-drone worker pool and hats
- `farm.py` — normal mixed farm, sunflowers, carrots, resources, polyculture
- `maze.py` — fresh maze creation + wall-following solver
- `pumpkin.py` — full-field giant pumpkin job
- `cactus.py` — full-field cactus job
- `unlocks.py` — upgrade selection, cost analysis, resource focus, unlock purchases
- `production.py` — resource-to-production dispatcher and prerequisite resolution
- `benmain.py` — simulation benchmark controller for maze strategies
- `benchmaze.py` — benchmark worker implementing fresh/reuse routing variants

Always use `import module`, not `from module import ...`.

All code that should only run when the file itself is executed should be behind:

```python
if __name__ == "__main__":
    ...
```

## Multi-drone rules

Use as many drones as `max_drones()` permits when useful.

Do NOT limit drone count to the number of available hats.

Hats may repeat. `workers.py` assigns hats cyclically.

Prefer **contiguous chunks** of the map rather than one tiny task per column/tile. This avoids drones spending most of their time flying to and from their assigned work.

## Normal farm

Current farm is 16x16.

Sunflowers are intended to be permanent and cheap to reach:

- left edge
- top edge

Because the map wraps, the top edge is one `South` move away from `(0,0)`.

A carrot support L sits directly inside the sunflower L.

Water production is high (~3.2/s) and fertilizer production is high (~0.8/s), so both may be used aggressively.

## Upgrade and resource planner

The main loop is **not cycle-driven anymore**. Do not reintroduce fixed counters such as `PUMPKIN_EVERY`, `CACTUS_EVERY`, or `DINOSAUR_EVERY`.

The current planner works in two stages.

### 1. Choose the next unlock

`config.AUTO_UNLOCKS` defines progression order:

1. `Unlocks.Speed`
2. `Unlocks.Expand`
3. `Unlocks.Watering`
4. `Unlocks.Grass`
5. `Unlocks.Cactus`
6. `Unlocks.Plant`
7. `Unlocks.Carrots`
8. `Unlocks.Trees`
9. `Unlocks.Pumpkins`
10. `Unlocks.Polyculture`
11. `Unlocks.Dinosaurs`
12. `Unlocks.Megafarm`

To avoid skipping progression dependencies, `unlocks.next_target()` only considers:

- every upgrade line that has already been unlocked at least once
- plus the first entry in the list that has never been unlocked

Within that candidate set, selection is cost-driven:

1. lowest **remaining total cost** wins (`sum(max(required - inventory, 0))`)
2. lowest nominal total `get_cost()` wins a tie
3. configured unlock order wins the remaining tie

`get_cost(unlock)` is queried every planner loop. Do not cache upgrade costs because they change with levels. Current game behavior/documentation returns `{}` for an upgradeable unlock that is already maxed.

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

If Gold is needed but a Maze cannot start yet, normal fertilized farming is used to generate Weird Substance until `maze.can_start()` succeeds.

After Pumpkin, Cactus, or Dinosaur full-field jobs, rebuild the permanent sunflower edges immediately. **Gold/Maze is the exception:** consecutive Gold runs must not rebuild sunflowers between mazes.

If `Unlocks.Expand` changes `get_world_size()`, clear/rebuild the layout and sunflower cache because the top-edge coordinates changed.

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

`get_time()`, `get_tick_count()`, and `quick_print()` are free.

Use `get_time()` for wait intervals instead of repeatedly moving over the whole field.

Current tuning lives in `config.py`:

- `PUMPKIN_ID_CHECK_INTERVAL`
- `PUMPKIN_INITIAL_WAIT`
- `PUMPKIN_PATCH_INTERVAL`

## Sunflowers

Energy matters a lot because active energy doubles drone speed.

Sunflowers are permanent and live on the left and top farm edges. They should be rebuilt immediately after full-field jobs such as:

- Maze
- Pumpkin
- Cactus
- Dinosaur

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

Fresh mazes have no loops, so the current production solver can safely use a right-hand wall follower.

Gold production has a special restore rule:

- while Gold remains the selected resource, `production.run_gold()` must **not** rebuild the sunflower L after each fresh Maze
- a subsequent non-Gold producer will restore/clear what it needs

This fixes the obvious waste where a Maze run was followed by sunflower planting only for the next Gold iteration to immediately `clear()` the farm again.

### Maze-reuse benchmark

Maze reuse is currently being evaluated rather than enabled blindly in production.

`benmain.py` calls `simulate("benchmaze", ...)` with identical seeds and start inventories. Because every strategy solves the same number of Treasures, the runtime returned by `simulate()` is directly comparable.

`benchmaze.py` currently contains five modes:

0. fresh Maze + right-hand wall follower (current-production baseline)
1. reused Maze + dynamic BFS on the discovered/opening graph
2. reused Maze + initial spanning tree + greedy shortcut attempts
3. reused Maze + tree + greedy + lazy parent rebalancing
4. reused Maze + tree + greedy + rebalancing plus a source-like full depth reindex

Default benchmark matrix:

- world sizes: 8 and 16
- solves per Maze workload: 25, 100, 250
- seeds: 1, 2, 3
- simulation speedup: 64
- greedy begins after solve 30
- rebalancing is limited to the first 140 solves

The benchmark intentionally uses oversized resources so it measures routing/maze overhead rather than farming prerequisites.

Set `BENCH_VERBOSE = True` in `benmain.py` to have each simulated worker additionally `quick_print()` its ending `get_tick_count()` and `get_time()`. `quick_print()`/the timing calls are free according to the game timing model, so this is useful for diagnosis without adding benchmark actions.

### Tree-rebalancing source

- **npcompl33t — `maze single - tree rebalancing`**  
  https://pastebin.com/KzGvn6nc  
  Community leaderboard implementation. Relevant ideas used for the benchmark are: map the initial loop-free Maze as a tree, route using tree metadata, begin direct greedy shortcut attempts after a number of solves, and rotate/reindex the tree when newly opened walls provide substantially shallower adjacency.

The source implementation performs a full `reindex_tree()` after some rotations. Benchmark modes 3 and 4 deliberately separate **rebalancing itself** from **full-tree reindex overhead** so we can determine which part affects performance on our 16x16 workload.

Do not promote a reuse strategy into production solely because it is conceptually shorter or more complex. Compare identical seeds and choose based on measured runtime/ticks.

## Future optimization ideas

- Measure job timings with `get_tick_count()` and `get_time()`.
- Tune pumpkin initial/patch waits empirically.
- Consider using fertilizer during Cactus jobs.
- If maze reuse becomes desirable, use sets/dicts for visited-state pathfinding.


## Dinosaur

The Dinosaur Hat is special:

- `change_hat(Hats.Dinosaur_Hat)` equips it.
- `clear()` wipes the farm **and resets the drone to the Straw Hat**, so always call `clear()` before equipping the Dinosaur Hat.
- There is only **one** Dinosaur Hat.
- Do not put `Hats.Dinosaur_Hat` into the normal repeating worker hat pool.
- Equipping the hat buys/places an Apple if enough Cactus is available.
- Moving away from a tile containing an Apple consumes it and grows the tail by one.
- A new Apple is then bought and placed at a random location if affordable.
- Apples cannot spawn on blocked/planted locations.
- `measure()` on the **current Apple**, before moving away and consuming it, returns the `(x, y)` position of the next Apple.
- Moving onto the dinosaur's own tail fails and returns `False`.
- The tail end moves away during normal movement.
- When the tail fills the whole farm, movement is no longer possible.
- Removing the Dinosaur Hat harvests the tail.
- A tail of length `n` yields `n**2` `Items.Bone`.
- Dinosaur movement cannot wrap around the farm boundary.
- Base Dinosaur `move()` cost is 400 ticks and becomes ~3% cheaper per collected Apple.

### Current Dinosaur strategy

`dinosaur.py` uses one drone and clears the farm first.

For the current even-sized 16x16 farm it follows a Hamiltonian cycle:

1. Start at `(0,0)`.
2. Move up the left column.
3. Snake through columns `1..N-1`, keeping the bottom row open.
4. Move onto the bottom row at the far right.
5. Move West across the bottom row back to `(0,0)`.
6. Repeat the same cycle.

This is intentionally safer than greedily pathfinding directly to the next Apple. A direct shortest path can cut across the current tail and trap the snake.

On a Hamiltonian cycle, every Apple will eventually be visited while the snake keeps a safe ordering around the cycle.

The implementation stops when:

- `move()` fails, normally meaning the snake has filled the map, or
- a complete Hamiltonian cycle consumes no Apple, meaning no reachable/new Apple currently exists (for example because Cactus ran out).

In either case the code removes the Dinosaur Hat to harvest the accumulated tail as Bones.

### Future Dinosaur optimization

`measure()` on the current Apple exposes the next Apple position **before the move that eats the current Apple**. This could be used to reduce travel, but only if a shortcut algorithm proves that the shortcut cannot intersect the existing tail. Until then the Hamiltonian cycle is the safe default.

For small experiments, `set_world_size(n)` can temporarily shrink the farm (minimum 3) and also clears it. Do not use that in normal production automation unless explicitly desired, because it changes the active farm size for the running program.
