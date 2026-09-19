import main


BENCH_VERSION = "transition-v1"

BENCH_WORLD_SIZE = 32
BENCH_SPEEDUP = 64

BENCH_CARROT_GAIN = 5000000
BENCH_HAY_GAIN = 5000000
BENCH_WOOD_GAIN = 10000000

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
    "legacy-l",
    "adaptive-production"
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
        Items.Power: 0,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_one(
    mode,
    profile,
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_CARROT_GAIN": BENCH_CARROT_GAIN,
        "BENCH_HAY_GAIN": BENCH_HAY_GAIN,
        "BENCH_WOOD_GAIN": BENCH_WOOD_GAIN
    }

    return simulate(
        "bench_transition",
        simulation_unlocks(
            profile
        ),
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_profile(profile):
    totals = [
        0,
        0
    ]

    minimums = [
        -1,
        -1
    ]

    maximums = [
        0,
        0
    ]

    quick_print(
        "TRANSITION CASE",
        PROFILE_NAMES[profile]
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
                profile,
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

    quick_print(
        "TRANSITION SUMMARY",
        PROFILE_NAMES[profile]
    )

    seed_count = len(
        BENCH_SEEDS
    )

    for mode in range(
        len(MODE_NAMES)
    ):
        quick_print(
            MODE_NAMES[mode],
            "avg",
            totals[mode] / seed_count,
            "min",
            minimums[mode],
            "max",
            maximums[mode]
        )


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "TRANSITION BENCH SUITE START"
    )

    for profile in range(
        len(PROFILE_NAMES)
    ):
        benchmark_profile(
            profile
        )

    quick_print(
        "TRANSITION BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "TRANSITION BENCHMARKS COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
