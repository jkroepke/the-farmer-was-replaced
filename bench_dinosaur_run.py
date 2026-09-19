import main

BENCH_VERSION = "dinosaur-v1"

# Dinosaur simulation benchmark controller.
#
# All implementations live in bench_dinosaur.py.
#
# This benchmark measures time to reach fixed tail occupancy targets,
# but production decisions must be based on Bone throughput.
#
# For the same target tail, lower runtime means higher throughput.
# Across different tail targets, compare Bones/second or Bones/minute
# because Dinosaur yield grows quadratically with tail length.


BENCH_WORLD_SIZES = [
    32
]

BENCH_TARGET_PERCENTS = [
    95,
    97,
    99,
    100
]

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 64

BENCH_VERBOSE = False

# Fixed-target runs isolate path efficiency.
BENCH_CYCLES = 1

# Only benchmark the two remaining production candidates.
BENCH_MODES = [
    0,
    4
]

# Sustained runs measure production efficiency across repeated
# harvest/restart cycles in one simulation.
SUSTAINED_CYCLES = 3
SUSTAINED_TARGET_PERCENTS = [
    95,
    97,
    99,
    100
]
SUSTAINED_MODES = [
    0,
    4
]


MODE_NAMES = [
    "hamiltonian-skyscraper",
    "safe-shortcuts-annealed-50",
    "safe-shortcuts-hard-25",
    "safe-shortcuts-hard-50",
    "skysdottir-tfwr-reference"
]


def target_tail_length(
    world_size,
    target_percent
):
    board = (
        world_size
        * world_size
    )

    target = (
        board
        * target_percent
        // 100
    )

    if target < 2:
        target = 2

    if target >= board:
        target = board - 1

    return target


def expected_bones(
    world_size,
    target_percent
):
    tail = target_tail_length(
        world_size,
        target_percent
    )

    return (
        tail
        * tail
    )


def simulation_items():
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 1000000000,
        Items.Cactus: 1000000000,
        Items.Bone: 0,
        Items.Gold: 1000000000,
        Items.Power: 1000000000,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_one(
    mode,
    world_size,
    target_percent,
    seed,
    cycles
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": world_size,
        "BENCH_TARGET_PERCENT": target_percent,
        "BENCH_VERBOSE": BENCH_VERBOSE,
        "BENCH_CYCLES": cycles
    }

    return simulate(
        "bench_dinosaur",
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_case(
    world_size,
    target_percent
):
    totals = []
    minimums = []
    maximums = []

    for _ in BENCH_MODES:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    quick_print(
        "CASE",
        world_size,
        target_percent
    )

    for seed in BENCH_SEEDS:
        quick_print(
            "SEED",
            seed
        )

        mode_index = 0

        for mode in BENCH_MODES:
            run_time = run_one(
                mode,
                world_size,
                target_percent,
                seed,
                BENCH_CYCLES
            )

            totals[mode_index] += (
                run_time
            )

            if (
                minimums[mode_index] < 0
                or run_time
                < minimums[mode_index]
            ):
                minimums[mode_index] = (
                    run_time
                )

            if (
                run_time
                > maximums[mode_index]
            ):
                maximums[mode_index] = (
                    run_time
                )

            bones = (
                expected_bones(
                    world_size,
                    target_percent
                )
                * BENCH_CYCLES
            )

            bones_per_second = (
                bones
                / run_time
            )

            quick_print(
                MODE_NAMES[mode],
                run_time,
                "bones/s",
                bones_per_second,
                "bones/min",
                bones_per_second * 60
            )

            mode_index += 1

    seed_count = len(
        BENCH_SEEDS
    )

    quick_print(
        "SUMMARY",
        world_size,
        target_percent
    )

    mode_index = 0

    for mode in BENCH_MODES:
        average = (
            totals[mode_index]
            / seed_count
        )

        bones = (
            expected_bones(
                world_size,
                target_percent
            )
            * BENCH_CYCLES
        )

        bones_per_second = (
            bones
            / average
        )

        quick_print(
            MODE_NAMES[mode],
            "avg",
            average,
            "min",
            minimums[mode_index],
            "max",
            maximums[mode_index],
            "tail",
            target_tail_length(
                world_size,
                target_percent
            ),
            "bones",
            bones,
            "bones/s",
            bones_per_second,
            "bones/min",
            bones_per_second * 60
        )

        mode_index += 1


def benchmark_sustained():
    world_size = 32

    quick_print(
        "DINOSAUR SUSTAINED START",
        "cycles",
        SUSTAINED_CYCLES
    )

    for target_percent in SUSTAINED_TARGET_PERCENTS:
        totals = []

        for _ in SUSTAINED_MODES:
            totals.append(0)

        quick_print(
            "SUSTAINED CASE",
            world_size,
            target_percent
        )

        for seed in BENCH_SEEDS:
            quick_print(
                "SEED",
                seed
            )

            mode_index = 0

            for mode in SUSTAINED_MODES:
                run_time = run_one(
                    mode,
                    world_size,
                    target_percent,
                    seed,
                    SUSTAINED_CYCLES
                )

                totals[
                    mode_index
                ] += run_time

                bones = (
                    expected_bones(
                        world_size,
                        target_percent
                    )
                    * SUSTAINED_CYCLES
                )

                bones_per_second = (
                    bones
                    / run_time
                )

                quick_print(
                    MODE_NAMES[mode],
                    run_time,
                    "cycles",
                    SUSTAINED_CYCLES,
                    "bones",
                    bones,
                    "bones/s",
                    bones_per_second,
                    "bones/min",
                    bones_per_second * 60
                )

                mode_index += 1

        quick_print(
            "SUSTAINED SUMMARY",
            world_size,
            target_percent
        )

        mode_index = 0

        for mode in SUSTAINED_MODES:
            average = (
                totals[
                    mode_index
                ]
                / len(BENCH_SEEDS)
            )

            bones = (
                expected_bones(
                    world_size,
                    target_percent
                )
                * SUSTAINED_CYCLES
            )

            bones_per_second = (
                bones
                / average
            )

            quick_print(
                MODE_NAMES[mode],
                "avg",
                average,
                "cycles",
                SUSTAINED_CYCLES,
                "bones",
                bones,
                "bones/s",
                bones_per_second,
                "bones/min",
                bones_per_second * 60
            )

            mode_index += 1

    quick_print(
        "DINOSAUR SUSTAINED DONE"
    )


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "DINOSAUR BENCH START"
    )

    for world_size in BENCH_WORLD_SIZES:
        for target_percent in BENCH_TARGET_PERCENTS:
            benchmark_case(
                world_size,
                target_percent
            )

    quick_print(
        "DINOSAUR BENCH DONE"
    )

    benchmark_sustained()


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "DINOSAUR BENCHMARKS COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
