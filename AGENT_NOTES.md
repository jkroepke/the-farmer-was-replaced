# The Farmer Was Replaced — Agent Notes

## Current architecture

The automation is split into modules:

- `main.py` — orchestration and periodic special jobs
- `config.py` — tuning knobs
- `utils.py` — movement, affordability, water helpers
- `workers.py` — multi-drone worker pool and hats
- `farm.py` — normal mixed farm, sunflowers, carrots, resources, polyculture
- `maze.py` — fresh maze creation + wall-following solver
- `pumpkin.py` — full-field giant pumpkin job
- `cactus.py` — full-field cactus job
- `unlocks.py` — automatic unlock purchases

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

Sunflowers should be rebuilt immediately after full-field jobs such as:

- Maze
- Pumpkin
- Cactus

Do not harvest arbitrary sunflowers.

With at least 10 sunflowers, harvest only a sunflower with the current maximum petal count to preserve the 8x energy bonus.

## Maze

Fresh mazes have no loops, so the right-hand wall-following solver is sufficient.

Maze reuse is intentionally not enabled yet because reused mazes can gain loops and require a more robust visited/pathfinding solver.

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
