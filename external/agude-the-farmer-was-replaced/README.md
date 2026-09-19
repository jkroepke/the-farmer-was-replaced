# agude/the-farmer-was-replaced

## Upstream

- URL: https://github.com/agude/the-farmer-was-replaced
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `15a68276c998039bcb90c0f6cbbdb006a6ce1065`
- Revision date: 2026-09-18
- Snapshot files: 82
- Snapshot size: 278821 bytes
- License: CC0-1.0
- Snapshot status: complete pinned repository mirrored unchanged under `source/`
- Snapshot verification: local `source/` tree SHA exactly equals upstream tree SHA `c6f9de46a1d8c3a6678a808300efd2aa905c779c`

This is one of the most current references in the archive and is particularly relevant to Fastest Reset / unlock planning.

It differs from most TFWR repositories because the game scripts are surrounded by a real engineering harness:

- static compatibility checks
- synchronized game API metadata
- unit-style behavioral tests
- CI
- task/fix history documenting planner regressions
- explicit separation between executable wrappers and import-safe controllers

The result is not necessarily leaderboard-optimal code, but many design assumptions are much easier to trust because they are encoded as tests rather than comments.

## Executive summary

The strongest reusable ideas are:

- read unlock/resource costs live with `get_cost()`
- re-read live costs after every bounded production action
- plan one finite action at a time rather than one long irreversible macro
- separate final unlock requirements from protected inventory and next-cycle budgets
- recursively resolve missing production inputs
- detect dependency cycles explicitly
- allow useful unrelated work when one dependency is blocked
- use Power low/high watermarks rather than threshold thrashing
- adapt the Power reserve using observed consumption
- wait explicitly for passive Fertilizer instead of spinning through unrelated production
- fund only the immediately needed Weird Substance for the next Maze plus required reserve
- use sparse revisit lists for Pumpkin/Cactus maturity
- phase-separate Cactus rows and columns
- preserve global Sunflower petal ordering across parallel workers
- treat tests as specification for planner behavior

For the current project, the Top Hat planner is more valuable as a **planning reference** than as a drop-in Fastest Reset solution, because the current fastest-reset objective is `Unlocks.Leaderboard`, not only `Unlocks.Top_Hat`.

## Repository structure

### Game code

All active game scripts live in `Save0/`.

Important files:

- `top_hat.py` — resource planner for `Unlocks.Top_Hat`
- `resource_costs.py` — live cost/budget helpers
- `maze.py` — fresh-Maze Gold production
- `cactus.py` — Cactus grow/sort/harvest
- `pumpkins.py` — Pumpkin pending-list farming
- `sunflowers.py` — parallel global petal-order Power cycle
- `parallel_farming.py` — bounded multi-drone dispatch
- `regular_farming.py`
- `farm_layout.py`
- `navigation.py`
- `traversal.py`
- `fertilizing.py`
- resource-specific runner files

### Test / tooling layer

The repository also contains:

- `scripts/test_top_hat.py`
- `scripts/test_maze.py`
- `scripts/test_sunflower_cycle.py`
- Cactus, Pumpkin, Hay, Carrot, Tree, layout and traversal tests
- `scripts/check_game_code.py`
- `scripts/sync_game_api.py`
- `game-api.json`
- Ruff configuration
- GitHub Actions CI
- agent task records describing planner fixes

This test layer is a major part of the repository's value.

## Live cost model

`resource_costs.py` deliberately avoids hard-coding final unlock costs.

`get_top_hat_cost()` calls:

```text
get_cost(Unlocks.Top_Hat)
```

at runtime.

Planting budgets are also derived from live entity costs:

```text
per-tile cost * explicit region area
```

This is exactly the right direction for reset automation, because unlock/entity costs can change with progression or game updates.

### Required inventory is three different concepts

The planner distinguishes:

1. the live final unlock cost
2. protected inventory that must not be consumed by the current stage
3. the input budget required for one next production cycle

`get_required_inventory()` merges those values only for an affordability decision.

This prevents a common planner error:

> "I already have enough of resource X for the final unlock, so I can freely spend it while producing another missing item."

Instead, completed stages can be protected while funding the next producer.

## Bounded action planning

The central Top Hat loop does not commit to a huge production plan.

`farm_top_hat()` repeatedly:

1. reads the current Top Hat cost
2. checks whether the unlock is already affordable
3. snapshots inventory
4. performs one bounded action
5. reads the live Top Hat cost again
6. snapshots inventory again
7. records observed Power consumption
8. checks whether real progress occurred
9. repeats

This is a strong generic reset-planner architecture.

### Why resampling matters

The test suite explicitly verifies that:

- costs can change while the planner is running
- a producer may overshoot the exact required quantity
- after that producer completes, the planner must re-evaluate instead of continuing an old plan

This reduces coupling to static assumptions.

## No-progress protection

`NO_PROGRESS_LIMIT = 2`.

If a non-wait action leaves the tracked inventory snapshot unchanged repeatedly, the planner stops with:

```text
Top Hat planner made no progress
```

This is useful for unattended automation because a failed producer does not create an infinite planner loop.

Explicit wait actions are excluded from this counter because waiting for passive Fertilizer can be legitimate progress in time even when inventory has not changed yet.

## Dependency resolver

`resolve_item_producer()` recursively chooses a producer for a missing item.

For example:

```text
Cactus
  -> needs Pumpkin planting budget
Pumpkin
  -> needs Carrot
Carrot
  -> needs its own inputs
```

The exact dependency comes from the **live planting budget**, not from a static hard-coded graph.

### Cycle detection

A dependency path is carried through recursive calls.

Before resolving an item, the planner checks whether that item is already in the path.

The tests cover:

- direct self-cycle
- multi-item cycle

and require the planner to stop visibly rather than recurse forever.

This is highly reusable for a full Leaderboard reset planner.

## Fallback work

When the selected dependency producer is blocked, `run_fallback_action()` tries independent useful resources:

```text
Wood
Hay
Carrot
```

This means one blocked chain does not necessarily idle the whole farm.

For fastest-reset work, the same principle can be generalized:

> if the critical-path action is temporarily blocked on passive generation, perform useful non-destructive work that will be needed later.

The difficult part is proving that fallback work is actually on the future critical path and does not delay the unblock condition.

## Power hysteresis

Power handling is unusually careful.

The planner tracks:

- low watermark
- high watermark
- whether an initial stockpile was established
- whether refill mode is active
- the largest observed Power consumption from a production action

Once Power crosses below the low watermark, refill mode stays active until the high target is reached.

It does **not** bounce out of Sunflower farming as soon as Power rises one unit above the lower threshold.

### Observed-consumption reserve

After each action:

```text
consumption = power_before - power_after
```

The maximum observed drop is retained.

That value is added to future Power targets/watermarks.

This is an adaptive safety margin learned from actual runtime consumption.

The tests explicitly verify this behavior.

### Reset relevance

This is a good pattern when an intermediate resource is consumed unpredictably by downstream actions.

Instead of guessing a fixed reserve, observe and adjust.

For a leaderboard-speed planner, the reserve may need tuning because excess safety stock can cost time.

## Fertilizer waiting

Gold can depend on Weird Substance, which in turn may require passive Fertilizer.

The planner has an explicit wait action:

```text
do_a_flip()
```

It only waits when:

- Gold is still required
- Maze exists but cannot yet be funded
- Fertilizer is currently zero

Diagnostics are rate-limited.

The tests simulate Fertilizer arriving after several flips and verify that planning resumes.

### Important interaction with Power

One regression test specifically ensures that a Fertilizer wait does not cause a new Sunflower cycle after every single flip while Power remains between the configured watermarks.

This is a subtle but useful reset-planner lesson:

> waiting must not continuously re-trigger unrelated hysteretic refill work.

## Gold and Weird Substance planning

Maze cost is current-version aware:

```text
world_size * 2 ** (maze_level - 1)
```

The planner distinguishes:

- Weird Substance required as a final unlock reserve
- Weird Substance needed to fund the **next immediate Maze**

If Gold is incomplete, the Weird Substance target is:

```text
next Maze cost + final reserve
```

not "produce some arbitrary large amount".

After Weird Substance production completes, the planner returns and resamples before actually entering a Maze.

The tests explicitly verify that it does not produce substance and spend it on a Maze inside the same stale planning decision.

This is a very strong bounded-action invariant.

## Maze implementation

The Maze producer itself is intentionally simple.

It:

1. clears once
2. creates a fresh Maze
3. solves it using a right-wall follower
4. harvests Treasure
5. repeats with a **new Maze** until Gold target or substance reserve stops it

It does not reuse Treasure within the same Maze.

For current high-performance Gold farming, this is much weaker than the local Zapakh/reference-tree reuse strategies.

Therefore:

- use agude's **resource planning**
- do not use its Maze algorithm as the current throughput winner

The test suite is still useful because it verifies current exponential Maze substance cost and reserve stopping behavior.

## Cactus

`cactus.py` contains both patch-oriented and generic full-region code.

The main full-cycle architecture is:

1. build one row job per row
2. grow rows in parallel
3. wait for all growth results
4. sort rows in parallel
5. wait for all row results
6. sort columns in parallel
7. wait for all column results
8. move to the start tile
9. bulk harvest

This preserves the critical row/column phase barrier.

### Sorter

Each line uses an early-terminating cocktail sort.

The boundaries shrink after each forward/backward pass.

This is a stronger local line sorter than a naive fixed-pass bubble implementation, but it still needs local current benchmark comparison.

### Sparse growth revisit

Each row maintains only unresolved x positions.

When only one cactus remains unresolved, the worker moves there once and polls in place until ready.

That final-single-tile optimization also appears in Pumpkin.

## Pumpkin

`pumpkins.py` uses the now-familiar pending-list architecture.

Every position starts unresolved.

Once a living mature Pumpkin has actually been observed at a coordinate, it drops out permanently for that cycle.

The worker revisits only remaining positions.

### Direction choice

Before each revisit pass, it compares distance from the current position to:

- first pending tile
- last pending tile

and scans in whichever direction is nearer.

This preserves snake order while reducing repositioning.

### Final unresolved Pumpkin

When exactly one position remains:

1. move to it once
2. stay there
3. repeatedly maintain/check the same tile
4. return as soon as it succeeds

This removes repeated travel during the slow tail of Pumpkin completion.

### Parallel full-field cycle

`farm_pumpkin_cycle()` gives each row to the indexed job dispatcher.

Only after all rows report readiness does the controller move to the final location and harvest the merged Pumpkin.

This is a clean current-memory-safe parallel design because each row job is independent and coordination is handle-based.

## Sunflowers

The Sunflower full-field cycle is particularly disciplined.

Each row worker:

1. plants/prepares its row
2. waits for all row flowers to mature
3. measures every flower exactly once
4. returns petal buckets with coordinates

The controller combines all returned buckets.

It then harvests **globally** from petals 15 down to 7.

Equal-petal positions can be harvested in parallel, but the code waits for an entire petal tier before starting the next.

This preserves the global ordering invariant across multiple drones.

### Leave-nine rule

The cycle harvests:

```text
world_size² - 9
```

flowers and leaves nine mature Sunflowers.

The tests verify both:

- global descending petal order
- exact replant set matching harvested positions

### Replant barrier

Replanting begins only after selected harvests complete.

This prevents new flowers from contaminating the petal ordering of the current cycle.

### Comparison to msmith93/Flekay

agude focuses on correctness and parallel tier barriers.

It does not appear to optimize within-tier movement using nearest-neighbor routing as aggressively as the strongest msmith93/Flekay references.

That makes a useful benchmark decomposition:

- correctness/order architecture from agude
- movement ordering from msmith93/Flekay

## Parallel dispatch

The repository's job dispatcher is used for rows/columns and keeps work finite.

Unlike immortal worker pools, jobs end and return values.

This avoids cross-worker shared memory completely.

The tradeoff is repeated spawn cost between phases/cycles.

For long-running production, persistent workers may still win.

For reset automation, where stages are finite and frequently change, finite job batches may be more appropriate because they reduce lifecycle complexity.

## Static farm layout

`farm_layout.py` defines fixed priority regions for:

- Cactus
- Pumpkin
- Sunflower
- Tree/Bush strip
- Grass
- Carrot fill

This is separate from Top Hat's full-field producer paths.

The layout provides a normal mixed-farming architecture, while the reset planner can choose whole-field finite cycles when it needs a particular resource.

That distinction is useful:

> steady-state production layout and fastest-reset production policy do not need to be the same architecture.

## Test-driven specification

The tests are one of the main reasons to retain this reference.

Examples of asserted behavior include:

- already-unlocked Top Hat returns immediately
- malformed/empty cost stops visibly
- dynamic live costs are resampled
- overshoot is accepted
- unlock failure is attempted once
- no-progress stops after a bounded number of actions
- Power stockpile happens before later stages
- refill remains active until high watermark
- Fertilizer wait does not thrash Power refill
- live explicit Power requirements override static watermark policy
- observed Power consumption raises future reserve
- planting budgets preserve checkerboard geometry
- protected balances plus one-cycle budgets are enforced
- dependency cycles stop cleanly
- blocked dependency can fall back to unrelated useful work
- Gold production first funds Weird Substance then resamples
- Maze cost uses the exponential unlock-level formula
- global Sunflower petal ordering survives different drone capacities

This is much stronger provenance than an untested optimization claim.

## Known limitation: in-game validation pending

The task record:

`.agent/tasks/03-validate-top-hat-in-game-task-14.md`

is still marked `pending`.

Its acceptance criteria include live confirmation that:

- initial Power reaches adaptive high target
- between-watermark Power does not trigger Sunflowers
- low-watermark Power refills continuously to high target
- Fertilizer waits do not trigger a Sunflower cycle every flip

So the planner has strong static/simulated regression tests, but the upstream repository itself still records final in-game validation as pending at the pinned revision.

That distinction should be preserved.

## Fastest Reset relevance

The local project's fastest-reset objective is:

```text
Unlocks.Leaderboard
```

agude's planner ends at:

```text
Unlocks.Top_Hat
```

Therefore it is not a complete direct competitor.

But several abstractions are directly reusable:

1. live cost sampling
2. bounded one-action planning
3. dependency recursion
4. cycle detection
5. protected balances
6. next-cycle affordability
7. adaptive reserves
8. passive-resource wait actions
9. progress watchdog
10. post-action replanning

A full Leaderboard planner can apply the same model recursively across the entire unlock frontier.

## Strongest benchmark/research candidates

### Very high priority

1. bounded live-cost reset planner
2. protected final inventory vs producer cycle budget
3. dependency-cycle detection
4. adaptive Power hysteresis
5. Gold -> immediate Maze substance target -> resample
6. finite parallel Sunflower tiers
7. sparse Pumpkin final-tile polling
8. cocktail row/column Cactus sorter

### Compare against current local implementations

1. fresh-Maze wall follower vs persistent Maze reuse only as a cost baseline
2. finite spawn-per-row phases vs persistent-worker production
3. agude Sunflower tier barriers vs nearest-neighbor per-tier routing
4. Pumpkin row jobs vs static region workers
5. static farm layout vs current normal-farm persistent-worker architecture

## Snapshot contents

The complete pinned upstream repository is mirrored unchanged under `source/`.

It contains:

- 82 files
- 278,821 bytes
- game scripts
- tests
- CI/tooling
- game API metadata
- agent task history

Revision:

`15a68276c998039bcb90c0f6cbbdb006a6ce1065`

Tree:

`c6f9de46a1d8c3a6678a808300efd2aa905c779c`

The local source tree is Git-tree-identical to upstream.
