import utils


MAZE_SIZE = 4


MODE_NAMES = [
    "baseline-origin00-rowmajor",
    "center-anchor-rowmajor",
    "band-anchor-rowmajor",
    "band-anchor-farthest-parent-near",
    "nearest-slots-origin00",
    "nearest-slots-farthest-parent-near",
    "spawn-at-rowmajor-origins"
]


def torus_axis_distance(a, b, size):
    direct = abs(a - b)
    wrapped = size - direct
    return min(direct, wrapped)


def torus_distance(x1, y1, x2, y2, size):
    return (
        torus_axis_distance(x1, x2, size)
        + torus_axis_distance(y1, y2, size)
    )


def block_origin(index, blocks_per_row):
    column = index % blocks_per_row
    row = index // blocks_per_row
    offset = MAZE_SIZE // 2

    return (
        column * MAZE_SIZE + offset,
        row * MAZE_SIZE + offset
    )


def current_origins(worker_count, blocks_per_row):
    origins = []

    for index in range(worker_count):
        origins.append(
            block_origin(
                index,
                blocks_per_row
            )
        )

    return origins


def all_origins(blocks_per_row):
    origins = []
    capacity = blocks_per_row * blocks_per_row

    for index in range(capacity):
        origins.append(
            block_origin(
                index,
                blocks_per_row
            )
        )

    return origins


def select_nearest(
    origins,
    count,
    anchor_x,
    anchor_y,
    size
):
    remaining = []

    for origin in origins:
        remaining.append(origin)

    selected = []

    while len(selected) < count:
        best_index = 0
        best_distance = torus_distance(
            remaining[0][0],
            remaining[0][1],
            anchor_x,
            anchor_y,
            size
        )

        index = 1

        while index < len(remaining):
            origin = remaining[index]
            distance = torus_distance(
                origin[0],
                origin[1],
                anchor_x,
                anchor_y,
                size
            )

            if distance < best_distance:
                best_distance = distance
                best_index = index

            index += 1

        selected.append(
            remaining.pop(best_index)
        )

    return selected


def order_farthest(
    origins,
    anchor_x,
    anchor_y,
    size
):
    remaining = []

    for origin in origins:
        remaining.append(origin)

    ordered = []

    while len(remaining) > 0:
        best_index = 0
        best_distance = torus_distance(
            remaining[0][0],
            remaining[0][1],
            anchor_x,
            anchor_y,
            size
        )

        index = 1

        while index < len(remaining):
            origin = remaining[index]
            distance = torus_distance(
                origin[0],
                origin[1],
                anchor_x,
                anchor_y,
                size
            )

            if distance > best_distance:
                best_distance = distance
                best_index = index

            index += 1

        ordered.append(
            remaining.pop(best_index)
        )

    return ordered


def nearest_origin_index(
    origins,
    anchor_x,
    anchor_y,
    size
):
    best_index = 0
    best_distance = torus_distance(
        origins[0][0],
        origins[0][1],
        anchor_x,
        anchor_y,
        size
    )

    index = 1

    while index < len(origins):
        origin = origins[index]
        distance = torus_distance(
            origin[0],
            origin[1],
            anchor_x,
            anchor_y,
            size
        )

        if distance < best_distance:
            best_distance = distance
            best_index = index

        index += 1

    return best_index


def prepare_plan(mode, worker_count, world_size):
    blocks_per_row = world_size // MAZE_SIZE
    origins = current_origins(
        worker_count,
        blocks_per_row
    )

    anchor = (0, 0)
    spawn_at = False
    parent_near = False
    farthest_first = False

    if mode == 1:
        anchor = (
            world_size // 2,
            world_size // 2
        )

    elif mode == 2:
        anchor = (
            0,
            world_size // 4
        )

    elif mode == 3:
        anchor = (
            0,
            world_size // 4
        )
        parent_near = True
        farthest_first = True

    elif mode == 4:
        origins = select_nearest(
            all_origins(blocks_per_row),
            worker_count,
            0,
            0,
            world_size
        )

    elif mode == 5:
        origins = select_nearest(
            all_origins(blocks_per_row),
            worker_count,
            0,
            0,
            world_size
        )
        parent_near = True
        farthest_first = True

    elif mode == 6:
        spawn_at = True

    parent_origin = origins[len(origins) - 1]

    if parent_near:
        parent_index = nearest_origin_index(
            origins,
            anchor[0],
            anchor[1],
            world_size
        )
        parent_origin = origins.pop(parent_index)

    else:
        origins.pop()

    if farthest_first:
        origins = order_farthest(
            origins,
            anchor[0],
            anchor[1],
            world_size
        )

    return [
        anchor,
        origins,
        parent_origin,
        spawn_at
    ]


def worker(origin_x, origin_y, move_self):
    if move_self:
        utils.move_to(
            origin_x,
            origin_y
        )

    if not plant(Entities.Bush):
        return False

    return True


def run_setup(mode):
    world_size = utils.size()
    worker_count = min(
        max_drones(),
        (
            world_size
            // MAZE_SIZE
        ) ** 2
    )

    plan = prepare_plan(
        mode,
        worker_count,
        world_size
    )

    anchor = plan[0]
    child_origins = plan[1]
    parent_origin = plan[2]
    spawn_at = plan[3]

    utils.move_to(
        anchor[0],
        anchor[1]
    )

    handles = []

    for origin in child_origins:
        if spawn_at:
            utils.move_to(
                origin[0],
                origin[1]
            )
            move_self = False
        else:
            move_self = True

        drone = spawn_drone(
            worker,
            origin[0],
            origin[1],
            move_self
        )

        if drone == None:
            return False

        handles.append(drone)

    utils.move_to(
        parent_origin[0],
        parent_origin[1]
    )

    if not plant(Entities.Bush):
        return False

    success = True

    for drone in handles:
        if not wait_for(drone):
            success = False

    return success


def main():
    set_world_size(BENCH_WORLD_SIZE)
    clear()

    start_time = get_time()
    start_ticks = get_tick_count()

    success = run_setup(BENCH_MODE)

    elapsed = get_time() - start_time
    ticks = get_tick_count() - start_ticks

    if success:
        result = "PASS"
    else:
        result = "FAIL"

    quick_print(
        "SPAWN RESULT",
        MODE_NAMES[BENCH_MODE],
        "elapsed",
        elapsed,
        "ticks",
        ticks,
        "drones",
        max_drones(),
        result
    )


if __name__ == "__main__":
    main()
