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
    "persistent-spatial-tree-ring",
    "persistent-power-ring",
    "persistent-power-ring-tail3",
    "patch16-6x6-power",
    "patch16-6x6-power-tail3",
    "patch16-7x7-power-tail3"
]

TAIL_LIMIT = 3
FALLBACK_ROUNDS = 200
PERSISTENT_MERGE_TIMEOUT = 30
SPATIAL_DEPLOY_TIMEOUT = 5
SPATIAL_DEPLOY_SETTLE = 0.05
PATCH_HARVEST_SETTLE = 0.05


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


def _wait_for_spatial_deployment(
    expected_drones
):
    deadline = (
        get_time()
        + SPATIAL_DEPLOY_TIMEOUT
    )

    while (
        num_drones()
        < expected_drones
    ):
        if get_time() >= deadline:
            return False

    # spawn_drone() places the child immediately at the parent's current
    # position, but the newly created task may not have executed yet.
    # Give the final generation a tiny scheduling window before any
    # Pumpkin worker starts growing/merging the field.
    end_time = (
        get_time()
        + SPATIAL_DEPLOY_SETTLE
    )

    while get_time() < end_time:
        pass

    return True


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

    # Every task owns exactly the midpoint of its interval.
    # The parent now moves to a child's midpoint BEFORE spawn_drone().
    # Because children inherit the parent's current position, every new
    # drone is born directly on its owned column.
    utils.move_to(
        column,
        0
    )

    handles = []

    if start_column < column:
        left_start = start_column
        left_end = column - 1
        left_column = (
            left_start
            + left_end
        ) // 2

        utils.move_to(
            left_column,
            0
        )

        handle = spawn_drone(
            _persistent_spatial_subtree,
            left_start,
            left_end,
            size,
            cycles
        )

        if handle == None:
            return False

        handles.append(handle)

        utils.move_to(
            column,
            0
        )

    if column < end_column:
        right_start = column + 1
        right_end = end_column
        right_column = (
            right_start
            + right_end
        ) // 2

        utils.move_to(
            right_column,
            0
        )

        handle = spawn_drone(
            _persistent_spatial_subtree,
            right_start,
            right_end,
            size,
            cycles
        )

        if handle == None:
            return False

        handles.append(handle)

        utils.move_to(
            column,
            0
        )

    # Critical correctness barrier:
    # do not allow early columns to mature into partial Giant Pumpkins
    # while deeper tree nodes are still being deployed. At full capacity
    # every column 0..size-1 has exactly one live owner.
    if not _wait_for_spatial_deployment(
        size
    ):
        return False

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

    left_start = 1
    left_end = split
    left_column = (
        left_start
        + left_end
    ) // 2

    utils.move_to(
        left_column,
        0
    )

    handle = spawn_drone(
        _persistent_spatial_subtree,
        left_start,
        left_end,
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

    if split + 1 <= size - 1:
        right_start = split + 1
        right_end = size - 1
        right_column = (
            right_start
            + right_end
        ) // 2

        utils.move_to(
            right_column,
            0
        )

        handle = spawn_drone(
            _persistent_spatial_subtree,
            right_start,
            right_end,
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

    if not _wait_for_spatial_deployment(
        size
    ):
        quick_print(
            "PUMPKIN SPATIAL DEPLOY INVALID",
            "drones",
            num_drones(),
            "expected",
            size
        )

        return []

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


def _tail_finish_ring_tile():
    # Source-near adaptation of Flekay mega_line.py:
    # spend extra resources only on the final local stragglers.
    if num_items(Items.Water) >= 2:
        use_item(
            Items.Water,
            2
        )

    while True:
        entity = get_entity_type()

        if (
            entity == Entities.Pumpkin
            and can_harvest()
        ):
            return 1

        if entity == Entities.Dead_Pumpkin:
            if not utils.can_afford(
                Entities.Pumpkin
            ):
                return -1

            plant(
                Entities.Pumpkin
            )

        elif entity == None:
            if get_ground_type() != Grounds.Soil:
                till()

            if not utils.can_afford(
                Entities.Pumpkin
            ):
                return -1

            plant(
                Entities.Pumpkin
            )

        if num_items(Items.Fertilizer) <= 0:
            return 0

        use_item(
            Items.Fertilizer
        )


def _persistent_ring_worker_tail(
    column,
    size,
    cycles,
    tail_limit
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

                    if (
                        state == 0
                        and remaining <= tail_limit
                    ):
                        state = (
                            _tail_finish_ring_tile()
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
            merge_deadline = (
                get_time()
                + PERSISTENT_MERGE_TIMEOUT
            )

            while not pumpkin.is_full_map_pumpkin():
                if get_time() >= merge_deadline:
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

            while (
                get_entity_type()
                == Entities.Pumpkin
            ):
                pass

    if column == 0:
        return gains

    return True


def _persistent_power_ring_worker(
    column,
    size,
    cycles,
    tail_limit
):
    handles = []
    power = 1

    # Flekay jarvan/for_all_sync power-of-two fan-out:
    # 0 -> 1,2,4,8,16
    # 1 -> 3,5,9,17
    # 2 -> 6,10,18
    # ...
    #
    # Crucially, do not move before spawning. spawn-v4 measured that
    # hierarchical spawn + later parallel positioning beats serial
    # parent placement by a large margin.
    while column + power < size:
        if power > column:
            child = (
                column
                + power
            )

            handle = spawn_drone(
                _persistent_power_ring_worker,
                child,
                size,
                cycles,
                tail_limit
            )

            if handle == None:
                if column == 0:
                    return []

                return False

            handles.append(
                handle
            )

        power *= 2

    if not _wait_for_spatial_deployment(
        size
    ):
        if column == 0:
            return []

        return False

    if tail_limit > 0:
        result = _persistent_ring_worker_tail(
            column,
            size,
            cycles,
            tail_limit
        )
    else:
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


def _run_persistent_power_ring(
    cycles,
    tail_limit
):
    size = utils.size()

    if max_drones() < size:
        return []

    clear()

    return _persistent_power_ring_worker(
        0,
        size,
        cycles,
        tail_limit
    )


def _patch_geometry(
    worker_index,
    patch_size
):
    patch_index = (
        worker_index
        // 2
    )
    side = (
        worker_index
        % 2
    )

    patch_x = (
        patch_index
        % 4
    )
    patch_y = (
        patch_index
        // 4
    )

    pitch = (
        patch_size
        + 1
    )

    origin_x = (
        patch_x
        * pitch
    )
    origin_y = (
        patch_y
        * pitch
    )

    split = (
        patch_size
        // 2
    )

    if side == 0:
        start_x = 0
        end_x = split
    else:
        start_x = split
        end_x = patch_size

    return (
        origin_x,
        origin_y,
        start_x,
        end_x,
        side
    )


def _patch_positions(
    origin_x,
    origin_y,
    start_x,
    end_x,
    patch_size
):
    positions = []

    for dy in range(
        patch_size
    ):
        y = (
            origin_y
            + dy
        )

        if dy % 2 == 0:
            for dx in range(
                start_x,
                end_x
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
                end_x - 1,
                start_x - 1,
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


def _patch_ensure_pumpkin():
    entity = get_entity_type()

    if entity == Entities.Pumpkin:
        return True

    if entity == Entities.Dead_Pumpkin:
        if not utils.can_afford(
            Entities.Pumpkin
        ):
            return False

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

    if not utils.can_afford(
        Entities.Pumpkin
    ):
        return False

    utils.water()

    return plant(
        Entities.Pumpkin
    )


def _patch_tail_finish():
    if num_items(Items.Water) >= 2:
        use_item(
            Items.Water,
            2
        )

    while True:
        entity = get_entity_type()

        if entity == None:
            # The patch leader may already have harvested the giant.
            return 0

        if (
            entity == Entities.Pumpkin
            and can_harvest()
        ):
            return 1

        if entity == Entities.Dead_Pumpkin:
            if not utils.can_afford(
                Entities.Pumpkin
            ):
                return -1

            plant(
                Entities.Pumpkin
            )

        if num_items(Items.Fertilizer) <= 0:
            return 0

        use_item(
            Items.Fertilizer
        )


def _patch_half_ready(
    worker_index,
    patch_size,
    tail_limit
):
    (
        origin_x,
        origin_y,
        start_x,
        end_x,
        side
    ) = _patch_geometry(
        worker_index,
        patch_size
    )

    positions = _patch_positions(
        origin_x,
        origin_y,
        start_x,
        end_x,
        patch_size
    )

    for position in positions:
        x, y = position

        utils.move_to(
            x,
            y
        )

        if not _patch_ensure_pumpkin():
            return -1

    remaining = positions

    while len(remaining) > 0:
        next_remaining = []
        use_tail = (
            tail_limit > 0
            and len(remaining) <= tail_limit
        )

        for position in remaining:
            x, y = position

            utils.move_to(
                x,
                y
            )

            entity = get_entity_type()

            if entity == None:
                # The complete patch was harvested while this worker was
                # still observing the final mature positions.
                return 0

            if entity == Entities.Dead_Pumpkin:
                if not _patch_ensure_pumpkin():
                    return -1

                if use_tail:
                    state = _patch_tail_finish()

                    if state < 0:
                        return -1

                    if state == 0:
                        return 0

                    continue

                next_remaining.append(
                    position
                )
                continue

            if (
                entity == Entities.Pumpkin
                and can_harvest()
            ):
                continue

            if use_tail:
                state = _patch_tail_finish()

                if state < 0:
                    return -1

                if state == 0:
                    return 0

                continue

            next_remaining.append(
                position
            )

        remaining = (
            next_remaining
        )

    return 1


def _is_patch_giant(
    origin_x,
    origin_y,
    patch_size
):
    utils.move_to(
        origin_x,
        origin_y
    )

    if get_entity_type() != Entities.Pumpkin:
        return False

    first_id = measure()

    utils.move_to(
        origin_x + patch_size - 1,
        origin_y + patch_size - 1
    )

    if get_entity_type() != Entities.Pumpkin:
        return False

    return (
        first_id == measure()
        and can_harvest()
    )


def _patch_worker(
    worker_index,
    patch_size,
    target,
    tail_limit
):
    (
        origin_x,
        origin_y,
        start_x,
        end_x,
        side
    ) = _patch_geometry(
        worker_index,
        patch_size
    )

    while (
        num_items(Items.Pumpkin)
        < target
    ):
        state = _patch_half_ready(
            worker_index,
            patch_size,
            tail_limit
        )

        if state < 0:
            return False

        if (
            num_items(Items.Pumpkin)
            >= target
        ):
            return True

        if side == 0:
            while (
                num_items(Items.Pumpkin)
                < target
            ):
                if _is_patch_giant(
                    origin_x,
                    origin_y,
                    patch_size
                ):
                    harvest()

                    # Give the helper a deterministic farm-state edge.
                    # Without this, the leader can replant the origin so
                    # quickly that the helper misses the empty-patch signal
                    # and waits until the following harvest.
                    settle_end = (
                        get_time()
                        + PATCH_HARVEST_SETTLE
                    )

                    while get_time() < settle_end:
                        pass

                    break
        else:
            utils.move_to(
                origin_x,
                origin_y
            )

            while (
                get_entity_type()
                != None
            ):
                if (
                    num_items(Items.Pumpkin)
                    >= target
                ):
                    return True

    return True


def _patch_power_worker(
    worker_index,
    patch_size,
    target,
    tail_limit
):
    handles = []
    power = 1
    worker_count = 32

    while (
        worker_index + power
        < worker_count
    ):
        if power > worker_index:
            child = (
                worker_index
                + power
            )

            handle = spawn_drone(
                _patch_power_worker,
                child,
                patch_size,
                target,
                tail_limit
            )

            if handle == None:
                return False

            handles.append(
                handle
            )

        power *= 2

    if not _wait_for_spatial_deployment(
        worker_count
    ):
        return False

    success = _patch_worker(
        worker_index,
        patch_size,
        target,
        tail_limit
    )

    for handle in handles:
        if not wait_for(handle):
            success = False

    return success


def _run_patch_power(
    patch_size,
    target,
    tail_limit
):
    if (
        utils.size() != 32
        or max_drones() < 32
    ):
        return False

    clear()

    return _patch_power_worker(
        0,
        patch_size,
        target,
        tail_limit
    )


def run_throughput_mode(
    mode,
    target
):
    if mode == 25:
        return _run_patch_power(
            6,
            target,
            0
        )

    if mode == 26:
        return _run_patch_power(
            6,
            target,
            3
        )

    if mode == 27:
        return _run_patch_power(
            7,
            target,
            3
        )

    return False


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

    if mode == 23:
        return _run_persistent_power_ring(
            cycles,
            0
        )

    if mode == 24:
        return _run_persistent_power_ring(
            cycles,
            3
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

    throughput_mode = (
        BENCH_MODE >= 25
    )

    if throughput_mode:
        gains = []
        success = run_throughput_mode(
            BENCH_MODE,
            BENCH_TARGET_PUMPKIN
        )
    else:
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

    if throughput_mode:
        valid = (
            success
            and gain >= BENCH_TARGET_PUMPKIN
        )
    else:
        valid = success

    pumpkins_per_second = 0

    if elapsed > 0:
        pumpkins_per_second = (
            gain
            / elapsed
        )

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
        "target",
        BENCH_TARGET_PUMPKIN,
        "cycle gain",
        cycle_gain,
        "ticks",
        ticks,
        "elapsed",
        elapsed,
        "pumpkins/sec",
        pumpkins_per_second,
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
