# Benchmark: Cactus

## Scope

| Field | Value |
| --- | --- |
| Topic | Cactus |
| Purpose | Compare Cactus sorting, rerolling, persistent waves, spawn topology, and exact leaderboard workloads. |
| Implementation | `bench_cactus.py` |
| Runner | `bench_cactus_run.py` |
| Primary metric | Elapsed time, ticks, exact Cactus gain, and repeated-cycle throughput. |
| Success condition | All requested cycles must complete with the exact expected Cactus gain. |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| Initial generalized matrix | Unknown / not recorded | 32x32 / 32 drones / 3 cycles | Measured historical |
| Source-near references | `567e0ab6f96305cd6c9a05fd5eea2917449c2407` | External reference provenance | Reference only |
| `cactus-v3` | `05ee0dbd2ff6483dec93c1707a0e957b25185c5f` | 32x32 / 32 drones / cold + 3 cycles | Measured |
| `cactus-v4` | Unknown / not recorded | Exact leaderboard-profile comparison | Pending |

## Results

### Benchmark results 2026-09-19

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | 1..3 |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

Measured by the user in-game on 32x32, 32 drones, three cycles, seeds 1..3:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `current-production` | 238.25 | — | average for 3 cycles |
| `two-wave-bubble-reset` | 221.38 | — | — |
| `two-wave-insertion-reset` | 168.89 | — | — |
| `two-wave-insertion-reuse` | 163.42 | — | — |
| `two-wave-insertion-reroll-reuse` | 136.91 | — | — |
- every finalist completed all requested cycles and produced the full expected gain

The measured improvement from current production to
`two-wave-insertion-reroll-reuse` is about 42.5%.

The source-near one-cycle references measured:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `tstambaugh-reference-32` | 37.97 | — | — |
| `nql1314-reference` | 89.22 | — | — |

The Tstambaugh reference is therefore still materially faster than the
generalized reroll candidate. Comparing one source-reference cycle with the
three-cycle average of the generalized winner gives roughly 37.97 s versus
45.64 s per cycle.

Measured generalization behavior:

| Profile | Comparison | First time (s) | Second time (s) |
| --- | --- | ---: | ---: |
| 6x6 | rerolling was much slower | 8.70 | 3.75 |
| 16x16 | rerolling was slower | 20.50 | 17.19 |
| 32x32 with 8 drones | rerolling was faster | 168.30 | 192.38 |

Therefore rerolling is currently only treated as a measured optimization for
world size 32. It must not be assumed beneficial for smaller worlds.


-----

### Follow-up benchmark run: placed-worker bug found

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The next in-game run compared the prior winner, the source-near Tstambaugh
control, and the two placed-worker candidates over three seeds / three cycles.

Valid full-gain results:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `two-wave-insertion-reroll-reuse` | 136.85 | — | average for 3 cycles |
| `tstambaugh-reference-32` | 124.86 | — | average for 3 cycles |

Both produced the full expected 100,663,296 Cactus over three 32x32 cycles.

Therefore the source-near Tstambaugh 32x32 path remained about 8.8% faster
than the best previously generalized candidate in this longer comparison.

The two new placed-worker candidates were invalid:

- `tstambaugh-placed-generalized`: repeated farm-edge `swap(East)` warnings
  and only partial gain
- `adaptive-placed-pool`: the same edge warnings and partial gain despite
  reporting `completed 3`

Root cause:

`_insertion_row()` initialized its local movement tracker with
`current_x = 0`. That assumption was true for the earlier scan path because
a complete row scan wraps back to x=0, but it is false after the batched
`redo` loop, which leaves the worker on the last rerolled x coordinate.
The movement helper then tracked a different x coordinate than the physical
drone position and could issue `swap(East)` from x=world_size-1.

Fix:

- initialize the row insertion movement tracker from `get_pos_x()`
- initialize the column insertion tracker from `get_pos_y()` for the same
  robustness principle

#### Benchmark validity hardening

The run also exposed that `completed` was too weak: `harvest()` can return
success after harvesting only part of the field.

The benchmark now validates every cycle against the measured fully-upgraded
full-chain yield:

`(world_size * world_size) ** 2 * 32`

For 32x32 this is 33,554,432 Cactus per cycle, matching the current Cactus
leaderboard target and prior full-chain benchmark results.

A cycle increments `completed` only when its exact gain matches that value.
The result line now also prints `expected` and `valid`.

#### Mateus persistent experiment fix

The first `persistent-mateus` smoke run aborted during its first vertical
pass because a not-yet-planted neighboring tile returned `None` from
`measure(North)`.

The upstream Mateus implementation has a `safe_measure()` helper that maps
`None` to `-1`. The local benchmark adaptation had accidentally omitted
that behavior. The candidate now restores that source behavior for current
and directional measurements.

The benchmark run stopped at the Mateus error, so the 6x6, 16x16, and
32x32/8-drone smoke sections did not execute. Re-run the suite after the
fixes before making a production decision.


-----

### Final measured decision 2026-09-19

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | 1..3 |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The repaired follow-up benchmark produced valid full-chain results for all
32x32 finalists across seeds 1..3:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `two-wave-insertion-reroll-reuse` | 138.91 | — | average / 3 cycles |
| `tstambaugh-reference-32` | 125.85 | — | — |
| `tstambaugh-placed-generalized` | 123.73 | — | — |
| `adaptive-placed-pool` | 119.69 | — | — |

Every finalist produced the exact expected 100,663,296 Cactus and reported
`valid True`.

Therefore `adaptive-placed-pool` is the measured 32x32 / 32-drone winner:

- about 13.8% faster than the previous generalized reroll candidate
- about 4.9% faster than the source-near Tstambaugh reference

Smaller-world smoke tests were also valid and favored the adaptive placed
architecture:

- 6x6: adaptive 3.50 s vs insertion-reset 3.75 s
- 16x16: adaptive 16.05 s vs insertion-reset 17.19 s

The Mateus persistent single-wave experiment completed with full gain but is
rejected for production:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `32x32 / 32 drones` | 66.05 | — | for one cycle |
- materially slower than the placed candidates
- emits repeated warnings from attempted swaps against non-swappable Cacti

The final benchmark log ended after starting the 32x32 / 8-drone smoke and
therefore did not provide a fresh result for the repaired adaptive placed
candidate at lower drone count.

#### Production architecture promoted

`cactus.py` now uses a measured hybrid:

- when `max_drones() >= world_size`, use the benchmark-winning placed worker
  architecture
- when fewer drones are available than field lines, use the previously
  validated generalized two-wave insertion fallback
- use quadrant rerolling only at world size 32
- use ordinary insertion sorting without rerolling on smaller measured worlds

The fewer-drone fallback is intentional: a previous benchmark already proved
the generalized 32x32 / 8-drone reroll path valid and faster than its
non-reroll control, while the latest adaptive lower-drone smoke did not finish
in the supplied log.

#### Consecutive Cactus production

The benchmark winner's best result reused the post-harvest field after the
first cycle. Production previously discarded that benefit because
`production.run_cactus()` immediately called `restore_normal_farm()` after
every successful Cactus run.

Production now tracks `_cactus_active` similarly to the existing Pumpkin and
Gold state:

- first Cactus-focused run clears/prepares the field
- consecutive Cactus-focused runs reuse the post-harvest Soil field
- switching to another production focus restores the normal farm exactly once
- expansion/reset clears the Cactus-active state

This lets the measured consecutive-cycle reuse optimization affect the real
main loop rather than only the benchmark.


-----

### Completed 32x32 / 8-drone smoke

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | **Unknown / not recorded** |
| Benchmark/version | Not versioned in this record |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Historical/non-canonical until rerun from a committed state |

#### Measurements and observations

The full follow-up log includes the previously missing lower-drone result.

Measured one-cycle 32x32 / 8-drone results:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `two-wave-insertion-reroll-reuse` | 164.77 | — | valid full gain |
| `tstambaugh-placed-generalized` | 129.84 | — | valid full gain |
| `adaptive-placed-pool` | 133.20 | — | valid full gain |

This proves that the placed/batched worker architecture also works when each
worker owns multiple rows/columns via `index += worker_count`.

The previous production safeguard that switched back to the older generalized
two-wave fallback when `max_drones() < world_size` is therefore no longer
needed. Production now uses the placed/batched architecture for all drone
counts. The row/column assignment already scales to fewer workers.

At 8 drones the placed source-near variant is about 21.2% faster than the old
reroll two-wave fallback. The adaptive placed result is about 19.2% faster.

The remaining `_run_fallback()` code is currently retained only as historical
implementation context; it is no longer selected by the production entrypoint.


-----

### cactus-v3 measured result and production promotion 2026-09-19

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `05ee0dbd2ff6483dec93c1707a0e957b25185c5f` |
| Benchmark/version | `cactus-v3` |
| Requested speedup | Not recorded |
| Seeds | See recorded setup |
| Canonical status | Source state recorded |

#### Measurements and observations

Benchmark commit: `05ee0dbd2ff6483dec93c1707a0e957b25185c5f`.

The user ran the full `cactus-v3` suite in-game.

#### Exact cold leaderboard workload

All candidates completed one 32x32 cycle with the exact expected gain of
33,554,432 Cactus on all three seeds.

Measured averages:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `current-production` | 42.04 | — | — |
| `tstambaugh-reference-32` | 39.49 | — | — |
| `tstambaugh-placed-generalized` | 40.70 | — | — |
| `adaptive-placed-pool` | 40.64 | — | — |
| `adaptive-binary-spawn` | 40.62 | — | — |
| `adaptive-flekay-powers` | 38.93 | — | — |
| `current-production-fresh` | 42.37 | — | — |

Therefore `adaptive-flekay-powers` is the measured cold-target winner:

- about 7.4% faster than current production
- about 4.2% faster than `adaptive-placed-pool`
- about 1.4% faster than the source-near Tstambaugh reference

Skipping the extra `clear()` did not improve the measured result and is not
promoted.

#### Three-cycle production workload

All finalists completed all three cycles with the exact expected total gain of
100,663,296 Cactus on every seed.

Measured averages:

| Mode / profile | Time (s) | Ticks | Notes |
| --- | ---: | ---: | --- |
| `adaptive-placed-pool` | 123.18 | — | — |
| `adaptive-binary-spawn` | 118.91 | — | — |
| `adaptive-flekay-powers` | 114.93 | — | — |

The powers-of-two topology is about 6.7% faster than the previous production
architecture on this measured workload.

#### Production decision

Promote the powers-of-two distributed spawn topology only for the exact
measured production case:

- world size 32
- at least 32 available drones

Keep the existing placed/batched architecture for:

- smaller worlds
- 32x32 with fewer than 32 drones

This preserves the already measured 6x6, 16x16, and 32x32/8-drone behavior
instead of extrapolating the new spawn topology beyond its benchmark evidence.

The dedicated `lb_cactus.py` automatically uses the new production path on
the full 32x32 leaderboard setup because it calls `cactus.run()`.


-----

## Interpretation

### Production decision

Do not replace `cactus.py` from source inspection alone.

Run `bench_cactus_run.py` in-game and compare:

- simulation runtime
- `CACTUS RESULT ... completed`
- `gain`
- ticks

A mode that is faster but does not complete all requested cycles or produces materially less Cactus is invalid.

After a winner is measured, promote only the winning generalized architecture to `cactus.py`. Keep 32x32 specialization only when the benchmark proves it useful.

### cactus-v3 leaderboard-profile correction 2026-09-19

Benchmark source commit:

`05ee0dbd2ff6483dec93c1707a0e957b25185c5f`

The v3 `CACTUS TARGET COLD` matrix was a valid one-cycle algorithm
comparison, but its simulation profile supplied 1,000,000,000 Water. The real
Cactus leaderboard run later emitted repeated `use_item(Items.Water)`
warnings, so v3 must not be described as an exact leaderboard-resource model.

The user confirmed that the leaderboard supplies the Cactus planting input
(Pumpkin) in effectively unlimited quantity. The dedicated leaderboard path
can therefore remove Main-Run affordability and optional-Water logic.

The v3 three-cycle Main-Run comparison remains valid for its documented
oversized-resource setup. Only the exact-LB interpretation is corrected.

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out the source commit listed for the result group. |
| 2 | Run the matching benchmark runner from Scope. |
| 3 | Preserve complete output and update this file without changing historical values. |

## Notes

### Benchmark suite

Files:

- `bench_cactus.py`
- `bench_cactus_run.py`

Modes:

0. `current-production`
1. `two-wave-bubble-reset`
2. `two-wave-insertion-reset`
3. `two-wave-insertion-reuse`
4. `two-wave-insertion-reroll-reuse`
5. `tstambaugh-reference-32`
6. `nql1314-reference`

The candidate matrix runs modes 0..4 on seeds 1, 2, and 3 at 32x32 for three complete Cactus cycles.

The two source-near references run as one-seed smoke tests until they prove competitive.

Generalization smoke tests also run the insertion candidates on 6x6 and 16x16 worlds plus a 32x32 run with Megafarm level 3, so workers must process multiple lines via `index += worker_count`.

Important comparison axes:

- fused row lifecycle vs separate planting/readiness/sort waves
- bubble vs cached insertion sorting
- resetting every cycle vs reusing post-harvest field state
- reroll cost vs reduced inversion/swap cost
- source-near 32x32 leaderboard implementation vs generalized candidate

### Follow-up finding: worker placement and batched rerolls

The source-near Tstambaugh worker does two things that the first generalized
candidate did not preserve closely enough:

1. it spawns each row/column drone while the caller is already standing on
   that worker's first row/column, so the child does not first travel from
   (0,0) to its assignment
2. it collects all bad Cactus positions into a local `redo` list and revisits
   them as a batch, allowing other plants to grow while the worker services a
   different rejected tile

The first generalized reroll implementation instead waited on rejected plants
inline and also watered every initially scanned tile. Those differences are
now isolated in new benchmark modes.

New modes:

- `tstambaugh-placed-generalized`
  - generalized placed-worker dispatch
  - batched local reroll queue
  - Tstambaugh 32x32 reroll heuristic
  - reset every cycle
- `adaptive-placed-pool`
  - same placed two-wave worker architecture
  - reroll only when `world_size == 32`, because that is the measured case
  - explicit readiness waiting on smaller worlds
  - field reset only on the first benchmark cycle so consecutive-cycle reuse
    can be measured separately

The follow-up benchmark compares modes 4, 5, 7 and 8 on the full 32x32
three-seed matrix. Smaller-world smoke tests compare the prior no-reroll
insertion control with the adaptive mode. The 32x32 / 8-drone smoke compares
the old reroll candidate with both new placed-worker candidates.

Do not promote a new production implementation until these follow-up results
are measured in-game.

### 2026-09-19 persistent-worker follow-up

The later placed-worker work superseded the separate positioned mode idea.

Current placed modes already cover spawn locality:

- `tstambaugh-placed-generalized`
- `adaptive-placed-pool`

They move the caller between `spawn_drone()` calls so children start on
their first owned row/column. This preserves the safe row barrier -> column
barrier architecture and is the preferred way to test placement optimization.

#### Mateus-style persistent single wave

New benchmark mode:

- `persistent-mateus`

This is a generalized finite experiment based on:

- `external/mateusmarochi-the-farmer-was-replaced-codes/source/cactus_farm.py`

One worker lifetime spans:

1. planting/repairing its columns
2. repeated vertical relaxation
3. repeated horizontal relaxation
4. readiness waiting for its rows

The caller participates as worker 0, so no scheduler slot is reserved.

The finite adaptation uses `world_size // 2` bidirectional passes. At 32x32
this matches the reference's 16 vertical and 16 horizontal sweep passes.

Important caveat:

There is no global barrier between the vertical and horizontal parts inside
the worker wave. A faster worker can therefore start horizontal swaps while
another worker is still doing vertical swaps. This is intentionally retained
as the central persistent-worker experiment and is not assumed race-safe.

The final harvest only happens after every worker in the wave has returned,
so the mode is finite and cannot leave permanent benchmark workers behind.

#### Benchmark policy

`persistent-mateus` is mode 9 and runs only in the one-seed, one-cycle
reference smoke section initially.

Promote it to the full finalist matrix only when the in-game result shows:

- `completed 1`
- full expected Cactus gain
- runtime competitive with the placed two-wave finalists

Do not promote this architecture into production from source inspection
alone. Its value is testing whether removing one complete worker wave is
worth the row/column overlap risk.

### Cactus leaderboard / Flekay follow-up 2026-09-19

Verified current leaderboard condition:

```python
num_items(Items.Cactus) >= 33554432
```

The current 32x32 fully upgraded benchmark already validates exactly
33,554,432 Cactus for one full-chain harvest. Therefore the multi-drone
Cactus leaderboard is fundamentally a **single cold full-field cycle**:
setup, planting, sorting, readiness, one chain harvest, then program exit.
Three-cycle reuse remains relevant for normal production throughput, but it
must not decide the leaderboard winner.

#### Flekay Cactus findings

Pinned upstream Flekay revision remains:

`567e0ab6f96305cd6c9a05fd5eea2917449c2407`

Its published 10x10 single-drone table reports gradient bubble sort slightly
ahead of plain insertion sort. The reusable idea is local repair after an
inversion rather than repeated blind full-field bubble passes.

This does **not** currently justify replacing the local parallel sorter:

- the Flekay table is 10x10 and single-drone
- the local 32x32 winner already caches values and uses insertion-style local
  repair independently in rows, then independently in columns
- Flekay's `plant_and_sort.py` also performs North/South repairs during
  planting, which would cross row ownership and create races if copied into
  the current multi-drone row phase

A future safe derivative could test row-only incremental repair while
planting, but it should be isolated as a benchmark before production use.

#### Spawn-topology candidates

The current production `_placed_wave()` serially calls `spawn_drone()`
from one controller. Recent spawn research makes distributed fan-out worth
testing directly in the Cactus workload.

`bench_cactus.py` now adds:

- `adaptive-binary-spawn`
  - balanced binary recursive fan-out
  - same batched reroll and row/column work as the adaptive candidate
- `adaptive-flekay-powers`
  - generic powers-of-two fan-out reproducing the Flekay/Jarvan topology
  - same Cactus work; only worker creation topology changes
- `current-production-fresh`
  - calls production Cactus with `reuse_field=True` in a simulation that
    was already cleared by `set_world_size()`
  - isolates the cost of the otherwise redundant extra `clear()`

Runner version is now `cactus-v3`.

Benchmark commit: `05ee0dbd2ff6483dec93c1707a0e957b25185c5f`.

The new `CACTUS TARGET COLD` matrix runs one 32x32 cycle from
`Items.Cactus: 0` on seeds 1, 2, and 3. Other resources remain oversized so
this matrix measures Cactus execution rather than resource starvation. This
is an exact target/gain workload, but it is **not claimed to reproduce every
hidden starting inventory value of `leaderboard_run()`**.

Do not promote binary/powers fan-out or skip-clear behavior into normal
production until `cactus-v3` is measured in-game. Normal main production can
enter Cactus from a non-empty farm, so the fresh-field skip-clear candidate is
leaderboard-specific unless a clean-field precondition is proven.

#### Dedicated leaderboard entrypoint

Added:

- `lb_cactus.py` — finite one-run Cactus program using the current production
  algorithm
- `lb_cactus_run.py` — starts `Leaderboards.Cactus` at speedup 256

The dedicated program terminates after the one Cactus run instead of entering
the normal endless planner loop.

-----

### cactus-v4 pending exact-LB comparison

The v4 default runner intentionally avoids the known noisy/rejected reference
smokes and runs only:

| Matrix | World | Drones | Cycles | Simulation items |
| --- | ---: | ---: | ---: | --- |
| `CACTUS LB EXACT` | 32 | 32 | 1 | Pumpkin=1e9, Power=1e9 |
| `CACTUS MAIN FINALISTS` | 32 | 32 | 3 | prior oversized Main profile |

`CACTUS LB EXACT` candidates:

| Mode | Purpose |
| --- | --- |
| `current-production` | generic Main-Run control |
| `adaptive-flekay-powers` | generic powers-of-two control |
| `lb-powers-specialized` | fixed LB-only implementation without Water/resource/repair checks |

The specialized LB implementation must still produce exactly 33,554,432
Cactus for every seed before it is considered valid.
