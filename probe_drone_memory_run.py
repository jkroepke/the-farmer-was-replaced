import main


def run_probe():
    quick_print(
        "DRONE MEMORY PROBE START"
    )

    simulate(
        "probe_drone_memory",
        Unlocks,
        {},
        {},
        1,
        64
    )

    quick_print(
        "DRONE MEMORY PROBE DONE"
    )


if __name__ == "__main__":
    run_probe()

    quick_print(
        "DRONE MEMORY PROBE COMPLETE",
        "STARTING MAIN LOOP"
    )

    main.main()
