import farm
import production
import unlocks
import utils


MODE_NAMES = [
    "current-dynamic-frontier",
    "agude-sticky-bounded",
    "msmith-static-bounded"
]


STATIC_ORDER = [
    Unlocks.Speed,
    Unlocks.Expand,
    Unlocks.Plant,
    Unlocks.Expand,
    Unlocks.Speed,
    Unlocks.Carrots,
    Unlocks.Expand,
    Unlocks.Speed,
    Unlocks.Watering,
    Unlocks.Trees,
    Unlocks.Grass,
    Unlocks.Trees,
    Unlocks.Carrots,
    Unlocks.Sunflowers,
    Unlocks.Expand,
    Unlocks.Grass,
    Unlocks.Speed,
    Unlocks.Fertilizer,
    Unlocks.Watering,
    Unlocks.Pumpkins,
    Unlocks.Polyculture,
    Unlocks.Speed,
    Unlocks.Carrots,
    Unlocks.Watering,
    Unlocks.Fertilizer,
    Unlocks.Trees,
    Unlocks.Pumpkins,
    Unlocks.Fertilizer,
    Unlocks.Grass,
    Unlocks.Trees,
    Unlocks.Watering,
    Unlocks.Carrots,
    Unlocks.Pumpkins,
    Unlocks.Expand,
    Unlocks.Cactus,
    Unlocks.Fertilizer,
    Unlocks.Expand,
    Unlocks.Carrots,
    Unlocks.Pumpkins,
    Unlocks.Expand,
    Unlocks.Mazes,
    Unlocks.Megafarm,
    Unlocks.Megafarm,
    Unlocks.Cactus,
    Unlocks.Mazes,
    Unlocks.Megafarm,
    Unlocks.Mazes,
    Unlocks.Dinosaurs,
    Unlocks.Cactus,
    Unlocks.Mazes,
    Unlocks.Dinosaurs,
    Unlocks.Hats,
    Unlocks.Polyculture,
    Unlocks.Polyculture,
    Unlocks.Grass,
    Unlocks.Trees,
    Unlocks.Carrots,
    Unlocks.Grass,
    Unlocks.Trees,
    Unlocks.Carrots,
    Unlocks.Grass,
    Unlocks.Trees,
    Unlocks.Carrots,
    Unlocks.Grass,
    Unlocks.Grass,
    Unlocks.Megafarm,
    Unlocks.Megafarm,
    Unlocks.Trees,
    Unlocks.Carrots,
    Unlocks.Pumpkins,
    Unlocks.Dinosaurs,
    Unlocks.Dinosaurs,
    Unlocks.Cactus,
    Unlocks.Mazes,
    Unlocks.Mazes,
    Unlocks.Leaderboard
]


def reset_runtime():
    # Fastest Reset simulations already start on a fresh one-tile farm.
    # Do not pay for or depend on an artificial clear() before progression.
    production.reset_state()
    farm.reset_state()


def after_unlock(
    previous_size
):
    if get_world_size() == previous_size:
        return

    production.reset_state()
    clear()
    farm.reset_state()


def run_one_action_for_target(
    target
):
    if target == None:
        return False

    focus = unlocks.focus_item(
        target
    )

    if focus == None:
        return False

    return production.run(
        focus
    )


def try_one_unlock(
    target
):
    previous_size = get_world_size()

    if not unlocks.try_unlock(
        target
    ):
        return False

    after_unlock(
        previous_size
    )

    return True


def run_dynamic():
    actions = 0
    unlocks_bought = 0

    while (
        num_unlocked(
            Unlocks.Leaderboard
        ) == 0
        and actions < BENCH_MAX_ACTIONS
    ):
        target = unlocks.next_target()

        if target == None:
            return [
                False,
                actions,
                unlocks_bought
            ]

        if try_one_unlock(
            target
        ):
            unlocks_bought += 1
            continue

        if not run_one_action_for_target(
            target
        ):
            return [
                False,
                actions,
                unlocks_bought
            ]

        actions += 1

        if try_one_unlock(
            target
        ):
            unlocks_bought += 1

    return [
        num_unlocked(
            Unlocks.Leaderboard
        ) > 0,
        actions,
        unlocks_bought
    ]


def run_sticky():
    actions = 0
    unlocks_bought = 0
    target = None

    while (
        num_unlocked(
            Unlocks.Leaderboard
        ) == 0
        and actions < BENCH_MAX_ACTIONS
    ):
        if target == None:
            target = unlocks.next_target()

            if target == None:
                return [
                    False,
                    actions,
                    unlocks_bought
                ]

        if try_one_unlock(
            target
        ):
            unlocks_bought += 1
            target = None
            continue

        if not run_one_action_for_target(
            target
        ):
            return [
                False,
                actions,
                unlocks_bought
            ]

        actions += 1

        # Agude-inspired invariant:
        # one bounded action, then re-read the same live target cost.
        if try_one_unlock(
            target
        ):
            unlocks_bought += 1
            target = None

    return [
        num_unlocked(
            Unlocks.Leaderboard
        ) > 0,
        actions,
        unlocks_bought
    ]


def run_static():
    actions = 0
    unlocks_bought = 0
    index = 0

    while (
        index < len(
            STATIC_ORDER
        )
        and num_unlocked(
            Unlocks.Leaderboard
        ) == 0
        and actions < BENCH_MAX_ACTIONS
    ):
        target = STATIC_ORDER[
            index
        ]

        cost = get_cost(
            target
        )

        if (
            cost == None
            or len(cost) == 0
        ):
            index += 1
            continue

        if try_one_unlock(
            target
        ):
            unlocks_bought += 1
            index += 1
            continue

        focus = unlocks.choose_focus_from_cost(
            get_cost(
                target
            )
        )

        if focus == None:
            return [
                False,
                actions,
                unlocks_bought
            ]

        if not production.run(
            focus
        ):
            return [
                False,
                actions,
                unlocks_bought
            ]

        actions += 1

        # Preserve the static unlock order, but resample live costs after
        # every bounded production action instead of carrying stale targets.
        if try_one_unlock(
            target
        ):
            unlocks_bought += 1
            index += 1

    return [
        num_unlocked(
            Unlocks.Leaderboard
        ) > 0,
        actions,
        unlocks_bought
    ]


def main():
    quick_print(
        "RESET WORKER START",
        MODE_NAMES[BENCH_MODE],
        "world",
        get_world_size(),
        "leaderboard-level",
        num_unlocked(
            Unlocks.Leaderboard
        )
    )

    reset_runtime()

    quick_print(
        "RESET WORKER READY",
        MODE_NAMES[BENCH_MODE]
    )

    start_ticks = get_tick_count()
    start_time = get_time()

    if BENCH_MODE == 0:
        result = run_dynamic()
    elif BENCH_MODE == 1:
        result = run_sticky()
    else:
        result = run_static()

    elapsed = (
        get_time()
        - start_time
    )
    ticks = (
        get_tick_count()
        - start_ticks
    )

    if result[0]:
        status = "PASS"
    else:
        status = "FAIL"

    quick_print(
        "RESET RESULT",
        MODE_NAMES[
            BENCH_MODE
        ],
        "elapsed",
        elapsed,
        "ticks",
        ticks,
        "actions",
        result[1],
        "unlocks",
        result[2],
        "leaderboard-level",
        num_unlocked(
            Unlocks.Leaderboard
        ),
        "world",
        get_world_size(),
        status
    )


if __name__ == "__main__":
    main()
