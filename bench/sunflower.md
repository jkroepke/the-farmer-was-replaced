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
| Status | Awaiting a complete measured run. |
