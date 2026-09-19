import main


BENCH_VERSION = "reset-v1"

BENCH_SPEEDUP = 64
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

    # Empty unlock/item maps model Fastest Reset from the initial farm.
    return simulate(
        "bench_reset",
        {},
        {},
        globals,
        seed,
        BENCH_SPEEDUP
    )


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

            totals[mode] += elapsed

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

    count = len(
        BENCH_SEEDS
    )

    for mode in range(
        len(MODE_NAMES)
    ):
        quick_print(
            MODE_NAMES[mode],
            "avg",
            totals[mode] / count,
            "min",
            minimums[mode],
            "max",
            maximums[mode]
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
