# Sunflower leaderboard algorithms.
#
# Goal:
#   num_items(Items.Power) >= 100000
#
# The ordered modes keep a global petal-order barrier:
#   1. measure every live Sunflower
#   2. harvest 15 -> 7
#   3. finish one petal tier before starting the next
#   4. leave exactly nine Sunflowers so the last harvested flower still sees
#      at least ten Sunflowers before it is removed
#   5. only replant after the complete ordered harvest phase
#
# Drones do not share Python memory. Fresh workers receive a snapshot of the
# current globals when they are spawned. The controller owns all authoritative
# petal state and rebuilds it from worker return values after replant phases.

MODE_NAMES = [
    "tier-tree-no-care",
    "tier-tree-water",
    "tier-tree-water-fertilizer",
    "equal7-tree-water",
    "equal7-tree-water-fertilizer",
    "dumb-tree-water",
    "dumb-tree-water-fertilizer",
    "tier-linear-water"
]

MIN_PETALS = 7
MAX_PETALS = 15
MIN_REMAINING = 9

TARGET_POWER = 100000
WORLD_SIZE = 0
PETALS = []

USE_WATER = False
USE_FERTILIZER = False
USE_TREE = True


def move_to(target_x, target_y):
    current_x = get_pos_x()

    east = (
        target_x
        - current_x
    ) % WORLD_SIZE

    west = (
        current_x
        - target_x
    ) % WORLD_SIZE

    if east <= west:
        for _ in range(east):
            move(East)
    else:
        for _ in range(west):
            move(West)

    current_y = get_pos_y()

    north = (
        target_y
        - current_y
    ) % WORLD_SIZE

    south = (
        current_y
        - target_y
    ) % WORLD_SIZE

    if north <= south:
        for _ in range(north):
            move(North)
    else:
        for _ in range(south):
            move(South)


def water_if_useful():
    if not USE_WATER:
        return

    if num_items(
        Items.Water
    ) <= 0:
        return

    if get_water() < 0.7:
        use_item(
            Items.Water
        )


def wait_until_ready():
    # Complete the selected petal tier atomically. Stopping workers here when
    # the Power target is crossed would leave the controller's PETALS cache
    # claiming that unharvested flowers were removed.
    while not can_harvest():
        if (
            USE_FERTILIZER
            and num_items(
                Items.Fertilizer
            ) > 0
        ):
            use_item(
                Items.Fertilizer
            )

    return True


def prepare_random_column(column):
    move_to(
        column,
        0
    )

    result = []

    for _ in range(
        WORLD_SIZE
    ):
        entity = get_entity_type()

        if entity != None:
            harvest()

        if get_ground_type() != Grounds.Soil:
            till()

        if not plant(
            Entities.Sunflower
        ):
            return None

        water_if_useful()

        result.append(
            measure()
        )

        move(
            North
        )

    return result


def prepare_equal7_column(column):
    move_to(
        column,
        0
    )

    result = []

    for _ in range(
        WORLD_SIZE
    ):
        entity = get_entity_type()

        if entity != None:
            harvest()

        if get_ground_type() != Grounds.Soil:
            till()

        accepted = False

        while not accepted:
            if not plant(
                Entities.Sunflower
            ):
                return None

            petals = measure()

            if petals == 7:
                water_if_useful()
                accepted = True
            else:
                # Destroy rejected rolls while they are still immature.
                # Rejected rolls are intentionally not watered.
                harvest()

        result.append(
            7
        )

        move(
            North
        )

    return result


def prepare_tree(
    start,
    count,
    equal7
):
    if count == 1:
        if equal7:
            column = prepare_equal7_column(
                start
            )
        else:
            column = prepare_random_column(
                start
            )

        return [
            [
                start,
                column
            ]
        ]

    second_count = count // 2
    first_count = (
        count
        - second_count
    )

    drone = spawn_drone(
        prepare_tree,
        start + first_count,
        second_count,
        equal7
    )

    if drone == None:
        return None

    own = prepare_tree(
        start,
        first_count,
        equal7
    )

    child = wait_for(
        drone
    )

    if (
        own == None
        or child == None
    ):
        return None

    for item in child:
        own.append(
            item
        )

    return own


def prepare_linear(equal7):
    handles = []
    column = 1

    while column < WORLD_SIZE:
        if equal7:
            drone = spawn_drone(
                prepare_equal7_column,
                column
            )
        else:
            drone = spawn_drone(
                prepare_random_column,
                column
            )

        if drone == None:
            return None

        handles.append(
            [
                column,
                drone
            ]
        )

        column += 1

    if equal7:
        own = prepare_equal7_column(
            0
        )
    else:
        own = prepare_random_column(
            0
        )

    if own == None:
        return None

    result = [
        [
            0,
            own
        ]
    ]

    for item in handles:
        value = wait_for(
            item[1]
        )

        if value == None:
            return None

        result.append(
            [
                item[0],
                value
            ]
        )

    return result


def install_columns(records):
    global PETALS

    PETALS = []

    for _ in range(
        WORLD_SIZE
    ):
        PETALS.append(
            None
        )

    for record in records:
        PETALS[
            record[0]
        ] = record[1]

    for column in PETALS:
        if column == None:
            return False

    return True


def prepare_field(equal7):
    if USE_TREE:
        records = prepare_tree(
            0,
            WORLD_SIZE,
            equal7
        )
    else:
        records = prepare_linear(
            equal7
        )

    if records == None:
        return False

    return install_columns(
        records
    )


def normalize_kept_petals():
    column = 0

    while column < WORLD_SIZE:
        row = 0

        while row < WORLD_SIZE:
            petals = PETALS[
                column
            ][
                row
            ]

            if petals < 0:
                PETALS[
                    column
                ][
                    row
                ] = -petals

            row += 1

        column += 1


def choose_harvest_floor():
    counts = []

    for _ in range(
        MAX_PETALS
        - MIN_PETALS
        + 1
    ):
        counts.append(
            0
        )

    column = 0

    while column < WORLD_SIZE:
        row = 0

        while row < WORLD_SIZE:
            petals = PETALS[
                column
            ][
                row
            ]

            if petals < 0:
                petals = -petals

            counts[
                petals
                - MIN_PETALS
            ] += 1

            row += 1

        column += 1

    lower_count = 0
    petals = MIN_PETALS

    while petals <= MAX_PETALS:
        count = counts[
            petals
            - MIN_PETALS
        ]

        if (
            lower_count
            + count
            >= MIN_REMAINING
        ):
            keep_in_floor = (
                MIN_REMAINING
                - lower_count
            )

            return (
                petals,
                keep_in_floor
            )

        lower_count += count
        petals += 1

    return (
        MAX_PETALS,
        0
    )


def mark_floor_kept(
    floor,
    keep_count
):
    if keep_count <= 0:
        return

    column = 0

    while (
        column < WORLD_SIZE
        and keep_count > 0
    ):
        row = 0

        while (
            row < WORLD_SIZE
            and keep_count > 0
        ):
            if PETALS[
                column
            ][
                row
            ] == floor:
                PETALS[
                    column
                ][
                    row
                ] = -floor

                keep_count -= 1

            row += 1

        column += 1


def harvest_tier_column(
    column,
    tier
):
    row = 0

    while row < WORLD_SIZE:
        if PETALS[
            column
        ][
            row
        ] == tier:
            move_to(
                column,
                row
            )

            if not wait_until_ready():
                return False

            harvest()

        row += 1

    return True


def harvest_tree(
    start,
    count,
    tier
):
    if count == 1:
        return harvest_tier_column(
            start,
            tier
        )

    second_count = count // 2
    first_count = (
        count
        - second_count
    )

    drone = spawn_drone(
        harvest_tree,
        start + first_count,
        second_count,
        tier
    )

    if drone == None:
        return False

    own = harvest_tree(
        start,
        first_count,
        tier
    )

    child = wait_for(
        drone
    )

    return (
        own
        and child
    )


def harvest_linear(tier):
    handles = []
    column = 1

    while column < WORLD_SIZE:
        drone = spawn_drone(
            harvest_tier_column,
            column,
            tier
        )

        if drone == None:
            return False

        handles.append(
            drone
        )

        column += 1

    own = harvest_tier_column(
        0,
        tier
    )

    for drone in handles:
        if not wait_for(
            drone
        ):
            own = False

    return own


def harvest_tier(tier):
    if USE_TREE:
        return harvest_tree(
            0,
            WORLD_SIZE,
            tier
        )

    return harvest_linear(
        tier
    )


def mark_tier_harvested(tier):
    column = 0

    while column < WORLD_SIZE:
        row = 0

        while row < WORLD_SIZE:
            if PETALS[
                column
            ][
                row
            ] == tier:
                PETALS[
                    column
                ][
                    row
                ] = 0

            row += 1

        column += 1


def replant_random_column(column):
    result = []
    row = 0

    while row < WORLD_SIZE:
        petals = PETALS[
            column
        ][
            row
        ]

        if petals == 0:
            move_to(
                column,
                row
            )

            if not plant(
                Entities.Sunflower
            ):
                return None

            water_if_useful()

            petals = measure()

        result.append(
            petals
        )

        row += 1

    return result


def replant_equal7_column(column):
    result = []
    row = 0

    while row < WORLD_SIZE:
        petals = PETALS[
            column
        ][
            row
        ]

        if petals == 0:
            move_to(
                column,
                row
            )

            accepted = False

            while not accepted:
                if not plant(
                    Entities.Sunflower
                ):
                    return None

                petals = measure()

                if petals == 7:
                    water_if_useful()
                    accepted = True
                else:
                    harvest()

        result.append(
            petals
        )

        row += 1

    return result


def replant_tree(
    start,
    count,
    equal7
):
    if count == 1:
        if equal7:
            column = replant_equal7_column(
                start
            )
        else:
            column = replant_random_column(
                start
            )

        return [
            [
                start,
                column
            ]
        ]

    second_count = count // 2
    first_count = (
        count
        - second_count
    )

    drone = spawn_drone(
        replant_tree,
        start + first_count,
        second_count,
        equal7
    )

    if drone == None:
        return None

    own = replant_tree(
        start,
        first_count,
        equal7
    )

    child = wait_for(
        drone
    )

    if (
        own == None
        or child == None
    ):
        return None

    for item in child:
        own.append(
            item
        )

    return own


def replant_linear(equal7):
    handles = []
    column = 1

    while column < WORLD_SIZE:
        if equal7:
            drone = spawn_drone(
                replant_equal7_column,
                column
            )
        else:
            drone = spawn_drone(
                replant_random_column,
                column
            )

        if drone == None:
            return None

        handles.append(
            [
                column,
                drone
            ]
        )

        column += 1

    if equal7:
        own = replant_equal7_column(
            0
        )
    else:
        own = replant_random_column(
            0
        )

    if own == None:
        return None

    result = [
        [
            0,
            own
        ]
    ]

    for item in handles:
        value = wait_for(
            item[1]
        )

        if value == None:
            return None

        result.append(
            [
                item[0],
                value
            ]
        )

    return result


def replant_field(equal7):
    if USE_TREE:
        records = replant_tree(
            0,
            WORLD_SIZE,
            equal7
        )
    else:
        records = replant_linear(
            equal7
        )

    if records == None:
        return False

    return install_columns(
        records
    )


def run_ordered(equal7):
    if not prepare_field(
        equal7
    ):
        return False

    while num_items(
        Items.Power
    ) < TARGET_POWER:
        normalize_kept_petals()

        floor, keep_count = choose_harvest_floor()

        mark_floor_kept(
            floor,
            keep_count
        )

        tier = MAX_PETALS

        while tier >= floor:
            if not harvest_tier(
                tier
            ):
                return False

            if num_items(
                Items.Power
            ) >= TARGET_POWER:
                return True

            mark_tier_harvested(
                tier
            )

            tier -= 1

        if not replant_field(
            equal7
        ):
            return False

    return True


def dumb_column_worker(column):
    move_to(
        column,
        0
    )

    row = 0

    while row < WORLD_SIZE:
        if get_ground_type() != Grounds.Soil:
            till()

        if get_entity_type() == None:
            if not plant(
                Entities.Sunflower
            ):
                return False

            water_if_useful()

        move(
            North
        )

        row += 1

    while num_items(
        Items.Power
    ) < TARGET_POWER:
        move_to(
            column,
            0
        )

        row = 0

        while (
            row < WORLD_SIZE
            and num_items(
                Items.Power
            ) < TARGET_POWER
        ):
            entity = get_entity_type()

            if entity != Entities.Sunflower:
                if entity != None:
                    harvest()

                if get_ground_type() != Grounds.Soil:
                    till()

                if not plant(
                    Entities.Sunflower
                ):
                    return False

                water_if_useful()

            elif can_harvest():
                harvest()

                if num_items(
                    Items.Power
                ) >= TARGET_POWER:
                    return True

                if not plant(
                    Entities.Sunflower
                ):
                    return False

                water_if_useful()

            elif (
                USE_FERTILIZER
                and num_items(
                    Items.Fertilizer
                ) > 0
            ):
                use_item(
                    Items.Fertilizer
                )

            move(
                North
            )

            row += 1

    return True


def dumb_tree(
    start,
    count
):
    if count == 1:
        return dumb_column_worker(
            start
        )

    second_count = count // 2
    first_count = (
        count
        - second_count
    )

    drone = spawn_drone(
        dumb_tree,
        start + first_count,
        second_count
    )

    if drone == None:
        return False

    own = dumb_tree(
        start,
        first_count
    )

    child = wait_for(
        drone
    )

    return (
        own
        and child
    )


def configure_mode(mode):
    global USE_WATER
    global USE_FERTILIZER
    global USE_TREE

    USE_WATER = False
    USE_FERTILIZER = False
    USE_TREE = True

    if mode == 0:
        return True

    if mode == 1:
        USE_WATER = True
        return True

    if mode == 2:
        USE_WATER = True
        USE_FERTILIZER = True
        return True

    if mode == 3:
        USE_WATER = True
        return True

    if mode == 4:
        USE_WATER = True
        USE_FERTILIZER = True
        return True

    if mode == 5:
        USE_WATER = True
        return True

    if mode == 6:
        USE_WATER = True
        USE_FERTILIZER = True
        return True

    if mode == 7:
        USE_WATER = True
        USE_TREE = False
        return True

    return False


def run(
    mode,
    target = 100000
):
    global TARGET_POWER
    global WORLD_SIZE
    global PETALS

    TARGET_POWER = target
    WORLD_SIZE = get_world_size()
    PETALS = []

    if WORLD_SIZE * WORLD_SIZE < 10:
        return False

    if not configure_mode(
        mode
    ):
        return False

    if mode == 3 or mode == 4:
        return run_ordered(
            True
        )

    if mode == 5 or mode == 6:
        return dumb_tree(
            0,
            WORLD_SIZE
        )

    return run_ordered(
        False
    )
