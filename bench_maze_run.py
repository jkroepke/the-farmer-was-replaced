# Finalist Maze benchmark controller for a real 32x32 farm.
#
# The extended 22-mode screen is recorded in docs/MAZE.md and is no longer
# rerun here.
#
# This runner answers the remaining production/leaderboard questions:
#
# 1. Which finalist wins at 1,000,000 Gold over three seeds?
# 2. Which finalist wins the real Maze leaderboard workload:
#    9,863,168 Gold, end-to-end including setup and termination?
#
# The world stays 32x32. Small Mazes are created only by changing the amount
# passed to use_item(Items.Weird_Substance, amount).


BENCH_SPEEDUP = 64
BENCH_VERBOSE = False
BENCH_GREEDY_AFTER = 30
BENCH_REBALANCE_UNTIL = 140
BENCH_SOLVES = 300
BENCH_WORLD_SIZE = 32

FINALIST_TARGET = 1000000
LEADERBOARD_TARGET = 9863168

FINALIST_SEEDS = [
    1,
    2,
    3
]

LEADERBOARD_SEEDS = [
    1,
    2
]


# Includes the current production/reference path plus every family that was
# still competitive after the extended screen.
FINALIST_MODE_IDS = [
    30,
    15,
    28,
    17,
    10,
    26,
    31
]

FINALIST_MODE_NAMES = [
    "final-uniform4-map-bfs-reuse300",
    "final-uniform5-map-bfs-reuse300",
    "final-packed-map-bfs-reuse300",
    "final-packed-reddit-visited-reuse300",
    "control-uniform4-zapakh-reuse300",
    "final-uniform5-zapakh-reuse300",
    "control-uniform4-zapakh-reuse8"
]


# The real leaderboard run is intentionally narrower. These are the strongest
# distinct architectures after the short and sustained screens.
LEADERBOARD_MODE_IDS = [
    30,
    15,
    28,
    17,
    10
]

LEADERBOARD_MODE_NAMES = [
    "lb-uniform4-map-bfs-reuse300",
    "lb-uniform5-map-bfs-reuse300",
    "lb-packed-map-bfs-reuse300",
    "lb-packed-reddit-visited-reuse300",
    "lb-uniform4-zapakh-reuse300"
]


def simulation_items():
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
    seed,
    gold_target
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_SOLVES": BENCH_SOLVES,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_GOLD_TARGET": gold_target,
        "BENCH_GREEDY_AFTER": BENCH_GREEDY_AFTER,
        "BENCH_REBALANCE_UNTIL": BENCH_REBALANCE_UNTIL,
        "BENCH_VERBOSE": BENCH_VERBOSE
    }

    return simulate(
        "bench_maze",
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_group(
    label,
    mode_ids,
    mode_names,
    seeds,
    gold_target
):
    quick_print(
        label,
        "START",
        "gold target",
        gold_target,
        "modes",
        len(mode_ids),
        "seeds",
        len(seeds)
    )

    totals = []
    minimums = []
    maximums = []

    for _ in mode_ids:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    for seed in seeds:
        quick_print(
            label,
            "SEED",
            seed
        )

        index = 0

        while index < len(mode_ids):
            quick_print(
                "RUN",
                mode_names[index]
            )

            run_time = run_one(
                mode_ids[index],
                seed,
                gold_target
            )

            totals[index] += run_time

            if (
                minimums[index] < 0
                or run_time < minimums[index]
            ):
                minimums[index] = run_time

            if run_time > maximums[index]:
                maximums[index] = run_time

            quick_print(
                mode_names[index],
                run_time
            )

            index += 1

    quick_print(
        label,
        "SUMMARY",
        "gold target",
        gold_target
    )

    seed_count = len(
        seeds
    )

    index = 0

    while index < len(mode_ids):
        quick_print(
            mode_names[index],
            "avg",
            totals[index] / seed_count,
            "min",
            minimums[index],
            "max",
            maximums[index]
        )

        index += 1

    quick_print(
        label,
        "DONE"
    )


def main():
    if get_world_size() != 32:
        quick_print(
            "MAZE BENCH NEEDS 32x32 WORLD",
            get_world_size()
        )
        return

    if max_drones() < 32:
        quick_print(
            "MAZE BENCH NEEDS 32 DRONES",
            max_drones()
        )
        return

    quick_print(
        "MAZE FINAL BENCH START"
    )

    benchmark_group(
        "MAZE FINALIST",
        FINALIST_MODE_IDS,
        FINALIST_MODE_NAMES,
        FINALIST_SEEDS,
        FINALIST_TARGET
    )

    benchmark_group(
        "MAZE LEADERBOARD",
        LEADERBOARD_MODE_IDS,
        LEADERBOARD_MODE_NAMES,
        LEADERBOARD_SEEDS,
        LEADERBOARD_TARGET
    )

    quick_print(
        "MAZE FINAL BENCH DONE"
    )


main()
