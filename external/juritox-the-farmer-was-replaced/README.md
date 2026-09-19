# juritox/the-farmer-was-replaced

## Upstream

- URL: https://github.com/juritox/the-farmer-was-replaced
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `544bb832ffcec00aacf2c8dd5278bdb534ab674b`
- License: MIT
- Upstream files: 24
- Upstream total size: 377364443 bytes
- Mirrored source/text files: 15
- Mirrored source/text size: 29242 bytes
- Binary media files: 9
- Binary media size: 377335201 bytes
- Snapshot verification: every upstream non-media blob is mirrored with the identical Git blob SHA
- Media status: large GIF/PNG blobs are recorded in `source/MEDIA-UPSTREAM.md` because the GitHub connector cannot transfer these repository-to-repository

The repository was last tested upstream against game BuildID `17763496` on 2025-05-09. Treat mechanics and performance assumptions as historical until revalidated against the current game.

## Executive summary

This is a compact, mostly single-drone TFWR automation repository.

Compared with the newer external references in this project, it is less interesting as a current performance implementation and more useful as:

- a simple baseline for each resource mechanic
- an example of a centralized resource scheduler
- a descending-petal Sunflower implementation
- a straightforward giant-Pumpkin correctness loop
- a single-drone 2D Cactus sorting approach
- a simple right-hand-rule Maze solver
- an older deterministic Dinosaur traversal
- a record of pre-Megafarm optimization thinking

The upstream README itself describes the scripts as work in progress and lists many possible optimizations that were not yet implemented.

This makes the repository useful for answering:

> What does a clear, relatively direct implementation look like before adding modern multi-drone/path-caching/precomputation optimizations?

## Repository map

### Orchestration

- `scripts/main.py` — resource scheduler
- `scripts/auto_unlock.py` — opportunistic unlock loop
- `scripts/run_simulation.py` — simulation launcher
- `scripts/utilities.py` — wrap-aware coordinate movement helper

### Resource scripts

- `scripts/hay_harvest.py`
- `scripts/wood_harvest.py`
- `scripts/carrot_harvest.py`
- `scripts/pumpkin_harvest.py`
- `scripts/cactus_harvest.py`
- `scripts/power_harvest.py`
- `scripts/gold_harvest.py`
- `scripts/bone_harvest.py`

### Media

The upstream repository also contains one PNG and eight large animated GIFs showing the scripts in action.

These are provenance-recorded in `source/MEDIA-UPSTREAM.md`.

They are not required to understand the algorithms.

## Main scheduler

`scripts/main.py` is a threshold-driven resource planner.

Configuration:

```text
priority = None
amount = 100000
WATER_THRESHOLD = 0.75
```

If `priority` is set, the script farms only that resource.

Otherwise it uses a fixed decision tree:

1. Power
2. Gold
3. Weird Substance
4. Bone
5. Cactus
6. Pumpkin
7. Carrot
8. Wood
9. Hay
10. auto-unlock when all thresholds are satisfied

After one complete threshold stage it increases `amount`:

- multiply by 10 while below 10,000
- otherwise multiply by 2

### Useful idea

The script treats farming as a dependency-aware resource scheduler rather than running one static crop forever.

Several conditions encode rough dependencies:

- Power requires enough Carrot
- Gold requires Weird Substance
- Weird Substance requires Fertilizer
- Cactus requires Pumpkin
- Pumpkin requires Carrot
- Carrot requires Hay + Wood

This is conceptually useful as a simple baseline.

### Limitations

The scheduler is not a full tech-tree planner.

It does not:

- inspect the actual cost graph before choosing a resource
- compute exact deficits per dependency
- account for setup/field-conversion cost
- choose a strategy based on expected throughput
- coordinate multiple simultaneous resources

Most resource functions begin with `clear()`, so every mode switch destroys the previous field layout and pays setup cost again.

## Important `amount` semantics

The variable called `amount` does not mean the same thing in every harvester.

Examples:

- Hay decrements it for actual harvested tiles
- Wood decrements it when Tree/Bush planting succeeds
- Carrot decrements it by the Wood planting cost
- Pumpkin decrements it by the Carrot planting cost
- Cactus decrements it by the Pumpkin planting cost
- Power decrements it by the Carrot planting cost
- Bone decrements it by a fixed world-size-based estimate

So the value is partly:

- harvest target
- planting budget
- loop-control estimate

depending on the resource.

That makes it unsuitable as a precise throughput/accounting interface.

For a modern planner, use:

```text
target inventory - current inventory
```

and measure actual yield rather than relying on a shared abstract counter.

## Hay

`hay_harvest.py` is intentionally minimal.

It:

1. calls `clear()`
2. walks one full column
3. harvests mature Grass/Hay
4. moves East
5. repeats

Over multiple loops it cycles through columns.

This is useful as a low-computation baseline.

The upstream README itself suggests two possible micro-optimizations:

- avoid full-field traversal if edge-only movement produces better cadence
- omit `can_harvest()` if timing guarantees maturity

Those are benchmark questions, not universal improvements.

## Wood

`wood_harvest.py` uses the classic checkerboard pattern:

- Tree when x/y parity matches
- Bush otherwise

This avoids orthogonally adjacent Trees while still using every tile for Wood production.

Optional Fertilizer mode is used to produce Weird Substance from Trees.

### Useful baseline

The geometry is simple and deterministic.

### Caveats

The script repeatedly checks/tills ground even though the upstream README notes that this may be unnecessary for Tree/Bush.

It also treats successful planting as progress on `amount`, not actual harvested Wood.

No companion optimization is used.

## Carrot

`carrot_harvest.py`:

- ensures Soil
- harvests when possible
- plants Carrot
- conditionally waters
- decrements its remaining counter by the Wood component of planting cost

This is a straightforward serial baseline.

It does not exploit:

- companions
- persistent prepared Soil state
- multi-drone columns
- targeted growth scheduling

## Pumpkin

`pumpkin_harvest.py` tries to produce one giant whole-field Pumpkin.

The flow is:

1. clear
2. plant the field
3. scan for any tile whose entity is not Pumpkin
4. only harvest when the scan finds no hole
5. otherwise repeat planting/repair

### Useful correctness idea

The script explicitly refuses to harvest while there is a missing/dead Pumpkin.

### Performance limitation

`detect_dead_pumpkin()` performs a field scan and returns as soon as it finds the first hole.

It does not remember the hole coordinate.

The next outer pass again traverses/attempts planting across the field.

This is the exact inefficiency addressed by later references that keep:

- dead-cell lists
- unverified-cell queues
- worker-local repair state
- fixed Pumpkin regions

So this implementation is a good source-near baseline for measuring the value of those optimizations.

## Cactus

`cactus_harvest.py` implements a single-drone iterative 2D relaxation sorter.

It distinguishes:

- interior tiles
- four corners
- four edges

Interior logic tries to enforce:

- North >= current
- East >= current
- South <= current
- West <= current

by swapping with out-of-order neighbors.

The full field is scanned repeatedly until one pass produces zero swaps.

Then one harvest attempts to trigger the chain.

### Interesting difference from row/column sorting

This is not:

```text
sort all rows
then
sort all columns
```

Instead each tile can compare/swap in several directions during the same global relaxation pass.

That is a useful algorithmic comparison candidate.

### Performance caveat

It is expensive:

- many `measure()` calls
- repeated whole-field passes
- no parallelism
- possible re-measuring after local swaps

Later phase-parallel Cactus implementations are much better performance candidates, but this file is a clean single-drone correctness baseline.

## Power / Sunflowers

`power_harvest.py` is one of the more interesting files.

It recognizes the need to harvest Sunflowers in descending petal order.

### Plant phase

It:

- clears
- prepares Soil
- plants Sunflowers
- optionally waters

### Measurement phase

`measure_petals()` scans the field and stores petal counts in one list.

15-petal Sunflowers are harvested immediately.

### Ordered harvest phase

The script repeatedly:

1. computes the current maximum remaining petal count
2. scans the field
3. harvests Sunflowers matching that count
4. removes one matching value from the list
5. advances to the next lower maximum

This preserves the core descending-petal idea without storing coordinates.

### Strength

The algorithm understands that arbitrary mature-Sunflower harvest is not equivalent to petal-aware harvesting.

### Cost

Because it stores only petal counts and not positions, it repeatedly scans the entire field to find each current maximum group.

This is far more movement than:

- coordinate bins
- nearest-neighbor routing
- static per-worker bins
- precomputed harvest paths

`measure_petals()` also calls `measure()` twice on the same tile in the 15-petal check path, adding unnecessary interpreter work.

This is an excellent baseline for quantifying the value of coordinate-aware petal bins.

## Gold / Maze

`gold_harvest.py` uses a simple wall-following policy.

At each step it effectively:

1. turns right and tries to move
2. if blocked, turns back left and tries forward
3. if still blocked, turns left again

This is a right-hand-style local Maze traversal.

It keeps no map and performs no BFS/DFS graph search.

### Cost formula warning

The pinned source computes/uses:

```text
get_world_size() * num_unlocked(Unlocks.Mazes)
```

for Weird Substance.

This differs from this project's current Maze code, which uses an exponential unlock-level factor.

Therefore the upstream Maze resource accounting is an older-version assumption and must not be copied into current production.

### Direction state

`direction` is a module global and is not explicitly reset to North for every new Maze.

The wall follower can still operate from another heading, but benchmark ports should make starting-state differences explicit.

## Dinosaur / Bone

`bone_harvest.py` is an older deterministic traversal.

It:

- forces an even world size
- clears
- equips Dinosaur Hat
- follows repeated vertical/return sweeps

It does not:

- call `measure()` to target the next Apple
- track body coordinates
- maintain Hamiltonian cycle indices
- evaluate shortcuts
- compute Bone throughput

### Movement as control flow

Several loops intentionally execute movement up to/at boundaries and rely on failed moves as part of the pattern.

This matches older simple Dinosaur implementations but is not competitive with the newer cycle/shortcut references.

### Accounting caveat

The function reduces `amount` by a fixed world-size amount during one part of the traversal rather than from observed Apple/Bone production.

It is therefore only a rough loop controller.

### Harvest lifecycle caveat

The function does not explicitly switch away from Dinosaur Hat at normal function completion.

Since removing the hat is what harvests the current tail, a standalone call should not be assumed to have produced its final Bone yield merely because the function returns.

For current production, explicit tail-harvest lifecycle must be part of the strategy.

## Auto unlock

`auto_unlock.py` iterates all values in `Unlocks`.

For each unlock with a non-empty cost it attempts `unlock()`.

This is a simple opportunistic pass.

It does not encode:

- dependency order
- relative strategic priority
- target unlock levels
- endgame exceptions

The outer resource loop can eventually revisit failed unlocks after more resources are gathered.

Useful as a baseline, but much less intentional than the explicit unlock-order/frontier strategies elsewhere in this project.

## Movement utility

`utilities.go_to(x, y)` chooses the shorter wrapped direction independently on X and Y.

This is appropriate for ordinary farm movement.

Do not reuse the wrap assumption for Dinosaur movement, where edge wrapping is unavailable.

## Simulation helper

`run_simulation.py` builds a large starting inventory and calls:

```text
simulate("simulation", ...)
```

The pinned repository does not contain a matching `simulation.py` file.

So this is a launcher/template rather than a self-contained reproducible benchmark suite at the pinned revision.

It also uses speedup 1, so it is not designed as a high-throughput batch benchmark runner.

## No Megafarm architecture

The pinned repository predates or does not use the multi-drone architectures that dominate newer optimization references.

There is no:

- `spawn_drone()` worker pool
- persistent spatial partitioning
- phase-parallel Cactus
- parallel Pumpkin regions
- shared/current-worker queue design

That is useful context when comparing performance.

A newer implementation beating these scripts does not necessarily prove a better crop algorithm; part of the gain may simply come from Megafarm parallelism.

## Best uses in this project

### Strong baseline candidates

1. single-drone Cactus relaxation sorter
2. descending-petal Sunflower without coordinate bins
3. whole-field Pumpkin hole scan
4. simple Maze wall follower
5. simple Wood checkerboard
6. threshold-based resource scheduler

### Mainly historical/reference value

1. Dinosaur sweep without Apple targeting
2. old Maze substance-cost formula
3. generic amount/budget accounting
4. full-field resets between resource modes

## Comparison to newer external references

### Versus MateusMarochi

MateusMarochi adds persistent/static multi-drone workers and specialized Pumpkin layouts.

juritox is a better simple single-drone baseline.

### Versus nql1314

nql1314 adds aggressive precomputation, static layouts, map caching, persistent-worker experiments, and historical shared-memory coordination.

juritox is much smaller and easier to reason about, but far less optimized.

### Versus skysdottir

skysdottir's Dinosaur work is algorithmically much more advanced, with indexed cycles and safe shortcutting.

juritox's Dinosaur file is useful only as a simple historical baseline.

### Versus msmith93

msmith93 contains more direct leaderboard experiments and simulator-backed Sunflower optimization.

juritox's descending-petal approach is a useful earlier/less optimized comparison point.

## Snapshot validity

The upstream README states:

```text
Latest tested game BuildID: 17763496
Last tested: 2025-05-09
```

That predates many later game updates represented elsewhere in this research repository.

Therefore:

- algorithms can still be useful
- current mechanics must be revalidated
- numeric resource costs must not be trusted without checking current behavior
- performance conclusions require fresh benchmarks

## Media manifest

The nine upstream media blobs total 377,335,201 bytes.

They are:

- eight animated GIF demonstrations
- one PNG screenshot

The GitHub connector used for this archive cannot transfer blobs of this size/type repository-to-repository.

`source/MEDIA-UPSTREAM.md` records for each file:

- upstream path
- Git blob SHA
- exact size

This is a provenance limitation only; all code/text needed for analysis is mirrored byte-identically.

## Snapshot contents

Mirrored unchanged under `source/`:

- `.gitignore`
- `LICENSE`
- upstream `README.md`
- all 12 scripts

Plus:

- `MEDIA-UPSTREAM.md` as local provenance metadata for the 9 unmirrored binary assets

Revision: `544bb832ffcec00aacf2c8dd5278bdb534ab674b`.
