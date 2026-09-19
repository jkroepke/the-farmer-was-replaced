from farm_config import FERTILIZE_REGULAR_HARVESTS, REGULAR_WATER_THRESHOLD
from fertilizing import fertilize_before_harvest
from farm_layout import is_regular_target, target_entity_at
from navigation import distance_to, move_to
from planting import plant_target_entity
from watering import water_if_dry


def tend_regular_tile(target) -> bool:
    # Harvest, plant, and water the current regular target tile.
    if can_harvest():
        if FERTILIZE_REGULAR_HARVESTS:
            fertilize_before_harvest()

        harvest()

    if not plant_target_entity(target):
        return False

    water_if_dry(REGULAR_WATER_THRESHOLD)
    return True


def get_regular_positions():
    # Return world positions assigned to regular targets in snake order.
    positions = []
    size = get_world_size()

    for x in range(size):
        if x % 2 == 0:
            for y in range(size):
                target = target_entity_at(x, y)

                if is_regular_target(target):
                    positions.append((x, y, target))

        else:
            for y in range(size - 1, -1, -1):
                target = target_entity_at(x, y)

                if is_regular_target(target):
                    positions.append((x, y, target))

    return positions


def should_scan_forward(positions) -> bool:
    # Return whether the first position is nearer than the last.
    if len(positions) == 0:
        return True

    first_x, first_y, _ = positions[0]
    last_x, last_y, _ = positions[len(positions) - 1]

    return distance_to(first_x, first_y) <= distance_to(last_x, last_y)


def farm_regular_tiles() -> None:
    # Visit and tend every regular tile in the shorter scan direction.
    positions = get_regular_positions()

    if len(positions) == 0:
        return

    if should_scan_forward(positions):
        for i in range(len(positions)):
            x, y, target = positions[i]

            move_to(x, y)
            tend_regular_tile(target)

    else:
        for i in range(len(positions) - 1, -1, -1):
            x, y, target = positions[i]

            move_to(x, y)
            tend_regular_tile(target)
