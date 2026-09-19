# Benchmark: Carrot leaderboard

## Scope

| Field | Value |
| --- | --- |
| Topic | Carrot resource leaderboard |
| Purpose | Compare dedicated finite Carrot hot paths and Water/Fertilizer policies without normal mixed-farm overhead. |
| Implementation | `bench_lb_carrot.py` |
| Runner | `bench_lb_car_run.py` |
| Primary metric | Elapsed time to Carrot target; ticks and resource use are secondary diagnostics. |
| Success condition | Candidate must reach the requested Carrot gain and report a valid run. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| `lbcar-v1` | `79a984cac3b376155d7b260bd23e445daeb31515` | Synthetic Hay/Wood support; seeds 1, 2, 3 | Pending measurement |

## Results

| Status | Detail |
| --- | --- |
| Pending | No canonical `lbcar-v1` timing result has been recorded yet. |

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Caveat | The real Carrot leaderboard start inventory has not been measured in this suite state. | Runner comments and synthetic setup. |
| Method | v1 intentionally oversupplies Hay and Wood to isolate crop hot-path behavior from starvation. | `simulation_items()` in the runner. |
| Open question | Re-run after the real Carrot leaderboard probe and bump the benchmark version if inputs change. | Provenance rule. |

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out `79a984cac3b376155d7b260bd23e445daeb31515` or the exact later source commit used for the run. |
| 2 | Run `bench_lb_car_run.py`. |
| 3 | Screen all modes at 50,000,000 Carrot gain. |
| 4 | Validate the three fastest modes across seeds 1, 2, 3 at the 2,000,000,000 Carrot target. |
| 5 | Record the exact source SHA and whether the setup is synthetic or measured. |

## Notes

### Setup

| Field | Value |
| --- | ---: |
| Requested speedup | 10000 |
| Screen gain | 50,000,000 Carrot |
| Final gain | 2,000,000,000 Carrot |
| Seeds | 1, 2, 3 |
| Synthetic starting Hay | 10,000,000,000 |
| Synthetic starting Wood | 10,000,000,000 |
| Starting Power | 1,000,000,000 |
| Starting Water | 0 |
| Starting Fertilizer | 0 |

### Modes

| Mode | Purpose |
| --- | --- |
| `carrot-lean` | Direct lean harvest/replant control |
| `carrot-water25` | Water threshold 0.25 |
| `carrot-water50` | Water threshold 0.50 |
| `carrot-water75` | Water threshold 0.75 |
| `carrot-fert` | Fertilizer ablation |
| `carrot-water-fert` | Combined Water + Fertilizer |
| `carrot-safe` | Defensive control with affordability checks |
