import main


BENCH_VERSION = "dinosaur-v4"

# Primary Dinosaur benchmark:
#
# - exact Leaderboards.Dinosaur starting items
# - 32x32 farm
# - speedup 10000
# - many route/shortcut variants
# - fixed-tail diagnostic targets plus the exact board-1 leaderboard target
#
# IMPORTANT: simulate() returns elapsed time, not the child script's validity.
# Always correlate summary rows with "DINOSAUR BENCH VALID" / "INVALID" lines.
# A fast INVALID run must never be treated as a winner.
#
# The primary algorithm matrix uses parallel Soil preparation so every
# algorithm sees the same permanently empty field. A separate setup sweep
# measures whether that preparation is actually worth its startup cost.


BENCH_WORLD_SIZE = 32

BENCH_TARGET_PERCENTS = [
    25,
    50,
    75,
    95,
    100
]

BENCH_SEEDS = [
    1,
    2,
    3
]

BENCH_SPEEDUP = 10000
BENCH_VERBOSE = False
BENCH_CYCLES = 1
BENCH_MAX_MOVES = 2000000
BENCH_MAX_CYCLES = 64

# Maxed Unlocks.Dinosaurs yield multiplier. The exact leaderboard target
# confirms it for a board-1 tail:
#
# 1023 * 1023 * 32 = 33,488,928
DINO_YIELD_MULTIPLIER = 32
LEADERBOARD_BONES = 33488928

# Main comparisons use parallel harvest + Soil conversion.
PRIMARY_SETUP_MODE = 4

SETUP_NAMES = [
    "none",
    "clear",
    "serial-soil",
    "parallel-harvest",
    "parallel-soil",
    "source-parallel-soil",
    "flekay-line-soil",
    "flekay-dual-soil"
]

MODE_NAMES = [
    "hamiltonian-skyscraper",
    "skyscraper-shortcuts-annealed50",
    "skyscraper-shortcuts-hard25",
    "skyscraper-shortcuts-hard50",
    "skysdottir-hilbert-reference",
    "skyscraper-fastlane-annealed50",
    "heartbeat-hamiltonian",
    "heartbeat-shortcuts-annealed50",
    "heartbeat-fastlane-annealed50",
    "hilbert-hamiltonian",
    "reddit-coil-strike-safe33",
    "reddit-coil-strike-source50",
    "reddit-coil-strike-safe66",
    "skyscraper-fastlane-annealed25",
    "heartbeat-fastlane-annealed25",
    "skyscraper-fastlane-hard25",
    "heartbeat-fastlane-hard25",
    "heartbeat-shortcuts-hard50",
    "skyscraper-fastlane-hard50",
    "heartbeat-fastlane-hard50",
    "flekay-axis-greedy",
    "flekay-parity-greedy"
]

BENCH_MODES = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19
]

# Cleanup/preparation uncertainty is benchmarked separately. Use one simple
# path, the skysdottir reference, and the Reddit coil/strike route so setup
# behavior is not accidentally coupled to one route family.
SETUP_SWEEP_MODES = [
    0,
    4,
    11
]

SETUP_SWEEP_SETUPS = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7
]

SETUP_SWEEP_TARGET_PERCENT = 100

# Flekay's Dino README contains historical phase thresholds around
# 18, 34, and 50 cells on its 100-cell-era algorithms. Re-test the
# reusable early routing policies as occupancy percentages on 32x32.
FLEKAY_DIAGNOSTIC_MODES = [
    20,
    21
]

FLEKAY_DIAGNOSTIC_TARGET_PERCENTS = [
    10,
    18,
    25,
    34,
    50
]

# The real leaderboard checks total Bones, not one tail. Compare repeated
# partial harvests against one near-full harvest until the exact target is met.
LEADERBOARD_SWEEP_MODES = [
    0,
    4,
    11
]

LEADERBOARD_SWEEP_TARGET_PERCENTS = [
    25,
    33,
    50,
    66,
    75,
    95,
    100
]


def target_tail_length(
    target_percent
):
    board = (
        BENCH_WORLD_SIZE
        * BENCH_WORLD_SIZE
    )

    target = (
        board
        * target_percent
        // 100
    )

    if target < 2:
        target = 2

    if target >= board:
        target = board - 1

    return target


def expected_bones(
    target_percent
):
    tail = target_tail_length(
        target_percent
    )

    return (
        tail
        * tail
        * DINO_YIELD_MULTIPLIER
    )


def simulation_items():
    # Exact Leaderboards.Dinosaur equivalent simulation state from the
    # current Wiki: everything unlocked, 1e9 Cactus, 1e9 Power.
    return {
        Items.Cactus: 1000000000,
        Items.Power: 1000000000
    }


def run_one(
    mode,
    setup_mode,
    target_percent,
    seed,
    bone_target=0
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_WORLD_SIZE": BENCH_WORLD_SIZE,
        "BENCH_TARGET_PERCENT": target_percent,
        "BENCH_VERBOSE": BENCH_VERBOSE,
        "BENCH_CYCLES": BENCH_CYCLES,
        "BENCH_SETUP_MODE": setup_mode,
        "BENCH_MAX_MOVES": BENCH_MAX_MOVES,
        "BENCH_BONE_TARGET": bone_target,
        "BENCH_MAX_CYCLES": BENCH_MAX_CYCLES
    }

    return simulate(
        "bench_dinosaur",
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def print_result(
    prefix,
    mode,
    setup_mode,
    target_percent,
    seed,
    elapsed
):
    bones = expected_bones(
        target_percent
    )

    bones_per_second = 0

    if elapsed > 0:
        bones_per_second = (
            bones
            / elapsed
        )

    quick_print(
        prefix,
        MODE_NAMES[mode],
        "setup",
        SETUP_NAMES[setup_mode],
        "target",
        target_percent,
        "tail",
        target_tail_length(
            target_percent
        ),
        "seed",
        seed,
        "elapsed",
        elapsed,
        "bones",
        bones,
        "bones/s",
        bones_per_second
    )


def run_algorithm_matrix():
    quick_print(
        "DINOSAUR ALGORITHM MATRIX START",
        "modes",
        len(BENCH_MODES),
        "targets",
        len(BENCH_TARGET_PERCENTS),
        "seeds",
        len(BENCH_SEEDS),
        "setup",
        SETUP_NAMES[
            PRIMARY_SETUP_MODE
        ]
    )

    for target_percent in BENCH_TARGET_PERCENTS:
        totals = []

        for _ in BENCH_MODES:
            totals.append(
                0
            )

        for seed in BENCH_SEEDS:
            mode_index = 0

            for mode in BENCH_MODES:
                elapsed = run_one(
                    mode,
                    PRIMARY_SETUP_MODE,
                    target_percent,
                    seed
                )

                totals[
                    mode_index
                ] += elapsed

                print_result(
                    "DINOSAUR RESULT",
                    mode,
                    PRIMARY_SETUP_MODE,
                    target_percent,
                    seed,
                    elapsed
                )

                mode_index += 1

        quick_print(
            "DINOSAUR SUMMARY RAW",
            "target",
            target_percent,
            "tail",
            target_tail_length(
                target_percent
            ),
            "setup",
            SETUP_NAMES[
                PRIMARY_SETUP_MODE
            ]
        )

        mode_index = 0

        for mode in BENCH_MODES:
            average = (
                totals[
                    mode_index
                ]
                / len(BENCH_SEEDS)
            )

            bones = expected_bones(
                target_percent
            )

            bones_per_second = 0

            if average > 0:
                bones_per_second = (
                    bones
                    / average
                )

            quick_print(
                MODE_NAMES[mode],
                "avg",
                average,
                "bones",
                bones,
                "bones/s",
                bones_per_second
            )

            mode_index += 1

    quick_print(
        "DINOSAUR ALGORITHM MATRIX DONE"
    )


def run_setup_sweep():
    quick_print(
        "DINOSAUR SETUP SWEEP START",
        "target",
        SETUP_SWEEP_TARGET_PERCENT
    )

    for mode in SETUP_SWEEP_MODES:
        quick_print(
            "DINOSAUR SETUP MODE",
            MODE_NAMES[mode]
        )

        totals = []

        for _ in SETUP_SWEEP_SETUPS:
            totals.append(
                0
            )

        for seed in BENCH_SEEDS:
            setup_index = 0

            for setup_mode in SETUP_SWEEP_SETUPS:
                elapsed = run_one(
                    mode,
                    setup_mode,
                    SETUP_SWEEP_TARGET_PERCENT,
                    seed
                )

                totals[
                    setup_index
                ] += elapsed

                print_result(
                    "DINOSAUR SETUP RESULT",
                    mode,
                    setup_mode,
                    SETUP_SWEEP_TARGET_PERCENT,
                    seed,
                    elapsed
                )

                setup_index += 1

        quick_print(
            "DINOSAUR SETUP SUMMARY RAW",
            MODE_NAMES[mode]
        )

        setup_index = 0

        for setup_mode in SETUP_SWEEP_SETUPS:
            average = (
                totals[
                    setup_index
                ]
                / len(BENCH_SEEDS)
            )

            quick_print(
                SETUP_NAMES[
                    setup_mode
                ],
                "avg",
                average
            )

            setup_index += 1

    quick_print(
        "DINOSAUR SETUP SWEEP DONE"
    )


def run_flekay_diagnostics():
    quick_print(
        "DINOSAUR FLEKAY DIAGNOSTICS START"
    )

    for target_percent in FLEKAY_DIAGNOSTIC_TARGET_PERCENTS:
        totals = []

        for _ in FLEKAY_DIAGNOSTIC_MODES:
            totals.append(
                0
            )

        for seed in BENCH_SEEDS:
            mode_index = 0

            for mode in FLEKAY_DIAGNOSTIC_MODES:
                elapsed = run_one(
                    mode,
                    PRIMARY_SETUP_MODE,
                    target_percent,
                    seed
                )

                totals[
                    mode_index
                ] += elapsed

                print_result(
                    "DINOSAUR FLEKAY RESULT",
                    mode,
                    PRIMARY_SETUP_MODE,
                    target_percent,
                    seed,
                    elapsed
                )

                mode_index += 1

        quick_print(
            "DINOSAUR FLEKAY SUMMARY RAW",
            "target",
            target_percent
        )

        mode_index = 0

        for mode in FLEKAY_DIAGNOSTIC_MODES:
            average = (
                totals[
                    mode_index
                ]
                / len(BENCH_SEEDS)
            )

            quick_print(
                MODE_NAMES[mode],
                "avg",
                average
            )

            mode_index += 1

    quick_print(
        "DINOSAUR FLEKAY DIAGNOSTICS DONE"
    )


def run_leaderboard_harvest_sweep():
    quick_print(
        "DINOSAUR LEADERBOARD HARVEST SWEEP START",
        "bone_target",
        LEADERBOARD_BONES
    )

    for target_percent in LEADERBOARD_SWEEP_TARGET_PERCENTS:
        totals = []

        for _ in LEADERBOARD_SWEEP_MODES:
            totals.append(
                0
            )

        for seed in BENCH_SEEDS:
            mode_index = 0

            for mode in LEADERBOARD_SWEEP_MODES:
                elapsed = run_one(
                    mode,
                    PRIMARY_SETUP_MODE,
                    target_percent,
                    seed,
                    LEADERBOARD_BONES
                )

                totals[
                    mode_index
                ] += elapsed

                quick_print(
                    "DINOSAUR LEADERBOARD RESULT",
                    MODE_NAMES[mode],
                    "harvest_target",
                    target_percent,
                    "seed",
                    seed,
                    "elapsed",
                    elapsed
                )

                mode_index += 1

        quick_print(
            "DINOSAUR LEADERBOARD SUMMARY RAW",
            "harvest_target",
            target_percent
        )

        mode_index = 0

        for mode in LEADERBOARD_SWEEP_MODES:
            average = (
                totals[
                    mode_index
                ]
                / len(BENCH_SEEDS)
            )

            quick_print(
                MODE_NAMES[mode],
                "avg",
                average
            )

            mode_index += 1

    quick_print(
        "DINOSAUR LEADERBOARD HARVEST SWEEP DONE"
    )


def run_benchmarks():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )

    quick_print(
        "DINOSAUR LEADERBOARD TARGET",
        LEADERBOARD_BONES,
        "tail",
        1023,
        "yield-multiplier",
        DINO_YIELD_MULTIPLIER,
        "speedup",
        BENCH_SPEEDUP
    )

    run_algorithm_matrix()
    run_setup_sweep()
    run_flekay_diagnostics()
    run_leaderboard_harvest_sweep()

    quick_print(
        "DINOSAUR BENCHMARKS COMPLETE"
    )


if __name__ == "__main__":
    run_benchmarks()

    quick_print(
        "STARTING MAIN LOOP"
    )

    main.main()
