import config
import utils
import workers


# ==================================================
# STARTBEDINGUNG
# ==================================================

def can_start():
    world_size = utils.size()

    fields = (
        world_size
        * world_size
    )

    required_fields = (
        fields
        * config.PUMPKIN_COST_FACTOR
    )

    return utils.can_afford(
        Entities.Pumpkin,
        required_fields
    )


# ==================================================
# ZEIT
# ==================================================

def wait_seconds(seconds):
    end_time = (
        get_time()
        + seconds
    )

    while get_time() < end_time:
        pass


# ==================================================
# FULL-MAP-PUMPKIN PER ID ERKENNEN
# ==================================================
#
# Community-Beobachtung / Reverse Engineering:
#
# measure() liefert bei Pumpkins eine eindeutige Pumpkin-ID.
# Beim Merge behält der größere Pumpkin die ID des ersten
# beteiligten Pumpkins.
#
# Wenn (0,0) und (size-1,size-1) dieselbe ID haben,
# gehören beide Ecken zum selben Full-Map-Pumpkin.
#
# Durch Wrap-Around erreichen wir die gegenüberliegende
# Ecke von (0,0) mit genau:
#
#   move(West)
#   move(South)
# ==================================================

def is_full_map_pumpkin():
    utils.move_to(
        0,
        0
    )

    if get_entity_type() != Entities.Pumpkin:
        return False

    first_id = measure()

    move(West)
    move(South)

    if get_entity_type() != Entities.Pumpkin:
        utils.move_to(
            0,
            0
        )

        return False

    opposite_id = measure()

    full = (
        first_id == opposite_id
        and can_harvest()
    )

    utils.move_to(
        0,
        0
    )

    return full


# ==================================================
# MEGAFARM FAST PATH: EINE DROHNE PRO SPALTE
# ==================================================
#
# Aktiv, wenn mindestens so viele Drohnen wie Spalten verfügbar sind.
#
# Jede Drohne:
#
# - gehört dauerhaft genau einer Spalte
# - läuft ausschließlich North
# - nutzt das Farm-Wrap statt am Spaltenende umzudrehen
# - merkt sich bereits fertig gewachsene, lebende Pumpkins
# - ersetzt tote/fehlende Pumpkins direkt
# - beendet sich erst, wenn ihre komplette Spalte sicher fertig ist
#
# Warum North-only:
#
# move(North) wrappt am oberen Rand direkt nach y=0. Damit kostet ein
# kompletter 32er-Spaltenumlauf genau 32 Bewegungen. Ein Hoch/Runter-Pass
# würde fast doppelt so viele Bewegungen benötigen.
#
# Mechanik-/Strategie-Referenzen:
#
# - https://thefarmerwasreplaced.wiki.gg/wiki/Move
# - https://thefarmerwasreplaced.wiki.gg/wiki/Pumpkins
# - external/mateusmarochi-the-farmer-was-replaced-codes/source/pumpkin_farm.py
# - https://www.reddit.com/r/TheFarmerWasReplaced/comments/1ohszgq/
# - https://www.reddit.com/r/TheFarmerWasReplaced/comments/1pz3nlc/
#
# Der MateusMarochi-Ansatz verteilt ebenfalls Worker über Spalten.
# Unsere Variante vermeidet dessen South-Rückweg und nutzt stattdessen
# den dokumentierten Wrap von move(North).
# ==================================================

def can_use_column_workers():
    return (
        max_drones()
        >= utils.size()
    )


def _service_column_pumpkin():
    entity = get_entity_type()

    # Ein lebender, ausgewachsener Pumpkin ist dauerhaft sicher:
    # die Todesentscheidung passiert beim Auswachsen.
    if entity == Entities.Pumpkin:
        if can_harvest():
            return 1

        return 0

    # Dead Pumpkin muss nicht geerntet werden. Ein neues plant()
    # ersetzt ihn direkt.
    if entity == Entities.Dead_Pumpkin:
        if not utils.can_afford(
            Entities.Pumpkin
        ):
            return -1

        utils.water()

        plant(
            Entities.Pumpkin
        )

        return 0

    # Nach clear() sollte dieser Fall praktisch nur None sein.
    # Für Robustheit entfernen wir unerwartete erntereife Entitäten.
    if entity != None:
        if not can_harvest():
            return 0

        harvest()

    if get_ground_type() != Grounds.Soil:
        till()

    if not utils.can_afford(
        Entities.Pumpkin
    ):
        return -1

    # Einmal beim Pflanzen wässern. Danach bewegt sich der Worker
    # weiter, statt auf dem Tile zu warten.
    utils.water()

    plant(
        Entities.Pumpkin
    )

    return 0


def _make_column_worker(column):
    def task():
        world_size = utils.size()

        utils.move_to(
            column,
            0
        )

        ready = []

        for _ in range(world_size):
            ready.append(False)

        remaining = world_size

        while remaining > 0:
            for row in range(world_size):
                if not ready[row]:
                    state = (
                        _service_column_pumpkin()
                    )

                    if state < 0:
                        return False

                    if state > 0:
                        ready[row] = True
                        remaining -= 1

                # North-only is intentional: after world_size moves
                # the worker wraps back to y=0 in the same column.
                move(North)

        return True

    return task


def run_column_workers():
    world_size = utils.size()
    tasks = []

    for column in range(world_size):
        tasks.append(
            _make_column_worker(
                column
            )
        )

    results = workers.run(tasks)

    for result in results:
        if not result:
            return False

    return True


# ==================================================
# INITIAL: KOMPLETTE FARM PFLANZEN
# ==================================================

def _make_initial_chunk_task(start_x, end_x):
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
                utils.water()

                if get_ground_type() != Grounds.Soil:
                    till()

                entity = get_entity_type()

                if entity != Entities.Pumpkin:
                    if entity != None:
                        if can_harvest():
                            harvest()

                    if get_entity_type() == None:
                        if not utils.can_afford(
                            Entities.Pumpkin
                        ):
                            return False

                        plant(
                            Entities.Pumpkin
                        )

                if step < world_size - 1:
                    move(direction)

            local_column += 1

        return True

    return task


def plant_full_field():
    world_size = utils.size()

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
            _make_initial_chunk_task(
                start_x,
                end_x
            )
        )

    results = workers.run(tasks)

    for result in results:
        if not result:
            return False

    return True


# ==================================================
# PROBLEMPOSITIONEN SAMMELN
# ==================================================
#
# Eine Position bleibt problematisch, wenn:
#
# - Pumpkin fehlt
# - Pumpkin tot ist
# - Pumpkin noch nicht ausgewachsen ist
#
# Ein bereits ausgewachsener, lebender Pumpkin ist sicher:
# die 20%-Todesentscheidung ist beim Auswachsen bereits gefallen.
#
# Dadurch müssen fertige Felder später nicht erneut geprüft werden.
# ==================================================

def _make_collect_chunk_task(start_x, end_x):
    def task():
        world_size = utils.size()
        problems = []

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
                entity = get_entity_type()

                if entity != Entities.Pumpkin:
                    problems.append(
                        (get_pos_x(), get_pos_y())
                    )

                elif not can_harvest():
                    problems.append(
                        (get_pos_x(), get_pos_y())
                    )

                if step < world_size - 1:
                    move(direction)

            local_column += 1

        return problems

    return task


def collect_problem_positions():
    world_size = utils.size()

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
            _make_collect_chunk_task(
                start_x,
                end_x
            )
        )

    results = workers.run(tasks)

    problems = []

    for result in results:
        for position in result:
            problems.append(position)

    return problems


# ==================================================
# NUR BEKANNTE PROBLEME PATCHEN
# ==================================================
#
# Das ist der Kern von "Patch & Wait":
#
# Statt 256 Felder erneut zu scannen, besuchen Worker
# nur noch die Koordinaten, die beim letzten Check noch
# tot, leer oder unreif waren.
#
# Rückgabe:
#   Liste der weiterhin nicht fertigen Positionen.
# ==================================================

def _make_patch_task(positions):
    def task():
        remaining = []

        for position in positions:
            x, y = position

            utils.move_to(
                x,
                y
            )

            utils.water()

            if get_ground_type() != Grounds.Soil:
                till()

            entity = get_entity_type()

            # Toter / fehlender Pumpkin:
            # direkt ersetzen und weiter beobachten.
            if (
                entity == None
                or entity == Entities.Dead_Pumpkin
            ):
                if not utils.can_afford(
                    Entities.Pumpkin
                ):
                    remaining.append(position)
                    continue

                plant(
                    Entities.Pumpkin
                )

                remaining.append(position)
                continue

            # Unerwartete andere Entität.
            if entity != Entities.Pumpkin:
                if can_harvest():
                    harvest()

                if get_entity_type() == None:
                    if utils.can_afford(
                        Entities.Pumpkin
                    ):
                        plant(
                            Entities.Pumpkin
                        )

                remaining.append(position)
                continue

            # Lebender Pumpkin, aber noch nicht fertig.
            if not can_harvest():
                remaining.append(position)

        return remaining

    return task


def patch_problem_positions(problems):
    if len(problems) == 0:
        return []

    worker_count = min(
        max_drones(),
        len(problems)
    )

    chunks = workers.make_chunks(
        len(problems),
        worker_count
    )

    tasks = []

    for start, end in chunks:
        tasks.append(
            _make_patch_task(
                problems[start:end]
            )
        )

    results = workers.run(tasks)

    remaining = []

    for result in results:
        for position in result:
            remaining.append(position)

    return remaining


# ==================================================
# KOMPLETTER PUMPKIN-JOB
# ==================================================
#
# Zwei Strategien:
#
# 1. Megafarm Fast Path
#    Wenn mindestens eine Drohne pro Spalte verfügbar ist:
#    dauerhafte North-only-Spaltenworker bis alle Tiles fertig sind.
#
# 2. Patch & Wait Fallback
#    Für weniger Drohnen:
#    Full field pflanzen, Problemkoordinaten sammeln und danach nur
#    bekannte Problempositionen erneut prüfen.
#
# Beide Pfade bestätigen den Full-Map-Merge abschließend über die
# Pumpkin-ID an gegenüberliegenden Ecken.
# ==================================================

def run():
    if not can_start():
        return False

    clear()

    # 32x32 + 32 Drohnen landet hier:
    # genau ein persistenter Worker pro Spalte.
    if can_use_column_workers():
        if not run_column_workers():
            return False

        # Normalerweise ist der Full-Map-Pumpkin jetzt bereits gemerged.
        if is_full_map_pumpkin():
            harvest()
            return True

        # Seltene Merge-Verzögerung / Robustheitsfallback:
        # ab hier übernimmt derselbe Patch-&-Wait-Abschluss wie bei
        # kleineren Worker-Pools.
        problems = (
            collect_problem_positions()
        )

    else:
        if not plant_full_field():
            return False

        wait_seconds(
            config.PUMPKIN_INITIAL_WAIT
        )

        # Sehr billiger Fast-Path:
        # vielleicht ist bereits alles gemerged.
        if is_full_map_pumpkin():
            harvest()
            return True

        problems = (
            collect_problem_positions()
        )

    while True:
        wait_seconds(
            config.PUMPKIN_ID_CHECK_INTERVAL
        )

        # Full-map merge kann bereits passiert sein,
        # auch wenn unsere lokale Problem-Liste noch
        # alte Einträge enthält.
        if is_full_map_pumpkin():
            harvest()
            return True

        if len(problems) > 0:
            problems = patch_problem_positions(
                problems
            )

            # Neu gepflanzte / noch unreife Problemfelder
            # brauchen etwas Zeit.
            if len(problems) > 0:
                wait_seconds(
                    config.PUMPKIN_PATCH_INTERVAL
                )

            continue

        # Keine bekannten Probleme mehr.
        #
        # Normalerweise sollte der Mega-Pumpkin jetzt
        # direkt entstehen. Falls Corner IDs noch nicht
        # identisch sind, einmal Fallback-Full-Scan:
        # möglicherweise gab es eine noch nicht bekannte
        # Problemposition.
        if is_full_map_pumpkin():
            harvest()
            return True

        problems = collect_problem_positions()

        # Falls der Scan ebenfalls keine Probleme findet,
        # kurz warten: der Merge kann unmittelbar bevorstehen.
        if len(problems) == 0:
            wait_seconds(
                config.PUMPKIN_ID_CHECK_INTERVAL
            )
