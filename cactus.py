import utils


def can_start():
    world_size = utils.size()

    fields = (
        world_size
        * world_size
    )

    return utils.can_afford(
        Entities.Cactus,
        fields
    )


def _reroll_needed(value, x, y, size):
    half = size // 2

    if x < half and y < half:
        return value >= 5

    if x >= half and y >= half:
        return value < 5

    return value < 2 or value > 7


def _move_x(current, target, size):
    east = (target - current) % size
    west = (current - target) % size

    if east <= west:
        for _ in range(east):
            move(East)
    else:
        for _ in range(west):
            move(West)

    return target


def _move_y(current, target, size):
    north = (target - current) % size
    south = (current - target) % size

    if north <= south:
        for _ in range(north):
            move(North)
    else:
        for _ in range(south):
            move(South)

    return target


def _ensure_cactus():
    entity = get_entity_type()

    if entity == Entities.Cactus:
        return True

    if entity != None:
        if can_harvest():
            harvest()
        else:
            till()
            till()

    if get_ground_type() != Grounds.Soil:
        till()

    return plant(
        Entities.Cactus
    )


def _reroll_inline(x, y, size):
    value = measure()

    while _reroll_needed(
        value,
        x,
        y,
        size
    ):
        while not can_harvest():
            pass

        # Do not destroy a usable Cactus if the replacement is currently
        # unaffordable. Keeping this value is slower to sort, but correct.
        if not utils.can_afford(
            Entities.Cactus
        ):
            return value

        till()
        till()

        if not plant(
            Entities.Cactus
        ):
            return value

        if num_items(Items.Water) > 0:
            use_item(Items.Water)

        value = measure()

    return value


def _wait_row(y, size):
    utils.move_to(
        0,
        y
    )

    for _ in range(size):
        while not can_harvest():
            pass

        move(East)


def _insertion_row(y, values, size):
    current_x = get_pos_x()

    for i in range(
        1,
        size
    ):
        j = i

        while (
            j > 0
            and values[j] < values[j - 1]
        ):
            current_x = _move_x(
                current_x,
                j - 1,
                size
            )

            swap(East)

            value = values[j]
            values[j] = values[j - 1]
            values[j - 1] = value

            j -= 1

    utils.move_to(
        0,
        y
    )


def _insertion_column(x, size):
    values = []

    utils.move_to(
        x,
        0
    )

    for _ in range(size):
        values.append(
            measure()
        )

        move(North)

    current_y = get_pos_y()

    for i in range(
        1,
        size
    ):
        j = i

        while (
            j > 0
            and values[j] < values[j - 1]
        ):
            current_y = _move_y(
                current_y,
                j - 1,
                size
            )

            swap(North)

            value = values[j]
            values[j] = values[j - 1]
            values[j - 1] = value

            j -= 1

    utils.move_to(
        x,
        0
    )


# ==================================================
# FULL-DRONE PLACED WORKERS
# ==================================================

def _batched_row_job(
    y,
    size,
    reroll,
    wait_ready
):
    values = []
    redo = []

    utils.move_to(
        0,
        y
    )

    for x in range(size):
        if get_ground_type() != Grounds.Soil:
            till()

        if get_entity_type() != Entities.Cactus:
            if not plant(
                Entities.Cactus
            ):
                return False

        level = measure()

        values.append(
            level
        )

        if (
            reroll
            and _reroll_needed(
                level,
                x,
                y,
                size
            )
        ):
            redo.append(
                x
            )

        move(East)

    # Revisit rejected positions as a batch. While this worker handles one
    # tile, the other rejected Cacti keep growing in parallel.
    while len(redo) > 0:
        index = 0
        length = len(redo)

        for _ in range(length):
            if index >= len(redo):
                break

            x = redo[index]

            utils.move_to(
                x,
                y
            )

            while not can_harvest():
                pass

            if not utils.can_afford(
                Entities.Cactus
            ):
                redo.pop(
                    index
                )
                continue

            till()
            till()

            if not plant(
                Entities.Cactus
            ):
                return False

            if num_items(Items.Water) > 0:
                use_item(
                    Items.Water
                )

            level = measure()
            values[x] = level

            if _reroll_needed(
                level,
                x,
                y,
                size
            ):
                index += 1
            else:
                redo.pop(
                    index
                )

    _insertion_row(
        y,
        values,
        size
    )

    if wait_ready:
        _wait_row(
            y,
            size
        )

    return True


def _batched_row_worker(
    index,
    count,
    size,
    reroll,
    wait_ready
):
    y = index

    while y < size:
        if not _batched_row_job(
            y,
            size,
            reroll,
            wait_ready
        ):
            return False

        y += count

    return True


def _column_worker(
    index,
    count,
    size,
    unused1,
    unused2
):
    x = index

    while x < size:
        _insertion_column(
            x,
            size
        )

        x += count

    return True


def _placed_wave(
    worker,
    size,
    arg1,
    arg2,
    direction
):
    worker_count = min(
        size,
        max_drones()
    )

    utils.move_to(
        0,
        0
    )

    handles = []

    for index in range(
        worker_count - 1
    ):
        drone = spawn_drone(
            worker,
            index,
            worker_count,
            size,
            arg1,
            arg2
        )

        if drone == None:
            for active in handles:
                wait_for(
                    active
                )

            return False

        handles.append(
            drone
        )

        move(
            direction
        )

    ok = worker(
        worker_count - 1,
        worker_count,
        size,
        arg1,
        arg2
    )

    for drone in handles:
        if not wait_for(
            drone
        ):
            ok = False

    return ok


def _run_placed(size):
    reroll = size == 32

    # On smaller measured worlds rerolling lost more time than it saved.
    # They therefore wait for ordinary Cactus maturity before the column
    # phase. The 32x32 reroll loop already provides sufficient growth time.
    wait_ready = not reroll

    if not _placed_wave(
        _batched_row_worker,
        size,
        reroll,
        wait_ready,
        North
    ):
        return False

    if not _placed_wave(
        _column_worker,
        size,
        False,
        False,
        East
    ):
        return False

    utils.move_to(
        size - 1,
        size - 1
    )

    if not can_harvest():
        return False

    return harvest()


# ==================================================
# FEWER-DRONE FALLBACK
# ==================================================

def _scan_row(
    y,
    size,
    reroll
):
    values = []

    utils.move_to(
        0,
        y
    )

    for x in range(size):
        if not _ensure_cactus():
            return []

        utils.water()

        value = measure()

        if reroll:
            value = _reroll_inline(
                x,
                y,
                size
            )

        values.append(
            value
        )

        move(East)

    return values


def _fallback_row_worker(
    index,
    count,
    size,
    reroll,
    unused
):
    y = index

    while y < size:
        values = _scan_row(
            y,
            size,
            reroll
        )

        if len(values) != size:
            return False

        _insertion_row(
            y,
            values,
            size
        )

        _wait_row(
            y,
            size
        )

        y += count

    return True


def _wave(
    worker,
    size,
    arg1,
    arg2
):
    worker_count = min(
        size,
        max_drones()
    )

    handles = []

    for index in range(
        1,
        worker_count
    ):
        drone = spawn_drone(
            worker,
            index,
            worker_count,
            size,
            arg1,
            arg2
        )

        if drone == None:
            for active in handles:
                wait_for(
                    active
                )

            return False

        handles.append(
            drone
        )

    ok = worker(
        0,
        worker_count,
        size,
        arg1,
        arg2
    )

    for drone in handles:
        if not wait_for(
            drone
        ):
            ok = False

    return ok


def _run_fallback(size):
    reroll = size == 32

    if not _wave(
        _fallback_row_worker,
        size,
        reroll,
        False
    ):
        return False

    if not _wave(
        _column_worker,
        size,
        False,
        False
    ):
        return False

    utils.move_to(
        0,
        0
    )

    if not can_harvest():
        return False

    return harvest()


# ==================================================
# PRODUCTION ENTRYPOINT
# ==================================================

def run(reuse_field = False):
    if not can_start():
        return False

    if not reuse_field:
        clear()

    size = utils.size()

    # This fast path is benchmark-proven for 6x6, 16x16 and 32x32 when
    # enough drones exist to place one worker on every row/column.
    if max_drones() >= size:
        return _run_placed(
            size
        )

    # With fewer drones keep the previously validated generalized two-wave
    # architecture. Each worker owns multiple rows/columns by index += count.
    return _run_fallback(
        size
    )
