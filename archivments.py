# Achievement helpers.
#
# Enable or disable achievement helpers here.
#
# Multiple non-blocking achievements can be enabled at the same time.
# master-acrobat runs forever and stack-overflow intentionally crashes,
# so enable those individually when needed.

ACHIEVEMENTS = {
    "wrong-order": False,
    "healer": False,
    "circular-import": False,
    "master-acrobat": False,
    "stack-overflow": True,
}

TARGET_DRONES = 32


def cause_stack_overflow():
    cause_stack_overflow()


def flip_forever():
    while True:
        do_a_flip()


def master_acrobat():
    while num_drones() < TARGET_DRONES and num_drones() < max_drones():
        spawn_drone(flip_forever)

    quick_print("FLIP FARM", num_drones(), "drones")
    flip_forever()


def _move_x(target, size):
    current = get_pos_x()
    east = (target - current) % size
    west = (current - target) % size

    if east <= west:
        for _ in range(east):
            move(East)
    else:
        for _ in range(west):
            move(West)


def _move_y(target, size):
    current = get_pos_y()
    north = (target - current) % size
    south = (current - target) % size

    if north <= south:
        for _ in range(north):
            move(North)
    else:
        for _ in range(south):
            move(South)


def _move_to(x, y, size):
    _move_x(x, size)
    _move_y(y, size)


def _plant_cactus_row():
    size = get_world_size()

    for _ in range(size):
        if get_ground_type() != Grounds.Soil:
            till()

        if not plant(Entities.Cactus):
            return False

        move(East)

    return True


def _sort_cactus_row_descending():
    size = get_world_size()
    values = []

    for _ in range(size):
        while not can_harvest():
            pass

        values.append(measure())
        move(East)

    for i in range(1, size):
        j = i

        while j > 0 and values[j] > values[j - 1]:
            _move_x(j - 1, size)
            swap(East)

            value = values[j]
            values[j] = values[j - 1]
            values[j - 1] = value

            j -= 1

    return True


def _sort_cactus_column_descending():
    size = get_world_size()
    values = []

    for _ in range(size):
        values.append(measure())
        move(North)

    for i in range(1, size):
        j = i

        while j > 0 and values[j] > values[j - 1]:
            _move_y(j - 1, size)
            swap(North)

            value = values[j]
            values[j] = values[j - 1]
            values[j - 1] = value

            j -= 1

    return True


def _line_wave(worker, direction):
    size = get_world_size()

    if max_drones() < size:
        quick_print("Need", size, "drone slots, have", max_drones())
        return False

    handles = []

    for _ in range(size - 1):
        drone = spawn_drone(worker)

        if drone == None:
            for active in handles:
                wait_for(active)

            return False

        handles.append(drone)
        move(direction)

    ok = worker()

    for drone in handles:
        if not wait_for(drone):
            ok = False

    return ok


def wrong_order():
    size = get_world_size()

    if size != 32:
        quick_print("Wrong Order needs a 32x32 field. Current:", size)
        return False

    clear()
    _move_to(0, 0, size)

    if not _line_wave(_plant_cactus_row, North):
        return False

    _move_to(0, 0, size)

    if not _line_wave(_sort_cactus_row_descending, North):
        return False

    _move_to(0, 0, size)

    if not _line_wave(_sort_cactus_column_descending, East):
        return False

    # Older game versions only checked Wrong Order during harvest.
    # Community reports identified (0, 31) as a reliable trigger location.
    _move_to(0, size - 1, size)
    return harvest()


def healer():
    clear()

    if get_ground_type() != Grounds.Soil:
        till()

    if not plant(Entities.Carrot):
        quick_print("Could not plant a carrot.")
        return False

    if num_items(Items.Weird_Substance) <= 0:
        quick_print("Need Weird Substance.")
        return False

    if num_items(Items.Fertilizer) > 0:
        if not use_item(Items.Fertilizer):
            return False
    else:
        if num_items(Items.Weird_Substance) < 2:
            quick_print("Need Fertilizer or 2 Weird Substance.")
            return False

        if not use_item(Items.Weird_Substance):
            return False

    return use_item(Items.Weird_Substance)


def circular_import():
    import archivments_cycle_a
    quick_print("Circular import created.")


if ACHIEVEMENTS["wrong-order"]:
    wrong_order()

if ACHIEVEMENTS["healer"]:
    healer()

if ACHIEVEMENTS["circular-import"]:
    circular_import()

# Blocking modes run last.
if ACHIEVEMENTS["master-acrobat"]:
    master_acrobat()

if ACHIEVEMENTS["stack-overflow"]:
    cause_stack_overflow()
