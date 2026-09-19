import config
import unlocks
import farm
import maze
import pumpkin
import cactus
import dinosaur
import workers
import utils


# True while consecutive Gold-focused Maze runs are active.
# This lets us avoid rebuilding the normal farm between mazes,
# while still restoring it exactly once when production focus changes.
_gold_active = False

# True after a successful full-field Pumpkin run.
# Consecutive Pumpkin-focused iterations must not rebuild the normal
# sunflower farm only for pumpkin.run() to clear it again immediately.
_pumpkin_active = False


# ==================================================
# RESTORE NORMAL FARM
# ==================================================

def reset_state():
    global _gold_active
    global _pumpkin_active

    _gold_active = False
    _pumpkin_active = False

    maze.reset()
    farm.reset_state()



def restore_normal_farm():
    global _gold_active
    global _pumpkin_active

    # Any normal farm restore destroys a reusable Maze.
    # Reset the in-memory tree before clearing the field.
    maze.reset()

    clear()

    workers.set_main_hat()

    # The adaptive normal farm establishes its own Sunflower columns
    # on the next farm.run() call.
    farm.reset_state()

    _gold_active = False
    _pumpkin_active = False


# ==================================================
# PRODUCER INPUTS
# ==================================================

def producer_multiplier(item):
    world_size = utils.size()

    if item == Items.Pumpkin:
        return (
            world_size
            * world_size
            * config.PUMPKIN_COST_FACTOR
        )

    if item == Items.Cactus:
        return (
            world_size
            * world_size
        )

    # Normal crops only need enough input to start making progress.
    # The next planner iteration will re-evaluate inventory/costs.
    return 1


def producer_prerequisite(item):
    producer = unlocks.producer_for(item)

    if producer == None:
        return None

    cost = get_cost(producer)

    return unlocks.choose_focus_from_cost(
        cost,
        producer_multiplier(item)
    )


# ==================================================
# BASIC RESOURCES
# ==================================================

def run_basic(item):
    prerequisite = producer_prerequisite(item)

    if (
        prerequisite != None
        and prerequisite != item
    ):
        return run(prerequisite)

    farm.run(item)

    return True


# ==================================================
# PUMPKIN
# ==================================================

def run_pumpkin():
    global _pumpkin_active

    if pumpkin.can_start():
        success = pumpkin.run()

        if success:
            # Keep the field in its post-Pumpkin state while Pumpkin
            # remains the planner focus. The next pumpkin.run() clears
            # the whole field anyway, so rebuilding Sunflowers here
            # would only plant them to destroy them immediately.
            _pumpkin_active = True

        return success

    prerequisite = producer_prerequisite(
        Items.Pumpkin
    )

    if prerequisite != None:
        return run(prerequisite)

    # Conservative fallback: pumpkin planting normally depends on
    # carrots, and the planner will re-evaluate after this farm run.
    farm.run(Items.Carrot)

    return True


# ==================================================
# CACTUS
# ==================================================

def run_cactus():
    if cactus.can_start():
        success = cactus.run()

        restore_normal_farm()

        return success

    prerequisite = producer_prerequisite(
        Items.Cactus
    )

    if prerequisite != None:
        return run(prerequisite)

    return run(Items.Pumpkin)


# ==================================================
# BONES / DINOSAUR
# ==================================================

def run_bones():
    if dinosaur.can_start():
        success = dinosaur.run()

        restore_normal_farm()

        return success

    # Apples consume Cactus. If we cannot start the Dinosaur job,
    # Cactus is therefore the first resource to replenish.
    return run(Items.Cactus)


# ==================================================
# GOLD / MAZE
# ==================================================

def run_gold():
    global _gold_active

    if maze.can_start():
        # Gold focus may immediately request another Maze.
        #
        # Do NOT rebuild the normal farm here. Rebuilding the permanent
        # sunflower L between consecutive Maze runs only adds movement
        # and planting work.
        success = maze.run()

        if success:
            _gold_active = True

        return success

    # We need normal farming to generate missing inputs / Weird Substance.
    # Restore exactly once if the previous iteration was a Gold Maze.
    if _gold_active:
        restore_normal_farm()

    # First ensure every Bush needed by the selected Maze strategy is
    # affordable. Parallel small-Maze production needs one Bush per worker.
    bush_focus = unlocks.choose_focus_from_cost(
        get_cost(Entities.Bush),
        maze.bushes_required()
    )

    if bush_focus != None:
        return run(bush_focus)

    # Gold requires a complete Weird-Substance reserve before entering
    # the Maze phase. Parallel production deliberately funds the whole
    # configured burst up front so no worker can starve mid-Maze.
    # Weird Substance is generated by harvesting fertilized normal crops,
    # so run a normal high-throughput Grass cycle until maze.can_start()
    # becomes true on a later planner iteration.
    farm.run(Items.Hay)

    return True


# ==================================================
# RESOURCE DISPATCH
# ==================================================

def run(item):
    global _gold_active
    global _pumpkin_active

    if item != Items.Gold and _gold_active:
        restore_normal_farm()

    if item != Items.Pumpkin and _pumpkin_active:
        restore_normal_farm()

    if item == None:
        farm.run()
        return True

    if item == Items.Pumpkin:
        return run_pumpkin()

    if item == Items.Cactus:
        return run_cactus()

    if item == Items.Bone:
        return run_bones()

    if item == Items.Gold:
        return run_gold()

    if item == Items.Weird_Substance:
        # Fertilizing normal crops generates Weird Substance.
        # farm.weird_substance_target() uses the first Maze unlock cost
        # before Mazes exists and the reusable-maze stockpile afterward.
        farm.run(
            Items.Hay
        )
        return True

    if (
        item == Items.Power
        or item == Items.Hay
        or item == Items.Wood
        or item == Items.Carrot
    ):
        return run_basic(item)

    # Unknown future resource:
    # keep the farm productive instead of stalling.
    farm.run()

    return False
