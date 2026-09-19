# Benchmark: Fastest Reset

## Scope

| Field | Value |
| --- | --- |
| Topic | Fastest Reset planner |
| Purpose | Compare planner policies from empty progression state until `Unlocks.Leaderboard` is unlocked. |
| Implementation | `bench_reset.py` |
| Runner | `bench_reset_run.py` |
| Primary metric | End-to-end elapsed simulation time to unlock `Unlocks.Leaderboard`. |
| Success condition | Run must unlock `Unlocks.Leaderboard` within the action watchdog. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| `reset-v2` | `7e58b52cb9d990121b0741a84330a6e0e53263b1` | Empty-state progression; seeds 1, 2, 3 | Invalid harness: first simulation returned `None`, runner crashed on aggregation |
| `reset-v3` | `8190fcd5ecb55b9f2286cf98d92fffb1c815603b` | Empty-state progression; seeds 1, 2, 3; diagnostic checkpoints | Pending measurement |

## Results

| Status | Detail |
| --- | --- |
| Invalid | `reset-v2` returned `None` for the first simulation and then raised on `totals[mode] += elapsed`; no timing result exists. |
| Pending | `reset-v3` removes the redundant initial `clear()`, reports worker checkpoints, and treats `simulate() == None` as a per-case failure instead of crashing the suite. |

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Comparison | The suite compares dynamic frontier, Agude-inspired sticky bounded targeting, and msmith93-style static bounded order. | Current mode matrix. |
| Open question | Determine which planner reaches `Unlocks.Leaderboard` fastest with the same production backend. | `reset-v3` pending. |
| Validity | A fast run is invalid if it exceeds the watchdog or fails to unlock the leaderboard. | Runner contract. |

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out `8190fcd5ecb55b9f2286cf98d92fffb1c815603b`. |
| 2 | Run `bench_reset_run.py`. |
| 3 | Keep requested speedup at 10000 for all compared modes. |
| 4 | Run seeds 1, 2, 3 with the same 10,000-action watchdog. |
| 5 | Record complete output, validity, and exact source SHA. |

## Notes

### Setup

| Field | Value |
| --- | ---: |
| Benchmark/version | `reset-v3` |
| Requested speedup | 10000 |
| Action watchdog | 10,000 |
| Seeds | 1, 2, 3 |

### Modes

| Mode | Purpose |
| --- | --- |
| `current-dynamic-frontier` | Current dynamic frontier planner |
| `agude-sticky-bounded` | Sticky bounded-target planner inspired by Agude |
| `msmith-static-bounded` | Pinned static unlock order with bounded/live production |
