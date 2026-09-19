import farm
import workers


MODE_NAMES = [
    "legacy-l",
    "adaptive-production"
]


def run_phase(
    item,
    gain,
    mode
):
    start_items = num_items(
        item
    )
    start_power = num_items(
        Items.Power
    )
    start_time = get_time()

    target = (
        start_items
        + gain
    )

    while num_items(item) < target:
        if mode == 0:
            farm.run_legacy(
                item
            )
        else:
            farm.run(
                item
            )

    elapsed = (
        get_time()
        - start_time
    )

    gained = (
        num_items(item)
        - start_items
    )

    quick_print(
        "TRANSITION PHASE",
        MODE_NAMES[mode],
        "item",
        item,
        "elapsed",
        elapsed,
        "gain",
        gained,
        "rate",
        gained / elapsed,
        "start-power",
        start_power,
        "end-power",
        num_items(
            Items.Power
        )
    )


def main():
    set_world_size(
        BENCH_WORLD_SIZE
    )

    clear()
    workers.set_main_hat()
    farm.reset_state()

    if BENCH_MODE == 0:
        farm.rebuild_sunflowers()

    start_time = get_time()
    start_power = num_items(
        Items.Power
    )

    # Persistent workload:
    #
    # Carrot -> Hay -> Wood -> Carrot
    #
    # No clear() and no Power reset between phases.
    run_phase(
        Items.Carrot,
        BENCH_CARROT_GAIN,
        BENCH_MODE
    )

    run_phase(
        Items.Hay,
        BENCH_HAY_GAIN,
        BENCH_MODE
    )

    run_phase(
        Items.Wood,
        BENCH_WOOD_GAIN,
        BENCH_MODE
    )

    run_phase(
        Items.Carrot,
        BENCH_CARROT_GAIN,
        BENCH_MODE
    )

    elapsed = (
        get_time()
        - start_time
    )

    quick_print(
        "TRANSITION RESULT",
        MODE_NAMES[BENCH_MODE],
        "world",
        BENCH_WORLD_SIZE,
        "drones",
        max_drones(),
        "elapsed",
        elapsed,
        "start-power",
        start_power,
        "end-power",
        num_items(
            Items.Power
        )
    )


if __name__ == "__main__":
    main()
