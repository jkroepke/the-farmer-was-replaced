import main


BENCH_VERSION = "farm-v1"

# Normal-farm benchmark suite.
#
# This runner intentionally uses two levels:
#
# 1. Finalist matrix:
#    only candidates still competitive after the first 3-seed Hay run.
#
# 2. Reference smoke tests:
#    source-near implementations remain unchanged, but use smaller targets
#    so a deliberately old/single-drone reference cannot dominate suite time.
#
# First screening result (32x32, 8 drones, Hay):
#
# current-l-no-polyculture:
#   avg 298.71 s
#
# columns-one-sunflower-column-simple-crop:
#   avg 436.96 s
#
# competitive modes:
#   about 29.6 .. 44.6 s
#
# Modes 1 and 7 therefore stay implemented in bench_farm.py for historical
# reproducibility, but are removed from the expensive full matrix.


BENCH_WORLD_SIZE = 32

BENCH_FOCUSES = [
    0,
    1,
    2
]

# Long enough to amortize setup, but much smaller than the original
# 20M / 100M / 20M screening targets.
BENCH_TARGET_GAINS = [
    10000000,
    20000000,
    10000000
]

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 64

PROFILE_NAMES = [
    "partial-megafarm-level-3",
    "max-megafarm"
]

# Finalists after the first full Hay screening.
CROP_MODES = [
    0,
    2,
    3,
    4,
    5,
    6
]

# Source-near crop reference. Keep it unchanged, but only smoke-test it.
REFERENCE_CROP_MODES = [
    8
]

REFERENCE_TARGET_GAINS = [
    1000000,
    2000000,
    1000000
]

REFERENCE_SEED = 1

# Dedicated Power throughput is secondary to crop throughput under
# self-powered conditions. Keep it available for targeted diagnostics,
# but do not make the default suite wait for it.
RUN_POWER_BENCHMARK = False

POWER_MODES = [
    20,
    21,
    22,
    23
]

# Small diagnostic target when RUN_POWER_BENCHMARK is enabled.
POWER_TARGET_GAIN = 5000

MODE_NAMES = [
    "current-l-production",
    "current-l-no-polyculture",
    "columns-pure-current-crop",
    "columns-one-sunflower-row-dumb",
    "columns-one-sunflower-column-dumb",
    "columns-two-sunflower-columns-dumb",
    "columns-one-sunflower-column-max-petal",
    "columns-one-sunflower-column-simple-crop",
    "juritox-reference-single-drone",
    "unused-9",
    "unused-10",
    "unused-11",
    "unused-12",
    "unused-13",
    "unused-14",
    "unused-15",
    "unused-16",
    "unused-17",
    "unused-18",
    "unused-19",
    "current-l-power",
    "mateus-reference-fullfield-dumb",
    "fullfield-dumb-north-only",
    "juritox-reference-max-petal"
]


def simulation_unlocks(profile):
    if profile == 1:
        return Unlocks

    unlocks = {}

    for unlock in Unlocks:
        unlocks[unlock] = -1

    unlocks[
        Unlocks.Megafarm
    ] = 3

    return unlocks


def simulation_items():
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 1000000000,
        Items.Cactus: 1000000000,
        Items.Bone: 1000000000,
        Items.Gold: 1000000000,
        # Start cold. Crop layouts must earn their own execution-speed
        # advantage instead of consuming a preloaded Power buffer.
        Items.Power: 0,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_clean_probe():
    globals = {
        "BENCH_MODE": 99,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_FOCUS": 0,
        "BENCH_TARGET_GAIN": 1,
        "BENCH_VERBOSE": False
    }

    simulate(
        "bench_farm",
        simulation_unlocks(
            1
        ),
        simulation_items(),
        globals,
        1,
        BENCH_SPEEDUP
    )


def run_one(
    mode,
    profile,
    focus,
    target_gain,
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_FOCUS": focus,
        "BENCH_TARGET_GAIN": target_gain,
        "BENCH_VERBOSE": False
    }

    return simulate(
        "bench_farm",
        simulation_unlocks(
            profile
        ),
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_modes(
    label,
    modes,
    profile,
    focus,
    target_gain,
    seeds
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
        PROFILE_NAMES[profile],
        "focus",
        focus,
        "target-gain",
        target_gain
    )

    for seed in seeds:
        quick_print(
            "SEED",
            seed
        )

        mode_index = 0

        for mode in modes:
            run_time = run_one(
                mode,
                profile,
                focus,
                target_gain,
                seed
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
        "SUMMARY",
        PROFILE_NAMES[profile],
        "focus",
        focus
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


def benchmark_crop_finalists():
    for profile in range(
        len(PROFILE_NAMES)
    ):
        focus_index = 0

        for focus in BENCH_FOCUSES:
            benchmark_modes(
                "FARM FINAL",
                CROP_MODES,
                profile,
                focus,
                BENCH_TARGET_GAINS[
                    focus_index
                ],
                BENCH_SEEDS
            )

            focus_index += 1


def benchmark_crop_references():
    seeds = [
        REFERENCE_SEED
    ]

    focus_index = 0

    for focus in BENCH_FOCUSES:
        benchmark_modes(
            "FARM REFERENCE SMOKE",
            REFERENCE_CROP_MODES,
            1,
            focus,
            REFERENCE_TARGET_GAINS[
                focus_index
            ],
            seeds
        )

        focus_index += 1


def benchmark_power():
    for seed in BENCH_SEEDS:
        quick_print(
            "POWER SEED",
            seed
        )

        for mode in POWER_MODES:
            run_time = run_one(
                mode,
                1,
                3,
                POWER_TARGET_GAIN,
                seed
            )

            quick_print(
                MODE_NAMES[mode],
                run_time
            )


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "FARM BENCH SUITE START"
    )

    run_clean_probe()

    benchmark_crop_finalists()

    benchmark_crop_references()

    if RUN_POWER_BENCHMARK:
        quick_print(
            "POWER FINAL",
            "target-gain",
            POWER_TARGET_GAIN
        )

        benchmark_power()

    quick_print(
        "FARM BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "FARM BENCHMARKS COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
