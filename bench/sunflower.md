# Sunflower benchmarks

This file is the canonical home for measured Sunflower leaderboard benchmark results.

## Run: interrupted sunflower-v1

### Provenance

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

## Interrupted sunflower-v1 result and root cause

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

## Next run: sunflower-v2-bounded7

| Field | Value |
| --- | --- |
| Fix commit | `f962b8615880d92b573beaa3c30389b817e32dc0` |
| Version bump commit | `689c8e20a44f6d24a46521ba1130360c5b5acbc5` |
| Benchmark/version | `sunflower-v2-bounded7` |
| Status | Partial preview available; full three-seed run still in progress. |


### Preview results

Status: **partial**. Seed 1 completed all seven modes. Seed 2 is currently
complete through `tier-linear-no-care`; the run is still executing
`scan-tree-bounded7`.

#### Seed 1

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

#### Seed 2 partial

| Mode | Time | Ticks | Final Power | Valid |
| --- | ---: | ---: | ---: | --- |
| `tier-tree-no-care` | 505.90 s | 3,024,491 | 100,459.09 | yes |
| `equal7-tree-no-care` | 654.84 s | 3,699,816 | 103,174.14 | yes |
| `dumb-tree-no-care` | 503.16 s | 3,034,224 | 100,004.88 | yes |
| `tier-linear-no-care` | 561.72 s | 3,362,057 | 100,409.31 | yes |

The non-scan controls are very stable between seeds 1 and 2, which makes the
large seed-1 scan improvement especially worth validating across the remaining
results.

