import config
import farm
import utils
import workers


# Normal-farm benchmark implementations.
#
# Modes intentionally include:
#
# - the current production implementation unchanged
# - small, isolated layout changes
# - deliberately simple controls
# - source-near external references
#
# Do not "improve" a reference mode in place. Add another mode instead.
#
# External source snapshots:
#
# - external/juritox-the-farmer-was-replaced/source/scripts/
#   hay_harvest.py
#   wood_harvest.py
#   carrot_harvest.py
#   power_harvest.py
# - external/mateusmarochi-the-farmer-was-replaced-codes/source/
#   sunflower_farm.py
#
# Community findings motivating separate candidate modes:
#
# - https://www.reddit.com/r/TheFarmerWasReplaced/comments/1pxb31j/
# - https://www.reddit.com/r/TheFarmerWasReplaced/comments/1qfv72c/
# - https://www.reddit.com/r/TheFarmerWasReplaced/comments/1vsh1qj/
#
# BENCH_FOCUS:
#   0 = Hay
#   1 = Wood
#   2 = Carrot
#   3 = Power


MODE_NAMES = [
    "current-l-production",
    "current-l-no-polyculture",
    "columns-pure-current-crop",
    "columns-one-sunflower-row-dumb",
    "columns-one-sunflower-column-dumb",
    "columns-two-sunflower-columns-dumb",
    "columns-one-sunflower-column-max-petal",
    "columns-one-sunflower-column-simple-crop",
    "juritox-reference-single-drone",
    "unused-9",
    "unused-10",
    "unused-11",
    "unused-12",
    "unused-13",
    "unused-14",
    "unused-15",
    "unused-16",
    "unused-17",
    "unused-18",
    "unused-19",
    "current-l-power",
    "mateus-reference-fullfield-dumb",
    "fullfield-dumb-north-only",
    "juritox-reference-max-petal"
]


def focus_item():
    if BENCH_FOCUS == 0:
        return Items.Hay

    if BENCH_FOCUS == 1:
        return Items.Wood

    if BENCH_FOCUS == 2:
        return Items.Carrot

    return Items.Power


def ensure_sunflower():
    entity = get_entity_type()

    if entity == Entities.Sunflower:
        return True

    if entity != None:
        if not can_harvest():
            return False

        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    if not utils.can_afford(
        Entities.Sunflower
    ):
        return False

    if not plant(
        Entities.Sunflower
    ):
        return False

    # Current community observations suggest watering once when planted
    # is enough; continuously topping water up wastes actions.
    utils.water()

    return True


def service_sunflower_dumb():
    if get_entity_type() == Entities.Sunflower:
        if not can_harvest():
            return

        harvest()

    if ensure_sunflower():
        return


def service_focus_simple(item):
    x = get_pos_x()
    y = get_pos_y()

    if item == Items.Hay:
        entity = get_entity_type()

        if (
            entity != None
            and entity != Entities.Grass
        ):
            if not can_harvest():
                return

            harvest()

        if get_ground_type() != Grounds.Grassland:
            till()

        if can_harvest():
            harvest()

        return

    if item == Items.Carrot:
        entity = get_entity_type()

        if (
            entity != None
            and entity != Entities.Carrot
        ):
            if not can_harvest():
                return

            harvest()

        if get_ground_type() != Grounds.Soil:
            till()

        if get_entity_type() == Entities.Carrot:
            if can_harvest():
                harvest()

        if get_entity_type() == None:
            if utils.can_afford(
                Entities.Carrot
            ):
                if plant(
                    Entities.Carrot
                ):
                    utils.water()

        return

    # Simple Wood control:
    # Tree/Bush checkerboard from the juritox reference.
    if (x + y) % 2 == 0:
        wanted = Entities.Tree
    else:
        wanted = Entities.Bush

    entity = get_entity_type()

    if entity == wanted:
        if can_harvest():
            harvest()

    elif entity != None:
        if not can_harvest():
            return

        harvest()

    if get_entity_type() == None:
        if utils.can_afford(wanted):
            if plant(wanted):
                utils.water()


def is_sunflower_tile(layout, x, y, world_size):
    if layout == 1:
        return y == world_size - 1

    if layout == 2:
        return x == world_size - 1

    if layout == 3:
        return x >= world_size - 2

    return False


def _make_column_region_task(
    start_x,
    end_x,
    item,
    target,
    layout,
    simple_crop
):
    def task():
        world_size = utils.size()
        x = start_x
        horizontal = 1

        utils.move_to(
            x,
            0
        )

        while num_items(item) < target:
            # Exactly world_size North moves return the worker to y=0
            # through normal farm wrapping.
            for _ in range(world_size):
                y = get_pos_y()

                if is_sunflower_tile(
                    layout,
                    x,
                    y,
                    world_size
                ):
                    service_sunflower_dumb()

                elif simple_crop:
                    service_focus_simple(
                        item
                    )

                else:
                    # Restrict companion changes to this same column.
                    # Cross-column worker coordination would require a
                    # separate algorithm because drones do not share memory.
                    farm.farm_resource(
                        x,
                        x + 1,
                        item
                    )

                move(North)

            if end_x - start_x <= 1:
                continue

            if horizontal > 0:
                if x < end_x - 1:
                    move(East)
                    x += 1
                else:
                    horizontal = -1
                    move(West)
                    x -= 1

            else:
                if x > start_x:
                    move(West)
                    x -= 1
                else:
                    horizontal = 1
                    move(East)
                    x += 1

        return True

    return task


def run_column_layout(
    item,
    target,
    layout,
    simple_crop
):
    clear()

    world_size = utils.size()
    worker_count = min(
        max_drones(),
        world_size
    )

    chunks = workers.make_chunks(
        world_size,
        worker_count
    )

    tasks = []

    for start_x, end_x in chunks:
        tasks.append(
            _make_column_region_task(
                start_x,
                end_x,
                item,
                target,
                layout,
                simple_crop
            )
        )

    workers.run(tasks)


def _make_max_petal_worker(
    column,
    item,
    target
):
    def task():
        world_size = utils.size()
        petals = []

        utils.move_to(
            column,
            0
        )

        # This dedicated column is the only place where this benchmark
        # mode plants Sunflowers. One worker therefore owns the complete
        # max-petal ordering problem and needs no cross-drone memory.
        for _ in range(world_size):
            if not ensure_sunflower():
                return False

            petals.append(
                measure()
            )

            move(North)

        while num_items(item) < target:
            max_petals = max(
                petals
            )

            harvested = False

            for row in range(world_size):
                if petals[row] != max_petals:
                    continue

                utils.move_to(
                    column,
                    row
                )

                if get_entity_type() != Entities.Sunflower:
                    if not ensure_sunflower():
                        return False

                    petals[row] = measure()
                    harvested = True
                    break

                if can_harvest():
                    harvest()

                    if not ensure_sunflower():
                        return False

                    petals[row] = measure()
                    harvested = True
                    break

            # If the current maximum is not mature yet, cheap observation
            # loops are preferable to harvesting a lower-petal flower and
            # intentionally losing the 8x ordering bonus.
            if not harvested:
                pass

        return True

    return task


def run_column_max_petal(
    item,
    target
):
    clear()

    world_size = utils.size()

    if max_drones() < 2:
        run_column_layout(
            item,
            target,
            2,
            False
        )
        return

    crop_columns = world_size - 1
    crop_workers = min(
        max_drones() - 1,
        crop_columns
    )

    chunks = workers.make_chunks(
        crop_columns,
        crop_workers
    )

    tasks = []

    for start_x, end_x in chunks:
        tasks.append(
            _make_column_region_task(
                start_x,
                end_x,
                item,
                target,
                0,
                False
            )
        )

    # Keep this last: workers.run() then gives the caller/main drone
    # this final task after spawning the crop workers.
    tasks.append(
        _make_max_petal_worker(
            world_size - 1,
            item,
            target
        )
    )

    workers.run(tasks)


def run_current(
    item,
    target,
    disable_polyculture
):
    clear()

    if disable_polyculture:
        config.ENABLE_POLYCULTURE = False

    workers.set_main_hat()

    farm.rebuild_sunflowers()

    while num_items(item) < target:
        farm.run(item)


# ==================================================
# JURITOX CROP REFERENCE
# ==================================================
#
# Source-near behavioral port of:
#
# external/juritox-the-farmer-was-replaced/source/scripts/
#   hay_harvest.py
#   wood_harvest.py
#   carrot_harvest.py
#
# Deliberately single-drone and full-field. The only material adaptation
# is stopping on an inventory target instead of decrementing a requested
# amount variable.
# ==================================================

def run_juritox_crop_reference(
    item,
    target
):
    clear()

    world_size = utils.size()

    while num_items(item) < target:
        for _ in range(world_size):
            for _ in range(world_size):
                if item == Items.Hay:
                    if can_harvest():
                        harvest()

                elif item == Items.Wood:
                    if can_harvest():
                        harvest()

                    if get_ground_type() != Grounds.Grassland:
                        till()

                    if (
                        get_pos_x() % 2 == 0
                        and get_pos_y() % 2 == 0
                    ):
                        plant(
                            Entities.Tree
                        )

                    elif (
                        get_pos_x() % 2 != 0
                        and get_pos_y() % 2 != 0
                    ):
                        plant(
                            Entities.Tree
                        )

                    else:
                        plant(
                            Entities.Bush
                        )

                    if get_entity_type() == Entities.Tree:
                        if (
                            get_water()
                            < config.WATER_LIMIT
                            and num_items(Items.Water) > 0
                        ):
                            use_item(
                                Items.Water
                            )

                else:
                    if can_harvest():
                        harvest()

                    if get_ground_type() != Grounds.Soil:
                        till()

                    plant(
                        Entities.Carrot
                    )

                    if (
                        get_water()
                        < config.WATER_LIMIT
                        and num_items(Items.Water) > 0
                    ):
                        use_item(
                            Items.Water
                        )

                move(North)

            move(East)


# ==================================================
# MATEUS SUNFLOWER REFERENCE
# ==================================================
#
# Source-near behavioral port of:
#
# external/mateusmarochi-the-farmer-was-replaced-codes/source/
# sunflower_farm.py
#
# Keep its explicit return to row 0. The North-only candidate is a
# separate mode so we can measure whether our apparent optimization
# actually helps.
# ==================================================

def mateus_move_to_column(target_column):
    while get_pos_x() < target_column:
        move(East)

    while get_pos_x() > target_column:
        move(West)


def mateus_move_to_row(target_row):
    while get_pos_y() < target_row:
        move(North)

    while get_pos_y() > target_row:
        move(South)


def mateus_plant_sunflower():
    if get_ground_type() != Grounds.Soil:
        till()

    plant(
        Entities.Sunflower
    )

    if (
        get_water() < 0.5
        and num_items(Items.Water) > 0
    ):
        use_item(
            Items.Water
        )


def mateus_maintain_sunflower_tile():
    if get_entity_type() != Entities.Sunflower:
        if can_harvest():
            harvest()

        mateus_plant_sunflower()

    else:
        if can_harvest():
            harvest()
            mateus_plant_sunflower()


def _make_mateus_worker(
    column,
    target
):
    def task():
        world_size = utils.size()

        mateus_move_to_column(
            column
        )
        mateus_move_to_row(
            0
        )

        while num_items(Items.Power) < target:
            row = 0

            while row < world_size:
                mateus_maintain_sunflower_tile()

                if row < world_size - 1:
                    move(North)

                row += 1

            mateus_move_to_row(
                0
            )

        return True

    return task


def run_mateus_reference_power(
    target
):
    clear()

    world_size = utils.size()
    assigned_columns = min(
        world_size,
        max_drones()
    )

    handles = []
    column = 1

    while column < assigned_columns:
        worker = _make_mateus_worker(
            column,
            target
        )

        drone = spawn_drone(
            worker
        )

        if drone == None:
            break

        handles.append(
            drone
        )

        column += 1

    _make_mateus_worker(
        0,
        target
    )()

    for drone in handles:
        wait_for(
            drone
        )


def _make_north_only_sunflower_task(
    start_x,
    end_x,
    target
):
    def task():
        world_size = utils.size()
        x = start_x
        horizontal = 1

        utils.move_to(
            x,
            0
        )

        while num_items(Items.Power) < target:
            for _ in range(world_size):
                service_sunflower_dumb()
                move(North)

            if end_x - start_x <= 1:
                continue

            if horizontal > 0:
                if x < end_x - 1:
                    move(East)
                    x += 1
                else:
                    horizontal = -1
                    move(West)
                    x -= 1
            else:
                if x > start_x:
                    move(West)
                    x -= 1
                else:
                    horizontal = 1
                    move(East)
                    x += 1

        return True

    return task


def run_north_only_power(
    target
):
    clear()

    world_size = utils.size()
    worker_count = min(
        max_drones(),
        world_size
    )

    chunks = workers.make_chunks(
        world_size,
        worker_count
    )

    tasks = []

    for start_x, end_x in chunks:
        tasks.append(
            _make_north_only_sunflower_task(
                start_x,
                end_x,
                target
            )
        )

    workers.run(tasks)


# ==================================================
# JURITOX POWER REFERENCE
# ==================================================
#
# Source-near port of:
#
# external/juritox-the-farmer-was-replaced/source/scripts/power_harvest.py
#
# Preserve the repeated full-field scans, the double measure() for the
# 15-petal fast path, and list/remove/max behavior. It is intentionally
# not rewritten into our cached-max implementation.
# ==================================================

def juritox_measure_petals():
    petals = []
    world_size = utils.size()

    for _ in range(world_size):
        for _ in range(world_size):
            petals.append(
                measure()
            )

            if measure() == 15:
                if can_harvest():
                    harvest()
                    petals.remove(
                        15
                    )

            move(North)

        move(East)

    return petals


def run_juritox_power_reference(
    target
):
    clear()

    world_size = utils.size()

    while num_items(Items.Power) < target:
        for _ in range(world_size):
            for _ in range(world_size):
                if can_harvest():
                    harvest()

                if get_ground_type() != Grounds.Soil:
                    till()

                plant(
                    Entities.Sunflower
                )

                if (
                    get_water()
                    < config.WATER_LIMIT
                    and num_items(Items.Water) > 0
                ):
                    use_item(
                        Items.Water
                    )

                move(North)

            move(East)

        petals = (
            juritox_measure_petals()
        )

        while (
            len(petals) > 0
            and num_items(Items.Power) < target
        ):
            max_petals = max(
                petals
            )

            max_available = True

            for _ in range(world_size):
                if not max_available:
                    break

                for _ in range(world_size):
                    if measure() == max_petals:
                        if can_harvest():
                            harvest()

                            petals.remove(
                                max_petals
                            )

                            if max_petals not in petals:
                                max_available = False
                                break

                    move(North)

                move(East)


def probe_clean_layout():
    # Diagnostic only. set_world_size() and clear() are both documented
    # to clear the farm. Probe two coordinates that are occupied by the
    # production L so we can distinguish simulated state from UI state.
    clear()

    first = get_entity_type()

    move(East)
    second = get_entity_type()

    quick_print(
        "FARM CLEAN PROBE",
        "x0y0",
        first,
        "x1y0",
        second
    )

    # Leave the simulation in the same neutral state after probing.
    clear()


def run_mode(
    mode,
    item,
    target
):
    if mode == 0:
        run_current(
            item,
            target,
            False
        )
        return

    if mode == 1:
        run_current(
            item,
            target,
            True
        )
        return

    if mode == 2:
        run_column_layout(
            item,
            target,
            0,
            False
        )
        return

    if mode == 3:
        run_column_layout(
            item,
            target,
            1,
            False
        )
        return

    if mode == 4:
        run_column_layout(
            item,
            target,
            2,
            False
        )
        return

    if mode == 5:
        run_column_layout(
            item,
            target,
            3,
            False
        )
        return

    if mode == 6:
        run_column_max_petal(
            item,
            target
        )
        return

    if mode == 7:
        run_column_layout(
            item,
            target,
            2,
            True
        )
        return

    if mode == 8:
        run_juritox_crop_reference(
            item,
            target
        )
        return

    if mode == 20:
        run_current(
            Items.Power,
            target,
            False
        )
        return

    if mode == 21:
        run_mateus_reference_power(
            target
        )
        return

    if mode == 22:
        run_north_only_power(
            target
        )
        return

    if mode == 23:
        run_juritox_power_reference(
            target
        )
        return

    if mode == 99:
        probe_clean_layout()


def main():
    set_world_size(
        BENCH_WORLD_SIZE
    )

    item = focus_item()

    start_items = num_items(
        item
    )
    start_power = num_items(
        Items.Power
    )

    target = (
        start_items
        + BENCH_TARGET_GAIN
    )

    if BENCH_MODE == 99:
        probe_clean_layout()
        return

    quick_print(
        "FARM MODE START",
        MODE_NAMES[BENCH_MODE],
        "focus",
        BENCH_FOCUS,
        "world",
        BENCH_WORLD_SIZE,
        "drones",
        max_drones()
    )

    start_time = get_time()

    run_mode(
        BENCH_MODE,
        item,
        target
    )

    elapsed = (
        get_time()
        - start_time
    )

    gained = (
        num_items(item)
        - start_items
    )

    power_delta = (
        num_items(Items.Power)
        - start_power
    )

    rate = 0

    if elapsed > 0:
        rate = (
            gained
            / elapsed
        )

    quick_print(
        "FARM RESULT",
        MODE_NAMES[BENCH_MODE],
        "focus",
        BENCH_FOCUS,
        "world",
        BENCH_WORLD_SIZE,
        "drones",
        max_drones(),
        "elapsed",
        elapsed,
        "gain",
        gained,
        "rate",
        rate,
        "power-delta",
        power_delta
    )


main()
