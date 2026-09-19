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
| `sunflower-v2-bounded7` | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` | 32x32 / seeds 1-3 | Partial: seeds 1-2 complete; seed 3 controls complete |

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


-----

### sunflower-v2-bounded7

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` |
| Benchmark/version | `sunflower-v2-bounded7` |
| Requested speedup | 10000 |
| Seeds | 1, 2, 3 |
| Canonical status | Partial run; retain until seed 3 scan modes complete |

#### Measurements and observations

| Field | Value |
| --- | --- |
| Fix commit | `f962b8615880d92b573beaa3c30389b817e32dc0` |
| Version bump commit | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` |
| Benchmark/version | `sunflower-v2-bounded7` |
| Status | Partial preview available; full three-seed run still in progress. |


#### Preview results

Status: **partial**. Seeds 1 and 2 completed all seven modes. Seed 3 has
completed the four non-scan controls and is currently executing
`scan-tree-bounded7`.

##### Seed 1

| Mode | Time | Ticks | Final Power | Valid |
| --- | ---: | ---: | ---: | --- |
| `tier-tree-no-care` | 504.77 s | 3,017,721 | 100,468.30 | yes |
| `equal7-tree-no-care` | 663.78 s | 3,776,706 | 103,035.43 | yes |
| `dumb-tree-no-care` | 507.34 s | 3,059,239 | 100,006.83 | yes |
| `tier-linear-no-care` | 561.17 s | 3,358,793 | 100,466.30 | yes |
| `scan-tree-bounded7` | 377.89 s | 2,262,596 | 100,513.07 | yes |
| `scan-tree-counted` | **372.15 s** | **2,227,645** | 100,486.21 | yes |
| `scan-linear-counted` | 424.92 s | 2,545,856 | 100,220.57 | yes |

Seed-1 observations:

| Comparison | Result |
| --- | ---: |
| `scan-tree-counted` vs `tier-tree-no-care` | 26.27% less wall-clock time |
| `scan-tree-bounded7` vs `tier-tree-no-care` | 25.14% less wall-clock time |
| `scan-tree-counted` vs `scan-tree-bounded7` | 1.52% less wall-clock time |
| `scan-tree-counted` vs `scan-linear-counted` | 12.42% less wall-clock time |

The scan family therefore has a strong first-seed lead, and the binary-tree
spawn topology also remains beneficial inside the scan algorithm. This is only
a preview; no winner should be promoted until all three seeds finish.

##### Seed 2

| Mode | Time | Ticks | Final Power | Valid |
| --- | ---: | ---: | ---: | --- |
| `tier-tree-no-care` | 505.90 s | 3,024,491 | 100,459.09 | yes |
| `equal7-tree-no-care` | 654.84 s | 3,699,816 | 103,174.14 | yes |
| `dumb-tree-no-care` | 503.16 s | 3,034,224 | 100,004.88 | yes |
| `tier-linear-no-care` | 561.72 s | 3,362,057 | 100,409.31 | yes |
| `scan-tree-bounded7` | 376.60 s | 2,254,714 | 100,630.53 | yes |
| `scan-tree-counted` | **372.42 s** | **2,229,249** | 100,592.43 | yes |
| `scan-linear-counted` | 426.60 s | 2,555,771 | 100,268.47 | yes |

##### Two-seed scan preview

| Mode | Avg time | Min | Max |
| --- | ---: | ---: | ---: |
| `scan-tree-counted` | **372.29 s** | 372.15 s | 372.42 s |
| `scan-tree-bounded7` | 377.25 s | 376.60 s | 377.89 s |
| `scan-linear-counted` | 425.76 s | 424.92 s | 426.60 s |

Across the same first two seeds, `scan-tree-counted` is 26.33% faster than
`tier-tree-no-care`, 1.31% faster than `scan-tree-bounded7`, and 12.56%
faster than `scan-linear-counted`.

##### Seed 3 partial

| Mode | Time | Ticks | Final Power | Valid |
| --- | ---: | ---: | ---: | --- |
| `tier-tree-no-care` | 503.52 s | 3,010,220 | 100,482.18 | yes |
| `equal7-tree-no-care` | 671.29 s | 3,784,208 | 103,045.48 | yes |
| `dumb-tree-no-care` | 509.10 s | 3,071,864 | 100,005.46 | yes |
| `tier-linear-no-care` | 561.17 s | 3,357,896 | 100,284.81 | yes |

##### Complete control averages

| Mode | Avg time | Min | Max |
| --- | ---: | ---: | ---: |
| `tier-tree-no-care` | **504.73 s** | 503.52 s | 505.90 s |
| `dumb-tree-no-care` | 506.53 s | 503.16 s | 509.10 s |
| `tier-linear-no-care` | 561.35 s | 561.17 s | 561.72 s |
| `equal7-tree-no-care` | 663.30 s | 654.84 s | 671.29 s |

The non-scan controls are now complete for all three seeds. Their low spread
confirms that the ~372 s scan result is not being compared against an unstable
control. The final decision still waits for the three seed-3 scan results.

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Measured | The four non-scan controls are complete across all three seeds; `tier-tree-no-care` averages 504.73 s. | `sunflower-v2-bounded7` partial run |
| Measured | `scan-tree-counted` averages 372.29 s across seeds 1-2 with only 0.27 s min/max spread. | `sunflower-v2-bounded7` partial run |
| Measured | Binary-tree fan-out is faster than linear fan-out for the counted scan: 372.29 s vs 425.76 s across seeds 1-2. | `sunflower-v2-bounded7` partial run |
| Open question | Seed 3 scan results are still required before selecting the leaderboard implementation. | Current partial run |

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
