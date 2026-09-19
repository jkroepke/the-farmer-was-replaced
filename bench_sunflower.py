import sunflower_lb


TARGET_POWER = 100000


def main():
    mode = BENCH_MODE
    target = BENCH_TARGET_POWER

    if get_world_size() != 32:
        quick_print(
            "SUNFLOWER INVALID WORLD",
            get_world_size()
        )
        return

    if max_drones() < 32:
        quick_print(
            "SUNFLOWER INVALID DRONES",
            max_drones()
        )
        return

    start_power = num_items(
        Items.Power
    )
    start_ticks = get_tick_count()
    start_time = get_time()

    success = sunflower_lb.run(
        mode,
        target
    )

    end_time = get_time()
    end_ticks = get_tick_count()
    end_power = num_items(
        Items.Power
    )

    valid = (
        success
        and end_power >= target
    )

    quick_print(
        "SUNFLOWER RESULT",
        mode,
        sunflower_lb.MODE_NAMES[
            mode
        ],
        "success",
        success,
        "valid",
        valid,
        "power",
        end_power,
        "gain",
        end_power - start_power,
        "ticks",
        end_ticks - start_ticks,
        "elapsed",
        end_time - start_time
    )


main()
