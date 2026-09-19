import farm
import utils
import workers


MODE_NAMES = [
    "sync-respawn",
    "persistent-workers"
]


def current_focus(
    carrot_target,
    hay_target,
    wood_target
):
    if num_items(
        Items.Carrot
    ) < carrot_target:
        return Items.Carrot

    if num_items(
        Items.Hay
    ) < hay_target:
        return Items.Hay

    if num_items(
        Items.Wood
    ) < wood_target:
        return Items.Wood

    return None


def run_sync(
    carrot_target,
    hay_target,
    wood_target
):
    while num_items(
        Items.Carrot
    ) < carrot_target:
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


def make_crop_worker(
    start_x,
    end_x,
    carrot_target,
    hay_target,
    wood_target
):
    def task():
        world_size = utils.size()

        while True:
            for x in range(
                start_x,
                end_x
            ):
                focus_item = current_focus(
                    carrot_target,
                    hay_target,
                    wood_target
                )

                if focus_item == None:
                    return True

                utils.move_to(
                    x,
                    0
                )

                for _ in range(
                    world_size
                ):
                    farm.farm_resource(
                        x,
                        x + 1,
                        focus_item
                    )

                    move(
                        North
                    )

    return task


def make_sun_worker(
    column,
    carrot_target,
    hay_target,
    wood_target
):
    def task():
        world_size = utils.size()

        while current_focus(
            carrot_target,
            hay_target,
            wood_target
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

    return task


def run_persistent(
    carrot_target,
    hay_target,
    wood_target
):
    world_size = utils.size()

    if max_drones() < world_size:
        quick_print(
            "PERSIST BENCH INVALID",
            "needs-full-megafarm",
            "world",
            world_size,
            "drones",
            max_drones()
        )

        return

    crop_columns = (
        world_size
        - 2
    )

    # Main remains the scheduler. With 31 available worker slots:
    #
    # - 29 crop workers cover 30 crop columns
    # - 2 workers continuously maintain one Sunflower column each
    #
    # The one two-column crop worker is intentionally not a barrier;
    # every other worker immediately starts its next column loop.
    crop_workers = (
        max_drones()
        - 3
    )

    chunks = workers.make_chunks(
        crop_columns,
        crop_workers
    )

    handles = []

    for start_x, end_x in chunks:
        drone = spawn_drone(
            make_crop_worker(
                start_x,
                end_x,
                carrot_target,
                hay_target,
                wood_target
            )
        )

        if drone == None:
            quick_print(
                "PERSIST BENCH INVALID",
                "crop-spawn-failed",
                start_x,
                end_x
            )

            return

        handles.append(
            drone
        )

    for column in range(
        world_size - 2,
        world_size
    ):
        drone = spawn_drone(
            make_sun_worker(
                column,
                carrot_target,
                hay_target,
                wood_target
            )
        )

        if drone == None:
            quick_print(
                "PERSIST BENCH INVALID",
                "sun-spawn-failed",
                column
            )

            return

        handles.append(
            drone
        )

    # No per-column or per-round barrier.
    # Every worker loops until the complete benchmark workload is done.
    for drone in handles:
        wait_for(
            drone
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

    carrot_target = (
        start_carrot
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

    quick_print(
        "PERSIST MODE START",
        MODE_NAMES[
            BENCH_MODE
        ],
        "world",
        BENCH_WORLD_SIZE,
        "drones",
        max_drones()
    )

    start_time = get_time()

    if BENCH_MODE == 0:
        run_sync(
            carrot_target,
            hay_target,
            wood_target
        )
    else:
        run_persistent(
            carrot_target,
            hay_target,
            wood_target
        )

    elapsed = (
        get_time()
        - start_time
    )

    quick_print(
        "PERSIST RESULT",
        MODE_NAMES[
            BENCH_MODE
        ],
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
