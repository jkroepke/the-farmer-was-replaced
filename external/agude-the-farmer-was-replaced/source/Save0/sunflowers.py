from farm_config import (
    POWER_TARGET,
    SUNFLOWER_HEIGHT,
    SUNFLOWER_START_X,
    SUNFLOWER_START_Y,
    SUNFLOWER_WATER_THRESHOLD,
    SUNFLOWER_WIDTH,
)
from navigation import distance_to, move_to
from parallel_farming import dispatch_indexed_jobs
from planting import ensure_soil
from traversal import get_snake_positions
from traversal import should_scan_forward as choose_scan_direction
from watering import water_if_dry


SUNFLOWER_MIN_PETALS = 7
SUNFLOWER_MAX_PETALS = 15
SUNFLOWER_MIN_REMAINING = 9


def sunflower_end_x() -> int:
    # Return the inclusive right edge of the sunflower patch.
    return SUNFLOWER_START_X + SUNFLOWER_WIDTH - 1


def sunflower_end_y() -> int:
    # Return the inclusive top edge of the sunflower patch.
    return SUNFLOWER_START_Y + SUNFLOWER_HEIGHT - 1


def get_sunflower_positions():
    # Return patch positions in continuous snake order.
    return get_snake_positions(
        SUNFLOWER_START_X,
        SUNFLOWER_START_Y,
        SUNFLOWER_WIDTH,
        SUNFLOWER_HEIGHT,
    )


def should_scan_forward(positions) -> bool:
    # Return whether the first position is nearer than the last.
    return choose_scan_direction(positions, distance_to)


def plant_sunflower() -> bool:
    # Plant and water a sunflower on the current tile.
    ensure_soil()
    if not plant(Entities.Sunflower):
        return False

    water_if_dry(SUNFLOWER_WATER_THRESHOLD)
    return True


def prepare_sunflower_tile() -> bool:
    # Replace a previous crop, or report that it must mature first.
    entity = get_entity_type()

    if entity == Entities.Sunflower:
        water_if_dry(SUNFLOWER_WATER_THRESHOLD)
        return True

    if entity == Entities.Dead_Pumpkin or entity == None:
        return plant_sunflower()

    if not can_harvest():
        water_if_dry(SUNFLOWER_WATER_THRESHOLD)
        return None

    harvest()
    return plant_sunflower()


def plant_and_measure_sunflowers(positions):
    # Plant every sunflower and measure each one exactly once.
    positions_by_petals = [[], [], [], [], [], [], [], [], []]
    pending = positions

    while len(pending) > 0:
        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                preparation = prepare_sunflower_tile()

                if preparation:
                    petals = measure()
                    positions_by_petals[petals - SUNFLOWER_MIN_PETALS].append((x, y))
                elif preparation == None:
                    still_pending.append((x, y))
                else:
                    return None

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                preparation = prepare_sunflower_tile()

                if preparation:
                    petals = measure()
                    positions_by_petals[petals - SUNFLOWER_MIN_PETALS].append((x, y))
                elif preparation == None:
                    still_pending = [(x, y)] + still_pending
                else:
                    return None

        pending = still_pending

    return positions_by_petals


def wait_for_sunflowers(positions) -> None:
    # Revisit positions until every sunflower is mature.
    pending = positions

    while len(pending) > 0:
        still_pending = []

        if should_scan_forward(pending):
            for i in range(len(pending)):
                x, y = pending[i]

                move_to(x, y)

                if not can_harvest():
                    water_if_dry(SUNFLOWER_WATER_THRESHOLD)
                    still_pending.append((x, y))

        else:
            for i in range(len(pending) - 1, -1, -1):
                x, y = pending[i]

                move_to(x, y)

                if not can_harvest():
                    water_if_dry(SUNFLOWER_WATER_THRESHOLD)
                    still_pending = [(x, y)] + still_pending

        pending = still_pending


def harvest_sunflowers(positions_by_petals, harvest_count):
    # Harvest the highest-petal batch while leaving nine flowers behind.
    harvested_positions = []

    for petals in range(SUNFLOWER_MAX_PETALS, SUNFLOWER_MIN_PETALS - 1, -1):
        positions = positions_by_petals[petals - SUNFLOWER_MIN_PETALS]

        for i in range(len(positions)):
            if len(harvested_positions) >= harvest_count:
                return harvested_positions

            x, y = positions[i]

            move_to(x, y)
            harvest()
            harvested_positions.append((x, y))

    return harvested_positions


def replant_sunflowers(positions) -> None:
    # Replant the harvested batch after all harvests finish.
    for i in range(len(positions)):
        x, y = positions[i]

        move_to(x, y)
        plant_sunflower()


def needs_power() -> bool:
    # Return whether the farm should harvest another sunflower cycle.
    return num_items(Items.Power) < POWER_TARGET


def farm_sunflower_patch() -> bool:
    # Replenish power with one complete measured-petal harvest cycle.
    if not needs_power():
        return None

    positions = get_sunflower_positions()
    positions_by_petals = plant_and_measure_sunflowers(positions)

    if positions_by_petals == None:
        return False

    wait_for_sunflowers(positions)
    harvest_count = len(positions) - SUNFLOWER_MIN_REMAINING
    harvested_positions = harvest_sunflowers(positions_by_petals, harvest_count)
    replant_sunflowers(harvested_positions)
    return True


def measure_sunflower_when_ready() -> int:
    # Poll one planted sunflower until it is mature, then measure it.
    while True:
        if can_harvest():
            return measure()

        water_if_dry(SUNFLOWER_WATER_THRESHOLD)


def grow_sunflower_row(row_y: int):
    # Plant, mature, and measure one explicit full-world row.
    size = get_world_size()
    pending = []

    for x in range(size):
        pending.append(x)

    while len(pending) > 0:
        still_pending = []

        for i in range(len(pending)):
            x = pending[i]
            move_to(x, row_y)
            preparation = prepare_sunflower_tile()

            if preparation:
                continue

            if preparation == None:
                still_pending.append(x)
            else:
                return None

        pending = still_pending

    positions_by_petals = [[], [], [], [], [], [], [], [], []]

    for x in range(size):
        move_to(x, row_y)
        petals = measure_sunflower_when_ready()
        positions_by_petals[petals - SUNFLOWER_MIN_PETALS].append((x, row_y))

    return positions_by_petals


def combine_row_measurements(row_measurements):
    # Merge every worker's petal buckets without rescanning the farm.
    positions_by_petals = [[], [], [], [], [], [], [], [], []]

    for row in row_measurements:
        for petals in range(len(positions_by_petals)):
            for position in row[petals]:
                positions_by_petals[petals].append(position)

    return positions_by_petals


def harvest_sunflower_position(position) -> bool:
    # Harvest one selected sunflower position.
    x, y = position
    move_to(x, y)
    harvest()
    return True


def replant_sunflower_position(position) -> bool:
    # Replant one selected sunflower position after harvesting completes.
    x, y = position
    move_to(x, y)
    return plant_sunflower()


def harvest_tier_in_parallel(positions) -> bool:
    # Harvest equal-petal positions together and wait before the next tier.
    results = dispatch_indexed_jobs(positions, harvest_sunflower_position)

    for result in results:
        if not result:
            return False

    return True


def replant_positions_in_parallel(positions) -> bool:
    # Replant only after every selected harvest has completed.
    results = dispatch_indexed_jobs(positions, replant_sunflower_position)

    for result in results:
        if not result:
            return False

    return True


def harvest_full_sunflower_tiers(positions_by_petals, harvest_count):
    # Harvest globally from highest petal count while leaving nine flowers.
    harvested_positions = []

    for petals in range(SUNFLOWER_MAX_PETALS, SUNFLOWER_MIN_PETALS - 1, -1):
        positions = positions_by_petals[petals - SUNFLOWER_MIN_PETALS]
        tier_positions = []

        for position in positions:
            if len(harvested_positions) + len(tier_positions) >= harvest_count:
                break

            tier_positions.append(position)

        if len(tier_positions) > 0:
            if not harvest_tier_in_parallel(tier_positions):
                return None

            for position in tier_positions:
                harvested_positions.append(position)

        if len(harvested_positions) >= harvest_count:
            return harvested_positions

    return harvested_positions


def farm_sunflower_cycle() -> bool:
    # Run one finite full-field power cycle and leave nine flowers mature.
    size = get_world_size()
    if size * size < SUNFLOWER_MIN_REMAINING + 1:
        return False

    rows = []

    for row_y in range(size):
        rows.append(row_y)

    row_measurements = dispatch_indexed_jobs(rows, grow_sunflower_row)

    for row in row_measurements:
        if row == None:
            return False

    positions_by_petals = combine_row_measurements(row_measurements)
    harvest_count = size * size - SUNFLOWER_MIN_REMAINING
    harvested_positions = harvest_full_sunflower_tiers(
        positions_by_petals,
        harvest_count,
    )

    if harvested_positions == None:
        return False

    return replant_positions_in_parallel(harvested_positions)
