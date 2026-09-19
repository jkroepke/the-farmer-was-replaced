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

For production selection, the runner now focuses on:

```text
world size: 32
target tail occupancy: 25%, 50%, 75%, 95%
seeds: 1, 2, 3
speedup: 64
```

8x8 and 16x16 remain useful as historical/debugging data, but they should not decide the production algorithm when the real production farm is 32x32.

The benchmark stops at fixed tail occupancy rather than only filling the board. This remains useful because shortcut value is concentrated in the early/middle run and because the optimal cutoff may be 25% rather than 50%.

The benchmark prints `DINOSAUR BENCH INVALID` if a strategy encounters a failed `move()` before reaching its requested tail target. Treat such a result as invalid even if the returned runtime looks fast.

For each run, start from:

- empty field
- same world size
- same simulation seed
- oversized Cactus inventory
- same unlock state

### Primary production metric: Bone throughput

Runtime is only directly comparable **between strategies at the same tail target**, because those runs produce the same Bone amount.

Across different target tail lengths, the primary metric is:

```text
Bones per second = tail_length ** 2 / runtime
Bones per minute = Bones per second * 60
```

The runner now prints:

- runtime
- target tail length
- expected Bones
- Bones/second
- Bones/minute

This distinction is critical because Bone yield grows quadratically with tail length. A 95% run can be much slower in absolute time and still produce far more Bones per unit time than a 25% run.

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

# Throughput reinterpretation

The initial benchmark discussion focused too much on raw runtime. For production, Bone throughput is the more important metric.

Because:

```text
Bones = tail_length ** 2
```

larger tail targets can dominate throughput even when they take longer.

Example from the completed 16x16 data:

| Target | Tail | Bones | Reference runtime | Reference Bones/s | Hamiltonian Bones/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25% | 64 | 4096 | 93.11 | 43.99 | 23.56 |
| 50% | 128 | 16384 | 187.03 | 87.60 | 75.89 |
| 75% | 192 | 36864 | 220.16 | 167.44 | 157.03 |
| 95% | 243 | 59049 | 230.92 | **255.71** | 244.58 |

So the 95% reference run has almost 6x the Bone throughput of the 25% reference run, despite taking much longer.

The same effect already appears in partial 32x32 data:

- 25% reference average:
  - tail 256
  - 65,536 Bones
  - 684.99 s
  - about **95.67 Bones/s**
- 50% seed 1:
  - tail 512
  - 262,144 Bones
  - Hamiltonian: about **152.67 Bones/s**
  - reference: about **139.33 Bones/s**

Therefore:

> The fastest algorithm to a short tail is not automatically the best Bone producer.

For production, the likely optimum may be a long 75-95% run even if its wall-clock duration is higher.

# Preliminary benchmark results

These are preview results from the first deterministic benchmark run. Lower is better.

## 8x8

| Target | Hamiltonian | Annealed 50 | Hard 25 | Hard 50 | skysdottir reference |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25% | 17.06 | 15.18 | 14.60 | 14.60 | **11.57** |
| 50% | 25.90 | **24.03** | 25.14 | 25.70 | 25.38 |
| 75% | 30.04 | **29.00** | 30.37 | 31.43 | 30.14 |
| 95% | 31.14 | **30.34** | 31.81 | 32.99 | 31.51 |

Observations:

- At only 25% fill, the reference is about 32% faster than the baseline.
- At larger 8x8 targets the simple annealed skyscraper shortcut mode is slightly fastest.
- The advantage becomes small near a full board.
- Hard cutoff at 50% is consistently unattractive late in the run.

## 16x16

| Target | Hamiltonian | Annealed 50 | Hard 25 | Hard 50 | skysdottir reference |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 25% | 173.85 | 146.28 | 142.07 | 142.07 | **93.11** |
| 50% | 215.90 | 245.25 | 202.12 | 254.54 | **187.03** |
| 75% | 234.76 | 277.65 | 234.27 | 287.50 | **220.16** |
| 95% | 241.43 | 287.95 | 245.12 | 298.10 | **230.92** |

Observations:

- The skysdottir reference wins all completed 16x16 cases.
- Relative to the baseline, its improvement is approximately:
  - 46% at 25% fill
  - 13% at 50% fill
  - 6% at 75% fill
  - 4% at 95% fill
- Hard-25 is much better than Hard-50 once the target exceeds 25%.
- Continuing to evaluate shortcuts too long can be slower than simply following the Hamiltonian cycle.
- The source-like annealed skyscraper mode also becomes slower than baseline after 25% on 16x16.
- This strongly supports an early-shortcut / late-Hamiltonian hybrid, but the path geometry matters: the Hilbert-based reference still outperforms our skyscraper adaptation on 16x16 despite earlier community reports that Hilbert can be slower.

## Plausibility check

For a 25% target, `safe-shortcuts-hard-25` and `safe-shortcuts-hard-50` are identical for every shown seed.

That is expected: both modes use identical shortcut behavior until 25% fill, and the benchmark stops there. This is a useful confirmation that the cutoff plumbing behaves as intended.

## 32x32, 25% tail target

| Strategy | Seed 1 | Seed 2 | Seed 3 | Average | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hamiltonian | 1172.46 | 1295.70 | 1344.10 | 1270.75 | 1172.46 | 1344.10 |
| Annealed 50 | 1369.73 | 1617.97 | 1569.37 | 1519.02 | 1369.73 | 1617.97 |
| Hard 25 | 1449.68 | 1600.50 | 1621.25 | 1557.14 | 1449.68 | 1621.25 |
| Hard 50 | 1449.68 | 1600.50 | 1621.25 | 1557.14 | 1449.68 | 1621.25 |
| **skysdottir reference** | **673.48** | **693.09** | **688.40** | **684.99** | **673.48** | **693.09** |

This is a very strong result.

At 25% tail occupancy on the production-relevant 32x32 board:

- the skysdottir reference is about **46% faster** than the plain Hamiltonian baseline
- our annealed skyscraper shortcut adaptation is about **20% slower** than baseline
- our hard-cutoff skyscraper variants are about **23% slower** than baseline

This cleanly separates two ideas:

> Shortcutting itself is not the problem. Our skyscraper shortcut implementation/path interaction is the problem.

The source-near Hilbert/reference algorithm scales much better in the early run.

## 32x32, 50% tail target — partial

Available values so far:

| Strategy | Seed 1 | Seed 2 | Seed 3 |
| --- | ---: | ---: | ---: |
| Hamiltonian | 1717.07 | 1815.90 | not yet recorded |
| Annealed 50 | 2830.86 | 3247.93 | not yet recorded |
| Hard 25 | 2293.98 | 2445.27 | not yet recorded |
| Hard 50 | 3255.35 | 3447.38 | not yet recorded |
| skysdottir reference | 1881.48 | not yet recorded | not yet recorded |

The first completed reference point suggests a possible crossover:

- at 25%, the reference is dramatically faster than Hamiltonian
- at 50% on seed 1, the reference is about **9.6% slower** than Hamiltonian

Do not conclude the crossover is confirmed until the remaining reference seeds complete.

However, the possibility is important because the source reference changes character around half-board: shortcutting disappears and the run becomes mostly pure traversal of the Hilbert cycle.

That may expose a path-geometry tradeoff:

- Hilbert/reference: excellent early shortcut opportunities
- skyscraper: potentially cheaper/faster pure late-cycle traversal

A mid-run switch from one unrelated Hamiltonian cycle to another is **not automatically safe**, because the existing tail occupies positions according to the old path/history. Do not switch from a Hilbert body directly onto the skyscraper cycle without proving tail safety.

Safer optimization directions are:

1. tune the reference cutoff earlier than 50%
2. keep the Hilbert path but stop expensive shortcut evaluation earlier
3. design a source-style shortcut algorithm on a path geometry that remains efficient after the shortcut phase
4. select the whole-run strategy based on requested Bone/tail target:
   - short target: reference
   - long target: possibly plain Hamiltonian

## Current benchmark conclusion

Do not promote the current skyscraper shortcut variants.

For 32x32 at 25%, the source-near reference is decisively best. The first 50% result suggests that the best strategy may depend on requested tail length rather than one algorithm winning the entire run.

This makes target-aware Bone production more important: if the planner needs only a modest Bone amount, stopping around a short tail target can exploit the reference algorithm's strongest phase instead of paying for a long late-game traversal.

## Current next step

Continue the 32x32 / 25% case far enough to obtain the skysdottir reference result. If it remains faster than the baseline, prioritize a source-faithful production adaptation over further tuning of the current skyscraper shortcut variants.

Run `bench_dinosaur_run.py` and record the results here before changing production `dinosaur.py`.

The first benchmark answers two questions:

1. How much does safe shortcutting improve the current skyscraper/Hamiltonian path?
2. Is it better to stop evaluating shortcuts around 25% fill or around 50% fill?

The source-like annealed mode is included because shortcut decision overhead itself may become significant as Dinosaur moves get cheaper after repeated Apples.

Do not promote a shortcut strategy into production until it reaches all requested tail targets without `DINOSAUR BENCH INVALID` and wins deterministic simulation comparisons.
