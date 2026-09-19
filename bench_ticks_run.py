import bench_ticks
import main


BENCH_VERSION = "ticks-v3"

BENCH_ITERATIONS = 512
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
    quick_print(
        "TICK CASE START",
        MODE_NAMES[mode],
        "iterations",
        BENCH_ITERATIONS,
        "size",
        size
    )

    return bench_ticks.run_mode(
        mode,
        BENCH_ITERATIONS,
        size
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
        run_one(
            mode,
            PRIMARY_SIZE
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
            run_one(
                mode,
                size
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
