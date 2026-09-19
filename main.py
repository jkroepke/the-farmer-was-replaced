import unlocks
import production
import farm
import workers


def restore_after_expand(previous_size):
    if get_world_size() == previous_size:
        return

    # Expansion invalidates any reusable Maze tree and changes the
    # coordinates of the permanent top edge.
    production.reset_state()

    clear()

    workers.set_main_hat()

    farm.reset_state()


def main():
    clear()

    workers.set_main_hat()

    # Normal farm layout is now established lazily by farm.run().
    # This avoids rebuilding the legacy L only to replace it immediately.
    farm.reset_state()

    last_target = None
    last_focus = None
    have_plan = False

    while True:
        # =================================================
        # CHOOSE NEXT UPGRADE
        # =================================================
        #
        # unlocks.next_target() considers:
        #
        # - all upgrade lines already unlocked at least once
        # - the next never-unlocked feature in configured order
        #
        # Lowest remaining total get_cost() wins.
        # =================================================

        target = unlocks.next_target()

        focus_item = None

        if target != None:
            focus_item = unlocks.focus_item(
                target
            )

        if (
            not have_plan
            or target != last_target
            or focus_item != last_focus
        ):
            quick_print(
                "PLAN",
                "goal",
                target,
                "focus",
                focus_item
            )

            last_target = target
            last_focus = focus_item
            have_plan = True

        # Everything configured is maxed:
        # keep the mixed farm productive.
        if target == None:
            production.run(None)

            pet_the_piggy()

            continue


        # =================================================
        # CHEAP FAST-PATH: UNLOCK NOW
        # =================================================

        previous_size = get_world_size()

        if unlocks.try_unlock(target):
            restore_after_expand(
                previous_size
            )

            pet_the_piggy()

            continue


        # =================================================
        # FARM THE MOST NEEDED RESOURCE
        # =================================================
        #
        # Resource choice uses the priority/order inspired by
        # Thorrdu/parameters.py, but the target quantities are
        # the real get_cost(target) values.
        # =================================================

        production.run(
            focus_item
        )


        # =================================================
        # TRY THE SAME TARGET AGAIN
        # =================================================
        #
        # The next loop recalculates the target from all current
        # inventories/costs, so the plan can naturally change.
        # =================================================

        previous_size = get_world_size()

        if unlocks.try_unlock(target):
            restore_after_expand(
                previous_size
            )

        pet_the_piggy()


if __name__ == "__main__":
    main()
