# Universal leaderboard start-state probe queue.
#
# Usage:
#
# 1. Run this file normally on the main farm.
# 2. The FIRST remaining leaderboard_run() line starts its leaderboard.
# 3. Inside the fresh leaderboard environment this same file prints the probe.
# 4. Back on the main farm, delete the completed leaderboard_run() line.
# 5. Run this file again to probe the next leaderboard.
#
# Keep the calls in this file intentionally. Do not create one launcher per LB.
#
# Why this does not recurse:
# A leaderboard starts with its own fresh timer. The payload executes immediately,
# while get_time() is still near zero. A normal/main farm session is expected to
# have been running longer than PROBE_START_WINDOW.
#
# If you run this file within the first few seconds of opening the normal farm,
# wait until the main-farm timer is above PROBE_START_WINDOW first.

PROBE_VERSION = "lbprobe-v4"
PROBE_START_WINDOW = 5


def print_cost(label, entity):
    quick_print(
        "LB PROBE COST",
        label,
        get_cost(entity)
    )


def probe():
    quick_print(
        "LB PROBE VERSION",
        PROBE_VERSION
    )

    quick_print(
        "LB PROBE START",
        "world",
        get_world_size(),
        "drones",
        max_drones(),
        "water-level",
        get_water(),
        "entity",
        get_entity_type(),
        "ground",
        get_ground_type()
    )

    for item in Items:
        quick_print(
            "LB PROBE ITEM",
            item,
            num_items(item)
        )

    for unlock in Unlocks:
        quick_print(
            "LB PROBE UNLOCK",
            unlock,
            num_unlocked(unlock)
        )

    print_cost(
        "Grass",
        Entities.Grass
    )
    print_cost(
        "Bush",
        Entities.Bush
    )
    print_cost(
        "Tree",
        Entities.Tree
    )
    print_cost(
        "Carrot",
        Entities.Carrot
    )
    print_cost(
        "Sunflower",
        Entities.Sunflower
    )
    print_cost(
        "Pumpkin",
        Entities.Pumpkin
    )
    print_cost(
        "Cactus",
        Entities.Cactus
    )

    quick_print(
        "LB PROBE DONE"
    )


def launch_next():
    # Queue semantics:
    # leaderboard_run() takes over execution and does not return here.
    # Delete the completed first line before running lb_probe.py again.

    leaderboard_run(Leaderboards.Fastest_Reset, "lb_probe", 256)
    leaderboard_run(Leaderboards.Maze, "lb_probe", 256)
    leaderboard_run(Leaderboards.Dinosaur, "lb_probe", 256)

    leaderboard_run(Leaderboards.Cactus, "lb_probe", 256)
    leaderboard_run(Leaderboards.Sunflowers, "lb_probe", 256)
    leaderboard_run(Leaderboards.Pumpkins, "lb_probe", 256)
    leaderboard_run(Leaderboards.Wood, "lb_probe", 256)
    leaderboard_run(Leaderboards.Carrots, "lb_probe", 256)
    leaderboard_run(Leaderboards.Hay, "lb_probe", 256)

    leaderboard_run(Leaderboards.Maze_Single, "lb_probe", 256)
    leaderboard_run(Leaderboards.Cactus_Single, "lb_probe", 256)
    leaderboard_run(Leaderboards.Sunflowers_Single, "lb_probe", 256)
    leaderboard_run(Leaderboards.Pumpkins_Single, "lb_probe", 256)
    leaderboard_run(Leaderboards.Wood_Single, "lb_probe", 256)
    leaderboard_run(Leaderboards.Carrots_Single, "lb_probe", 256)
    leaderboard_run(Leaderboards.Hay_Single, "lb_probe", 256)


def main():
    if get_time() < PROBE_START_WINDOW:
        probe()
        return

    launch_next()


main()
