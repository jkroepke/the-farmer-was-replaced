# Flekay reference research

Source:

- upstream: `Flekay/The-Farmer-Was-Replaced`
- pinned upstream revision: `567e0ab6f96305cd6c9a05fd5eea2917449c2407`
- revision date: 2026-01-28
- local mirror: `external/flekay-the-farmer-was-replaced/source/`

The upstream repository has not advanced beyond the revision already mirrored locally as of 2026-09-19. The local mirror is therefore current.

## High-value benchmark ideas not yet exhausted locally

### Spawn topology

Flekay's `Movement/line_formation` benchmark reports:

```text
for_all.py              25006 runtime ticks
for_all_dual.py         16224 runtime ticks
for_all_sync_col/row.py 16224 runtime ticks
```

These are historical upstream measurements, but they reinforce the locally measured `spawn-v4` result that serial parent spawning is expensive.

Important topology candidates for a current-runtime 32-drone benchmark:

- one serial spawner
- two-spawner / dual fan-out
- Flekay hardcoded powers-of-two fan-out
- Jarvan-style powers-of-two `spawn_all`
- locally measured balanced binary tree

Do not assume the balanced binary tree is globally optimal merely because it beat serial spawning. Compare the dependency depth and positioning cost of these topologies directly.

### Wrapped movement implementation

Flekay's 10x10 wrapped movement benchmark reports:

```text
gen_move_to          setup 0.0050s / 450 ticks per benchmark
move_to              setup 0.0001s / 630 ticks per benchmark
navi_pos_to_pos_func setup 4.8068s / 271 ticks per benchmark
navi_pos_to_pos      setup 6.6733s / 270 ticks per benchmark
navi_to_deltalist    setup 0.0069s / 240 ticks per benchmark
navi_to_dict         setup 0.0908s / 330 ticks per benchmark
navi_to_list         setup 0.0016s / 270 ticks per benchmark
```

The strongest source candidate is the precomputed delta-list approach.

Re-benchmark at 32x32 because the upstream numbers are 10x10 and old-runtime. Measure both:

- cold setup + N destinations
- warm repeated destinations with setup amortized

Compare against current `utils.move_to`. This may matter for Maze return-to-origin, Sunflower target routing, Pumpkin repair targets, and companion routing.

Also test passing known current coordinates into movement helpers rather than calling `get_pos_x()` and `get_pos_y()` again; Flekay records each position getter as 1 tick.

### Multi-target routing break-even

Flekay's pathfinding benchmark demonstrates that route optimization can cost more than the movement it saves.

Recorded totals:

```text
5 points:
  unordered        5702
  nearest-neighbor 5030
  two-opt          5269

20 points:
  unordered        11802
  nearest-neighbor 10155
  two-opt          20714

60 points:
  unordered        21602
  nearest-neighbor 30855
  two-opt         141112
```

Therefore benchmark route planning by target-set size and shape rather than adopting nearest-neighbor universally.

Recommended current-runtime sizes:

- 5
- 10
- 16
- 20
- 32
- 60

Recommended distributions:

- uniform/random
- clustered
- one row/column
- toroidal edge-heavy

This is directly relevant to Sunflower petal buckets and Pumpkin repair lists.

The Flekay README also contains a `divinepath` row with unusually strong totals, but the pinned source benchmark does not import a `divinepath` implementation and no corresponding source file was found. Treat those numbers as non-reproducible until the missing implementation is located.

### Interpreter hot-loop extensions

Current local `bench_ticks` already covers integer-vs-tuple dict keys, membership, queue cursor vs `pop(0)`, append, and list concatenation.

Flekay provides additional current-runtime hypotheses worth re-measuring:

- direct user-function call vs function stored in a variable
- direct module function vs stored/dynamic module function
- `list.remove()`, `list.pop(index)`, and `list.insert()` scaling
- literal/list/set/dict construction and copying
- slice cost
- recursive tuple/list comparisons
- `pass` vs `continue` in spin loops

Historical Flekay tick model says:

```text
pass      1 tick
continue  0 ticks
num_items 1 tick
measure   1 tick
get_entity_type 1 tick
get_pos_x / get_pos_y 1 tick each
```

Several local Maze synchronization loops currently use `while ...: pass`; benchmark before changing them because busy loops can also reduce effective `simulate()` speedup.

### Maze shared vector flow field

Flekay's strongest Maze reference is `Shared_Vector_Flow_Field.py`.

Key ideas:

- map the initial tree Maze once
- build one BFS flow/distance field toward a fixed base
- derive current->target travel by stitching the current and target paths where they share the route toward the base
- probe previously closed walls during travel
- incrementally repair the graph/flow field when a wall disappears after Treasure relocation

Historical 10x10 single-drone averages:

```text
20 treasures   9.6710s
100 treasures 25.9778s
300 treasures 54.2558s
```

The exact numbers are not comparable to the current 32-drone 4x4/5x5 leaderboard, but the incremental-routing architecture remains relevant.

High-priority Maze ablation:

- current map+BFS recomputed per target
- shared base flow field + intersection stitching
- shared flow field + incremental wall-removal repair

Run at the exact 9863168-Gold leaderboard target after a small screen.

### Sunflower 7-petal simplification

Flekay's old single-drone throughput table reports:

```text
power-fart 6600 items/min
power-spam 6310
power-path 3840
power-hash 3470
power-runs 2540
```

`power-fart` aggressively rerolls each Sunflower to 7 petals and then uses an extremely simple harvest/replant loop. `power-path` pays for petal buckets plus nearest-neighbor routing.

This suggests a modern benchmark family:

- dumb harvest/replant
- fixed 7-petal reroll + dumb loop
- normal petal-order buckets
- petal-order + nearest-neighbor within bucket
- fixed local Sunflower per worker / no dedicated Sunflower worker

Test with current 32-drone Farm because the old single-drone item/min values are not directly transferable.

### Pumpkin repair-list implementation

Flekay/Jarvan reinforces the useful policy:

- initial full planting
- record only failed/unready tiles
- revisit only failures
- when only a few remain, finish aggressively with Water/Fertilizer

However, Jarvan removes entries from `dead_pumpkins` while iterating. Flekay's own tick model says list `remove()` scales with list length.

Benchmark repair-list representations:

- remove-in-place
- cursor + compact into a new list
- swap/pop-end when ordering is irrelevant
- fixed index/bitset-like state if practical

This isolates interpreter overhead from the already useful revisit-only-failures farming policy.

### Loop/scan representation

Flekay's 10x10 loop-around benchmark reports very low per-cycle interpreter cost for precomputed direction sequences:

```text
map_adv   setup 610 ticks / 1 tick per benchmark
map_hard  setup   8 ticks / 1 tick per benchmark
map_light setup 117 ticks / 1 tick per benchmark
map_inline setup 15 ticks / 12 ticks per benchmark
```

Physical movement still dominates at 200 ticks per successful move, so this is lower priority. It may matter only in extremely repeated persistent-worker scans or non-moving computation-heavy traversal logic.

## Priority order

Recommended order for new local work:

1. exact Maze `maze-v3` binary-tree validation already queued
2. spawn topology shootout: binary vs Flekay powers-of-two vs dual-spawner
3. wrapped movement cold/warm benchmark at 32x32
4. Maze shared-flow-field / incremental-repair ablation
5. Sunflower 7-petal simplification benchmark
6. multi-target routing break-even by target count
7. extend `bench_ticks` with function/module/list/spin-loop costs
8. Pumpkin repair-list data-structure ablation

Cactus and Dinosaur already have stronger local domain-specific benchmark suites; Flekay is more useful there as corroborating strategy evidence than as the next benchmark source.
