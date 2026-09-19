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

## Spawn locality hypothesis 2026-09-19

Current `builtins.py` documents a critical property of `spawn_drone()`:

> the new drone starts at the same position as the drone that called `spawn_drone()`

This creates a second optimization axis beyond spawn count:

- **spawn topology**: who spawns whom and how much spawning can overlap
- **spawn locality**: where the parent is standing when each child is created

For a uniformly distributed set of 32 column targets on a wrapping 32-wide ring, moving one fixed launcher from x=0 to x=16 does not reduce the aggregate shortest-path distance. Translation symmetry gives every fixed launch column the same distance multiset.

The potentially useful optimization is therefore not "spawn everything from the center", but **move parents before spawning spatially local children**.

Two benchmarkable forms:

1. sequential placed launch
   - parent walks to each worker's target column
   - spawns the worker directly on its owned column
   - removes child positioning but serializes parent movement

2. spatial spawn tree
   - parent moves to the midpoint of its assigned region
   - spawns children from there
   - children repeat recursively for their subregions
   - combines parallel spawning with progressively better locality

For spatial workloads such as Pumpkin columns or independent Maze blocks, the second topology is the stronger general hypothesis.

Do not assume locality wins automatically: a parent move costs a physical action too, and sequential placement may lengthen the critical launch path. Measure cold start and amortized repeated-work throughput separately.

## Benchmark record

The probe matrix and measured current-runtime result are maintained in `bench/runtime.md`. This memory file keeps only the durable semantics derived from that run.
