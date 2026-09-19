import main


BENCH_VERSION = "persist-v1"

BENCH_WORLD_SIZE = 32
BENCH_SPEEDUP = 64

FINAL_CARROT_GAIN = 5000000
FINAL_HAY_GAIN = 5000000
FINAL_WOOD_GAIN = 10000000

SCREEN_CARROT_GAIN = 1000000
SCREEN_HAY_GAIN = 1000000
SCREEN_WOOD_GAIN = 2000000

BENCH_SEEDS = [
    1,
    2,
    3
]

PROFILE_NAMES = [
    "partial-megafarm-level-3",
    "max-megafarm"
]

LAYOUT_NAMES = [
    "pure-crop",
    "one-row-dumb",
    "one-col-dumb",
    "two-col-dumb",
    "one-col-max"
]

ARCH_NAMES = [
    "main-stride",
    "main-chunks",
    "main-pairs",
    "scheduler-chunks"
]


def simulation_unlocks(
    profile
):
    if profile == 1:
        return Unlocks

    unlocks = {}

    for unlock in Unlocks:
        unlocks[
            unlock
        ] = -1

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
    profile,
    kind,
    layout,
    architecture,
    seed,
    carrot_gain,
    hay_gain,
    wood_gain
):
    globals = {
        "BENCH_KIND": kind,
        "BENCH_LAYOUT": layout,
        "BENCH_ARCH": architecture,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_CARROT_GAIN": carrot_gain,
        "BENCH_HAY_GAIN": hay_gain,
        "BENCH_WOOD_GAIN": wood_gain
    }

    return simulate(
        "bench_persist",
        simulation_unlocks(
            profile
        ),
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def screen_layout(
    profile,
    layout
):
    seed = 1
    best_arch = 0
    best_time = -1

    quick_print(
        "PERSIST ARCH SCREEN",
        PROFILE_NAMES[
            profile
        ],
        "layout",
        LAYOUT_NAMES[
            layout
        ]
    )

    for architecture in range(
        len(
            ARCH_NAMES
        )
    ):
        run_time = run_one(
            profile,
            1,
            layout,
            architecture,
            seed,
            SCREEN_CARROT_GAIN,
            SCREEN_HAY_GAIN,
            SCREEN_WOOD_GAIN
        )

        quick_print(
            LAYOUT_NAMES[
                layout
            ],
            ARCH_NAMES[
                architecture
            ],
            run_time
        )

        if (
            best_time < 0
            or run_time < best_time
        ):
            best_time = run_time
            best_arch = architecture

    quick_print(
        "PERSIST ARCH WINNER",
        PROFILE_NAMES[
            profile
        ],
        LAYOUT_NAMES[
            layout
        ],
        ARCH_NAMES[
            best_arch
        ],
        best_time
    )

    return best_arch


def benchmark_profile(
    profile,
    architectures
):
    mode_count = (
        len(
            LAYOUT_NAMES
        )
        + 1
    )

    totals = []
    minimums = []
    maximums = []

    for _ in range(
        mode_count
    ):
        totals.append(
            0
        )
        minimums.append(
            -1
        )
        maximums.append(
            0
        )

    quick_print(
        "PERSIST FINAL CASE",
        PROFILE_NAMES[
            profile
        ]
    )

    for seed in BENCH_SEEDS:
        quick_print(
            "SEED",
            seed
        )

        sync_time = run_one(
            profile,
            0,
            0,
            0,
            seed,
            FINAL_CARROT_GAIN,
            FINAL_HAY_GAIN,
            FINAL_WOOD_GAIN
        )

        totals[0] += sync_time

        if (
            minimums[0] < 0
            or sync_time < minimums[0]
        ):
            minimums[0] = sync_time

        if sync_time > maximums[0]:
            maximums[0] = sync_time

        quick_print(
            "sync-selected",
            sync_time
        )

        for layout in range(
            len(
                LAYOUT_NAMES
            )
        ):
            architecture = architectures[
                layout
            ]

            run_time = run_one(
                profile,
                1,
                layout,
                architecture,
                seed,
                FINAL_CARROT_GAIN,
                FINAL_HAY_GAIN,
                FINAL_WOOD_GAIN
            )

            result_index = (
                layout
                + 1
            )

            totals[
                result_index
            ] += run_time

            if (
                minimums[
                    result_index
                ] < 0
                or run_time
                < minimums[
                    result_index
                ]
            ):
                minimums[
                    result_index
                ] = run_time

            if (
                run_time
                > maximums[
                    result_index
                ]
            ):
                maximums[
                    result_index
                ] = run_time

            quick_print(
                LAYOUT_NAMES[
                    layout
                ],
                ARCH_NAMES[
                    architecture
                ],
                run_time
            )

    count = len(
        BENCH_SEEDS
    )

    quick_print(
        "PERSIST FINAL SUMMARY",
        PROFILE_NAMES[
            profile
        ]
    )

    quick_print(
        "sync-selected",
        "avg",
        totals[0] / count,
        "min",
        minimums[0],
        "max",
        maximums[0]
    )

    for layout in range(
        len(
            LAYOUT_NAMES
        )
    ):
        result_index = (
            layout
            + 1
        )
        architecture = architectures[
            layout
        ]

        quick_print(
            LAYOUT_NAMES[
                layout
            ],
            ARCH_NAMES[
                architecture
            ],
            "avg",
            totals[
                result_index
            ] / count,
            "min",
            minimums[
                result_index
            ],
            "max",
            maximums[
                result_index
            ]
        )


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "PERSIST BENCH SUITE START"
    )

    for profile in range(
        len(
            PROFILE_NAMES
        )
    ):
        architectures = []

        for layout in range(
            len(
                LAYOUT_NAMES
            )
        ):
            architectures.append(
                screen_layout(
                    profile,
                    layout
                )
            )

        benchmark_profile(
            profile,
            architectures
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
