# Universal leaderboard start-state probe.
#
# This file is the PAYLOAD for every leaderboard probe.
# It intentionally does not call leaderboard_run() itself.
#
# Run exactly one of these from the game/launcher context:
#
# leaderboard_run(Leaderboards.Fastest_Reset, "lb_probe", 256)
# leaderboard_run(Leaderboards.Maze, "lb_probe", 256)
# leaderboard_run(Leaderboards.Dinosaur, "lb_probe", 256)
# leaderboard_run(Leaderboards.Cactus, "lb_probe", 256)
# leaderboard_run(Leaderboards.Sunflowers, "lb_probe", 256)
# leaderboard_run(Leaderboards.Pumpkins, "lb_probe", 256)
# leaderboard_run(Leaderboards.Wood, "lb_probe", 256)
# leaderboard_run(Leaderboards.Carrots, "lb_probe", 256)
# leaderboard_run(Leaderboards.Hay, "lb_probe", 256)
# leaderboard_run(Leaderboards.Maze_Single, "lb_probe", 256)
# leaderboard_run(Leaderboards.Cactus_Single, "lb_probe", 256)
# leaderboard_run(Leaderboards.Sunflowers_Single, "lb_probe", 256)
# leaderboard_run(Leaderboards.Pumpkins_Single, "lb_probe", 256)
# leaderboard_run(Leaderboards.Wood_Single, "lb_probe", 256)
# leaderboard_run(Leaderboards.Carrots_Single, "lb_probe", 256)
# leaderboard_run(Leaderboards.Hay_Single, "lb_probe", 256)
#
# leaderboard_run() replaces the current execution with the leaderboard
# environment, so one invocation probes exactly one leaderboard.

PROBE_VERSION = "lbprobe-v3"


def print_cost(label, entity):
    quick_print(
        "LB PROBE COST",
        label,
        get_cost(entity)
    )


def main():
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


main()
