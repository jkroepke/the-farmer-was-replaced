def print_cost(label, entity):
    cost = get_cost(entity)

    quick_print(
        "LB RESOURCE COST",
        label,
        cost
    )


def print_unlock(label, unlock):
    quick_print(
        "LB RESOURCE UNLOCK",
        label,
        num_unlocked(unlock)
    )


def main():
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

    print_unlock(
        "Speed",
        Unlocks.Speed
    )
    print_unlock(
        "Watering",
        Unlocks.Watering
    )
    print_unlock(
        "Fertilizer",
        Unlocks.Fertilizer
    )
    print_unlock(
        "Sunflowers",
        Unlocks.Sunflowers
    )
    print_unlock(
        "Trees",
        Unlocks.Trees
    )
    print_unlock(
        "Carrots",
        Unlocks.Carrots
    )
    print_unlock(
        "Grass",
        Unlocks.Grass
    )
    print_unlock(
        "Megafarm",
        Unlocks.Megafarm
    )
    print_unlock(
        "Polyculture",
        Unlocks.Polyculture
    )

    print_cost(
        "Carrot",
        Entities.Carrot
    )
    print_cost(
        "Tree",
        Entities.Tree
    )
    print_cost(
        "Bush",
        Entities.Bush
    )
    print_cost(
        "Sunflower",
        Entities.Sunflower
    )

    quick_print(
        "LB RESOURCE PROBE DONE"
    )


if __name__ == "__main__":
    main()
