# Benchmark: Wood leaderboard

## Scope

| Field | Value |
| --- | --- |
| Topic | Wood resource leaderboard |
| Purpose | Compare dedicated finite Wood layouts and Water/Fertilizer policies without Main-Run Sunflower overhead. |
| Implementation | `bench_lb_wood.py` |
| Runner | `bench_lb_wood_run.py` |
| Primary metric | Elapsed time to Wood target; ticks and remaining resources are secondary diagnostics. |
| Success condition | Candidate must reach the requested Wood gain and report a valid run. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| `lbwood-v1` | `3410ac30c7c2f75cbaa16053b94e405c972e1bba` | Measured Wood-LB start state; seeds 1, 2, 3 | Pending measurement |

## Results

| Status | Detail |
| --- | --- |
| Pending | No canonical `lbwood-v1` timing result has been recorded yet. |

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Measured setup | The real Wood leaderboard starts with 1,000,000,000 Power and zero Water/Fertilizer inventory. | Recorded Wood leaderboard probe used by the runner. |
| Hypothesis | Dedicated Sunflower production should not be needed for this finite leaderboard workload. | Large measured starting Power reserve. |
| Open question | Determine whether checkerboard, full-Tree, Water, or Fertilizer variants win end-to-end. | `lbwood-v1` pending. |

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out `3410ac30c7c2f75cbaa16053b94e405c972e1bba` or the exact later source commit used for the run. |
| 2 | Run `bench_lb_wood_run.py`. |
| 3 | Screen all modes at 100,000,000 Wood gain. |
| 4 | Validate the three fastest modes across seeds 1, 2, 3 at the 10,000,000,000 Wood target. |
| 5 | Record complete output and exact source SHA before promoting a winner. |

## Notes

### Setup

| Field | Value |
| --- | ---: |
| Requested speedup | 10000 |
| Screen gain | 100,000,000 Wood |
| Final gain | 10,000,000,000 Wood |
| Seeds | 1, 2, 3 |
| Starting Power | 1,000,000,000 |
| Starting Water | 0 |
| Starting Fertilizer | 0 |

### Modes

| Mode | Purpose |
| --- | --- |
| `checker-grass-lean` | Tree/Grass checkerboard, lean hot path |
| `checker-bush-lean` | Tree/Bush checkerboard, lean hot path |
| `checker-grass-water75` | Checkerboard with 0.75 Water threshold |
| `checker-bush-water75` | Bush checkerboard with 0.75 Water threshold |
| `checker-grass-fert` | Checkerboard Fertilizer ablation |
| `checker-grass-water-fert` | Combined Water + Fertilizer ablation |
| `full-tree-lean` | Full-Tree control |
| `full-tree-water75` | Full-Tree + Water control |
| `checker-grass-safe` | Defensive control including safety/affordability checks |
