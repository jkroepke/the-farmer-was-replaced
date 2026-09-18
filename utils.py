import config


def size():
    # Nicht cachen:
    # Unlocks.Expand kann die Farm im laufenden Programm vergrößern.
    return get_world_size()


def can_afford(thing, multiplier = 1):
    cost = get_cost(thing)

    if cost == None:
        return False

    for item in cost:
        required = cost[item] * multiplier

        if num_items(item) < required:
            return False

    return True


def water():
    if get_water() < config.WATER_LIMIT:
        if num_items(Items.Water) > 0:
            use_item(Items.Water)


def move_to(target_x, target_y):
    world_size = size()

    current_x = get_pos_x()

    east_distance = (
        target_x - current_x
    ) % world_size

    west_distance = (
        current_x - target_x
    ) % world_size

    if east_distance <= west_distance:
        for _ in range(east_distance):
            move(East)
    else:
        for _ in range(west_distance):
            move(West)

    current_y = get_pos_y()

    north_distance = (
        target_y - current_y
    ) % world_size

    south_distance = (
        current_y - target_y
    ) % world_size

    if north_distance <= south_distance:
        for _ in range(north_distance):
            move(North)
    else:
        for _ in range(south_distance):
            move(South)
