# Benchmark: <item>

## Scope

| Field | Value |
| --- | --- |
| Topic | `<item>` |
| Purpose | <what this benchmark decides> |
| Implementation | `<bench_item.py>` |
| Runner | `<bench_item_run.py>` |
| Primary metric | <for example elapsed time, ticks, throughput> |
| Success condition | <exact validity / target condition> |

## Benchmark index

| Run / version | Source commit | Profile | Status |
| --- | --- | --- | --- |
| `<suite-v1>` | `<full 40-character Git SHA>` | <world / drones / target> | Measured |
| `<suite-v2>` | `<full 40-character Git SHA>` | <changed setup> | Pending |

Use the exact source commit that pins both runner and implementation. If an old result has no recorded source commit, write **Unknown / not recorded** and treat it as historical/non-canonical instead of guessing.

## Results

### <run label>

#### Provenance

| Field | Value |
| --- | --- |
| Source commit | `<full 40-character Git SHA>` |
| Benchmark/version | `<suite-v1>` |
| World/profile | <for example 32x32> |
| Drones | <count or `max_drones()`> |
| Requested speedup | <value> |
| Seeds | <seed list> |
| Target / cycles | <value> |
| Validity | PASS / FAIL and exact condition |

#### Measurements

Put elapsed times, ticks, throughput, gains, min/max, and comparisons in Markdown tables.

| Mode | Seed(s) | Gain / result | Ticks | Time (s) | Throughput | Valid |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `example` | 1, 2, 3 | 0 | 0 | 0.00 | 0.00 | PASS |

Do not use prose lists or code blocks for measured timings.

-----

### <next run label>

Repeat the provenance and measurements structure whenever the source commit or material setup changes.

## Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Measured | <direct observation> | <result table / run label> |
| Conclusion | <decision supported by measurements> | <why> |
| Rejected | <approach not selected> | <measured reason> |
| Open question | <remaining uncertainty> | <next comparison needed> |

Interpretation must not be mixed into the measurement tables.

## Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out the exact source commit for the run. |
| 2 | Run `<bench_item_run.py>`. |
| 3 | Preserve the complete runner output. |
| 4 | Update this file without changing the historical source SHA or measured values. |

## Notes

| Kind | Detail |
| --- | --- |
| Method | <important benchmark method / invariant> |
| Reference | <source-near implementation or external reference> |
| Caveat | <known limitation> |
| Pending | <planned benchmark work> |
