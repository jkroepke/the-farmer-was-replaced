import main


BENCH_VERSION = "ticks-v1"

BENCH_ITERATIONS = 512
BENCH_SPEEDUP = 64
PRIMARY_SIZE = 128

MODE_NAMES = [
    "loop-add-baseline",
    "dict-int-key",
    "dict-tuple-key",
    "list-membership",
    "set-membership",
    "dict-membership",
    "queue-cursor",
    "queue-pop-zero",
    "list-append",
    "list-concat"
]

MEMBERSHIP_SIZES = [
    16,
    64,
    256
]


def run_one(
    mode,
    size
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_ITERATIONS": BENCH_ITERATIONS,
        "BENCH_COLLECTION_SIZE": size
    }

    return simulate(
        "bench_ticks",
        Unlocks,
        {},
        globals,
        1,
        BENCH_SPEEDUP
    )


def run_primary():
    quick_print(
        "TICK BENCH PRIMARY",
        "iterations",
        BENCH_ITERATIONS,
        "size",
        PRIMARY_SIZE
    )

    for mode in range(
        len(MODE_NAMES)
    ):
        elapsed = run_one(
            mode,
            PRIMARY_SIZE
        )

        quick_print(
            "TICK SIM TIME",
            MODE_NAMES[mode],
            elapsed
        )


def run_membership_scaling():
    quick_print(
        "TICK BENCH MEMBERSHIP SCALING"
    )

    for size in MEMBERSHIP_SIZES:
        for mode in [
            3,
            4,
            5
        ]:
            elapsed = run_one(
                mode,
                size
            )

            quick_print(
                "TICK SCALE TIME",
                MODE_NAMES[mode],
                "size",
                size,
                elapsed
            )


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "TICK BENCH SUITE START"
    )

    run_primary()
    run_membership_scaling()

    quick_print(
        "TICK BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "TICK BENCH COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
