# ==================================================
# DROHNEN
# ==================================================
#
# Es werden so viele Drohnen parallel verwendet,
# wie max_drones() erlaubt.
#
# Generische Worker wechseln absichtlich NICHT den Hut.
#
# change_hat() kostet 200 Ticks. Normale Hüte haben für diese
# Farm-Worker keinen dokumentierten Gameplay-Nutzen, daher wäre
# jeder Hutwechsel nur Spawn-Overhead.
#
# set_main_hat() bleibt bestehen, weil der Dinosaur-Job damit den
# Dinosaur_Hat explizit ablegt und dadurch den Schwanz erntet.
# ==================================================


def set_main_hat():
    change_hat(
        Hats.Straw_Hat
    )


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

        worker_index = 1

        # Zusätzliche Drohnen bis zum echten Drohnenlimit.
        # Kein change_hat(): der Worker startet direkt mit seiner Aufgabe.
        while (
            task_index < task_count
            and worker_index < parallel_limit
        ):
            drone = spawn_drone(
                tasks[task_index]
            )

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
