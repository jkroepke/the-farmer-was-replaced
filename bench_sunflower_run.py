BENCH_VERSION = "sunflower-v1"
BENCH_SPEEDUP = 10000
BENCH_TARGET_POWER = 100000

BENCH_SEEDS = [
    1,
    2,
    3
]

MODE_NAMES = [
    "tier-tree-no-care",
    "tier-tree-water",
    "tier-tree-water-fertilizer",
    "equal7-tree-water",
    "equal7-tree-water-fertilizer",
    "dumb-tree-water",
    "dumb-tree-water-fertilizer",
    "tier-linear-water",
    "scan-tree-leave7",
    "scan-tree-counted",
    "scan-linear-counted",
    "dumb-tree-no-care",
    "equal7-tree-no-care",
    "tier-linear-no-care"
]

# Leaderboard-focused modes. The actual resource leaderboard is expected to
# provide planting input, not Water/Fertilizer. Water/Fertilizer modes stay in
# sunflower_lb.py as explicit reference ablations but are not part of the first
# leaderboard-equivalent screen.
SCREEN_MODES = [
    0,
    12,
    11,
    13,
    8,
    9,
    10
]


def simulation_items():
    # Current community leaderboard simulations use Carrot as the Sunflower
    # planting input. Keep this intentionally minimal so care modes cannot hide
    # behind resources that may not exist in the real leaderboard start state.
    return {
        Items.Carrot: 1000000000
    }


def run_one(
    mode,
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_TARGET_POWER": BENCH_TARGET_POWER
    }

    return simulate(
        "bench_sunflower",
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

    quick_print(
        "SUNFLOWER BENCH START",
        "world",
        32,
        "target",
        BENCH_TARGET_POWER,
        "modes",
        len(
            SCREEN_MODES
        ),
        "seeds",
        len(
            BENCH_SEEDS
        )
    )

    totals = []
    minimums = []
    maximums = []

    for _ in MODE_NAMES:
        totals.append(
            0
        )
        minimums.append(
            -1
        )
        maximums.append(
            0
        )

    for seed in BENCH_SEEDS:
        quick_print(
            "SUNFLOWER SEED",
            seed
        )

        for mode in SCREEN_MODES:
            quick_print(
                "RUN",
                MODE_NAMES[
                    mode
                ]
            )

            run_time = run_one(
                mode,
                seed
            )

            totals[
                mode
            ] += run_time

            if (
                minimums[
                    mode
                ] < 0
                or run_time
                < minimums[
                    mode
                ]
            ):
                minimums[
                    mode
                ] = run_time

            if run_time > maximums[
                mode
            ]:
                maximums[
                    mode
                ] = run_time

            quick_print(
                MODE_NAMES[
                    mode
                ],
                run_time
            )

    quick_print(
        "SUNFLOWER BENCH SUMMARY"
    )

    count = len(
        BENCH_SEEDS
    )

    for mode in SCREEN_MODES:
        quick_print(
            MODE_NAMES[
                mode
            ],
            "avg",
            totals[
                mode
            ] / count,
            "min",
            minimums[
                mode
            ],
            "max",
            maximums[
                mode
            ]
        )

    quick_print(
        "SUNFLOWER BENCH DONE"
    )


main()
