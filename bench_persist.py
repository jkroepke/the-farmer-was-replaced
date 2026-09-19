import farm
import utils
import workers


LAYOUT_NAMES = [
    "pure-crop",
    "one-row-dumb",
    "one-col-dumb",
    "two-col-dumb",
    "one-col-max"
]

ARCH_NAMES = [
    "main-stride",
    "main-chunks",
    "main-pairs",
    "scheduler-chunks"
]


def current_focus(
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    if num_items(
        Items.Carrot
    ) < carrot_mid:
        return Items.Carrot

    if num_items(
        Items.Hay
    ) < hay_target:
        return Items.Hay

    if num_items(
        Items.Wood
    ) < wood_target:
        return Items.Wood

    if num_items(
        Items.Carrot
    ) < carrot_final:
        return Items.Carrot

    return None


def run_sync(
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    while num_items(
        Items.Carrot
    ) < carrot_mid:
        farm.run(
            Items.Carrot
        )

    while num_items(
        Items.Hay
    ) < hay_target:
        farm.run(
            Items.Hay
        )

    while num_items(
        Items.Wood
    ) < wood_target:
        farm.run(
            Items.Wood
        )

    while num_items(
        Items.Carrot
    ) < carrot_final:
        farm.run(
            Items.Carrot
        )


def layout_sun_columns(
    layout
):
    if layout == 2:
        return 1

    if layout == 3:
        return 2

    if layout == 4:
        return 1

    return 0


def layout_crop_columns(
    layout,
    world_size
):
    return (
        world_size
        - layout_sun_columns(
            layout
        )
    )


def service_crop_tile(
    layout,
    focus_item,
    x,
    world_size
):
    if (
        layout == 1
        and get_pos_y()
        == world_size - 1
    ):
        farm._service_sunflower_dumb()
        return

    farm.farm_resource(
        x,
        x + 1,
        focus_item
    )


def process_column(
    x,
    layout,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    focus_item = current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )

    if focus_item == None:
        return False

    world_size = utils.size()

    utils.move_to(
        x,
        0
    )

    for _ in range(
        world_size
    ):
        service_crop_tile(
            layout,
            focus_item,
            x,
            world_size
        )

        move(
            North
        )

    return True


def crop_stride(
    worker_index,
    worker_count,
    crop_columns,
    layout,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    while current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ) != None:
        x = worker_index

        while x < crop_columns:
            if not process_column(
                x,
                layout,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            ):
                return True

            x += worker_count

    return True


def crop_chunk(
    start_x,
    end_x,
    layout,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    while current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ) != None:
        for x in range(
            start_x,
            end_x
        ):
            if not process_column(
                x,
                layout,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            ):
                return True

    return True


def crop_pairs(
    worker_index,
    worker_count,
    crop_columns,
    layout,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    pair = worker_index

    while current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ) != None:
        pair = worker_index

        while (
            pair * 2
            < crop_columns
        ):
            start_x = pair * 2

            if not process_column(
                start_x,
                layout,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            ):
                return True

            if (
                start_x + 1
                < crop_columns
            ):
                if not process_column(
                    start_x + 1,
                    layout,
                    carrot_mid,
                    hay_target,
                    wood_target,
                    carrot_final
                ):
                    return True

            pair += worker_count

    return True


def sun_dumb_worker(
    column,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    world_size = utils.size()

    while current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ) != None:
        utils.move_to(
            column,
            0
        )

        for _ in range(
            world_size
        ):
            farm._service_sunflower_dumb()

            move(
                North
            )

    return True


def sun_max_worker(
    column,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    world_size = utils.size()
    petals = []

    utils.move_to(
        column,
        0
    )

    for _ in range(
        world_size
    ):
        if farm._ensure_sunflower_here():
            petals.append(
                measure()
            )
        else:
            petals.append(
                -1
            )

        move(
            North
        )

    while current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ) != None:
        max_petals = max(
            petals
        )

        if max_petals <= 0:
            row = 0

            while row < world_size:
                utils.move_to(
                    column,
                    row
                )

                if farm._ensure_sunflower_here():
                    petals[row] = measure()

                row += 1

            continue

        harvested = False
        repaired = False

        for row in range(
            world_size
        ):
            if petals[row] != max_petals:
                continue

            utils.move_to(
                column,
                row
            )

            if get_entity_type() != Entities.Sunflower:
                if farm._ensure_sunflower_here():
                    petals[row] = measure()
                else:
                    petals[row] = -1

                repaired = True
                break

            actual_petals = measure()

            if actual_petals != petals[row]:
                petals[row] = actual_petals
                repaired = True
                break

            if can_harvest():
                harvest()

                if farm._ensure_sunflower_here():
                    petals[row] = measure()
                else:
                    petals[row] = -1

                harvested = True
                break

        if repaired:
            continue

        if not harvested:
            pass

    return True


def spawn_sun_workers(
    handles,
    layout,
    world_size,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    if layout == 2:
        drone = spawn_drone(
            sun_dumb_worker,
            world_size - 1,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if drone != None:
            handles.append(
                drone
            )

        return drone != None

    if layout == 3:
        column = world_size - 2

        while column < world_size:
            drone = spawn_drone(
                sun_dumb_worker,
                column,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            )

            if drone == None:
                return False

            handles.append(
                drone
            )

            column += 1

        return True

    if layout == 4:
        drone = spawn_drone(
            sun_max_worker,
            world_size - 1,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if drone != None:
            handles.append(
                drone
            )

        return drone != None

    return True


def run_main_workers(
    layout,
    architecture,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    world_size = utils.size()
    sun_workers = layout_sun_columns(
        layout
    )
    crop_columns = layout_crop_columns(
        layout,
        world_size
    )
    crop_workers = min(
        crop_columns,
        max_drones()
        - sun_workers
    )

    if crop_workers < 1:
        return False

    handles = []

    if architecture == 0:
        worker_index = 1

        while worker_index < crop_workers:
            drone = spawn_drone(
                crop_stride,
                worker_index,
                crop_workers,
                crop_columns,
                layout,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            )

            if drone == None:
                return False

            handles.append(
                drone
            )

            worker_index += 1

        if not spawn_sun_workers(
            handles,
            layout,
            world_size,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        ):
            return False

        crop_stride(
            0,
            crop_workers,
            crop_columns,
            layout,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

    elif architecture == 1:
        chunks = workers.make_chunks(
            crop_columns,
            crop_workers
        )

        chunk_index = 1

        while chunk_index < len(
            chunks
        ):
            start_x, end_x = chunks[
                chunk_index
            ]

            drone = spawn_drone(
                crop_chunk,
                start_x,
                end_x,
                layout,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            )

            if drone == None:
                return False

            handles.append(
                drone
            )

            chunk_index += 1

        if not spawn_sun_workers(
            handles,
            layout,
            world_size,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        ):
            return False

        start_x, end_x = chunks[0]

        crop_chunk(
            start_x,
            end_x,
            layout,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

    else:
        pair_count = (
            crop_columns
            + 1
        ) // 2

        pair_workers = min(
            pair_count,
            crop_workers
        )

        worker_index = 1

        while worker_index < pair_workers:
            drone = spawn_drone(
                crop_pairs,
                worker_index,
                pair_workers,
                crop_columns,
                layout,
                carrot_mid,
                hay_target,
                wood_target,
                carrot_final
            )

            if drone == None:
                return False

            handles.append(
                drone
            )

            worker_index += 1

        if not spawn_sun_workers(
            handles,
            layout,
            world_size,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        ):
            return False

        crop_pairs(
            0,
            pair_workers,
            crop_columns,
            layout,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

    for drone in handles:
        wait_for(
            drone
        )

    return True


def run_scheduler(
    layout,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    world_size = utils.size()
    sun_workers = layout_sun_columns(
        layout
    )
    crop_columns = layout_crop_columns(
        layout,
        world_size
    )
    crop_workers = min(
        crop_columns,
        max_drones()
        - sun_workers
        - 1
    )

    if crop_workers < 1:
        return False

    chunks = workers.make_chunks(
        crop_columns,
        crop_workers
    )

    handles = []

    for start_x, end_x in chunks:
        drone = spawn_drone(
            crop_chunk,
            start_x,
            end_x,
            layout,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if drone == None:
            return False

        handles.append(
            drone
        )

    if not spawn_sun_workers(
        handles,
        layout,
        world_size,
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ):
        return False

    for drone in handles:
        wait_for(
            drone
        )

    return True


def run_persistent(
    layout,
    architecture,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    if architecture == 3:
        return run_scheduler(
            layout,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

    return run_main_workers(
        layout,
        architecture,
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )


def main():
    set_world_size(
        BENCH_WORLD_SIZE
    )

    clear()
    workers.set_main_hat()
    farm.reset_state()

    start_carrot = num_items(
        Items.Carrot
    )
    start_hay = num_items(
        Items.Hay
    )
    start_wood = num_items(
        Items.Wood
    )
    start_power = num_items(
        Items.Power
    )

    carrot_mid = (
        start_carrot
        + BENCH_CARROT_GAIN
    )

    carrot_final = (
        carrot_mid
        + BENCH_CARROT_GAIN
    )

    hay_target = (
        start_hay
        + BENCH_HAY_GAIN
    )

    wood_target = (
        start_wood
        + BENCH_WOOD_GAIN
    )

    start_time = get_time()

    if BENCH_KIND == 0:
        quick_print(
            "PERSIST MODE START",
            "sync-selected",
            "world",
            BENCH_WORLD_SIZE,
            "drones",
            max_drones()
        )

        run_sync(
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

    else:
        quick_print(
            "PERSIST MODE START",
            LAYOUT_NAMES[
                BENCH_LAYOUT
            ],
            ARCH_NAMES[
                BENCH_ARCH
            ],
            "world",
            BENCH_WORLD_SIZE,
            "drones",
            max_drones()
        )

        success = run_persistent(
            BENCH_LAYOUT,
            BENCH_ARCH,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if not success:
            quick_print(
                "PERSIST BENCH INVALID",
                LAYOUT_NAMES[
                    BENCH_LAYOUT
                ],
                ARCH_NAMES[
                    BENCH_ARCH
                ]
            )

    elapsed = (
        get_time()
        - start_time
    )

    quick_print(
        "PERSIST RESULT",
        "kind",
        BENCH_KIND,
        "layout",
        BENCH_LAYOUT,
        "arch",
        BENCH_ARCH,
        "elapsed",
        elapsed,
        "carrot-gain",
        num_items(
            Items.Carrot
        ) - start_carrot,
        "hay-gain",
        num_items(
            Items.Hay
        ) - start_hay,
        "wood-gain",
        num_items(
            Items.Wood
        ) - start_wood,
        "start-power",
        start_power,
        "end-power",
        num_items(
            Items.Power
        )
    )


if __name__ == "__main__":
    main()
