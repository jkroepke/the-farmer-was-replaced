# Amount-based Maze benchmark controller for a real 32x32 farm.
#
# This runner intentionally does NOT call set_world_size(). The farm must
# already be 32x32. Small mazes are created by changing only the amount passed
# to use_item(Items.Weird_Substance, amount).
#
# Historical 8/16/32 x 25/100/300 results remain documented in docs/MAZE.md,
# but this runner no longer executes that old matrix.

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 64
BENCH_GOLD_TARGET = 200000
BENCH_VERBOSE = False

# Keep the historical reference thresholds unchanged for the current-method
# control mode.
BENCH_GREEDY_AFTER = 30
BENCH_REBALANCE_UNTIL = 140
BENCH_SOLVES = 300
BENCH_WORLD_SIZE = 32

MODE_IDS = [
    6,
    7,
    8,
    9,
    10,
    11
]

MODE_NAMES = [
    "current-reference-32",
    "cover-3x3",
    "cover-4x4",
    "cover-2x4x4",
    "zapakh-32x4x4",
    "steam-32x4x4"
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
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_SOLVES": BENCH_SOLVES,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_GOLD_TARGET": BENCH_GOLD_TARGET,
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
        "MAZE SPECIAL BENCH START",
        "gold target",
        BENCH_GOLD_TARGET
    )

    totals = []
    minimums = []
    maximums = []

    for _ in MODE_NAMES:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    for seed in BENCH_SEEDS:
        quick_print(
            "SEED",
            seed
        )

        mode_index = 0

        while mode_index < len(MODE_IDS):
            quick_print(
                "RUN",
                MODE_NAMES[mode_index]
            )

            run_time = run_one(
                MODE_IDS[mode_index],
                seed
            )

            totals[mode_index] += run_time

            if (
                minimums[mode_index] < 0
                or run_time < minimums[mode_index]
            ):
                minimums[mode_index] = run_time

            if run_time > maximums[mode_index]:
                maximums[mode_index] = run_time

            quick_print(
                MODE_NAMES[mode_index],
                run_time
            )

            mode_index += 1

    seed_count = len(
        BENCH_SEEDS
    )

    quick_print(
        "SUMMARY",
        "gold target",
        BENCH_GOLD_TARGET
    )

    mode_index = 0

    while mode_index < len(MODE_NAMES):
        quick_print(
            MODE_NAMES[mode_index],
            "avg",
            totals[mode_index] / seed_count,
            "min",
            minimums[mode_index],
            "max",
            maximums[mode_index]
        )

        mode_index += 1

    quick_print(
        "MAZE SPECIAL BENCH DONE"
    )


main()
