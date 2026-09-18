# Dinosaur simulation benchmark controller.
#
# All implementations live in bench_dinosaur.py.
#
# This benchmark measures time to reach fixed tail occupancy targets.
# That is more informative than only measuring a full board because
# shortcutting is expected to matter mainly in the early/mid run.


BENCH_WORLD_SIZES = [
    8,
    16,
    32
]

BENCH_TARGET_PERCENTS = [
    25,
    50,
    75,
    95
]

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 64

BENCH_VERBOSE = False


MODE_NAMES = [
    "hamiltonian-skyscraper",
    "safe-shortcuts-annealed-50",
    "safe-shortcuts-hard-25",
    "safe-shortcuts-hard-50",
    "skysdottir-tfwr-reference"
]


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
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": world_size,
        "BENCH_TARGET_PERCENT": target_percent,
        "BENCH_VERBOSE": BENCH_VERBOSE
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

    for _ in MODE_NAMES:
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

        for mode in range(
            len(MODE_NAMES)
        ):
            run_time = run_one(
                mode,
                world_size,
                target_percent,
                seed
            )

            totals[mode] += (
                run_time
            )

            if (
                minimums[mode] < 0
                or run_time
                < minimums[mode]
            ):
                minimums[mode] = (
                    run_time
                )

            if (
                run_time
                > maximums[mode]
            ):
                maximums[mode] = (
                    run_time
                )

            quick_print(
                MODE_NAMES[mode],
                run_time
            )

    seed_count = len(
        BENCH_SEEDS
    )

    quick_print(
        "SUMMARY",
        world_size,
        target_percent
    )

    for mode in range(
        len(MODE_NAMES)
    ):
        average = (
            totals[mode]
            / seed_count
        )

        quick_print(
            MODE_NAMES[mode],
            "avg",
            average,
            "min",
            minimums[mode],
            "max",
            maximums[mode]
        )


def main():
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


main()
