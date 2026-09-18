import config
import utils
import workers


# ==================================================
# DÜNGER / WEIRD SUBSTANCE
# ==================================================

def weird_substance_target():
    maze_level = num_unlocked(Unlocks.Mazes)

    if maze_level <= 0:
        return 0

    one_maze = (
        utils.size()
        * 2**(maze_level - 1)
    )

    return (
        one_maze
        * config.MAZE_STOCKPILE
    )


def fertilize():
    if not config.ENABLE_FERTILIZER:
        return

    if num_items(Items.Fertilizer) <= config.FERTILIZER_RESERVE:
        return

    if (
        num_items(Items.Weird_Substance)
        >= weird_substance_target()
    ):
        return

    if get_entity_type() == None:
        return

    if can_harvest():
        return

    use_item(Items.Fertilizer)


# ==================================================
# FARM-LAYOUT
# ==================================================
#
# Sonnenblumen:
#
#   permanentes L am linken und oberen Rand
#
#   x = 0
#   oder
#   y = world_size - 1
#
# Karotten:
#
#   direkt dahinter als zweites L
#
#   x = 1
#   oder
#   y = world_size - 2
#
# Bei Breite 1.
# ==================================================

def is_sunflower_position(x, y):
    world_size = utils.size()
    width = config.SUNFLOWER_EDGE_WIDTH

    return (
        x < width
        or y >= world_size - width
    )


def is_carrot_position(x, y):
    world_size = utils.size()

    sunflower_width = config.SUNFLOWER_EDGE_WIDTH
    carrot_width = config.CARROT_SUPPORT_EDGE_WIDTH

    # Sonnenblumen haben Priorität.
    if is_sunflower_position(x, y):
        return False

    left_start = sunflower_width
    left_end = sunflower_width + carrot_width

    top_end = world_size - sunflower_width
    top_start = top_end - carrot_width

    return (
        (
            x >= left_start
            and x < left_end
        )
        or
        (
            y >= top_start
            and y < top_end
        )
    )


def is_protected_position(x, y):
    if is_sunflower_position(x, y):
        return True

    if is_carrot_position(x, y):
        return True

    return False


# ==================================================
# POLYKULTUR
# ==================================================

def plant_companion(entity):
    current = get_entity_type()

    if current == entity:
        return True

    if current != None:
        if not can_harvest():
            return False

        harvest()

    if entity == Entities.Grass:
        if get_ground_type() != Grounds.Grassland:
            till()

        return True

    if entity == Entities.Carrot:
        if get_ground_type() != Grounds.Soil:
            till()

        if not utils.can_afford(Entities.Carrot):
            return False

        plant(Entities.Carrot)

        return get_entity_type() == Entities.Carrot

    if entity == Entities.Tree:
        if not utils.can_afford(Entities.Tree):
            return False

        plant(Entities.Tree)

        return get_entity_type() == Entities.Tree

    if entity == Entities.Bush:
        if not utils.can_afford(Entities.Bush):
            return False

        plant(Entities.Bush)

        return get_entity_type() == Entities.Bush

    return False


def prepare_companion(min_x, max_x):
    if not config.ENABLE_POLYCULTURE:
        return

    companion = get_companion()

    if companion == None:
        return

    companion_entity, position = companion
    target_x, target_y = position

    # Jede Worker-Drohne verändert nur Companion-Felder
    # innerhalb ihrer eigenen Spalte.
    if target_x < min_x or target_x >= max_x:
        return

    if is_protected_position(
        target_x,
        target_y
    ):
        return

    original_x = get_pos_x()
    original_y = get_pos_y()

    utils.move_to(
        target_x,
        target_y
    )

    plant_companion(
        companion_entity
    )

    utils.move_to(
        original_x,
        original_y
    )


# ==================================================
# GRAS
# ==================================================

def farm_grass(min_x, max_x):
    utils.water()

    entity = get_entity_type()

    if (
        entity != None
        and entity != Entities.Grass
    ):
        if not can_harvest():
            return

        harvest()

    if get_ground_type() != Grounds.Grassland:
        till()

    if can_harvest():
        prepare_companion(
            min_x,
            max_x
        )

        harvest()

    # Bei hoher Düngerproduktion auch Gras beschleunigen.
    # Sonnenblumen bleiben absichtlich undüngt.
    fertilize()


# ==================================================
# BAUM
# ==================================================

def farm_tree(min_x, max_x):
    utils.water()

    entity = get_entity_type()

    if entity == Entities.Tree:
        if can_harvest():
            prepare_companion(
                min_x,
                max_x
            )

            harvest()

    elif entity != None:
        if not can_harvest():
            return

        harvest()

    if get_entity_type() == None:
        if utils.can_afford(Entities.Tree):
            plant(Entities.Tree)

    fertilize()


# ==================================================
# KAROTTE
# ==================================================

def farm_carrot(min_x, max_x):
    utils.water()

    entity = get_entity_type()

    if (
        entity != None
        and entity != Entities.Carrot
    ):
        if not can_harvest():
            return

        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    if get_entity_type() == Entities.Carrot:
        if can_harvest():
            prepare_companion(
                min_x,
                max_x
            )

            harvest()

    if get_entity_type() == None:
        if utils.can_afford(Entities.Carrot):
            plant(Entities.Carrot)

    fertilize()


# ==================================================
# SONNENBLUME
# ==================================================

def farm_sunflower():
    utils.water()

    entity = get_entity_type()

    if (
        entity != None
        and entity != Entities.Sunflower
    ):
        if not can_harvest():
            return

        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    # Sonnenblumen werden nur von refresh_energy()
    # geerntet, damit der 8x-Bonus erhalten bleibt.
    if get_entity_type() == None:
        if utils.can_afford(Entities.Sunflower):
            plant(Entities.Sunflower)


# ==================================================
# RESSOURCENFELDER
# ==================================================

def farm_resource(min_x, max_x):
    if (
        get_pos_x()
        + get_pos_y()
    ) % 4 == 0:
        farm_tree(
            min_x,
            max_x
        )
    else:
        farm_grass(
            min_x,
            max_x
        )


# ==================================================
# AKTUELLES FELD
# ==================================================

def farm_current_field(min_x, max_x):
    x = get_pos_x()
    y = get_pos_y()

    if is_sunflower_position(x, y):
        farm_sunflower()
        return

    if is_carrot_position(x, y):
        farm_carrot(
            min_x,
            max_x
        )
        return

    farm_resource(
        min_x,
        max_x
    )


# ==================================================
# SONNENBLUMEN SOFORT WIEDER AUFBAUEN
# ==================================================
#
# Zwei kurze Tasks:
#
# 1. linke Spalte
# 2. obere Reihe (ohne doppelte Ecke)
#
# Dadurch ist der Energiebereich nach Maze/Pumpkin/Cactus
# sofort wieder vorhanden, ohne eine große Fläche zu scannen.
# ==================================================

def _rebuild_left_edge():
    world_size = utils.size()

    x = 0

    for y in range(world_size - 1):
        utils.move_to(
            x,
            y
        )

        utils.water()

        if get_ground_type() != Grounds.Soil:
            till()

        entity = get_entity_type()

        if entity != Entities.Sunflower:
            if entity != None:
                if can_harvest():
                    harvest()
                else:
                    continue

            if utils.can_afford(
                Entities.Sunflower
            ):
                plant(
                    Entities.Sunflower
                )

    return True


def _rebuild_top_edge():
    world_size = utils.size()

    y = world_size - 1

    for x in range(world_size):
        utils.move_to(
            x,
            y
        )

        utils.water()

        if get_ground_type() != Grounds.Soil:
            till()

        entity = get_entity_type()

        if entity != Entities.Sunflower:
            if entity != None:
                if can_harvest():
                    harvest()
                else:
                    continue

            if utils.can_afford(
                Entities.Sunflower
            ):
                plant(
                    Entities.Sunflower
                )

    return True


def rebuild_sunflowers():
    tasks = [
        _rebuild_left_edge,
        _rebuild_top_edge
    ]

    workers.run(tasks)

    utils.move_to(
        0,
        0
    )

    return True


# ==================================================
# ENERGIE NACHLADEN
# ==================================================
#
# Die Sonnenblumen liegen bereits am Rand.
# Deshalb genügen zwei kurze Scans.
#
# Rückgabe eines Scan-Tasks:
#
# (count, max_petals, best_x, best_y)
# ==================================================

def _scan_left_edge():
    world_size = utils.size()

    count = 0
    max_petals = 0

    best_x = -1
    best_y = -1

    x = 0

    for y in range(world_size - 1):
        utils.move_to(
            x,
            y
        )

        if get_entity_type() == Entities.Sunflower:
            count += 1
            petals = measure()

            if petals > max_petals:
                max_petals = petals
                best_x = -1
                best_y = -1

                if can_harvest():
                    best_x = x
                    best_y = y

            elif petals == max_petals:
                if best_x == -1 and can_harvest():
                    best_x = x
                    best_y = y

    return (
        count,
        max_petals,
        best_x,
        best_y
    )


def _scan_top_edge():
    world_size = utils.size()

    count = 0
    max_petals = 0

    best_x = -1
    best_y = -1

    y = world_size - 1

    for x in range(world_size):
        utils.move_to(
            x,
            y
        )

        if get_entity_type() == Entities.Sunflower:
            count += 1
            petals = measure()

            if petals > max_petals:
                max_petals = petals
                best_x = -1
                best_y = -1

                if can_harvest():
                    best_x = x
                    best_y = y

            elif petals == max_petals:
                if best_x == -1 and can_harvest():
                    best_x = x
                    best_y = y

    return (
        count,
        max_petals,
        best_x,
        best_y
    )


def refresh_energy():
    original_x = get_pos_x()
    original_y = get_pos_y()

    results = workers.run([
        _scan_left_edge,
        _scan_top_edge
    ])

    sunflower_count = 0
    global_max = 0

    best_x = -1
    best_y = -1

    for result in results:
        count, petals, x, y = result

        sunflower_count += count

        if petals > global_max:
            global_max = petals

            best_x = -1
            best_y = -1

            if x >= 0:
                best_x = x
                best_y = y

        elif petals == global_max:
            if best_x == -1 and x >= 0:
                best_x = x
                best_y = y

    if (
        sunflower_count >= 10
        and best_x >= 0
    ):
        utils.move_to(
            best_x,
            best_y
        )

        if (
            get_entity_type() == Entities.Sunflower
            and measure() == global_max
            and can_harvest()
        ):
            harvest()

            if utils.can_afford(
                Entities.Sunflower
            ):
                plant(
                    Entities.Sunflower
                )

    utils.move_to(
        original_x,
        original_y
    )


# ==================================================
# EINEN FESTEN FARM-CHUNK BEARBEITEN
# ==================================================
#
# Jede Drohne bleibt in einem zusammenhängenden
# X-Bereich und fährt darin Snake/Zickzack.
# ==================================================

def _make_chunk_task(start_x, end_x):
    def task():
        world_size = utils.size()
        local_column = 0

        for x in range(start_x, end_x):
            if local_column % 2 == 0:
                direction = North
                start_y = 0
            else:
                direction = South
                start_y = world_size - 1

            utils.move_to(
                x,
                start_y
            )

            for step in range(world_size):
                farm_current_field(
                    start_x,
                    end_x
                )

                if step < world_size - 1:
                    move(direction)

            local_column += 1

        return True

    return task


# ==================================================
# KOMPLETTE PRODUKTIONSRUNDE
# ==================================================
#
# Beispiel 16x16 mit 4 verfügbaren Drohnen:
#
#   Drone A -> x 0..3
#   Drone B -> x 4..7
#   Drone C -> x 8..11
#   Drone D -> x 12..15
#
# Weniger Leerbewegung, keine separaten Spalten-Tasks.
# ==================================================

def run():
    world_size = utils.size()

    refresh_energy()

    worker_count = min(
        max_drones(),
        world_size
    )

    chunks = workers.make_chunks(
        world_size,
        worker_count
    )

    tasks = []

    for start_x, end_x in chunks:
        tasks.append(
            _make_chunk_task(
                start_x,
                end_x
            )
        )

    workers.run(tasks)

    utils.move_to(
        0,
        0
    )

    refresh_energy()
