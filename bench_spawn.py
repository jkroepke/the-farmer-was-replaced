import utils


MAZE_SIZE = 4

CURRENT_ORIGINS = [
    (2, 2), (6, 2), (10, 2), (14, 2),
    (18, 2), (22, 2), (26, 2), (30, 2),
    (2, 6), (6, 6), (10, 6), (14, 6),
    (18, 6), (22, 6), (26, 6), (30, 6),
    (2, 10), (6, 10), (10, 10), (14, 10),
    (18, 10), (22, 10), (26, 10), (30, 10),
    (2, 14), (6, 14), (10, 14), (14, 14),
    (18, 14), (22, 14), (26, 14), (30, 14)
]

NEAREST_ORIGINS = [
    (2, 2), (6, 2), (10, 2), (14, 2),
    (18, 2), (22, 2), (26, 2), (30, 2),
    (2, 6), (6, 6), (10, 6), (22, 6),
    (26, 6), (30, 6), (2, 10), (6, 10),
    (26, 10), (30, 10), (2, 14), (30, 14),
    (2, 22), (30, 22), (2, 26), (6, 26),
    (26, 26), (30, 26), (2, 30), (6, 30),
    (10, 30), (22, 30), (26, 30), (30, 30)
]

BAND_FARTHEST_CHILDREN = [
    (14, 2), (18, 2), (14, 14), (18, 14),
    (10, 2), (22, 2), (14, 6), (18, 6),
    (14, 10), (18, 10), (10, 14), (22, 14),
    (6, 2), (26, 2), (10, 6), (22, 6),
    (10, 10), (22, 10), (6, 14), (26, 14),
    (2, 2), (30, 2), (6, 6), (26, 6),
    (6, 10), (26, 10), (2, 14), (30, 14),
    (30, 6), (2, 10), (30, 10)
]

NEAREST_FARTHEST_CHILDREN = [
    (14, 2), (18, 2), (10, 6), (22, 6),
    (6, 10), (26, 10), (2, 14), (30, 14),
    (10, 2), (22, 2), (6, 6), (26, 6),
    (2, 10), (30, 10), (2, 22), (30, 22),
    (6, 26), (26, 26), (10, 30), (22, 30),
    (6, 2), (26, 2), (2, 6), (30, 6),
    (2, 26), (30, 26), (6, 30), (26, 30),
    (30, 2), (2, 30), (30, 30)
]

MODE_NAMES = [
    "baseline-origin00-rowmajor",
    "origin00-parent-near",
    "band-anchor-rowmajor",
    "band-precomputed-farthest-parent-near",
    "nearest-slots-precomputed-rowmajor",
    "nearest-slots-precomputed-farthest-parent-near",
    "binary-tree-rowmajor-origin00",
    "binary-tree-nearest-origin00"
]


def copy_origins(source):
    result = []

    for origin in source:
        result.append(origin)

    return result


def worker(origin_x, origin_y):
    utils.move_to(
        origin_x,
        origin_y
    )

    if not plant(Entities.Bush):
        return False

    return True


def run_linear(
    anchor,
    child_origins,
    parent_origin
):
    utils.move_to(
        anchor[0],
        anchor[1]
    )

    handles = []

    for origin in child_origins:
        drone = spawn_drone(
            worker,
            origin[0],
            origin[1]
        )

        if drone == None:
            return False

        handles.append(drone)

    if not worker(
        parent_origin[0],
        parent_origin[1]
    ):
        return False

    success = True

    for drone in handles:
        if not wait_for(drone):
            success = False

    return success


def tree_worker(
    origins,
    start,
    count
):
    if count == 1:
        origin = origins[start]

        return worker(
            origin[0],
            origin[1]
        )

    second_count = count // 2
    first_count = count - second_count

    drone = spawn_drone(
        tree_worker,
        origins,
        start + first_count,
        second_count
    )

    if drone == None:
        return False

    own_success = tree_worker(
        origins,
        start,
        first_count
    )

    child_success = wait_for(
        drone
    )

    return (
        own_success
        and child_success
    )


def run_setup(mode):
    if max_drones() < 32:
        return False

    if mode == 0:
        origins = copy_origins(
            CURRENT_ORIGINS
        )
        parent_origin = origins.pop()

        return run_linear(
            (0, 0),
            origins,
            parent_origin
        )

    if mode == 1:
        origins = copy_origins(
            CURRENT_ORIGINS
        )
        parent_origin = origins.pop(0)

        return run_linear(
            (0, 0),
            origins,
            parent_origin
        )

    if mode == 2:
        origins = copy_origins(
            CURRENT_ORIGINS
        )
        parent_origin = origins.pop()

        return run_linear(
            (0, 8),
            origins,
            parent_origin
        )

    if mode == 3:
        return run_linear(
            (0, 8),
            BAND_FARTHEST_CHILDREN,
            (2, 6)
        )

    if mode == 4:
        origins = copy_origins(
            NEAREST_ORIGINS
        )
        parent_origin = origins.pop(0)

        return run_linear(
            (0, 0),
            origins,
            parent_origin
        )

    if mode == 5:
        return run_linear(
            (0, 0),
            NEAREST_FARTHEST_CHILDREN,
            (2, 2)
        )

    if mode == 6:
        return tree_worker(
            CURRENT_ORIGINS,
            0,
            len(CURRENT_ORIGINS)
        )

    return tree_worker(
        NEAREST_ORIGINS,
        0,
        len(NEAREST_ORIGINS)
    )


def main():
    set_world_size(BENCH_WORLD_SIZE)
    clear()

    start_time = get_time()
    start_ticks = get_tick_count()

    success = run_setup(
        BENCH_MODE
    )

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
