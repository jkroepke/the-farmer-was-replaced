from Helpers import goto
from replant import replantPumpkin
from cactus import doCactus
from maze import substanceAbuse, startMaze

unlock_list = [
    Unlocks.Fertilizer,
    Unlocks.Pumpkins,
    Unlocks.Speed,
    Unlocks.Grass,
    Unlocks.Expand,
    Unlocks.Plant,
    Unlocks.Leaderboard,
    Unlocks.Carrots,
    Unlocks.Trees,
    Unlocks.Watering,
    Unlocks.Sunflowers,
    Unlocks.Cactus,
    Unlocks.Mazes,
    Unlocks.Megafarm,
]
unlock_history = []
easy_farms = [Items.Carrot, Items.Hay, Items.Wood]


def farm_needed(thing, count):
    cost = get_cost(thing)

    for it_c in cost:
        tt_c = cost[it_c]
        total_cost = tt_c * count

        if num_items(it_c) < tt_c or total_cost > num_items(it_c) - total_cost:
            farm_item(it_c, tt_c * count)


def calculate_total_cost(thing, count):
    cost = get_cost(thing)
    tt_cost = 0

    for it_c in cost:
        tt_c = cost[it_c]
        tt_cost += tt_c * count

    return tt_cost


def generic_farm(thing, count, force=False):
    clear()
    goto(0, 0)
    world_size = get_world_size()
    farmed = False
    while num_items(thing) < count:
        for x in range(world_size):
            for y in range(world_size):
                if can_harvest():
                    harvest()

                    if num_items(Items.Cactus) >= 2000 and not force:
                        break

                    if thing == Items.Wood:
                        if (
                            get_entity_type() != Entities.Bush
                            or get_entity_type() != Entities.Tree
                        ):
                            curr_x = get_pos_x()
                            curr_y = get_pos_y()

                            can_plant_tree = curr_x % 2 == curr_y % 2

                            if (
                                not check_if_unlocked(Entities.Tree)
                                or not can_plant_tree
                            ):
                                plant(Entities.Bush)
                            else:
                                plant(Entities.Tree)

                    if thing == Items.Carrot:
                        if not farmed:
                            farm_needed(Entities.Carrot, count)
                        farmed = True

                        if get_ground_type() != Grounds.Soil:
                            till()

                        if get_entity_type() != Entities.Carrot:
                            plant(Entities.Carrot)

                    if thing == Items.Pumpkin:
                        if not farmed:
                            farm_needed(Entities.Pumpkin, count)
                        farmed = True

                        clear()

                        while num_items(thing) < count:
                            replantPumpkin(world_size, Entities.Pumpkin, 1)

                    if thing == Items.Power:
                        if not farmed:
                            farm_needed(Entities.Sunflower, count)
                        farmed = True
                        clear()

                        if get_ground_type() != Grounds.Soil:
                            till()
                            plant(Entities.Sunflower)
                        elif get_entity_type() != Entities.Sunflower:
                            plant(Entities.Sunflower)
                        else:
                            harvest()
                            plant(Entities.Sunflower)

                    if thing == Items.Cactus:
                        if not farmed:
                            farm_needed(Entities.Cactus, count)
                        farmed = True

                        clear()

                        while num_items(thing) < count:
                            doCactus(world_size)

                    if thing == Items.Bone:
                        goto(0, 0)
                        while num_items(thing) < count:
                            change_hat(Hats.Dinosaur_Hat)
                            finished = False
                            while not finished:
                                while get_pos_y() < world_size - 1:
                                    harvest()
                                    if not move(North):
                                        finished = True
                                        break
                                while get_pos_y() > 0 and not finished:
                                    while get_pos_x() < world_size - 1:
                                        harvest()
                                        if not move(East):
                                            finished = True
                                            break
                                    harvest()
                                    move(South)
                                    while get_pos_x() > 1:
                                        harvest()
                                        if not move(West):
                                            finished = True
                                            break
                                    if not get_pos_y() == 0:
                                        harvest()
                                        if not move(South):
                                            finished = True
                                            break
                                move(West)
                            change_hat(Hats.Straw_Hat)

                    if thing == Items.Gold:
                        while num_items(thing) < count:
                            startMaze()

                    if thing == Items.Weird_Substance:
                        while num_items(thing) < count:
                            substanceAbuse(count)

                move(North)
            move(East)


def farm_item(item, count, force=False):
    quick_print("Farming: ", count, " of ", item)
    while num_items(item) < count:
        if num_items(Items.Cactus) >= 2000 and not force:
            break
        generic_farm(item, count, force)


def check_if_unlocked(thing):
    second_thing = thing
    if thing == Items.Carrot:
        second_thing = Unlocks.Carrots
    elif thing == Items.Pumpkin:
        second_thing = Unlocks.Pumpkins
    elif thing == Items.Bone:
        second_thing = Unlocks.Dinosaurs
    elif thing == Items.Cactus:
        second_thing = Unlocks.Cactus
    elif thing == Items.Gold:
        second_thing = Unlocks.Mazes
    return num_unlocked(thing) > 0 and num_unlocked(second_thing) > 0


def cheapest_upgrade():
    cheapest_upgrade = None
    lowest_cost = 999999999
    cheapest_upgrade_full = None

    for upg in unlock_list:
        upgrade_cost = get_cost(upg)

        can_pursue = True
        total_cost = 0

        if num_items(Items.Cactus) >= 2000:
            break

        for item in upgrade_cost:
            if not check_if_unlocked(item):
                can_pursue = False
                total_cost += 1000000
                break

            total_cost += upgrade_cost[item]

            easy_items = [Items.Hay, Items.Wood, Items.Bone]
            if item not in easy_items:
                if item == Items.Cactus:
                    total_cost += calculate_total_cost(
                        Entities.Cactus, upgrade_cost[item]
                    )
                elif item == Items.Pumpkin:
                    total_cost += calculate_total_cost(
                        Entities.Pumpkin, upgrade_cost[item]
                    )
                elif item == Items.Carrot:
                    total_cost += calculate_total_cost(
                        Entities.Carrot, upgrade_cost[item]
                    )

        if can_pursue and total_cost < lowest_cost:
            lowest_cost = total_cost
            cheapest_upgrade = upg
            cheapest_upgrade_full = upgrade_cost

    return cheapest_upgrade


def check_upgrades(ung, force=False):
    upgrade_cost = get_cost(ung)
    upgrade_unlock = False

    for item in upgrade_cost:
        if num_items(Items.Cactus) >= 2000 and not force:
            break

        quick_print("Upgrade: ", ung, " Item: ", item, " Count: ", upgrade_cost[item])
        if num_items(item) <= upgrade_cost[item]:
            farm_item(item, upgrade_cost[item])

            upgrade_unlock = True
        else:
            upgrade_unlock = True
    if upgrade_unlock:
        unlock(ung)
        unlock_history.append(ung)

        if len(get_cost(ung)) == 0:
            unlock_list.remove(ung)
            quick_print("Removed", ung, "from upgrade list")

        current_level = num_unlocked(ung)
        quick_print(ung, "level", current_level)


while num_unlocked(Unlocks.Leaderboard) == 0:
    if num_items(Items.Cactus) > 2000:
        quick_print("Endgame")
        unlock(Unlocks.Dinosaurs)
        quick_print("Dino")
        check_upgrades(Unlocks.Hats)
        quick_print("Hats")

        generic_farm(Items.Cactus, 30000, True)

        generic_farm(Items.Bone, 2000000, True)

        quick_print("Bone")
        while num_items(Items.Gold) < 1000000:
            startMaze()
        quick_print("Gold")
        check_upgrades(Unlocks.Mazes, True)
        check_upgrades(Unlocks.Mazes, True)
        unlock(Unlocks.Leaderboard)
        quick_print("Goodnight")
        break
    else:
        current_goal = cheapest_upgrade()

        check_upgrades(current_goal)
