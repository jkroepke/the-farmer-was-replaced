import utils


MODE_NAMES = [
    "utils-arithmetic",
    "delta-static",
    "direction-static",
    "dict-runtime",
    "list-runtime",
    "delta-known-current"
]


TARGETS = [
    (17, 3),
    (2, 29),
    (31, 16),
    (8, 8),
    (24, 27),
    (5, 19),
    (28, 1),
    (13, 30),
    (0, 12),
    (21, 21),
    (7, 2),
    (30, 25),
    (11, 17),
    (26, 10),
    (4, 31),
    (19, 6),
    (3, 23),
    (29, 14),
    (15, 0),
    (9, 28),
    (25, 5),
    (1, 18),
    (22, 30),
    (6, 11),
    (31, 31),
    (12, 4),
    (27, 20),
    (0, 27),
    (18, 13),
    (5, 5),
    (23, 24),
    (10, 16)
]


# Signed shortest wrapped delta for (target - current) % 32.
DELTA_32 = [
    0,
    1, 2, 3, 4, 5, 6, 7,
    8, 9, 10, 11, 12, 13, 14, 15,
    16,
    -15, -14, -13, -12, -11, -10, -9,
    -8, -7, -6, -5, -4, -3, -2, -1
]


STEP_DIR_32 = [
    None,
    East, East, East, East, East, East, East,
    East, East, East, East, East, East, East, East,
    East,
    West, West, West, West, West, West, West,
    West, West, West, West, West, West, West, West
]


STEP_COUNT_32 = [
    0,
    1, 2, 3, 4, 5, 6, 7,
    8, 9, 10, 11, 12, 13, 14, 15,
    16,
    15, 14, 13, 12, 11, 10, 9,
    8, 7, 6, 5, 4, 3, 2, 1
]


def build_lookup(
    mode
):
    if mode == 3:
        lookup = {}

        index = 0

        while index < 32:
            lookup[index] = (
                STEP_DIR_32[index],
                STEP_COUNT_32[index]
            )

            index += 1

        return lookup

    if mode == 4:
        lookup = []

        index = 0

        while index < 32:
            lookup.append(
                (
                    STEP_DIR_32[index],
                    STEP_COUNT_32[index]
                )
            )

            index += 1

        return lookup

    return None


def move_delta_axis(
    current,
    target,
    positive,
    negative
):
    delta = DELTA_32[
        (
            target - current
        ) % 32
    ]

    if delta > 0:
        for _ in range(
            delta
        ):
            move(
                positive
            )

    elif delta < 0:
        for _ in range(
            -delta
        ):
            move(
                negative
            )


def move_delta(
    target_x,
    target_y
):
    move_delta_axis(
        get_pos_x(),
        target_x,
        East,
        West
    )

    move_delta_axis(
        get_pos_y(),
        target_y,
        North,
        South
    )


def move_direction_axis(
    current,
    target,
    positive,
    negative
):
    index = (
        target - current
    ) % 32

    direction = STEP_DIR_32[
        index
    ]

    count = STEP_COUNT_32[
        index
    ]

    if direction == East:
        direction = positive

    elif direction == West:
        direction = negative

    else:
        return

    for _ in range(
        count
    ):
        move(
            direction
        )


def move_direction(
    target_x,
    target_y
):
    move_direction_axis(
        get_pos_x(),
        target_x,
        East,
        West
    )

    move_direction_axis(
        get_pos_y(),
        target_y,
        North,
        South
    )


def move_lookup_axis(
    lookup,
    current,
    target,
    positive,
    negative
):
    entry = lookup[
        (
            target - current
        ) % 32
    ]

    direction = entry[0]
    count = entry[1]

    if direction == East:
        direction = positive

    elif direction == West:
        direction = negative

    else:
        return

    for _ in range(
        count
    ):
        move(
            direction
        )


def move_lookup(
    lookup,
    target_x,
    target_y
):
    move_lookup_axis(
        lookup,
        get_pos_x(),
        target_x,
        East,
        West
    )

    move_lookup_axis(
        lookup,
        get_pos_y(),
        target_y,
        North,
        South
    )


def move_known(
    current_x,
    current_y,
    target_x,
    target_y
):
    move_delta_axis(
        current_x,
        target_x,
        East,
        West
    )

    move_delta_axis(
        current_y,
        target_y,
        North,
        South
    )


def run_route(
    mode,
    lookup,
    count
):
    target_index = 0

    if mode == 5:
        current_x = get_pos_x()
        current_y = get_pos_y()

        iteration = 0

        while iteration < count:
            target = TARGETS[
                target_index
            ]

            move_known(
                current_x,
                current_y,
                target[0],
                target[1]
            )

            current_x = target[0]
            current_y = target[1]

            target_index += 1

            if target_index >= len(
                TARGETS
            ):
                target_index = 0

            iteration += 1

        return

    iteration = 0

    while iteration < count:
        target = TARGETS[
            target_index
        ]

        if mode == 0:
            utils.move_to(
                target[0],
                target[1]
            )

        elif mode == 1:
            move_delta(
                target[0],
                target[1]
            )

        elif mode == 2:
            move_direction(
                target[0],
                target[1]
            )

        else:
            move_lookup(
                lookup,
                target[0],
                target[1]
            )

        target_index += 1

        if target_index >= len(
            TARGETS
        ):
            target_index = 0

        iteration += 1


def expected_target(
    count
):
    index = (
        count - 1
    ) % len(
        TARGETS
    )

    return TARGETS[
        index
    ]


def main():
    set_world_size(
        BENCH_WORLD_SIZE
    )

    clear()

    lookup = None
    setup_ticks = 0

    if BENCH_WARM:
        setup_start = get_tick_count()

        lookup = build_lookup(
            BENCH_MODE
        )

        setup_ticks = (
            get_tick_count()
            - setup_start
        )

        run_start = get_tick_count()

        run_route(
            BENCH_MODE,
            lookup,
            BENCH_COUNT
        )

        run_ticks = (
            get_tick_count()
            - run_start
        )

        total_ticks = run_ticks

    else:
        total_start = get_tick_count()
        setup_start = total_start

        lookup = build_lookup(
            BENCH_MODE
        )

        setup_ticks = (
            get_tick_count()
            - setup_start
        )

        run_start = get_tick_count()

        run_route(
            BENCH_MODE,
            lookup,
            BENCH_COUNT
        )

        run_ticks = (
            get_tick_count()
            - run_start
        )

        total_ticks = (
            get_tick_count()
            - total_start
        )

    target = expected_target(
        BENCH_COUNT
    )

    status = "FAIL"

    if (
        get_pos_x() == target[0]
        and get_pos_y() == target[1]
    ):
        status = "PASS"

    quick_print(
        "MOVE RESULT",
        MODE_NAMES[BENCH_MODE],
        "warm",
        BENCH_WARM,
        "count",
        BENCH_COUNT,
        "setup ticks",
        setup_ticks,
        "run ticks",
        run_ticks,
        "total ticks",
        total_ticks,
        status
    )


main()
