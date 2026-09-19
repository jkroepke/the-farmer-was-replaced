BENCH_VERSION = "spawn-v5"

BENCH_WORLD_SIZE = 32
BENCH_SPEEDUP = 10000

BENCH_SEEDS = [
    1,
    2,
    3
]

MODE_NAMES = [
    "baseline-origin00-rowmajor",
    "origin00-parent-near",
    "band-anchor-rowmajor",
    "band-precomputed-farthest-parent-near",
    "nearest-slots-precomputed-rowmajor",
    "nearest-slots-precomputed-farthest-parent-near",
    "binary-tree-rowmajor-origin00",
    "binary-tree-nearest-origin00",
    "dual-spawner-rowmajor",
    "flekay-powers-rowmajor",
    "jarvan-powers-rowmajor"
]

# Topology shootout keeps the final 32 target origins identical and keeps
# the root/parent on CURRENT_ORIGINS[0]. Mode 1 is therefore the serial control.
# Mode 7 remains the measured locality+binary winner but is not a topology-only
# comparison because it uses the alternate NEAREST_ORIGINS layout.
TOPOLOGY_MODES = [
    1,
    8,
    9,
    10,
    6
]


def simulation_items():
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 1000000000,
        Items.Cactus: 1000000000,
        Items.Bone: 1000000000,
        Items.Gold: 1000000000,
        Items.Power: 1000000000,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_one(mode, seed):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE
    }

    return simulate(
        "bench_spawn",
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

    if get_world_size() != BENCH_WORLD_SIZE:
        quick_print(
            "SPAWN BENCH NEEDS WORLD",
            BENCH_WORLD_SIZE,
            "current",
            get_world_size()
        )
        return

    if max_drones() < 32:
        quick_print(
            "SPAWN BENCH NEEDS 32 DRONES",
            max_drones()
        )
        return

    quick_print(
        "SPAWN BENCH START",
        "world",
        BENCH_WORLD_SIZE,
        "modes",
        len(MODE_NAMES),
        "seeds",
        len(BENCH_SEEDS)
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
            "SPAWN SEED",
            seed
        )

        mode_index = 0

        while mode_index < len(
            TOPOLOGY_MODES
        ):
            mode = TOPOLOGY_MODES[
                mode_index
            ]

            run_time = run_one(
                mode,
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

            mode_index += 1

    quick_print(
        "SPAWN BENCH SUMMARY"
    )

    mode_index = 0
    count = len(BENCH_SEEDS)

    while mode_index < len(
        TOPOLOGY_MODES
    ):
        mode = TOPOLOGY_MODES[
            mode_index
        ]

        quick_print(
            MODE_NAMES[mode],
            "avg",
            totals[mode] / count,
            "min",
            minimums[mode],
            "max",
            maximums[mode]
        )

        mode_index += 1

    quick_print(
        "SPAWN BENCH DONE"
    )


main()
