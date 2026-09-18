import utils
import workers


def can_start():
    world_size = utils.size()

    fields = (
        world_size
        * world_size
    )

    return utils.can_afford(
        Entities.Cactus,
        fields
    )


# ==================================================
# PFLANZEN
# ==================================================

def _make_plant_column_task(x):
    def task():
        world_size = utils.size()

        utils.move_to(
            x,
            0
        )

        for y in range(world_size):
            utils.water()

            if get_ground_type() != Grounds.Soil:
                till()

            if not utils.can_afford(
                Entities.Cactus
            ):
                utils.move_to(
                    0,
                    0
                )

                return False

            if get_entity_type() != Entities.Cactus:
                plant(
                    Entities.Cactus
                )

            if y < world_size - 1:
                move(North)

        utils.move_to(
            0,
            0
        )

        return True

    return task


def plant_all():
    clear()

    tasks = []

    for x in range(utils.size()):
        tasks.append(
            _make_plant_column_task(x)
        )

    results = workers.run(tasks)

    for result in results:
        if not result:
            return False

    return True


# ==================================================
# REIFE PRÜFEN
# ==================================================

def _make_ready_column_task(x):
    def task():
        world_size = utils.size()

        ready = True

        utils.move_to(
            x,
            0
        )

        for y in range(world_size):
            utils.water()

            if (
                get_entity_type()
                != Entities.Cactus
            ):
                ready = False

            elif not can_harvest():
                ready = False

            if y < world_size - 1:
                move(North)

        utils.move_to(
            0,
            0
        )

        return ready

    return task


def all_ready():
    tasks = []

    for x in range(utils.size()):
        tasks.append(
            _make_ready_column_task(x)
        )

    results = workers.run(tasks)

    for result in results:
        if not result:
            return False

    return True


# ==================================================
# ZEILEN SORTIEREN
# ==================================================

def _make_sort_row_task(y):
    def task():
        world_size = utils.size()

        for pass_index in range(
            world_size - 1
        ):
            utils.move_to(
                0,
                y
            )

            for x in range(
                world_size - 1 - pass_index
            ):
                current = measure()
                east = measure(East)

                if current > east:
                    swap(East)

                move(East)

        utils.move_to(
            0,
            0
        )

        return True

    return task


def sort_rows():
    tasks = []

    for y in range(utils.size()):
        tasks.append(
            _make_sort_row_task(y)
        )

    workers.run(tasks)


# ==================================================
# SPALTEN SORTIEREN
# ==================================================

def _make_sort_column_task(x):
    def task():
        world_size = utils.size()

        for pass_index in range(
            world_size - 1
        ):
            utils.move_to(
                x,
                0
            )

            for y in range(
                world_size - 1 - pass_index
            ):
                current = measure()
                north = measure(North)

                if current > north:
                    swap(North)

                move(North)

        utils.move_to(
            0,
            0
        )

        return True

    return task


def sort_columns():
    tasks = []

    for x in range(utils.size()):
        tasks.append(
            _make_sort_column_task(x)
        )

    workers.run(tasks)


# ==================================================
# KOMPLETTER CACTUS-JOB
# ==================================================

def run():
    if not can_start():
        return False

    if not plant_all():
        return False

    while not all_ready():
        pass

    sort_rows()
    sort_columns()

    utils.move_to(
        0,
        0
    )

    if can_harvest():
        harvest()

        return True

    return False
