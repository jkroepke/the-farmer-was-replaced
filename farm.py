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

def sunflower_start():
    return (
        utils.size()
        - config.SUNFLOWER_SIZE
    ) // 2


def sunflower_end():
    return (
        sunflower_start()
        + config.SUNFLOWER_SIZE
    )


def is_sunflower_position(x, y):
    start = sunflower_start()
    end = sunflower_end()

    return (
        x >= start
        and x < end
        and y >= start
        and y < end
    )


def is_carrot_position(x, y):
    start = sunflower_start()
    end = sunflower_end()

    outer_start = max(
        0,
        start - config.CARROT_RING_WIDTH
    )

    outer_end = min(
        utils.size(),
        end + config.CARROT_RING_WIDTH
    )

    inside_outer = (
        x >= outer_start
        and x < outer_end
        and y >= outer_start
        and y < outer_end
    )

    if not inside_outer:
        return False

    if is_sunflower_position(x, y):
        return False

    return True


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

def _make_rebuild_chunk_task(start_x, end_x):
    def task():
        start_y = sunflower_start()
        end_y = sunflower_end()
        all_planted = True

        for x in range(start_x, end_x):
            utils.move_to(x, start_y)

            for y in range(start_y, end_y):
                utils.water()

                if get_ground_type() != Grounds.Soil:
                    till()

                entity = get_entity_type()

                if entity != Entities.Sunflower:
                    if entity != None:
                        if can_harvest():
                            harvest()
                        else:
                            all_planted = False

                    if get_entity_type() == None:
                        if utils.can_afford(Entities.Sunflower):
                            plant(Entities.Sunflower)
                        else:
                            all_planted = False

                if y < end_y - 1:
                    move(North)

        return all_planted

    return task


def rebuild_sunflowers():
    start = sunflower_start()
    end = sunflower_end()
    width = end - start

    # Maximal vier Worker für das kleine zentrale Feld.
    worker_count = min(
        max_drones(),
        width,
        4
    )

    chunks = workers.make_chunks(
        width,
        worker_count
    )

    tasks = []

    for chunk_start, chunk_end in chunks:
        tasks.append(
            _make_rebuild_chunk_task(
                start + chunk_start,
                start + chunk_end
            )
        )

    results = workers.run(tasks)

    for result in results:
        if not result:
            return False

    return True


# ==================================================
# ENERGIE NACHLADEN
# ==================================================
#
# Das zentrale Sonnenblumenfeld wird in wenige Chunks
# geteilt. Keine einzelne Scanner-Drohne pro Spalte.
# ==================================================

def _make_energy_chunk_task(start_x, end_x):
    def task():
        start_y = sunflower_start()
        end_y = sunflower_end()

        sunflower_count = 0
        max_petals = 0
        best_x = -1
        best_y = -1

        for x in range(start_x, end_x):
            utils.move_to(x, start_y)

            for y in range(start_y, end_y):
                if get_entity_type() == Entities.Sunflower:
                    sunflower_count += 1
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

                if y < end_y - 1:
                    move(North)

        return (
            sunflower_count,
            max_petals,
            best_x,
            best_y
        )

    return task


def refresh_energy():
    original_x = get_pos_x()
    original_y = get_pos_y()

    start = sunflower_start()
    end = sunflower_end()
    width = end - start

    worker_count = min(
        max_drones(),
        width,
        4
    )

    chunks = workers.make_chunks(
        width,
        worker_count
    )

    tasks = []

    for chunk_start, chunk_end in chunks:
        tasks.append(
            _make_energy_chunk_task(
                start + chunk_start,
                start + chunk_end
            )
        )

    results = workers.run(tasks)

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

    if sunflower_count >= 10 and best_x >= 0:
        utils.move_to(best_x, best_y)

        if (
            get_entity_type() == Entities.Sunflower
            and measure() == global_max
            and can_harvest()
        ):
            harvest()

            if utils.can_afford(Entities.Sunflower):
                plant(Entities.Sunflower)

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
