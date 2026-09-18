# ==================================================
# DROHNEN UND HÜTE
# ==================================================
#
# Es werden so viele Drohnen parallel verwendet,
# wie max_drones() erlaubt.
#
# Hüte dürfen sich wiederholen. Die vorhandenen
# Hüte werden einfach zyklisch auf die Worker verteilt.
# ==================================================

# Hats.Dinosaur_Hat gehört absichtlich NICHT in diese Liste.
# Davon existiert nur ein Exemplar und es wird ausschließlich
# vom Dinosaur-Spezialjob verwendet.
HATS = [
    Hats.Straw_Hat,
    Hats.Gray_Hat,
    Hats.Purple_Hat,
    Hats.Green_Hat,
    Hats.Brown_Hat,
    Hats.Carrot_Hat,
    Hats.Gold_Hat,
    Hats.Pumpkin_Hat,
    Hats.Sunflower_Hat,
    Hats.Traffic_Cone,
    Hats.Tree_Hat
]


def set_main_hat():
    change_hat(HATS[0])


def _hat_for(index):
    return HATS[index % len(HATS)]


def _with_hat(task, hat):
    def wrapped():
        change_hat(hat)
        return task()

    return wrapped


# ==================================================
# CHUNKS
# ==================================================

def make_chunks(total, parts):
    if parts < 1:
        parts = 1

    parts = min(parts, total)

    chunks = []
    base = total // parts
    extra = total % parts
    start = 0

    for index in range(parts):
        width = base

        if index < extra:
            width += 1

        end = start + width
        chunks.append((start, end))
        start = end

    return chunks


# ==================================================
# INTERNER WORKER-POOL
# ==================================================
#
# call_between_batches:
#   True  -> between_batches() nach jedem Batch
#   False -> kein Callback
#
# Funktionsobjekte werden nicht mit None verglichen.
# ==================================================

def _run(tasks, between_batches, call_between_batches):
    results = []

    task_index = 0
    task_count = len(tasks)

    # Keine künstliche Hut-Grenze:
    # max_drones() bestimmt die Parallelität.
    parallel_limit = max_drones()

    while task_index < task_count:
        active = []

        # Hauptdrohne verwendet Hut 0.
        change_hat(
            _hat_for(0)
        )

        worker_index = 1

        # Zusätzliche Drohnen bis zum echten Drohnenlimit.
        while (
            task_index < task_count
            and worker_index < parallel_limit
        ):
            wrapped = _with_hat(
                tasks[task_index],
                _hat_for(worker_index)
            )

            drone = spawn_drone(wrapped)

            if drone == None:
                break

            active.append(drone)

            task_index += 1
            worker_index += 1

        # Hauptdrohne übernimmt ebenfalls eine Aufgabe.
        if task_index < task_count:
            results.append(
                tasks[task_index]()
            )

            task_index += 1

        # Alle gespawnten Worker einsammeln.
        for drone in active:
            results.append(
                wait_for(drone)
            )

        if call_between_batches:
            between_batches()

    return results


# ==================================================
# OHNE CALLBACK
# ==================================================

def run(tasks):
    def no_op():
        pass

    return _run(
        tasks,
        no_op,
        False
    )


# ==================================================
# MIT CALLBACK ZWISCHEN BATCHES
# ==================================================

def run_with_between(tasks, between_batches):
    return _run(
        tasks,
        between_batches,
        True
    )
