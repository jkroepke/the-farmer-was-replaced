# skysdottir/tfwr

## Upstream

- URL: https://github.com/skysdottir/tfwr
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `e15968982e957045c5239e580e2d040a9ac73a52`
- Snapshot files: 8
- Snapshot size: 12384 bytes
- License metadata: no repository license is declared upstream
- Snapshot status: complete upstream file tree at the pinned revision is mirrored unchanged under `source/`

This archive preserves the source as an external reference. Local interpretation, current-game validity notes, and benchmark results belong in this README; files under `source/` should remain unchanged.

## Executive summary

This is a small, focused Dinosaur/Snake research repository.

Its central idea is stronger than a plain Hamiltonian cycle:

1. assign every board position an index and normal next direction on a Hamiltonian cycle
2. keep the actual tail history in a circular queue
3. track how much nominal cycle length has been removed by shortcuts that are still inside the body
4. target the current Apple with shortcuts only when cycle-order safety checks allow it
5. gradually reduce shortcut attempts as the tail grows
6. stop shortcutting entirely around half-board occupancy and continue on the Hamiltonian cycle

The upstream entrypoint currently uses a Hilbert cycle, but the repository also contains skyscraper, heartbeat, and starburst path generators.

This repository is already represented in this project by the source-near `skysdottir-tfwr-reference` Dinosaur benchmark. That local benchmark is especially valuable because it separates the useful algorithm from old/source-specific syntax and leaderboard behavior.

## Repository map

- `dinos3.py` — Dinosaur controller, shortcut safety, annealing, tail accounting, preparation, and leaderboard timing
- `queue_utils.py` — circular tail/history queue
- `hilbert.py` — recursive Hilbert-cycle generator
- `skyscraper.py` — simple vertical-sweep Hamiltonian cycle with a bottom return lane
- `heartbeat.py` — two-half structured Hamiltonian cycle
- `starburst.py` — experimental radial/ray-style cycle generator
- `pos.py` — wrap-aware movement, recursive farm partitioning, and multi-drone traversal helpers
- `m_utils.py` — primitive "wait until only the parent drone remains" helper

## Dinosaur controller: `dinos3.py`

The active upstream program is:

```text
set_world_size(16)
prep()
farm()
```

The source therefore targets a 16x16 test/leaderboard environment rather than being a generic production entrypoint.

### Indexed cycle representation

Each path generator fills:

```text
path_ids[(x, y)] = (cycle_index, next_direction)
```

This gives every position two useful properties:

- total ordering around the cycle
- O(1) lookup of the safe baseline direction

The same index space is then reused for shortcut safety checks.

### Tail/history queue

`queue_utils.py` stores entries of:

```text
(position, shortcut_savings)
```

rather than only body coordinates.

The second field is important. A shortcut compresses the currently active safe cycle. When that shortcut eventually leaves the tail, its removed cycle distance can be added back.

The controller maintains:

- `current_tail_length`
- `current_cycle_length`
- `full_cycle_length`
- `next_apple`

On every move, `scoot()`:

1. moves the Dinosaur
2. subtracts the newly taken shortcut distance from `current_cycle_length`
3. pushes the new head position and shortcut distance into the queue
4. if the new position is the tracked Apple, increments logical tail length and measures the next Apple
5. otherwise pops the oldest tail-history entry and adds its shortcut distance back to the effective cycle length

This is the most interesting data-structure idea in the repository. It lets safety depend on the actual sequence of shortcuts still represented inside the body instead of assuming the body always occupies an unmodified Hamiltonian interval.

### Shortcut safety

The baseline move is always the path generator's normal Hamiltonian next direction.

Before replacing that move, `can_shortcut()` requires:

1. `can_move(direction)` succeeds
2. the annealing/random gate permits a shortcut attempt
3. the target cycle index is not inside the forbidden tail-to-head interval
4. the shortcut does not jump past the current Apple in cycle order
5. removing the skipped cycle segment still leaves more effective cycle capacity than the current tail plus a safety margin

The final condition is:

```text
current_cycle_length - removed_len > current_tail_length + 1
```

That `+1` is explicitly described upstream as a safety margin for Apples encountered on the return path.

### Greedy Apple direction

The controller does not evaluate every board direction equally.

It builds `wanna_dirs` only from coordinates that move the head closer to the tracked Apple:

- West/East based on x
- South/North based on y

It then accepts the first candidate producing more saved cycle steps than the baseline.

The source contains disabled alternatives and path-specific "fast lane" ideas for heartbeat/skyscraper, showing that the author was actively exploring the interaction between shortcut policy and cycle geometry.

### Annealing / cutoff

The shortcut-attempt threshold is:

```text
1 - (current_tail_length * 2 / full_cycle_length)
```

So shortcut attempts are frequent with a short tail and become progressively less likely as occupancy rises.

Separately, `dino_iter()` completely disables shortcutting once:

```text
current_tail_length >= full_cycle_length / 2
```

After that point, the algorithm follows the Hamiltonian cycle directly.

This matches the broader optimization lesson already confirmed by this project's benchmark work: expensive shortcut decisions are useful early but can become net-negative once Dinosaur movement is cheap and the board is crowded.

## Important accounting detail: arrival vs actual Apple consumption

The source increments `current_tail_length` when the head **arrives at** `next_apple`.

For benchmark stopping conditions, this project separately tracks actual Apple consumption/tail growth according to current runtime behavior while preserving the source's logical accounting for shortcut decisions.

That is why the local source-near benchmark has both:

- source-like logical tail state
- actual tail length used for fair target comparisons

Do not remove that distinction when comparing the upstream algorithm against current implementations.

## Path generators

### Hilbert: `hilbert.py`

The active `dinos3.py` setup calls `hilbert.gen_hilbert_path(path_ids)`.

The generator recursively subdivides the board and records one cycle index/direction per tile.

Upstream explicitly notes:

> the Hilbert generator only works on farms whose size is `2**n`

Properties relevant to this project:

- strong spatial locality
- many short turns
- recursively generated rather than hard-coded
- compatible with the same indexed-cycle shortcut logic

The local source-near benchmark uses 8x8, 16x16, and 32x32, all of which satisfy the power-of-two requirement.

The benchmark port intentionally uses integer-safe operations and normal list-length syntax rather than depending on the original interpreter/source syntax.

### Skyscraper: `skyscraper.py`

This generator is very close to this project's production Hamiltonian geometry:

- start at `(0, 0)`
- sweep vertically through paired columns
- leave row 0 as a return lane
- travel West across the bottom row to close the cycle

This is why the repository's biggest contribution is not "discover the skyscraper path"; this project already uses that family.

The important contribution is the indexed-cycle shortcut machinery.

### Heartbeat: `heartbeat.py`

Heartbeat splits the board into upper and lower halves:

- traverse paired columns through the upper half
- reverse across the lower half
- connect the two regions into one structured cycle

The source comments in `dinos3.py` suggest heartbeat may benefit from explicit "fast lanes" when the Apple is behind the head.

Those optimizations are disabled in the pinned revision, so heartbeat is best treated as a candidate cycle geometry rather than a measured upstream winner.

### Starburst: `starburst.py`

Starburst builds a path from expanding/contracting rays around the board.

It is currently used only by the unused `lawnmow()` experiment in `dinos3.py`, not by `prep(); farm()`.

The generator contains several source/interpreter-specific arithmetic assumptions such as `range((Z-2)/4)`. Do not assume it executes unchanged under current language semantics.

Treat it as an experimental path-construction reference unless separately validated.

## Multi-drone preparation: `pos.py`

The Dinosaur itself is necessarily single-drone, but field preparation is parallelized.

`pos.divide()` recursively subdivides the world into `max_drones()` rectangular zones, splitting along the longer dimension.

`pos.traverse(fn)` then:

1. creates one payload per zone
2. spawns workers while drone slots are available
3. executes the final zone on the parent when all slots are occupied

This neatly uses the parent as one worker instead of trying to spawn `max_drones()` children in addition to it.

The subdivision behaves cleanly when the drone count repeatedly halves to 1. If a future game configuration exposes a non-power-of-two worker count, the `D//2` recursion should be revalidated rather than assumed to create exactly `D` regions.

### Synchronization helper

`m_utils.await()` waits for child workers indirectly:

```text
while num_drones() > 1:
    do_a_flip()
```

This is not a modern synchronization pattern worth copying.

Current code should prefer explicit handles/`wait_for()` when task completion must be synchronized. The source helper also pays the behavior/cost of `do_a_flip()` while waiting.

The interesting part is the zone decomposition, not this wait loop.

## Source-level caveats

The pinned repository is from 2025-11-02 and contains code written for that game's Python-like interpreter/environment.

Examples that should not be silently normalized inside the mirror:

- `set_world_size(16)` is hard-coded in the entrypoint
- `path.len()` and `queue.len()` are used instead of current-style `len(path)` / `len(queue)`
- several generators use `/` values directly in `range()` or coordinate calculations
- `starburst.py` has arithmetic/layout assumptions that are not exercised by the active entrypoint
- `m_utils.await()` uses a busy/wait animation instead of explicit task handles
- `queue_utils.reset()` assigns `queue = []` without declaring `global queue`; the first run starts from the module's initially empty queue, but repeated reuse of the same module state should be validated before assuming reset semantics
- `dinos3.py` contains disabled/experimental path-specific branches
- `lawnmow()` is defined but not called by the active entrypoint

The complete source is mirrored unchanged so these details remain inspectable.

## Leaderboard-specific behavior

`farm()` intentionally waits until 225 seconds have elapsed before removing the Dinosaur Hat:

```text
while get_time() - start < 225:
    continue
```

This is leaderboard-oriented behavior, not an optimization for normal Bone production.

A production implementation should harvest based on requested Bone throughput/target and measured strategy behavior, not reproduce this fixed 3:45 hold.

## Local source-near benchmark

This project already ports the behavior into `bench_dinosaur.py` as:

```text
skysdottir-tfwr-reference
```

The port intentionally preserves:

- Hilbert cycle geometry
- source cycle-index ordering
- tail-history queue semantics
- effective-cycle-length accounting
- source annealing formula
- greedy directions toward the Apple
- source half-board shortcut cutoff

It also makes the minimum changes necessary for a fair current benchmark, including separate actual-tail accounting and interpreter-safe implementation details.

Therefore the benchmark is a behavioral/source-near reference, not a byte-for-byte execution of `dinos3.py`.

## Measured relevance in this repository

These numbers are local benchmark results already recorded in `docs/DINOSAUR.md`; they are not claims from the upstream repository.

### 16x16

Average runtime to fixed tail targets:

| Target | Hamiltonian | skysdottir reference |
| ---: | ---: | ---: |
| 25% | 173.85 s | **93.11 s** |
| 50% | 215.90 s | **187.03 s** |
| 75% | 234.76 s | **220.16 s** |
| 95% | 241.43 s | **230.92 s** |

The source-near reference is faster in all four completed 16x16 cases, with the largest benefit early in the run.

### 32x32 crossover

Measured Bone throughput:

| Target | Hamiltonian Bones/s | skysdottir reference Bones/s |
| ---: | ---: | ---: |
| 25% | 51.57 | **95.68** |
| 50% | **145.70** | 143.61 |
| 75% | **279.48** | 254.81 |
| 95% | **426.66** | 381.66 |

The reference nearly doubles early 25% throughput, but the simple Hamiltonian path catches up around 50% and wins increasingly at longer tail targets.

This supports a very specific conclusion:

> the skysdottir shortcut algorithm is highly valuable for short targeted Bone jobs, while its Hilbert/full-run behavior is not the best measured steady-state producer on 32x32.

### Near-full 32x32 production

At the maximum safe benchmark target, `board - 1` / tail 1023:

| Mode | Single-run Bones/s | Sustained 3-cycle Bones/s |
| --- | ---: | ---: |
| Hamiltonian skyscraper | **464.86** | **453.57** |
| skysdottir reference | 417.96 | 415.31 |

At that target, Hamiltonian is about 9.2% higher sustained throughput.

The current steady-state production evidence therefore favors plain Hamiltonian/skyscraper at near-full occupancy.

The skysdottir reference remains important because it is the strongest measured short-run strategy and because its safety/accounting machinery provides reusable ideas for future hybrid algorithms.

## What is worth reusing

The strongest reusable concepts are:

1. **cycle index + next direction per coordinate**
2. **actual tail-history queue rather than tail length alone**
3. **store shortcut savings with tail entries**
4. **restore removed cycle capacity as shortcuts leave the tail**
5. **never shortcut across the Apple in cycle order**
6. **never shortcut into the forbidden tail/head interval**
7. **reduce or stop shortcut decisions as occupancy increases**
8. **benchmark path geometry and shortcut policy as a pair**
9. **use the parent as one worker during parallel field preparation**

What should not be copied blindly:

- hard-coded 16x16 setup
- fixed 225-second leaderboard hold
- old/interpreter-specific syntax
- `do_a_flip()` synchronization
- the assumption that Hilbert is always superior
- the assumption that a 50% shortcut cutoff is optimal for every board/target

## Snapshot contents

The complete pinned upstream source tree is under `source/`:

- `dinos3.py`
- `heartbeat.py`
- `hilbert.py`
- `m_utils.py`
- `pos.py`
- `queue_utils.py`
- `skyscraper.py`
- `starburst.py`

Revision: `e15968982e957045c5239e580e2d040a9ac73a52`.
