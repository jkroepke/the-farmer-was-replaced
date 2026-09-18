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

## Benchmark convention

Use the repository-wide convention:

- `bench_dinosaur.py` — all Dinosaur benchmark modes
- `bench_dinosaur_run.py` — matrix, seeds, `simulate()`, and result aggregation

Do not create one benchmark file per strategy.

## Recommended initial benchmark modes

Start with:

| Mode | Strategy | Priority |
| ---: | --- | --- |
| 0 | current Hamiltonian/skyscraper baseline | baseline |
| 1 | skyscraper + safe cycle-index shortcutting | highest |
| 2 | edge-square + wave | high |
| 3 | Moore-style indexed loop + safe shortcuts | high after correctness proof |
| 4 | Hilbert + safe shortcutting | comparison |
| 5+ | Pastebin strategies | after source can be read |

Do not replace production `dinosaur.py` until a candidate wins deterministic simulation benchmarks.

## Benchmark dimensions

World sizes:

```text
8
16
32
```

Seeds:

```text
1
2
3
```

Do not benchmark only "fill the entire board".

Use tail-length checkpoints, because shortcut value is concentrated in the early/middle run:

```text
25% board occupancy
50% board occupancy
75% board occupancy
near/full board
```

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

Implement the first benchmark pair before changing production:

1. existing Hamiltonian/skyscraper baseline
2. same skyscraper cycle with safe shortcutting based on the `skysdottir/tfwr` cycle-index + tail-history approach

This gives the cleanest answer to the highest-value question:

> How much speed can we gain without changing our already-safe Hamiltonian path?
