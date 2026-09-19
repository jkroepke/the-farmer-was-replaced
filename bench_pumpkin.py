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
    "tree-8x4-tail"
]

TAIL_LIMIT = 3
FALLBACK_ROUNDS = 200


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

    return _run_sparse(
        8,
        4,
        True,
        True
    )


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

    success = run_mode(
        BENCH_MODE
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

    valid = (
        success
        and gain > 0
    )

    quick_print(
        "PUMPKIN RESULT",
        BENCH_MODE,
        MODE_NAMES[
            BENCH_MODE
        ],
        "success",
        success,
        "gain",
        gain,
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
