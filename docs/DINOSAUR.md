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

### 2. Pastebin strategy pair

Sources supplied for future comparison:

- https://pastebin.com/xsZL19rH
- https://pastebin.com/z4Rxj5CE

The Pastebin contents could not be retrieved through the current research environment. Do not invent their behavior from the URLs alone.

Before implementing this benchmark mode, fetch/read the actual source and document its invariants here.

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

## Benchmark convention

Use the repository-wide convention:

- `bench_dinosaur.py` — all Dinosaur benchmark modes
- `bench_dinosaur_run.py` — matrix, seeds, `simulate()`, and result aggregation

Do not create one benchmark file per strategy.

## Implemented initial benchmark modes

The first benchmark now exists in:

- `bench_dinosaur.py`
- `bench_dinosaur_run.py`

Current modes:

| Mode | Strategy | Purpose |
| ---: | --- | --- |
| 0 | `hamiltonian-skyscraper` | current production-style baseline |
| 1 | `safe-shortcuts-annealed-50` | source-like shortcut probability that fades toward 50% fill |
| 2 | `safe-shortcuts-hard-25` | always evaluate safe shortcuts until 25% fill, then pure Hamiltonian |
| 3 | `safe-shortcuts-hard-50` | always evaluate safe shortcuts until 50% fill, then pure Hamiltonian |
| 4 | `skysdottir-tfwr-reference` | source-near behavioral port of `dinos3.py` + `hilbert.py`: Hilbert cycle, source tail queue semantics, annealing, 50% cutoff |

Modes 1-3 deliberately use the same skyscraper/Hamiltonian geometry as production. This isolates shortcut value from path-shape changes.

Mode 4 is intentionally different: it preserves the current `skysdottir/tfwr` reference path and control flow closely enough to detect performance lost in our adaptations. The benchmark still stops at the same actual consumed-Apple/tail target so runtime remains comparable.

Future modes can add edge-wave, Moore, Hilbert, and the Pastebin implementations after the current benchmark establishes a shortcut baseline.

Do not replace production `dinosaur.py` until a candidate wins deterministic simulation benchmarks.

## Benchmark dimensions

The current runner uses:

```text
world sizes: 8, 16, 32
target tail occupancy: 25%, 50%, 75%, 95%
seeds: 1, 2, 3
speedup: 64
```

The benchmark stops at fixed tail occupancy rather than only filling the board. This is important because shortcut value is expected to be concentrated in the early/middle run and because the optimal cutoff may be 25% rather than 50%.

The benchmark prints `DINOSAUR BENCH INVALID` if a strategy encounters a failed `move()` before reaching its requested tail target. Treat such a result as invalid even if the returned runtime looks fast.

This also lets us test the claim that shortcut logic should be disabled around 25-50% occupancy.

For each run, start from:

- empty field
- same world size
- same simulation seed
- oversized Cactus inventory
- same unlock state

Primary metric:

- runtime returned by `simulate()`

Useful verbose diagnostics:

- ending `get_tick_count()`
- successful moves
- Apples collected
- shortcut attempts
- shortcuts taken
- moves saved by shortcuts
- tail length at completion

## Suggested benchmark workflow

Dinosaur full-board 32x32 runs can be expensive.

Use staged benchmarking:

1. 8x8 for correctness/debugging
2. 16x16 for tuning
3. 32x32 only for promising finalists
4. one seed during early iteration
5. three seeds for final comparisons

When tuning shortcut cutoff, compare only the current best path and candidate cutoff values rather than rerunning every historical mode.

## Current next step

Run `bench_dinosaur_run.py` and record the results here before changing production `dinosaur.py`.

The first benchmark answers two questions:

1. How much does safe shortcutting improve the current skyscraper/Hamiltonian path?
2. Is it better to stop evaluating shortcuts around 25% fill or around 50% fill?

The source-like annealed mode is included because shortcut decision overhead itself may become significant as Dinosaur moves get cheaper after repeated Apples.

Do not promote a shortcut strategy into production until it reaches all requested tail targets without `DINOSAUR BENCH INVALID` and wins deterministic simulation comparisons.
