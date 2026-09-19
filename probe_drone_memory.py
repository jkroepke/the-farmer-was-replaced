# Reproduce the historical nql1314 wait_for(shared_source) trick.
#
# Historical source:
# nql1314/The-Farmer-Was-Replaced-AI-Code
# archived/ref_test.py
# revision 688325db004607563e59535a15ce94fad092ff9f
#
# Expected current behavior after the shared-memory fixes:
# every wait_for(source) caller receives isolated data and mutations made
# by worker drones do not appear in a later parent wait_for(source) result.


def create_source():
    return []


source = spawn_drone(
    create_source
)


def mutate_source(marker):
    data = wait_for(
        source
    )

    data.append(
        marker
    )

    return data


def main():
    initial = wait_for(
        source
    )

    quick_print(
        "DRONE MEMORY PROBE",
        "initial",
        initial
    )

    marker = 1

    while marker <= 3:
        drone = spawn_drone(
            mutate_source,
            marker
        )

        if drone == None:
            quick_print(
                "DRONE MEMORY PROBE",
                "spawn-failed",
                marker
            )

            return

        worker_result = wait_for(
            drone
        )

        source_result = wait_for(
            source
        )

        quick_print(
            "DRONE MEMORY STEP",
            marker,
            "worker",
            worker_result,
            "source",
            source_result,
            "initial-view",
            initial
        )

        marker += 1

    final = wait_for(
        source
    )

    if (
        len(final) == 0
        and len(initial) == 0
    ):
        quick_print(
            "DRONE MEMORY RESULT",
            "isolated"
        )
    else:
        quick_print(
            "DRONE MEMORY RESULT",
            "shared",
            final,
            initial
        )


if __name__ == "__main__":
    main()
