from farm_config import REGULAR_WATER_THRESHOLD
from navigation import move_to
from parallel_farming import dispatch_indexed_jobs
from planting import plant_target_entity
from watering import water_if_dry


def get_tree_target(x: int, y: int):
    # Keep trees orthogonally separated with bushes on the other color.
    if (x + y) % 2:
        return Entities.Tree

    return Entities.Bush


def tend_tree_row(row_y: int) -> bool:
    # Tend one complete checkerboard row and return after one pass.
    size = get_world_size()
    move_to(0, row_y)

    for x in range(size):
        move_to(x, row_y)
        target = get_tree_target(x, row_y)

        if can_harvest():
            harvest()

        if not plant_target_entity(target):
            return False

        water_if_dry(REGULAR_WATER_THRESHOLD)

    return True


def farm_tree_cycle() -> bool:
    # Run one finite checkerboard pass over every world row.
    size = get_world_size()
    rows = []

    for row_y in range(size):
        rows.append(row_y)

    results = dispatch_indexed_jobs(rows, tend_tree_row)

    for result in results:
        if not result:
            return False

    return True
