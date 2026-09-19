# Benchmark: <item>

## Scope

| Field | Value |
| --- | --- |
| Item / topic | `<item>` |
| Runner | `<bench_runner.py>` |
| Implementation | `<implementation.py>` |
| Purpose | <what this benchmark decides> |
| Success condition | <exact condition> |

## Run: <date or descriptive label>

### Provenance

| Field | Value |
| --- | --- |
| Source commit | `<full 40-character Git SHA>` |
| Benchmark/version | `<version label printed by runner>` |
| World/profile | <for example 32x32> |
| Drones | <count or max_drones()> |
| Simulation speedup | <value> |
| Seeds | <seed list> |
| Cycles / target | <value> |
| Validity | PASS / FAIL and reason |

Do not record canonical numeric results until the source commit above exists and pins both runner and implementation.

### Results

| Mode | Seed(s) | Result / gain | Ticks | Elapsed | Throughput | Valid |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `example` | 1,2,3 | 0 | 0 | 0.00 | 0.00 | PASS |

### Interpretation

| Kind | Statement | Evidence |
| --- | --- | --- |
| Measured | <directly measured fact> | <result row(s)> |
| Conclusion | <decision supported by the measurements> | <why the evidence supports it> |
| Open question | <what still needs testing> | <missing comparison or uncertainty> |

### Reproduction

| Step | Action |
| ---: | --- |
| 1 | Check out the exact source commit above. |
| 2 | Run `<bench_runner.py>`. |
| 3 | Preserve the runner's complete output when adding or changing the result table. |

-----

## Run: <next source commit or materially different setup>

Repeat the same Provenance, Results, Interpretation, and Reproduction tables.
