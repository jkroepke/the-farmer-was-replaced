BENCH_VERSION = "move-v1"
BENCH_SPEEDUP = 10000
BENCH_WORLD_SIZE = 32

MODE_NAMES = [
    "utils-arithmetic",
    "delta-static",
    "direction-static",
    "dict-runtime",
    "list-runtime",
    "delta-known-current"
]

COLD_COUNTS = [
    1,
    10,
    100
]

WARM_COUNTS = [
    10,
    100,
    1000
]


def run_one(
    mode,
    count,
    warm
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_COUNT": count,
        "BENCH_WARM": warm,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE
    }

    return simulate(
        "bench_move",
        Unlocks,
        {},
        globals,
        1,
        BENCH_SPEEDUP
    )


def run_phase(
    label,
    counts,
    warm
):
    quick_print(
        label,
        "START"
    )

    for count in counts:
        quick_print(
            label,
            "COUNT",
            count
        )

        mode = 0

        while mode < len(
            MODE_NAMES
        ):
            elapsed = run_one(
                mode,
                count,
                warm
            )

            quick_print(
                "MOVE SIM TIME",
                MODE_NAMES[mode],
                "count",
                count,
                elapsed
            )

            mode += 1

    quick_print(
        label,
        "DONE"
    )


def main():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    run_phase(
        "MOVE COLD",
        COLD_COUNTS,
        False
    )

    run_phase(
        "MOVE WARM",
        WARM_COUNTS,
        True
    )

    quick_print(
        "MOVE BENCH DONE"
    )


main()
