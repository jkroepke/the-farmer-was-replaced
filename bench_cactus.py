import cactus
import utils


MODE_NAMES = [
    "current-production",
    "two-wave-bubble-reset",
    "two-wave-insertion-reset",
    "two-wave-insertion-reuse",
    "two-wave-insertion-reroll-reuse",
    "tstambaugh-reference-32",
    "nql1314-reference",
    "tstambaugh-placed-generalized",
    "adaptive-placed-pool"
]


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

    return plant(Entities.Cactus)


def _reroll_needed(value, x, y, size):
    half = size // 2

    if x < half and y < half:
        return value >= 5

    if x >= half and y >= half:
        return value < 5

    return value < 2 or value > 7


def _reroll(x, y, size):
    value = measure()

    while _reroll_needed(value, x, y, size):
        while not can_harvest():
            pass

        # Current game behavior only gives a new Cactus value after the
        # old plant matured. Toggle twice to destroy it and keep Soil.
        till()
        till()
        plant(Entities.Cactus)
        utils.water()
        value = measure()

    return value


def _scan_row(y, size, reroll):
    values = []
    utils.move_to(0, y)

    for x in range(size):
        if not _ensure_cactus():
            return []

        utils.water()
        value = measure()

        if reroll:
            value = _reroll(
                x,
                y,
                size
            )

        values.append(value)
        move(East)

    return values


def _wait_row(y, size):
    utils.move_to(0, y)

    for _ in range(size):
        while not can_harvest():
            pass

        move(East)


def _insertion_row(y, values, size):
    current_x = 0

    for i in range(1, size):
        j = i

        while j > 0 and values[j] < values[j - 1]:
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

    utils.move_to(0, y)


def _insertion_column(x, size):
    values = []
    utils.move_to(x, 0)

    for _ in range(size):
        values.append(measure())
        move(North)

    current_y = 0

    for i in range(1, size):
        j = i

        while j > 0 and values[j] < values[j - 1]:
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

    utils.move_to(x, 0)


def _bubble_row(y, size):
    for pass_index in range(size - 1):
        utils.move_to(0, y)
        swapped = False

        for _ in range(size - 1 - pass_index):
            if measure() > measure(East):
                swap(East)
                swapped = True

            move(East)

        if not swapped:
            break

    utils.move_to(0, y)


def _bubble_column(x, size):
    for pass_index in range(size - 1):
        utils.move_to(x, 0)
        swapped = False

        for _ in range(size - 1 - pass_index):
            if measure() > measure(North):
                swap(North)
                swapped = True

            move(North)

        if not swapped:
            break

    utils.move_to(x, 0)


def _row_worker(index, count, size, sort_mode, reroll):
    y = index

    while y < size:
        values = _scan_row(
            y,
            size,
            reroll
        )

        if len(values) != size:
            return False

        if sort_mode == 0:
            _bubble_row(y, size)
        else:
            _insertion_row(
                y,
                values,
                size
            )

        _wait_row(y, size)
        y += count

    return True


def _column_worker(index, count, size, sort_mode, unused):
    x = index

    while x < size:
        if sort_mode == 0:
            _bubble_column(x, size)
        else:
            _insertion_column(x, size)

        x += count

    return True


def _wave(worker, size, arg1, arg2):
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
            return False

        handles.append(drone)

    ok = worker(
        0,
        worker_count,
        size,
        arg1,
        arg2
    )

    for drone in handles:
        if not wait_for(drone):
            ok = False

    return ok


def _harvest_sorted():
    utils.move_to(0, 0)

    if not can_harvest():
        return False

    return harvest()


def run_two_wave(sort_mode, reroll, reset_field):
    size = utils.size()

    if reset_field:
        clear()

    if not _wave(
        _row_worker,
        size,
        sort_mode,
        reroll
    ):
        return False

    if not _wave(
        _column_worker,
        size,
        sort_mode,
        False
    ):
        return False

    return _harvest_sorted()


# ==================================================
# nql1314 source-near reference
# ==================================================

def _nql_sort_row(y, size):
    while True:
        swapped = False

        for x in range(size - 1):
            utils.move_to(x, y)

            if measure() > measure(East):
                swap(East)
                swapped = True

        if not swapped:
            return True


def _nql_sort_column(x, size):
    while True:
        swapped = False

        for y in range(size - 1):
            utils.move_to(x, y)

            if measure() > measure(North):
                swap(North)
                swapped = True

        if not swapped:
            return True


def _nql_plant_worker(index, count, size, unused1, unused2):
    y = index

    while y < size:
        utils.move_to(0, y)

        for _ in range(size):
            if get_ground_type() != Grounds.Soil:
                till()

            if get_entity_type() != Entities.Cactus:
                plant(Entities.Cactus)

            move(East)

        y += count

    return True


def _nql_row_worker(index, count, size, unused1, unused2):
    y = index

    while y < size:
        _nql_sort_row(y, size)
        y += count

    return True


def _nql_column_worker(index, count, size, unused1, unused2):
    x = index

    while x < size:
        _nql_sort_column(x, size)
        x += count

    return True


def run_nql_reference():
    clear()
    size = utils.size()

    if not _wave(
        _nql_plant_worker,
        size,
        False,
        False
    ):
        return False

    if not _wave(
        _nql_row_worker,
        size,
        False,
        False
    ):
        return False

    if not _wave(
        _nql_column_worker,
        size,
        False,
        False
    ):
        return False

    return _harvest_sorted()


# ==================================================
# tstambaugh92 source-near 32x32 reference
# ==================================================

def _reference_insert_sort(values, horizontal):
    size = len(values)

    for i in range(1, size):
        j = i

        while j > 0 and values[j][1] < values[j - 1][1]:
            x, y = values[j - 1][0]
            utils.move_to(x, y)

            if horizontal:
                swap(East)
            else:
                swap(North)

            value = values[j][1]
            values[j][1] = values[j - 1][1]
            values[j - 1][1] = value
            j -= 1


def _reference_row_job():
    size = utils.size()
    y = get_pos_y()
    values = []
    redo = []

    for x in range(size):
        till()
        plant(Entities.Cactus)
        level = measure()

        if _reroll_needed(
            level,
            x,
            y,
            size
        ):
            redo.append((x, y))

        values.append(
            [
                (x, y),
                level
            ]
        )

        move(East)

    while len(redo) > 0:
        index = 0
        length = len(redo)

        for _ in range(length):
            if index >= len(redo):
                break

            target = redo[index]
            utils.move_to(
                target[0],
                target[1]
            )

            while not can_harvest():
                pass

            till()
            till()
            plant(Entities.Cactus)
            use_item(Items.Water)
            level = measure()

            values[
                target[0]
            ][1] = level

            if _reroll_needed(
                level,
                target[0],
                y,
                size
            ):
                index += 1
            else:
                redo.pop(index)

    _reference_insert_sort(
        values,
        True
    )

    return True


def _reference_column_job():
    size = utils.size()
    x = get_pos_x()
    values = []

    for y in range(size):
        values.append(
            [
                (x, y),
                measure()
            ]
        )

        move(North)

    _reference_insert_sort(
        values,
        False
    )

    return True


def run_tstambaugh_reference():
    size = utils.size()

    if size != 32 or max_drones() < 32:
        return False

    clear()
    handles = []

    for _ in range(size - 1):
        drone = spawn_drone(
            _reference_row_job
        )

        if drone == None:
            return False

        handles.append(drone)
        move(North)

    _reference_row_job()

    for drone in handles:
        if not wait_for(drone):
            return False

    utils.move_to(0, 0)
    handles = []

    for _ in range(size - 1):
        drone = spawn_drone(
            _reference_column_job
        )

        if drone == None:
            return False

        handles.append(drone)
        move(East)

    _reference_column_job()

    for drone in handles:
        if not wait_for(drone):
            return False

    utils.move_to(
        size - 1,
        size - 1
    )

    if not can_harvest():
        return False

    return harvest()



# ==================================================
# generalized Tstambaugh-style placed worker pool
# ==================================================

def _batched_row_job(y, size, reroll, wait_ready):
    values = []
    redo = []

    utils.move_to(0, y)

    for x in range(size):
        if get_ground_type() != Grounds.Soil:
            till()

        if get_entity_type() != Entities.Cactus:
            if not plant(Entities.Cactus):
                return False

        level = measure()
        values.append(level)

        if reroll and _reroll_needed(
            level,
            x,
            y,
            size
        ):
            redo.append(x)

        move(East)

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

            # A mature Cactus must be destroyed before a replant gets a
            # fresh random size. Two tills remove it and restore Soil.
            till()
            till()

            if not plant(Entities.Cactus):
                return False

            use_item(Items.Water)
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
                redo.pop(index)

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


def _placed_wave(
    worker,
    size,
    arg1,
    arg2,
    column_phase
):
    worker_count = min(
        size,
        max_drones()
    )

    if worker_count < 1:
        return False

    utils.move_to(
        0,
        0
    )

    handles = []

    # Spawn each worker directly on its first owned row/column. This keeps
    # the source-reference locality instead of spawning every drone at 0,0
    # and paying a separate move_to() afterward.
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
                wait_for(active)

            return False

        handles.append(drone)

        if column_phase:
            move(East)
        else:
            move(North)

    ok = worker(
        worker_count - 1,
        worker_count,
        size,
        arg1,
        arg2
    )

    for drone in handles:
        if not wait_for(drone):
            ok = False

    return ok


def _harvest_sorted_top_right(size):
    utils.move_to(
        size - 1,
        size - 1
    )

    if not can_harvest():
        return False

    return harvest()


def run_placed_batched(
    reroll,
    wait_ready,
    reset_field
):
    size = utils.size()

    if reset_field:
        clear()

    if not _placed_wave(
        _batched_row_worker,
        size,
        reroll,
        wait_ready,
        False
    ):
        return False

    if not _placed_wave(
        _column_worker,
        size,
        1,
        False,
        True
    ):
        return False

    return _harvest_sorted_top_right(
        size
    )


def run_adaptive_placed(cycle):
    size = utils.size()

    # The 32x32 benchmark is the only measured case where rerolling is
    # currently proven beneficial. Smaller measured worlds were slower.
    reroll = size == 32
    wait_ready = not reroll

    return run_placed_batched(
        reroll,
        wait_ready,
        cycle == 0
    )

def run_cycle(mode, cycle):
    if mode == 0:
        return cactus.run()

    if mode == 1:
        return run_two_wave(
            0,
            False,
            True
        )

    if mode == 2:
        return run_two_wave(
            1,
            False,
            True
        )

    if mode == 3:
        return run_two_wave(
            1,
            False,
            cycle == 0
        )

    if mode == 4:
        return run_two_wave(
            1,
            True,
            cycle == 0
        )

    if mode == 5:
        return run_tstambaugh_reference()

    if mode == 6:
        return run_nql_reference()

    if mode == 7:
        return run_placed_batched(
            True,
            False,
            True
        )

    if mode == 8:
        return run_adaptive_placed(
            cycle
        )

    return False


def main():
    set_world_size(BENCH_WORLD_SIZE)

    start_items = num_items(
        Items.Cactus
    )
    start_time = get_time()
    start_ticks = get_tick_count()

    quick_print(
        "CACTUS MODE START",
        MODE_NAMES[BENCH_MODE],
        "world",
        BENCH_WORLD_SIZE,
        "drones",
        max_drones(),
        "cycles",
        BENCH_CYCLES
    )

    completed = 0

    for cycle in range(BENCH_CYCLES):
        if not run_cycle(
            BENCH_MODE,
            cycle
        ):
            break

        completed += 1

    elapsed = get_time() - start_time
    ticks = get_tick_count() - start_ticks
    gained = (
        num_items(Items.Cactus)
        - start_items
    )

    quick_print(
        "CACTUS RESULT",
        MODE_NAMES[BENCH_MODE],
        "completed",
        completed,
        "elapsed",
        elapsed,
        "ticks",
        ticks,
        "gain",
        gained
    )


main()
