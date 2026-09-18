import utils


def substance_required():
    maze_level = num_unlocked(
        Unlocks.Mazes
    )

    if maze_level <= 0:
        return 0

    return (
        utils.size()
        * 2**(maze_level - 1)
    )


def can_start():
    substance = substance_required()

    if substance <= 0:
        return False

    if (
        num_items(Items.Weird_Substance)
        < substance
    ):
        return False

    if not utils.can_afford(Entities.Bush):
        return False

    return True


def create():
    if not can_start():
        return False

    substance = substance_required()

    clear()

    plant(Entities.Bush)

    use_item(
        Items.Weird_Substance,
        substance
    )

    return True


def solve():
    directions = [
        North,
        East,
        South,
        West
    ]

    direction = 0

    while (
        get_entity_type()
        != Entities.Treasure
    ):
        right = (
            direction + 1
        ) % 4

        if can_move(
            directions[right]
        ):
            direction = right

            move(
                directions[direction]
            )

        elif can_move(
            directions[direction]
        ):
            move(
                directions[direction]
            )

        else:
            direction = (
                direction - 1
            ) % 4

    harvest()


def run():
    if not create():
        return False

    solve()

    return True
