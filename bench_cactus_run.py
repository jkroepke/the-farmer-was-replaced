import main


BENCH_VERSION = "cactus-v3"

BENCH_WORLD_SIZE = 32
BENCH_CYCLES = 3
BENCH_SPEEDUP = 10000

BENCH_SEEDS = [
    1,
    2,
    3
]

MODE_NAMES = [
    "current-production",
    "two-wave-bubble-reset",
    "two-wave-insertion-reset",
    "two-wave-insertion-reuse",
    "two-wave-insertion-reroll-reuse",
    "tstambaugh-reference-32",
    "nql1314-reference",
    "tstambaugh-placed-generalized",
    "adaptive-placed-pool",
    "persistent-mateus",
    "adaptive-binary-spawn",
    "adaptive-flekay-powers",
    "current-production-fresh"
]

# Follow-up finalists. The source-near Tstambaugh mode proved competitive,
# so it now runs the full three-seed / three-cycle matrix as a control.
CANDIDATE_MODES = [
    8,
    10,
    11
]

# One cold 32x32 cycle is decisive for Leaderboards.Cactus because one valid
# full-chain harvest produces the exact 33,554,432-Cactus target.
TARGET_MODES = [
    0,
    5,
    7,
    8,
    10,
    11,
    12
]

REFERENCE_MODES = [
    6,
    9
]


def simulation_items(cactus_amount):
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 1000000000,
        Items.Cactus: cactus_amount,
        Items.Bone: 1000000000,
        Items.Gold: 1000000000,
        Items.Power: 1000000000,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def simulation_unlocks(
    megafarm_level
):
    if megafarm_level < 0:
        return Unlocks

    unlocks = {}

    for unlock in Unlocks:
        unlocks[unlock] = -1

    unlocks[
        Unlocks.Megafarm
    ] = megafarm_level

    return unlocks


def run_one(
    mode,
    seed,
    world_size,
    cycles,
    megafarm_level,
    cactus_amount
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": world_size,
        "BENCH_CYCLES": cycles
    }

    return simulate(
        "bench_cactus",
        simulation_unlocks(
            megafarm_level
        ),
        simulation_items(
            cactus_amount
        ),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_modes(
    label,
    modes,
    seeds,
    world_size,
    cycles,
    megafarm_level,
    cactus_amount
):
    totals = []
    minimums = []
    maximums = []

    for _ in modes:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    quick_print(
        label,
        "world",
        world_size,
        "cycles",
        cycles,
        "megafarm",
        megafarm_level
    )

    for seed in seeds:
        quick_print(
            "SEED",
            seed
        )

        mode_index = 0

        for mode in modes:
            quick_print(
                "RUN",
                MODE_NAMES[mode]
            )

            run_time = run_one(
                mode,
                seed,
                world_size,
                cycles,
                megafarm_level,
                cactus_amount
            )

            totals[
                mode_index
            ] += run_time

            if (
                minimums[
                    mode_index
                ] < 0
                or run_time
                < minimums[
                    mode_index
                ]
            ):
                minimums[
                    mode_index
                ] = run_time

            if (
                run_time
                > maximums[
                    mode_index
                ]
            ):
                maximums[
                    mode_index
                ] = run_time

            quick_print(
                MODE_NAMES[mode],
                run_time
            )

            mode_index += 1

    quick_print(
        label,
        "SUMMARY"
    )

    mode_index = 0
    seed_count = len(
        seeds
    )

    for mode in modes:
        average = (
            totals[
                mode_index
            ]
            / seed_count
        )

        quick_print(
            MODE_NAMES[mode],
            "avg",
            average,
            "min",
            minimums[
                mode_index
            ],
            "max",
            maximums[
                mode_index
            ]
        )

        mode_index += 1


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "CACTUS BENCH SUITE START"
    )

    benchmark_modes(
        "CACTUS TARGET COLD",
        TARGET_MODES,
        BENCH_SEEDS,
        BENCH_WORLD_SIZE,
        1,
        -1,
        0
    )

    benchmark_modes(
        "CACTUS FINALISTS",
        CANDIDATE_MODES,
        BENCH_SEEDS,
        BENCH_WORLD_SIZE,
        BENCH_CYCLES,
        -1,
        1000000000
    )

    benchmark_modes(
        "CACTUS REFERENCE SMOKE",
        REFERENCE_MODES,
        [1],
        BENCH_WORLD_SIZE,
        1,
        -1,
        1000000000
    )

    # Generalization smoke tests:
    # - smaller worlds with max available drones
    # - 32x32 with fewer drones so each persistent worker owns
    #   multiple rows/columns through index += worker_count
    for world_size in [
        6,
        16
    ]:
        benchmark_modes(
            "CACTUS SIZE SMOKE",
            [
                2,
                8
            ],
            [1],
            world_size,
            1,
            -1,
            1000000000
        )

    benchmark_modes(
        "CACTUS DRONE SMOKE",
        [
            4,
            7,
            8
        ],
        [1],
        BENCH_WORLD_SIZE,
        1,
        3,
        1000000000
    )

    quick_print(
        "CACTUS BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "CACTUS BENCHMARKS COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
