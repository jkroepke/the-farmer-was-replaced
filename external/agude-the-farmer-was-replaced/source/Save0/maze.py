from farm_config import GOLD_TARGET as DEFAULT_GOLD_TARGET
from farm_config import WEIRD_SUBSTANCE_RESERVE as DEFAULT_WEIRD_SUBSTANCE_RESERVE


def get_maze_substance_cost() -> int:
    # Return the full-field cost, or zero when mazes are unavailable.
    maze_level = num_unlocked(Unlocks.Mazes)

    if maze_level == 0:
        return 0

    world_size = get_world_size()
    return world_size * 2 ** (maze_level - 1)


def can_fund_maze(substance_cost: int, substance_reserve: int) -> bool:
    # Keep the caller's Weird Substance reserve untouched.
    return num_items(Items.Weird_Substance) >= (substance_cost + substance_reserve)


def create_maze(substance_cost: int) -> bool:
    # Turn the current tile into a fresh full-field maze.
    if get_ground_type() != Grounds.Soil:
        till()

    if not plant(Entities.Bush):
        return False

    return use_item(Items.Weird_Substance, substance_cost)


def solve_maze() -> bool:
    # Follow the right wall through a fresh maze without crossing hedges.
    directions = [North, East, South, West]
    facing = 0

    while get_entity_type() != Entities.Treasure:
        right = (facing + 1) % 4

        if move(directions[right]):
            facing = right
            continue

        if move(directions[facing]):
            continue

        left = (facing - 1) % 4

        if move(directions[left]):
            facing = left
            continue

        reverse = (facing + 2) % 4

        if not move(directions[reverse]):
            return False

        facing = reverse

    if get_entity_type() != Entities.Treasure:
        return False

    harvest()
    return True


def farm_mazes(gold_target=None, substance_reserve=None) -> bool:
    # Create fresh mazes until the caller's target or reserve is reached.
    if gold_target == None:
        gold_target = DEFAULT_GOLD_TARGET

    if substance_reserve == None:
        substance_reserve = DEFAULT_WEIRD_SUBSTANCE_RESERVE

    if num_items(Items.Gold) >= gold_target:
        return True

    substance_cost = get_maze_substance_cost()

    if substance_cost == 0:
        return False

    if not can_fund_maze(substance_cost, substance_reserve):
        return False

    clear()
    completed_maze = False

    while num_items(Items.Gold) < gold_target:
        substance_cost = get_maze_substance_cost()

        if substance_cost == 0:
            return completed_maze

        if not can_fund_maze(substance_cost, substance_reserve):
            return completed_maze

        if not create_maze(substance_cost):
            return False

        if not solve_maze():
            return False

        completed_maze = True

    return True
