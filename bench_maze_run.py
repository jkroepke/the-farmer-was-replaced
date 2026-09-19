# Maze leaderboard finalist benchmark.
#
# Decisive workload:
#
#     num_items(Items.Gold) >= 9863168
#
# Every run starts cold through simulate():
# - empty farm state for the strategy
# - worker spawn and positioning
# - initial Bush/Maze creation
# - all Treasure solves and relocations
# - any 300-reuse Maze rebuilds
# - termination after the exact leaderboard threshold
#
# Short 200k / 1M screens are recorded in docs/MAZE.md and are no longer
# used to select the final leaderboard algorithm.
#
# Modes 32/33 test route-spawn placement.
# Modes 34/35 test the spawn-v4 hierarchical result in the real leaderboard
# workload: a persistent binary spawn tree with row-major 4x4 slots versus
# the precomputed nearest-32 toroidal 4x4 slot set.
# Modes 36..39 test Flekay's stationary full-coverage Maze idea:
# source-near 5x5 substance spam, one-drone-per-cell spam/event-gated
# mutations, and a 4x4 event-gated geometry control.


BENCH_VERSION = "maze-v4"
BENCH_SPEEDUP = 10000
BENCH_VERBOSE = False
BENCH_GREEDY_AFTER = 30
BENCH_REBALANCE_UNTIL = 140
BENCH_SOLVES = 300
BENCH_WORLD_SIZE = 32

LEADERBOARD_TARGET = 9863168

LEADERBOARD_SEEDS = [
    1,
    2,
    3
]


LEADERBOARD_MODE_IDS = [
    38,
    37,
    36,
    39,
    35,
    34,
    33,
    32,
    30,
    15,
    28,
    17,
    10
]

LEADERBOARD_MODE_NAMES = [
    "lb-stationary5-event",
    "lb-stationary5-spam",
    "ref-flekay-5x5-substance-spam",
    "lb-stationary4-event",
    "lb-nearest4-map-bfs-tree-spawn",
    "lb-uniform4-map-bfs-tree-spawn",
    "lb-uniform4-map-bfs-route-spawn",
    "lb-uniform5-map-bfs-route-spawn",
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
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_SOLVES": BENCH_SOLVES,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_GOLD_TARGET": LEADERBOARD_TARGET,
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
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

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
        "MAZE LEADERBOARD COLD BENCH START",
        "gold target",
        LEADERBOARD_TARGET,
        "modes",
        len(LEADERBOARD_MODE_IDS),
        "seeds",
        len(LEADERBOARD_SEEDS)
    )

    totals = []
    minimums = []
    maximums = []

    for _ in LEADERBOARD_MODE_IDS:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    for seed in LEADERBOARD_SEEDS:
        quick_print(
            "MAZE LEADERBOARD SEED",
            seed
        )

        index = 0

        while index < len(
            LEADERBOARD_MODE_IDS
        ):
            quick_print(
                "RUN",
                LEADERBOARD_MODE_NAMES[
                    index
                ]
            )

            run_time = run_one(
                LEADERBOARD_MODE_IDS[
                    index
                ],
                seed
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
                LEADERBOARD_MODE_NAMES[
                    index
                ],
                run_time
            )

            index += 1

    quick_print(
        "MAZE LEADERBOARD SUMMARY",
        "gold target",
        LEADERBOARD_TARGET
    )

    index = 0
    seed_count = len(
        LEADERBOARD_SEEDS
    )

    while index < len(
        LEADERBOARD_MODE_IDS
    ):
        quick_print(
            LEADERBOARD_MODE_NAMES[
                index
            ],
            "avg",
            totals[index] / seed_count,
            "min",
            minimums[index],
            "max",
            maximums[index]
        )

        index += 1

    quick_print(
        "MAZE LEADERBOARD COLD BENCH DONE"
    )


main()
