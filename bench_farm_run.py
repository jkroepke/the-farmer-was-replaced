import main


# Normal-farm benchmark suite.
#
# Crop cases use fixed inventory gains, so simulate() runtime is directly
# comparable within one focus/profile. bench_farm.py also prints actual gain,
# rate, max_drones(), and Power delta for each simulation.
#
# Targets are 1% of the current 32-drone resource leaderboard goals:
#
# Hay     2,000,000,000 -> 20,000,000
# Wood   10,000,000,000 -> 100,000,000
# Carrot  2,000,000,000 -> 20,000,000
#
# Power uses the full 100,000 leaderboard-sized gain because the dedicated
# Power references are fast enough and startup effects should be amortized.


BENCH_WORLD_SIZE = 32

BENCH_FOCUSES = [
    0,
    1,
    2
]

BENCH_TARGET_GAINS = [
    20000000,
    100000000,
    20000000
]

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 64

# profile 0 deliberately represents max_drones() < world_size.
# Megafarm level 3 is used; bench_farm.py prints the actual max_drones()
# so the result remains unambiguous if the game's level mapping changes.
#
# profile 1 uses fully upgraded Unlocks and should be 32 drones on 32x32.
PROFILE_NAMES = [
    "partial-megafarm-level-3",
    "max-megafarm"
]

CROP_MODES_PARTIAL = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7
]

CROP_MODES_MAX = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8
]

POWER_MODES = [
    20,
    21,
    22,
    23
]

POWER_TARGET_GAIN = 100000

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
    # Large producer-input pools keep the benchmark focused on farming
    # throughput instead of prerequisite acquisition.
    #
    # Power is intentionally small. Crop cases therefore reveal whether
    # their integrated Sunflower layout can sustain the speed boost.
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 1000000000,
        Items.Cactus: 1000000000,
        Items.Bone: 1000000000,
        Items.Gold: 1000000000,
        Items.Power: 1000,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


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


def modes_for_profile(profile):
    if profile == 0:
        return CROP_MODES_PARTIAL

    return CROP_MODES_MAX


def benchmark_crop_case(
    profile,
    focus,
    target_gain
):
    modes = modes_for_profile(
        profile
    )

    totals = []
    minimums = []
    maximums = []

    for _ in modes:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    quick_print(
        "FARM CASE",
        PROFILE_NAMES[profile],
        "focus",
        focus,
        "target-gain",
        target_gain
    )

    for seed in BENCH_SEEDS:
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
        "FARM SUMMARY",
        PROFILE_NAMES[profile],
        "focus",
        focus
    )

    mode_index = 0
    seed_count = len(
        BENCH_SEEDS
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


def benchmark_power_case():
    profile = 1

    totals = []
    minimums = []
    maximums = []

    for _ in POWER_MODES:
        totals.append(0)
        minimums.append(-1)
        maximums.append(0)

    quick_print(
        "POWER CASE",
        PROFILE_NAMES[profile],
        "target-gain",
        POWER_TARGET_GAIN
    )

    for seed in BENCH_SEEDS:
        quick_print(
            "SEED",
            seed
        )

        mode_index = 0

        for mode in POWER_MODES:
            run_time = run_one(
                mode,
                profile,
                3,
                POWER_TARGET_GAIN,
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
        "POWER SUMMARY"
    )

    mode_index = 0
    seed_count = len(
        BENCH_SEEDS
    )

    for mode in POWER_MODES:
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
        "FARM BENCH SUITE START"
    )

    for profile in range(
        len(PROFILE_NAMES)
    ):
        focus_index = 0

        for focus in BENCH_FOCUSES:
            benchmark_crop_case(
                profile,
                focus,
                BENCH_TARGET_GAINS[
                    focus_index
                ]
            )

            focus_index += 1

    benchmark_power_case()

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
