import config
import utils


def try_unlock(feature):
    if get_cost(feature) == None:
        return False

    if not utils.can_afford(feature):
        return False

    before = num_unlocked(feature)

    unlock(feature)

    return num_unlocked(feature) > before


def run():
    for feature in config.AUTO_UNLOCKS:
        try_unlock(feature)
