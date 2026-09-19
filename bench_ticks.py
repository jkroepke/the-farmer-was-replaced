# Flekay-inspired interpreter/tick microbenchmarks.
#
# Source reference:
# external/flekay-the-farmer-was-replaced/
#
# These tests intentionally run directly in the current interpreter instead
# of through simulate(). They mutate only local collections, so no farm-state
# isolation is required. get_tick_count() is the metric.


MODE_NAMES = [
    "loop-add-baseline",
    "dict-int-key",
    "dict-tuple-key",
    "list-membership",
    "set-membership",
    "dict-membership",
    "queue-cursor",
    "queue-pop-zero",
    "list-append",
    "list-concat"
]


def report(
    name,
    iterations,
    size,
    start_ticks,
    checksum
):
    ticks = (
        get_tick_count()
        - start_ticks
    )

    quick_print(
        "TICK RESULT",
        name,
        "iterations",
        iterations,
        "size",
        size,
        "ticks",
        ticks,
        "ticks-per-op",
        ticks / iterations,
        "checksum",
        checksum
    )

    return ticks


def run_loop_add(
    iterations,
    size
):
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        checksum += 1

    return report(
        MODE_NAMES[0],
        iterations,
        size,
        start_ticks,
        checksum
    )


def run_dict_int(
    iterations,
    size
):
    data = {}
    key = size - 1
    data[key] = 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        checksum += data[key]

    return report(
        MODE_NAMES[1],
        iterations,
        size,
        start_ticks,
        checksum
    )


def run_dict_tuple(
    iterations,
    size
):
    data = {}
    key = (
        size - 1,
        size - 2
    )
    data[key] = 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        checksum += data[key]

    return report(
        MODE_NAMES[2],
        iterations,
        size,
        start_ticks,
        checksum
    )


def make_values(
    size
):
    values = []

    for value in range(
        size
    ):
        values.append(
            value
        )

    return values


def run_list_membership(
    iterations,
    size
):
    values = make_values(
        size
    )
    target = size - 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        if target in values:
            checksum += 1

    return report(
        MODE_NAMES[3],
        iterations,
        size,
        start_ticks,
        checksum
    )


def run_set_membership(
    iterations,
    size
):
    values = set()

    for value in range(
        size
    ):
        values.add(
            value
        )

    target = size - 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        if target in values:
            checksum += 1

    return report(
        MODE_NAMES[4],
        iterations,
        size,
        start_ticks,
        checksum
    )


def run_dict_membership(
    iterations,
    size
):
    values = {}

    for value in range(
        size
    ):
        values[value] = True

    target = size - 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        if target in values:
            checksum += 1

    return report(
        MODE_NAMES[5],
        iterations,
        size,
        start_ticks,
        checksum
    )


def make_queue(
    iterations
):
    queue = []

    for value in range(
        iterations
    ):
        queue.append(
            value
        )

    return queue


def run_queue_cursor(
    iterations,
    size
):
    queue = make_queue(
        iterations
    )
    index = 0
    checksum = 0
    start_ticks = get_tick_count()

    while index < iterations:
        checksum += queue[
            index
        ]
        index += 1

    return report(
        MODE_NAMES[6],
        iterations,
        size,
        start_ticks,
        checksum
    )


def run_queue_pop_zero(
    iterations,
    size
):
    queue = make_queue(
        iterations
    )
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        iterations
    ):
        checksum += queue.pop(
            0
        )

    return report(
        MODE_NAMES[7],
        iterations,
        size,
        start_ticks,
        checksum
    )


def run_list_append(
    iterations,
    size
):
    values = []
    start_ticks = get_tick_count()

    for value in range(
        iterations
    ):
        values.append(
            value
        )

    return report(
        MODE_NAMES[8],
        iterations,
        size,
        start_ticks,
        len(values)
    )


def run_list_concat(
    iterations,
    size
):
    values = []
    start_ticks = get_tick_count()

    for value in range(
        iterations
    ):
        values = values + [
            value
        ]

    return report(
        MODE_NAMES[9],
        iterations,
        size,
        start_ticks,
        len(values)
    )


def run_mode(
    mode,
    iterations,
    size
):
    if mode == 0:
        return run_loop_add(
            iterations,
            size
        )

    if mode == 1:
        return run_dict_int(
            iterations,
            size
        )

    if mode == 2:
        return run_dict_tuple(
            iterations,
            size
        )

    if mode == 3:
        return run_list_membership(
            iterations,
            size
        )

    if mode == 4:
        return run_set_membership(
            iterations,
            size
        )

    if mode == 5:
        return run_dict_membership(
            iterations,
            size
        )

    if mode == 6:
        return run_queue_cursor(
            iterations,
            size
        )

    if mode == 7:
        return run_queue_pop_zero(
            iterations,
            size
        )

    if mode == 8:
        return run_list_append(
            iterations,
            size
        )

    return run_list_concat(
        iterations,
        size
    )
