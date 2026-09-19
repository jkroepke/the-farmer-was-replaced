import config
import utils
import maze_parallel


# Reference strategy:
# https://pastebin.com/KzGvn6nc
#
# The initial fresh maze is mapped once into an ordered tree. Consecutive
# Gold-focused runs keep reusing that maze. As walls disappear, greedy
# movement discovers shortcuts and selected branches are rotated/reindexed.
#
# Node dictionaries intentionally use coordinate comparisons instead of
# direct node equality because parent/child links form cyclic structures.


_DIRECTIONS = [
    North,
    South,
    East,
    West
]


_ROOT = None
_VISITED = {}
_TOTAL_STEPS = 0
_NODES = {}
_SOLVED = 0
_TARGET = None
_ACTIVE = False
_WORLD_SIZE = 0
_REROOTED = False


# ==================================================
# PUBLIC STATE / COST
# ==================================================

def substance_required():
    maze_level = num_unlocked(
        Unlocks.Mazes
    )

    if maze_level <= 0:
        return 0

    return (
        utils.size()
        * 2**(maze_level - 1)
    )


def parallel_plan():
    return maze_parallel.plan()


def bushes_required():
    if maze_parallel.enabled():
        return maze_parallel.bushes_required()

    return 1


def stockpile_required():
    if maze_parallel.enabled():
        return maze_parallel.stockpile_required()

    return (
        substance_required()
        * config.MAZE_STOCKPILE
    )


def reset():
    global _ROOT
    global _VISITED
    global _TOTAL_STEPS
    global _NODES
    global _SOLVED
    global _TARGET
    global _ACTIVE
    global _WORLD_SIZE
    global _REROOTED

    _ROOT = None
    _VISITED = {}
    _TOTAL_STEPS = 0
    _NODES = {}
    _SOLVED = 0
    _TARGET = None
    _ACTIVE = False
    _WORLD_SIZE = 0
    _REROOTED = False


def is_active():
    return _ACTIVE


def can_start():
    global _ACTIVE

    if (
        _ACTIVE
        and _WORLD_SIZE != utils.size()
    ):
        reset()

    substance = substance_required()

    if substance <= 0:
        return False

    # Never switch algorithms in the middle of an already-active
    # reference Maze. Finish or abandon that Maze first.
    if _ACTIVE:
        # After the final relocation only the final Treasure harvest
        # remains, which does not need more Weird Substance.
        if _SOLVED >= config.MAZE_REUSE_LIMIT:
            return True

        return (
            num_items(Items.Weird_Substance)
            >= substance
        )

    if maze_parallel.enabled():
        return maze_parallel.can_start()

    # Single-Maze fallback also waits for the configured reserve instead
    # of entering Gold production with only one relocation available.
    if (
        num_items(Items.Weird_Substance)
        < stockpile_required()
    ):
        return False

    if not utils.can_afford(
        Entities.Bush
    ):
        return False

    return True


# ==================================================
# DIRECTIONS / NODES
# ==================================================

def _back(direction):
    if direction == North:
        return South

    if direction == South:
        return North

    if direction == East:
        return West

    return East


def _left(direction):
    if direction == North:
        return West

    if direction == West:
        return South

    if direction == South:
        return East

    return North


def _right(direction):
    if direction == North:
        return East

    if direction == East:
        return South

    if direction == South:
        return West

    return North


def _neighbor(coord, direction):
    x, y = coord

    if direction == North:
        return (x, y + 1)

    if direction == South:
        return (x, y - 1)

    if direction == East:
        return (x + 1, y)

    return (x - 1, y)


def _coord():
    return (
        get_pos_x(),
        get_pos_y()
    )


def _node(
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


def _child_names():
    return [
        "left",
        "forward",
        "right",
        "root_extra"
    ]


def _attach(parent, child):
    names = _child_names()

    for name in names:
        if parent[name] == None:
            parent[name] = child
            return True

    return False


def _detach(parent, child):
    names = _child_names()

    found = -1

    for index in range(len(names)):
        candidate = parent[
            names[index]
        ]

        if (
            candidate != None
            and candidate["coord"]
            == child["coord"]
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

    parent[
        names[len(names) - 1]
    ] = None

    return True


# ==================================================
# TREASURE / MAZE CREATION
# ==================================================

def _relocate_here():
    global _SOLVED
    global _TARGET

    if (
        get_entity_type()
        != Entities.Treasure
    ):
        return False

    if (
        _SOLVED
        >= config.MAZE_REUSE_LIMIT
    ):
        return False

    substance = substance_required()

    if (
        num_items(Items.Weird_Substance)
        < substance
    ):
        return False

    use_item(
        Items.Weird_Substance,
        substance
    )

    _SOLVED += 1
    _TARGET = measure()

    return True


def _touch_target():
    if _TARGET == None:
        return False

    if _coord() != _TARGET:
        return False

    return _relocate_here()


def create():
    global _ACTIVE
    global _WORLD_SIZE
    global _TARGET

    if _ACTIVE:
        return True

    if not can_start():
        return False

    substance = substance_required()

    reset()

    clear()

    plant(
        Entities.Bush
    )

    use_item(
        Items.Weird_Substance,
        substance
    )

    _ACTIVE = True
    _WORLD_SIZE = utils.size()
    _TARGET = measure()

    _map()

    # Mapping may have relocated one or more Treasures.
    # measure() gives the current Treasure coordinate from the maze.
    _TARGET = measure()

    return True


# ==================================================
# INITIAL FRESH-MAZE TREE
# ==================================================

def _explore(
    facing,
    parent,
    distance
):
    global _TOTAL_STEPS
    global _VISITED
    global _NODES

    coord = _coord()

    _touch_target()

    if coord in _VISITED:
        return parent["max_val"]

    explored = set()

    _VISITED[coord] = explored

    node = _node(
        _TOTAL_STEPS,
        coord,
        facing,
        distance
    )

    _NODES[coord] = node

    node["parent"] = parent

    _attach(
        parent,
        node
    )

    max_value = _TOTAL_STEPS

    directions = [
        _left(facing),
        facing,
        _right(facing)
    ]

    for direction in directions:
        if (
            can_move(direction)
            and direction not in explored
        ):
            move(
                direction
            )

            _TOTAL_STEPS += 1

            explored.add(
                direction
            )

            child_max = _explore(
                direction,
                node,
                distance + 1
            )

            node["max_val"] = child_max
            max_value = child_max

            if (
                len(_VISITED)
                != get_world_size()
                * get_world_size()
            ):
                move(
                    _back(direction)
                )

                _TOTAL_STEPS += 1

                _touch_target()

    node["max_val"] = max_value

    return max_value


def _map():
    global _ROOT
    global _TARGET
    global _TOTAL_STEPS
    global _VISITED
    global _NODES

    coord = _coord()

    _VISITED[coord] = set()

    _TARGET = measure()

    _ROOT = _node(
        0,
        coord,
        None,
        0
    )

    _NODES[coord] = _ROOT

    explored = _VISITED[coord]

    for direction in _DIRECTIONS:
        if (
            can_move(direction)
            and direction not in explored
        ):
            move(
                direction
            )

            _TOTAL_STEPS += 1

            explored.add(
                direction
            )

            _explore(
                direction,
                _ROOT,
                1
            )

            move(
                _back(direction)
            )

            if (
                len(_VISITED)
                == get_world_size()
                * get_world_size()
            ):
                break

    _reindex_tree(
        _ROOT,
        0,
        0
    )


# ==================================================
# TREE MAINTENANCE
# ==================================================

def _reindex_tree(
    node,
    value,
    level
):
    node["val"] = value
    node["level"] = level

    max_value = value

    names = _child_names()

    for name in names:
        child = node[name]

        if child == None:
            continue

        child["parent"] = node

        max_value = _reindex_tree(
            child,
            max_value + 1,
            level + 1
        )

    node["max_val"] = max_value

    return max_value


def _is_ancestor(
    ancestor,
    node
):
    current = node

    while current != None:
        if (
            current["coord"]
            == ancestor["coord"]
        ):
            return True

        current = current["parent"]

    return False


def _rotate(
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
            old_parent["max_val"] = (
                old_parent["val"]
            )

        _detach(
            old_parent,
            node
        )

    node["parent"] = new_parent
    node["dir"] = direction_from_parent

    _attach(
        new_parent,
        node
    )


def _evaluate_new_path(
    node,
    neighbor,
    direction
):
    if (
        _SOLVED
        >= config.MAZE_REBALANCE_UNTIL
    ):
        return

    if (
        node["level"]
        <= neighbor["level"] + 2
    ):
        return

    if _is_ancestor(
        node,
        neighbor
    ):
        return

    _rotate(
        node,
        neighbor,
        _back(direction)
    )

    _reindex_tree(
        _ROOT,
        0,
        0
    )


def _find_tree_center():
    leaves = []
    max_depth = 0

    for coord in _NODES:
        node = _NODES[coord]

        if (
            node["coord"] != _ROOT["coord"]
            and node["val"]
            == node["max_val"]
        ):
            leaves.append(
                node
            )

            if (
                node["level"]
                > max_depth
            ):
                max_depth = node["level"]

    if len(leaves) == 0:
        return _ROOT

    branches = leaves

    while len(branches) > 1:
        next_branches = []
        seen = set()

        for node in branches:
            current = node

            if (
                current["coord"]
                != _ROOT["coord"]
                and current["level"]
                == max_depth
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

    return _ROOT


def _reroot(new_root):
    global _ROOT

    if (
        new_root["coord"]
        == _ROOT["coord"]
    ):
        return

    path = []

    current = new_root

    while (
        current["coord"]
        != _ROOT["coord"]
    ):
        path.append(
            current
        )

        current = current["parent"]

    index = len(path) - 1

    while index >= 0:
        child = path[index]
        parent = child["parent"]

        _detach(
            parent,
            child
        )

        old_direction = child["dir"]

        parent["parent"] = child
        parent["dir"] = _back(
            old_direction
        )

        _attach(
            child,
            parent
        )

        index -= 1

    new_root["parent"] = None
    new_root["dir"] = None

    _ROOT = new_root

    _reindex_tree(
        _ROOT,
        0,
        0
    )


# ==================================================
# GREEDY SHORTCUT DISCOVERY
# ==================================================

def _try_greedy(
    target,
    route,
    update_tree
):
    current = _coord()

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

        next_coord = _neighbor(
            current,
            direction
        )

        if next_coord in route:
            continue

        explored = _VISITED[current]

        if (
            update_tree
            and direction not in explored
        ):
            explored.add(
                direction
            )

            _evaluate_new_path(
                _NODES[current],
                _NODES[next_coord],
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

def _child_for_target(
    node,
    target_value
):
    names = _child_names()

    for name in names:
        child = node[name]

        if child == None:
            continue

        if (
            target_value >= child["val"]
            and target_value
            <= child["max_val"]
        ):
            return child

    return None


def _path_to(
    target_coord,
    optimize_pathing
):
    current_coord = _coord()
    current = _NODES[
        current_coord
    ]

    target = _NODES[
        target_coord
    ]

    target_value = target["val"]

    greedy_from = set()

    while current_coord != target_coord:
        if (
            current_coord not in greedy_from
            and _SOLVED
            > config.MAZE_GREEDY_AFTER
        ):
            greedy_from.add(
                current_coord
            )

            while _try_greedy(
                target_coord,
                greedy_from,
                optimize_pathing
            ):
                pass

            current_coord = _coord()
            current = _NODES[
                current_coord
            ]
            target = _NODES[
                target_coord
            ]
            target_value = target["val"]

        parent = current["parent"]

        if (
            parent != None
            and (
                target_value < current["val"]
                or target_value
                > current["max_val"]
            )
        ):
            move(
                _back(
                    current["dir"]
                )
            )

            current = parent

        else:
            child = _child_for_target(
                current,
                target_value
            )

            if child == None:
                return False

            move(
                child["dir"]
            )

            current = child

        current_coord = _coord()

    return True


# ==================================================
# REUSED MAZE RUN
# ==================================================

def _finish_maze():
    global _TARGET

    _TARGET = measure()

    if not _path_to(
        _TARGET,
        False
    ):
        return False

    harvest()

    reset()

    return True


def _run_reference():
    global _TARGET
    global _REROOTED

    # First Gold-focused call creates and fully maps the fresh maze.
    # Mapping itself may already relocate/collect Treasure several times.
    if not _ACTIVE:
        return create()

    if not can_start():
        return False

    # After 300 relocations, route to the final Treasure once and harvest
    # it. The next Gold call will create/map a new maze.
    if (
        _SOLVED
        >= config.MAZE_REUSE_LIMIT
    ):
        return _finish_maze()

    _TARGET = measure()

    optimize_pathing = (
        _SOLVED
        > config.MAZE_REBALANCE_FROM
        and _SOLVED
        < config.MAZE_REBALANCE_ACTIVE_UNTIL
    )

    if not _path_to(
        _TARGET,
        optimize_pathing
    ):
        return False

    if (
        not _REROOTED
        and _SOLVED
        >= config.MAZE_REROOT_AT
    ):
        center = _find_tree_center()

        _reroot(
            center
        )

        _REROOTED = True

    return _relocate_here()



# ==================================================
# ADAPTIVE PRODUCTION ENTRY POINT
# ==================================================

def run():
    # Preserve an already-active legacy/reference Maze until its lifecycle
    # ends. New Gold phases use the parallel small-Maze strategy whenever
    # the current world/drone layout can support at least two workers.
    if _ACTIVE:
        return _run_reference()

    if maze_parallel.enabled():
        return maze_parallel.run()

    return _run_reference()
