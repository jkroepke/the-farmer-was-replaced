import bench_persist
import farm
import utils
import workers


MODE_NAMES = [
    "sync-selected",
    "current-one-max-stride",
    "current-one-max-chunks",
    "current-one-max-pairs",
    "current-two-sun-stride",
    "current-two-sun-chunks",
    "current-two-sun-pairs",
    "poly-one-max-stride",
    "poly-one-max-chunks",
    "poly-one-max-pairs",
    "poly-two-sun-stride",
    "poly-two-sun-chunks",
    "poly-two-sun-pairs"
]


def current_focus(carrot_mid, hay_target, wood_target, carrot_final):
    return bench_persist.current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )


def focus_entity(item):
    if item == Items.Hay:
        return Entities.Grass
    if item == Items.Wood:
        return Entities.Tree
    return Entities.Carrot


def mode_sun_layout(mode):
    if mode >= 10 or mode >= 4 and mode <= 6:
        return 2
    if mode >= 1:
        return 1
    return 0


def mode_arch(mode):
    if mode >= 10:
        return mode - 10
    if mode >= 7:
        return mode - 7
    if mode >= 4:
        return mode - 4
    return mode - 1


def crop_columns(sun_layout, world_size):
    return world_size - sun_layout


def ensure_bush():
    entity = get_entity_type()

    if entity == Entities.Bush:
        return True

    if entity != None:
        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    return plant(Entities.Bush)


def companion_matches(crop_columns_count):
    companion = get_companion()

    if companion == None:
        return False

    companion_entity, position = companion
    target_x, target_y = position

    return (
        companion_entity == Entities.Bush
        and target_x < crop_columns_count
        and (target_x + target_y) % 2 == 0
    )


def reroll_focus(item, crop_columns_count):
    wanted = focus_entity(item)
    entity = get_entity_type()

    if entity != wanted:
        if entity != None:
            harvest()

        if get_ground_type() != Grounds.Soil:
            till()

        if not utils.can_afford(wanted):
            return False

        if not plant(wanted):
            return False

        utils.water()

    while not companion_matches(crop_columns_count):
        harvest()

        if not utils.can_afford(wanted):
            return False

        if not plant(wanted):
            return False

        utils.water()

    return True


def service_focus(item, crop_columns_count):
    if not reroll_focus(item, crop_columns_count):
        return

    if not can_harvest():
        return

    harvest()

    wanted = focus_entity(item)

    if not utils.can_afford(wanted):
        return

    if not plant(wanted):
        return

    utils.water()
    reroll_focus(item, crop_columns_count)


def prep_column(x):
    world_size = utils.size()

    utils.move_to(x, 0)

    for y in range(world_size):
        if get_ground_type() != Grounds.Soil:
            till()

        if (x + y) % 2 == 0:
            ensure_bush()

        move(North)


def prep_worker(worker_index, worker_count, crop_columns_count):
    x = worker_index

    while x < crop_columns_count:
        prep_column(x)
        x += worker_count

    return True


def prepare_poly(crop_columns_count):
    worker_count = min(
        max_drones(),
        crop_columns_count
    )
    handles = []

    for worker_index in range(1, worker_count):
        drone = spawn_drone(
            prep_worker,
            worker_index,
            worker_count,
            crop_columns_count
        )

        if drone == None:
            return False

        handles.append(drone)

    prep_worker(
        0,
        worker_count,
        crop_columns_count
    )

    for drone in handles:
        wait_for(drone)

    return True


def process_column(
    x,
    crop_columns_count,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    item = current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )

    if item == None:
        return False

    world_size = utils.size()
    utils.move_to(x, 0)

    for y in range(world_size):
        if (x + y) % 2 == 0:
            ensure_bush()
        else:
            service_focus(
                item,
                crop_columns_count
            )

        move(North)

    return True


def poly_worker(
    architecture,
    worker_index,
    worker_count,
    crop_columns_count,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    chunks = workers.make_chunks(
        crop_columns_count,
        worker_count
    )

    while current_focus(
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ) != None:
        if architecture == 0:
            x = worker_index

            while x < crop_columns_count:
                if not process_column(
                    x,
                    crop_columns_count,
                    carrot_mid,
                    hay_target,
                    wood_target,
                    carrot_final
                ):
                    return True

                x += worker_count

        elif architecture == 1:
            start_x, end_x = chunks[
                worker_index
            ]

            for x in range(start_x, end_x):
                if not process_column(
                    x,
                    crop_columns_count,
                    carrot_mid,
                    hay_target,
                    wood_target,
                    carrot_final
                ):
                    return True

        else:
            pair = worker_index

            while pair * 2 < crop_columns_count:
                x = pair * 2

                if not process_column(
                    x,
                    crop_columns_count,
                    carrot_mid,
                    hay_target,
                    wood_target,
                    carrot_final
                ):
                    return True

                if x + 1 < crop_columns_count:
                    if not process_column(
                        x + 1,
                        crop_columns_count,
                        carrot_mid,
                        hay_target,
                        wood_target,
                        carrot_final
                    ):
                        return True

                pair += worker_count

    return True


def spawn_sun_workers(
    handles,
    sun_layout,
    world_size,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    if sun_layout == 1:
        drone = spawn_drone(
            bench_persist.sun_max_worker,
            world_size - 1,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if drone == None:
            return False

        handles.append(drone)
        return True

    for column in range(world_size - 2, world_size):
        drone = spawn_drone(
            bench_persist.sun_dumb_worker,
            column,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if drone == None:
            return False

        handles.append(drone)

    return True


def run_poly(
    sun_layout,
    architecture,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    world_size = utils.size()
    crop_columns_count = crop_columns(
        sun_layout,
        world_size
    )

    prep_start_time = get_time()
    prep_start_ticks = get_tick_count()

    if not prepare_poly(crop_columns_count):
        return False

    quick_print(
        "FARMX POLY PREP",
        "elapsed",
        get_time() - prep_start_time,
        "ticks",
        get_tick_count() - prep_start_ticks
    )

    crop_worker_count = min(
        crop_columns_count,
        max_drones() - sun_layout
    )

    if architecture == 2:
        crop_worker_count = min(
            crop_worker_count,
            (crop_columns_count + 1) // 2
        )

    if crop_worker_count < 1:
        return False

    handles = []
    launch_start_time = get_time()
    launch_start_ticks = get_tick_count()

    for worker_index in range(1, crop_worker_count):
        drone = spawn_drone(
            poly_worker,
            architecture,
            worker_index,
            crop_worker_count,
            crop_columns_count,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

        if drone == None:
            return False

        handles.append(drone)

    if not spawn_sun_workers(
        handles,
        sun_layout,
        world_size,
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    ):
        return False

    quick_print(
        "FARMX POLY LAUNCH",
        "elapsed",
        get_time() - launch_start_time,
        "ticks",
        get_tick_count() - launch_start_ticks,
        "crop-workers",
        crop_worker_count,
        "sun-workers",
        sun_layout
    )

    poly_worker(
        architecture,
        0,
        crop_worker_count,
        crop_columns_count,
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )

    for drone in handles:
        wait_for(drone)

    return True


def run_mode(
    mode,
    carrot_mid,
    hay_target,
    wood_target,
    carrot_final
):
    if mode == 0:
        bench_persist.run_sync(
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )
        return True

    sun_layout = mode_sun_layout(mode)
    architecture = mode_arch(mode)

    if mode < 7:
        if sun_layout == 1:
            layout = 4
        else:
            layout = 3

        return bench_persist.run_persistent(
            layout,
            architecture,
            carrot_mid,
            hay_target,
            wood_target,
            carrot_final
        )

    return run_poly(
        sun_layout,
        architecture,
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )


def main():
    set_world_size(BENCH_WORLD_SIZE)

    cold_start_time = get_time()
    cold_start_ticks = get_tick_count()

    clear()
    workers.set_main_hat()
    farm.reset_state()

    start_carrot = num_items(Items.Carrot)
    start_hay = num_items(Items.Hay)
    start_wood = num_items(Items.Wood)
    start_power = num_items(Items.Power)

    carrot_mid = start_carrot + BENCH_CARROT_GAIN
    carrot_final = carrot_mid + BENCH_CARROT_GAIN
    hay_target = start_hay + BENCH_HAY_GAIN
    wood_target = start_wood + BENCH_WOOD_GAIN

    quick_print(
        "FARMX MODE START",
        MODE_NAMES[BENCH_MODE],
        "horizon",
        BENCH_HORIZON,
        "world",
        BENCH_WORLD_SIZE,
        "drones",
        max_drones()
    )

    success = run_mode(
        BENCH_MODE,
        carrot_mid,
        hay_target,
        wood_target,
        carrot_final
    )

    elapsed = get_time() - cold_start_time
    ticks = get_tick_count() - cold_start_ticks

    carrot_gain = num_items(Items.Carrot) - start_carrot
    hay_gain = num_items(Items.Hay) - start_hay
    wood_gain = num_items(Items.Wood) - start_wood
    power_delta = num_items(Items.Power) - start_power

    passed = (
        success
        and carrot_gain >= BENCH_CARROT_GAIN * 2
        and hay_gain >= BENCH_HAY_GAIN
        and wood_gain >= BENCH_WOOD_GAIN
    )

    if passed:
        result = "PASS"
    else:
        result = "FAIL"

    quick_print(
        "FARMX RESULT",
        MODE_NAMES[BENCH_MODE],
        "horizon",
        BENCH_HORIZON,
        "elapsed",
        elapsed,
        "ticks",
        ticks,
        "carrot-gain",
        carrot_gain,
        "hay-gain",
        hay_gain,
        "wood-gain",
        wood_gain,
        "power-delta",
        power_delta,
        result
    )


if __name__ == "__main__":
    main()
