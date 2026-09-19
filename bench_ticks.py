# Flekay-inspired interpreter/tick microbenchmarks.
#
# Source reference:
# external/flekay-the-farmer-was-replaced/
#
# The purpose is to re-measure hot-path claims on the current game build,
# not to assume the January 2026 numbers are still exact.


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
        BENCH_ITERATIONS,
        "size",
        BENCH_COLLECTION_SIZE,
        "ticks",
        ticks,
        "ticks-per-op",
        ticks / BENCH_ITERATIONS,
        "checksum",
        checksum
    )


def run_loop_add():
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        checksum += 1

    report(
        MODE_NAMES[0],
        start_ticks,
        checksum
    )


def run_dict_int():
    data = {}
    key = BENCH_COLLECTION_SIZE - 1
    data[key] = 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        checksum += data[key]

    report(
        MODE_NAMES[1],
        start_ticks,
        checksum
    )


def run_dict_tuple():
    data = {}
    key = (
        BENCH_COLLECTION_SIZE - 1,
        BENCH_COLLECTION_SIZE - 2
    )
    data[key] = 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        checksum += data[key]

    report(
        MODE_NAMES[2],
        start_ticks,
        checksum
    )


def make_values():
    values = []

    for value in range(
        BENCH_COLLECTION_SIZE
    ):
        values.append(
            value
        )

    return values


def run_list_membership():
    values = make_values()
    target = BENCH_COLLECTION_SIZE - 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        if target in values:
            checksum += 1

    report(
        MODE_NAMES[3],
        start_ticks,
        checksum
    )


def run_set_membership():
    values = set()

    for value in range(
        BENCH_COLLECTION_SIZE
    ):
        values.add(
            value
        )

    target = BENCH_COLLECTION_SIZE - 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        if target in values:
            checksum += 1

    report(
        MODE_NAMES[4],
        start_ticks,
        checksum
    )


def run_dict_membership():
    values = {}

    for value in range(
        BENCH_COLLECTION_SIZE
    ):
        values[value] = True

    target = BENCH_COLLECTION_SIZE - 1
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        if target in values:
            checksum += 1

    report(
        MODE_NAMES[5],
        start_ticks,
        checksum
    )


def make_queue():
    queue = []

    for value in range(
        BENCH_ITERATIONS
    ):
        queue.append(
            value
        )

    return queue


def run_queue_cursor():
    queue = make_queue()
    index = 0
    checksum = 0
    start_ticks = get_tick_count()

    while index < BENCH_ITERATIONS:
        checksum += queue[
            index
        ]
        index += 1

    report(
        MODE_NAMES[6],
        start_ticks,
        checksum
    )


def run_queue_pop_zero():
    queue = make_queue()
    checksum = 0
    start_ticks = get_tick_count()

    for _ in range(
        BENCH_ITERATIONS
    ):
        checksum += queue.pop(
            0
        )

    report(
        MODE_NAMES[7],
        start_ticks,
        checksum
    )


def run_list_append():
    values = []
    start_ticks = get_tick_count()

    for value in range(
        BENCH_ITERATIONS
    ):
        values.append(
            value
        )

    report(
        MODE_NAMES[8],
        start_ticks,
        len(values)
    )


def run_list_concat():
    values = []
    start_ticks = get_tick_count()

    for value in range(
        BENCH_ITERATIONS
    ):
        values = values + [
            value
        ]

    report(
        MODE_NAMES[9],
        start_ticks,
        len(values)
    )


def main():
    if BENCH_MODE == 0:
        run_loop_add()
    elif BENCH_MODE == 1:
        run_dict_int()
    elif BENCH_MODE == 2:
        run_dict_tuple()
    elif BENCH_MODE == 3:
        run_list_membership()
    elif BENCH_MODE == 4:
        run_set_membership()
    elif BENCH_MODE == 5:
        run_dict_membership()
    elif BENCH_MODE == 6:
        run_queue_cursor()
    elif BENCH_MODE == 7:
        run_queue_pop_zero()
    elif BENCH_MODE == 8:
        run_list_append()
    else:
        run_list_concat()


if __name__ == "__main__":
    main()
