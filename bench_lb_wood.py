MODE_NAMES = [
    "checker-grass-lean",
    "checker-bush-lean",
    "checker-grass-water75",
    "checker-bush-water75",
    "checker-grass-fert",
    "checker-grass-water-fert",
    "full-tree-lean",
    "full-tree-water75",
    "checker-grass-safe"
]


def mode_layout(mode):
    if mode == 1 or mode == 3:
        return 1

    if mode == 6 or mode == 7:
        return 2

    return 0


def mode_water(mode):
    return (
        mode == 2
        or mode == 3
        or mode == 5
        or mode == 7
    )


def mode_fertilizer(mode):
    return (
        mode == 4
        or mode == 5
    )


def water_tile():
    if get_water() < 0.75:
        use_item(
            Items.Water
        )


def wanted_entity(
    layout,
    x,
    y
):
    if layout == 2:
        return Entities.Tree

    if (x + y) % 2 == 0:
        return Entities.Tree

    if layout == 1:
        return Entities.Bush

    return Entities.Grass


def prepare_tile(
    mode,
    x,
    y
):
    layout = mode_layout(
        mode
    )
    wanted = wanted_entity(
        layout,
        x,
        y
    )

    if wanted == Entities.Grass:
        if get_ground_type() != Grounds.Grassland:
            till()

    else:
        # Leaderboard starts with Grass on Grassland. Destructive harvest is
        # intentional during one-time setup; waiting for maturity only delays
        # the benchmark.
        if get_entity_type() != None:
            harvest()

        plant(
            wanted
        )

    if mode_water(mode):
        water_tile()

    if mode_fertilizer(mode):
        use_item(
            Items.Fertilizer
        )


def service_safe(
    mode,
    x,
    y
):
    layout = mode_layout(
        mode
    )
    wanted = wanted_entity(
        layout,
        x,
        y
    )
    entity = get_entity_type()

    if wanted == Entities.Grass:
        if (
            entity != None
            and entity != Entities.Grass
        ):
            harvest()

        if get_ground_type() != Grounds.Grassland:
            till()

        if can_harvest():
            harvest()

        return

    if entity == wanted:
        if can_harvest():
            harvest()
            plant(
                wanted
            )

        return

    if entity != None:
        harvest()

    plant(
        wanted
    )


def service_lean(
    mode,
    x,
    y
):
    layout = mode_layout(
        mode
    )
    wanted = wanted_entity(
        layout,
        x,
        y
    )

    if can_harvest():
        harvest()

        if wanted != Entities.Grass:
            plant(
                wanted
            )

    if mode_water(mode):
        water_tile()

    if (
        mode_fertilizer(mode)
        and not can_harvest()
    ):
        use_item(
            Items.Fertilizer
        )


def column_worker(
    mode,
    column,
    target
):
    world_size = get_world_size()

    move(East) if False else None
    # All child drones start on the root tile. Move once to the owned column.
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

    for y in range(
        world_size
    ):
        prepare_tile(
            mode,
            column,
            y
        )
        move(
            North
        )

    while num_items(
        Items.Wood
    ) < target:
        for y in range(
            world_size
        ):
            if mode == 8:
                service_safe(
                    mode,
                    column,
                    y
                )
            else:
                service_lean(
                    mode,
                    column,
                    y
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
            "LBWOOD INVALID WORLD",
            get_world_size()
        )
        return

    if max_drones() < 32:
        quick_print(
            "LBWOOD INVALID DRONES",
            max_drones()
        )
        return

    start = num_items(
        Items.Wood
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
            Items.Wood
        )
        - start
    )

    valid = (
        success
        and gain >= BENCH_TARGET_GAIN
    )

    quick_print(
        "LBWOOD RESULT",
        MODE_NAMES[BENCH_MODE],
        "gain",
        gain,
        "ticks",
        ticks,
        "elapsed",
        elapsed,
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
