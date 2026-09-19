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
    "binary-tree-nearest-origin00",
    "dual-spawner-rowmajor",
    "flekay-powers-rowmajor",
    "jarvan-powers-rowmajor"
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
    layout,
    start,
    count
):
    if layout == 0:
        origins = CURRENT_ORIGINS
    else:
        origins = NEAREST_ORIGINS

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
        layout,
        start + first_count,
        second_count
    )

    if drone == None:
        return False

    own_success = tree_worker(
        layout,
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


POWER_CHILDREN = [
    [1, 2, 4, 8, 16],
    [3, 5, 9, 17],
    [6, 10, 18],
    [7, 11, 19],
    [12, 20],
    [13, 21],
    [14, 22],
    [15, 23],
    [24],
    [25],
    [26],
    [27],
    [28],
    [29],
    [30],
    [31],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    []
]


def dual_branch(
    start,
    count
):
    handles = []
    index = start + 1
    end = start + count

    while index < end:
        origin = CURRENT_ORIGINS[
            index
        ]

        drone = spawn_drone(
            worker,
            origin[0],
            origin[1]
        )

        if drone == None:
            return False

        handles.append(
            drone
        )

        index += 1

    origin = CURRENT_ORIGINS[
        start
    ]

    success = worker(
        origin[0],
        origin[1]
    )

    for drone in handles:
        if not wait_for(
            drone
        ):
            success = False

    return success


def run_dual_spawner():
    second = spawn_drone(
        dual_branch,
        16,
        16
    )

    if second == None:
        return False

    own_success = dual_branch(
        0,
        16
    )

    other_success = wait_for(
        second
    )

    return (
        own_success
        and other_success
    )


def flekay_power_worker(
    index
):
    handles = []

    for child_index in POWER_CHILDREN[
        index
    ]:
        drone = spawn_drone(
            flekay_power_worker,
            child_index
        )

        if drone == None:
            return False

        handles.append(
            drone
        )

    origin = CURRENT_ORIGINS[
        index
    ]

    success = worker(
        origin[0],
        origin[1]
    )

    for drone in handles:
        if not wait_for(
            drone
        ):
            success = False

    return success


def jarvan_power_worker(
    index
):
    handles = []
    power = 1

    while (
        index + power
        < len(
            CURRENT_ORIGINS
        )
    ):
        if power > index:
            drone = spawn_drone(
                jarvan_power_worker,
                index + power
            )

            if drone == None:
                return False

            handles.append(
                drone
            )

        power = power * 2

    origin = CURRENT_ORIGINS[
        index
    ]

    success = worker(
        origin[0],
        origin[1]
    )

    for drone in handles:
        if not wait_for(
            drone
        ):
            success = False

    return success


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
            0,
            0,
            len(CURRENT_ORIGINS)
        )

    if mode == 7:
        return tree_worker(
            1,
            0,
            len(NEAREST_ORIGINS)
        )

    if mode == 8:
        return run_dual_spawner()

    if mode == 9:
        return flekay_power_worker(
            0
        )

    if mode == 10:
        return jarvan_power_worker(
            0
        )

    return False


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
