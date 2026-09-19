import main


BENCH_VERSION = "reset-v3"

BENCH_SPEEDUP = 10000
BENCH_MAX_ACTIONS = 10000

BENCH_SEEDS = [
    1,
    2,
    3
]

MODE_NAMES = [
    "current-dynamic-frontier",
    "agude-sticky-bounded",
    "msmith-static-bounded"
]


def run_one(
    mode,
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_MAX_ACTIONS": BENCH_MAX_ACTIONS
    }

    quick_print(
        "RESET CASE START",
        MODE_NAMES[mode],
        "seed",
        seed
    )

    # Empty unlock/item maps model Fastest Reset from the initial farm.
    elapsed = simulate(
        "bench_reset",
        {},
        {},
        globals,
        seed,
        BENCH_SPEEDUP
    )

    if elapsed == None:
        quick_print(
            "RESET CASE FAIL",
            MODE_NAMES[mode],
            "seed",
            seed,
            "reason",
            "simulate-returned-none"
        )

        return -1

    quick_print(
        "RESET CASE DONE",
        MODE_NAMES[mode],
        "seed",
        seed,
        "elapsed",
        elapsed
    )

    return elapsed


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    totals = [
        0,
        0,
        0
    ]
    minimums = [
        -1,
        -1,
        -1
    ]
    maximums = [
        0,
        0,
        0
    ]
    successes = [
        0,
        0,
        0
    ]

    quick_print(
        "RESET BENCH SUITE START",
        "max-actions",
        BENCH_MAX_ACTIONS
    )

    for seed in BENCH_SEEDS:
        quick_print(
            "RESET SEED",
            seed
        )

        for mode in range(
            len(MODE_NAMES)
        ):
            elapsed = run_one(
                mode,
                seed
            )

            if elapsed < 0:
                quick_print(
                    "RESET TIME",
                    MODE_NAMES[mode],
                    "FAIL"
                )

                continue

            totals[mode] += elapsed
            successes[mode] += 1

            if (
                minimums[mode] < 0
                or elapsed < minimums[mode]
            ):
                minimums[mode] = elapsed

            if elapsed > maximums[mode]:
                maximums[mode] = elapsed

            quick_print(
                "RESET TIME",
                MODE_NAMES[mode],
                elapsed
            )

    quick_print(
        "RESET SUMMARY"
    )

    for mode in range(
        len(MODE_NAMES)
    ):
        if successes[mode] == 0:
            quick_print(
                MODE_NAMES[mode],
                "FAIL",
                "no-successful-runs"
            )

        else:
            quick_print(
                MODE_NAMES[mode],
                "avg",
                totals[mode] / successes[mode],
                "min",
                minimums[mode],
                "max",
                maximums[mode],
                "successful",
                successes[mode],
                "requested",
                len(BENCH_SEEDS)
            )

    quick_print(
        "RESET BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "RESET BENCH COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
