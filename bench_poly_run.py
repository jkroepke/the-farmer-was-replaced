import main


BENCH_WORLD_SIZE = 32
BENCH_SPEEDUP = 64

HORIZON_NAMES = [
    "cold-short",
    "cold-medium",
    "sustained"
]

CARROT_GAINS = [
    100000,
    1000000,
    5000000
]

HAY_GAINS = [
    100000,
    1000000,
    5000000
]

WOOD_GAINS = [
    200000,
    2000000,
    10000000
]

BENCH_SEEDS = [
    1,
    2,
    3
]

PROFILE_NAMES = [
    "partial-megafarm-level-3",
    "max-megafarm"
]

MODE_NAMES = [
    "sync-selected",
    "current-one-max-stride",
    "current-one-max-chunks",
    "current-one-max-pairs",
    "current-two-sun-stride",
    "current-two-sun-chunks",
    "current-two-sun-pairs",
    "poly-one-max-stride",
    "poly-one-max-chunks",
    "poly-one-max-pairs",
    "poly-two-sun-stride",
    "poly-two-sun-chunks",
    "poly-two-sun-pairs"
]


def simulation_unlocks(profile):
    if profile == 1:
        return Unlocks

    unlocks = {}

    for unlock in Unlocks:
        unlocks[unlock] = -1

    unlocks[Unlocks.Megafarm] = 3

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
        Items.Power: 0,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_one(profile, mode, horizon, seed):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_HORIZON": horizon,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_CARROT_GAIN": CARROT_GAINS[horizon],
        "BENCH_HAY_GAIN": HAY_GAINS[horizon],
        "BENCH_WOOD_GAIN": WOOD_GAINS[horizon]
    }

    return simulate(
        "bench_poly",
        simulation_unlocks(profile),
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def screen_horizon(profile, horizon):
    times = []

    quick_print(
        "FARMX SCREEN START",
        PROFILE_NAMES[profile],
        HORIZON_NAMES[horizon]
    )

    for mode in range(len(MODE_NAMES)):
        run_time = run_one(
            profile,
            mode,
            horizon,
            1
        )

        times.append(run_time)

        quick_print(
            "FARMX SCREEN",
            PROFILE_NAMES[profile],
            HORIZON_NAMES[horizon],
            MODE_NAMES[mode],
            run_time
        )

    return times


def best_in_range(times, start_mode, end_mode):
    best_mode = start_mode
    best_time = times[start_mode]

    mode = start_mode + 1

    while mode <= end_mode:
        if times[mode] < best_time:
            best_time = times[mode]
            best_mode = mode

        mode += 1

    return best_mode


def benchmark_finalists(
    profile,
    current_mode,
    poly_mode
):
    modes = [
        0,
        current_mode,
        poly_mode
    ]

    totals = [0, 0, 0]
    minimums = [-1, -1, -1]
    maximums = [0, 0, 0]

    quick_print(
        "FARMX FINAL START",
        PROFILE_NAMES[profile],
        "current",
        MODE_NAMES[current_mode],
        "poly",
        MODE_NAMES[poly_mode]
    )

    for seed in BENCH_SEEDS:
        result_index = 0

        for mode in modes:
            run_time = run_one(
                profile,
                mode,
                2,
                seed
            )

            totals[result_index] += run_time

            if (
                minimums[result_index] < 0
                or run_time < minimums[result_index]
            ):
                minimums[result_index] = run_time

            if run_time > maximums[result_index]:
                maximums[result_index] = run_time

            quick_print(
                "FARMX FINAL",
                PROFILE_NAMES[profile],
                "seed",
                seed,
                MODE_NAMES[mode],
                run_time
            )

            result_index += 1

    count = len(BENCH_SEEDS)

    quick_print(
        "FARMX FINAL SUMMARY",
        PROFILE_NAMES[profile]
    )

    result_index = 0

    for mode in modes:
        quick_print(
            MODE_NAMES[mode],
            "avg",
            totals[result_index] / count,
            "min",
            minimums[result_index],
            "max",
            maximums[result_index]
        )

        result_index += 1


def benchmark_profile(profile):
    # Cold-short exposes clear/layout/spawn overhead.
    screen_horizon(
        profile,
        0
    )

    # Medium selects one current and one rerolling finalist.
    medium_times = screen_horizon(
        profile,
        1
    )

    current_mode = best_in_range(
        medium_times,
        1,
        6
    )
    poly_mode = best_in_range(
        medium_times,
        7,
        12
    )

    quick_print(
        "FARMX FINALISTS",
        PROFILE_NAMES[profile],
        "current",
        MODE_NAMES[current_mode],
        medium_times[current_mode],
        "poly",
        MODE_NAMES[poly_mode],
        medium_times[poly_mode]
    )

    benchmark_finalists(
        profile,
        current_mode,
        poly_mode
    )


def run_benchmarks():
    quick_print(
        "FARMX BENCH SUITE START"
    )

    for profile in range(len(PROFILE_NAMES)):
        benchmark_profile(profile)

    quick_print(
        "FARMX BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "FARMX BENCH COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
