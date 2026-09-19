# Drone memory

## Historical reference

The pinned nql1314 reference at `688325db004607563e59535a15ce94fad092ff9f` contains explicit 2025 experiments around drone memory.

Most importantly, `archived/ref_test.py` and `docs/DRONE_SHARED_MEMORY_DISCOVERY.md` document a historical engine behavior where multiple drones called `wait_for()` on the same completed source drone and observed cumulative mutations of one returned mutable list.

That behavior enabled shared lists, dictionaries, counters, task queues, companion maps, dynamic worker priorities and stop flags.

## Current documented model

Current repository/game assumptions:

- each drone has its own memory
- globals are not shared
- arguments passed through `spawn_drone(task, *args)` are copied
- return values are used with `wait_for()` to move data back to the caller

A previous minimal current-runtime probe reproduced the historical source-list pattern and observed isolated worker results:

```text
worker 1 -> [1], source -> []
worker 2 -> [2], source -> []
worker 3 -> [3], source -> []
DRONE MEMORY RESULT isolated
```

This invalidates the historical shared mutable queue/list mechanism for the tested current runtime.

## Expanded probe suite

`drone_mem_probe.py` now tests the semantics independently:

- global mutation isolation
- mutable list arguments passed to spawned drones
- nested mutable argument copying
- closure-captured list isolation
- normal worker return-value communication
- repeated `wait_for(source)` calls in the parent
- repeated `wait_for(source)` calls inside one worker
- parent mutation -> worker visibility
- worker mutation -> parent visibility
- worker mutation -> later worker visibility
- nested source-return isolation
- the historical producer/consumer queue pattern

The cross-worker tests are intentionally sequential. That removes scheduler races and makes any cumulative mutable state evidence much stronger.

The parent/worker repeated-wait tests accept and report either `copy-per-wait` or `same-drone-alias` for calls made by the same drone. The critical invariant is cross-drone isolation.

## Status

The expanded suite was added on 2026-09-19 but has not yet been executed in the game after this expansion.

Run `drone_mem_run.py` and persist the complete output here once measured. If current game behavior changes in a future update, keep the old result with its date/build context rather than overwriting the history.
