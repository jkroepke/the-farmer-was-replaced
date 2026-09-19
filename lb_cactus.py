SIZE = 32
WORKERS = 32


def _reroll_needed(value, x, y):
    if x < 16 and y < 16:
        return value >= 5

    if x >= 16 and y >= 16:
        return value < 5

    return value < 2 or value > 7


def _move_x(current, target):
    east = (target - current) % SIZE
    west = (current - target) % SIZE

    if east <= west:
        for _ in range(east):
            move(East)
    else:
        for _ in range(west):
            move(West)

    return target


def _move_y(current, target):
    north = (target - current) % SIZE
    south = (current - target) % SIZE

    if north <= south:
        for _ in range(north):
            move(North)
    else:
        for _ in range(south):
            move(South)

    return target


def _move_to(target_x, target_y):
    _move_x(
        get_pos_x(),
        target_x
    )

    _move_y(
        get_pos_y(),
        target_y
    )


def _insertion_row(y, values):
    current_x = get_pos_x()

    for i in range(
        1,
        SIZE
    ):
        j = i

        while (
            j > 0
            and values[j] < values[j - 1]
        ):
            current_x = _move_x(
                current_x,
                j - 1
            )

            swap(East)

            value = values[j]
            values[j] = values[j - 1]
            values[j - 1] = value
            j -= 1

    _move_to(
        0,
        y
    )


def _insertion_column(x):
    values = []

    _move_to(
        x,
        0
    )

    for _ in range(SIZE):
        values.append(
            measure()
        )
        move(North)

    current_y = get_pos_y()

    for i in range(
        1,
        SIZE
    ):
        j = i

        while (
            j > 0
            and values[j] < values[j - 1]
        ):
            current_y = _move_y(
                current_y,
                j - 1
            )

            swap(North)

            value = values[j]
            values[j] = values[j - 1]
            values[j - 1] = value
            j -= 1

    _move_to(
        x,
        0
    )


def _row_worker(index):
    y = index
    values = []
    redo = []

    _move_to(
        0,
        y
    )

    # Fixed leaderboard contract: fresh Grassland, 32x32, full unlocks,
    # and the Cactus planting input supplied in bulk.
    for x in range(SIZE):
        till()
        plant(Entities.Cactus)

        level = measure()
        values.append(
            level
        )

        if _reroll_needed(
            level,
            x,
            y
        ):
            redo.append(
                x
            )

        move(East)

    while len(redo) > 0:
        redo_index = 0
        length = len(redo)

        for _ in range(length):
            if redo_index >= len(redo):
                break

            x = redo[redo_index]

            _move_to(
                x,
                y
            )

            while not can_harvest():
                pass

            till()
            till()
            plant(Entities.Cactus)

            level = measure()
            values[x] = level

            if _reroll_needed(
                level,
                x,
                y
            ):
                redo_index += 1
            else:
                redo.pop(
                    redo_index
                )

    _insertion_row(
        y,
        values
    )

    return True


def _column_worker(index):
    _insertion_column(
        index
    )

    return True


def _power_worker(
    phase,
    index
):
    handles = []
    power = 1

    while index + power < WORKERS:
        if power > index:
            drone = spawn_drone(
                _power_worker,
                phase,
                index + power
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

        power = power * 2

    if phase == 0:
        success = _row_worker(
            index
        )
    else:
        success = _column_worker(
            index
        )

    for drone in handles:
        if not wait_for(
            drone
        ):
            success = False

    return success


def run():
    if not _power_worker(
        0,
        0
    ):
        return False

    if not _power_worker(
        1,
        0
    ):
        return False

    _move_to(
        SIZE - 1,
        SIZE - 1
    )

    while not can_harvest():
        pass

    return harvest()


def main():
    run()


if __name__ == "__main__":
    main()
