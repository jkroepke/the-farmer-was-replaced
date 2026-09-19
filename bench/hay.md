# Benchmark: Hay leaderboard

## Scope

| Field | Value |
| --- | --- |
| Topic | Hay resource leaderboard |
| Purpose | Compare dedicated finite Grass/Hay hot paths and Water/Fertilizer policies. |
| Implementation | `bench_lb_hay.py` |
| Runner | `bench_lb_hay_run.py` |
| Primary metric | Elapsed time to Hay target; ticks and resource use are secondary diagnostics. |
| Success condition | Candidate must reach the requested Hay gain and report a valid run. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| `lbhay-v1` | `6f738fc4dfdff7810409e0d3e2687406ef2afaad` | Provisional Wood-LB Power assumption; seeds 1, 2, 3 | Pending measurement |

## Results

| Status | Detail |
| --- | --- |
| Pending | No canonical `lbhay-v1` timing result has been recorded yet. |

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Caveat | The v1 runner uses the measured Wood Power reserve as a provisional Hay assumption. | Runner comments. |
| Open question | Confirm the real Hay leaderboard starting inventory with the dedicated probe before treating v1 as leaderboard-equivalent. | `lb_hay_probe.py`. |
| Open question | Compare Water thresholds and Fertilizer against the lean Grass control. | `lbhay-v1` pending. |

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out `6f738fc4dfdff7810409e0d3e2687406ef2afaad` or the exact later source commit used for the run. |
| 2 | Run `bench_lb_hay_run.py`. |
| 3 | Screen all modes at 50,000,000 Hay gain. |
| 4 | Validate the three fastest modes across seeds 1, 2, 3 at the 2,000,000,000 Hay target. |
| 5 | If the real Hay probe changes the setup, bump the benchmark version before measuring again. |

## Notes

### Setup

| Field | Value |
| --- | ---: |
| Requested speedup | 10000 |
| Screen gain | 50,000,000 Hay |
| Final gain | 2,000,000,000 Hay |
| Seeds | 1, 2, 3 |
| Provisional starting Power | 1,000,000,000 |
| Starting Water | 0 |
| Starting Fertilizer | 0 |

### Modes

| Mode | Purpose |
| --- | --- |
| `grass-lean` | Lean Grass harvest control |
| `grass-water25` | Water threshold 0.25 |
| `grass-water50` | Water threshold 0.50 |
| `grass-water75` | Water threshold 0.75 |
| `grass-fert` | Fertilizer ablation |
| `grass-water-fert` | Combined Water + Fertilizer |
| `grass-safe` | Defensive control |
