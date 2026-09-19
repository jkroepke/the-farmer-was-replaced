# Extended Maze benchmark controller for a real 32x32 farm.
#
# The world remains 32x32. Small Mazes are created only through the amount
# passed to use_item(Items.Weird_Substance, amount).
#
# Benchmark structure:
# - SCREEN: all current references and mutations, 200k Gold, seeds 1/2/3
# - SUSTAINED: strongest/most informative families, 1M Gold, seeds 1/2
#
# Historical benchmark matrices remain in docs/MAZE.md and are not rerun.


BENCH_SPEEDUP = 64
BENCH_VERBOSE = False
BENCH_GREEDY_AFTER = 30
BENCH_REBALANCE_UNTIL = 140
BENCH_SOLVES = 300
BENCH_WORLD_SIZE = 32

REBUILD_SMOKE_TARGET = 100000
SCREEN_TARGET = 200000
SUSTAINED_TARGET = 1000000

SCREEN_SEEDS = [
    1,
    2,
    3
]

SUSTAINED_SEEDS = [
    1,
    2
]


REBUILD_SMOKE_MODE_IDS = [
    18
]

REBUILD_SMOKE_MODE_NAMES = [
    "mut-packed-zapakh-reuse1"
]


CORE_MODE_IDS = [
    10,
    12,
    13,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    31
]

CORE_MODE_NAMES = [
    "ref-zapakh-4-reuse300",
    "mut-packed-zapakh-fresh",
    "mut-packed-zapakh-reuse300",
    "desc-reddit-packed-fresh",
    "mut-reddit-packed-visited-reuse300",
    "mut-packed-zapakh-reuse1",
    "mut-packed-zapakh-reuse2",
    "mut-packed-zapakh-reuse4",
    "mut-packed-zapakh-reuse8",
    "mut-packed-zapakh-reuse16",
    "mut-packed-unranked-fresh",
    "mut-packed-unranked-reuse300",
    "mut-uniform4-zapakh-fresh",
    "mut-uniform5-zapakh-reuse300",
    "mut-uniform5-zapakh-fresh",
    "mut-uniform4-zapakh-reuse8"
]


MAP_MODE_IDS = [
    11,
    15,
    28,
    29,
    30
]

MAP_MODE_NAMES = [
    "ref-steam-4-reuse300",
    "ref-reddit5-map-bfs-reuse300",
    "mut-packed-map-bfs-reuse300",
    "mut-packed-map-bfs-fresh",
    "mut-uniform4-map-bfs-reuse300"
]


# Keep the most synchronization-sensitive source-near port last so a problem
# here cannot hide the results from all newer candidates.
LEGACY_MODE_IDS = [
    14
]

LEGACY_MODE_NAMES = [
    "ref-msmith93-full32-fresh"
]


# Sustained set deliberately spans different hypotheses rather than only
# variants expected to be fast:
# - current measured winner
# - full-field packing + ranked reuse
# - Reddit fresh intersection solver
# - Reddit solver with visited/reuse mutation
# - source-described 5x5 map+BFS
# - unranked packed reuse (ranking ablation)
# - packed map+BFS
# - short reuse cap
SUSTAINED_MODE_IDS = [
    10,
    13,
    16,
    17,
    15,
    24,
    28,
    21
]

SUSTAINED_MODE_NAMES = [
    "ref-zapakh-4-reuse300",
    "mut-packed-zapakh-reuse300",
    "desc-reddit-packed-fresh",
    "mut-reddit-packed-visited-reuse300",
    "ref-reddit5-map-bfs-reuse300",
    "mut-packed-unranked-reuse300",
    "mut-packed-map-bfs-reuse300",
    "mut-packed-zapakh-reuse8"
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

    index = 0
    seed_count = len(seeds)

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
        "MAZE EXTENDED BENCH START"
    )

    benchmark_group(
        "MAZE REBUILD SMOKE",
        REBUILD_SMOKE_MODE_IDS,
        REBUILD_SMOKE_MODE_NAMES,
        [
            1
        ],
        REBUILD_SMOKE_TARGET
    )

    benchmark_group(
        "MAZE CORE",
        CORE_MODE_IDS,
        CORE_MODE_NAMES,
        SCREEN_SEEDS,
        SCREEN_TARGET
    )

    benchmark_group(
        "MAZE MAP",
        MAP_MODE_IDS,
        MAP_MODE_NAMES,
        SCREEN_SEEDS,
        SCREEN_TARGET
    )

    benchmark_group(
        "MAZE SUSTAINED",
        SUSTAINED_MODE_IDS,
        SUSTAINED_MODE_NAMES,
        SUSTAINED_SEEDS,
        SUSTAINED_TARGET
    )

    benchmark_group(
        "MAZE LEGACY REF",
        LEGACY_MODE_IDS,
        LEGACY_MODE_NAMES,
        SCREEN_SEEDS,
        SCREEN_TARGET
    )

    quick_print(
        "MAZE EXTENDED BENCH DONE"
    )


main()
