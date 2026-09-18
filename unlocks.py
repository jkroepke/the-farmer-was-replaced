import config
import utils


# ==================================================
# COST HELPERS
# ==================================================

def cost_total(cost):
    total = 0

    if cost == None:
        return total

    for item in cost:
        total += cost[item]

    return total


def remaining_total(cost):
    total = 0

    if cost == None:
        return total

    for item in cost:
        missing = (
            cost[item]
            - num_items(item)
        )

        if missing > 0:
            total += missing

    return total


# ==================================================
# RESOURCE PRIORITY
# ==================================================
#
# This mirrors the ordering/priority concept from:
# https://github.com/Thorrdu/the-farmer-was-replaced/blob/main/parameters.py
#
# Unlike that repository, the target amount comes from the
# actual get_cost() dictionary instead of static target values.
# ==================================================

def resource_priority(item):
    for plan in config.RESOURCE_PLANS:
        if plan["item"] == item:
            return plan["priority"]

    return 1


def producer_for(item):
    for plan in config.RESOURCE_PLANS:
        if plan["item"] == item:
            return plan["plant"]

    return None


def choose_focus_from_cost(cost, multiplier = 1):
    if cost == None:
        return None

    best_item = None
    best_score = 999999

    # Known farmable resources are considered in RESOURCE_PLANS
    # order. This also acts as the deterministic tie-breaker.
    for plan in config.RESOURCE_PLANS:
        item = plan["item"]

        if item not in cost:
            continue

        required = (
            cost[item]
            * multiplier
        )

        if required <= 0:
            continue

        current = num_items(item)

        if current >= required:
            continue

        progress_ratio = (
            current
            / required
        )

        score = (
            progress_ratio
            / plan["priority"]
        )

        if score < best_score:
            best_score = score
            best_item = item

    if best_item != None:
        return best_item

    # Fallback for future/unknown cost items that are not yet in
    # RESOURCE_PLANS. We can at least expose the missing item to the
    # production planner instead of silently pretending the cost is met.
    for item in cost:
        required = (
            cost[item]
            * multiplier
        )

        if num_items(item) < required:
            return item

    return None


# ==================================================
# NEXT UNLOCK
# ==================================================
#
# We do not blindly max the first entry in AUTO_UNLOCKS.
#
# Candidate set:
#
# - every upgrade line that has already been unlocked at least once
# - plus the first upgrade line in AUTO_UNLOCKS that has never been
#   unlocked yet
#
# This preserves the configured progression/frontier while allowing
# cheap levels of Speed/Expand/etc. to compete with each other.
#
# Within that candidate set:
#
# 1. lowest remaining total resource cost wins
# 2. lower nominal total cost wins ties
# 3. AUTO_UNLOCKS order wins remaining ties
# ==================================================

def next_target():
    best_feature = None
    best_remaining = -1
    best_total = -1

    reached_frontier = False

    for feature in config.AUTO_UNLOCKS:
        if reached_frontier:
            break

        cost = get_cost(feature)

        # Current game docs return {} for an upgradeable unlock at
        # maximum level. Keep None compatibility for older behavior.
        if cost != None and len(cost) > 0:
            remaining = remaining_total(cost)
            total = cost_total(cost)

            if best_feature == None:
                best_feature = feature
                best_remaining = remaining
                best_total = total

            elif remaining < best_remaining:
                best_feature = feature
                best_remaining = remaining
                best_total = total

            elif (
                remaining == best_remaining
                and total < best_total
            ):
                best_feature = feature
                best_remaining = remaining
                best_total = total

        if num_unlocked(feature) == 0:
            reached_frontier = True

    return best_feature


def focus_item(feature):
    if feature == None:
        return None

    return choose_focus_from_cost(
        get_cost(feature)
    )


# ==================================================
# UNLOCK ACTION
# ==================================================

def try_unlock(feature):
    if feature == None:
        return False

    cost = get_cost(feature)

    if cost == None:
        return False

    if len(cost) == 0:
        return False

    if not utils.can_afford(feature):
        return False

    before = num_unlocked(feature)

    unlock(feature)

    return num_unlocked(feature) > before


def run():
    target = next_target()

    if target == None:
        return False

    return try_unlock(target)
