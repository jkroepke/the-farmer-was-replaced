import config
import utils
import workers


# Petal metadata for the permanent sunflower L.
#
# Each entry is:
#   [x, y, petals]
#
# This cache belongs to the current drone. Spawned drones do not share globals,
# so rebuild workers return their measurements and the caller rebuilds this list.
_sunflower_petals = []


def reset_state():
    global _sunflower_petals

    _sunflower_petals = []


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
#
# Die permanenten Sonnenblumen werden ausschließlich von
# rebuild_sunflowers() und refresh_energy() gepflanzt/geerntet.
#
# Normale Farm-Worker dürfen den Petal-Cache nicht verändern,
# weil Drohnen keinen gemeinsamen Speicher haben.
# ==================================================

def farm_sunflower():
    utils.water()


# ==================================================
# RESSOURCENFELDER
# ==================================================
#
# focus_item comes from the upgrade planner.
#
# Permanent sunflower/carrot support tiles keep their dedicated
# roles. Only the normal resource area changes its production mix.
# ==================================================

def farm_resource(min_x, max_x, focus_item):
    if focus_item == Items.Hay:
        farm_grass(
            min_x,
            max_x
        )
        return

    if focus_item == Items.Wood:
        # 50% checkerboard trees:
        # no north/east/south/west tree adjacency, but much more
        # wood throughput than the normal 25% mixed-farm pattern.
        if (
            get_pos_x()
            + get_pos_y()
        ) % 2 == 0:
            farm_tree(
                min_x,
                max_x
            )
        else:
            farm_grass(
                min_x,
                max_x
            )

        return

    if focus_item == Items.Carrot:
        farm_carrot(
            min_x,
            max_x
        )
        return

    # Power is produced by the permanent sunflower L and therefore
    # does not require converting the rest of the farm to sunflowers.
    #
    # Unknown/non-basic resources also fall back to this mixed layout;
    # their dedicated production jobs are handled in production.py.
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

def farm_current_field(min_x, max_x, focus_item):
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
        max_x,
        focus_item
    )


# ==================================================
# SONNENBLUMEN-CACHE AUFBAUEN
# ==================================================
#
# Beim Pflanzen bzw. Wiederaufbau wird measure() genau einmal
# pro Sonnenblume ausgeführt und das Ergebnis gecacht.
#
# Mit zwei Drohnen teilen wir das permanente L natürlich auf:
#
# - linke Kante
# - obere Kante
#
# Die Worker geben ihre [x, y, petals]-Listen zurück. Erst die
# aufrufende Drohne schreibt daraus den globalen Cache, weil
# Drohnen keinen gemeinsamen Speicher besitzen.
# ==================================================

def _prepare_sunflower():
    utils.water()

    if get_ground_type() != Grounds.Soil:
        till()

    entity = get_entity_type()

    if entity != Entities.Sunflower:
        if entity != None:
            if not can_harvest():
                return None

            harvest()

        if get_entity_type() == None:
            if not utils.can_afford(
                Entities.Sunflower
            ):
                return None

            plant(
                Entities.Sunflower
            )

    if get_entity_type() != Entities.Sunflower:
        return None

    return [
        get_pos_x(),
        get_pos_y(),
        measure()
    ]


def _rebuild_left_edge():
    world_size = utils.size()
    petals = []

    x = 0

    # Ecke oben links wird vom Top-Edge-Worker übernommen.
    for y in range(world_size - 1):
        utils.move_to(
            x,
            y
        )

        item = _prepare_sunflower()

        if item != None:
            petals.append(item)

    return petals


def _rebuild_top_edge():
    world_size = utils.size()
    petals = []

    y = world_size - 1

    for x in range(world_size):
        utils.move_to(
            x,
            y
        )

        item = _prepare_sunflower()

        if item != None:
            petals.append(item)

    return petals


def rebuild_sunflowers():
    global _sunflower_petals

    original_x = get_pos_x()
    original_y = get_pos_y()

    results = workers.run([
        _rebuild_left_edge,
        _rebuild_top_edge
    ])

    petals = []

    for result in results:
        for item in result:
            petals.append(item)

    _sunflower_petals = petals

    utils.move_to(
        original_x,
        original_y
    )

    return len(_sunflower_petals) >= 10


# ==================================================
# PETAL-CACHE
# ==================================================

def _cached_sunflower_count():
    count = 0

    for item in _sunflower_petals:
        if item[2] >= 0:
            count += 1

    return count


def _cached_max_petals():
    max_petals = 0

    for item in _sunflower_petals:
        if item[2] > max_petals:
            max_petals = item[2]

    return max_petals


# ==================================================
# ENERGIE NACHLADEN
# ==================================================
#
# Kein Full-L-Scan mehr bei jedem Refresh.
#
# Ablauf:
#
# 1. Maximum nur aus dem Cache bestimmen.
# 2. Nur Positionen mit diesem Maximum besuchen.
# 3. Nur ernten, wenn eine Max-Petal-Sonnenblume reif ist.
# 4. Direkt neu pflanzen und measure() für genau diese Position.
# 5. Danach Maximum erneut aus dem Cache bestimmen.
#
# Wichtig:
# Wenn eine neu gepflanzte Sonnenblume wieder das höchste
# Petal-Level hat, aber noch unreif ist, blockiert sie korrekt
# niedrigere Petal-Level. Dann wird nichts Falsches geerntet.
# ==================================================

def refresh_energy():
    global _sunflower_petals

    original_x = get_pos_x()
    original_y = get_pos_y()

    # Nach clear()/Spezialjobs wird der Cache normalerweise durch
    # rebuild_sunflowers() aufgebaut. Dieser Fallback schützt den
    # Start mit leerem/zu kleinem Cache.
    if _cached_sunflower_count() < 10:
        rebuild_sunflowers()

    if _cached_sunflower_count() < 10:
        utils.move_to(
            original_x,
            original_y
        )

        return False

    harvested_any = False

    while True:
        max_petals = _cached_max_petals()

        if max_petals <= 0:
            break

        harvested = False
        cache_invalid = False

        for item in _sunflower_petals:
            if item[2] != max_petals:
                continue

            utils.move_to(
                item[0],
                item[1]
            )

            if get_entity_type() != Entities.Sunflower:
                item[2] = -1
                cache_invalid = True
                break

            # Petal-Zahl sollte stabil sein. Re-check kostet nur
            # measure(), verhindert aber einen falschen Harvest,
            # falls der Cache aus irgendeinem Grund veraltet ist.
            actual_petals = measure()

            if actual_petals != item[2]:
                item[2] = actual_petals
                cache_invalid = True
                break

            if not can_harvest():
                continue

            harvest()
            harvested = True
            harvested_any = True

            if utils.can_afford(
                Entities.Sunflower
            ):
                plant(
                    Entities.Sunflower
                )

                # Petal-Wert der neuen Blume sofort cachen.
                item[2] = measure()
            else:
                # Tile ist aktuell leer und darf bei der
                # Max-Berechnung nicht mehr berücksichtigt werden.
                item[2] = -1

            # Nach JEDEM Harvest das globale Maximum neu bestimmen.
            break

        if cache_invalid:
            # Normalerweise nie nötig. Wenn ein Cache-Eintrag nicht
            # mehr zur Farm passt, reparieren wir die L-Kante sauber.
            rebuild_sunflowers()

            if _cached_sunflower_count() < 10:
                break

            continue

        if not harvested:
            # Das aktuelle Maximum existiert, ist aber noch nicht reif.
            # Niedrigere Petal-Level dürfen dann nicht geerntet werden.
            break

    utils.move_to(
        original_x,
        original_y
    )

    return harvested_any


# ==================================================
# EINEN FESTEN FARM-CHUNK BEARBEITEN
# ==================================================
#
# Jede Drohne bleibt in einem zusammenhängenden
# X-Bereich und fährt darin Snake/Zickzack.
# ==================================================

def _make_chunk_task(start_x, end_x, focus_item):
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
                    end_x,
                    focus_item
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

def run_legacy(focus_item = None):
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
                end_x,
                focus_item
            )
        )

    workers.run(tasks)

    utils.move_to(
        0,
        0
    )

    refresh_energy()
