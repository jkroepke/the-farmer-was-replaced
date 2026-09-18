import config
import utils
import workers


def can_start():
    world_size = utils.size()

    fields = (
        world_size
        * world_size
    )

    required_fields = (
        fields
        * config.PUMPKIN_COST_FACTOR
    )

    return utils.can_afford(
        Entities.Pumpkin,
        required_fields
    )


def farm_current():
    utils.water()

    if get_ground_type() != Grounds.Soil:
        till()

    entity = get_entity_type()

    if (
        entity == None
        or entity == Entities.Dead_Pumpkin
    ):
        if not utils.can_afford(
            Entities.Pumpkin
        ):
            return False, True

        plant(
            Entities.Pumpkin
        )

        return False, False

    if entity == Entities.Pumpkin:
        if can_harvest():
            return True, False

        return False, False

    return False, False


def _make_column_task(x):
    def task():
        world_size = utils.size()

        all_ready = True
        missing_resources = False

        utils.move_to(
            x,
            0
        )

        for y in range(world_size):
            ready, missing = farm_current()

            if missing:
                missing_resources = True

            if not ready:
                all_ready = False

            if y < world_size - 1:
                move(North)

        utils.move_to(
            0,
            0
        )

        return (
            all_ready,
            missing_resources
        )

    return task


def scan():
    world_size = utils.size()

    tasks = []

    for x in range(world_size):
        tasks.append(
            _make_column_task(x)
        )

    results = workers.run(tasks)

    all_ready = True

    for result in results:
        ready, missing_resources = result

        if missing_resources:
            return False, True

        if not ready:
            all_ready = False

    return all_ready, False


def run():
    if not can_start():
        return False

    clear()

    while True:
        ready, missing_resources = scan()

        if missing_resources:
            return False

        if ready:
            utils.move_to(
                0,
                0
            )

            if (
                get_entity_type()
                == Entities.Pumpkin
            ):
                if can_harvest():
                    harvest()

                    return True
