import config
import pumpkin
import utils


MODE_NAMES = [
    "current-production",
    "legacy-patch-wait",
    "sparse-1x32",
    "sparse-2x16",
    "sparse-4x8",
    "sparse-8x4",
    "sparse-16x2",
    "sparse-1x32-tail",
    "sparse-4x8-tail",
    "sparse-8x4-tail",
    "tree-1x32-tail",
    "tree-4x8-tail",
    "tree-8x4-tail",
    "persistent-1x32-tail",
    "persistent-4x8-tail",
    "persistent-8x4-tail",
    "persistent-tree-4x8-tail",
    "persistent-tree-8x4-tail",
    "ring-reuse",
    "persistent-ring",
    "persistent-tree-ring",
    "persistent-placed-ring",
    "persistent-spatial-tree-ring"
]

TAIL_LIMIT = 3
FALLBACK_ROUNDS = 200
PERSISTENT_MERGE_TIMEOUT = 30


def _repair_current():
    entity = get_entity_type()

    if entity == Entities.Pumpkin:
        return True

    if entity == Entities.Dead_Pumpkin:
        utils.water()

        return plant(
            Entities.Pumpkin
        )

    if entity != None:
        if not can_harvest():
            return False

        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    utils.water()

    return plant(
        Entities.Pumpkin
    )


def _tail_finish_current():
    utils.water()

    while True:
        entity = get_entity_type()

        if (
            entity == Entities.Pumpkin
            and can_harvest()
        ):
            return True

        if entity != Entities.Pumpkin:
            if not _repair_current():
                return False

        if num_items(
            Items.Fertilizer
        ) > 0:
            use_item(
                Items.Fertilizer
            )


def _position_ready(
    tail_boost
):
    entity = get_entity_type()

    if entity == Entities.Pumpkin:
        if can_harvest():
            return True

        if tail_boost:
            return _tail_finish_current()

        return False

    if not _repair_current():
        return False

    if tail_boost:
        return _tail_finish_current()

    return False


def _region_positions(
    origin_x,
    origin_y,
    width,
    height
):
    positions = []

    for dy in range(
        height
    ):
        y = (
            origin_y
            + dy
        )

        if dy % 2 == 0:
            for dx in range(
                width
            ):
                positions.append(
                    (
                        origin_x
                        + dx,
                        y
                    )
                )
        else:
            for dx in range(
                width - 1,
                -1,
                -1
            ):
                positions.append(
                    (
                        origin_x
                        + dx,
                        y
                    )
                )

    return positions


def _run_region(
    origin_x,
    origin_y,
    width,
    height,
    tail_boost
):
    positions = _region_positions(
        origin_x,
        origin_y,
        width,
        height
    )

    for position in positions:
        x, y = position

        utils.move_to(
            x,
            y
        )

        if not _repair_current():
            return False

    remaining = positions

    while len(
        remaining
    ) > 0:
        next_remaining = []

        use_tail = (
            tail_boost
            and len(
                remaining
            ) <= TAIL_LIMIT
        )

        for position in remaining:
            x, y = position

            utils.move_to(
                x,
                y
            )

            if not _position_ready(
                use_tail
            ):
                next_remaining.append(
                    position
                )

        remaining = (
            next_remaining
        )

    return True


def _region_count(
    width,
    height
):
    world_size = (
        utils.size()
    )

    return (
        world_size
        // width
        * (
            world_size
            // height
        )
    )


def _run_region_index(
    index,
    width,
    height,
    tail_boost
):
    world_size = (
        utils.size()
    )

    columns = (
        world_size
        // width
    )

    origin_x = (
        index
        % columns
        * width
    )

    origin_y = (
        index
        // columns
        * height
    )

    return _run_region(
        origin_x,
        origin_y,
        width,
        height,
        tail_boost
    )


def _tree_region_worker(
    index,
    width,
    height,
    tail_boost
):
    count = _region_count(
        width,
        height
    )

    handles = []

    left = (
        index
        * 2
        + 1
    )

    right = (
        left
        + 1
    )

    if left < count:
        handle = spawn_drone(
            _tree_region_worker,
            left,
            width,
            height,
            tail_boost
        )

        if handle == None:
            return False

        handles.append(
            handle
        )

    if right < count:
        handle = spawn_drone(
            _tree_region_worker,
            right,
            width,
            height,
            tail_boost
        )

        if handle == None:
            return False

        handles.append(
            handle
        )

    success = _run_region_index(
        index,
        width,
        height,
        tail_boost
    )

    for handle in handles:
        if not wait_for(
            handle
        ):
            success = False

    return success


def _complete_from_problems(
    problems
):
    rounds = 0

    while rounds < FALLBACK_ROUNDS:
        pumpkin.wait_seconds(
            config.PUMPKIN_ID_CHECK_INTERVAL
        )

        if pumpkin.is_full_map_pumpkin():
            return harvest()

        if len(
            problems
        ) > 0:
            problems = (
                pumpkin.patch_problem_positions(
                    problems
                )
            )

            if len(
                problems
            ) > 0:
                pumpkin.wait_seconds(
                    config.PUMPKIN_PATCH_INTERVAL
                )

                rounds += 1
                continue

        if pumpkin.is_full_map_pumpkin():
            return harvest()

        problems = (
            pumpkin.collect_problem_positions()
        )

        rounds += 1

    return False


def _finish_sparse(
    all_ready
):
    if not all_ready:
        return False

    if pumpkin.is_full_map_pumpkin():
        return harvest()

    problems = (
        pumpkin.collect_problem_positions()
    )

    return _complete_from_problems(
        problems
    )


def _run_sparse(
    width,
    height,
    tail_boost,
    tree_spawn
):
    world_size = (
        utils.size()
    )

    if (
        world_size % width != 0
        or world_size % height != 0
    ):
        return False

    count = _region_count(
        width,
        height
    )

    if count > max_drones():
        return False

    clear()

    if tree_spawn:
        return _finish_sparse(
            _tree_region_worker(
                0,
                width,
                height,
                tail_boost
            )
        )

    handles = []
    index = 1

    while index < count:
        handle = spawn_drone(
            _run_region_index,
            index,
            width,
            height,
            tail_boost
        )

        if handle == None:
            for active in handles:
                wait_for(
                    active
                )

            return False

        handles.append(
            handle
        )

        index += 1

    success = _run_region_index(
        0,
        width,
        height,
        tail_boost
    )

    for handle in handles:
        if not wait_for(
            handle
        ):
            success = False

    return _finish_sparse(
        success
    )


def _persistent_region_worker(
    index,
    width,
    height,
    tail_boost,
    cycles
):
    gains = []

    for _ in range(cycles):
        cycle_start = 0

        if index == 0:
            cycle_start = num_items(
                Items.Pumpkin
            )

        if not _run_region_index(
            index,
            width,
            height,
            tail_boost
        ):
            if index == 0:
                return []

            return False

        if index == 0:
            while not pumpkin.is_full_map_pumpkin():
                pumpkin.wait_seconds(
                    0.02
                )

            if not harvest():
                return []

            gains.append(
                num_items(
                    Items.Pumpkin
                )
                - cycle_start
            )
        else:
            world_size = utils.size()
            columns = (
                world_size
                // width
            )
            origin_x = (
                index
                % columns
                * width
            )
            origin_y = (
                index
                // columns
                * height
            )

            utils.move_to(
                origin_x,
                origin_y
            )

            # The merged Pumpkin remains a Pumpkin until worker 0
            # harvests it. Its disappearance is a global, observable
            # cycle barrier that does not require shared Python memory.
            while (
                get_entity_type()
                == Entities.Pumpkin
            ):
                pass

            # Normal full-map harvest leaves the Pumpkin field on Soil.
            # A non-Soil origin means worker 0 aborted the benchmark with
            # clear() after the bounded merge wait.
            if get_ground_type() != Grounds.Soil:
                return False

    if index == 0:
        return gains

    return True


def _persistent_tree_worker(
    index,
    width,
    height,
    tail_boost,
    cycles
):
    count = _region_count(
        width,
        height
    )
    handles = []

    left = index * 2 + 1
    right = left + 1

    if left < count:
        handle = spawn_drone(
            _persistent_tree_worker,
            left,
            width,
            height,
            tail_boost,
            cycles
        )

        if handle == None:
            if index == 0:
                return []

            return False

        handles.append(handle)

    if right < count:
        handle = spawn_drone(
            _persistent_tree_worker,
            right,
            width,
            height,
            tail_boost,
            cycles
        )

        if handle == None:
            if index == 0:
                return []

            return False

        handles.append(handle)

    result = _persistent_region_worker(
        index,
        width,
        height,
        tail_boost,
        cycles
    )

    success = True

    if index == 0:
        success = len(result) == cycles
    else:
        success = result

    for handle in handles:
        child = wait_for(handle)

        if not child:
            success = False

    if index == 0:
        if success:
            return result

        return []

    return success


def _run_persistent_sparse(
    width,
    height,
    tail_boost,
    tree_spawn,
    cycles
):
    world_size = utils.size()

    if (
        world_size % width != 0
        or world_size % height != 0
    ):
        return []

    count = _region_count(
        width,
        height
    )

    if count > max_drones():
        return []

    clear()

    if tree_spawn:
        return _persistent_tree_worker(
            0,
            width,
            height,
            tail_boost,
            cycles
        )

    handles = []

    for index in range(1, count):
        handle = spawn_drone(
            _persistent_region_worker,
            index,
            width,
            height,
            tail_boost,
            cycles
        )

        if handle == None:
            return []

        handles.append(handle)

    gains = _persistent_region_worker(
        0,
        width,
        height,
        tail_boost,
        cycles
    )

    success = (
        len(gains)
        == cycles
    )

    for handle in handles:
        if not wait_for(handle):
            success = False

    if success:
        return gains

    return []


def _finish_ring_cycle():
    if pumpkin.is_full_map_pumpkin():
        return harvest()

    problems = (
        pumpkin.collect_problem_positions()
    )

    return _complete_from_problems(
        problems
    )


def _run_ring_cycle(
    reset_field
):
    if reset_field:
        clear()

    if not pumpkin.run_column_workers():
        return False

    return _finish_ring_cycle()


def _run_ring_reuse(
    cycles
):
    gains = []

    for cycle in range(cycles):
        cycle_start = num_items(
            Items.Pumpkin
        )

        if not _run_ring_cycle(
            cycle == 0
        ):
            return []

        gains.append(
            num_items(
                Items.Pumpkin
            )
            - cycle_start
        )

    return gains


def _persistent_ring_worker(
    column,
    size,
    cycles
):
    gains = []
    utils.move_to(
        column,
        0
    )

    for _ in range(cycles):
        cycle_start = 0

        if column == 0:
            cycle_start = num_items(
                Items.Pumpkin
            )

        ready = []

        for _ in range(size):
            ready.append(False)

        remaining = size

        while remaining > 0:
            for row in range(size):
                if not ready[row]:
                    state = (
                        pumpkin._service_column_pumpkin()
                    )

                    if state < 0:
                        if column == 0:
                            return []

                        return False

                    if state > 0:
                        ready[row] = True
                        remaining -= 1

                move(North)

        if column == 0:
            # This is intentionally the same merge condition as current
            # production. The ring traversal is already measured valid;
            # this mode changes worker lifetime, not repair semantics.
            merge_deadline = (
                get_time()
                + PERSISTENT_MERGE_TIMEOUT
            )

            while not pumpkin.is_full_map_pumpkin():
                if get_time() >= merge_deadline:
                    # Global abort signal for the waiting column owners.
                    # A normal giant-Pumpkin harvest leaves Soil; clear()
                    # resets the failed test field instead.
                    clear()
                    return []

            if not harvest():
                clear()
                return []

            gains.append(
                num_items(
                    Items.Pumpkin
                )
                - cycle_start
            )
        else:
            utils.move_to(
                column,
                0
            )

            # Only this worker owns this column. After worker 0 harvests
            # the full-map Pumpkin, the origin becomes empty/soil and is
            # therefore an unambiguous next-cycle signal.
            while (
                get_entity_type()
                == Entities.Pumpkin
            ):
                pass

    if column == 0:
        return gains

    return True


def _run_persistent_ring(
    cycles,
    tree_spawn
):
    size = utils.size()

    if max_drones() < size:
        return []

    clear()

    if tree_spawn:
        return _persistent_ring_tree_worker(
            0,
            size,
            cycles
        )

    handles = []

    for column in range(1, size):
        handle = spawn_drone(
            _persistent_ring_worker,
            column,
            size,
            cycles
        )

        if handle == None:
            return []

        handles.append(handle)

    gains = _persistent_ring_worker(
        0,
        size,
        cycles
    )

    success = (
        len(gains)
        == cycles
    )

    for handle in handles:
        if not wait_for(handle):
            success = False

    if success:
        return gains

    return []


def _run_persistent_placed_ring(
    cycles
):
    size = utils.size()

    if max_drones() < size:
        return []

    clear()
    utils.move_to(
        0,
        0
    )
    handles = []

    # Direct interpretation of spawn locality:
    # move the launcher to the child's owned column first, then spawn.
    # This eliminates child positioning, but serializes one parent move
    # between each spawn. The benchmark decides whether that trade pays.
    for column in range(1, size):
        move(East)

        handle = spawn_drone(
            _persistent_ring_worker,
            column,
            size,
            cycles
        )

        if handle == None:
            return []

        handles.append(handle)

    utils.move_to(
        0,
        0
    )

    gains = _persistent_ring_worker(
        0,
        size,
        cycles
    )

    success = (
        len(gains)
        == cycles
    )

    for handle in handles:
        if not wait_for(handle):
            success = False

    if success:
        return gains

    return []


def _persistent_spatial_subtree(
    start_column,
    end_column,
    size,
    cycles
):
    if start_column > end_column:
        return True

    column = (
        start_column
        + end_column
    ) // 2

    # This is the key locality experiment: a child starts at its parent's
    # current location, moves only to the midpoint of its own interval,
    # then spawns the next generation from that new position.
    utils.move_to(
        column,
        0
    )

    handles = []

    if start_column < column:
        handle = spawn_drone(
            _persistent_spatial_subtree,
            start_column,
            column - 1,
            size,
            cycles
        )

        if handle == None:
            return False

        handles.append(handle)

    if column < end_column:
        handle = spawn_drone(
            _persistent_spatial_subtree,
            column + 1,
            end_column,
            size,
            cycles
        )

        if handle == None:
            return False

        handles.append(handle)

    success = _persistent_ring_worker(
        column,
        size,
        cycles
    )

    for handle in handles:
        if not wait_for(handle):
            success = False

    return success


def _run_persistent_spatial_tree_ring(
    cycles
):
    size = utils.size()

    if max_drones() < size:
        return []

    clear()
    utils.move_to(
        0,
        0
    )

    handles = []

    # Keep worker 0 at the origin as the merge/harvest coordinator.
    # Split the remaining ring into two near-equal arcs. Both first-level
    # children start at column 0, then move in opposite short directions
    # to their interval midpoints (8 and 24 for size 32).
    split = size // 2

    handle = spawn_drone(
        _persistent_spatial_subtree,
        1,
        split,
        size,
        cycles
    )

    if handle == None:
        return []

    handles.append(handle)

    if split + 1 <= size - 1:
        handle = spawn_drone(
            _persistent_spatial_subtree,
            split + 1,
            size - 1,
            size,
            cycles
        )

        if handle == None:
            return []

        handles.append(handle)

    gains = _persistent_ring_worker(
        0,
        size,
        cycles
    )

    success = (
        len(gains)
        == cycles
    )

    for handle in handles:
        if not wait_for(handle):
            success = False

    if success:
        return gains

    return []


def _persistent_ring_tree_worker(
    column,
    size,
    cycles
):
    handles = []

    left = column * 2 + 1
    right = left + 1

    if left < size:
        handle = spawn_drone(
            _persistent_ring_tree_worker,
            left,
            size,
            cycles
        )

        if handle == None:
            if column == 0:
                return []

            return False

        handles.append(handle)

    if right < size:
        handle = spawn_drone(
            _persistent_ring_tree_worker,
            right,
            size,
            cycles
        )

        if handle == None:
            if column == 0:
                return []

            return False

        handles.append(handle)

    result = _persistent_ring_worker(
        column,
        size,
        cycles
    )

    if column == 0:
        success = (
            len(result)
            == cycles
        )
    else:
        success = result

    for handle in handles:
        if not wait_for(handle):
            success = False

    if column == 0:
        if success:
            return result

        return []

    return success


def _run_legacy():
    if not pumpkin.can_start():
        return False

    clear()

    if not pumpkin.plant_full_field():
        return False

    pumpkin.wait_seconds(
        config.PUMPKIN_INITIAL_WAIT
    )

    if pumpkin.is_full_map_pumpkin():
        return harvest()

    problems = (
        pumpkin.collect_problem_positions()
    )

    return _complete_from_problems(
        problems
    )


def run_mode(
    mode
):
    if mode == 0:
        return pumpkin.run()

    if mode == 1:
        return _run_legacy()

    if mode == 2:
        return _run_sparse(
            1,
            32,
            False,
            False
        )

    if mode == 3:
        return _run_sparse(
            2,
            16,
            False,
            False
        )

    if mode == 4:
        return _run_sparse(
            4,
            8,
            False,
            False
        )

    if mode == 5:
        return _run_sparse(
            8,
            4,
            False,
            False
        )

    if mode == 6:
        return _run_sparse(
            16,
            2,
            False,
            False
        )

    if mode == 7:
        return _run_sparse(
            1,
            32,
            True,
            False
        )

    if mode == 8:
        return _run_sparse(
            4,
            8,
            True,
            False
        )

    if mode == 9:
        return _run_sparse(
            8,
            4,
            True,
            False
        )

    if mode == 10:
        return _run_sparse(
            1,
            32,
            True,
            True
        )

    if mode == 11:
        return _run_sparse(
            4,
            8,
            True,
            True
        )

    if mode == 12:
        return _run_sparse(
            8,
            4,
            True,
            True
        )

    return False


def run_benchmark_mode(
    mode,
    cycles
):
    if mode == 13:
        return _run_persistent_sparse(
            1,
            32,
            True,
            False,
            cycles
        )

    if mode == 14:
        return _run_persistent_sparse(
            4,
            8,
            True,
            False,
            cycles
        )

    if mode == 15:
        return _run_persistent_sparse(
            8,
            4,
            True,
            False,
            cycles
        )

    if mode == 16:
        return _run_persistent_sparse(
            4,
            8,
            True,
            True,
            cycles
        )

    # Modes 13..17 were the first persistent sparse experiment.
    # In-game measurement showed that sparse local completion creates
    # harvestable partial Giant Pumpkins. Those modes can never satisfy
    # the full-map merge invariant and are intentionally rejected here
    # instead of entering the old infinite merge wait.
    if (
        mode >= 13
        and mode <= 17
    ):
        return []

    if mode == 18:
        return _run_ring_reuse(
            cycles
        )

    if mode == 19:
        return _run_persistent_ring(
            cycles,
            False
        )

    if mode == 20:
        return _run_persistent_ring(
            cycles,
            True
        )

    if mode == 21:
        return _run_persistent_placed_ring(
            cycles
        )

    if mode == 22:
        return _run_persistent_spatial_tree_ring(
            cycles
        )

    gains = []

    for _ in range(cycles):
        cycle_start = num_items(
            Items.Pumpkin
        )

        if not run_mode(mode):
            return []

        gains.append(
            num_items(
                Items.Pumpkin
            )
            - cycle_start
        )

    return gains


def _valid_gains(
    gains,
    cycles
):
    if (
        len(gains) != cycles
        or cycles < 1
    ):
        return False

    expected = BENCH_EXPECTED_CYCLE_GAIN

    if expected <= 0:
        return False

    for gain in gains:
        if gain != expected:
            return False

    return True


def main():
    set_world_size(
        BENCH_WORLD_SIZE
    )

    start_pumpkin = num_items(
        Items.Pumpkin
    )

    start_carrot = num_items(
        Items.Carrot
    )

    start_water = num_items(
        Items.Water
    )

    start_fertilizer = num_items(
        Items.Fertilizer
    )

    start_ticks = (
        get_tick_count()
    )

    start_time = (
        get_time()
    )

    gains = run_benchmark_mode(
        BENCH_MODE,
        BENCH_CYCLES
    )

    success = _valid_gains(
        gains,
        BENCH_CYCLES
    )

    elapsed = (
        get_time()
        - start_time
    )

    ticks = (
        get_tick_count()
        - start_ticks
    )

    gain = (
        num_items(
            Items.Pumpkin
        )
        - start_pumpkin
    )

    carrot_used = (
        start_carrot
        - num_items(
            Items.Carrot
        )
    )

    water_used = (
        start_water
        - num_items(
            Items.Water
        )
    )

    fertilizer_used = (
        start_fertilizer
        - num_items(
            Items.Fertilizer
        )
    )

    valid = success

    cycle_gain = 0

    if len(gains) > 0:
        cycle_gain = gains[0]

    quick_print(
        "PUMPKIN RESULT",
        BENCH_MODE,
        MODE_NAMES[
            BENCH_MODE
        ],
        "success",
        success,
        "completed",
        len(gains),
        "cycles",
        BENCH_CYCLES,
        "gain",
        gain,
        "cycle gain",
        cycle_gain,
        "ticks",
        ticks,
        "elapsed",
        elapsed,
        "carrot used",
        carrot_used,
        "water used",
        water_used,
        "fertilizer used",
        fertilizer_used,
        "valid",
        valid
    )


main()
