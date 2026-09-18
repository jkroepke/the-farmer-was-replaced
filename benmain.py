# Maze simulation benchmark controller.
#
# Run this file on the real farm. simulate() restores the real farm
# after every benchmark run.
#
# Runtime returned by simulate() is the primary metric because every
# strategy solves the same number of treasures with the same seed.
#
# Modes are implemented in benchmaze.py.


BENCH_WORLD_SIZES = [
    8,
    16,
    32
]

BENCH_SOLVE_COUNTS = [
    25,
    100,
    300
]

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 64

# Community tree/greedy code begins greedy path attempts after ~30 solves.
BENCH_GREEDY_AFTER = 30

# The referenced rebalancing implementation only rotates early/mid run.
# Its source uses solved < 140.
BENCH_REBALANCE_UNTIL = 140

# Set True when you also want each simulated worker to quick_print
# its final get_tick_count()/get_time() values.
BENCH_VERBOSE = False


MODE_NAMES = [
    "fresh-right-hand",
    "reuse-bfs",
    "reuse-tree-greedy",
    "reuse-tree-greedy-lazy-rebalance",
    "reuse-tree-greedy-full-reindex",
    "reference-tree-rebalancing"
]


def simulation_items():
    # Deliberately oversized resource pool so benchmarks measure maze
    # pathing rather than resource acquisition.
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 1000000000,
        Items.Cactus: 1000000000,
        Items.Bone: 1000000000,
        Items.Gold: 0,
        Items.Power: 1000000000,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_one(
    mode,
    world_size,
    solves,
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": world_size,
        "BENCH_SOLVES": solves,
        "BENCH_GREEDY_AFTER": BENCH_GREEDY_AFTER,
        "BENCH_REBALANCE_UNTIL": BENCH_REBALANCE_UNTIL,
        "BENCH_VERBOSE": BENCH_VERBOSE
    }

    filename = "benchmaze"

    if mode == 5:
        filename = "benchmaze_reference"

    return simulate(
        filename,
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_case(
    world_size,
    solves
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
        solves
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
                solves,
                seed
            )

            totals[mode] += run_time

            if (
                minimums[mode] < 0
                or run_time < minimums[mode]
            ):
                minimums[mode] = run_time

            if run_time > maximums[mode]:
                maximums[mode] = run_time

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
        solves
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
        "MAZE BENCH START"
    )

    for world_size in BENCH_WORLD_SIZES:
        for solves in BENCH_SOLVE_COUNTS:
            benchmark_case(
                world_size,
                solves
            )

    quick_print(
        "MAZE BENCH DONE"
    )


main()
