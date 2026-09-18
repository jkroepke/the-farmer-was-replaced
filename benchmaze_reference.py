# Behavioral port of the community "maze single - tree rebalancing"
# benchmark strategy:
#
# https://pastebin.com/KzGvn6nc
#
# This is intentionally kept separate from benchmaze.py so the
# reference strategy is not mixed with our own simplified variants.
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
        get_world_size()
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

        if parent[name] == child:
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

    turns = [
        ref_left,
        None,
        ref_right
    ]

    for turn in turns:
        if turn == None:
            direction = facing
        else:
            direction = turn(
                facing
            )

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
                != get_world_size()
                * get_world_size()
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
                == get_world_size()
                * get_world_size()
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
        if current == ancestor:
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
            node != REF_ROOT
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
                current != REF_ROOT
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

    if new_root == REF_ROOT:
        return

    path = []

    current = new_root

    while current != REF_ROOT:
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

def main():
    global REF_ROOT
    global REF_VISITED
    global REF_TOTAL_STEPS
    global REF_NODES
    global REF_SOLVED
    global REF_TARGET

    set_world_size(
        BENCH_WORLD_SIZE
    )

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


main()
