# Maze benchmark worker.
#
# This file is executed through simulate() from benmain.py.
# The controller injects:
#
# BENCH_MODE
# BENCH_SOLVES
# BENCH_WORLD_SIZE
# BENCH_GREEDY_AFTER
# BENCH_REBALANCE_UNTIL
# BENCH_VERBOSE
#
# Modes:
#
# 0 = fresh maze + right-hand wall follower
# 1 = reused maze + dynamic BFS
# 2 = reused maze + initial tree + greedy shortcuts
# 3 = reused maze + tree + greedy + lazy reparent
# 4 = reused maze + tree + greedy + reparent + full depth reindex
#
# Mode 4 approximates the maintenance cost of the community
# tree-rebalancing approach. Mode 3 tests whether the same basic
# reparenting idea performs better without a full-tree reindex.


DIRECTIONS = [
    North,
    East,
    South,
    West
]


def opposite(direction):
    if direction == North:
        return South

    if direction == South:
        return North

    if direction == East:
        return West

    return East


def direction_index(direction):
    if direction == North:
        return 0

    if direction == East:
        return 1

    if direction == South:
        return 2

    return 3


def neighbor(coord, direction):
    x, y = coord

    if direction == North:
        return (x, y + 1)

    if direction == East:
        return (x + 1, y)

    if direction == South:
        return (x, y - 1)

    return (x - 1, y)


def direction_between(current, target):
    x0, y0 = current
    x1, y1 = target

    if x1 > x0:
        return East

    if x1 < x0:
        return West

    if y1 > y0:
        return North

    return South


def current_coord():
    return (
        get_pos_x(),
        get_pos_y()
    )


def substance_required():
    return (
        get_world_size()
        * 2**(
            num_unlocked(Unlocks.Mazes)
            - 1
        )
    )


# ==================================================
# MAZE CREATE / COLLECT
# ==================================================

def create_maze():
    clear()

    plant(
        Entities.Bush
    )

    use_item(
        Items.Weird_Substance,
        substance_required()
    )


def collect_and_relocate():
    use_item(
        Items.Weird_Substance,
        substance_required()
    )

    return measure()


# ==================================================
# BASELINE: FRESH + RIGHT HAND
# ==================================================

def solve_right_hand():
    direction = 0

    while get_entity_type() != Entities.Treasure:
        right = (
            direction
            + 1
        ) % 4

        if can_move(
            DIRECTIONS[right]
        ):
            direction = right

            move(
                DIRECTIONS[direction]
            )

        elif can_move(
            DIRECTIONS[direction]
        ):
            move(
                DIRECTIONS[direction]
            )

        else:
            direction = (
                direction
                - 1
            ) % 4

    harvest()


def run_fresh():
    for _ in range(BENCH_SOLVES):
        create_maze()

        solve_right_hand()


# ==================================================
# GRAPH MAP
# ==================================================

def ensure_cell(graph, coord):
    if coord not in graph:
        graph[coord] = [
            False,
            False,
            False,
            False
        ]


def add_edge(graph, coord, direction):
    ensure_cell(
        graph,
        coord
    )

    next_coord = neighbor(
        coord,
        direction
    )

    ensure_cell(
        graph,
        next_coord
    )

    ix = direction_index(
        direction
    )

    back_ix = direction_index(
        opposite(direction)
    )

    changed = False

    if not graph[coord][ix]:
        graph[coord][ix] = True
        changed = True

    if not graph[next_coord][back_ix]:
        graph[next_coord][back_ix] = True
        changed = True

    return changed


def scan_current(graph):
    coord = current_coord()

    ensure_cell(
        graph,
        coord
    )

    changed = False

    for direction in DIRECTIONS:
        if can_move(direction):
            if add_edge(
                graph,
                coord,
                direction
            ):
                changed = True

    return changed


# ==================================================
# INITIAL FRESH-MAZE MAP
# ==================================================
#
# Fresh mazes contain no loops, so a DFS gives us both:
#
# - a complete adjacency map
# - a valid spanning tree through parent[]
#
# The drone returns to the starting coordinate when done.
# ==================================================

def map_fresh_maze():
    graph = {}
    parent = {}

    start = current_coord()

    visited = set()

    visited.add(
        start
    )

    parent[start] = None

    stack = [
        start
    ]

    while len(stack) > 0:
        current = stack[
            len(stack) - 1
        ]

        scan_current(
            graph
        )

        moved = False

        for direction in DIRECTIONS:
            ix = direction_index(
                direction
            )

            if not graph[current][ix]:
                continue

            next_coord = neighbor(
                current,
                direction
            )

            if next_coord in visited:
                continue

            parent[next_coord] = current

            visited.add(
                next_coord
            )

            move(
                direction
            )

            stack.append(
                next_coord
            )

            moved = True
            break

        if moved:
            continue

        stack.pop()

        if len(stack) > 0:
            next_coord = stack[
                len(stack) - 1
            ]

            move(
                direction_between(
                    current,
                    next_coord
                )
            )

    return (
        graph,
        parent
    )


# ==================================================
# BFS
# ==================================================

def bfs_path_stack(
    graph,
    start,
    target
):
    if start == target:
        return []

    queue = [
        start
    ]

    queue_index = 0

    previous = {}

    previous[start] = None

    while queue_index < len(queue):
        current = queue[
            queue_index
        ]

        queue_index += 1

        if current == target:
            break

        edges = graph[current]

        for index in range(4):
            if not edges[index]:
                continue

            next_coord = neighbor(
                current,
                DIRECTIONS[index]
            )

            if next_coord in previous:
                continue

            previous[next_coord] = current

            queue.append(
                next_coord
            )

    if target not in previous:
        return []

    # Build target -> ... -> child-of-start.
    #
    # pop() then returns the next forward step without an expensive
    # front-of-list removal.
    path = []

    current = target

    while current != start:
        path.append(
            current
        )

        current = previous[current]

    return path


def move_bfs(
    graph,
    target
):
    while current_coord() != target:
        current = current_coord()

        scan_current(
            graph
        )

        path = bfs_path_stack(
            graph,
            current,
            target
        )

        if len(path) == 0:
            return False

        while len(path) > 0:
            # New openings discovered while following this route may
            # produce a shorter path. Recompute immediately.
            if scan_current(graph):
                break

            next_coord = path.pop()

            move(
                direction_between(
                    current_coord(),
                    next_coord
                )
            )

            if current_coord() == target:
                return True

    return True


# ==================================================
# TREE ROUTING
# ==================================================

def is_ancestor(
    ancestor,
    node,
    parent
):
    current = node

    while current != None:
        if current == ancestor:
            return True

        current = parent[current]

    return False


def tree_depth(
    node,
    parent
):
    depth = 0
    current = node

    while parent[current] != None:
        current = parent[current]
        depth += 1

    return depth


def tree_path_stack(
    start,
    target,
    parent
):
    if start == target:
        return []

    start_ancestors = set()

    current = start

    while current != None:
        start_ancestors.add(
            current
        )

        current = parent[current]

    down = []

    current = target

    while current not in start_ancestors:
        down.append(
            current
        )

        current = parent[current]

    lca = current

    up = []

    current = start

    while current != lca:
        current = parent[current]

        up.append(
            current
        )

    # pop() should return:
    #
    # parent(start), ..., lca, child(lca), ..., target
    path = []

    for coord in down:
        path.append(
            coord
        )

    index = (
        len(up)
        - 1
    )

    while index >= 0:
        path.append(
            up[index]
        )

        index -= 1

    return path


# ==================================================
# REBALANCING
# ==================================================

def reparent_if_better(
    a,
    b,
    parent
):
    depth_a = tree_depth(
        a,
        parent
    )

    depth_b = tree_depth(
        b,
        parent
    )

    if depth_a > depth_b + 2:
        if not is_ancestor(
            a,
            b,
            parent
        ):
            parent[a] = b

            return True

    elif depth_b > depth_a + 2:
        if not is_ancestor(
            b,
            a,
            parent
        ):
            parent[b] = a

            return True

    return False


def full_depth_reindex(
    parent
):
    # Source-like maintenance overhead:
    # walk every node and recompute its current depth.
    #
    # The route implementation itself only needs parent pointers;
    # this function intentionally measures the cost of doing a
    # full-tree level refresh after every rotation.
    depths = {}

    for coord in parent:
        depths[coord] = tree_depth(
            coord,
            parent
        )

    return depths


# ==================================================
# GREEDY SHORTCUTS
# ==================================================

def try_greedy(
    graph,
    parent,
    target,
    route_seen,
    rebalance,
    full_reindex
):
    current = current_coord()

    x0, y0 = current
    target_x, target_y = target

    direction = None

    if target_y < y0:
        direction = South

    elif target_y > y0:
        direction = North

    elif target_x > x0:
        direction = East

    elif target_x < x0:
        direction = West

    if direction == None:
        return False

    next_coord = neighbor(
        current,
        direction
    )

    if next_coord in route_seen:
        return False

    ix = direction_index(
        direction
    )

    was_known = graph[current][ix]

    if not can_move(direction):
        return False

    add_edge(
        graph,
        current,
        direction
    )

    if (
        rebalance
        and not was_known
    ):
        if reparent_if_better(
            current,
            next_coord,
            parent
        ):
            if full_reindex:
                full_depth_reindex(
                    parent
                )

    move(
        direction
    )

    route_seen.add(
        next_coord
    )

    return True


def move_tree(
    graph,
    parent,
    target,
    solved,
    rebalance,
    full_reindex
):
    route_seen = set()

    route_seen.add(
        current_coord()
    )

    path = tree_path_stack(
        current_coord(),
        target,
        parent
    )

    while current_coord() != target:
        if solved > BENCH_GREEDY_AFTER:
            if try_greedy(
                graph,
                parent,
                target,
                route_seen,
                rebalance,
                full_reindex
            ):
                path = tree_path_stack(
                    current_coord(),
                    target,
                    parent
                )

                continue

        if len(path) == 0:
            path = tree_path_stack(
                current_coord(),
                target,
                parent
            )

            if len(path) == 0:
                return False

        next_coord = path.pop()

        move(
            direction_between(
                current_coord(),
                next_coord
            )
        )

        route_seen.add(
            next_coord
        )

    return True


# ==================================================
# REUSED MAZE
# ==================================================

def run_reuse(mode):
    create_maze()

    target = measure()

    graph, parent = map_fresh_maze()

    solved = 0

    while solved < BENCH_SOLVES:
        if mode == 1:
            if not move_bfs(
                graph,
                target
            ):
                return

        elif mode == 2:
            if not move_tree(
                graph,
                parent,
                target,
                solved,
                False,
                False
            ):
                return

        elif mode == 3:
            rebalance = (
                solved
                < BENCH_REBALANCE_UNTIL
            )

            if not move_tree(
                graph,
                parent,
                target,
                solved,
                rebalance,
                False
            ):
                return

        else:
            rebalance = (
                solved
                < BENCH_REBALANCE_UNTIL
            )

            if not move_tree(
                graph,
                parent,
                target,
                solved,
                rebalance,
                True
            ):
                return

        solved += 1

        if solved >= BENCH_SOLVES:
            harvest()
            break

        target = collect_and_relocate()


# ==================================================
# BENCH ENTRYPOINT
# ==================================================

def main():
    set_world_size(
        BENCH_WORLD_SIZE
    )

    start_ticks = get_tick_count()
    start_time = get_time()

    if BENCH_MODE == 0:
        run_fresh()

    else:
        run_reuse(
            BENCH_MODE
        )

    if BENCH_VERBOSE:
        quick_print(
            "BENCH",
            BENCH_MODE,
            BENCH_WORLD_SIZE,
            BENCH_SOLVES,
            get_tick_count() - start_ticks,
            get_time() - start_time
        )


main()
