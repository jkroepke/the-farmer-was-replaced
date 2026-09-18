import utils
import workers


# ==================================================
# DINOSAUR JOB
# ==================================================
#
# Der Dinosaurier ist absichtlich ein Single-Drone-Job:
# Es existiert nur ein Hats.Dinosaur_Hat.
#
# Strategie:
#
# Auf geraden quadratischen Feldern folgt die Drohne einem
# Hamiltonian Cycle. Dadurch besucht sie jedes Feld genau
# einmal pro Runde und kann danach wieder am Start weiterfahren.
#
# Solange der Schwanz noch nicht die ganze Farm füllt, ist das
# nächste Feld auf diesem Zyklus sicher.
#
# Wenn move() schließlich False liefert, ist der Schwanz so groß,
# dass kein weiterer Zug mehr möglich ist. Dann wird der Hut
# abgelegt und der komplette Schwanz als Bones geerntet.
#
# Das Feld wird vorher geleert, damit zufällige Apples nicht durch
# Pflanzen blockiert werden.
# ==================================================


def can_start():
    world_size = utils.size()

    # Ein Hamiltonian Cycle auf dem rechteckigen Grid ist mit
    # dieser Implementierung für gerade Feldgrößen vorgesehen.
    if world_size < 2:
        return False

    if world_size % 2 != 0:
        return False

    # Ohne Cactus kann bereits der erste Apple nicht gekauft werden.
    if num_items(Items.Cactus) <= 0:
        return False

    return True


# ==================================================
# EIN DINOSAURIER-SCHRITT
# ==================================================
#
# Rückgabe:
#
# -1 -> move() fehlgeschlagen
#  0 -> normaler Schritt
#  1 -> auf dem verlassenen Feld lag ein Apple und wurde gegessen
# ==================================================

def dino_move(direction):
    on_apple = (
        get_entity_type()
        == Entities.Apple
    )

    if not move(direction):
        return -1

    if on_apple:
        return 1

    return 0


# ==================================================
# EIN KOMPLETTER HAMILTONIAN CYCLE
# ==================================================
#
# Beispiel-Idee:
#
# Start (0,0)
#
# linke Spalte ganz hoch,
# dann Spalten 1..N-1 zwischen y=1 und y=N-1 schlängeln,
# anschließend unten nach (0,0) zurück.
#
# Die unterste Reihe wird bis zum Ende freigehalten und schließt
# den Pfad wieder zu einem Cycle.
#
# Rückgabe:
#
# (cycle_completed, apples_eaten)
# ==================================================

def run_cycle():
    world_size = utils.size()
    apples_eaten = 0

    # Linke Spalte hoch.
    for _ in range(world_size - 1):
        result = dino_move(North)

        if result < 0:
            return False, apples_eaten

        apples_eaten += result

    # Innere Spalten schlängeln.
    for x in range(1, world_size):
        result = dino_move(East)

        if result < 0:
            return False, apples_eaten

        apples_eaten += result

        if x % 2 == 1:
            direction = South
        else:
            direction = North

        # y=0 bleibt zunächst frei.
        for _ in range(world_size - 2):
            result = dino_move(direction)

            if result < 0:
                return False, apples_eaten

            apples_eaten += result

    # Bei gerader Farmgröße endet die letzte Spalte bei y=1.
    result = dino_move(South)

    if result < 0:
        return False, apples_eaten

    apples_eaten += result

    # Untere Reihe zurück zum Start.
    for _ in range(world_size - 1):
        result = dino_move(West)

        if result < 0:
            return False, apples_eaten

        apples_eaten += result

    return True, apples_eaten


# ==================================================
# HUT ABLEGEN = SCHWANZ ERNTEN
# ==================================================

def harvest_tail():
    # workers.set_main_hat() setzt wieder den normalen
    # Hauptdrohnen-Hut und löst damit die Bone-Ernte aus.
    workers.set_main_hat()


# ==================================================
# KOMPLETTER DINOSAURIER-JOB
# ==================================================

def run():
    if not can_start():
        return False

    # clear() also resets the hat to Hats.Straw_Hat.
    # Therefore the Dinosaur Hat must always be equipped afterwards.
    clear()

    utils.move_to(
        0,
        0
    )

    # Dinosaurier-Hut ist exklusiv für diese Drohne.
    # measure() on the current Apple could reveal the next Apple position,
    # but the safe Hamiltonian strategy intentionally does not shortcut.
    change_hat(
        Hats.Dinosaur_Hat
    )

    # Wenn kein Apple unter der Drohne erscheint, reichen die
    # Cactus-Ressourcen nicht für einen sinnvollen Lauf.
    if get_entity_type() != Entities.Apple:
        harvest_tail()

        return False

    while True:
        completed, apples_eaten = run_cycle()

        # move() ist auf dem Hamiltonian Cycle fehlgeschlagen.
        # Normalerweise bedeutet das: der Schwanz füllt die Farm.
        if not completed:
            harvest_tail()

            return True

        # Ein kompletter Cycle besucht jedes Feld.
        #
        # Wenn dabei kein Apple gegessen wurde, existiert aktuell
        # kein erreichbarer Apple mehr. Das passiert z.B. wenn die
        # Cactus-Währung für einen neuen Apple ausgegangen ist.
        #
        # In diesem Fall ernten wir lieber den bereits vorhandenen
        # Schwanz, statt endlos weiterzufliegen.
        if apples_eaten == 0:
            harvest_tail()

            return True
