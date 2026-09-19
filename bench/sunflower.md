# Benchmark: Sunflower

## Scope

| Field | Value |
| --- | --- |
| Topic | Sunflower |
| Purpose | Compare finite 32x32 Sunflower leaderboard algorithms to reach the Power target while preserving ordering correctness. |
| Implementation | `sunflower_lb.py`, `bench_sunflower.py` |
| Runner | `bench_sunflower_run.py` |
| Primary metric | Elapsed time and ticks to the Power target. |
| Success condition | Terminate with `num_items(Items.Power) >= 100000`; candidate must report `valid True`. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| `sunflower-v1` | `6a34d906f5ee5cb2902fa891fe268cbff0e1b151` | 32x32 / seed 1 partial output | Interrupted; historical |
| `sunflower-v2-bounded7` | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` | 32x32 / seeds 1-3 | Complete; measured winner `scan-tree-counted` |

## Results

### interrupted sunflower-v1

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `6a34d906f5ee5cb2902fa891fe268cbff0e1b151` |
| Benchmark/version | `sunflower-v1` |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Source state recorded |

#### Measurements and observations

| Field | Value |
| --- | --- |
| Source commit | `6a34d906f5ee5cb2902fa891fe268cbff0e1b151` |
| Benchmark/version | `sunflower-v1` |
| Runner | `bench_sunflower_run.py` |
| Implementation | `sunflower_lb.py` |
| Requested speedup | 10000 |
| Target | 100000 Power |
| Status | Partial/interrupted; only completed rows are historical evidence. |

The source commit above is the final code-state commit that defines the exact `sunflower-v1` screen shown by the recorded output. The later `87f80fe175f81ae0fd43d5bcb99240f25676832d` commit changed documentation only.


-----

### Interrupted sunflower-v1 result and root cause

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | `sunflower-v1`, `sunflower-v2-bounded7` |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The first supplied `sunflower-v1` run reached these seed-1 results before
stalling in the old `scan-tree-leave7` mode:

```text
tier-tree-no-care    504.77
equal7-tree-no-care  663.78
dumb-tree-no-care    507.34
tier-linear-no-care  561.17
```

The first three completed modes were valid at the 100000-Power target; the
linear ordered control was also valid.

The old scan mode had a deterministic algorithmic failure mode:

1. it left every seven-petal Sunflower standing;
2. every replant of harvested 8..15 tiles had another chance to roll seven;
3. those new sevens were also retained forever;
4. the permanent seven-petal population therefore grew monotonically;
5. the harvestable 8..15 population shrank every cycle;
6. the mode could converge toward a field with no productive higher tier and
   loop below the Power target.

This was not a drone-memory or binary-tree-spawn failure.

Fix commit: `f962b8615880d92b573beaa3c30389b817e32dc0`.

`scan-tree-bounded7` now keeps at most `WORLD_SIZE` seven-petal flowers
(32 for the leaderboard). When more sevens exist, tier 7 is harvested down to
that quota after higher tiers. A scan-cycle progress guard also aborts visibly
with `SUNFLOWER SCAN NO PROGRESS` if a full harvest phase produces no Power.

Because the candidate semantics changed, the runner version was bumped to
`sunflower-v2-bounded7`. Do not merge the interrupted v1 timings into a v2
summary without marking their provenance.

-----

### sunflower-v2-bounded7

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` |
| Benchmark/version | `sunflower-v2-bounded7` |
| Requested speedup | 10000 |
| Seeds | 1, 2, 3 |
| Canonical status | Complete three-seed benchmark |

#### Measurements and observations

| Field | Value |
| --- | --- |
| Fix commit | `f962b8615880d92b573beaa3c30389b817e32dc0` |
| Version bump commit | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` |
| Target | 100000 Power |
| Status | Complete. All seven modes reported `valid True` across all three seeds. |

##### Per-seed results

| Mode | Seed 1 | Seed 2 | Seed 3 |
| --- | ---: | ---: | ---: |
| `tier-tree-no-care` | 504.77 s | 505.90 s | 503.52 s |
| `equal7-tree-no-care` | 663.78 s | 654.84 s | 671.29 s |
| `dumb-tree-no-care` | 507.34 s | 503.16 s | 509.10 s |
| `tier-linear-no-care` | 561.17 s | 561.72 s | 561.17 s |
| `scan-tree-bounded7` | 377.89 s | 376.60 s | 376.87 s |
| `scan-tree-counted` | **372.15 s** | **372.42 s** | **370.04 s** |
| `scan-linear-counted` | 424.92 s | 426.60 s | 426.20 s |

##### Final summary

| Mode | Avg time | Min | Max | Avg ticks |
| --- | ---: | ---: | ---: | ---: |
| `scan-tree-counted` | **371.54 s** | **370.04 s** | **372.42 s** | **2,223,888** |
| `scan-tree-bounded7` | 377.12 s | 376.60 s | 377.89 s | 2,257,843 |
| `scan-linear-counted` | 425.91 s | 424.92 s | 426.60 s | 2,551,904 |
| `tier-tree-no-care` | 504.73 s | 503.52 s | 505.90 s | 3,017,477 |
| `dumb-tree-no-care` | 506.54 s | 503.16 s | 509.10 s | 3,055,109 |
| `tier-linear-no-care` | 561.35 s | 561.17 s | 561.72 s | 3,359,582 |
| `equal7-tree-no-care` | 663.31 s | 654.84 s | 671.29 s | 3,753,577 |

`scan-tree-counted` is the measured winner.

| Comparison | Result |
| --- | ---: |
| vs `tier-tree-no-care` | 26.39% less wall-clock time |
| vs `dumb-tree-no-care` | 26.65% less wall-clock time |
| vs `scan-tree-bounded7` | 1.48% less wall-clock time |
| vs `scan-linear-counted` | 12.77% less wall-clock time |

The final Power values for `scan-tree-counted` were 100486.21, 100592.43,
and 100475.86 for seeds 1, 2, and 3 respectively, so all three runs satisfied
the target and terminated successfully.

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Measured | `scan-tree-counted` is the fastest valid mode at 371.54 s average across seeds 1-3. | `sunflower-v2-bounded7` complete run |
| Measured | `scan-tree-counted` is 26.39% faster than `tier-tree-no-care`. | 371.54 s vs 504.73 s |
| Measured | The counted binary-tree scan is 12.77% faster than its linear equivalent. | 371.54 s vs 425.91 s |
| Measured | Bounded-seven retention is valid but slightly slower than exact counted retention. | 377.12 s vs 371.54 s |
| Decision | Use `scan-tree-counted` (mode 9) for the multi-drone Sunflower leaderboard. | Complete three-seed benchmark |

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out the source commit listed for the result group. |
| 2 | Run the matching benchmark runner from Scope. |
| 3 | Preserve complete output and update this file without changing historical values. |

## Notes

| Kind | Detail |
| --- | --- |
| Note | No additional notes. |
