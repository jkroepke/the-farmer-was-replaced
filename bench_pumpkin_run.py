import main


BENCH_VERSION = "pumpkin-v1"

BENCH_VERSION = "pumpkin-v3-spawn-locality"
BENCH_WORLD_SIZE = 32
BENCH_SPEEDUP = 64

BENCH_SEEDS = [
    1,
    2,
    3
]

MODE_NAMES = [
    "current-production",
    "legacy-patch-wait",
    "sparse-1x32",
    "sparse-2x16",
    "sparse-4x8",
    "sparse-8x4",
    "sparse-16x2",
    "sparse-1x32-tail",
    "sparse-4x8-tail",
    "sparse-8x4-tail",
    "tree-1x32-tail",
    "tree-4x8-tail",
    "tree-8x4-tail",
    "persistent-1x32-tail",
    "persistent-4x8-tail",
    "persistent-8x4-tail",
    "persistent-tree-4x8-tail",
    "persistent-tree-8x4-tail",
    "ring-reuse",
    "persistent-ring",
    "persistent-tree-ring",
    "persistent-placed-ring",
    "persistent-spatial-tree-ring"
]

PRIMARY_MODES = [
    0,
    19,
    20,
    21,
    22
]

CONTROL_MODES = [
    1
]

AMORTIZED_MODES = [
    0,
    18,
    19,
    20,
    21,
    22
]

AMORTIZED_CYCLES = 3

# Verified from the supplied in-game current-production runs for the fully
# upgraded 32x32 simulation: every valid full-map harvest yielded 3,145,728.
EXPECTED_CYCLE_GAIN = 3145728


def simulation_items():
    return {
        Items.Hay: 1000000000,
        Items.Wood: 1000000000,
        Items.Carrot: 1000000000,
        Items.Pumpkin: 0,
        Items.Cactus: 1000000000,
        Items.Bone: 1000000000,
        Items.Gold: 1000000000,
        Items.Power: 1000000000,
        Items.Water: 1000000000,
        Items.Fertilizer: 1000000000,
        Items.Weird_Substance: 1000000000
    }


def run_one(
    mode,
    seed,
    cycles
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_CYCLES": cycles,
        "BENCH_EXPECTED_CYCLE_GAIN": EXPECTED_CYCLE_GAIN
    }

    return simulate(
        "bench_pumpkin",
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def benchmark_modes(
    label,
    modes,
    seeds,
    cycles
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
        BENCH_WORLD_SIZE,
        "drones",
        max_drones(),
        "cycles",
        cycles
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
                MODE_NAMES[
                    mode
                ]
            )

            run_time = run_one(
                mode,
                seed,
                cycles
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
                MODE_NAMES[
                    mode
                ],
                run_time
            )

            mode_index += 1

    quick_print(
        label,
        "SUMMARY"
    )

    seed_count = len(
        seeds
    )

    mode_index = 0

    for mode in modes:
        quick_print(
            MODE_NAMES[
                mode
            ],
            "avg",
            totals[
                mode_index
            ] / seed_count,
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
        "PUMPKIN BENCH SUITE START"
    )

    benchmark_modes(
        "PUMPKIN PRIMARY",
        PRIMARY_MODES,
        BENCH_SEEDS,
        1
    )

    benchmark_modes(
        "PUMPKIN CONTROL",
        CONTROL_MODES,
        [1],
        1
    )

    benchmark_modes(
        "PUMPKIN AMORTIZED",
        AMORTIZED_MODES,
        BENCH_SEEDS,
        AMORTIZED_CYCLES
    )

    quick_print(
        "PUMPKIN BENCH SUITE DONE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "PUMPKIN BENCH COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
