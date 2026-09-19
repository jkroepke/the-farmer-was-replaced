import main


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

MODE_NAMES = [
    "sync-respawn",
    "persistent-workers"
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
        Items.Power: 0,
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
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_CARROT_GAIN": BENCH_CARROT_GAIN,
        "BENCH_HAY_GAIN": BENCH_HAY_GAIN,
        "BENCH_WOOD_GAIN": BENCH_WOOD_GAIN
    }

    return simulate(
        "bench_persist",
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def run_benchmarks():
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
        "PERSIST BENCH SUITE START"
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
                seed
            )

            totals[mode] += run_time

            if (
                minimums[mode] < 0
                or run_time < minimums[mode]
            ):
                minimums[mode] = run_time

            if (
                run_time
                > maximums[mode]
            ):
                maximums[mode] = run_time

            quick_print(
                MODE_NAMES[mode],
                run_time
            )

    quick_print(
        "PERSIST BENCH SUMMARY"
    )

    count = len(
        BENCH_SEEDS
    )

    for mode in range(
        len(MODE_NAMES)
    ):
        quick_print(
            MODE_NAMES[mode],
            "avg",
            totals[mode] / count,
            "min",
            minimums[mode],
            "max",
            maximums[mode]
        )

    quick_print(
        "PERSIST BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "PERSIST BENCH COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
