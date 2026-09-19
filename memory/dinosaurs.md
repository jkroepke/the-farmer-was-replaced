# Dinosaurs

## Goal

Optimize Dinosaur/Bone farming in `jkroepke/the-farmer-was-replaced`, with two separate targets:

1. normal production: stop once the required Bone deficit is covered
2. Dinosaur leaderboard: optimize cold-start time to the fixed success condition

The leaderboard success condition is:

```python
num_items(Items.Bone) >= 33488928
```

For leaderboard work, the primary metric is therefore **cold start -> 33,488,928 Bones**, not sustained Bones/min over arbitrary repeated cycles.

Current benchmark rule from the user:

- normal `simulate()` benchmarks: speedup `10000`
- real `leaderboard_run()` launchers: speedup `256`

## Verified current mechanics

Current Wiki behavior:

- only one drone can wear `Hats.Dinosaur_Hat`
- equipping the hat buys/places an Apple if enough Cactus exists
- moving away from an Apple eats it and grows the tail by one
- `measure()` while on an Apple returns the next Apple coordinates
- moving into the tail fails, but the oldest tail segment moves away during a successful move and may be entered
- Dinosaur movement does not wrap at the farm border
- removing the Dinosaur Hat harvests the tail
- base Bone payout is tail length squared; Dinosaur unlock levels increase yield/cost
- Dinosaur movement starts at 400 ticks
- each Apple reduces Dinosaur move cost by 3%, rounded down
- `can_move()` and `measure()` are cheap compared with a successful Dinosaur move, but interpreter logic still costs ticks

Primary source:

- https://thefarmerwasreplaced.wiki.gg/wiki/Dinosaurs
- https://thefarmerwasreplaced.wiki.gg/wiki/Operation_Costs

Leaderboard source:

- https://github.com/Flekay/The-Farmer-Was-Replaced/blob/main/Leaderboards.md

## Current production baseline

`dinosaur.py` uses a deterministic skyscraper-style Hamiltonian cycle:

- start at `(0, 0)`
- climb the left edge
- snake vertically through the remaining columns
- reserve the bottom row as the return lane
- repeat until movement fails
- remove the hat and harvest

This is safe and simple, but it intentionally ignores the next Apple position even though `measure()` exposes it.

The existing `bench_dinosaur.py` already contains:

- plain Hamiltonian/skyscraper baseline
- skyscraper + safe cycle-index shortcuts
- 25% / 50% shortcut cutoff variants
- source-near skysdottir Hilbert + shortcut reference

Existing local benchmark evidence recorded in `docs/DINOSAUR.md`:

- skysdottir shortcutting is much stronger for short target tails
- plain Hamiltonian catches up around 50% occupancy on 32x32
- plain Hamiltonian wins the measured near-full 32x32 case
- at tail 1023, recorded sustained throughput was 453.57 Bones/s for Hamiltonian vs 415.31 for the skysdottir reference

Important: those results were produced with the older benchmark setup/speedup and are not direct leaderboard scores. Do not use them as a final leaderboard ranking.

## Optimization candidates

### 1. Greedy startup -> deterministic Hamiltonian finish

Highest-priority candidate.

Use direct Apple pursuit while the tail is short and there is lots of free space, then switch to a guaranteed Hamiltonian route before the body becomes dangerous.

Relevant references:

- Flekay `Dinosaur/Single Drone/drone.py`
- Flekay `hybrid.py`
- Steam/community hybrid implementations already summarized in `docs/DINOSAUR.md`

Why it is promising:

- early Dinosaur moves are expensive, so saving physical moves early is very valuable
- later moves become much cheaper after many Apples
- the algorithm can stop paying shortcut/pathfinding decision cost when it matters less

Do not hard-code a 50% switch without benchmarking. Candidate transition points should include very early fixed lengths and occupancy-based cutoffs.

### 2. Coil -> Strike -> Pre-return -> Return

High-priority structurally different candidate.

Community description:

1. coil the tail into a known safe shape
2. strike eastward toward one or more reachable Apples
3. move to the south-east corner
4. return to the origin and repeat

Source:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1p0ox9z/my_fastest_dinosaur_run/
- referenced Pastebins `xsZL19rH` and `z4Rxj5CE`

This avoids general pathfinding and makes the tail geometry predictable.

A later commenter reported a large middlegame improvement after adding tail tracking and allowing westward double-backs during the strike phase. Treat that as community evidence, not a locally verified result.

### 3. Two-stage corridor / wavy Apple chasing

High-priority source-near benchmark candidate.

Relevant local file:

- `external/msmith93-thefarmerwasreplaced/source/dino_leaderboard.py`

The algorithm alternates between two directional stages, records off-limit column depths, pursues Apples only inside the currently safe corridor, then transitions to a deterministic wavy full-board route.

This is attractive because it encodes safety through geometry instead of expensive generic search.

### 4. Skyscraper fast-lane shortcutting

Medium priority.

The existing safe shortcut benchmark already showed that the current generic shortcut implementation does not beat plain Hamiltonian for near-full 32x32 production.

Do not benchmark the same implementation again.

A new version is only interesting if it substantially reduces decision cost, for example:

- precomputed cycle index and next direction
- integer cell IDs instead of tuple-heavy hot-path structures
- Apple-aligned fast lanes
- no `can_move()` on the known-safe Hamiltonian baseline
- shortcut checks only in a small early window

### 5. Tail-aware greedy Apple routing + tail chase fallback

Medium/high priority experimental candidate.

Policy:

1. greedily route toward the Apple when safe
2. track actual tail order / release time
3. if the Apple is temporarily unreachable, follow/chase the moving tail to create space
4. retry Apple routing
5. fall back to Hamiltonian only when neither strategy is cheap/safe

Reference idea:

- ketrab2004 implementation archived/reviewed in `docs/DINOSAUR.md`

Do not port its static-tail DFS directly. A correct planner must account for when occupied cells become free.

### 6. Moore/indexed-cycle excluded interval

Medium priority.

Use a closed indexed cycle as a safety ordering, rotate the logical index around the current Apple, and greedily choose a safe neighbor outside the forbidden tail interval.

This can be cheaper than full pathfinding, but correctness becomes subtle after arbitrary shortcuts. Keep actual tail history unless the shortcut rules preserve a strict contiguous-cycle invariant.

### 7. A* / DFS with exact tail simulation

Low priority as a production candidate, useful as a correctness/control benchmark.

Why low priority:

- the game charges ticks for interpreter work
- lists/dicts/sets, loops, tuple operations and path reconstruction are not free
- several community A*/DFS versions are slow or incomplete

A* is still useful to answer: how many physical moves could an ideal local planner save?

### 8. Alternative full-board curves

Low priority unless paired with a new shortcut policy:

- Hilbert
- heartbeat
- starburst
- other Hamiltonian/Moore curves

Existing evidence already shows that changing from skyscraper to a more complex curve alone is not enough. Hilbert was weaker than skyscraper on the measured near-full 32x32 workload.

## Historical Flekay evidence

The pinned Flekay snapshot contains this historical table:

| strategy | reported leaderboard time |
| --- | ---: |
| `drone.py` | 18.741 s |
| `circle.py` | 23.924 s |
| `timon.py` | 27.889 s |
| `almighty.py` | 42.221 s |
| `hybrid.py` | no valid score |
| `astar.py` | no valid score |

These numbers are useful only as upstream historical evidence. They were not reproduced locally and may use a different game revision, simulator behavior, machine, or benchmark conditions.

The most useful idea from the table is the strategy family: direct/simple Apple routing early, then a deterministic safe route.

## Benchmark record

Measured Dinosaur results and benchmark-derived corrections are maintained in `bench/dinosaurs.md`.
