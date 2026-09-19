# Dinosaur Design and Optimization Notes

This document is the canonical reference for Dinosaur behavior, current production strategy, external algorithm research, and future benchmarks.

Read this file before changing:

- `dinosaur.py`
- Dinosaur/Bone handling in `production.py`
- future `bench_dinosaur.py`
- future `bench_dinosaur_run.py`

## Current game mechanics

Primary reference:

- https://thefarmerwasreplaced.wiki.gg/wiki/Dinosaurs

Relevant current behavior:

- only one drone can wear `Hats.Dinosaur_Hat`
- equipping the hat purchases/places an Apple if enough Cactus exists
- moving away from an Apple consumes it and increases tail length by one
- `measure()` while standing on the current Apple returns the next Apple coordinates
- the new Apple is randomly placed on an available tile
- moving into the tail fails
- the final tail segment moves away during a successful move, so entering that just-vacated position is allowed
- Dinosaur movement does not wrap over farm boundaries
- removing the Dinosaur Hat harvests the tail
- a tail of length `n` yields `n**2` Bones
- current documented Dinosaur move cost starts at 400 ticks
- each collected Apple reduces the move cost by 3%, rounded down

Older community discussions sometimes mention 800 ticks. Treat those numbers as historical; use current game behavior / current Wiki documentation for new benchmarks.

## Current repository implementation

`dinosaur.py` currently:

1. clears the field
2. moves to `(0, 0)`
3. equips the Dinosaur Hat
4. follows one fixed Hamiltonian cycle
5. repeats the cycle until movement fails or a full cycle finds no Apple
6. removes the hat to harvest the tail as Bones

The path is:

- up the left edge
- snake vertically through columns `1..N-1`, leaving the bottom row free
- return West along the bottom row

This is effectively the same family of path as the "skyscraper" path in:

- https://github.com/skysdottir/tfwr

That is important: the current production path itself is not obviously the weak point. The major missing optimization is shortcutting.

## External strategies

### 1. Edge square + wave

Source:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1o90hxs/my_sna_i_mean_dinosaur_algorithm/

Description from the author:

- move around the outer square/perimeter
- when the Apple can be reached from above or below, make a wave into the field
- as the tail becomes longer, periodically make a full wave before beginning the next square
- wave frequency grows with tail length, approximately one full wave per `world_size * 2` of tail length

Why it is interesting:

- simple control flow
- likely low interpreter/check overhead
- preserves a structured body shape
- avoids fully generic pathfinding

Community reaction suggests the approach improves significantly over naive full-cycle traversal, but its exact advantage must be measured locally.

### 2. Reddit/Pastebin coil -> strike -> pre-return -> return

Sources:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1p0ox9z/my_fastest_dinosaur_run/
- https://pastebin.com/xsZL19rH
- https://pastebin.com/z4Rxj5CE
- local provenance: `external/reddit-dinosaur-coil/`

The Pastebins were successfully reviewed on 2026-09-19.

The main source uses a four-phase state machine:

1. **coil**: build a predictable vertical zig-zag tail
2. **strike**: pursue Apples in the open eastern area while the next Apple remains usefully farther east
3. **pre-return**: move toward the south-east corner when further strikes are no longer useful
4. **return**: use the bottom row and return to `(0, 0)`, then start another coil

The source eventually switches to a deterministic safe sweep when the tail is large.

A later Reddit commenter reports a substantial middlegame improvement by tracking the real tail and allowing westward double-backs during the strike phase. Treat that as community evidence until reproduced locally.

The local benchmark does **not** copy the unlicensed Pastebin source verbatim. Modes 10/11/12 are independent implementations of the published route policy and compare safe-route transition points around 33%, 50%, and 66% occupancy.

### 3. Hamiltonian path + safe shortcutting

Primary sources:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1omrxi4/some_dinosaur_path_speed_comparisons/
- https://github.com/skysdottir/tfwr

This is currently the highest-priority strategy to benchmark because it directly extends our existing Hamiltonian/skyscraper production path.

The external implementation tracks:

- a Hamiltonian cycle index for every tile
- the normal next direction on the cycle
- current tail length
- current effective cycle length
- a ring buffer / queue containing actual tail history
- current/next Apple coordinates

A shortcut is rejected when it would:

- hit an invalid/tail tile
- jump ahead of the current tail
- skip past the Apple in cycle order
- shorten the remaining safe cycle so far that it cannot contain the tail

The external code gradually reduces shortcut attempts as the tail grows and switches completely to the Hamiltonian path when tail length reaches roughly half the board.

The author reports that Hilbert was about 15 seconds slower on repeated 16x16 runs than the simpler paths. Their explanation is that Hilbert has many short turns and fewer useful long straight shortcut opportunities.

The simpler "skyscraper" and "heartbeat" paths also admit special fast-lane optimizations when the Apple lies behind the head.

### 4. Hilbert curve + shortcutting

Source:

- https://github.com/skysdottir/tfwr/blob/main/hilbert.py

Properties:

- good locality
- recursive space-filling path
- implementation only works directly for world sizes `2**n`
- more complex path geometry
- published community comparison found it slower than simpler paths on 16x16

Do not assume a sophisticated space-filling curve is faster. Benchmark it.

### 5. Moore-style closed loop + excluded interval

Source supplied by user:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1w0bznt/whats_a_good_strategy_for_dinosaur/

Proposed idea:

- use a Moore-style closed loop / indexed cycle
- rotate indices so the Apple is logically index 0
- derive an excluded interval from snake length
- prefer:
  1. greedy movement toward Apple if safe/non-excluded
  2. allowed neighbor with lowest shifted cycle index
  3. excluded neighbor with highest shifted index as fallback

This is elegant because cycle position becomes an ordering/safety signal.

However, be careful: if arbitrary shortcuts create gaps in the actual body, a safety test based only on tail length and nominal cycle indices may no longer describe the exact occupied cells. The actual tail-history queue used by the skysdottir implementation is a stronger correctness signal.

A Moore implementation should therefore either:

- prove that its shortcut rules preserve the contiguous-cycle invariant, or
- track actual tail positions as well.


### 6. Steam discussion: hybrid startup pathfinding + Hamiltonian fallback

Source:

- https://steamcommunity.com/app/2060160/discussions/0/600768831220139619/

This thread contains several implementations of the same broad idea that appears in the Reddit/GitHub research:

> use aggressive direct Apple routing while the tail is short, then fall back to a deterministic Hamiltonian/full-coverage path once the tail becomes dangerous.

Useful observations:

- One author explicitly describes a "startup_sequence" that targets Apples directly first and switches to the full loop when the tail becomes too long.
- A later 32x32 implementation does opportunistic direct routing while the snake length is below half of the board, then switches completely to the full Hamiltonian-style path after 50% occupancy.
- Another recent implementation reports a leaderboard time of about **21.35** and uses multiple phases:
  - direct routing for roughly the first 20-30 Apples
  - side-oriented sweeps afterward
  - skip portions of the path that do not contain the Apple
  - gradually fill lower rows as the tail grows to reduce self-collision risk
  - even-sized worlds only
- The same author notes that the algorithm can still fail on unlucky early Apple placements, roughly "once every 10 times". Treat it as performance evidence, not a correctness reference.

This reinforces the benchmark priority already identified here: **hybrid early shortcuts + deterministic late Hamiltonian** is more promising than replacing the Hamiltonian path entirely.

### 7. Steam discussion: exact tail simulation with DFS/A*

The same Steam thread also contains two attempts at generic pathfinding.

One DFS implementation:

- tracks the full current snake/tail state
- tries directions ordered by a Manhattan-like score toward the Apple
- simulates the body shifting on each candidate move
- backtracks when a route would collide with the tail

Another much larger A*-style implementation:

- keeps an explicit deque of tail positions
- simulates the tail while evaluating a candidate path
- correctly recognizes an important Snake rule: the oldest tail segment can be treated specially because it may move away on the next successful step
- uses Manhattan distance as the pathfinding heuristic
- backtracks and restores the simulated tail when a route fails

However, the posted A* code is **not a production-quality reference**:

- another participant reports multiple errors in the pasted implementation
- the thread mentions invalid indexing / tuple mutation / missing globals
- the author-side comments themselves show unfinished logic
- generic DFS/A* can take seconds to calculate in some cases

This makes it useful as a source of **safety invariants**, but not as a direct implementation candidate.

Key invariant worth preserving:

> A safe planner should simulate the tail's movement, not merely treat every currently occupied tail tile as permanently blocked.

That observation can improve shortcut validation without paying the full cost of DFS/A*.

### 8. Steam discussion: do not assume maximum tail is optimal

An early thread calculation argues that a shorter target tail can produce Bones more efficiently per tick than always maximizing the board.

Its numeric examples use an old **800-tick** Dinosaur movement model and are therefore outdated, but the optimization question remains valid:

- a full-board run gives quadratic Bone yield
- reaching that full board can require a large amount of movement
- an upgrade-driven planner may need far fewer Bones than the maximum harvest

This independently supports benchmarking target-tail production instead of always filling the complete farm.

### 9. MateusMarochi repository: collision-triggered harvest/restart

Source:

- https://github.com/MateusMarochi/the-farmer-was-replaced-codes
- `bone_farm.py`

The repository's Dinosaur path is not a fundamentally new geometry. It is effectively another skyscraper/Hamiltonian sweep:

- alternating vertical columns
- row 0 kept as a return lane
- West along row 0 back toward x=0
- repeat

So it does not provide a better path candidate than the ones already benchmarked.

However, its `dinosaur_safe_move()` contains an important production idea:

```text
if move is blocked:
    change away from Dinosaur Hat
    change back to Dinosaur Hat
```

Changing away from the Dinosaur Hat harvests the current tail. Changing back starts another Dinosaur run.

Therefore this is not really a "safe move" workaround. It is effectively:

> collision-triggered harvest + immediate restart

The outer traversal then continues from the current position with a fresh Dinosaur/tail.

### Why this matters for our benchmark

Our current benchmark answers:

> What is the throughput of one run harvested at a chosen 25/50/75/95% tail target?

The MateusMarochi code suggests a second production question:

> What is the sustained Bones/minute over many consecutive harvest/restart cycles when the algorithm decides naturally when it can no longer continue?

For long-running Bone production, that may be the more relevant metric.

A strategy can have excellent one-run throughput but perform worse over time if it:

- chooses a poor harvest point
- has expensive restart/setup overhead
- repeatedly spends too long in a low-throughput early phase

Conversely, a collision-triggered or target-triggered strategy can be evaluated across several complete cycles.

### Implemented sustained-throughput benchmark

The benchmark runner now includes a second phase after the normal fixed-target benchmark.

It runs:

```text
world size: 32
cycles per simulation: 3
target tail occupancy: 95%, 97%, 99%, 100% (clamped to board - 1)
seeds: 1, 2, 3
strategies:
- hamiltonian-skyscraper
- skysdottir-tfwr-reference
```

Each sustained simulation:

1. calls `set_world_size(32)` once
2. runs three Dinosaur production cycles
3. harvests the tail after each target is reached
4. repositions to the origin without clearing/resetting the world again
5. starts the next Dinosaur cycle
6. reports aggregate runtime, expected Bones, Bones/s, and Bones/min

The runner also prints a `SUSTAINED SUMMARY` averaged across seeds.

The two benchmark phases answer different questions:

- fixed target benchmark isolates path efficiency
- repeated-cycle benchmark measures sustained production efficiency

Collision-triggered/natural-end harvesting is still a future extension because the runner currently needs a deterministic known tail length to compute aggregate expected Bones automatically.

### Benchmark setup

The redundant `clear()` after `set_world_size()` has been removed.

`set_world_size()` already clears/resets the field, so the benchmark now pays that setup cost only once per simulation. Sustained cycles do not resize or clear the world again between harvests.

This is important when comparing 25% vs 95% targets because otherwise a fixed setup cost would distort short-run throughput more strongly.

### 10. Repository comparison: MateusMarochi, juritox, ketrab2004

Repositories reviewed:

- https://github.com/MateusMarochi/the-farmer-was-replaced-codes
- https://github.com/juritox/the-farmer-was-replaced
- https://github.com/ketrab2004/the-farmer-was-replaced

#### MateusMarochi

Relevant file:

- `bone_farm.py`

This uses essentially the same skyscraper/Hamiltonian geometry already covered by our baseline:

- alternating vertical columns
- bottom row kept free
- return West on the bottom row
- repeat

Its only distinctive production behavior is collision-triggered hat switching, which effectively harvests and restarts the Dinosaur. That insight is already represented by the sustained-throughput benchmark.

No new pathfinding strategy needs to be added from this repository.

The Dinosaur file has only one historical commit from October 2025, so treat it as a strategy example rather than a current optimized reference.

#### juritox

Relevant file:

- `scripts/bone_harvest.py`

This is an older 2025 implementation built around deterministic full-field sweeps. It does not use:

- `measure()` to target the next Apple
- explicit tail tracking
- shortcut safety
- a Hamiltonian index
- throughput measurement

It also contains movement patterns that rely on failed boundary moves as control flow.

There is no new optimization worth porting into the current benchmark.

Useful conceptual reminder only:

> keep the movement pattern structurally simple when interpreter overhead dominates.

But our existing plain Hamiltonian baseline already covers that tradeoff better.

#### ketrab2004

Relevant files:

- `dinosaur.py`
- `pathfind.py`
- `queue.py`
- `tail.py`

This repository contains a genuinely different Dinosaur idea.

The main loop:

1. measures the Apple target
2. builds an in-memory map of current tail positions
3. tries a DFS route directly to the Apple
4. if no path to the Apple exists, finds the tail end
5. uses BFS to route toward the tail end
6. if even that fails, takes any currently legal move

The interesting fallback is:

> **if the Apple is temporarily unreachable, chase the tail instead of immediately switching to a fixed Hamiltonian cycle.**

Following the tail can create space because the tail moves away as the head advances.

This is conceptually different from both:

- fixed Hamiltonian fallback
- cycle-index shortcutting

However, the posted implementation is not safe enough to use directly.

The code explicitly contains:

```text
TODO take into account tail moving
```

Its DFS/BFS treats the current tail map mostly as static while planning. That misses the most important Dinosaur pathfinding rule: cells occupied now may become free before the head reaches them.

It also rebuilds the complete `tail_dict` from the queue on every outer iteration, making the implementation O(tail length) before pathfinding even starts.

#### Useful data-structure idea from ketrab2004

The repository also contains `tail.py`, which models the body with:

- tail-end coordinate
- head/front coordinate
- length
- monotonic sequence index
- dictionary keyed by coordinate
- previous/next links per occupied position

That structure is more interesting than the actual `dinosaur.py` implementation.

For a future dynamic solver, maintain both:

```text
queue/order of body positions
+
dict/set coordinate -> tail age/order
```

This allows:

- O(1) occupied-cell lookup
- O(1) updates as the tail advances
- knowing **when** an occupied tile will become free
- tail-aware path validation without rescanning the full body every step

This is a useful direction for improving on the generic DFS/A* ideas found in the Steam thread.

### New future benchmark candidate: Apple path + tail chase

A future experimental mode should test:

```text
tail-aware-apple-path-tail-chase
```

Policy:

1. greedily/directly route toward the Apple while a safe path exists
2. pathfinding state must include the time/step at which each tail tile becomes free
3. if no Apple path is safe, route toward/follow the moving tail
4. retry Apple routing as space opens
5. use a Hamiltonian fallback only if neither strategy has a safe route

Do **not** port ketrab2004's static-tail DFS directly.

The benchmark is worthwhile only if the planner accounts for future tail release. Otherwise it repeats the known flaw of treating every currently occupied tile as permanently blocked.

Because generic search can be expensive in the game interpreter, compare:

- pathfinding ticks spent
- physical moves saved
- resulting Bones/s

against the current reference before considering production use.

## Important research conclusion: our baseline is already skyscraper-like

The current repository path and the external `skyscraper.py` share the same core geometry:

- vertical sweeps
- bottom return lane
- closed Hamiltonian cycle

Therefore the first optimization should not be "replace the path with Hilbert".

The first experiment should be:

> current skyscraper Hamiltonian cycle vs current skyscraper path + safe cycle-index shortcutting

This isolates shortcut value without changing the underlying path.

## Interpreter overhead matters

A shortcut algorithm does not automatically win just because it saves physical moves.

Community observations report cases where:

- pure Hamiltonian movement late in a run becomes very cheap
- shortcut decision logic costs enough ticks that continuing to evaluate shortcuts becomes slower than simply following the cycle

This fits the game mechanic: Dinosaur move cost decreases by 3% after every Apple.

Therefore shortcutting needs a cutoff.

Do not hard-code 50% as unquestionably optimal.

Candidate cutoffs should be benchmarked, for example:

- 20%
- 25%
- 33%
- 50%
- adaptive based on measured decision cost vs current move cost

The user's supplied community example found a 25% cutoff faster for a particularly expensive shortcut implementation.

## Production-size optimization may matter as much as pathfinding

Current `production.run_bones()` starts a Dinosaur job and `dinosaur.run()` normally grows until movement fails / the farm is effectively full.

That can massively overproduce Bones when the selected upgrade needs only a smaller deficit.

Because harvested Bones scale as:

```text
bones = tail_length ** 2
```

a future production optimization should consider a target tail length derived from the required Bone deficit rather than always filling the board.

Conceptually:

```text
target_tail >= ceil(sqrt(missing_bones))
```

Do not implement this blindly yet:

- account for any game/unlock multipliers if present
- verify exact observed reward
- preserve enough margin if production planning changes while the job runs

But benchmark both full-tail throughput and smaller target-tail jobs. A path strategy that wins at full board may not win when only 25% of the board is needed.

## Reference requirement

Whenever a benchmark is inspired by or adapted from an external implementation, include a source-near reference mode in the same benchmark.

For Dinosaur work, `skysdottir/tfwr` is therefore not only a design source. Its current `dinos3.py` + `hilbert.py` behavior is preserved as `skysdottir-tfwr-reference`.

The purpose is to catch regressions introduced by our own translation, cleanup, different path geometry, or tuning. Never compare only "our baseline" against "our adaptation" when an external reference implementation exists.

A reference mode may adapt setup/termination to the benchmark contract, but should preserve the reference algorithm's path, decision rules, and state semantics as closely as the game interpreter permits.

## Benchmarks

Measured Dinosaur matrices, throughput results, corrections, and follow-up runs are maintained in `bench/dinosaurs.md`.
