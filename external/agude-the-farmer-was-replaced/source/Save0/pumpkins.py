from farm_config import (
    FERTILIZE_PUMPKIN_HARVEST,
    PUMPKIN_SIZE,
    PUMPKIN_START_X,
    PUMPKIN_START_Y,
    PUMPKIN_WATER_THRESHOLD,
)
from fertilizing import fertilize_before_harvest
from navigation import distance_to, move_to
from parallel_farming import dispatch_indexed_jobs
from planting import ensure_soil
from traversal import get_snake_positions
from traversal import should_scan_forward as choose_scan_direction
from watering import water_if_dry


def pumpkin_end_x() -> int:
    # Return the inclusive right edge of the pumpkin patch.
    return PUMPKIN_START_X + PUMPKIN_SIZE - 1


def pumpkin_end_y() -> int:
    # Return the inclusive bottom edge of the pumpkin patch.
    return PUMPKIN_START_Y + PUMPKIN_SIZE - 1


def plant_pumpkin() -> bool:
    # Ensure soil and plant a pumpkin on the current tile.
    ensure_soil()
    return plant(Entities.Pumpkin)


def pumpkin_is_ready() -> bool:
    # Maintain the current pumpkin tile and report when it is mature.
    entity = get_entity_type()

    #
    # Living pumpkin.
    #
    if entity == Entities.Pumpkin:
        if can_harvest():
            return True

        water_if_dry(PUMPKIN_WATER_THRESHOLD)
        return False

    #
    # Dead pumpkin.
    #
    if entity == Entities.Dead_Pumpkin:
        if not plant_pumpkin():
            return None

        water_if_dry(PUMPKIN_WATER_THRESHOLD)
        return False

    #
    # Empty tile.
    #
    if entity == None:
        if not plant_pumpkin():
            return None

        water_if_dry(PUMPKIN_WATER_THRESHOLD)
        return False

    #
    # Some other crop is occupying a tile that now
    # belongs to the pumpkin patch.
    #
    if can_harvest():
        harvest()
        if not plant_pumpkin():
            return None

    water_if_dry(PUMPKIN_WATER_THRESHOLD)

    return False


def get_pumpkin_positions():
    # Return all pumpkin-patch positions in continuous snake order.
    return get_snake_positions(PUMPKIN_START_X, PUMPKIN_START_Y, PUMPKIN_SIZE, PUMPKIN_SIZE)


def should_scan_forward(positions) -> bool:
    # Return whether the first pending tile is nearer than the last.
    return choose_scan_direction(positions, distance_to)


def wait_for_positions(positions) -> bool:
    # Revisit pending tiles until each has produced a mature pumpkin.
    #
    # A position remains pending until we have
    # personally observed a mature living pumpkin
    # there.
    #
    pending = positions

    while len(pending) > 0:
        #
        # Endgame optimization:
        #
        # Only one pumpkin remains unresolved.
        # Go there ONCE and don't move again until
        # that pumpkin succeeds.
        #
        if len(pending) == 1:
            x, y = pending[0]

            move_to(x, y)

            while True:
                readiness = pumpkin_is_ready()

                if readiness == None:
                    return False

                if readiness:
                    return True

            return None

        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                readiness = pumpkin_is_ready()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                readiness = pumpkin_is_ready()

                if readiness == None:
                    return False

                if not readiness:
                    #
                    # Preserve normal snake order.
                    #
                    still_pending = [(x, y)] + still_pending

        pending = still_pending

    return True


def farm_pumpkin_patch() -> None:
    # Grow the full patch, then harvest the final mature pumpkin.
    positions = get_pumpkin_positions()

    #
    # Every position begins unresolved.
    #
    # Once a mature pumpkin is seen there, that
    # position drops out permanently.
    #
    if not wait_for_positions(positions):
        return False

    #
    # When this returns, EVERY pumpkin has been
    # observed mature.
    #
    # We're standing on the final one, so harvest
    # immediately. No redundant verification pass.
    #
    if FERTILIZE_PUMPKIN_HARVEST:
        fertilize_before_harvest()

    harvest()

    return True


def grow_pumpkin_row_until_ready(row_y: int) -> bool:
    # Grow one full-world row and return after every tile is mature.
    size = get_world_size()
    pending = []

    for x in range(size):
        pending.append(x)

    while len(pending) > 0:
        if len(pending) == 1:
            move_to(pending[0], row_y)

            while True:
                readiness = pumpkin_is_ready()

                if readiness == None:
                    return False

                if readiness:
                    return True

        still_pending = []

        if distance_to(pending[0], row_y) <= distance_to(pending[-1], row_y):
            for i in range(len(pending)):
                x = pending[i]
                move_to(x, row_y)

                readiness = pumpkin_is_ready()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending.append(x)
        else:
            for i in range(len(pending) - 1, -1, -1):
                x = pending[i]
                move_to(x, row_y)

                readiness = pumpkin_is_ready()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending = [x] + still_pending

        pending = still_pending

    return True


def farm_pumpkin_cycle() -> bool:
    # Grow the full world before one bulk harvest.
    size = get_world_size()
    rows = []

    for row_y in range(size):
        rows.append(row_y)

    results = dispatch_indexed_jobs(rows, grow_pumpkin_row_until_ready)

    for result in results:
        if not result:
            return False

    move_to(size - 1, size - 1)

    if not can_harvest():
        return False

    if FERTILIZE_PUMPKIN_HARVEST:
        fertilize_before_harvest()

    harvest()
    return True
