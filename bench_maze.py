# Maze benchmark implementations.
#
# Run through bench_maze_run.py. All Maze benchmark strategies live here
# so the *_run file owns only the simulation matrix and result aggregation.
#
# Modes:
# 0 = fresh maze + right-hand wall follower
# 1 = reused maze + dynamic BFS
# 2 = reused maze + initial tree + greedy shortcuts
# 3 = reused maze + tree + greedy + lazy reparent
# 4 = reused maze + tree + greedy + approximate full reindex
# 5 = behavioral port of the reference tree-rebalancing strategy
#
# Reference:
# https://pastebin.com/KzGvn6nc
#
# ------------------------------------------------------------------
# STANDARD / EXPERIMENTAL STRATEGIES
# ------------------------------------------------------------------

# Maze benchmark worker.
#
# This file is executed through simulate() from bench_maze_run.py.
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
    # Reuse strategies perform BENCH_SOLVES relocations and then
    # harvest the final treasure. Match that total reward count.
    for _ in range(BENCH_SOLVES + 1):
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

        target = collect_and_relocate()

        solved += 1

    # Same end-of-maze behavior as the reference implementation:
    # follow the final relocated treasure and harvest it.
    if mode == 1:
        move_bfs(
            graph,
            target
        )

    else:
        move_tree(
            graph,
            parent,
            target,
            solved,
            False,
            False
        )

    harvest()


# ==================================================
# BENCH ENTRYPOINT
# ==================================================

def run_standard():
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



# ------------------------------------------------------------------
# REFERENCE TREE-REBALANCING STRATEGY
# ------------------------------------------------------------------

# Behavioral port of the community "maze single - tree rebalancing"
# benchmark strategy:
#
# https://pastebin.com/KzGvn6nc
#
# The reference strategy is kept as its own mode in this shared
# benchmark file so every Maze strategy uses the same simulation entrypoint.
#
# The port preserves the important algorithmic behavior:
#
# - DFS-map the initial loop-free maze into an ordered tree
# - node metadata: val, max_val, level, parent, direction, 4 child slots
# - route by subtree value ranges instead of BFS
# - greedy target-directed shortcut attempts after ~30 solves
# - reroot near solve 40
# - update the tree when newly opened walls connect to a much shallower node
# - full-tree reindex after a rotation
#
# BENCH_SOLVES means number of Weird-Substance treasure relocations.
# After those relocations, the final treasure is harvested, matching
# the reference workflow.


REF_DIRECTIONS = [
    North,
    South,
    East,
    West
]


def ref_back(direction):
    if direction == North:
        return South

    if direction == South:
        return North

    if direction == East:
        return West

    return East


def ref_left(direction):
    if direction == North:
        return West

    if direction == West:
        return South

    if direction == South:
        return East

    return North


def ref_right(direction):
    if direction == North:
        return East

    if direction == East:
        return South

    if direction == South:
        return West

    return North


def ref_neighbor(coord, direction):
    x, y = coord

    if direction == North:
        return (x, y + 1)

    if direction == South:
        return (x, y - 1)

    if direction == East:
        return (x + 1, y)

    return (x - 1, y)


def ref_coord():
    return (
        get_pos_x(),
        get_pos_y()
    )


def ref_substance():
    return (
        REF_MAZE_SIZE
        * 2**(
            num_unlocked(Unlocks.Mazes)
            - 1
        )
    )


def ref_node(
    value,
    coord,
    direction,
    level
):
    return {
        "val": value,
        "coord": coord,
        "dir": direction,
        "max_val": value,
        "level": level,
        "parent": None,
        "left": None,
        "forward": None,
        "right": None,
        "root_extra": None
    }


def ref_child_names():
    return [
        "left",
        "forward",
        "right",
        "root_extra"
    ]


def ref_attach(parent, child):
    names = ref_child_names()

    for name in names:
        if parent[name] == None:
            parent[name] = child
            return True

    return False


def ref_detach(parent, child):
    names = ref_child_names()

    found = -1

    for index in range(len(names)):
        name = names[index]

        candidate = parent[name]

        if (
            candidate != None
            and candidate["coord"] == child["coord"]
        ):
            found = index
            break

    if found < 0:
        return False

    index = found

    while index < len(names) - 1:
        parent[names[index]] = parent[
            names[index + 1]
        ]

        index += 1

    parent[names[len(names) - 1]] = None

    return True


def ref_create_or_relocate():
    if get_entity_type() != Entities.Treasure:
        plant(
            Entities.Bush
        )

    use_item(
        Items.Weird_Substance,
        ref_substance()
    )


# ==================================================
# INITIAL TREE MAP
# ==================================================

def ref_touch_target():
    global REF_SOLVED
    global REF_TARGET

    if ref_coord() != REF_TARGET:
        return

    ref_create_or_relocate()

    REF_SOLVED += 1
    REF_TARGET = measure()


def ref_explore(
    facing,
    parent,
    distance
):
    global REF_TOTAL_STEPS
    global REF_VISITED
    global REF_NODES

    coord = ref_coord()

    ref_touch_target()

    if coord in REF_VISITED:
        return parent["max_val"]

    explored = set()

    REF_VISITED[coord] = explored

    node = ref_node(
        REF_TOTAL_STEPS,
        coord,
        facing,
        distance
    )

    REF_NODES[coord] = node

    node["parent"] = parent

    ref_attach(
        parent,
        node
    )

    max_value = REF_TOTAL_STEPS

    directions = [
        ref_left(facing),
        facing,
        ref_right(facing)
    ]

    for direction in directions:
        if (
            can_move(direction)
            and direction not in explored
        ):
            move(
                direction
            )

            REF_TOTAL_STEPS += 1

            explored.add(
                direction
            )

            child_max = ref_explore(
                direction,
                node,
                distance + 1
            )

            node["max_val"] = child_max
            max_value = child_max

            if (
                len(REF_VISITED)
                != REF_MAZE_SIZE
                * REF_MAZE_SIZE
            ):
                move(
                    ref_back(direction)
                )

                REF_TOTAL_STEPS += 1

                ref_touch_target()

    node["max_val"] = max_value

    return max_value


def ref_map():
    global REF_ROOT
    global REF_TARGET
    global REF_TOTAL_STEPS
    global REF_VISITED
    global REF_NODES

    coord = ref_coord()

    REF_VISITED[coord] = set()

    REF_TARGET = measure()

    REF_ROOT = ref_node(
        0,
        coord,
        None,
        0
    )

    REF_NODES[coord] = REF_ROOT

    explored = REF_VISITED[coord]

    for direction in REF_DIRECTIONS:
        if (
            can_move(direction)
            and direction not in explored
        ):
            move(
                direction
            )

            REF_TOTAL_STEPS += 1

            explored.add(
                direction
            )

            ref_explore(
                direction,
                REF_ROOT,
                1
            )

            move(
                ref_back(direction)
            )

            if (
                len(REF_VISITED)
                == REF_MAZE_SIZE
                * REF_MAZE_SIZE
            ):
                break

    # The initial DFS order is already a contiguous subtree ordering,
    # but a clean reindex removes any dependence on backtracking step
    # counts and makes the subsequent range-routing invariant explicit.
    ref_reindex_tree(
        REF_ROOT,
        0,
        0
    )


# ==================================================
# TREE MAINTENANCE
# ==================================================

def ref_reindex_tree(
    node,
    value,
    level
):
    node["val"] = value
    node["level"] = level

    max_value = value

    names = ref_child_names()

    for name in names:
        child = node[name]

        if child == None:
            continue

        child["parent"] = node

        max_value = ref_reindex_tree(
            child,
            max_value + 1,
            level + 1
        )

    node["max_val"] = max_value

    return max_value


def ref_is_ancestor(
    ancestor,
    node
):
    current = node

    while current != None:
        if current["coord"] == ancestor["coord"]:
            return True

        current = current["parent"]

    return False


def ref_rotate(
    node,
    new_parent,
    direction_from_parent
):
    old_parent = node["parent"]

    if old_parent != None:
        if (
            old_parent["max_val"]
            == node["max_val"]
        ):
            old_parent["max_val"] = old_parent["val"]

        ref_detach(
            old_parent,
            node
        )

    node["parent"] = new_parent
    node["dir"] = direction_from_parent

    ref_attach(
        new_parent,
        node
    )


def ref_evaluate_new_path(
    node,
    neighbor,
    direction
):
    global REF_ROOT
    global REF_SOLVED

    if REF_SOLVED >= BENCH_REBALANCE_UNTIL:
        return

    if (
        node["level"]
        <= neighbor["level"] + 2
    ):
        return

    if ref_is_ancestor(
        node,
        neighbor
    ):
        return

    ref_rotate(
        node,
        neighbor,
        ref_back(direction)
    )

    ref_reindex_tree(
        REF_ROOT,
        0,
        0
    )


def ref_find_tree_center():
    global REF_ROOT
    global REF_NODES

    leaves = []
    max_depth = 0

    for coord in REF_NODES:
        node = REF_NODES[coord]

        if (
            node["coord"] != REF_ROOT["coord"]
            and node["val"]
            == node["max_val"]
        ):
            leaves.append(
                node
            )

            if node["level"] > max_depth:
                max_depth = node["level"]

    if len(leaves) == 0:
        return REF_ROOT

    branches = leaves

    while len(branches) > 1:
        next_branches = []
        seen = set()

        for node in branches:
            current = node

            if (
                current["coord"] != REF_ROOT["coord"]
                and current["level"] == max_depth
            ):
                current = current["parent"]

            coord = current["coord"]

            if coord not in seen:
                seen.add(
                    coord
                )

                next_branches.append(
                    current
                )

        branches = next_branches
        max_depth -= 1

        if max_depth < 0:
            break

    if len(branches) > 0:
        return branches[0]

    return REF_ROOT


def ref_reroot(new_root):
    global REF_ROOT

    if new_root["coord"] == REF_ROOT["coord"]:
        return

    path = []

    current = new_root

    while current["coord"] != REF_ROOT["coord"]:
        path.append(
            current
        )

        current = current["parent"]

    old_root = REF_ROOT

    index = len(path) - 1

    while index >= 0:
        child = path[index]
        parent = child["parent"]

        ref_detach(
            parent,
            child
        )

        old_direction = child["dir"]

        parent["parent"] = child
        parent["dir"] = ref_back(
            old_direction
        )

        ref_attach(
            child,
            parent
        )

        index -= 1

    new_root["parent"] = None
    new_root["dir"] = None

    REF_ROOT = new_root

    ref_reindex_tree(
        REF_ROOT,
        0,
        0
    )


# ==================================================
# GREEDY SHORTCUT DISCOVERY
# ==================================================

def ref_try_greedy(
    target,
    route,
    update_tree
):
    global REF_VISITED
    global REF_NODES

    current = ref_coord()

    x0, y0 = current
    target_x, target_y = target

    directions = []

    if target_y < y0:
        directions.append(
            South
        )

    elif target_y > y0:
        directions.append(
            North
        )

    if target_x > x0:
        directions.append(
            East
        )

    elif target_x < x0:
        directions.append(
            West
        )

    for direction in directions:
        if not can_move(direction):
            continue

        next_coord = ref_neighbor(
            current,
            direction
        )

        if next_coord in route:
            continue

        explored = REF_VISITED[current]

        if (
            update_tree
            and direction not in explored
        ):
            explored.add(
                direction
            )

            ref_evaluate_new_path(
                REF_NODES[current],
                REF_NODES[next_coord],
                direction
            )

        route.add(
            next_coord
        )

        move(
            direction
        )

        return True

    return False


# ==================================================
# TREE RANGE ROUTING
# ==================================================

def ref_child_for_target(
    node,
    target_value
):
    names = ref_child_names()

    for name in names:
        child = node[name]

        if child == None:
            continue

        if (
            target_value >= child["val"]
            and target_value <= child["max_val"]
        ):
            return child

    return None


def ref_path_to(
    target_coord,
    optimize_pathing
):
    global REF_SOLVED
    global REF_NODES

    current_coord = ref_coord()
    current = REF_NODES[current_coord]

    target = REF_NODES[target_coord]

    target_value = target["val"]

    greedy_from = set()

    steps = 0

    while current_coord != target_coord:
        if (
            current_coord not in greedy_from
            and REF_SOLVED > BENCH_GREEDY_AFTER
        ):
            greedy_from.add(
                current_coord
            )

            while ref_try_greedy(
                target_coord,
                greedy_from,
                optimize_pathing
            ):
                steps += 1

            current_coord = ref_coord()
            current = REF_NODES[current_coord]
            target = REF_NODES[target_coord]
            target_value = target["val"]

        parent = current["parent"]

        if (
            parent != None
            and (
                target_value < current["val"]
                or target_value > current["max_val"]
            )
        ):
            direction = ref_back(
                current["dir"]
            )

            move(
                direction
            )

            steps += 1
            current = parent

        else:
            child = ref_child_for_target(
                current,
                target_value
            )

            if child == None:
                # Should not happen if subtree ranges are valid.
                # Abort this path rather than wandering arbitrarily.
                return steps

            move(
                child["dir"]
            )

            steps += 1
            current = child

        current_coord = ref_coord()

    return steps


# ==================================================
# BENCHMARK ENTRYPOINT
# ==================================================

def run_reference():
    global REF_ROOT
    global REF_VISITED
    global REF_TOTAL_STEPS
    global REF_NODES
    global REF_SOLVED
    global REF_TARGET
    global REF_MAZE_SIZE

    set_world_size(
        BENCH_WORLD_SIZE
    )

    REF_MAZE_SIZE = BENCH_WORLD_SIZE

    REF_ROOT = None
    REF_VISITED = {}
    REF_TOTAL_STEPS = 0
    REF_NODES = {}
    REF_SOLVED = 0
    REF_TARGET = None

    start_ticks = get_tick_count()
    start_time = get_time()

    ref_create_or_relocate()

    ref_map()

    optimize_pathing = False

    while REF_SOLVED < BENCH_SOLVES:
        REF_TARGET = measure()

        ref_path_to(
            REF_TARGET,
            optimize_pathing
        )

        if REF_SOLVED == 40:
            center = ref_find_tree_center()

            ref_reroot(
                center
            )

        if (
            REF_SOLVED > 40
            and REF_SOLVED < 80
        ):
            optimize_pathing = True

        else:
            optimize_pathing = False

        ref_create_or_relocate()

        REF_SOLVED += 1

    # Follow the final relocated treasure and harvest it, matching
    # the reference implementation's end-of-maze behavior.
    REF_TARGET = measure()

    ref_path_to(
        REF_TARGET,
        False
    )

    harvest()

    if BENCH_VERBOSE:
        quick_print(
            "BENCH_REFERENCE",
            BENCH_WORLD_SIZE,
            BENCH_SOLVES,
            get_tick_count() - start_ticks,
            get_time() - start_time
        )



# ------------------------------------------------------------------
# 32x32 AMOUNT-BASED SMALL-MAZE BENCHMARKS
# ------------------------------------------------------------------
#
# These modes deliberately keep the real/simulated world at 32x32.
# Small mazes are created only by changing the amount passed to
# use_item(Items.Weird_Substance, amount). Do not use set_world_size()
# in this benchmark path.
#
# Modes:
# 6 = current full-field reference strategy, fixed Gold target
# 7 = one 3x3 maze covered by one stationary drone per maze cell
# 8 = one 4x4 maze covered by one stationary drone per maze cell
# 9 = two independent 4x4 mazes, 16 stationary drones each
# 10 = 32 independent 4x4 mazes using a source-near zapakh ranked DFS
# 11 = 32 independent 4x4 mazes using the Jan-2026 Steam route/path solver
# 12 = packed 4..7 + zapakh fresh
# 13 = packed 4..7 + zapakh reuse 300
# 14 = msmith93 source-near full 32x32 multi-drone fresh search
# 15 = Feb-2026 Reddit 32x5x5 right-hand map + BFS + reuse
# 16 = Sep-2026 Reddit-described packed fresh intersection DFS
# 17 = mode 16 mutated with visited-set loop handling + reuse
# 18..22 = packed zapakh reuse caps 1, 2, 4, 8, 16
# 23 = packed unranked DFS fresh
# 24 = packed unranked DFS reuse 300
# 25 = uniform 32x4x4 zapakh fresh
# 26 = uniform 32x5x5 zapakh reuse 300
# 27 = uniform 32x5x5 zapakh fresh
# 28 = packed map+BFS reuse 300
# 29 = packed map+BFS fresh
# 30 = uniform 32x4x4 map+BFS reuse 300
# 31 = uniform 32x4x4 zapakh reuse 8


SPEC_DIRECTIONS = [
    North,
    East,
    South,
    West
]


def spec_back(direction):
    if direction == North:
        return South

    if direction == South:
        return North

    if direction == East:
        return West

    return East


def spec_neighbor(coord, direction):
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


def spec_move_to(x, y):
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


def spec_substance(maze_size):
    return (
        maze_size
        * 2**(
            num_unlocked(Unlocks.Mazes)
            - 1
        )
    )


def spec_gold_done(start_gold):
    return (
        num_items(Items.Gold)
        - start_gold
        >= BENCH_GOLD_TARGET
    )


def spec_create_maze(maze_size):
    plant(
        Entities.Bush
    )

    use_item(
        Items.Weird_Substance,
        spec_substance(maze_size)
    )


def spec_relocate(maze_size):
    return use_item(
        Items.Weird_Substance,
        spec_substance(maze_size)
    )


# ==================================================
# CURRENT 32x32 REFERENCE, FIXED GOLD TARGET
# ==================================================


def spec_reset_reference():
    global REF_ROOT
    global REF_VISITED
    global REF_TOTAL_STEPS
    global REF_NODES
    global REF_SOLVED
    global REF_TARGET
    global REF_MAZE_SIZE

    REF_ROOT = None
    REF_VISITED = {}
    REF_TOTAL_STEPS = 0
    REF_NODES = {}
    REF_SOLVED = 0
    REF_TARGET = None
    REF_MAZE_SIZE = get_world_size()


def spec_run_reference_target():
    global REF_SOLVED
    global REF_TARGET

    clear()

    start_gold = num_items(
        Items.Gold
    )

    while not spec_gold_done(
        start_gold
    ):
        spec_reset_reference()

        ref_create_or_relocate()
        ref_map()

        optimize_pathing = False

        while (
            REF_SOLVED < 300
            and not spec_gold_done(
                start_gold
            )
        ):
            REF_TARGET = measure()

            ref_path_to(
                REF_TARGET,
                optimize_pathing
            )

            if REF_SOLVED == 40:
                center = ref_find_tree_center()

                ref_reroot(
                    center
                )

            if (
                REF_SOLVED > 40
                and REF_SOLVED < 80
            ):
                optimize_pathing = True

            else:
                optimize_pathing = False

            ref_create_or_relocate()
            REF_SOLVED += 1

        if spec_gold_done(
            start_gold
        ):
            return

        REF_TARGET = measure()

        ref_path_to(
            REF_TARGET,
            False
        )

        harvest()


# ==================================================
# STATIONARY FULL-COVERAGE SMALL MAZES
# ==================================================


def spec_cover_worker(
    maze_size,
    start_gold,
    creator
):
    while not spec_gold_done(
        start_gold
    ):
        entity = get_entity_type()

        if entity == Entities.Treasure:
            # measure() keeps returning the Treasure position after the
            # 300-reuse limit. use_item() is the reliable cap signal:
            # it fails once the Treasure can no longer be relocated.
            if not spec_relocate(
                maze_size
            ):
                harvest()

        elif (
            creator
            and entity == Entities.Grass
        ):
            spec_create_maze(
                maze_size
            )


def spec_cover_prepare(
    maze_size,
    start_gold
):
    root = (
        get_pos_x(),
        get_pos_y()
    )

    # First build a temporary Maze with no coverage workers. Mapping must
    # stay single-drone so Treasure relocation cannot mutate walls while
    # the set of Maze cells is still being discovered.
    spec_create_maze(
        maze_size
    )

    graph, parent = map_fresh_maze()

    target = measure()

    if target != None:
        move_bfs(
            graph,
            target
        )

    if (
        get_entity_type()
        == Entities.Treasure
    ):
        harvest()

    # The temporary Maze is gone. Return to its fixed root while the farm
    # is open, then place one waiting worker on every other discovered cell.
    spec_move_to(
        root[0],
        root[1]
    )

    for coord in graph:
        if coord == root:
            continue

        spec_move_to(
            coord[0],
            coord[1]
        )

        spawn_drone(
            spec_cover_worker,
            maze_size,
            start_gold,
            False
        )

    spec_move_to(
        root[0],
        root[1]
    )

    return root


def spec_cover_maze(
    maze_size,
    start_gold
):
    root = spec_cover_prepare(
        maze_size,
        start_gold
    )

    # Existing children are already sitting on all non-root Maze cells. The
    # creator owns the root cell and recreates the Maze after its final
    # Treasure is harvested.
    spec_create_maze(
        maze_size
    )

    spec_cover_worker(
        maze_size,
        start_gold,
        True
    )


def spec_run_single_cover(
    maze_size
):
    clear()

    start_gold = num_items(
        Items.Gold
    )

    spec_move_to(
        16,
        16
    )

    spec_cover_maze(
        maze_size,
        start_gold
    )


def spec_cover_wait_start(
    maze_size,
    start_gold,
    start_water
):
    while (
        num_items(Items.Water)
        == start_water
    ):
        pass

    spec_cover_maze(
        maze_size,
        start_gold
    )


def spec_run_double_cover():
    clear()

    start_gold = num_items(
        Items.Gold
    )

    start_water = num_items(
        Items.Water
    )

    spec_move_to(
        8,
        8
    )

    spawn_drone(
        spec_cover_wait_start,
        4,
        start_gold,
        start_water
    )

    spec_move_to(
        24,
        24
    )

    use_item(
        Items.Water
    )

    spec_cover_maze(
        4,
        start_gold
    )


# ==================================================
# ZAPAKH GIST: SOURCE-NEAR RANKED IN-SITU DFS
# ==================================================


def spec_ranked_dirs(
    pos_x,
    pos_y,
    goal_x,
    goal_y,
    exclude
):
    if goal_x == None:
        all_dirs = [
            (1, North),
            (2, East),
            (3, South),
            (4, West)
        ]

    else:
        all_dirs = [
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

    ranked_dirs = []

    for _ in range(
        len(all_dirs)
    ):
        worst_dir = min(
            all_dirs
        )

        all_dirs.remove(
            worst_dir
        )

        if worst_dir[1] != exclude:
            ranked_dirs.append(
                worst_dir[1]
            )

    return ranked_dirs


def spec_zapakh_find(
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
        dirs, back = stack[
            len(stack) - 1
        ]

        old_x = x
        old_y = y
        direction = None

        while len(dirs) > 0:
            direction = dirs.pop()

            next_coord = spec_neighbor(
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

            back = spec_back(
                direction
            )

            stack.append(
                (
                    spec_ranked_dirs(
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


def spec_zapakh_solve_current(
    start_gold,
    maze_size,
    reuse_limit
):
    solved = 0

    while (
        solved < reuse_limit
        and not spec_gold_done(
            start_gold
        )
    ):
        goal = measure()

        if goal == None:
            if (
                get_entity_type()
                == Entities.Treasure
            ):
                harvest()

            return True

        goal_x, goal_y = goal

        if not spec_zapakh_find(
            goal_x,
            goal_y
        ):
            return False

        if not spec_relocate(
            maze_size
        ):
            harvest()
            return True

        solved += 1

    if spec_gold_done(
        start_gold
    ):
        return True

    goal = measure()

    if (
        get_entity_type()
        != Entities.Treasure
        and goal != None
    ):
        goal_x, goal_y = goal

        if not spec_zapakh_find(
            goal_x,
            goal_y
        ):
            return False

    if (
        get_entity_type()
        == Entities.Treasure
    ):
        harvest()

    return True


def spec_zapakh_run(
    origin_x,
    origin_y,
    start_gold,
    maze_size,
    maze_ready
):
    while not spec_gold_done(
        start_gold
    ):
        if not maze_ready:
            spec_create_maze(
                maze_size
            )

        maze_ready = False

        if not spec_zapakh_solve_current(
            start_gold,
            maze_size,
            300
        ):
            return

        if spec_gold_done(
            start_gold
        ):
            return

        if not spec_move_to(
            origin_x,
            origin_y
        ):
            quick_print(
                "MAZE RETURN BLOCKED",
                origin_x,
                origin_y
            )
            return


def spec_zapakh_worker(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    start_substance
):
    spec_move_to(
        origin_x,
        origin_y
    )

    plant(
        Entities.Bush
    )

    # The parent changes Weird Substance only after all 31 child origins
    # have been verified as ready. This is a deterministic shared-world
    # barrier; unlike Water, the signal action is guaranteed to be the
    # creation of the parent's own 4x4 Maze.
    while (
        num_items(Items.Weird_Substance)
        == start_substance
    ):
        pass

    if not spec_relocate(
        maze_size
    ):
        return

    spec_zapakh_run(
        origin_x,
        origin_y,
        start_gold,
        maze_size,
        True
    )


# ==================================================
# SEP-2026 REDDIT: 32-SQUARE FULL-FIELD PACKING
# ==================================================
#
# Reference:
# https://www.reddit.com/r/TheFarmerWasReplaced/comments/1wjxxhx/
#
# The thread describes filling a 32x32 field with exactly 32 square Mazes,
# one per drone, and reports that reducing the maximum individual Maze size
# improves leaderboard throughput. A linked community layout uses integer
# square sizes 4..7.
#
# The exact-cover layout below was independently reconstructed from those
# constraints and verified to cover all 1024 cells exactly once:
#
#   12 x 4x4
#    4 x 5x5
#    4 x 6x6
#   12 x 7x7
#
# Each entry is [lower_left_x, lower_left_y, maze_size].
#
# Mode 12 recreates a fresh Maze after every Treasure, matching the Reddit
# OP's no-reuse assumption.
# Mode 13 uses the same packing with our loop-safe zapakh DFS and Maze reuse.


SPEC_PACKED_32 = [
    [0, 0, 7],
    [7, 0, 7],
    [14, 0, 7],
    [21, 0, 7],
    [28, 0, 4],
    [28, 4, 4],
    [0, 7, 7],
    [7, 7, 7],
    [14, 7, 7],
    [21, 7, 7],
    [28, 8, 4],
    [28, 12, 4],
    [0, 14, 4],
    [4, 14, 4],
    [8, 14, 7],
    [15, 14, 7],
    [22, 14, 6],
    [28, 16, 4],
    [0, 18, 4],
    [4, 18, 4],
    [22, 20, 5],
    [27, 20, 5],
    [8, 21, 5],
    [13, 21, 5],
    [18, 21, 4],
    [0, 22, 4],
    [4, 22, 4],
    [18, 25, 7],
    [25, 25, 7],
    [0, 26, 6],
    [6, 26, 6],
    [12, 26, 6]
]


def spec_packed_origin(
    square
):
    return (
        square[0]
        + square[2] // 2,
        square[1]
        + square[2] // 2
    )


def spec_zapakh_fresh_current(
    start_gold
):
    goal = measure()

    if goal == None:
        return False

    goal_x, goal_y = goal

    if not spec_zapakh_find(
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


def spec_packed_run(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    maze_ready,
    reuse_limit
):
    while not spec_gold_done(
        start_gold
    ):
        if not maze_ready:
            spec_create_maze(
                maze_size
            )

        maze_ready = False

        if reuse_limit > 0:
            if not spec_zapakh_solve_current(
                start_gold,
                maze_size,
                reuse_limit
            ):
                return

        else:
            if not spec_zapakh_fresh_current(
                start_gold
            ):
                return

        if spec_gold_done(
            start_gold
        ):
            return

        if not spec_move_to(
            origin_x,
            origin_y
        ):
            quick_print(
                "MAZE RETURN BLOCKED",
                origin_x,
                origin_y
            )
            return


def spec_packed_worker(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    start_substance,
    reuse_limit
):
    spec_move_to(
        origin_x,
        origin_y
    )

    plant(
        Entities.Bush
    )

    while (
        num_items(Items.Weird_Substance)
        == start_substance
    ):
        pass

    if not spec_relocate(
        maze_size
    ):
        return

    spec_packed_run(
        origin_x,
        origin_y,
        maze_size,
        start_gold,
        True,
        reuse_limit
    )


def spec_run_packed_32(
    reuse_limit
):
    clear()

    start_gold = num_items(
        Items.Gold
    )

    start_substance = num_items(
        Items.Weird_Substance
    )

    child_origins = []

    index = 0

    while index < len(
        SPEC_PACKED_32
    ) - 1:
        square = SPEC_PACKED_32[
            index
        ]

        origin = spec_packed_origin(
            square
        )

        child_origins.append(
            origin
        )

        spawn_drone(
            spec_packed_worker,
            origin[0],
            origin[1],
            square[2],
            start_gold,
            start_substance,
            reuse_limit
        )

        index += 1

    for origin in child_origins:
        spec_wait_for_bush(
            origin[0],
            origin[1]
        )

    if reuse_limit > 0:
        label = "PACKED REUSE READY"
    else:
        label = "PACKED FRESH READY"

    quick_print(
        label,
        len(child_origins)
    )

    parent_square = SPEC_PACKED_32[
        len(SPEC_PACKED_32) - 1
    ]

    parent_origin = spec_packed_origin(
        parent_square
    )

    spec_move_to(
        parent_origin[0],
        parent_origin[1]
    )

    plant(
        Entities.Bush
    )

    if not spec_relocate(
        parent_square[2]
    ):
        return

    spec_packed_run(
        parent_origin[0],
        parent_origin[1],
        parent_square[2],
        start_gold,
        True,
        reuse_limit
    )


# ==================================================
# EXTENDED SMALL-MAZE SOLVER ABLATIONS
# ==================================================


def spec_unranked_find():
    x = get_pos_x()
    y = get_pos_y()

    stack = [
        (
            [
                West,
                South,
                East,
                North
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
        dirs, back = stack[
            len(stack) - 1
        ]

        direction = None

        while len(dirs) > 0:
            candidate = dirs.pop()

            next_coord = spec_neighbor(
                (x, y),
                candidate
            )

            if (
                next_coord in visited
                or not move(candidate)
            ):
                continue

            direction = candidate
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

            stack.append(
                (
                    [
                        West,
                        South,
                        East,
                        North
                    ],
                    spec_back(
                        direction
                    )
                )
            )

    return True


def spec_reddit_score(
    direction,
    pos_x,
    pos_y,
    goal_x,
    goal_y
):
    if direction == North:
        return goal_y - pos_y

    if direction == East:
        return goal_x - pos_x

    if direction == South:
        return pos_y - goal_y

    return pos_x - goal_x


def spec_reddit_rank(
    options,
    goal_x,
    goal_y
):
    pool = []

    for direction in options:
        pool.append(
            direction
        )

    ranked = []

    pos_x = get_pos_x()
    pos_y = get_pos_y()

    while len(pool) > 0:
        best_index = 0
        best_score = spec_reddit_score(
            pool[0],
            pos_x,
            pos_y,
            goal_x,
            goal_y
        )

        index = 1

        while index < len(pool):
            score = spec_reddit_score(
                pool[index],
                pos_x,
                pos_y,
                goal_x,
                goal_y
            )

            if score > best_score:
                best_score = score
                best_index = index

            index += 1

        ranked.append(
            pool.pop(
                best_index
            )
        )

    return ranked


def spec_reddit_find(
    goal_x,
    goal_y,
    avoid_visited
):
    # Behavioral reconstruction of the September 2026 Reddit description:
    # keep walking forced corridors, record only intersections, rank branches
    # toward the Treasure, and rewind the recorded movement on dead ends.
    trail = []
    frames = []

    visited = {
        (
            get_pos_x(),
            get_pos_y()
        )
    }

    while (
        get_entity_type()
        != Entities.Treasure
    ):
        back = None

        if len(trail) > 0:
            back = spec_back(
                trail[
                    len(trail) - 1
                ]
            )

        options = []
        current = (
            get_pos_x(),
            get_pos_y()
        )

        for direction in SPEC_DIRECTIONS:
            if direction == back:
                continue

            if not can_move(
                direction
            ):
                continue

            next_coord = spec_neighbor(
                current,
                direction
            )

            if (
                avoid_visited
                and next_coord in visited
            ):
                continue

            options.append(
                direction
            )

        if len(options) > 0:
            ranked = spec_reddit_rank(
                options,
                goal_x,
                goal_y
            )

            chosen = ranked[0]

            if len(ranked) > 1:
                remaining = []
                index = len(ranked) - 1

                while index >= 1:
                    remaining.append(
                        ranked[index]
                    )
                    index -= 1

                frames.append(
                    [
                        len(trail),
                        remaining
                    ]
                )

            if not move(
                chosen
            ):
                return False

            trail.append(
                chosen
            )

            if avoid_visited:
                visited.add(
                    (
                        get_pos_x(),
                        get_pos_y()
                    )
                )

            continue

        advanced = False

        while len(frames) > 0:
            frame = frames[
                len(frames) - 1
            ]

            while (
                len(trail)
                > frame[0]
            ):
                move(
                    spec_back(
                        trail.pop()
                    )
                )

            if len(frame[1]) > 0:
                chosen = frame[1].pop()

                if not move(
                    chosen
                ):
                    return False

                trail.append(
                    chosen
                )

                if avoid_visited:
                    visited.add(
                        (
                            get_pos_x(),
                            get_pos_y()
                        )
                    )

                advanced = True
                break

            frames.pop()

        if not advanced:
            return False

    return True


def spec_solver_find(
    solver_mode,
    goal_x,
    goal_y
):
    if solver_mode == 0:
        return spec_zapakh_find(
            goal_x,
            goal_y
        )

    if solver_mode == 1:
        return spec_unranked_find()

    if solver_mode == 2:
        return spec_reddit_find(
            goal_x,
            goal_y,
            False
        )

    return spec_reddit_find(
        goal_x,
        goal_y,
        True
    )


def spec_solver_fresh(
    start_gold,
    solver_mode
):
    goal = measure()

    if goal == None:
        return False

    if not spec_solver_find(
        solver_mode,
        goal[0],
        goal[1]
    ):
        return False

    if (
        get_entity_type()
        != Entities.Treasure
    ):
        return False

    harvest()

    return True


def spec_solver_reuse(
    start_gold,
    maze_size,
    solver_mode,
    reuse_limit
):
    solved = 0

    while (
        solved < reuse_limit
        and not spec_gold_done(
            start_gold
        )
    ):
        goal = measure()

        if goal == None:
            return False

        if not spec_solver_find(
            solver_mode,
            goal[0],
            goal[1]
        ):
            return False

        if not spec_relocate(
            maze_size
        ):
            harvest()
            return True

        solved += 1

    if spec_gold_done(
        start_gold
    ):
        return True

    goal = measure()

    if goal != None:
        if not spec_solver_find(
            solver_mode,
            goal[0],
            goal[1]
        ):
            return False

    if (
        get_entity_type()
        == Entities.Treasure
    ):
        harvest()
        return True

    return False


def spec_search_run(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    maze_ready,
    solver_mode,
    reuse_limit
):
    while not spec_gold_done(
        start_gold
    ):
        if not maze_ready:
            spec_create_maze(
                maze_size
            )

        maze_ready = False

        if reuse_limit > 0:
            if not spec_solver_reuse(
                start_gold,
                maze_size,
                solver_mode,
                reuse_limit
            ):
                return

        else:
            if not spec_solver_fresh(
                start_gold,
                solver_mode
            ):
                return

        if spec_gold_done(
            start_gold
        ):
            return

        if not spec_move_to(
            origin_x,
            origin_y
        ):
            quick_print(
                "MAZE RETURN BLOCKED",
                origin_x,
                origin_y
            )
            return


def spec_search_worker(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    start_substance,
    solver_mode,
    reuse_limit
):
    spec_move_to(
        origin_x,
        origin_y
    )

    plant(
        Entities.Bush
    )

    while (
        num_items(
            Items.Weird_Substance
        )
        == start_substance
    ):
        pass

    if not spec_relocate(
        maze_size
    ):
        return

    spec_search_run(
        origin_x,
        origin_y,
        maze_size,
        start_gold,
        True,
        solver_mode,
        reuse_limit
    )


def spec_layout_square(
    layout_mode,
    index
):
    if layout_mode == 0:
        return SPEC_PACKED_32[
            index
        ]

    if layout_mode == 1:
        return [
            (
                index % 8
            ) * 4,
            (
                index // 8
            ) * 4,
            4
        ]

    # 32 of the 36 non-overlapping 5x5 slots in a 6x6 grid.
    return [
        (
            index % 6
        ) * 5,
        (
            index // 6
        ) * 5,
        5
    ]


def spec_run_search_layout(
    layout_mode,
    solver_mode,
    reuse_limit,
    label
):
    clear()

    start_gold = num_items(
        Items.Gold
    )

    start_substance = num_items(
        Items.Weird_Substance
    )

    child_origins = []

    index = 0

    while index < 31:
        square = spec_layout_square(
            layout_mode,
            index
        )

        origin = spec_packed_origin(
            square
        )

        child_origins.append(
            origin
        )

        spawn_drone(
            spec_search_worker,
            origin[0],
            origin[1],
            square[2],
            start_gold,
            start_substance,
            solver_mode,
            reuse_limit
        )

        index += 1

    for origin in child_origins:
        spec_wait_for_bush(
            origin[0],
            origin[1]
        )

    quick_print(
        label,
        "READY",
        len(child_origins)
    )

    square = spec_layout_square(
        layout_mode,
        31
    )

    origin = spec_packed_origin(
        square
    )

    spec_move_to(
        origin[0],
        origin[1]
    )

    plant(
        Entities.Bush
    )

    if not spec_relocate(
        square[2]
    ):
        return

    spec_search_run(
        origin[0],
        origin[1],
        square[2],
        start_gold,
        True,
        solver_mode,
        reuse_limit
    )


# ==================================================
# FEB-2026 REDDIT: RIGHT-HAND MAP + BFS + REUSE
# ==================================================


def spec_graph_ensure(
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


def spec_graph_scan(
    graph
):
    current = (
        get_pos_x(),
        get_pos_y()
    )

    spec_graph_ensure(
        graph,
        current
    )

    changed = False

    for index in range(4):
        direction = SPEC_DIRECTIONS[
            index
        ]

        if not can_move(
            direction
        ):
            continue

        next_coord = spec_neighbor(
            current,
            direction
        )

        spec_graph_ensure(
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


def spec_turn_right(
    direction
):
    if direction == North:
        return East

    if direction == East:
        return South

    if direction == South:
        return West

    return North


def spec_turn_left(
    direction
):
    if direction == North:
        return West

    if direction == West:
        return South

    if direction == South:
        return East

    return North


def spec_map_right_hand(
    maze_size
):
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

        spec_graph_scan(
            graph
        )

        if (
            moved
            and len(visited)
            >= maze_size * maze_size
            and current == start
        ):
            return graph

        candidates = [
            spec_turn_right(
                direction
            ),
            direction,
            spec_turn_left(
                direction
            ),
            spec_back(
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


def spec_graph_bfs_path(
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

            next_coord = spec_neighbor(
                current,
                SPEC_DIRECTIONS[
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


def spec_graph_move_bfs(
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

        spec_graph_scan(
            graph
        )

        path = spec_graph_bfs_path(
            graph,
            current,
            target
        )

        if len(path) == 0:
            return False

        while len(path) > 0:
            if spec_graph_scan(
                graph
            ):
                break

            next_coord = path.pop()
            current = (
                get_pos_x(),
                get_pos_y()
            )

            direction = None

            for candidate in SPEC_DIRECTIONS:
                if (
                    spec_neighbor(
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


def spec_map_bfs_run(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    maze_ready,
    reuse_limit
):
    while not spec_gold_done(
        start_gold
    ):
        if not maze_ready:
            spec_create_maze(
                maze_size
            )

        maze_ready = False

        graph = spec_map_right_hand(
            maze_size
        )

        if reuse_limit <= 0:
            target = measure()

            if (
                target == None
                or not spec_graph_move_bfs(
                    graph,
                    target
                )
            ):
                return

            if (
                get_entity_type()
                != Entities.Treasure
            ):
                return

            harvest()

            if spec_gold_done(
                start_gold
            ):
                return

            if not spec_move_to(
                origin_x,
                origin_y
            ):
                quick_print(
                    "MAZE RETURN BLOCKED",
                    origin_x,
                    origin_y
                )
                return

            continue

        solved = 0

        while (
            solved < reuse_limit
            and not spec_gold_done(
                start_gold
            )
        ):
            target = measure()

            if target == None:
                return

            if not spec_graph_move_bfs(
                graph,
                target
            ):
                return

            if not spec_relocate(
                maze_size
            ):
                harvest()
                break

            solved += 1

        if spec_gold_done(
            start_gold
        ):
            return

        if (
            get_entity_type()
            != Entities.Treasure
        ):
            target = measure()

            if target != None:
                spec_graph_move_bfs(
                    graph,
                    target
                )

        if (
            get_entity_type()
            == Entities.Treasure
        ):
            harvest()

        if not spec_move_to(
            origin_x,
            origin_y
        ):
            quick_print(
                "MAZE RETURN BLOCKED",
                origin_x,
                origin_y
            )
            return


def spec_map_bfs_worker(
    origin_x,
    origin_y,
    maze_size,
    start_gold,
    start_substance,
    reuse_limit
):
    spec_move_to(
        origin_x,
        origin_y
    )

    plant(
        Entities.Bush
    )

    while (
        num_items(
            Items.Weird_Substance
        )
        == start_substance
    ):
        pass

    if not spec_relocate(
        maze_size
    ):
        return

    spec_map_bfs_run(
        origin_x,
        origin_y,
        maze_size,
        start_gold,
        True,
        reuse_limit
    )


def spec_run_map_bfs_layout(
    layout_mode,
    reuse_limit,
    label
):
    clear()

    start_gold = num_items(
        Items.Gold
    )

    start_substance = num_items(
        Items.Weird_Substance
    )

    origins = []

    index = 0

    while index < 31:
        square = spec_layout_square(
            layout_mode,
            index
        )

        origin = spec_packed_origin(
            square
        )

        origins.append(
            origin
        )

        spawn_drone(
            spec_map_bfs_worker,
            origin[0],
            origin[1],
            square[2],
            start_gold,
            start_substance,
            reuse_limit
        )

        index += 1

    for origin in origins:
        spec_wait_for_bush(
            origin[0],
            origin[1]
        )

    quick_print(
        label,
        "READY",
        len(origins)
    )

    square = spec_layout_square(
        layout_mode,
        31
    )

    origin = spec_packed_origin(
        square
    )

    spec_move_to(
        origin[0],
        origin[1]
    )

    plant(
        Entities.Bush
    )

    if not spec_relocate(
        square[2]
    ):
        return

    spec_map_bfs_run(
        origin[0],
        origin[1],
        square[2],
        start_gold,
        True,
        reuse_limit
    )


# ==================================================
# MSMITH93 MULTI-DRONE FULL-MAZE SOURCE-NEAR REFERENCE
# ==================================================


def spec_msmith_dirs(
    drone_id
):
    dirs = [
        North,
        South,
        East,
        West
    ]

    if drone_id % 2:
        dirs = [
            West,
            East,
            South,
            North
        ]

    if drone_id % 3:
        value = dirs[0]
        dirs[0] = dirs[1]
        dirs[1] = value

    if drone_id % 5:
        value = dirs[1]
        dirs[1] = dirs[3]
        dirs[3] = value

    return dirs


def spec_msmith_explore(
    start_direction,
    dirs,
    start_gold
):
    if not move(
        start_direction
    ):
        return False

    path_stack = [
        (
            start_direction,
            0
        )
    ]

    while (
        len(path_stack) > 0
        and not spec_gold_done(
            start_gold
        )
    ):
        if (
            get_entity_type()
            == Entities.Treasure
        ):
            harvest()

            if not spec_gold_done(
                start_gold
            ):
                spec_create_maze(
                    get_world_size()
                )

            return True

        last_direction, next_index = (
            path_stack[
                len(path_stack) - 1
            ]
        )

        moved = False

        while next_index < len(dirs):
            explore_direction = dirs[
                next_index
            ]

            path_stack[
                len(path_stack) - 1
            ] = (
                last_direction,
                next_index + 1
            )

            if (
                spec_back(
                    explore_direction
                )
                != last_direction
                and move(
                    explore_direction
                )
            ):
                path_stack.append(
                    (
                        explore_direction,
                        0
                    )
                )

                moved = True
                break

            next_index += 1

        if not moved:
            path_stack.pop()

            move(
                spec_back(
                    last_direction
                )
            )

    move(
        spec_back(
            start_direction
        )
    )

    return False


def spec_msmith_search(
    drone_id,
    start_gold
):
    for _ in range(
        drone_id
    ):
        do_a_flip()

    dirs = spec_msmith_dirs(
        drone_id
    )

    while not spec_gold_done(
        start_gold
    ):
        found = False

        for direction in dirs:
            if spec_msmith_explore(
                direction,
                dirs,
                start_gold
            ):
                found = True
                break

        if not found:
            return False

    return True


def spec_run_msmith93():
    clear()

    start_gold = num_items(
        Items.Gold
    )

    spec_create_maze(
        get_world_size()
    )

    handles = []

    drone_id = 1

    while drone_id < max_drones():
        drone = spawn_drone(
            spec_msmith_search,
            drone_id,
            start_gold
        )

        if drone == None:
            break

        handles.append(
            drone
        )

        drone_id += 1

    spec_msmith_search(
        0,
        start_gold
    )

    for drone in handles:
        wait_for(
            drone
        )


# ==================================================
# JAN-2026 STEAM: 32 INDEPENDENT 4x4 MAZES
# ==================================================


def spec_steam_next_move(
    heading
):
    for offset in [
        1,
        0,
        3,
        2
    ]:
        direction = SPEC_DIRECTIONS[
            (heading + offset) % 4
        ]

        if can_move(
            direction
        ):
            return direction

    return None


def spec_steam_move(
    heading
):
    for offset in [
        1,
        0,
        3,
        2
    ]:
        next_heading = (
            heading + offset
        ) % 4

        if move(
            SPEC_DIRECTIONS[
                next_heading
            ]
        ):
            return next_heading

    return heading


def spec_steam_moves():
    moves = {}

    current = (
        get_pos_x(),
        get_pos_y()
    )

    for direction in SPEC_DIRECTIONS:
        if can_move(
            direction
        ):
            moves[
                spec_neighbor(
                    current,
                    direction
                )
            ] = direction

    return moves


def spec_steam_path_move(
    paths,
    from_loc,
    to_loc,
    depth,
    visited
):
    if to_loc in visited:
        return False

    visited[to_loc] = True

    for loc in paths[to_loc]:
        if loc == from_loc:
            move(
                paths[loc][to_loc]
            )

            return True

        if depth > 0:
            if spec_steam_path_move(
                paths,
                from_loc,
                loc,
                depth - 1,
                visited
            ):
                move(
                    paths[loc][to_loc]
                )

                return True

    return False


def spec_steam_distance(
    location
):
    return (
        abs(
            get_pos_x()
            - location[0]
        )
        + abs(
            get_pos_y()
            - location[1]
        )
    )


def spec_steam_hunt(
    start_gold
):
    heading = 0

    start_x = get_pos_x()
    start_y = get_pos_y()

    paths = {}
    route = []

    while (
        spec_steam_distance(
            (start_x, start_y)
        ) > 0
        or len(paths) < 16
    ):
        route.append(
            spec_steam_next_move(
                heading
            )
        )

        paths[
            (
                get_pos_x(),
                get_pos_y()
            )
        ] = spec_steam_moves()

        heading = spec_steam_move(
            heading
        )

    found = 0

    while (
        found < 200
        and not spec_gold_done(
            start_gold
        )
    ):
        for direction in route:
            if (
                get_entity_type()
                == Entities.Treasure
            ):
                if measure() == None:
                    harvest()
                    return -1

                if not spec_relocate(
                    4
                ):
                    harvest()
                    return -1

                found += 1

                if spec_gold_done(
                    start_gold
                ):
                    return found

            move(
                direction
            )

        for direction in route:
            paths[
                (
                    get_pos_x(),
                    get_pos_y()
                )
            ] = spec_steam_moves()

            move(
                direction
            )

    while (
        found < 300
        and not spec_gold_done(
            start_gold
        )
    ):
        target = measure()

        if target == None:
            harvest()
            return -1

        depth = spec_steam_distance(
            target
        )

        while not spec_steam_path_move(
            paths,
            (
                get_pos_x(),
                get_pos_y()
            ),
            target,
            depth,
            {}
        ):
            depth += 1

        if not spec_relocate(
            4
        ):
            harvest()
            return -1

        found += 1

    return found


def spec_steam_run(
    origin_x,
    origin_y,
    start_gold,
    maze_ready
):
    while not spec_gold_done(
        start_gold
    ):
        if not maze_ready:
            spec_create_maze(
                4
            )

        maze_ready = False

        found = spec_steam_hunt(
            start_gold
        )

        if spec_gold_done(
            start_gold
        ):
            return

        if found < 0:
            spec_move_to(
                origin_x,
                origin_y
            )
            continue

        if found >= 300:
            target = measure()

            if (
                get_entity_type()
                != Entities.Treasure
                and target != None
            ):
                goal_x, goal_y = target

                spec_zapakh_find(
                    goal_x,
                    goal_y
                )

        if (
            get_entity_type()
            == Entities.Treasure
        ):
            harvest()

        if not spec_move_to(
            origin_x,
            origin_y
        ):
            quick_print(
                "MAZE RETURN BLOCKED",
                origin_x,
                origin_y
            )
            return


def spec_steam_worker(
    origin_x,
    origin_y,
    start_gold,
    start_substance
):
    spec_move_to(
        origin_x,
        origin_y
    )

    # Preserved from the January 2026 community implementation.
    do_a_flip()

    plant(
        Entities.Bush
    )

    while (
        num_items(Items.Weird_Substance)
        == start_substance
    ):
        pass

    if not spec_relocate(
        4
    ):
        return

    spec_steam_run(
        origin_x,
        origin_y,
        start_gold,
        True
    )


# ==================================================
# 32-WORKER GRID LAUNCHER
# ==================================================


def spec_wait_for_bush(
    x,
    y
):
    spec_move_to(
        x,
        y
    )

    while (
        get_entity_type()
        != Entities.Bush
    ):
        pass


def spec_run_32x4():
    clear()

    start_gold = num_items(
        Items.Gold
    )

    start_substance = num_items(
        Items.Weird_Substance
    )

    child_origins = []

    worker_index = 0
    last_x = 30
    last_y = 14

    for row in range(4):
        for column in range(8):
            x = column * 4 + 2
            y = row * 4 + 2

            if worker_index < 31:
                child_origins.append(
                    (x, y)
                )

                spawn_drone(
                    spec_zapakh_worker,
                    x,
                    y,
                    4,
                    start_gold,
                    start_substance
                )

            else:
                last_x = x
                last_y = y

            worker_index += 1

    # No Maze exists yet. Verify that every child has reached its assigned
    # origin and planted its ready Bush before releasing the barrier.
    for origin in child_origins:
        spec_wait_for_bush(
            origin[0],
            origin[1]
        )

    quick_print(
        "ZAPAKH READY",
        len(child_origins)
    )

    spec_move_to(
        last_x,
        last_y
    )

    plant(
        Entities.Bush
    )

    if not spec_relocate(
        4
    ):
        return

    spec_zapakh_run(
        last_x,
        last_y,
        start_gold,
        4,
        True
    )


def spec_run_steam_32x4():
    clear()

    start_gold = num_items(
        Items.Gold
    )

    start_substance = num_items(
        Items.Weird_Substance
    )

    parent_x = 14
    parent_y = 30

    spec_move_to(
        parent_x,
        parent_y
    )

    child_origins = []
    worker_index = 0

    # Preserve the source correction's 8x8 spawn attempts. With 32 drones,
    # the first 31 children wait at their origins and all later attempts fail.
    for i in range(8):
        for j in range(8):
            x = i * 4 + 2
            y = j * 4 + 2

            if worker_index < 31:
                child_origins.append(
                    (x, y)
                )

            spawn_drone(
                spec_steam_worker,
                x,
                y,
                start_gold,
                start_substance
            )

            worker_index += 1

    for origin in child_origins:
        spec_wait_for_bush(
            origin[0],
            origin[1]
        )

    quick_print(
        "STEAM READY",
        len(child_origins)
    )

    spec_move_to(
        parent_x,
        parent_y
    )

    # Preserved from the source worker.
    do_a_flip()

    plant(
        Entities.Bush
    )

    if not spec_relocate(
        4
    ):
        return

    spec_steam_run(
        parent_x,
        parent_y,
        start_gold,
        True
    )


def spec_report_result(
    start_gold,
    start_substance,
    start_ticks
):
    gained = (
        num_items(Items.Gold)
        - start_gold
    )

    substance_used = (
        start_substance
        - num_items(
            Items.Weird_Substance
        )
    )

    status = "FAIL"

    if gained >= BENCH_GOLD_TARGET:
        status = "PASS"

    quick_print(
        "MAZE SPECIAL RESULT",
        BENCH_MODE,
        "gold gained",
        gained,
        "target",
        BENCH_GOLD_TARGET,
        "substance used",
        substance_used,
        "ticks",
        get_tick_count() - start_ticks,
        status
    )


def run_special():
    start_gold = num_items(
        Items.Gold
    )

    start_substance = num_items(
        Items.Weird_Substance
    )

    start_ticks = get_tick_count()

    if BENCH_MODE == 6:
        spec_run_reference_target()

    elif BENCH_MODE == 7:
        spec_run_single_cover(
            3
        )

    elif BENCH_MODE == 8:
        spec_run_single_cover(
            4
        )

    elif BENCH_MODE == 9:
        spec_run_double_cover()

    elif BENCH_MODE == 10:
        spec_run_32x4()

    elif BENCH_MODE == 11:
        spec_run_steam_32x4()

    elif BENCH_MODE == 12:
        spec_run_packed_32(
            0
        )

    elif BENCH_MODE == 13:
        spec_run_packed_32(
            300
        )

    elif BENCH_MODE == 14:
        spec_run_msmith93()

    elif BENCH_MODE == 15:
        spec_run_map_bfs_layout(
            2,
            300,
            "REDDIT BFS5"
        )

    elif BENCH_MODE == 16:
        spec_run_search_layout(
            0,
            2,
            0,
            "PACKED REDDIT FRESH"
        )

    elif BENCH_MODE == 17:
        spec_run_search_layout(
            0,
            3,
            300,
            "PACKED REDDIT VISITED"
        )

    elif BENCH_MODE == 18:
        spec_run_packed_32(
            1
        )

    elif BENCH_MODE == 19:
        spec_run_packed_32(
            2
        )

    elif BENCH_MODE == 20:
        spec_run_packed_32(
            4
        )

    elif BENCH_MODE == 21:
        spec_run_packed_32(
            8
        )

    elif BENCH_MODE == 22:
        spec_run_packed_32(
            16
        )

    elif BENCH_MODE == 23:
        spec_run_search_layout(
            0,
            1,
            0,
            "PACKED UNRANKED FRESH"
        )

    elif BENCH_MODE == 24:
        spec_run_search_layout(
            0,
            1,
            300,
            "PACKED UNRANKED REUSE"
        )

    elif BENCH_MODE == 25:
        spec_run_search_layout(
            1,
            0,
            0,
            "UNIFORM4 FRESH"
        )

    elif BENCH_MODE == 26:
        spec_run_search_layout(
            2,
            0,
            300,
            "UNIFORM5 ZAPAKH REUSE"
        )

    elif BENCH_MODE == 27:
        spec_run_search_layout(
            2,
            0,
            0,
            "UNIFORM5 ZAPAKH FRESH"
        )

    elif BENCH_MODE == 28:
        spec_run_map_bfs_layout(
            0,
            300,
            "PACKED MAP BFS REUSE"
        )

    elif BENCH_MODE == 29:
        spec_run_map_bfs_layout(
            0,
            0,
            "PACKED MAP BFS FRESH"
        )

    elif BENCH_MODE == 30:
        spec_run_map_bfs_layout(
            1,
            300,
            "UNIFORM4 MAP BFS"
        )

    else:
        spec_run_search_layout(
            1,
            0,
            8,
            "UNIFORM4 REUSE8"
        )

    spec_report_result(
        start_gold,
        start_substance,
        start_ticks
    )


# ==================================================
# SHARED BENCH ENTRYPOINT
# ==================================================

def main():
    if BENCH_MODE >= 6:
        run_special()

    elif BENCH_MODE == 5:
        run_reference()

    else:
        run_standard()


main()
