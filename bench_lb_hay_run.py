BENCH_VERSION = "lbhay-v2"
BENCH_SPEEDUP = 10000

SCREEN_GAIN = 50000000
FINAL_GAIN = 2000000000

BENCH_SEEDS = [
    1,
    2,
    3
]

MODE_NAMES = [
    "grass-lean",
    "grass-water25",
    "grass-water50",
    "grass-water75",
    "grass-fert",
    "grass-water-fert",
    "grass-safe"
]


def simulation_items():
    # Measured real Hay leaderboard start inventory (lbprobe-v4).
    return {
        Items.Hay: 0,
        Items.Wood: 0,
        Items.Carrot: 0,
        Items.Pumpkin: 0,
        Items.Cactus: 0,
        Items.Bone: 0,
        Items.Weird_Substance: 0,
        Items.Gold: 0,
        Items.Water: 0,
        Items.Fertilizer: 0,
        Items.Power: 1000000000,
        Items.Piggy: 0
    }


def run_one(
    mode,
    target_gain,
    seed
):
    globals = {
        "BENCH_MODE": mode,
        "BENCH_TARGET_GAIN": target_gain
    }

    return simulate(
        "bench_lb_hay",
        Unlocks,
        simulation_items(),
        globals,
        seed,
        BENCH_SPEEDUP
    )


def best_three(times):
    selected = []

    while len(selected) < 3:
        best_mode = -1
        best_time = -1

        for mode in range(
            len(MODE_NAMES)
        ):
            if mode in selected:
                continue

            if (
                best_mode < 0
                or times[mode] < best_time
            ):
                best_mode = mode
                best_time = times[mode]

        selected.append(
            best_mode
        )

    return selected


def main():
    quick_print(
        "BENCHMARK VERSION",
        BENCH_VERSION
    )
    quick_print(
        "LBHAY START PROFILE",
        "measured-hay-lb"
    )

    times = []

    for mode in range(
        len(MODE_NAMES)
    ):
        run_time = run_one(
            mode,
            SCREEN_GAIN,
            1
        )
        times.append(
            run_time
        )

        quick_print(
            "LBHAY SCREEN",
            MODE_NAMES[mode],
            run_time
        )

    finalists = best_three(
        times
    )

    quick_print(
        "LBHAY FINALISTS",
        MODE_NAMES[finalists[0]],
        times[finalists[0]],
        MODE_NAMES[finalists[1]],
        times[finalists[1]],
        MODE_NAMES[finalists[2]],
        times[finalists[2]]
    )

    totals = [0, 0, 0]
    minimums = [-1, -1, -1]
    maximums = [0, 0, 0]

    for seed in BENCH_SEEDS:
        index = 0

        while index < len(
            finalists
        ):
            mode = finalists[index]
            run_time = run_one(
                mode,
                FINAL_GAIN,
                seed
            )

            totals[index] += run_time

            if (
                minimums[index] < 0
                or run_time < minimums[index]
            ):
                minimums[index] = run_time

            if run_time > maximums[index]:
                maximums[index] = run_time

            quick_print(
                "LBHAY FINAL",
                "seed",
                seed,
                MODE_NAMES[mode],
                run_time
            )

            index += 1

    quick_print(
        "LBHAY FINAL SUMMARY",
        "target",
        FINAL_GAIN
    )

    index = 0
    count = len(BENCH_SEEDS)

    while index < len(
        finalists
    ):
        mode = finalists[index]

        quick_print(
            MODE_NAMES[mode],
            "avg",
            totals[index] / count,
            "min",
            minimums[index],
            "max",
            maximums[index]
        )

        index += 1


main()
