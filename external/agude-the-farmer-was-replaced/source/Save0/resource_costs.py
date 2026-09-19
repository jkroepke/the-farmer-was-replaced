def get_valid_cost(target, allow_empty=False):
    # Return a live cost map, or report why it is unusable.
    cost = get_cost(target)

    if cost == None:
        quick_print("Missing resource cost")
        return None

    if len(cost) == 0:
        if allow_empty:
            return cost

        quick_print("Missing resource cost")
        return None

    for item in cost:
        amount = cost[item]

        if amount == None or amount <= 0:
            quick_print("Malformed resource cost")
            return None

    return cost


def get_top_hat_cost():
    # Read the current Top Hat requirement from the installed game.
    return get_valid_cost(Unlocks.Top_Hat)


def get_planting_budget(entity, width: int, height: int):
    # Scale a live per-tile planting cost by explicit region geometry.
    cost = get_valid_cost(entity, True)

    if cost == None or width <= 0 or height <= 0:
        if cost != None:
            quick_print("Invalid planting region")
        return None

    tile_count = width * height
    budget = {}

    for item in cost:
        budget[item] = cost[item] * tile_count

    return budget


def get_required_inventory(cost, protected_inventory=None, cycle_budget=None):
    # Combine a live cost with protected balances and the next cycle budget.
    if cost == None:
        quick_print("Missing required inventory cost")
        return None

    required = {}

    for item in cost:
        required[item] = cost[item]

    if protected_inventory != None:
        for item in protected_inventory:
            if item in required:
                required[item] = required[item] + protected_inventory[item]
            else:
                required[item] = protected_inventory[item]

    if cycle_budget != None:
        for item in cycle_budget:
            if item in required:
                required[item] = required[item] + cycle_budget[item]
            else:
                required[item] = cycle_budget[item]

    return required


def can_afford_cost(cost, protected_inventory=None, cycle_budget=None) -> bool:
    # Check live inventory against protected balances and one cycle budget.
    required = get_required_inventory(cost, protected_inventory, cycle_budget)

    if required == None:
        return False

    for item in required:
        if num_items(item) < required[item]:
            return False

    return True
