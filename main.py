import config
import unlocks
import farm
import maze
import pumpkin
import cactus
import workers


def main():
    clear()

    # Die Hauptdrohne trägt immer den ersten Hut.
    workers.set_main_hat()

    # Nach dem Start zuerst die Energieversorgung aufbauen.
    farm.rebuild_sunflowers()

    # Gesamtzahl normaler Mischfarm-Runden.
    production_runs = 0

    # Produktionsrunden seit dem letzten Maze.
    maze_runs = 0

    # Produktionsrunden seit dem letzten Pumpkin.
    pumpkin_runs = 0

    # Produktionsrunden seit dem letzten Cactus.
    cactus_runs = 0


    while True:

        # =================================================
        # NORMALE MEGA-FARM
        # =================================================
        #
        # farm.run() verteilt die Spalten automatisch
        # auf mehrere Drohnen.
        # =================================================

        farm.run()

        production_runs += 1
        maze_runs += 1
        pumpkin_runs += 1
        cactus_runs += 1

        pet_the_piggy()


        # =================================================
        # AUTOMATISCHE UPGRADES
        # =================================================

        unlocks.run()


        # =================================================
        # MAZE
        # =================================================
        #
        # Maze bleibt bewusst seriell.
        # =================================================

        if (
            maze_runs >= config.MAZE_EVERY
            and maze.can_start()
        ):
            if maze.run():
                maze_runs = 0

                clear()

                # Nach Full-Field-Jobs Sonnenblumen
                # sofort wieder parallel aufbauen.
                farm.rebuild_sunflowers()

                unlocks.run()

                pet_the_piggy()


        # =================================================
        # PUMPKIN
        # =================================================
        #
        # Pumpkin-Scans laufen spaltenweise parallel.
        # =================================================

        elif (
            pumpkin_runs >= config.PUMPKIN_EVERY
            and pumpkin.can_start()
        ):
            pumpkin.run()

            pumpkin_runs = 0

            clear()

            farm.rebuild_sunflowers()

            unlocks.run()

            pet_the_piggy()


        # =================================================
        # CACTUS
        # =================================================
        #
        # Pflanzen, Warten und Sortieren werden
        # soweit möglich über mehrere Drohnen verteilt.
        # =================================================

        elif (
            cactus_runs >= config.CACTUS_EVERY
            and cactus.can_start()
        ):
            cactus.run()

            cactus_runs = 0

            clear()

            farm.rebuild_sunflowers()

            unlocks.run()

            pet_the_piggy()


if __name__ == "__main__":
    main()
