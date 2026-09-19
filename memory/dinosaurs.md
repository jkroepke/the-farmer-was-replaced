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

## Benchmark plan

Create/extend a Dinosaur benchmark that measures the actual leaderboard workload.

Required baseline/candidates:

1. current plain Hamiltonian
2. current skysdottir source-near reference
3. Flekay `drone.py` source-near port
4. MSmith two-stage/wavy `dino_leaderboard.py` source-near port
5. coil/strike/pre-return/return source-near port
6. one optimized local hybrid derived from the best structural ideas

Benchmark constraints:

- world size: 32
- all leaderboard unlocks/resources equivalent to `Leaderboards.Dinosaur`
- stop immediately once `num_items(Items.Bone) >= 33488928`
- deterministic seeds first; then a larger seed set for failure-rate/variance
- `simulate()` speedup: `10000`
- final `leaderboard_run()` launcher speedup: `256`
- source-near reference modes must preserve the source algorithm's core route/state/decision rules
- any mode that can fail must report completion rate; a fast invalid run is not competitive

Record at least:

- elapsed simulation time
- tick count if available
- final Bones
- Apples eaten / final tail length
- movement count
- failed moves
- strategy phase transition points
- correctness / success
- seed

## Recommended order

1. Add direct leaderboard-target benchmark/launcher first.
2. Port Flekay `drone.py` source-near.
3. Port MSmith `dino_leaderboard.py` source-near.
4. Retrieve/port the actual coil/strike Pastebin implementation.
5. Benchmark all source-near modes against current Hamiltonian at speedup 10000.
6. Only then build a local hybrid from the winner's strongest phases.
7. Validate the final candidate with `leaderboard_run(..., 256)`.

Do not replace production `dinosaur.py` based only on external reported times.


## 2026-09-19 benchmark v3 update

The two Reddit references were reviewed in detail:

- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1p0ox9z/my_fastest_dinosaur_run/
- https://www.reddit.com/r/TheFarmerWasReplaced/comments/1omrxi4/some_dinosaur_path_speed_comparisons/

The first Reddit post's Pastebins were successfully retrieved this time:

- https://pastebin.com/xsZL19rH
- https://pastebin.com/z4Rxj5CE

The durable route model is a four-phase state machine: **coil -> strike -> pre-return -> return**, followed by a deterministic safe sweep once the tail is large. A later commenter reports that real tail tracking plus westward double-backs improves the middlegame; this is not locally verified yet.

Local provenance is stored under:

`external/reddit-dinosaur-coil/`

The second Reddit/skysdottir reference confirms that its preparation phase clears the farm in parallel with multiple drones and converts the field to Soil. The author also states they had never checked whether this cleanup is necessary for Dinosaurs. Since current Wiki behavior says Apples cannot spawn on occupied tiles and Grass grows automatically on Grassland, cleanup is now a measured benchmark dimension rather than an assumption.

### Implemented benchmark

`bench_dinosaur.py` now contains 20 modes:

0. plain skyscraper Hamiltonian
1. skyscraper annealed shortcuts 50%
2. skyscraper hard shortcuts 25%
3. skyscraper hard shortcuts 50%
4. skysdottir Hilbert source-near reference
5. skyscraper fast-lane annealed 50%
6. heartbeat Hamiltonian
7. heartbeat annealed shortcuts 50%
8. heartbeat fast-lane annealed 50%
9. Hilbert Hamiltonian without shortcuts
10. Reddit coil/strike -> safe route at 33%
11. Reddit coil/strike -> safe route at 50%
12. Reddit coil/strike -> safe route at 66%
13. skyscraper fast-lane annealed 25%
14. heartbeat fast-lane annealed 25%
15. skyscraper fast-lane hard 25%
16. heartbeat fast-lane hard 25%
17. heartbeat hard shortcuts 50%
18. skyscraper fast-lane hard 50%
19. heartbeat fast-lane hard 50%

Setup modes:

0. no cleanup
1. `clear()`
2. serial harvest + Soil
3. parallel harvest
4. parallel harvest + Soil
5. source-style Sunflower Hat + parallel harvest + Soil

The main algorithm matrix uses setup mode 4. A separate setup sweep compares all six setup modes with representative route families.

Runner:

- `bench_dinosaur_run.py`
- version `dinosaur-v3`
- world 32
- targets 25/50/75/95/100%, where 100% is clamped to tail 1023
- seeds 1/2/3
- speedup 10000
- exact leaderboard-like starting items: 1e9 Cactus + 1e9 Power, all unlocks
- exact leaderboard threshold validation at board-1: 33,488,928 Bone
- 20 algorithms x 5 targets x 3 seeds = 300 main simulations
- 3 representative algorithms x 6 setup modes x 3 seeds = 54 setup simulations
- total: 354 simulations

Every successful child emits `DINOSAUR BENCH VALID`; failures emit `DINOSAUR BENCH INVALID`. The runner's summaries are labeled `RAW` because `simulate()` returns elapsed time and cannot directly return the child validity flag. Ignore a fast raw summary if any corresponding seed is invalid.

Implementation commits:

- strategy matrix: `624827d0520ca183353c0102562dfdc253d6fab1`
- setup/accounting fix: `92e420f70a8c76c498caf0d5beb2e06425456300`
- valid marker: `1ecfb09d2cdfd8078c182f7b5e7f48d291316e55`
- runner v3: `1f65a3663e6322d07b80496b71ea5bd84b4c2544`
- raw-summary marker: `7e51103180c4484ef68e91c974fcca5b05f94af9`
- canonical docs update: `68d906c195d9d063d100985490cc32343c96124f`

Static consistency was checked: 20 mode names match modes 0 through 19, six setup names exist, all required benchmark globals are referenced, and no duplicate function definitions were found.

Runtime correctness/performance of v3 is **not yet verified in the game**. The next step is to run `bench_dinosaur_run.py`, capture the complete output, reject every mode/seed with an `INVALID` marker, and then narrow the next benchmark around the valid fastest modes.


## 2026-09-19 Flekay deep-dive / benchmark v4

Further review of `Flekay/The-Farmer-Was-Replaced` found several Dinosaur-specific details that were not captured by the v3 benchmark.

### Historical `drone.py` result is not the current source

Flekay's Dinosaur README still reports `drone.py` at 18.741 s, but the current source cannot reproduce that result.

The README predates commit:

`d3a0fc555d5e78466fd1eb39e608b9ef0627b6b6`

("Simplify drone's dino movement logic", 2025-10-18).

That commit replaced the previous complete implementation with a three-phase skeleton whose `phase_two()` is intentionally unimplemented.

The complete predecessor was recovered from parent revision:

`fe4df71ae877a484b091c2fa276cae0a6f0e2039`

Useful old architecture:

1. parity-based aggressive Apple routing
2. early phase ends after about 50 Apples
3. build a deterministic "almighty" continuation from the resulting state
4. follow that continuation until blocked

Other historical Flekay Dino implementations are clearly 100-cell / 10x10-specific:

- `circle.py` contains explicit coordinates 0..9 and transitions around length 38
- `timon.py` uses coordinates up to y=9 and comments that length 34 was fastest
- `hybrid.py` switches roughly at lengths 18 and 34

Do not reuse 18/34/50 as absolute 32x32 lengths. v4 re-tests them as occupancy-style diagnostic targets.

### New early-phase diagnostic modes

`bench_dinosaur.py` now also contains:

- mode 20: Flekay-style simple axis greedy
- mode 21: Flekay parity greedy derived from the historical/current `drone.py` phase-one policy

Diagnostic targets:

- 10%
- 18%
- 25%
- 34%
- 50%

These modes are early-phase experiments. They are not assumed to be safe near full occupancy.

### Cheap failed-move probing

Flekay frequently uses:

```text
if not move(preferred):
    move(fallback)
```

Its historical tick measurements record both `can_move()` and a failed `move()` as one tick. If both possible successful directions are known-safe, optimistic movement can therefore avoid a separate `can_move()` check.

This is only useful inside constrained safe movement policies. It must not replace cycle/tail safety validation for arbitrary shortcuts.

### Cleanup topology

Flekay's historical line-formation benchmark reports:

```text
for_all.py                  25006 runtime ticks
for_all_dual.py             16224 runtime ticks
for_all_sync_col/row.py     16224 runtime ticks
```

The reusable lesson is that the spawn chain itself can be parallelized.

v4 adds setup modes:

- 6: Flekay-style line-spawn Soil cleanup
- 7: Flekay-style dual-spawner Soil cleanup

The local benchmark result, not the historical upstream tick count, decides whether either setup is useful for Dinosaur leaderboard runs.

### Exact leaderboard harvest-size sweep

The Dinosaur leaderboard checks total Bones, not one tail.

v4 therefore adds an experiment that repeatedly harvests/restarts at:

- 25%
- 33%
- 50%
- 66%
- 75%
- 95%
- board-1

until:

```text
num_items(Items.Bone) >= 33488928
```

This directly answers whether several shorter fast runs can beat one almost-full tail after accounting for restart cost and the expensive early Dinosaur moves.

Compared route families:

- mode 0: plain Hamiltonian
- mode 4: skysdottir Hilbert shortcut reference
- mode 11: Reddit coil/strike 50% transition

### Flekay route-planning negative results

Do not add generic all-pairs Dinosaur routing based on Flekay's non-wrapping benchmark.

Historical values:

```text
goto.py        setup 0.0002 s, 7590 ticks/benchmark
runto_local.py setup 7.7344 s, 7470 ticks/benchmark
```

The precomputed all-pairs map has a very large setup cost for a small warm-path saving.

The generic pathfinding benchmark also shows that planning cost can dominate movement savings as target counts grow. Additionally, the README's `divinepath` result rows are not reproducible from the current pinned source: `benchmark.py` does not import it and no implementation exists in the directory.

### Hot-path follow-up

Flekay's tick research suggests later ablations for any winning shortcut family:

- integer cell ID / nested list instead of tuple-key dict path lookup
- avoid temporary per-step direction lists
- fixed early cutoff vs `random()` annealing
- explicitly tracked head x/y vs repeated `get_pos_x()/get_pos_y()`
- precomputed direction sequence vs structured Hamiltonian loops

Do this only after route-level v4 identifies which family is worth optimizing.

### v4 implementation

Commits:

- `be91a2d6ad846490130bea03cb965d48d86f085a` — Flekay early-phase diagnostics, line/dual cleanup, repeated Bone-target support
- `4ed309863c7199b3d3a9bf08bfd1137a7b57093a` — `dinosaur-v4` runner
- `965fd30828350a4167e5f74bb71ca91a4b213166` — canonical Flekay deep-dive documentation

v4 simulation count:

```text
main route matrix         300
setup sweep                72
Flekay early diagnostics   30
leaderboard harvest sweep  63
total                      465
```

Runtime correctness and performance remain unverified until `bench_dinosaur_run.py` is executed in the game/simulator and the complete `VALID` / `INVALID` output is inspected.


## 2026-09-19 Dinosaur v5 accounting correction

The first live v4 preview revealed an off-by-one in the benchmark's tail terminology.

At nominal target 25%, the child reported occupied length 256 but harvested exactly 2,080,800 Bones:

`255^2 * 32 = 2,080,800`

Therefore `CURRENT_TAIL_LENGTH` and `REF_ACTUAL_TAIL_LENGTH` were really **head + tail occupied length**. Bone rewards count only tail segments.

v4 consequently stopped one Apple early at every target and is not valid final benchmark data. In particular, nominal board-1 would have produced only:

`1022^2 * 32 = 33,423,488`

instead of the leaderboard requirement 33,488,928.

v5 fix:

- `target_tail_length()` = actual reward tail segments
- `target_snake_length()` = head + tail = target tail + 1
- all route termination checks compare occupied counters with `target_snake_length()`
- every successful harvest validates exact cycle gain `target_tail_length()^2 * 32`
- full 32x32 target = 1023 tail segments / 1024 occupied cells / 33,488,928 Bones

Commits:

- `7febc4bd1238a54e9ae4456ab3621d9d0625241d`
- `cd3070188dce3da68a5c065fb16caafa5917c7f1`

Incomplete v4 Seed 1 / nominal-25% preview signal only:

- Hamiltonian: 1176.76 s
- skysdottir reference: 677.80 s (~42.4% faster than Hamiltonian)
- heartbeat annealed shortcuts: 999.26 s (~15.1% faster)
- heartbeat fast-lane annealed: 1133.28 s (~3.7% faster)
- tested skyscraper shortcut/fast-lane variants were ~46-59% slower

These relative values are only preview evidence. Re-run the full suite as `dinosaur-v5`.


## 2026-09-19 Dinosaur v6 Reddit coil/strike correction

A live v4 screenshot taken after mode 9 completed showed the next candidate (mode 10) coiling on the west side while an Apple was visible on the east side.

The **coil-before-strike behavior itself is intentional** in the Reddit algorithm: the tail is first shaped into a known safe coil, then the head strikes east-side Apples.

Comparison with the actual Pastebin nevertheless found two local port bugs:

- same-column Apple progress used the old/pre-move Y instead of the current Apple Y relative to the newly measured next Apple
- the coil -> strike transition omitted the source's north-edge alignment and persistent `fixFlag1` handling

Fixed in:

- `1e47c5201207fac0d6cf35b23f8fd56c2483c477`

Runner is now `dinosaur-v6` and emits `DINOSAUR RUN START ...` before each simulation so the current candidate is always visible:

- `7081dc129241652273e6793d3352db487faf3fdf`

Do not use or continue v4 output. v4 is invalid both because of the head/tail accounting bug and because its Reddit modes 10/11/12 were not source-near enough.
