from farm_config import REGULAR_WATER_THRESHOLD
from navigation import move_to
from parallel_farming import dispatch_indexed_jobs
from watering import water_if_dry


def random_color_hat():
    # Explicit allowlist: keep crop, trophy, gold, dinosaur, and novelty hats out.
    color_hats = []

    if num_unlocked(Hats.Brown_Hat):
        color_hats.append(Hats.Brown_Hat)

    if num_unlocked(Hats.Gray_Hat):
        color_hats.append(Hats.Gray_Hat)

    if num_unlocked(Hats.Green_Hat):
        color_hats.append(Hats.Green_Hat)

    if num_unlocked(Hats.Purple_Hat):
        color_hats.append(Hats.Purple_Hat)

    if len(color_hats) == 0:
        return Hats.Straw_Hat

    index = random() * len(color_hats) // 1
    return color_hats[index]


def tend_hay_tile() -> None:
    # Remove other crops and return soil to grassland before harvesting hay.
    entity = get_entity_type()

    if entity == Entities.Grass:
        if can_harvest():
            harvest()
        elif get_ground_type() == Grounds.Soil:
            # Grass on soil is not the target state; remove it before tilling.
            harvest()
    elif entity != None:
        # Harvest ready crops or remove unready crops while switching modes.
        harvest()

    if get_ground_type() == Grounds.Soil and get_entity_type() == None:
        till()

    water_if_dry(REGULAR_WATER_THRESHOLD)


def harvest_grass_row(row_y: int) -> None:
    # Harvest one complete row and leave the drone at its row start.
    size = get_world_size()
    move_to(0, row_y)
    change_hat(random_color_hat())

    for x in range(size):
        move_to(x, row_y)
        tend_hay_tile()


def farm_hay_cycle() -> bool:
    # Run one finite hay pass over every world row.
    size = get_world_size()
    rows = []

    for row_y in range(size):
        rows.append(row_y)

    dispatch_indexed_jobs(rows, harvest_grass_row)
    return True
