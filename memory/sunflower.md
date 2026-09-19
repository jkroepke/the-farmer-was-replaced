# Sunflower

## Scope

Dedicated research for the multi-drone Sunflower leaderboard.

This work is intentionally separate from normal farming. Normal-farm Power is an
inventory-maintenance problem; the Sunflower leaderboard is a finite
time-to-target problem and can justify full-field phase barriers and repeated
worker fan-out that would be unattractive in the normal mixed farm.

Success condition supplied for the current leaderboard:

```python
num_items(Items.Power) >= 100000
```

The submitted program must terminate after the threshold is reached.

## Mechanics used by the implementation

The current repository `builtins.py` says:

- Sunflowers have a measurable petal count.
- With at least 10 Sunflowers present, harvesting a current maximum-petal
  Sunflower receives the large Power bonus.
- The local game file currently describes that bonus as 5x.

There is a documentation conflict worth preserving: the current wiki page
queried on 2026-09-19 describes the bonus as 8x. Older/current community
simulators also disagree about the multiplier.

Do not hard-code expected Power-per-harvest from either value. The leaderboard
code only depends on the ordering invariant and the benchmark validates the
actual runtime.

For ordered harvesting, leaving exactly nine flowers after the phase is enough:
the final selected flower is harvested while ten flowers still exist, and its
removal leaves nine.

## References reviewed

### Flekay

Pinned local snapshot:

`external/flekay-the-farmer-was-replaced/`

The single-drone Sunflower benchmark table records:

```text
power-fart.py  6600 items/min
power-spam.py  6310 items/min
power-path.py  3840 items/min
power-hash.py  3470 items/min
power-runs.py  2540 items/min
```

The important algorithmic candidates are:

- reroll every Sunflower to seven petals, so all accepted flowers are tied for
  the current maximum;
- petal buckets plus ordered harvesting;
- nearest-neighbor movement within one petal bucket;
- batch harvesting before replanting versus immediate replant.

These are upstream measurements, not current-local benchmark results.

### msmith93

Pinned local snapshot:

`external/msmith93-thefarmerwasreplaced/`

Relevant files:

- `source/sunflower_leaderboard.py`
- `source/multidrone/sunflowers.py`
- `source/claude/`

The multi-drone implementation supplies the key phase-barrier idea:

1. plant the field in parallel;
2. process one petal value at a time from high to low;
3. wait for all workers in the tier;
4. only then advance to the next petal value.

The single-drone optimization series is useful for movement/path and watering
hypotheses but should not be assumed to transfer to the 32-drone leaderboard.

### agude

Pinned local snapshot:

`external/agude-the-farmer-was-replaced/`

Its tested Sunflower cycle contributes the strongest correctness structure:

- row workers return measured petal buckets;
- the controller preserves global 15 -> 7 ordering;
- equal-petal work can run in parallel;
- a complete tier is a synchronization barrier;
- nine flowers are left behind;
- replanting happens only after the ordered harvest phase.

The local implementation keeps those invariants but also benchmarks a smaller
count-only representation to avoid carrying all 1024 coordinates/petal values
through every worker phase.

### Reddit archive

`external/reddit-normal-farm-sunflower-research/`

The archived discussions contain competing observations:

- simple multi-drone harvest/replant can beat an expensive ordered
  implementation;
- synchronized smaller regions / ordered phases can also work well.

Therefore simple unordered farming remains a benchmark control instead of being
discarded theoretically.

### Local spawn benchmark

The current spawn research found binary-tree fan-out materially faster than
serial parent spawning for 32 workers. Sunflower modes therefore include both
tree and linear controls so the spawn result is tested in this workload rather
than assumed.

## Current implementation

Files:

- `sunflower_lb.py` - finite algorithms and benchmark modes
- `bench_sunflower.py` - one simulated leaderboard target
- `bench_sunflower_run.py` - multi-seed comparison
- `lb_sunflower.py` - provisional finite leaderboard program
- `lb_sunflower_run.py` - real leaderboard launcher at speedup 256

The measured leaderboard implementation uses mode 9:

```text
scan-tree-counted
```

It is the measured winner of `sunflower-v2-bounded7`: 371.54 s average across
seeds 1, 2, and 3.

Architecture:

1. use binary-tree fan-out across 32 column workers;
2. plant/repair each column and return only nine petal counts, not all
   coordinates;
3. aggregate global counts in the controller;
4. determine the lowest tier that may be harvested while leaving exactly nine;
5. distribute the keep quota for that floor tier across columns;
6. scan/harvest 15 down to that floor, with a full worker barrier after every
   tier;
7. never replant during the ordered harvest phase;
8. replant only empty tiles after the phase and rebuild the compact counts;
9. stop after a completed tier once Power is at least 100000.

The tier itself is atomic. Workers do not stop in the middle of a tier merely
because the target was crossed, because that could make controller state diverge
from the actual field.

## Benchmark modes

`sunflower-v2-bounded7` screens the following leaderboard-relevant modes:

```text
tier-tree-no-care
equal7-tree-no-care
dumb-tree-no-care
tier-linear-no-care
scan-tree-bounded7
scan-tree-counted
scan-linear-counted
```

Meaning:

- `tier-*`: cache the complete 32x32 petal matrix and travel directly to known
  positions;
- `equal7-*`: Flekay-inspired rerolling until every harvested/replanted flower
  is exactly seven petals;
- `dumb-*`: intentionally ignores global petal ordering and acts as the simple
  multi-drone community control;
- `scan-tree-bounded7`: repeated per-tier scans with a bounded seven-petal
  reserve of at most one world width (32 on the leaderboard); excess seven-petal
  flowers are harvested after higher tiers so random replants cannot accumulate
  an ever-growing permanent tier;
- `scan-tree-counted`: scans tiers but keeps only nine counts per column and
  leaves exactly nine flowers;
- `linear` versus `tree`: isolates worker-spawn topology.

Water/Fertilizer variants remain in `sunflower_lb.py` as explicit ablations,
but they are excluded from the first leaderboard-equivalent screen.

## Simulation start state

The official resource-leaderboard documentation states that resource
leaderboards start with all unlocks and the inputs needed for the target crop,
but it does not spell out the exact Sunflower item dictionary.

A recently crawled public leaderboard implementation
(`enihsyou/The-Farmer-Was-Replaced/leaderboards.py`) uses this equivalent
Sunflower simulation:

```python
items = {
    Items.Carrot: 1000000000
}
```

`sunflower-v2-bounded7` uses that as a benchmark proxy. Treat it as a community-derived
proxy until the actual leaderboard start state is independently confirmed.

## Current benchmark result

The complete `sunflower-v2-bounded7` run used world 32x32, target 100000
Power, seeds 1/2/3, speedup 10000, and the Carrot-only leaderboard simulation
proxy.

| Mode | Average |
| --- | ---: |
| `scan-tree-counted` | **371.54 s** |
| `scan-tree-bounded7` | 377.12 s |
| `scan-linear-counted` | 425.91 s |
| `tier-tree-no-care` | 504.73 s |
| `dumb-tree-no-care` | 506.54 s |
| `tier-linear-no-care` | 561.35 s |
| `equal7-tree-no-care` | 663.31 s |

Decision: keep `lb_sunflower.py` on mode 9, `scan-tree-counted`.

Full measurements and provenance live in `bench/sunflower.md`.

## Normal-farm separation

Do not copy the leaderboard winner into `farm.py` automatically.

The normal farm already has its own Power/Sunflower placement research in
`memory/farm.md`. A leaderboard winner may spend the entire 32x32 map on
Sunflowers and repeatedly synchronize 32 drones; that is acceptable for this
finite leaderboard and may be bad for normal mixed-resource throughput.

## Benchmark record

Measured Sunflower leaderboard results are maintained in `bench/sunflower.md`.

| Kind | Statement | Evidence |
| --- | --- | --- |
| Conclusion | The old leave-all-seven scan can accumulate seven-petal flowers until productive higher tiers disappear. | `bench/sunflower.md`, interrupted `sunflower-v1` run |
| Fix | Use the bounded-seven implementation and no-progress guard for the follow-up suite. | `f962b8615880d92b573beaa3c30389b817e32dc0` |
| Result | `scan-tree-counted` is the measured winner at 371.54 s average across seeds 1-3. | `bench/sunflower.md` |
| Decision | Keep the real multi-drone Sunflower leaderboard on mode 9. | `lb_sunflower.py` |
