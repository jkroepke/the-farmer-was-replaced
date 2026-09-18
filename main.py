import config
import unlocks
import farm
import maze
import pumpkin
import cactus
import dinosaur
import workers


def main():
    clear()

    # Die Hauptdrohne trägt im normalen Betrieb
    # immer den ersten Hut aus workers.py.
    workers.set_main_hat()

    # Nach dem Start zuerst die permanente
    # Energieversorgung am linken/oberen Rand aufbauen.
    farm.rebuild_sunflowers()

    # Gesamtzahl normaler Mischfarm-Runden.
    production_runs = 0

    # Produktionsrunden seit dem letzten Spezialjob.
    maze_runs = 0
    pumpkin_runs = 0
    cactus_runs = 0
    dinosaur_runs = 0

    while True:

        # =================================================
        # NORMALE MEGA-FARM
        # =================================================

        farm.run()

        production_runs += 1
        maze_runs += 1
        pumpkin_runs += 1
        cactus_runs += 1
        dinosaur_runs += 1

        pet_the_piggy()


        # =================================================
        # AUTOMATISCHE UPGRADES
        # =================================================

        unlocks.run()


        # =================================================
        # MAZE
        # =================================================

        if (
            maze_runs >= config.MAZE_EVERY
            and maze.can_start()
        ):
            if maze.run():
                maze_runs = 0

                clear()

                farm.rebuild_sunflowers()

                unlocks.run()

                pet_the_piggy()


        # =================================================
        # PUMPKIN
        # =================================================

        elif (
            pumpkin_runs >= config.PUMPKIN_EVERY
            and pumpkin.can_start()
        ):
            if pumpkin.run():
                pumpkin_runs = 0

                clear()

                farm.rebuild_sunflowers()

                unlocks.run()

                pet_the_piggy()


        # =================================================
        # CACTUS
        # =================================================

        elif (
            cactus_runs >= config.CACTUS_EVERY
            and cactus.can_start()
        ):
            if cactus.run():
                cactus_runs = 0

                clear()

                farm.rebuild_sunflowers()

                unlocks.run()

                pet_the_piggy()


        # =================================================
        # DINOSAURIER
        # =================================================
        #
        # Exklusiver Single-Drone-Job.
        #
        # Das Feld wird geleert und der Dinosaur folgt
        # einem Hamiltonian Cycle, bis der Schwanz die Farm
        # füllt oder keine Apples mehr entstehen.
        # =================================================

        elif (
            dinosaur_runs >= config.DINOSAUR_EVERY
            and dinosaur.can_start()
        ):
            if dinosaur.run():
                dinosaur_runs = 0

                clear()

                # Dinosaur entfernt den normalen Farm-Inhalt.
                # Danach sofort wieder Sonnenblumen aufbauen.
                farm.rebuild_sunflowers()

                unlocks.run()

                pet_the_piggy()


if __name__ == "__main__":
    main()
