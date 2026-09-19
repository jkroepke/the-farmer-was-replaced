# Dinosaur benchmark implementations.
#
# Run through bench_dinosaur_run.py.
#
# Modes:
# 0 = current Hamiltonian/skyscraper baseline
# 1 = skyscraper + safe shortcuts + source-like annealing, stop at 50%
# 2 = skyscraper + safe shortcuts, hard stop at 25%
# 3 = skyscraper + safe shortcuts, hard stop at 50%
# 4 = skysdottir/tfwr behavioral reference:
#     Hilbert cycle + source-like safe shortcutting/annealing
#
# Shortcut logic is based on:
# https://github.com/skysdottir/tfwr
#
# The path geometry intentionally matches the current production
# dinosaur.py Hamiltonian/skyscraper cycle so this benchmark isolates
# the value and cost of shortcutting.


DIRECTIONS = [
    North,
    East,
    South,
    West
]


PATH_IDS = {}
TAIL_QUEUE = []
TAIL_HEAD = 0
TAIL_TAIL = 0
TAIL_MAX = 0

CURRENT_TAIL_LENGTH = 1
CURRENT_CYCLE_LENGTH = 0
FULL_CYCLE_LENGTH = 0
NEXT_APPLE = None

SHORTCUT_ATTEMPTS = 0
SHORTCUTS_TAKEN = 0
SHORTCUT_STEPS_SAVED = 0
MOVES_MADE = 0


# ==================================================
# BASIC HELPERS
# ==================================================

def coord():
    return (
        get_pos_x(),
        get_pos_y()
    )


def neighbor(
    location,
    direction
):
    x, y = location

    if direction == North:
        return (
            x,
            y + 1
        )

    if direction == East:
        return (
            x + 1,
            y
        )

    if direction == South:
        return (
            x,
            y - 1
        )

    return (
        x - 1,
        y
    )


def target_tail_length():
    board = (
        get_world_size()
        * get_world_size()
    )

    target = (
        board
        * BENCH_TARGET_PERCENT
        // 100
    )

    if target < 2:
        target = 2

    if target >= board:
        target = board - 1

    return target


def harvest_tail():
    change_hat(
        Hats.Straw_Hat
    )


# ==================================================
# CURRENT BASELINE
# ==================================================

def baseline_move(direction):
    global CURRENT_TAIL_LENGTH
    global MOVES_MADE
    global NEXT_APPLE

    on_apple = (
        get_entity_type()
        == Entities.Apple
    )

    if on_apple:
        NEXT_APPLE = measure()

    if not move(direction):
        return False

    MOVES_MADE += 1

    if on_apple:
        CURRENT_TAIL_LENGTH += 1

    return True


def baseline_reached_target():
    return (
        CURRENT_TAIL_LENGTH
        >= target_tail_length()
    )


def run_baseline_cycle():
    world_size = get_world_size()

    # Left column upward.
    for _ in range(
        world_size - 1
    ):
        if not baseline_move(
            North
        ):
            return False

        if baseline_reached_target():
            return True

    # Vertical skyscraper columns.
    for x in range(
        1,
        world_size
    ):
        if not baseline_move(
            East
        ):
            return False

        if baseline_reached_target():
            return True

        if x % 2 == 1:
            direction = South
        else:
            direction = North

        for _ in range(
            world_size - 2
        ):
            if not baseline_move(
                direction
            ):
                return False

            if baseline_reached_target():
                return True

    if not baseline_move(
        South
    ):
        return False

    if baseline_reached_target():
        return True

    # Bottom return lane.
    for _ in range(
        world_size - 1
    ):
        if not baseline_move(
            West
        ):
            return False

        if baseline_reached_target():
            return True

    return True


def run_baseline():
    while not baseline_reached_target():
        if not run_baseline_cycle():
            return False

    return True


# ==================================================
# HAMILTONIAN / SKYSCRAPER PATH INDEX
# ==================================================

def build_path():
    global PATH_IDS
    global FULL_CYCLE_LENGTH
    global CURRENT_CYCLE_LENGTH

    PATH_IDS = {}

    world_size = get_world_size()

    FULL_CYCLE_LENGTH = (
        world_size
        * world_size
    )

    CURRENT_CYCLE_LENGTH = (
        FULL_CYCLE_LENGTH
    )

    location = (
        0,
        0
    )

    index = 0

    # Left column.
    for _ in range(
        world_size - 1
    ):
        PATH_IDS[location] = [
            index,
            North
        ]

        location = neighbor(
            location,
            North
        )

        index += 1

    # Vertical skyscraper columns.
    for x in range(
        1,
        world_size
    ):
        PATH_IDS[location] = [
            index,
            East
        ]

        location = neighbor(
            location,
            East
        )

        index += 1

        if x % 2 == 1:
            direction = South
        else:
            direction = North

        for _ in range(
            world_size - 2
        ):
            PATH_IDS[location] = [
                index,
                direction
            ]

            location = neighbor(
                location,
                direction
            )

            index += 1

    # Enter bottom return lane.
    PATH_IDS[location] = [
        index,
        South
    ]

    location = neighbor(
        location,
        South
    )

    index += 1

    # Bottom row back to start.
    for _ in range(
        world_size - 1
    ):
        PATH_IDS[location] = [
            index,
            West
        ]

        location = neighbor(
            location,
            West
        )

        index += 1


# ==================================================
# TAIL RING BUFFER
# ==================================================

def tail_reset():
    global TAIL_QUEUE
    global TAIL_HEAD
    global TAIL_TAIL
    global TAIL_MAX

    TAIL_QUEUE = []
    TAIL_HEAD = 0
    TAIL_TAIL = 0

    TAIL_MAX = (
        get_world_size()
        * get_world_size()
    )


def tail_push(item):
    global TAIL_HEAD

    if len(TAIL_QUEUE) < TAIL_MAX:
        TAIL_QUEUE.append(
            item
        )

    else:
        TAIL_QUEUE[
            TAIL_HEAD
        ] = item

    TAIL_HEAD = (
        TAIL_HEAD + 1
    ) % TAIL_MAX


def tail_pop():
    global TAIL_TAIL

    item = TAIL_QUEUE[
        TAIL_TAIL
    ]

    TAIL_TAIL = (
        TAIL_TAIL + 1
    ) % TAIL_MAX

    return item


def tail_peek():
    return TAIL_QUEUE[
        TAIL_TAIL
    ]


# ==================================================
# CYCLE SAFETY
# ==================================================

def mod_between(
    target,
    start,
    end,
    modulo
):
    if end < start:
        end += modulo

    if target < start:
        target += modulo

    return (
        target >= start
        and target <= end
    )


def shortcut_cutoff_percent():
    if BENCH_MODE == 2:
        return 25

    return 50


def shortcut_phase_active():
    fill_percent = (
        CURRENT_TAIL_LENGTH
        * 100
        // FULL_CYCLE_LENGTH
    )

    return (
        fill_percent
        < shortcut_cutoff_percent()
    )


def annealing_allows_shortcut():
    # Mode 1 follows the source-like behavior:
    # shortcut attempts become less frequent as the tail approaches
    # half the board.
    if BENCH_MODE != 1:
        return True

    threshold = (
        1
        - (
            CURRENT_TAIL_LENGTH
            * 2
            / FULL_CYCLE_LENGTH
        )
    )

    return (
        random()
        <= threshold
    )


def can_shortcut(
    here,
    direction
):
    global SHORTCUT_ATTEMPTS

    SHORTCUT_ATTEMPTS += 1

    if not can_move(
        direction
    ):
        return 0

    if not annealing_allows_shortcut():
        return 0

    target = neighbor(
        here,
        direction
    )

    tail = tail_peek()
    tail_location = tail[0]

    # Do not jump forward into the logical interval occupied by
    # the body/tail along the Hamiltonian cycle.
    if mod_between(
        PATH_IDS[target][0],
        PATH_IDS[tail_location][0],
        PATH_IDS[here][0],
        FULL_CYCLE_LENGTH
    ):
        return 0

    # Do not skip past the current Apple in cycle order.
    if not mod_between(
        PATH_IDS[target][0],
        PATH_IDS[here][0],
        PATH_IDS[NEXT_APPLE][0],
        FULL_CYCLE_LENGTH
    ):
        return 0

    here_index = PATH_IDS[
        here
    ][0]

    target_index = PATH_IDS[
        target
    ][0]

    if target_index < here_index:
        target_index += (
            FULL_CYCLE_LENGTH
        )

    removed = (
        target_index
        - here_index
        - 1
    )

    if removed <= 0:
        return 0

    # Keep enough logical cycle length to contain the complete body.
    if (
        CURRENT_CYCLE_LENGTH
        - removed
        <= CURRENT_TAIL_LENGTH + 1
    ):
        return 0

    return removed


# ==================================================
# SAFE SHORTCUT MOVEMENT
# ==================================================

def shortcut_move(
    direction,
    saved
):
    global CURRENT_TAIL_LENGTH
    global CURRENT_CYCLE_LENGTH
    global SHORTCUTS_TAKEN
    global SHORTCUT_STEPS_SAVED
    global MOVES_MADE

    on_apple = (
        get_entity_type()
        == Entities.Apple
    )

    if not move(
        direction
    ):
        return False

    MOVES_MADE += 1

    here = coord()

    CURRENT_CYCLE_LENGTH -= (
        saved
    )

    tail_push([
        here,
        saved
    ])

    if saved > 0:
        SHORTCUTS_TAKEN += 1
        SHORTCUT_STEPS_SAVED += (
            saved
        )

    if on_apple:
        CURRENT_TAIL_LENGTH += 1

    else:
        old_tail = tail_pop()

        CURRENT_CYCLE_LENGTH += (
            old_tail[1]
        )

    return True


def greedy_directions(
    here,
    apple
):
    directions = []

    if here[0] > apple[0]:
        directions.append(
            West
        )

    elif here[0] < apple[0]:
        directions.append(
            East
        )

    if here[1] > apple[1]:
        directions.append(
            South
        )

    elif here[1] < apple[1]:
        directions.append(
            North
        )

    return directions


def shortcut_step():
    global NEXT_APPLE

    here = coord()

    # measure() on the current Apple reveals the following Apple.
    # Update the target before selecting this move so the departure
    # from an Apple may itself take a safe shortcut.
    if (
        get_entity_type()
        == Entities.Apple
    ):
        NEXT_APPLE = measure()

    direction = PATH_IDS[
        here
    ][1]

    saved = 0

    if shortcut_phase_active():
        directions = greedy_directions(
            here,
            NEXT_APPLE
        )

        for candidate in directions:
            candidate_saved = (
                can_shortcut(
                    here,
                    candidate
                )
            )

            if candidate_saved > 0:
                direction = candidate
                saved = candidate_saved
                break

    return shortcut_move(
        direction,
        saved
    )


def run_shortcuts():
    while (
        CURRENT_TAIL_LENGTH
        < target_tail_length()
    ):
        if not shortcut_step():
            return False

    return True


# ==================================================
# SKYSDOTTIR/TFWR REFERENCE
# ==================================================
#
# Behavioral port of:
# https://github.com/skysdottir/tfwr/blob/main/dinos3.py
# https://github.com/skysdottir/tfwr/blob/main/hilbert.py
#
# Keep this mode source-like. It intentionally uses Hilbert rather
# than our production/skyscraper path, source-style tail anticipation
# on arrival at the Apple, and the source annealing formula.
#
# REF_ACTUAL_TAIL_LENGTH is separate from REF_TAIL_LENGTH:
# - REF_TAIL_LENGTH preserves the source's logical accounting
# - REF_ACTUAL_TAIL_LENGTH gives the benchmark a fair stop condition
#   based on Apples actually consumed by leaving their tile.
# ==================================================

REF_PATH_IDS = {}

REF_TAIL_LENGTH = 1
REF_ACTUAL_TAIL_LENGTH = 1
REF_CYCLE_LENGTH = 0
REF_FULL_CYCLE_LENGTH = 0
REF_NEXT_APPLE = None

REF_DIR_2_ENTRY_CORNER = {
    East: (0, 1),
    West: (1, 0),
    South: (0, 1),
    North: (1, 0)
}

REF_HILBERT_PATHS = {
    (North, North): [
        West,
        North,
        East,
        North
    ],
    (South, South): [
        East,
        South,
        West,
        South
    ],
    (East, East): [
        South,
        East,
        North,
        East
    ],
    (West, West): [
        North,
        West,
        South,
        West
    ],
    (North, East): [
        West,
        North,
        East,
        East
    ],
    (North, West): [
        North,
        West,
        South,
        West
    ],
    (East, North): [
        South,
        East,
        North,
        North
    ],
    (East, South): [
        East,
        South,
        West,
        South
    ],
    (South, East): [
        South,
        East,
        North,
        East
    ],
    (South, West): [
        East,
        South,
        West,
        West
    ],
    (West, North): [
        West,
        North,
        East,
        North
    ],
    (West, South): [
        North,
        West,
        South,
        South
    ]
}


def ref_hilbert_move(
    location,
    delta,
    direction
):
    x, y = location

    if direction == North:
        return (
            x,
            y + delta
        )

    if direction == South:
        return (
            x,
            y - delta
        )

    if direction == East:
        return (
            x + delta,
            y
        )

    if direction == West:
        return (
            x - delta,
            y
        )

    return location


def ref_hilbert_recurse(
    enter,
    exit_direction,
    location,
    delta,
    range_start
):
    global REF_PATH_IDS

    if delta == 1:
        REF_PATH_IDS[
            location
        ] = [
            range_start,
            exit_direction
        ]

        return

    half = delta // 2

    path = REF_HILBERT_PATHS[
        (
            enter,
            exit_direction
        )
    ]

    entry_corner = (
        REF_DIR_2_ENTRY_CORNER[
            enter
        ]
    )

    sub_square = (
        location[0]
        + entry_corner[0]
        * half,
        location[1]
        + entry_corner[1]
        * half
    )

    current_enter = enter

    for index in range(
        len(path)
    ):
        direction = path[index]

        ref_hilbert_recurse(
            current_enter,
            direction,
            sub_square,
            half,
            range_start
            + (
                index
                * half
                * half
            )
        )

        sub_square = (
            ref_hilbert_move(
                sub_square,
                half,
                direction
            )
        )

        current_enter = (
            direction
        )


def ref_build_hilbert_path():
    global REF_PATH_IDS
    global REF_FULL_CYCLE_LENGTH
    global REF_CYCLE_LENGTH

    REF_PATH_IDS = {}

    world_size = get_world_size()

    REF_FULL_CYCLE_LENGTH = (
        world_size
        * world_size
    )

    REF_CYCLE_LENGTH = (
        REF_FULL_CYCLE_LENGTH
    )

    half = world_size // 2

    location = (
        0,
        0
    )

    enter = West

    path = [
        North,
        East,
        South,
        West
    ]

    for index in range(4):
        direction = path[index]

        ref_hilbert_recurse(
            enter,
            direction,
            location,
            half,
            index
            * half
            * half
        )

        location = ref_hilbert_move(
            location,
            half,
            direction
        )

        enter = direction


def ref_get_target(
    here,
    direction
):
    return neighbor(
        here,
        direction
    )


def ref_can_shortcut(
    here,
    direction
):
    global SHORTCUT_ATTEMPTS

    SHORTCUT_ATTEMPTS += 1

    if not can_move(
        direction
    ):
        return 0

    threshold = (
        1
        - (
            REF_TAIL_LENGTH
            * 2
            / REF_FULL_CYCLE_LENGTH
        )
    )

    if random() > threshold:
        return 0

    tail = tail_peek()
    tail_location = tail[0]

    target = ref_get_target(
        here,
        direction
    )

    if mod_between(
        REF_PATH_IDS[target][0],
        REF_PATH_IDS[tail_location][0],
        REF_PATH_IDS[here][0],
        REF_FULL_CYCLE_LENGTH
    ):
        return 0

    if not mod_between(
        REF_PATH_IDS[target][0],
        REF_PATH_IDS[here][0],
        REF_PATH_IDS[REF_NEXT_APPLE][0],
        REF_FULL_CYCLE_LENGTH
    ):
        return 0

    here_index = (
        REF_PATH_IDS[here][0]
    )

    target_index = (
        REF_PATH_IDS[target][0]
    )

    if target_index < here_index:
        target_index += (
            REF_FULL_CYCLE_LENGTH
        )

    removed = (
        target_index
        - here_index
        - 1
    )

    if (
        REF_CYCLE_LENGTH
        - removed
        > REF_TAIL_LENGTH + 1
    ):
        return removed

    return 0


def ref_scoot(
    direction,
    saved
):
    global REF_TAIL_LENGTH
    global REF_ACTUAL_TAIL_LENGTH
    global REF_CYCLE_LENGTH
    global REF_NEXT_APPLE
    global SHORTCUTS_TAKEN
    global SHORTCUT_STEPS_SAVED
    global MOVES_MADE

    on_apple = (
        get_entity_type()
        == Entities.Apple
    )

    if not move(
        direction
    ):
        return -1

    MOVES_MADE += 1

    if on_apple:
        REF_ACTUAL_TAIL_LENGTH += 1

    here = coord()

    REF_CYCLE_LENGTH -= (
        saved
    )

    tail_push([
        here,
        saved
    ])

    if saved > 0:
        SHORTCUTS_TAKEN += 1
        SHORTCUT_STEPS_SAVED += (
            saved
        )

    # Source behavior: logical tail accounting advances on ARRIVAL
    # at the current Apple, then measure() reveals the following Apple.
    if here == REF_NEXT_APPLE:
        REF_TAIL_LENGTH += 1
        REF_NEXT_APPLE = measure()

        return 1

    old_tail = tail_pop()

    REF_CYCLE_LENGTH += (
        old_tail[1]
    )

    return 0


def ref_dino_iter():
    here = coord()

    direction = REF_PATH_IDS[
        here
    ][1]

    saved = 0

    # Exact source policy: once at half-board, stop shortcutting.
    if (
        REF_TAIL_LENGTH
        >= REF_FULL_CYCLE_LENGTH / 2
    ):
        return ref_scoot(
            direction,
            saved
        )

    wanted = []

    if here[0] > REF_NEXT_APPLE[0]:
        wanted.append(
            West
        )

    if here[0] < REF_NEXT_APPLE[0]:
        wanted.append(
            East
        )

    if here[1] > REF_NEXT_APPLE[1]:
        wanted.append(
            South
        )

    if here[1] < REF_NEXT_APPLE[1]:
        wanted.append(
            North
        )

    for candidate in wanted:
        candidate_saved = (
            ref_can_shortcut(
                here,
                candidate
            )
        )

        if candidate_saved > saved:
            direction = candidate
            saved = candidate_saved
            break

    return ref_scoot(
        direction,
        saved
    )


def run_skysdottir_reference():
    while (
        REF_ACTUAL_TAIL_LENGTH
        < target_tail_length()
    ):
        result = ref_dino_iter()

        if result < 0:
            return False

    return True


def setup_skysdottir_reference():
    global REF_TAIL_LENGTH
    global REF_ACTUAL_TAIL_LENGTH
    global REF_NEXT_APPLE

    # The reference Hilbert generator requires a 2^n world size.
    # Current benchmark sizes 8, 16, and 32 all satisfy this.
    ref_build_hilbert_path()

    tail_reset()

    REF_TAIL_LENGTH = 1
    REF_ACTUAL_TAIL_LENGTH = 1

    REF_NEXT_APPLE = measure()

    tail_push([
        (
            0,
            0
        ),
        0
    ])


# ==================================================
# SETUP / ENTRYPOINT
# ==================================================

def setup_cycle(
    reset_world
):
    global CURRENT_TAIL_LENGTH
    global NEXT_APPLE
    global SHORTCUT_ATTEMPTS
    global SHORTCUTS_TAKEN
    global SHORTCUT_STEPS_SAVED
    global MOVES_MADE

    if reset_world:
        set_world_size(
            BENCH_WORLD_SIZE
        )

    # Between sustained cycles the harvested tail leaves the field
    # empty. Reposition without clearing/resetting the world again.
    move_to_x = get_pos_x()

    while move_to_x > 0:
        move(
            West
        )
        move_to_x -= 1

    move_to_y = get_pos_y()

    while move_to_y > 0:
        move(
            South
        )
        move_to_y -= 1

    change_hat(
        Hats.Dinosaur_Hat
    )

    if (
        get_entity_type()
        != Entities.Apple
    ):
        return False

    CURRENT_TAIL_LENGTH = 1
    NEXT_APPLE = measure()

    SHORTCUT_ATTEMPTS = 0
    SHORTCUTS_TAKEN = 0
    SHORTCUT_STEPS_SAVED = 0
    MOVES_MADE = 0

    if BENCH_MODE == 4:
        setup_skysdottir_reference()

    elif BENCH_MODE != 0:
        build_path()
        tail_reset()

        tail_push([
            (
                0,
                0
            ),
            0
        ])

    return True


def run_one_cycle():
    global CURRENT_TAIL_LENGTH

    if BENCH_MODE == 0:
        return run_baseline()

    if BENCH_MODE == 4:
        success = (
            run_skysdottir_reference()
        )

        CURRENT_TAIL_LENGTH = (
            REF_ACTUAL_TAIL_LENGTH
        )

        return success

    return run_shortcuts()


def main():
    start_ticks = get_tick_count()
    start_time = get_time()

    completed_cycles = 0

    for cycle in range(
        BENCH_CYCLES
    ):
        if not setup_cycle(
            cycle == 0
        ):
            quick_print(
                "DINOSAUR BENCH INVALID",
                "setup",
                cycle
            )
            return

        success = run_one_cycle()

        if not success:
            quick_print(
                "DINOSAUR BENCH INVALID",
                BENCH_MODE,
                BENCH_WORLD_SIZE,
                BENCH_TARGET_PERCENT,
                CURRENT_TAIL_LENGTH,
                "cycle",
                cycle
            )

            harvest_tail()
            return

        harvest_tail()
        completed_cycles += 1

    elapsed_ticks = (
        get_tick_count()
        - start_ticks
    )

    elapsed_time = (
        get_time()
        - start_time
    )

    if BENCH_VERBOSE:
        quick_print(
            "DINOSAUR BENCH",
            BENCH_MODE,
            BENCH_WORLD_SIZE,
            BENCH_TARGET_PERCENT,
            "cycles",
            completed_cycles,
            "tail",
            CURRENT_TAIL_LENGTH,
            "moves",
            MOVES_MADE,
            "shortcut_attempts",
            SHORTCUT_ATTEMPTS,
            "shortcuts",
            SHORTCUTS_TAKEN,
            "saved",
            SHORTCUT_STEPS_SAVED,
            "ticks",
            elapsed_ticks,
            "time",
            elapsed_time
        )


main()
