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

## Verified current-runtime result

Executed in-game on 2026-09-19 via `drone_mem_run.py`.

Simulation runtime reported: `1.5` seconds.

Complete result:

```text
DRONE_MEMORY RUN START
DRONE_MEMORY SUITE START
DRONE_MEMORY global PASS worker-mutates-parent-stays-zero
DRONE_MEMORY spawn-arg-list PASS copied
DRONE_MEMORY spawn-arg-nested PASS deep-copied
DRONE_MEMORY closure-list PASS isolated
DRONE_MEMORY return-value PASS worker-to-caller
DRONE_MEMORY source-parent-repeat PASS copy-per-wait
DRONE_MEMORY source-worker-repeat PASS copy-per-wait
DRONE_MEMORY source-parent-worker PASS parent-mutation-not-visible
DRONE_MEMORY source-worker-parent PASS worker-mutation-not-visible
DRONE_MEMORY source-worker-worker PASS historical-exploit-isolated
DRONE_MEMORY source-nested PASS deep-isolation
DRONE_MEMORY source-queue PASS historical-producer-consumer-isolated
DRONE_MEMORY SUMMARY 12 12
DRONE_MEMORY RESULT PASS
DRONE_MEMORY RUN DONE 1.5
```

## Confirmed semantics

The 12/12 result establishes the following for the tested current runtime:

- spawned drones do not mutate the parent's globals
- mutable arguments passed through `spawn_drone(task, *args)` are copied
- nested mutable argument structures are isolated as well
- closure-captured mutable state is isolated between parent and worker
- normal return-value communication through `wait_for(worker)` works
- each `wait_for(source)` call receives a fresh copy of the completed source drone's returned mutable object, even when the same drone calls `wait_for(source)` repeatedly
- parent mutations to one `wait_for(source)` result are not visible to workers
- worker mutations to one `wait_for(source)` result are not visible to the parent
- worker mutations are not visible to later workers
- nested lists/dicts returned by the source are isolated across callers
- the historical shared producer/consumer queue no longer works as shared state; each worker receives its own queue copy

The strongest new finding is `copy-per-wait`: isolation is not merely a consequence of crossing a drone boundary once. Repeated waits on the same completed source handle return independent mutable values.

For the tested list/dict/nested structures, the current operational model is therefore:

```text
spawn arguments -> copied into worker memory
worker globals/closures -> isolated from caller
wait_for(worker) -> returns data to caller
wait_for(completed_source) -> fresh copy per call, not a shared mutable reference
```

This directly disproves the historical nql1314 shared-`wait_for()` queue/list mechanism on the tested current runtime.

Keep the probe suite as a regression test after future game updates. The result proves the tested mutable list/dict semantics; do not generalize it to every possible engine-internal value type without a dedicated probe.
