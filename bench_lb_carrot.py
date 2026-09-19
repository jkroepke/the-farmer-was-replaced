MODE_NAMES = [
    "carrot-lean",
    "carrot-water25",
    "carrot-water50",
    "carrot-water75",
    "carrot-fert",
    "carrot-water-fert",
    "carrot-safe"
]


def water_limit(mode):
    if mode == 1:
        return 0.25

    if mode == 2:
        return 0.50

    if mode == 3 or mode == 5:
        return 0.75

    return -1


def mode_fertilizer(mode):
    return (
        mode == 4
        or mode == 5
    )


def move_to_column(column):
    world_size = get_world_size()
    current_x = get_pos_x()

    east = (
        column - current_x
    ) % world_size
    west = (
        current_x - column
    ) % world_size

    if east <= west:
        for _ in range(east):
            move(East)
    else:
        for _ in range(west):
            move(West)


def water_tile(mode):
    limit = water_limit(
        mode
    )

    if (
        limit >= 0
        and get_water() < limit
    ):
        use_item(
            Items.Water
        )


def prepare_tile(mode):
    if get_ground_type() != Grounds.Soil:
        till()

    if get_entity_type() != None:
        harvest()

    plant(
        Entities.Carrot
    )

    water_tile(
        mode
    )

    if mode_fertilizer(mode):
        use_item(
            Items.Fertilizer
        )


def service_lean(mode):
    if can_harvest():
        harvest()
        plant(
            Entities.Carrot
        )

    water_tile(
        mode
    )

    if (
        mode_fertilizer(mode)
        and not can_harvest()
    ):
        use_item(
            Items.Fertilizer
        )


def service_safe(mode):
    entity = get_entity_type()

    if (
        entity != None
        and entity != Entities.Carrot
    ):
        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    if get_entity_type() == Entities.Carrot:
        if can_harvest():
            harvest()

    if get_entity_type() == None:
        if get_cost(
            Entities.Carrot
        ) != None:
            plant(
                Entities.Carrot
            )

    water_tile(
        mode
    )


def column_worker(
    mode,
    column,
    target
):
    world_size = get_world_size()

    move_to_column(
        column
    )

    for _ in range(
        world_size
    ):
        prepare_tile(
            mode
        )
        move(
            North
        )

    while num_items(
        Items.Carrot
    ) < target:
        for _ in range(
            world_size
        ):
            if mode == 6:
                service_safe(
                    mode
                )
            else:
                service_lean(
                    mode
                )

            move(
                North
            )

    return True


def tree_worker(
    mode,
    target,
    start,
    count
):
    if count == 1:
        return column_worker(
            mode,
            start,
            target
        )

    second_count = count // 2
    first_count = count - second_count

    child = spawn_drone(
        tree_worker,
        mode,
        target,
        start + first_count,
        second_count
    )

    if child == None:
        return False

    own = tree_worker(
        mode,
        target,
        start,
        first_count
    )

    other = wait_for(
        child
    )

    return own and other


def main():
    if get_world_size() != 32:
        quick_print(
            "LBCAR INVALID WORLD",
            get_world_size()
        )
        return

    if max_drones() < 32:
        quick_print(
            "LBCAR INVALID DRONES",
            max_drones()
        )
        return

    start = num_items(
        Items.Carrot
    )
    target = (
        start
        + BENCH_TARGET_GAIN
    )

    start_time = get_time()
    start_ticks = get_tick_count()

    success = tree_worker(
        BENCH_MODE,
        target,
        0,
        32
    )

    elapsed = (
        get_time()
        - start_time
    )
    ticks = (
        get_tick_count()
        - start_ticks
    )
    gain = (
        num_items(
            Items.Carrot
        )
        - start
    )

    valid = (
        success
        and gain >= BENCH_TARGET_GAIN
    )

    quick_print(
        "LBCAR RESULT",
        MODE_NAMES[BENCH_MODE],
        "gain",
        gain,
        "ticks",
        ticks,
        "elapsed",
        elapsed,
        "hay-left",
        num_items(Items.Hay),
        "wood-left",
        num_items(Items.Wood),
        "water-left",
        num_items(Items.Water),
        "fert-left",
        num_items(Items.Fertilizer),
        "power-left",
        num_items(Items.Power),
        "valid",
        valid
    )


if __name__ == "__main__":
    main()
