from cactus import farm_cactus_cycle
from carrots import farm_carrot_cycle
from farm_config import (
    CACTUS_REVERSE_SORT,
    POWER_TARGET,
)
from hay import farm_hay_cycle
from maze import farm_mazes, get_maze_substance_cost
from pumpkins import farm_pumpkin_cycle
from resource_costs import (
    can_afford_cost,
    get_planting_budget,
    get_required_inventory,
    get_top_hat_cost,
)
from sunflowers import farm_sunflower_cycle
from trees import farm_tree_cycle


POWER_LOW_WATERMARK = POWER_TARGET // 10
POWER_HIGH_WATERMARK = POWER_TARGET
POWER_OBSERVED_CONSUMPTION = 0
POWER_STOCKPILE_ESTABLISHED = False
POWER_REFILL_ACTIVE = False
NO_PROGRESS_LIMIT = 2
WAIT_DIAGNOSTIC_INTERVAL = 10
ACTION_NONE = "none"
ACTION_PRODUCER = "producer"
ACTION_WAIT = "wait"
ACTION_BLOCKED = "blocked"
LAST_ACTION_RESULT = (ACTION_NONE, False)
WAIT_ACTION_COUNT = 0


def get_cost_amount(cost, item) -> int:
    if item in cost:
        return cost[item]

    return 0


def set_action_result(action, succeeded) -> None:
    global LAST_ACTION_RESULT

    LAST_ACTION_RESULT = (action, succeeded)


def get_last_action_result():
    return LAST_ACTION_RESULT


def needs_item(cost, item) -> bool:
    return num_items(item) < get_cost_amount(cost, item)


def get_power_low_watermark() -> int:
    return POWER_LOW_WATERMARK + POWER_OBSERVED_CONSUMPTION


def get_power_target(cost) -> int:
    target = get_cost_amount(cost, Items.Power)

    if target < POWER_HIGH_WATERMARK:
        target = POWER_HIGH_WATERMARK

    return target + POWER_OBSERVED_CONSUMPTION


def is_power_stockpile_complete(cost) -> bool:
    if POWER_STOCKPILE_ESTABLISHED and not needs_item(cost, Items.Power):
        return True

    return num_items(Items.Power) >= get_power_target(cost)


def update_power_refill_state(cost) -> bool:
    # Preserve an established stockpile until the low watermark is crossed.
    global POWER_REFILL_ACTIVE
    global POWER_STOCKPILE_ESTABLISHED

    power_amount = num_items(Items.Power)
    power_target = get_power_target(cost)

    if not POWER_STOCKPILE_ESTABLISHED:
        if power_amount >= power_target:
            POWER_STOCKPILE_ESTABLISHED = True
            POWER_REFILL_ACTIVE = False
        else:
            POWER_REFILL_ACTIVE = True
        return POWER_REFILL_ACTIVE

    if POWER_REFILL_ACTIVE:
        if power_amount >= power_target:
            POWER_REFILL_ACTIVE = False
        return POWER_REFILL_ACTIVE

    if power_amount < get_power_low_watermark() or needs_item(cost, Items.Power):
        POWER_REFILL_ACTIVE = True

    return POWER_REFILL_ACTIVE


def add_protected_balance(protected_inventory, item, amount) -> None:
    if amount > 0:
        protected_inventory[item] = amount


def get_protected_inventory(cost, stage):
    # Protect only completed earlier stages while funding the current stage.
    protected_inventory = {}

    if stage != Items.Power and is_power_stockpile_complete(cost):
        add_protected_balance(
            protected_inventory,
            Items.Power,
            get_power_low_watermark(),
        )

    if stage != Items.Cactus and not (
        stage == Items.Weird_Substance and not needs_item(cost, Items.Cactus)
    ):
        if not needs_item(cost, Items.Cactus):
            add_protected_balance(
                protected_inventory,
                Items.Cactus,
                get_cost_amount(cost, Items.Cactus),
            )

    if stage != Items.Gold and not needs_item(cost, Items.Gold):
        add_protected_balance(
            protected_inventory,
            Items.Gold,
            get_cost_amount(cost, Items.Gold),
        )

    if stage not in (Items.Carrot, Items.Pumpkin, Items.Cactus):
        if (
            is_power_stockpile_complete(cost)
            and not needs_item(cost, Items.Cactus)
            and not needs_item(cost, Items.Gold)
            and not needs_item(cost, Items.Carrot)
        ):
            add_protected_balance(
                protected_inventory,
                Items.Carrot,
                get_cost_amount(cost, Items.Carrot),
            )

    if stage == Items.Hay and not needs_item(cost, Items.Wood):
        add_protected_balance(
            protected_inventory,
            Items.Wood,
            get_cost_amount(cost, Items.Wood),
        )

    return protected_inventory


def merge_costs(first_cost, second_cost):
    # Combine live budgets for mixed tree and bush rows.
    if first_cost == None or second_cost == None:
        return None

    merged = {}

    for item in first_cost:
        merged[item] = first_cost[item]

    for item in second_cost:
        if item in merged:
            merged[item] = merged[item] + second_cost[item]
        else:
            merged[item] = second_cost[item]

    return merged


def get_entity_cycle_budget(entity, width, height):
    return get_planting_budget(entity, width, height)


def get_tree_cycle_budget(width, height):
    tree_tiles = 0
    bush_tiles = 0

    for x in range(width):
        for y in range(height):
            if (x + y) % 2:
                tree_tiles += 1
            else:
                bush_tiles += 1

    tree_budget = get_entity_cycle_budget(Entities.Tree, tree_tiles, 1)
    bush_budget = get_entity_cycle_budget(Entities.Bush, bush_tiles, 1)
    return merge_costs(tree_budget, bush_budget)


def get_missing_input(cycle_budget, protected_inventory):
    required = get_required_inventory({}, protected_inventory, cycle_budget)

    if required == None:
        return None

    for item in required:
        if num_items(item) < required[item]:
            return item

    return None


def can_run_budget(cycle_budget, protected_inventory) -> bool:
    if cycle_budget == None:
        return False

    return can_afford_cost({}, protected_inventory, cycle_budget)


def can_run_sunflowers(cost, size, stage=None) -> bool:
    if stage == None:
        stage = Items.Power

    budget = get_entity_cycle_budget(Entities.Sunflower, size, size)
    return can_run_budget(budget, get_protected_inventory(cost, stage))


def can_run_carrots(cost, size, stage=None) -> bool:
    if stage == None:
        stage = Items.Carrot

    budget = get_entity_cycle_budget(Entities.Carrot, size, size)
    return can_run_budget(budget, get_protected_inventory(cost, stage))


def can_run_pumpkins(cost, size, stage=None) -> bool:
    if stage == None:
        stage = Items.Cactus

    budget = get_entity_cycle_budget(Entities.Pumpkin, size, size)
    return can_run_budget(budget, get_protected_inventory(cost, stage))


def can_run_cactus(cost, size, stage=None) -> bool:
    if stage == None:
        stage = Items.Cactus

    budget = get_entity_cycle_budget(Entities.Cactus, size, size)
    return can_run_budget(budget, get_protected_inventory(cost, stage))


def can_run_trees(cost, size, stage=None) -> bool:
    if stage == None:
        stage = Items.Wood

    budget = get_tree_cycle_budget(size, size)
    return can_run_budget(budget, get_protected_inventory(cost, stage))


def can_run_maze(cost) -> bool:
    maze_cost = get_maze_substance_cost()

    if maze_cost <= 0:
        return False

    gold_target = get_cost_amount(cost, Items.Gold)
    substance_reserve = get_cost_amount(cost, Items.Weird_Substance)
    return num_items(Items.Gold) < gold_target and num_items(Items.Weird_Substance) >= (
        maze_cost + substance_reserve
    )


def get_weird_substance_target(cost) -> int:
    # Fund one immediate maze and preserve any explicit final reserve.
    substance_reserve = get_cost_amount(cost, Items.Weird_Substance)
    if Items.Gold not in cost or num_items(Items.Gold) >= get_cost_amount(
        cost,
        Items.Gold,
    ):
        return substance_reserve

    maze_cost = get_maze_substance_cost()

    if maze_cost < 0:
        maze_cost = 0

    return maze_cost + substance_reserve


def run_cactus_action(cost, size, weird_substance_target=None) -> bool:
    if weird_substance_target == None:
        weird_substance_target = get_weird_substance_target(cost)

    return farm_cactus_cycle(
        0,
        0,
        size,
        size,
        CACTUS_REVERSE_SORT,
        weird_substance_target,
        0,
        True,
    )


def make_producer_result(succeeded, reason):
    # Keep failure details separate from the public boolean producer contract.
    return (succeeded, reason)


def has_dependency(dependency_path, item) -> bool:
    for path_item in dependency_path:
        if path_item == item:
            return True

    return False


def extend_dependency_path(dependency_path, item):
    extended_path = []

    for path_item in dependency_path:
        extended_path.append(path_item)

    extended_path.append(item)
    return extended_path


def get_operation_result(item, succeeded):
    if succeeded:
        return make_producer_result(True, "")

    return make_producer_result(
        False,
        "producer operation failed for " + str(item),
    )


def resolve_item_producer(item, cost, stage, dependency_path):
    # Resolve one finite production action while tracking the full path.
    if has_dependency(dependency_path, item):
        return make_producer_result(
            False,
            "dependency cycle at " + str(item),
        )

    if stage == None:
        stage = item

    path = extend_dependency_path(dependency_path, item)
    size = get_world_size()

    if item == Items.Hay:
        return get_operation_result(item, farm_hay_cycle())

    if item == Items.Wood:
        if can_run_trees(cost, size, stage):
            return get_operation_result(item, farm_tree_cycle())

        budget = get_tree_cycle_budget(size, size)
        protected_inventory = get_protected_inventory(cost, stage)
        missing_item = get_missing_input(budget, protected_inventory)
        if missing_item == None:
            return make_producer_result(
                False,
                "unavailable feedstock for " + str(item),
            )

        return resolve_item_producer(missing_item, cost, stage, path)

    if item == Items.Carrot:
        if can_run_carrots(cost, size, stage):
            return get_operation_result(item, farm_carrot_cycle())

        budget = get_entity_cycle_budget(Entities.Carrot, size, size)
        protected_inventory = get_protected_inventory(cost, stage)
        missing_item = get_missing_input(budget, protected_inventory)
        if missing_item == None:
            return make_producer_result(
                False,
                "unavailable feedstock for " + str(item),
            )

        return resolve_item_producer(missing_item, cost, stage, path)

    if item == Items.Pumpkin:
        if can_run_pumpkins(cost, size, stage):
            return get_operation_result(item, farm_pumpkin_cycle())

        budget = get_entity_cycle_budget(Entities.Pumpkin, size, size)
        protected_inventory = get_protected_inventory(cost, stage)
        missing_item = get_missing_input(budget, protected_inventory)
        if missing_item == None:
            return make_producer_result(
                False,
                "unavailable feedstock for " + str(item),
            )

        return resolve_item_producer(missing_item, cost, stage, path)

    if item == Items.Cactus:
        if can_run_cactus(cost, size, stage):
            return get_operation_result(
                item,
                run_cactus_action(
                    cost,
                    size,
                    get_weird_substance_target(cost),
                ),
            )

        budget = get_entity_cycle_budget(Entities.Cactus, size, size)
        protected_inventory = get_protected_inventory(cost, stage)
        missing_item = get_missing_input(budget, protected_inventory)
        if missing_item == None:
            return make_producer_result(
                False,
                "unavailable feedstock for " + str(item),
            )

        return resolve_item_producer(missing_item, cost, stage, path)

    if item == Items.Power:
        if can_run_sunflowers(cost, size, stage):
            return get_operation_result(item, farm_sunflower_cycle())

        budget = get_entity_cycle_budget(Entities.Sunflower, size, size)
        protected_inventory = get_protected_inventory(cost, stage)
        missing_item = get_missing_input(budget, protected_inventory)
        if missing_item == None:
            return make_producer_result(
                False,
                "unavailable feedstock for " + str(item),
            )

        return resolve_item_producer(missing_item, cost, stage, path)

    if item == Items.Weird_Substance:
        weird_substance_target = get_weird_substance_target(cost)
        if num_items(Items.Weird_Substance) >= weird_substance_target:
            return make_producer_result(
                False,
                "Weird Substance target already satisfied",
            )

        if num_items(Items.Fertilizer) <= 0:
            return make_producer_result(
                False,
                "missing fertilizer for Weird Substance",
            )

        if can_run_cactus(cost, size, stage):
            return get_operation_result(
                item,
                run_cactus_action(cost, size, weird_substance_target),
            )

        budget = get_entity_cycle_budget(Entities.Cactus, size, size)
        protected_inventory = get_protected_inventory(cost, stage)
        missing_item = get_missing_input(budget, protected_inventory)
        if missing_item == None:
            return make_producer_result(
                False,
                "unavailable feedstock for " + str(item),
            )

        return resolve_item_producer(missing_item, cost, stage, path)

    if item == Items.Gold:
        if can_run_maze(cost):
            return get_operation_result(
                item,
                farm_mazes(
                    get_cost_amount(cost, Items.Gold),
                    get_cost_amount(cost, Items.Weird_Substance),
                ),
            )

        if num_items(Items.Fertilizer) > 0:
            return resolve_item_producer(
                Items.Weird_Substance,
                cost,
                stage,
                path,
            )

        return make_producer_result(
            False,
            "missing fertilizer for Gold dependency",
        )

    return make_producer_result(
        False,
        "no producer for required item " + str(item),
    )


def run_item_producer(item, cost, blocked_item=None, stage=None) -> bool:
    # Preserve the boolean API while reporting structured resolver failures.
    dependency_path = []

    if blocked_item != None:
        dependency_path.append(blocked_item)

    result = resolve_item_producer(item, cost, stage, dependency_path)

    if not result[0]:
        quick_print("Top Hat producer blocked: " + result[1])

    return result[0]


def run_selected_producer(item, cost) -> bool:
    # Keep producer failures visible to the next planner iteration.
    result = run_item_producer(item, cost)
    set_action_result(ACTION_PRODUCER, result)

    if not result:
        quick_print("Top Hat producer failed for " + str(item))

    return result


def run_fallback_action(cost, blocked_item) -> bool:
    # Keep useful independent work moving after a blocked dependency.
    fallback_items = [Items.Wood, Items.Hay, Items.Carrot]

    for item in fallback_items:
        if item == blocked_item or not needs_item(cost, item):
            continue

        if run_selected_producer(item, cost):
            return True

    return False


def run_required_action(item, cost) -> bool:
    if run_selected_producer(item, cost):
        return True

    return run_fallback_action(cost, item)


def should_wait_for_fertilizer(cost) -> bool:
    # Wait only for a Gold dependency that can become maze-fundable.
    if not needs_item(cost, Items.Gold):
        return False

    if get_maze_substance_cost() <= 0 or can_run_maze(cost):
        return False

    return num_items(Items.Fertilizer) <= 0


def run_wait_action() -> bool:
    # Advance time once and rate-limit unattended wait diagnostics.
    global WAIT_ACTION_COUNT

    do_a_flip()
    WAIT_ACTION_COUNT += 1
    set_action_result(ACTION_WAIT, True)

    if WAIT_ACTION_COUNT == 1 or WAIT_ACTION_COUNT % WAIT_DIAGNOSTIC_INTERVAL == 0:
        quick_print("Top Hat planner waiting for fertilizer")

    return True


def perform_next_action(cost) -> bool:
    # Select one bounded action using current protected balances.
    if update_power_refill_state(cost):
        return run_required_action(Items.Power, cost)

    if needs_item(cost, Items.Cactus) or needs_item(cost, Items.Weird_Substance):
        if needs_item(cost, Items.Cactus):
            return run_required_action(Items.Cactus, cost)

        return run_required_action(Items.Weird_Substance, cost)

    if needs_item(cost, Items.Gold):
        if run_required_action(Items.Gold, cost):
            return True

        if should_wait_for_fertilizer(cost):
            return run_wait_action()

        return False

    if (
        is_power_stockpile_complete(cost)
        and not needs_item(cost, Items.Cactus)
        and not needs_item(cost, Items.Gold)
        and needs_item(cost, Items.Carrot)
    ):
        return run_required_action(Items.Carrot, cost)

    if needs_item(cost, Items.Wood):
        return run_required_action(Items.Wood, cost)

    if needs_item(cost, Items.Hay):
        return run_required_action(Items.Hay, cost)

    set_action_result(ACTION_BLOCKED, False)
    quick_print("Top Hat planner has no selected action")
    return False


def get_inventory_snapshot(cost):
    # Track all production resources plus any live-cost keys.
    snapshot = []
    tracked_items = [
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Pumpkin,
        Items.Cactus,
        Items.Power,
        Items.Weird_Substance,
        Items.Gold,
        Items.Fertilizer,
    ]

    for item in tracked_items:
        snapshot.append((item, num_items(item)))

    for item in cost:
        if item not in tracked_items:
            snapshot.append((item, num_items(item)))

    return snapshot


def get_snapshot_amount(snapshot, item) -> int:
    for snapshot_item, amount in snapshot:
        if snapshot_item == item:
            return amount

    return 0


def record_power_consumption(before, after) -> None:
    # Retain the largest observed net power drop as a future reserve.
    global POWER_OBSERVED_CONSUMPTION

    before_power = get_snapshot_amount(before, Items.Power)
    after_power = get_snapshot_amount(after, Items.Power)
    consumption = before_power - after_power

    if consumption > POWER_OBSERVED_CONSUMPTION:
        POWER_OBSERVED_CONSUMPTION = consumption


def farm_top_hat() -> bool:
    # Reconcile live costs one bounded action at a time before unlocking.
    global WAIT_ACTION_COUNT
    global POWER_OBSERVED_CONSUMPTION
    global POWER_REFILL_ACTIVE
    global POWER_STOCKPILE_ESTABLISHED

    POWER_OBSERVED_CONSUMPTION = 0
    POWER_REFILL_ACTIVE = False
    POWER_STOCKPILE_ESTABLISHED = False

    if num_unlocked(Unlocks.Top_Hat) > 0:
        return True

    cost = get_top_hat_cost()

    if cost == None:
        quick_print("Top Hat cost unavailable")
        return False

    update_power_refill_state(cost)
    no_progress_count = 0
    WAIT_ACTION_COUNT = 0

    while True:
        cost = get_top_hat_cost()

        if cost == None:
            quick_print("Top Hat cost unavailable")
            return False

        if can_afford_cost(cost):
            if unlock(Unlocks.Top_Hat):
                return True

            quick_print("Top Hat unlock failed")
            return False

        before = get_inventory_snapshot(cost)
        set_action_result(ACTION_NONE, False)
        perform_next_action(cost)

        refreshed_cost = get_top_hat_cost()
        if refreshed_cost == None:
            quick_print("Top Hat cost unavailable")
            return False

        after = get_inventory_snapshot(refreshed_cost)
        record_power_consumption(before, after)

        if LAST_ACTION_RESULT[0] == ACTION_WAIT:
            no_progress_count = 0
        elif before == after:
            no_progress_count += 1
        else:
            no_progress_count = 0

        if no_progress_count >= NO_PROGRESS_LIMIT:
            quick_print("Top Hat planner made no progress")
            return False
