PROBE_VERSION = "lbprobe-v2"


def print_cost(label, entity):
    quick_print(
        "LB RESOURCE COST",
        label,
        get_cost(entity)
    )


def main():
    quick_print(
        "LB RESOURCE PROBE VERSION",
        PROBE_VERSION
    )

    quick_print(
        "LB RESOURCE PROBE START",
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
            "LB RESOURCE ITEM",
            item,
            num_items(item)
        )

    for unlock in Unlocks:
        quick_print(
            "LB RESOURCE UNLOCK",
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
        "LB RESOURCE PROBE DONE"
    )


if __name__ == "__main__":
    main()
