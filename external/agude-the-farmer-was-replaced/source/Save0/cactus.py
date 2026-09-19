from farm_config import (
    CACTUS_SIZE,
    CACTUS_REVERSE_SORT,
    CACTUS_START_X,
    CACTUS_START_Y,
    CACTUS_WATER_THRESHOLD,
    FERTILIZE_CACTUS_HARVEST,
)
from fertilizing import fertilize_before_harvest
from navigation import distance_to, move_to
from parallel_farming import dispatch_indexed_jobs
from planting import ensure_soil
from traversal import get_snake_positions
from traversal import should_scan_forward as choose_scan_direction
from watering import water_if_dry


def cactus_end_x() -> int:
    # Return the inclusive right edge of the cactus patch.
    return CACTUS_START_X + CACTUS_SIZE - 1


def cactus_end_y() -> int:
    # Return the inclusive top edge of the cactus patch.
    return CACTUS_START_Y + CACTUS_SIZE - 1


def plant_cactus() -> bool:
    # Ensure soil and plant a cactus on the current tile.
    ensure_soil()
    return plant(Entities.Cactus)


def maintain_cactus_tile() -> bool:
    # Prepare the current tile and report whether its cactus is mature.
    entity = get_entity_type()

    if entity == Entities.Cactus:
        if can_harvest():
            return True

        water_if_dry(CACTUS_WATER_THRESHOLD)
        return False

    if entity == Entities.Dead_Pumpkin or entity == None:
        if not plant_cactus():
            return None

        water_if_dry(CACTUS_WATER_THRESHOLD)
        return False

    # Wait for an existing crop to mature before converting this tile.
    if not can_harvest():
        water_if_dry(CACTUS_WATER_THRESHOLD)
        return False

    harvest()
    if not plant_cactus():
        return None

    water_if_dry(CACTUS_WATER_THRESHOLD)

    return False


def get_cactus_positions():
    # Return all cactus-patch positions in continuous snake order.
    return get_snake_positions(CACTUS_START_X, CACTUS_START_Y, CACTUS_SIZE, CACTUS_SIZE)


def should_scan_forward(positions) -> bool:
    # Return whether the first position is nearer than the last.
    return choose_scan_direction(positions, distance_to)


def wait_for_cactuses(positions) -> bool:
    # Revisit positions until every cactus is fully grown.
    pending = positions

    while len(pending) > 0:
        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                readiness = maintain_cactus_tile()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                readiness = maintain_cactus_tile()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending = [(x, y)] + still_pending

        pending = still_pending

    return True


def sort_cactus_row(y: int, start_x=CACTUS_START_X, end_x=None, reverse=False) -> None:
    # Sort one row west to east with an early-terminating cocktail sort.
    if end_x == None:
        end_x = cactus_end_x()

    left_x = start_x
    right_x = end_x

    while left_x < right_x:
        swapped = False

        for x in range(left_x, right_x):
            move_to(x, y)

            if (not reverse and measure() > measure(East)) or (
                reverse and measure() < measure(East)
            ):
                swap(East)
                swapped = True

        right_x -= 1

        if not swapped:
            return

        swapped = False

        for x in range(right_x, left_x, -1):
            move_to(x, y)

            if (not reverse and measure() < measure(West)) or (
                reverse and measure() > measure(West)
            ):
                swap(West)
                swapped = True

        left_x += 1

        if not swapped:
            return


def sort_cactus_rows(
    start_x=CACTUS_START_X,
    start_y=CACTUS_START_Y,
    width=CACTUS_SIZE,
    height=CACTUS_SIZE,
    reverse=False,
) -> None:
    # Sort every row west to east with adjacent swaps.
    end_x = start_x + width - 1

    for y in range(start_y, start_y + height):
        sort_cactus_row(y, start_x, end_x, reverse)


def sort_cactus_column(x: int, start_y=CACTUS_START_Y, end_y=None, reverse=False) -> None:
    # Sort one column south to north with an early-terminating cocktail sort.
    if end_y == None:
        end_y = cactus_end_y()

    bottom_y = start_y
    top_y = end_y

    while bottom_y < top_y:
        swapped = False

        for y in range(bottom_y, top_y):
            move_to(x, y)

            if (not reverse and measure() > measure(North)) or (
                reverse and measure() < measure(North)
            ):
                swap(North)
                swapped = True

        top_y -= 1

        if not swapped:
            return

        swapped = False

        for y in range(top_y, bottom_y, -1):
            move_to(x, y)

            if (not reverse and measure() < measure(South)) or (
                reverse and measure() > measure(South)
            ):
                swap(South)
                swapped = True

        bottom_y += 1

        if not swapped:
            return


def sort_cactus_columns(
    start_x=CACTUS_START_X,
    start_y=CACTUS_START_Y,
    width=CACTUS_SIZE,
    height=CACTUS_SIZE,
    reverse=False,
) -> None:
    # Sort every column south to north with adjacent swaps.
    end_y = start_y + height - 1

    for x in range(start_x, start_x + width):
        sort_cactus_column(x, start_y, end_y, reverse)


def sort_cactuses() -> None:
    # Arrange the patch in the order required for bulk harvesting.
    sort_cactus_rows()
    sort_cactus_columns()


def grow_cactus_row_job(job) -> bool:
    # Grow one explicit row in an arbitrary cactus region.
    row_y, start_x, start_y, width, height, _ = job
    pending = []

    for x in range(start_x, start_x + width):
        pending.append(x)

    while len(pending) > 0:
        if len(pending) == 1:
            move_to(pending[0], row_y)

            while True:
                readiness = maintain_cactus_tile()

                if readiness == None:
                    return False

                if readiness:
                    return True

        still_pending = []

        if distance_to(pending[0], row_y) <= distance_to(pending[-1], row_y):
            for i in range(len(pending)):
                x = pending[i]
                move_to(x, row_y)
                readiness = maintain_cactus_tile()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending.append(x)
        else:
            for i in range(len(pending) - 1, -1, -1):
                x = pending[i]
                move_to(x, row_y)
                readiness = maintain_cactus_tile()

                if readiness == None:
                    return False

                if not readiness:
                    still_pending = [x] + still_pending

        pending = still_pending

    return True


def sort_cactus_row_job(job) -> bool:
    # Sort one explicit row in an arbitrary cactus region.
    row_y, start_x, start_y, width, height, reverse = job
    sort_cactus_row(row_y, start_x, start_x + width - 1, reverse)
    return True


def sort_cactus_column_job(job) -> bool:
    # Sort one explicit column in an arbitrary cactus region.
    column_x, start_x, start_y, width, height, reverse = job
    sort_cactus_column(column_x, start_y, start_y + height - 1, reverse)
    return True


def harvest_cactus(
    weird_substance_target=None,
    fertilizer_reserve=None,
    production_enabled=None,
) -> bool:
    # Fertilize and harvest the mature cactus at the current tile.
    if not can_harvest():
        return False

    if FERTILIZE_CACTUS_HARVEST:
        fertilize_before_harvest(
            weird_substance_target,
            fertilizer_reserve,
            production_enabled,
        )

    harvest()
    return True


def farm_cactus_cycle(
    start_x=CACTUS_START_X,
    start_y=CACTUS_START_Y,
    width=CACTUS_SIZE,
    height=CACTUS_SIZE,
    reverse=False,
    weird_substance_target=None,
    fertilizer_reserve=None,
    production_enabled=None,
) -> bool:
    # Grow, sort, and bulk-harvest one explicit cactus region.
    if width <= 0 or height <= 0:
        return False

    row_jobs = []
    column_jobs = []

    for row_y in range(start_y, start_y + height):
        row_jobs.append((row_y, start_x, start_y, width, height, reverse))

    for column_x in range(start_x, start_x + width):
        column_jobs.append((column_x, start_x, start_y, width, height, reverse))

    growth_results = dispatch_indexed_jobs(row_jobs, grow_cactus_row_job)

    for result in growth_results:
        if not result:
            return False

    row_results = dispatch_indexed_jobs(row_jobs, sort_cactus_row_job)

    for result in row_results:
        if not result:
            return False

    column_results = dispatch_indexed_jobs(column_jobs, sort_cactus_column_job)

    for result in column_results:
        if not result:
            return False

    move_to(start_x, start_y)
    return harvest_cactus(
        weird_substance_target,
        fertilizer_reserve,
        production_enabled,
    )


def farm_cactus_patch() -> bool:
    # Grow, sort, and bulk-harvest the cactus patch.
    return farm_cactus_cycle(
        CACTUS_START_X,
        CACTUS_START_Y,
        CACTUS_SIZE,
        CACTUS_SIZE,
        CACTUS_REVERSE_SORT,
    )
