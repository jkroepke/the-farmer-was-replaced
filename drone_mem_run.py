# Run the drone memory semantics probe in an isolated simulation.


def run_probe():
    quick_print(
        "DRONE_MEMORY RUN START"
    )

    elapsed = simulate(
        "drone_mem_probe",
        Unlocks,
        {},
        {},
        1,
        64
    )

    quick_print(
        "DRONE_MEMORY RUN DONE",
        elapsed
    )


if __name__ == "__main__":
    run_probe()
