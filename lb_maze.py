# Maze leaderboard implementation.
#
# Current long-run candidate:
# - 32 independent 5x5 Mazes
# - one drone per Maze
# - right-hand mapping on each fresh Maze
# - BFS routing to the measured Treasure
# - learn newly-opened walls after Treasure relocation
# - reuse each Maze up to 300 times
#
# The program terminates as soon as the Maze leaderboard target is reached.


TARGET_GOLD = 9863168
MAZE_SIZE = 5
REUSE_LIMIT = 300

DIRECTIONS = [
    North,
    East,
    South,
    West
]


def done():
    return (
        num_items(Items.Gold)
        >= TARGET_GOLD
    )


def back(direction):
    if direction == North:
        return South

    if direction == South:
        return North

    if direction == East:
        return West

    return East


def neighbor(
    coord,
    direction
):
    x, y = coord
    size = get_world_size()

    if direction == North:
        return (
            x,
            (y + 1) % size
        )

    if direction == East:
        return (
            (x + 1) % size,
            y
        )

    if direction == South:
        return (
            x,
            (y - 1) % size
        )

    return (
        (x - 1) % size,
        y
    )


def move_to(
    x,
    y
):
    size = get_world_size()

    while get_pos_x() != x:
        current = get_pos_x()

        east_distance = (
            x - current
        ) % size

        west_distance = (
            current - x
        ) % size

        if east_distance <= west_distance:
            direction = East
        else:
            direction = West

        if not move(
            direction
        ):
            return False

    while get_pos_y() != y:
        current = get_pos_y()

        north_distance = (
            y - current
        ) % size

        south_distance = (
            current - y
        ) % size

        if north_distance <= south_distance:
            direction = North
        else:
            direction = South

        if not move(
            direction
        ):
            return False

    return True


def substance_required():
    return (
        MAZE_SIZE
        * 2**(
            num_unlocked(
                Unlocks.Mazes
            )
            - 1
        )
    )


def create_maze():
    if not plant(
        Entities.Bush
    ):
        return False

    return use_item(
        Items.Weird_Substance,
        substance_required()
    )


def relocate():
    return use_item(
        Items.Weird_Substance,
        substance_required()
    )


def graph_ensure(
    graph,
    coord
):
    if coord not in graph:
        graph[coord] = [
            False,
            False,
            False,
            False
        ]


def graph_scan(
    graph
):
    current = (
        get_pos_x(),
        get_pos_y()
    )

    graph_ensure(
        graph,
        current
    )

    changed = False

    for index in range(4):
        direction = DIRECTIONS[
            index
        ]

        if not can_move(
            direction
        ):
            continue

        next_coord = neighbor(
            current,
            direction
        )

        graph_ensure(
            graph,
            next_coord
        )

        back_index = (
            index + 2
        ) % 4

        if not graph[current][index]:
            graph[current][index] = True
            changed = True

        if not graph[
            next_coord
        ][back_index]:
            graph[
                next_coord
            ][back_index] = True
            changed = True

    return changed


def turn_right(
    direction
):
    if direction == North:
        return East

    if direction == East:
        return South

    if direction == South:
        return West

    return North


def turn_left(
    direction
):
    if direction == North:
        return West

    if direction == West:
        return South

    if direction == South:
        return East

    return North


def map_right_hand():
    graph = {}
    visited = set()

    start = (
        get_pos_x(),
        get_pos_y()
    )

    direction = North
    moved = False

    while True:
        current = (
            get_pos_x(),
            get_pos_y()
        )

        visited.add(
            current
        )

        graph_scan(
            graph
        )

        if (
            moved
            and len(visited)
            >= MAZE_SIZE * MAZE_SIZE
            and current == start
        ):
            return graph

        candidates = [
            turn_right(
                direction
            ),
            direction,
            turn_left(
                direction
            ),
            back(
                direction
            )
        ]

        did_move = False

        for candidate in candidates:
            if move(
                candidate
            ):
                direction = candidate
                did_move = True
                moved = True
                break

        if not did_move:
            return graph


def bfs_path(
    graph,
    start,
    target
):
    if start == target:
        return []

    queue = [
        start
    ]

    previous = {
        start: None
    }

    queue_index = 0

    while queue_index < len(queue):
        current = queue[
            queue_index
        ]

        queue_index += 1

        if current == target:
            break

        if current not in graph:
            continue

        edges = graph[
            current
        ]

        for index in range(4):
            if not edges[index]:
                continue

            next_coord = neighbor(
                current,
                DIRECTIONS[
                    index
                ]
            )

            if next_coord in previous:
                continue

            previous[
                next_coord
            ] = current

            queue.append(
                next_coord
            )

    if target not in previous:
        return []

    path = []
    current = target

    while current != start:
        path.append(
            current
        )

        current = previous[
            current
        ]

    return path


def move_bfs(
    graph,
    target
):
    while (
        (
            get_pos_x(),
            get_pos_y()
        )
        != target
    ):
        current = (
            get_pos_x(),
            get_pos_y()
        )

        graph_scan(
            graph
        )

        path = bfs_path(
            graph,
            current,
            target
        )

        if len(path) == 0:
            return False

        while len(path) > 0:
            # Reuse can open walls. Recompute the route as soon as a new
            # connection is discovered.
            if graph_scan(
                graph
            ):
                break

            next_coord = path.pop()

            current = (
                get_pos_x(),
                get_pos_y()
            )

            direction = None

            for candidate in DIRECTIONS:
                if (
                    neighbor(
                        current,
                        candidate
                    )
                    == next_coord
                ):
                    direction = candidate
                    break

            if direction == None:
                return False

            if not move(
                direction
            ):
                break

    return True


def solve_worker(
    origin_x,
    origin_y,
    first_maze_ready
):
    maze_ready = first_maze_ready

    while not done():
        if not maze_ready:
            if not move_to(
                origin_x,
                origin_y
            ):
                return

            if not create_maze():
                return

        maze_ready = False

        graph = map_right_hand()
        solved = 0

        while (
            solved < REUSE_LIMIT
            and not done()
        ):
            target = measure()

            if target == None:
                return

            if not move_bfs(
                graph,
                target
            ):
                return

            if done():
                return

            if not relocate():
                if (
                    get_entity_type()
                    == Entities.Treasure
                ):
                    harvest()

                break

            solved += 1

        if done():
            return

        # After 300 relocations the final Treasure still exists. Harvest it
        # before rebuilding the local Maze.
        if (
            get_entity_type()
            != Entities.Treasure
        ):
            target = measure()

            if target != None:
                if not move_bfs(
                    graph,
                    target
                ):
                    return

        if (
            get_entity_type()
            == Entities.Treasure
        ):
            harvest()


def worker(
    origin_x,
    origin_y,
    start_substance
):
    if not move_to(
        origin_x,
        origin_y
    ):
        return

    if not plant(
        Entities.Bush
    ):
        return

    # Children are positioned before any Maze exists. The parent creates its
    # Maze only after seeing all 31 ready Bushes. That guaranteed substance
    # change releases every child.
    while (
        num_items(
            Items.Weird_Substance
        )
        == start_substance
        and not done()
    ):
        pass

    if done():
        return

    if not relocate():
        return

    solve_worker(
        origin_x,
        origin_y,
        True
    )


def origin(
    index
):
    # 32 non-overlapping 5x5 slots from a 6x6 grid.
    return (
        (
            index % 6
        ) * 5 + 2,
        (
            index // 6
        ) * 5 + 2
    )


def wait_for_bush(
    x,
    y
):
    if not move_to(
        x,
        y
    ):
        return False

    while (
        get_entity_type()
        != Entities.Bush
    ):
        if done():
            return False

    return True


def main():
    clear()

    start_substance = num_items(
        Items.Weird_Substance
    )

    drones = []
    origins = []

    index = 0

    while index < 31:
        worker_origin = origin(
            index
        )

        drone = spawn_drone(
            worker,
            worker_origin[0],
            worker_origin[1],
            start_substance
        )

        if drone == None:
            return

        drones.append(
            drone
        )

        origins.append(
            worker_origin
        )

        index += 1

    # Do not create any Maze while children are still crossing the field.
    for worker_origin in origins:
        if not wait_for_bush(
            worker_origin[0],
            worker_origin[1]
        ):
            return

    parent_origin = origin(
        31
    )

    if not move_to(
        parent_origin[0],
        parent_origin[1]
    ):
        return

    if not create_maze():
        return

    solve_worker(
        parent_origin[0],
        parent_origin[1],
        True
    )

    # Ensure the leaderboard program itself terminates after all children
    # observe the global Gold target and return.
    for drone in drones:
        wait_for(
            drone
        )


main()
