import config
import utils


# Adaptive parallel small-Maze production.
#
# The 32x32 / 32-drone 4x4 strategy is derived from the benchmarked
# zapakh source-near mode in bench_maze.py.
#
# Benchmark:
# 55734c855dd464dd846deef280d8a65d9f2c3bf7
#
# At 32x32 / 32 drones, 4x4 is the measured production candidate.
# Smaller-world 3x3 selection is an adaptive heuristic and should be
# benchmarked separately before treating it as an optimal choice.


_DIRECTIONS = [
    North,
    East,
    South,
    West
]


def _maze_level():
    return num_unlocked(
        Unlocks.Mazes
    )


def substance_required(maze_size):
    maze_level = _maze_level()

    if maze_level <= 0:
        return 0

    return (
        maze_size
        * 2**(maze_level - 1)
    )


def _candidate(
    maze_size
):
    world_size = utils.size()

    if world_size < maze_size:
        return None

    blocks = (
        world_size
        // maze_size
    )

    capacity = (
        blocks
        * blocks
    )

    worker_count = min(
        max_drones(),
        capacity
    )

    if (
        worker_count
        < config.MAZE_PARALLEL_MIN_WORKERS
    ):
        return None

    # Approximate useful Gold per synchronized Treasure round.
    score = (
        worker_count
        * maze_size
        * maze_size
    )

    return [
        maze_size,
        worker_count,
        blocks,
        score
    ]


def plan():
    if _maze_level() <= 0:
        return None

    best = None

    # Prefer 4x4 on ties because it is the measured endgame strategy
    # and has better Gold / Weird-Substance efficiency.
    for maze_size in [
        4,
        3
    ]:
        candidate = _candidate(
            maze_size
        )

        if candidate == None:
            continue

        if (
            best == None
            or candidate[3] > best[3]
        ):
            best = candidate

    if best == None:
        return None

    return [
        best[0],
        best[1],
        best[2]
    ]


def enabled():
    return plan() != None


def worker_count():
    current = plan()

    if current == None:
        return 0

    return current[1]


def bushes_required():
    return worker_count()


def stockpile_required():
    current = plan()

    if current == None:
        return 0

    maze_size = current[0]
    workers = current[1]

    # Each worker pays once to create its Maze and once per configured
    # Treasure relocation. The final Treasure harvest costs no substance.
    actions_per_worker = (
        config.MAZE_PARALLEL_RELOCATIONS
        + 1
    )

    return (
        substance_required(
            maze_size
        )
        * workers
        * actions_per_worker
    )


def can_start():
    current = plan()

    if current == None:
        return False

    if (
        num_items(
            Items.Weird_Substance
        )
        < stockpile_required()
    ):
        return False

    if not utils.can_afford(
        Entities.Bush,
        current[1]
    ):
        return False

    return True


def _back(direction):
    if direction == North:
        return South

    if direction == South:
        return North

    if direction == East:
        return West

    return East


def _neighbor(
    coord,
    direction
):
    x, y = coord
    world_size = utils.size()

    if direction == North:
        return (
            x,
            (y + 1) % world_size
        )

    if direction == East:
        return (
            (x + 1) % world_size,
            y
        )

    if direction == South:
        return (
            x,
            (y - 1) % world_size
        )

    return (
        (x - 1) % world_size,
        y
    )


def _ranked_directions(
    pos_x,
    pos_y,
    goal_x,
    goal_y,
    exclude
):
    if goal_x == None:
        all_directions = [
            (1, North),
            (2, East),
            (3, South),
            (4, West)
        ]

    else:
        all_directions = [
            (
                goal_y - pos_y + 0.1,
                North
            ),
            (
                goal_x - pos_x + 0.2,
                East
            ),
            (
                pos_y - goal_y + 0.3,
                South
            ),
            (
                pos_x - goal_x + 0.4,
                West
            )
        ]

    ranked = []

    for _ in range(
        len(all_directions)
    ):
        selected = min(
            all_directions
        )

        all_directions.remove(
            selected
        )

        if selected[1] != exclude:
            ranked.append(
                selected[1]
            )

    return ranked


def _find_treasure(
    goal_x,
    goal_y
):
    x = get_pos_x()
    y = get_pos_y()

    stack = [
        (
            [
                North,
                East,
                South,
                West
            ],
            None
        )
    ]

    visited = {
        (x, y)
    }

    while (
        get_entity_type()
        != Entities.Treasure
    ):
        directions, back = stack[
            len(stack) - 1
        ]

        old_x = x
        old_y = y
        direction = None

        while len(directions) > 0:
            direction = directions.pop()

            next_coord = _neighbor(
                (old_x, old_y),
                direction
            )

            if (
                next_coord in visited
                or not move(direction)
            ):
                direction = None
                continue

            x = get_pos_x()
            y = get_pos_y()
            break

        if direction == None:
            stack.pop()

            if back == None:
                return False

            move(
                back
            )

            x = get_pos_x()
            y = get_pos_y()

        else:
            visited.add(
                (x, y)
            )

            back = _back(
                direction
            )

            stack.append(
                (
                    _ranked_directions(
                        x,
                        y,
                        goal_x,
                        goal_y,
                        back
                    ),
                    back
                )
            )

    return True


def _solve(
    maze_size,
    relocations
):
    substance = substance_required(
        maze_size
    )

    solved = 0

    while solved < relocations:
        goal = measure()

        if goal == None:
            return False

        goal_x, goal_y = goal

        if not _find_treasure(
            goal_x,
            goal_y
        ):
            return False

        if not use_item(
            Items.Weird_Substance,
            substance
        ):
            return False

        solved += 1

    goal = measure()

    if (
        get_entity_type()
        != Entities.Treasure
    ):
        if goal == None:
            return False

        goal_x, goal_y = goal

        if not _find_treasure(
            goal_x,
            goal_y
        ):
            return False

    if (
        get_entity_type()
        != Entities.Treasure
    ):
        return False

    harvest()

    return True


def _worker(
    origin_x,
    origin_y,
    maze_size,
    relocations,
    start_substance
):
    utils.move_to(
        origin_x,
        origin_y
    )

    if not plant(
        Entities.Bush
    ):
        return False

    # All workers are placed first. The parent creates its own Maze only
    # after every child Bush is visible. That guaranteed substance change
    # releases all children at the same time.
    while (
        num_items(
            Items.Weird_Substance
        )
        == start_substance
    ):
        pass

    if not use_item(
        Items.Weird_Substance,
        substance_required(
            maze_size
        )
    ):
        return False

    return _solve(
        maze_size,
        relocations
    )


def _origin(
    index,
    maze_size,
    blocks_per_row
):
    column = (
        index
        % blocks_per_row
    )

    row = (
        index
        // blocks_per_row
    )

    offset = (
        maze_size
        // 2
    )

    return (
        column * maze_size + offset,
        row * maze_size + offset
    )


def _wait_for_bush(
    x,
    y
):
    utils.move_to(
        x,
        y
    )

    while (
        get_entity_type()
        != Entities.Bush
    ):
        pass


def run():
    current = plan()

    if (
        current == None
        or not can_start()
    ):
        return False

    maze_size = current[0]
    planned_workers = current[1]
    blocks_per_row = current[2]

    quick_print(
        "MAZE PARALLEL",
        maze_size,
        "workers",
        planned_workers,
        "relocations",
        config.MAZE_PARALLEL_RELOCATIONS,
        "substance",
        stockpile_required()
    )

    clear()

    start_substance = num_items(
        Items.Weird_Substance
    )

    drones = []
    origins = []

    # Children move to their origins in parallel. If a spawn unexpectedly
    # fails, stop adding workers and let the parent own the next free origin.
    index = 0

    while index < planned_workers - 1:
        origin = _origin(
            index,
            maze_size,
            blocks_per_row
        )

        drone = spawn_drone(
            _worker,
            origin[0],
            origin[1],
            maze_size,
            config.MAZE_PARALLEL_RELOCATIONS,
            start_substance
        )

        if drone == None:
            break

        drones.append(
            drone
        )

        origins.append(
            origin
        )

        index += 1

    for origin in origins:
        _wait_for_bush(
            origin[0],
            origin[1]
        )

    parent_origin = _origin(
        len(drones),
        maze_size,
        blocks_per_row
    )

    utils.move_to(
        parent_origin[0],
        parent_origin[1]
    )

    if not plant(
        Entities.Bush
    ):
        return False

    if not use_item(
        Items.Weird_Substance,
        substance_required(
            maze_size
        )
    ):
        return False

    success = _solve(
        maze_size,
        config.MAZE_PARALLEL_RELOCATIONS
    )

    for drone in drones:
        if not wait_for(
            drone
        ):
            success = False

    return success
