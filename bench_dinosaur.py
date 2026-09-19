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
    # This is the number that the Bone reward uses: tail segments only.
    # The Dinosaur's occupied length is one larger because it also has
    # a head. CURRENT_TAIL_LENGTH historically tracked occupied length.
    board = (
        get_world_size()
        * get_world_size()
    )

    target = (
        board
        * BENCH_TARGET_PERCENT
        // 100
    )

    if target < 1:
        target = 1

    if target >= board:
        target = board - 1

    return target


def target_snake_length():
    return (
        target_tail_length()
        + 1
    )


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
        >= target_snake_length()
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
    # 25% experiments.
    if (
        BENCH_MODE == 2
        or BENCH_MODE == 13
        or BENCH_MODE == 14
        or BENCH_MODE == 15
        or BENCH_MODE == 16
    ):
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
    # Annealed variants follow the skysdottir idea:
    # shortcut attempts become less frequent as the tail grows.
    annealed = (
        BENCH_MODE == 1
        or BENCH_MODE == 5
        or BENCH_MODE == 7
        or BENCH_MODE == 8
        or BENCH_MODE == 13
        or BENCH_MODE == 14
    )

    if not annealed:
        return True

    threshold = (
        1
        - (
            CURRENT_TAIL_LENGTH
            * 2
            / FULL_CYCLE_LENGTH
        )
    )

    if threshold < 0:
        return False

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


def append_direction_once(
    directions,
    direction
):
    if direction not in directions:
        directions.append(
            direction
        )


def shortcut_directions(
    here
):
    directions = []

    # Reddit/skysdottir skyscraper fast-lane idea:
    # when the Apple is behind us, prefer dropping toward the
    # bottom return lane before evaluating normal greedy moves.
    skyscraper_fastlane = (
        BENCH_MODE == 5
        or BENCH_MODE == 13
        or BENCH_MODE == 15
        or BENCH_MODE == 18
    )

    if (
        skyscraper_fastlane
        and here[1] > 1
        and NEXT_APPLE[0] < here[0]
    ):
        append_direction_once(
            directions,
            South
        )

    # Reddit/skysdottir heartbeat fast-lane idea:
    # move toward the central return lane when the Apple is in
    # the opposite half / behind the current sweep.
    heartbeat_fastlane = (
        BENCH_MODE == 8
        or BENCH_MODE == 14
        or BENCH_MODE == 16
        or BENCH_MODE == 19
    )

    if heartbeat_fastlane:
        half = (
            get_world_size()
            // 2
        )

        if (
            here[1] > half
            and (
                NEXT_APPLE[1] < half
                or NEXT_APPLE[0] < here[0]
            )
        ):
            append_direction_once(
                directions,
                South
            )

        if (
            here[1] < half - 1
            and (
                NEXT_APPLE[1] >= half
                or NEXT_APPLE[0] > here[0]
            )
        ):
            append_direction_once(
                directions,
                North
            )

    greedy = greedy_directions(
        here,
        NEXT_APPLE
    )

    for candidate in greedy:
        append_direction_once(
            directions,
            candidate
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

    if NEXT_APPLE == None:
        return False

    direction = PATH_IDS[
        here
    ][1]

    saved = 0

    if shortcut_phase_active():
        directions = shortcut_directions(
            here
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
        < target_snake_length()
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
        < target_snake_length()
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
# ADDITIONAL PATH / REDDIT / SETUP EXPERIMENTS
# ==================================================
#
# Additional modes:
#
#  5 = skyscraper fast-lane + annealed shortcuts, cutoff 50%
#  6 = heartbeat Hamiltonian only
#  7 = heartbeat + annealed shortcuts, cutoff 50%
#  8 = heartbeat fast-lane + annealed shortcuts, cutoff 50%
#  9 = Hilbert Hamiltonian only
# 10 = Reddit coil/strike, safe transition at 33%
# 11 = Reddit coil/strike, source-like safe transition at 50%
# 12 = Reddit coil/strike, safe transition at 66%
# 13 = skyscraper fast-lane + annealed shortcuts, cutoff 25%
# 14 = heartbeat fast-lane + annealed shortcuts, cutoff 25%
# 15 = skyscraper fast-lane + hard shortcuts, cutoff 25%
# 16 = heartbeat fast-lane + hard shortcuts, cutoff 25%
# 17 = heartbeat + hard shortcuts, cutoff 50%
# 18 = skyscraper fast-lane + hard shortcuts, cutoff 50%
# 19 = heartbeat fast-lane + hard shortcuts, cutoff 50%
#
# Setup modes:
#
# 0 = no cleanup
# 1 = clear()
# 2 = serial harvest + convert every tile to Soil
# 3 = parallel harvest only
# 4 = parallel harvest + convert every tile to Soil
# 5 = source-style Sunflower Hat + parallel harvest + Soil
#
# Reddit references:
# https://www.reddit.com/r/TheFarmerWasReplaced/comments/1p0ox9z/
# https://www.reddit.com/r/TheFarmerWasReplaced/comments/1omrxi4/
#
# The coil/strike implementation below is an independent benchmark
# implementation of the published four-phase algorithm description.
# It is not a verbatim copy of the unlicensed Pastebin source.
# ==================================================


def build_heartbeat_path():
    global PATH_IDS
    global FULL_CYCLE_LENGTH
    global CURRENT_CYCLE_LENGTH

    world_size = get_world_size()

    FULL_CYCLE_LENGTH = (
        world_size
        * world_size
    )

    CURRENT_CYCLE_LENGTH = (
        FULL_CYCLE_LENGTH
    )

    next_directions = {}

    half = (
        world_size
        // 2
    )

    # Upper half: left-to-right vertical sweeps.
    for x in range(
        0,
        world_size,
        2
    ):
        for y in range(
            half,
            world_size
        ):
            direction = North

            if y == world_size - 1:
                direction = East

            next_directions[
                (
                    x,
                    y
                )
            ] = direction

        for y in range(
            world_size - 1,
            half - 1,
            -1
        ):
            direction = South

            if (
                y == half
                and x != world_size - 2
            ):
                direction = East

            next_directions[
                (
                    x + 1,
                    y
                )
            ] = direction

    # Lower half: right-to-left vertical sweeps.
    for x in range(
        world_size - 1,
        0,
        -2
    ):
        for y in range(
            half - 1,
            -1,
            -1
        ):
            direction = South

            if y == 0:
                direction = West

            next_directions[
                (
                    x,
                    y
                )
            ] = direction

        for y in range(
            0,
            half
        ):
            direction = North

            if (
                y == half - 1
                and x != 1
            ):
                direction = West

            next_directions[
                (
                    x - 1,
                    y
                )
            ] = direction

    # Normalize the upstream geometry to indices 0..N*N-1,
    # starting from the benchmark origin.
    PATH_IDS = {}

    here = (
        0,
        0
    )

    for index in range(
        FULL_CYCLE_LENGTH
    ):
        direction = next_directions[
            here
        ]

        PATH_IDS[
            here
        ] = [
            index,
            direction
        ]

        here = neighbor(
            here,
            direction
        )


def build_path_for_mode():
    heartbeat = (
        BENCH_MODE == 6
        or BENCH_MODE == 7
        or BENCH_MODE == 8
        or BENCH_MODE == 14
        or BENCH_MODE == 16
        or BENCH_MODE == 17
        or BENCH_MODE == 19
    )

    if heartbeat:
        build_heartbeat_path()
    else:
        build_path()


def run_indexed_path():
    global NEXT_APPLE

    while (
        CURRENT_TAIL_LENGTH
        < target_snake_length()
    ):
        if (
            get_entity_type()
            == Entities.Apple
        ):
            NEXT_APPLE = measure()

        if NEXT_APPLE == None:
            return False

        here = coord()

        if not shortcut_move(
            PATH_IDS[
                here
            ][1],
            0
        ):
            return False

    return True


def run_hilbert_path_only():
    while (
        REF_ACTUAL_TAIL_LENGTH
        < target_snake_length()
    ):
        here = coord()

        result = ref_scoot(
            REF_PATH_IDS[
                here
            ][1],
            0
        )

        if result < 0:
            return False

        if REF_NEXT_APPLE == None:
            return False

    return True


def move_to_origin_normal():
    world_size = get_world_size()

    x = get_pos_x()

    if x <= world_size - x:
        for _ in range(
            x
        ):
            move(
                West
            )
    else:
        for _ in range(
            world_size - x
        ):
            move(
                East
            )

    y = get_pos_y()

    if y <= world_size - y:
        for _ in range(
            y
        ):
            move(
                South
            )
    else:
        for _ in range(
            world_size - y
        ):
            move(
                North
            )


def prep_tile(
    make_soil
):
    if get_entity_type() != None:
        harvest()

    if (
        make_soil
        and get_ground_type()
        != Grounds.Soil
    ):
        till()


def prep_column(
    column,
    make_soil
):
    world_size = get_world_size()

    # Spawned workers start at the controller position. The controller
    # is at (0,0), so use normal wrap-around movement to reach the
    # assigned column with the shorter direction.
    if column <= world_size // 2:
        for _ in range(
            column
        ):
            move(
                East
            )
    else:
        for _ in range(
            world_size - column
        ):
            move(
                West
            )

    for y in range(
        world_size
    ):
        prep_tile(
            make_soil
        )

        if y < world_size - 1:
            move(
                North
            )


def prep_serial_soil():
    world_size = get_world_size()

    move_to_origin_normal()

    for x in range(
        world_size
    ):
        if x % 2 == 0:
            direction = North
        else:
            direction = South

        for y in range(
            world_size
        ):
            prep_tile(
                True
            )

            if y < world_size - 1:
                move(
                    direction
                )

        if x < world_size - 1:
            move(
                East
            )


def prep_current_column(
    make_soil
):
    world_size = get_world_size()

    for y in range(
        world_size
    ):
        prep_tile(
            make_soil
        )

        if y < world_size - 1:
            move(
                North
            )


def prep_flekay_line(
    make_soil
):
    world_size = get_world_size()

    move_to_origin_normal()

    handles = []

    for column in range(
        world_size - 1
    ):
        handle = spawn_drone(
            prep_current_column,
            make_soil
        )

        if handle != None:
            handles.append(
                handle
            )

        move(
            East
        )

    prep_current_column(
        make_soil
    )

    for handle in handles:
        wait_for(
            handle
        )


def prep_flekay_dual_right(
    make_soil
):
    world_size = get_world_size()
    half = (
        world_size
        // 2
    )

    handles = []

    for column in range(
        half + 1,
        world_size
    ):
        handle = spawn_drone(
            prep_column,
            column,
            make_soil
        )

        if handle != None:
            handles.append(
                handle
            )

    # The second spawner owns the center column.
    prep_column(
        half,
        make_soil
    )

    for handle in handles:
        wait_for(
            handle
        )


def prep_flekay_dual(
    make_soil
):
    world_size = get_world_size()
    half = (
        world_size
        // 2
    )

    move_to_origin_normal()

    right_spawner = spawn_drone(
        prep_flekay_dual_right,
        make_soil
    )

    handles = []

    for column in range(
        1,
        half
    ):
        handle = spawn_drone(
            prep_column,
            column,
            make_soil
        )

        if handle != None:
            handles.append(
                handle
            )

    # The controller owns column zero.
    prep_column(
        0,
        make_soil
    )

    for handle in handles:
        wait_for(
            handle
        )

    if right_spawner != None:
        wait_for(
            right_spawner
        )


def prep_parallel(
    make_soil
):
    world_size = get_world_size()

    move_to_origin_normal()

    handles = []
    column = 0
    worker_limit = (
        max_drones()
        - 1
    )

    while (
        column < world_size
        and len(handles) < worker_limit
    ):
        handle = spawn_drone(
            prep_column,
            column,
            make_soil
        )

        if handle == None:
            break

        handles.append(
            handle
        )

        column += 1

    # The controller is a worker as well.
    while column < world_size:
        prep_column(
            column,
            make_soil
        )

        column += 1

    for handle in handles:
        wait_for(
            handle
        )


def prepare_field():
    if BENCH_SETUP_MODE == 0:
        return

    if BENCH_SETUP_MODE == 1:
        clear()
        return

    if BENCH_SETUP_MODE == 2:
        prep_serial_soil()
        return

    if BENCH_SETUP_MODE == 3:
        prep_parallel(
            False
        )
        return

    if BENCH_SETUP_MODE == 5:
        # Match the skysdottir prep shape more closely, including
        # the otherwise unnecessary hat switch.
        change_hat(
            Hats.Sunflower_Hat
        )

        prep_parallel(
            True
        )
        return

    if BENCH_SETUP_MODE == 6:
        prep_flekay_line(
            True
        )
        return

    if BENCH_SETUP_MODE == 7:
        prep_flekay_dual(
            True
        )
        return

    prep_parallel(
        True
    )


# ==================================================
# FLEKAY EARLY-PHASE DIAGNOSTICS
# ==================================================
#
# Modes 20 and 21 intentionally benchmark only the early Apple-chasing
# phase. They are not assumed to survive a near-full board.
#
# 20 = plain axis-greedy with cheap failed-move fallbacks
# 21 = parity-greedy from Flekay's historical/current drone.py phase one
#
# The current upstream drone.py no longer has a working phase two.
# These modes therefore measure the reusable early-phase idea without
# inventing a Hamiltonian handoff that the source does not provide.
# ==================================================


def refresh_next_apple_on_arrival():
    global NEXT_APPLE

    if (
        NEXT_APPLE != None
        and get_pos_x() == NEXT_APPLE[0]
        and get_pos_y() == NEXT_APPLE[1]
    ):
        NEXT_APPLE = measure()


def flekay_try_move(
    primary,
    fallback
):
    first = baseline_move(
        primary
    )

    if first:
        refresh_next_apple_on_arrival()
        return True

    second = baseline_move(
        fallback
    )

    if second:
        refresh_next_apple_on_arrival()
        return True

    return False


def run_flekay_axis_greedy():
    loops = 0

    while (
        CURRENT_TAIL_LENGTH
        < target_snake_length()
        and loops < BENCH_MAX_MOVES
    ):
        loops += 1

        if NEXT_APPLE == None:
            return False

        x = get_pos_x()
        y = get_pos_y()

        moved = False

        if x < NEXT_APPLE[0]:
            moved = flekay_try_move(
                East,
                North
            )

        elif x > NEXT_APPLE[0]:
            moved = flekay_try_move(
                West,
                South
            )

        elif y < NEXT_APPLE[1]:
            moved = flekay_try_move(
                North,
                East
            )

        elif y > NEXT_APPLE[1]:
            moved = flekay_try_move(
                South,
                West
            )

        else:
            refresh_next_apple_on_arrival()
            moved = True

        if not moved:
            return False

    return (
        CURRENT_TAIL_LENGTH
        >= target_snake_length()
    )


def run_flekay_parity_greedy():
    loops = 0

    while (
        CURRENT_TAIL_LENGTH
        < target_snake_length()
        and loops < BENCH_MAX_MOVES
    ):
        loops += 1

        if NEXT_APPLE == None:
            return False

        x = get_pos_x()
        y = get_pos_y()

        x_even = (
            x % 2 == 0
        )
        y_even = (
            y % 2 == 0
        )

        if x_even:
            if y_even:
                if NEXT_APPLE[1] < y:
                    if not flekay_try_move(
                        South,
                        East
                    ):
                        return False
                else:
                    if not flekay_try_move(
                        East,
                        South
                    ):
                        return False
            else:
                if NEXT_APPLE[0] < x:
                    if not flekay_try_move(
                        West,
                        South
                    ):
                        return False
                else:
                    if not flekay_try_move(
                        South,
                        West
                    ):
                        return False
        else:
            if y_even:
                if NEXT_APPLE[0] > x:
                    if not flekay_try_move(
                        East,
                        North
                    ):
                        return False
                else:
                    if not flekay_try_move(
                        North,
                        East
                    ):
                        return False
            else:
                if NEXT_APPLE[1] > y:
                    if not flekay_try_move(
                        North,
                        West
                    ):
                        return False
                else:
                    if not flekay_try_move(
                        West,
                        North
                    ):
                        return False

    return (
        CURRENT_TAIL_LENGTH
        >= target_snake_length()
    )


def coil_cutoff_percent():
    if BENCH_MODE == 10:
        return 33

    if BENCH_MODE == 12:
        return 66

    return 50


def coil_refresh_apple():
    global NEXT_APPLE

    if (
        get_entity_type()
        == Entities.Apple
    ):
        NEXT_APPLE = measure()


def coil_blocked(
    direction,
    target_x,
    target_y
):
    quick_print(
        "DINOSAUR COIL BLOCKED",
        "mode",
        BENCH_MODE,
        "at",
        get_pos_x(),
        get_pos_y(),
        "direction",
        direction,
        "target",
        target_x,
        target_y,
        "tail",
        CURRENT_TAIL_LENGTH - 1,
        "apple",
        NEXT_APPLE
    )


def coil_move_to(
    target_x,
    target_y
):
    world_size = get_world_size()

    # The published source sometimes targets world_size itself and
    # relies on the blocked border move. Clamp to the actual edge so
    # this benchmark measures the route instead of repeated failures.
    if target_x < 0:
        target_x = 0

    if target_x >= world_size:
        target_x = world_size - 1

    if target_y < 0:
        target_y = 0

    if target_y >= world_size:
        target_y = world_size - 1

    while get_pos_x() < target_x:
        if not baseline_move(
            East
        ):
            coil_blocked(
                East,
                target_x,
                target_y
            )
            return False

        if (
            CURRENT_TAIL_LENGTH
            >= target_snake_length()
        ):
            return True

    while get_pos_x() > target_x:
        if not baseline_move(
            West
        ):
            coil_blocked(
                West,
                target_x,
                target_y
            )
            return False

        if (
            CURRENT_TAIL_LENGTH
            >= target_snake_length()
        ):
            return True

    while get_pos_y() < target_y:
        if not baseline_move(
            North
        ):
            coil_blocked(
                North,
                target_x,
                target_y
            )
            return False

        if (
            CURRENT_TAIL_LENGTH
            >= target_snake_length()
        ):
            return True

    while get_pos_y() > target_y:
        if not baseline_move(
            South
        ):
            coil_blocked(
                South,
                target_x,
                target_y
            )
            return False

        if (
            CURRENT_TAIL_LENGTH
            >= target_snake_length()
        ):
            return True

    return True


def run_coil_safe_finish():
    world_size = get_world_size()

    while (
        CURRENT_TAIL_LENGTH
        < target_snake_length()
    ):
        for column in range(
            world_size
        ):
            if column % 2 == 0:
                target_y = (
                    world_size - 1
                )
            else:
                target_y = 1

            if not coil_move_to(
                get_pos_x(),
                target_y
            ):
                return False

            if (
                CURRENT_TAIL_LENGTH
                >= target_snake_length()
            ):
                return True

            if column < world_size - 1:
                if not coil_move_to(
                    get_pos_x() + 1,
                    target_y
                ):
                    return False

                if (
                    CURRENT_TAIL_LENGTH
                    >= target_snake_length()
                ):
                    return True

        if not baseline_move(
            South
        ):
            return False

        if (
            CURRENT_TAIL_LENGTH
            >= target_snake_length()
        ):
            return True

        if not coil_move_to(
            0,
            0
        ):
            return False

        if not coil_move_to(
            0,
            1
        ):
            return False

    return True


def run_reddit_coil_strike():
    global NEXT_APPLE

    world_size = get_world_size()
    board = (
        world_size
        * world_size
    )

    # Source-near state:
    # 0=coil, 1=strike, 2=pre-return, 3=return.
    phase = 0
    path_progress = 1
    fix_flag = False
    loops = 0

    # The source measures the initial Apple at (0,0), then leaves it
    # toward (0,1). setup_cycle() already populated NEXT_APPLE.
    if not coil_move_to(
        0,
        1
    ):
        return False

    while (
        CURRENT_TAIL_LENGTH
        < target_snake_length()
        and loops < BENCH_MAX_MOVES
    ):
        loops += 1

        if NEXT_APPLE == None:
            return False

        # The source enters the deterministic safe phase only after a
        # complete return to the origin resets its path counter.
        if (
            path_progress == 0
            and (
                (
                    CURRENT_TAIL_LENGTH
                    - 1
                )
                * 100
                >= board
                * coil_cutoff_percent()
            )
        ):
            return run_coil_safe_finish()

        if phase == 0:
            # COIL
            #
            # Build a known vertical zig-zag body. Apples on the current
            # column are consumed immediately because that does not leave
            # the safe coil corridor.
            if (
                NEXT_APPLE[0]
                == get_pos_x()
            ):
                if not coil_move_to(
                    NEXT_APPLE[0],
                    NEXT_APPLE[1]
                ):
                    return False

                coil_refresh_apple()

                # Source behavior: after refreshing the Apple target,
                # compare from the CURRENT y position to the NEW Apple.
                # The old port incorrectly used the pre-move y value.
                if NEXT_APPLE != None:
                    path_progress += abs(
                        get_pos_y()
                        - NEXT_APPLE[1]
                    )

            else:
                if (
                    get_pos_x()
                    % 2
                    == 0
                ):
                    if not coil_move_to(
                        get_pos_x(),
                        world_size - 1
                    ):
                        return False

                    if not coil_move_to(
                        get_pos_x() + 1,
                        world_size - 1
                    ):
                        return False
                else:
                    if not coil_move_to(
                        get_pos_x(),
                        1
                    ):
                        return False

                    if not coil_move_to(
                        get_pos_x() + 1,
                        1
                    ):
                        return False

                path_progress += (
                    world_size
                )

            # Flekay/Reddit source tracks tail segments, while our
            # CURRENT_TAIL_LENGTH tracks occupied cells (head + tail).
            if (
                path_progress
                > CURRENT_TAIL_LENGTH - 1
            ):
                phase = 1

                # The original aligns to the north edge when the next
                # Apple lies on the transition column. This piece was
                # missing from the first local translation.
                if (
                    NEXT_APPLE != None
                    and NEXT_APPLE[0]
                    == get_pos_x()
                ):
                    if not coil_move_to(
                        NEXT_APPLE[0],
                        NEXT_APPLE[1]
                    ):
                        return False

                    coil_refresh_apple()

                    if fix_flag:
                        if (
                            get_pos_x()
                            != world_size - 2
                        ):
                            if not baseline_move(
                                East
                            ):
                                return False

                        if not coil_move_to(
                            get_pos_x(),
                            world_size - 1
                        ):
                            return False

                        fix_flag = False
                    else:
                        if not coil_move_to(
                            get_pos_x(),
                            world_size - 1
                        ):
                            return False

            if (
                get_pos_x()
                >= world_size - 1
            ):
                phase = 2

        elif phase == 1:
            # STRIKE
            #
            # Apples farther east and away from the bottom return row are
            # in the open strike region and can be chased directly.
            if (
                NEXT_APPLE[0]
                == world_size - 1
                and NEXT_APPLE[1]
                > get_pos_y()
            ):
                phase = 2
                fix_flag = True

            elif (
                NEXT_APPLE[0]
                > get_pos_x()
                and NEXT_APPLE[1]
                != 0
            ):
                if not coil_move_to(
                    NEXT_APPLE[0],
                    NEXT_APPLE[1]
                ):
                    return False

                coil_refresh_apple()

                if (
                    get_pos_x()
                    == world_size - 1
                ):
                    phase = 2

            else:
                phase = 2

        elif phase == 2:
            # PRE-RETURN
            if (
                NEXT_APPLE[0]
                == world_size - 1
                and NEXT_APPLE[1]
                < get_pos_y()
            ):
                if not coil_move_to(
                    NEXT_APPLE[0],
                    NEXT_APPLE[1]
                ):
                    return False

                coil_refresh_apple()

            else:
                if not coil_move_to(
                    world_size - 1,
                    get_pos_y()
                ):
                    return False

                if not coil_move_to(
                    world_size - 1,
                    0
                ):
                    return False

                phase = 3

        else:
            # RETURN
            if NEXT_APPLE[1] == 0:
                if not coil_move_to(
                    NEXT_APPLE[0],
                    NEXT_APPLE[1]
                ):
                    return False

                coil_refresh_apple()

            else:
                if not coil_move_to(
                    0,
                    0
                ):
                    return False

                path_progress = 0
                phase = 0

                if not coil_move_to(
                    0,
                    1
                ):
                    return False

                coil_refresh_apple()

    return (
        CURRENT_TAIL_LENGTH
        >= target_snake_length()
    )


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

    # Leaderboards.Dinosaur already starts at the maximum farm size.
    # Only resize diagnostic simulations that explicitly request
    # another world size. Avoid an unnecessary clear/reset on 32x32.
    if (
        reset_world
        and get_world_size()
        != BENCH_WORLD_SIZE
    ):
        set_world_size(
            BENCH_WORLD_SIZE
        )

    if reset_world:
        prepare_field()

    # Between sustained cycles the harvested tail leaves the field
    # empty. Reposition without clearing/resetting the world again.
    move_to_origin_normal()

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

    if (
        BENCH_MODE == 4
        or BENCH_MODE == 9
    ):
        setup_skysdottir_reference()

    elif (
        BENCH_MODE != 0
        and BENCH_MODE != 10
        and BENCH_MODE != 11
        and BENCH_MODE != 12
        and BENCH_MODE != 20
        and BENCH_MODE != 21
    ):
        build_path_for_mode()
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

    if BENCH_MODE == 6:
        return run_indexed_path()

    if BENCH_MODE == 9:
        success = (
            run_hilbert_path_only()
        )

        CURRENT_TAIL_LENGTH = (
            REF_ACTUAL_TAIL_LENGTH
        )

        return success

    if (
        BENCH_MODE == 10
        or BENCH_MODE == 11
        or BENCH_MODE == 12
    ):
        return run_reddit_coil_strike()

    if BENCH_MODE == 20:
        return run_flekay_axis_greedy()

    if BENCH_MODE == 21:
        return run_flekay_parity_greedy()

    return run_shortcuts()


def continue_benchmark(
    completed_cycles
):
    if BENCH_BONE_TARGET > 0:
        return (
            num_items(Items.Bone)
            < BENCH_BONE_TARGET
            and completed_cycles
            < BENCH_MAX_CYCLES
        )

    return (
        completed_cycles
        < BENCH_CYCLES
    )


def main():
    start_ticks = get_tick_count()
    start_time = get_time()

    completed_cycles = 0

    while continue_benchmark(
        completed_cycles
    ):
        if not setup_cycle(
            completed_cycles == 0
        ):
            quick_print(
                "DINOSAUR BENCH INVALID",
                "setup",
                completed_cycles
            )
            return

        bones_before = num_items(
            Items.Bone
        )

        success = run_one_cycle()

        if not success:
            quick_print(
                "DINOSAUR BENCH INVALID",
                BENCH_MODE,
                BENCH_WORLD_SIZE,
                BENCH_TARGET_PERCENT,
                "tail",
                CURRENT_TAIL_LENGTH - 1,
                "occupied",
                CURRENT_TAIL_LENGTH,
                "cycle",
                completed_cycles
            )

            harvest_tail()
            return

        harvest_tail()

        bones_after = num_items(
            Items.Bone
        )

        expected_cycle_bones = (
            target_tail_length()
            * target_tail_length()
            * 32
        )

        if (
            bones_after
            - bones_before
            != expected_cycle_bones
        ):
            quick_print(
                "DINOSAUR BENCH INVALID",
                "bone-gain",
                BENCH_MODE,
                "setup",
                BENCH_SETUP_MODE,
                "target",
                BENCH_TARGET_PERCENT,
                "tail",
                target_tail_length(),
                "actual_gain",
                bones_after - bones_before,
                "expected_gain",
                expected_cycle_bones
            )

            return

        completed_cycles += 1

        # For the one-cycle board-1 diagnostic, validate the exact
        # current Dinosaur leaderboard Bone threshold.
        if (
            BENCH_BONE_TARGET == 0
            and BENCH_WORLD_SIZE == 32
            and BENCH_TARGET_PERCENT == 100
            and num_items(Items.Bone) < 33488928
        ):
            quick_print(
                "DINOSAUR BENCH INVALID",
                "leaderboard-bones",
                BENCH_MODE,
                "setup",
                BENCH_SETUP_MODE,
                "bones",
                num_items(Items.Bone),
                "required",
                33488928
            )

            return

    if (
        BENCH_BONE_TARGET > 0
        and num_items(Items.Bone)
        < BENCH_BONE_TARGET
    ):
        quick_print(
            "DINOSAUR BENCH INVALID",
            "bone-target-watchdog",
            BENCH_MODE,
            "setup",
            BENCH_SETUP_MODE,
            "cycles",
            completed_cycles,
            "bones",
            num_items(Items.Bone),
            "required",
            BENCH_BONE_TARGET
        )

        return

    elapsed_ticks = (
        get_tick_count()
        - start_ticks
    )

    elapsed_time = (
        get_time()
        - start_time
    )

    quick_print(
        "DINOSAUR BENCH VALID",
        BENCH_MODE,
        "setup",
        BENCH_SETUP_MODE,
        "target",
        BENCH_TARGET_PERCENT,
        "tail",
        CURRENT_TAIL_LENGTH - 1,
        "occupied",
        CURRENT_TAIL_LENGTH,
        "cycles",
        completed_cycles,
        "bone_target",
        BENCH_BONE_TARGET,
        "bones",
        num_items(Items.Bone),
        "ticks",
        elapsed_ticks,
        "time",
        elapsed_time
    )

    if BENCH_VERBOSE:
        quick_print(
            "DINOSAUR BENCH",
            BENCH_MODE,
            "setup",
            BENCH_SETUP_MODE,
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
