#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise Top Hat policy, live resampling, safeguards, and producer routing."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import top_hat  # noqa: E402
import resource_costs  # noqa: E402


class Items:
    Hay = "Hay"
    Wood = "Wood"
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
    Cactus = "Cactus"
    Power = "Power"
    Weird_Substance = "Weird Substance"
    Gold = "Gold"
    Fertilizer = "Fertilizer"


class Entities:
    Tree = "Tree"
    Bush = "Bush"
    Carrot = "Carrot"
    Pumpkin = "Pumpkin"
    Cactus = "Cactus"
    Sunflower = "Sunflower"


class Unlocks:
    Top_Hat = "Top Hat"


top_hat.Items = Items
top_hat.Entities = Entities
top_hat.Unlocks = Unlocks
REAL_PERFORM_NEXT_ACTION = top_hat.perform_next_action
REAL_RUN_ITEM_PRODUCER = top_hat.run_item_producer
REAL_CAN_RUN_CACTUS = top_hat.can_run_cactus
REAL_CAN_RUN_SUNFLOWERS = top_hat.can_run_sunflowers
REAL_GET_ENTITY_CYCLE_BUDGET = top_hat.get_entity_cycle_budget
REAL_GET_TREE_CYCLE_BUDGET = top_hat.get_tree_cycle_budget
inventory = {}
messages = []
unlock_calls = []


def reset_inventory() -> None:
    inventory.clear()
    for item in (
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Pumpkin,
        Items.Cactus,
        Items.Power,
        Items.Weird_Substance,
        Items.Gold,
        Items.Fertilizer,
    ):
        inventory[item] = 0

    messages.clear()
    unlock_calls.clear()
    top_hat.num_items = lambda item: inventory[item]
    resource_costs.num_items = lambda item: inventory[item]
    top_hat.quick_print = lambda message: messages.append(message)
    top_hat.num_unlocked = lambda unlock: 0
    top_hat.unlock = lambda unlock: unlock_calls.append(unlock) or True
    top_hat.get_world_size = lambda: 4
    top_hat.POWER_LOW_WATERMARK = 10
    top_hat.POWER_HIGH_WATERMARK = 20
    top_hat.POWER_OBSERVED_CONSUMPTION = 0
    top_hat.POWER_STOCKPILE_ESTABLISHED = False
    top_hat.POWER_REFILL_ACTIVE = False


def test_already_unlocked_returns_immediately() -> None:
    reset_inventory()
    top_hat.num_unlocked = lambda unlock: 1
    top_hat.get_top_hat_cost = lambda: (_ for _ in ()).throw(
        AssertionError("already-unlocked state queried costs")
    )

    if not top_hat.farm_top_hat():
        raise AssertionError("already-unlocked state reported failure")

    if unlock_calls:
        raise AssertionError("already-unlocked state called unlock")


def test_empty_cost_stops_visibly() -> None:
    reset_inventory()
    top_hat.get_top_hat_cost = lambda: None

    if top_hat.farm_top_hat():
        raise AssertionError("empty Top Hat cost reported success")

    if not messages:
        raise AssertionError("empty Top Hat cost was not reported")

    if unlock_calls:
        raise AssertionError("empty Top Hat cost called unlock")


def test_dynamic_costs_resample_and_allow_overshoot() -> None:
    reset_inventory()
    cost_calls = []

    def live_cost():
        cost_calls.append(inventory[Items.Wood])
        if len(cost_calls) < 4:
            return {Items.Wood: 2}

        return {Items.Wood: 4}

    top_hat.get_top_hat_cost = live_cost

    def produce_wood(cost) -> bool:
        inventory[Items.Wood] += 3
        return True

    top_hat.perform_next_action = produce_wood
    if not top_hat.farm_top_hat():
        raise AssertionError("dynamic-cost planner did not unlock")

    if inventory[Items.Wood] != 6:
        raise AssertionError("planner did not preserve an overshooting production cycle")

    if len(cost_calls) < 5:
        raise AssertionError("planner did not resample live costs after its action")

    if len(unlock_calls) != 1:
        raise AssertionError("dynamic-cost planner unlocked an unexpected number of times")


def test_no_progress_stops_after_repeated_action() -> None:
    reset_inventory()
    top_hat.get_top_hat_cost = lambda: {Items.Wood: 2}
    action_calls = []

    def no_progress(cost) -> bool:
        action_calls.append(cost)
        return False

    top_hat.perform_next_action = no_progress
    if top_hat.farm_top_hat():
        raise AssertionError("no-progress planner reported success")

    if len(action_calls) != top_hat.NO_PROGRESS_LIMIT:
        raise AssertionError("no-progress planner did not stop at its limit")

    if "no progress" not in messages[-1].lower():
        raise AssertionError("no-progress planner did not report its stop reason")


def test_unlock_failure_is_called_once() -> None:
    reset_inventory()
    inventory[Items.Wood] = 5
    top_hat.get_top_hat_cost = lambda: {Items.Wood: 2}
    top_hat.unlock = lambda unlock: unlock_calls.append(unlock) or False

    if top_hat.farm_top_hat():
        raise AssertionError("unlock failure reported success")

    if len(unlock_calls) != 1:
        raise AssertionError("unlock failure retried the unlock")


def test_policy_priority() -> None:
    reset_inventory()
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    cost = {
        Items.Hay: 1,
        Items.Wood: 1,
        Items.Carrot: 1,
        Items.Pumpkin: 1,
        Items.Cactus: 1,
        Items.Power: 1,
        Items.Weird_Substance: 1,
        Items.Gold: 1,
    }
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True

    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Power:
        raise AssertionError("power was not the first missing production target")

    inventory[Items.Power] = 20
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Cactus:
        raise AssertionError("cactus was not prioritized after power")

    inventory[Items.Cactus] = 1
    inventory[Items.Gold] = 1
    inventory[Items.Weird_Substance] = 1
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Carrot:
        raise AssertionError("carrots were not deferred until prerequisites completed")


def test_power_reaches_high_watermark_without_live_power_cost() -> None:
    reset_inventory()
    cost = {Items.Wood: 1}
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True

    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Power:
        raise AssertionError("low power watermark did not trigger replenishment")

    inventory[Items.Power] = 10
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Power:
        raise AssertionError("power did not refill from low to high watermark")

    inventory[Items.Power] = 20
    top_hat.perform_next_action(cost)
    if actions[-1] != Items.Wood:
        raise AssertionError("planner did not leave power mode at the high watermark")


def test_initial_power_stockpile_precedes_later_stages() -> None:
    reset_inventory()
    inventory[Items.Power] = 15
    top_hat.get_top_hat_cost = lambda: {Items.Cactus: 1}
    actions = []

    def produce(item, policy) -> bool:
        actions.append(item)
        if item == Items.Power:
            inventory[Items.Power] = 20
        else:
            inventory[item] = 1
        return True

    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    top_hat.run_item_producer = produce

    if not top_hat.farm_top_hat():
        raise AssertionError("initial power stockpile did not complete")

    if actions[:2] != [Items.Power, Items.Cactus]:
        raise AssertionError(
            "planner advanced before establishing the initial power stockpile: " + str(actions)
        )


def test_established_power_between_watermarks_uses_required_resource() -> None:
    reset_inventory()
    inventory[Items.Power] = 15
    top_hat.POWER_STOCKPILE_ESTABLISHED = True
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION

    if not top_hat.perform_next_action({Items.Wood: 1}):
        raise AssertionError("planner did not select the required resource")

    if actions[-1] != Items.Wood:
        raise AssertionError("established power between watermarks triggered a sunflower cycle")


def test_power_refill_stays_active_until_high_watermark() -> None:
    reset_inventory()
    top_hat.POWER_STOCKPILE_ESTABLISHED = True
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    cost = {Items.Wood: 1}

    inventory[Items.Power] = 9
    if not top_hat.perform_next_action(cost):
        raise AssertionError("low power did not start refill mode")
    if not top_hat.POWER_REFILL_ACTIVE:
        raise AssertionError("low power did not activate refill mode")

    inventory[Items.Power] = 15
    if not top_hat.perform_next_action(cost):
        raise AssertionError("refill mode did not continue below the high watermark")
    if actions[-1] != Items.Power:
        raise AssertionError("refill mode stopped between the watermarks")

    inventory[Items.Power] = 20
    if not top_hat.perform_next_action(cost):
        raise AssertionError("planner did not resume later-stage work at the target")
    if top_hat.POWER_REFILL_ACTIVE:
        raise AssertionError("refill mode remained active at the high watermark")
    if actions[-1] != Items.Wood:
        raise AssertionError("planner did not select later-stage work at the target")


def test_fertilizer_wait_does_not_restart_power_refill() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    top_hat.POWER_STOCKPILE_ESTABLISHED = True
    top_hat.get_maze_substance_cost = lambda: 5
    actions = []

    def produce(item, policy) -> bool:
        actions.append(item)
        return item == Items.Gold

    top_hat.run_item_producer = produce
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    top_hat.do_a_flip = lambda: inventory.__setitem__(Items.Power, 19)

    if not top_hat.run_wait_action():
        raise AssertionError("bounded fertilizer wait failed")
    if not top_hat.perform_next_action({Items.Gold: 1}):
        raise AssertionError("planner did not resume Gold work after the wait")

    if actions[-1] != Items.Gold:
        raise AssertionError("fertilizer wait caused a sunflower cycle above the low watermark")


def test_live_power_cost_overrides_watermark_policy() -> None:
    reset_inventory()
    inventory[Items.Power] = 22
    top_hat.POWER_STOCKPILE_ESTABLISHED = True
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION

    if not top_hat.perform_next_action({Items.Power: 25, Items.Wood: 1}):
        raise AssertionError("explicit live Power requirement did not trigger refill")

    if actions[-1] != Items.Power:
        raise AssertionError("planner ignored an unmet explicit Power cost")


def test_power_watermarks_adjust_from_observed_consumption() -> None:
    reset_inventory()
    cost = {Items.Power: 5}
    before = [(Items.Power, 30)]
    after = [(Items.Power, 22)]

    top_hat.record_power_consumption(before, after)

    if top_hat.get_power_low_watermark() != 18:
        raise AssertionError("low power watermark ignored observed consumption")

    if top_hat.get_power_target(cost) != 28:
        raise AssertionError("high power watermark ignored observed consumption")

    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True
    inventory[Items.Power] = 17
    top_hat.perform_next_action(cost)

    if actions[-1] != Items.Power:
        raise AssertionError("observed consumption did not trigger replenishment")


def test_tree_budget_counts_checkerboard_tiles() -> None:
    reset_inventory()
    original_budget = top_hat.get_planting_budget
    calls = []

    def record_budget(entity, width, height):
        calls.append((entity, width, height))
        return {Items.Wood: width * height}

    top_hat.get_planting_budget = record_budget
    budget = top_hat.get_tree_cycle_budget(4, 3)
    top_hat.get_planting_budget = original_budget

    if budget != {Items.Wood: 12}:
        raise AssertionError(f"tree budget counted non-checkerboard tiles: {budget}")

    if calls != [(Entities.Tree, 6, 1), (Entities.Bush, 6, 1)]:
        raise AssertionError(f"checkerboard geometry was not passed to costs: {calls}")


def test_protected_balance_plus_cycle_budget() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    inventory[Items.Cactus] = 3
    inventory[Items.Gold] = 2
    inventory[Items.Wood] = 2
    top_hat.get_planting_budget = lambda entity, width, height: {Items.Wood: 2}
    cost = {
        Items.Power: 1,
        Items.Cactus: 3,
        Items.Gold: 2,
        Items.Carrot: 999,
        Items.Wood: 999,
    }

    if not top_hat.can_run_carrots(cost, 2):
        raise AssertionError("stage-protected balance plus cycle budget was rejected")

    inventory[Items.Wood] = 1
    if top_hat.can_run_carrots(cost, 2):
        raise AssertionError("underfunded cycle budget was accepted")


def test_missing_fertilizer_reports_wait() -> None:
    reset_inventory()
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    top_hat.get_world_size = lambda: 4

    if top_hat.run_item_producer(Items.Weird_Substance, {Items.Weird_Substance: 2}):
        raise AssertionError("missing fertilizer reported Weird Substance progress")

    if "fertilizer" not in messages[-1].lower():
        raise AssertionError("missing fertilizer did not identify its feedstock")


def test_gold_and_cactus_receive_live_policy() -> None:
    reset_inventory()
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    inventory[Items.Weird_Substance] = 6
    inventory[Items.Fertilizer] = 1
    top_hat.get_maze_substance_cost = lambda: 5
    maze_calls = []
    cactus_calls = []
    top_hat.farm_mazes = lambda gold, reserve: maze_calls.append((gold, reserve)) or True
    top_hat.farm_cactus_cycle = lambda *args: cactus_calls.append(args) or True

    cost = {Items.Gold: 10, Items.Weird_Substance: 1}
    if not top_hat.run_item_producer(Items.Gold, cost):
        raise AssertionError("funded maze action reported failure")

    if maze_calls != [(10, 1)]:
        raise AssertionError(f"maze did not receive live targets: {maze_calls}")

    top_hat.can_run_cactus = lambda *args: True
    if not top_hat.run_item_producer(Items.Cactus, cost):
        raise AssertionError("funded cactus action reported failure")

    if cactus_calls[-1][5] != 6 or cactus_calls[-1][7] is not True:
        raise AssertionError("cactus did not receive maze-funded Weird Substance policy")


def test_cactus_cycle_ignores_missing_final_cactus_balance() -> None:
    reset_inventory()
    top_hat.can_run_cactus = REAL_CAN_RUN_CACTUS
    inventory[Items.Hay] = 1
    inventory[Items.Wood] = 1
    inventory[Items.Carrot] = 1
    inventory[Items.Pumpkin] = 1
    inventory[Items.Gold] = 1
    inventory[Items.Power] = 20
    cactus_calls = []

    def cactus_budget(entity, width, height):
        if entity == Entities.Cactus:
            return {Items.Pumpkin: 1}

        return {}

    top_hat.get_entity_cycle_budget = cactus_budget
    top_hat.farm_cactus_cycle = lambda *args: cactus_calls.append(args) or True
    cost = {
        Items.Hay: 1,
        Items.Wood: 1,
        Items.Carrot: 1,
        Items.Cactus: 10,
        Items.Gold: 1,
    }

    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    if not top_hat.perform_next_action(cost):
        raise AssertionError("funded cactus cycle was blocked by its final output")

    if len(cactus_calls) != 1:
        raise AssertionError("cactus producer was not called for a funded cycle")


def test_gold_plans_positive_weird_substance_target() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    inventory[Items.Fertilizer] = 1
    top_hat.get_maze_substance_cost = lambda: 5
    top_hat.can_run_cactus = lambda *args: True
    cactus_calls = []
    top_hat.farm_cactus_cycle = lambda *args: cactus_calls.append(args) or True

    if not top_hat.run_item_producer(Items.Gold, {Items.Gold: 10}):
        raise AssertionError("Gold dependency planning reported failure")

    if len(cactus_calls) != 1:
        raise AssertionError("Gold planning did not request Weird Substance production")

    if cactus_calls[0][5] != 5:
        raise AssertionError(
            "Weird Substance target did not use the immediate maze cost: " + str(cactus_calls[0][5])
        )


def test_gold_resamples_after_weird_substance_production() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    inventory[Items.Fertilizer] = 1
    top_hat.get_maze_substance_cost = lambda: 5
    top_hat.can_run_cactus = lambda *args: True
    cactus_calls = []
    maze_calls = []

    def produce_weird_substance(*args):
        cactus_calls.append(args)
        inventory[Items.Weird_Substance] += 5
        return True

    top_hat.farm_cactus_cycle = produce_weird_substance
    top_hat.farm_mazes = lambda gold, reserve: maze_calls.append((gold, reserve)) or True
    cost = {Items.Gold: 10}

    if not top_hat.run_item_producer(Items.Gold, cost):
        raise AssertionError("Weird Substance production reported failure")

    if maze_calls:
        raise AssertionError("Gold planning spent maze inputs before resampling")

    if not top_hat.run_item_producer(Items.Gold, cost):
        raise AssertionError("resampled maze action reported failure")

    if maze_calls != [(10, 0)]:
        raise AssertionError("Gold planning did not resample after Weird Substance production")


def test_weird_substance_action_stops_at_immediate_target() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    inventory[Items.Fertilizer] = 1
    inventory[Items.Weird_Substance] = 5
    top_hat.get_maze_substance_cost = lambda: 5
    top_hat.can_run_cactus = lambda *args: True
    cactus_calls = []
    top_hat.farm_cactus_cycle = lambda *args: cactus_calls.append(args) or True

    if top_hat.run_item_producer(Items.Weird_Substance, {}):
        raise AssertionError("satisfied Weird Substance target reported production")

    if cactus_calls:
        raise AssertionError("cactus action continued after Weird Substance target")


def test_gold_complete_does_not_request_weird_substance() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    inventory[Items.Gold] = 10
    inventory[Items.Fertilizer] = 1
    top_hat.can_run_cactus = lambda *args: True
    cactus_calls = []
    top_hat.farm_cactus_cycle = lambda *args: cactus_calls.append(args) or True
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION

    cost = {Items.Gold: 10, Items.Cactus: 1}
    top_hat.run_item_producer(Items.Cactus, cost)

    if cactus_calls[0][5] != 0:
        raise AssertionError("completed Gold stage requested Weird Substance")

    cactus_calls.clear()
    if top_hat.run_item_producer(Items.Weird_Substance, cost):
        raise AssertionError("completed Gold stage produced Weird Substance")

    if cactus_calls:
        raise AssertionError("completed Gold stage invoked the cactus action")


def test_fertilizer_wait_resumes_planner() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    top_hat.get_top_hat_cost = lambda: {Items.Gold: 10}
    top_hat.get_maze_substance_cost = lambda: 5
    top_hat.can_run_cactus = lambda *args: True
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    waits = []

    def advance_time() -> None:
        waits.append(True)
        if len(waits) == 3:
            inventory[Items.Fertilizer] = 1

    top_hat.do_a_flip = advance_time
    top_hat.farm_cactus_cycle = lambda *args: (
        inventory.__setitem__(Items.Weird_Substance, 5) or True
    )
    top_hat.farm_mazes = lambda gold, reserve: inventory.__setitem__(Items.Gold, gold) or True

    if not top_hat.farm_top_hat():
        raise AssertionError("planner did not resume after fertilizer arrived")

    if len(waits) != 3:
        raise AssertionError("planner did not use bounded fertilizer waits")
    if len(unlock_calls) != 1:
        raise AssertionError("planner did not reach the unlock after waiting")


def test_wait_diagnostics_are_rate_limited() -> None:
    reset_inventory()
    top_hat.WAIT_ACTION_COUNT = 0
    top_hat.do_a_flip = lambda: None

    for _ in range(21):
        top_hat.run_wait_action()

    if len(messages) != 3:
        raise AssertionError("fertilizer wait diagnostics were not rate-limited")


def test_power_boundary_uses_adaptive_target() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    top_hat.POWER_OBSERVED_CONSUMPTION = 8
    actions = []
    top_hat.run_item_producer = lambda item, policy: actions.append(item) or True

    top_hat.perform_next_action({Items.Wood: 1})

    if actions[-1] != Items.Power:
        raise AssertionError("power at the static target did not reach the adaptive target")


def test_adaptive_power_target_runs_full_cycle() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    top_hat.POWER_OBSERVED_CONSUMPTION = 8
    top_hat.can_run_sunflowers = lambda *args: True
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    cycle_calls = []
    top_hat.farm_sunflower_cycle = lambda: cycle_calls.append(True) or True

    if not top_hat.perform_next_action({Items.Wood: 1}):
        raise AssertionError("adaptive power cycle reported failure")

    if len(cycle_calls) != 1:
        raise AssertionError("adaptive power target did not run a sunflower cycle")


def test_direct_dependency_cycle_stops_cleanly() -> None:
    reset_inventory()
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    top_hat.get_entity_cycle_budget = lambda entity, width, height: {Items.Carrot: 1}

    if top_hat.run_item_producer(Items.Carrot, {Items.Hay: 1}):
        raise AssertionError("direct dependency cycle reported progress")

    if "cycle" not in messages[-1].lower():
        raise AssertionError("direct dependency cycle was not reported")


def test_multi_item_dependency_cycle_stops_cleanly() -> None:
    reset_inventory()
    top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
    top_hat.get_entity_cycle_budget = lambda entity, width, height: {Items.Wood: 1}
    top_hat.get_tree_cycle_budget = lambda width, height: {Items.Carrot: 1}

    if top_hat.run_item_producer(Items.Carrot, {Items.Hay: 1}):
        raise AssertionError("multi-item dependency cycle reported progress")

    if "cycle" not in messages[-1].lower():
        raise AssertionError("multi-item dependency cycle was not reported")


def test_blocked_dependency_allows_unrelated_resource_work() -> None:
    reset_inventory()
    inventory[Items.Power] = 20
    actions = []

    def produce(item, policy) -> bool:
        actions.append(item)
        return item == Items.Wood

    top_hat.run_item_producer = produce
    cost = {Items.Cactus: 1, Items.Wood: 1}
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION

    if not top_hat.perform_next_action(cost):
        raise AssertionError("unrelated resource work did not make progress")

    if actions != [Items.Cactus, Items.Wood]:
        raise AssertionError("planner did not fall back from the blocked dependency")


def test_planner_simulation_matches_live_top_hat_cost_shape() -> None:
    simulator = PlannerSimulation()
    required_items = (
        Items.Hay,
        Items.Wood,
        Items.Carrot,
        Items.Cactus,
        Items.Gold,
    )
    excluded_items = (
        Items.Power,
        Items.Weird_Substance,
        Items.Pumpkin,
        Items.Fertilizer,
    )

    for item in required_items:
        if item not in simulator.top_hat_cost:
            raise AssertionError("simulation omitted live Top Hat cost item " + str(item))

    for item in excluded_items:
        if item in simulator.top_hat_cost:
            raise AssertionError("simulation added non-cost item " + str(item))


class PlannerSimulation:
    def __init__(self) -> None:
        self.inventory = {
            Items.Hay: 0,
            Items.Wood: 0,
            Items.Carrot: 0,
            Items.Pumpkin: 0,
            Items.Cactus: 0,
            Items.Power: 5,
            Items.Weird_Substance: 0,
            Items.Gold: 0,
            Items.Fertilizer: 0,
        }
        self.top_hat_cost = {
            Items.Cactus: 2,
            Items.Gold: 8,
            Items.Carrot: 3,
            Items.Wood: 2,
            Items.Hay: 4,
        }
        self.entity_costs = {
            Entities.Carrot: {Items.Hay: 1},
            Entities.Pumpkin: {Items.Carrot: 1},
            Entities.Cactus: {Items.Pumpkin: 1},
            Entities.Sunflower: {Items.Carrot: 1},
            Entities.Tree: {Items.Hay: 1},
            Entities.Bush: {Items.Hay: 1},
        }
        self.actions = []
        self.messages = []
        self.unlock_calls = 0
        self.wait_count = 0
        self.protection_checks = 0
        self.protected_snapshots = []
        self.power_after_actions = []
        self.consume_protected_balance = False
        self.unlocked = False

    def install(self) -> None:
        resource_costs.Items = Items
        resource_costs.Unlocks = Unlocks
        top_hat.num_items = self.num_items
        resource_costs.num_items = self.num_items
        resource_costs.get_cost = self.get_cost
        resource_costs.quick_print = self.record_message
        top_hat.quick_print = self.record_message
        top_hat.get_world_size = lambda: 2
        top_hat.get_maze_substance_cost = lambda: 8
        top_hat.get_top_hat_cost = resource_costs.get_top_hat_cost
        top_hat.get_planting_budget = resource_costs.get_planting_budget
        top_hat.can_run_cactus = REAL_CAN_RUN_CACTUS
        top_hat.can_run_sunflowers = REAL_CAN_RUN_SUNFLOWERS
        top_hat.get_entity_cycle_budget = REAL_GET_ENTITY_CYCLE_BUDGET
        top_hat.get_tree_cycle_budget = REAL_GET_TREE_CYCLE_BUDGET
        top_hat.num_unlocked = self.num_unlocked
        top_hat.unlock = self.unlock
        top_hat.do_a_flip = self.advance_time
        top_hat.farm_hay_cycle = self.farm_hay_cycle
        top_hat.farm_carrot_cycle = self.farm_carrot_cycle
        top_hat.farm_pumpkin_cycle = self.farm_pumpkin_cycle
        top_hat.farm_cactus_cycle = self.farm_cactus_cycle
        top_hat.farm_sunflower_cycle = self.farm_sunflower_cycle
        top_hat.farm_tree_cycle = self.farm_tree_cycle
        top_hat.farm_mazes = self.farm_mazes
        top_hat.POWER_LOW_WATERMARK = 10
        top_hat.POWER_HIGH_WATERMARK = 20
        top_hat.POWER_OBSERVED_CONSUMPTION = 0
        top_hat.POWER_STOCKPILE_ESTABLISHED = False
        top_hat.POWER_REFILL_ACTIVE = False
        top_hat.run_item_producer = REAL_RUN_ITEM_PRODUCER
        top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION

    def num_items(self, item):
        return self.inventory[item]

    def get_cost(self, target):
        if target == Unlocks.Top_Hat:
            return self.top_hat_cost

        return self.entity_costs.get(target)

    def num_unlocked(self, unlock) -> int:
        if unlock == Unlocks.Top_Hat and self.unlocked:
            return 1

        return 0

    def record_message(self, message) -> None:
        self.messages.append(message)

    def record_action(self, action) -> None:
        self.actions.append(action)

    def capture_protected(self, stage):
        current_protection = top_hat.get_protected_inventory(self.top_hat_cost, stage)
        protected = {}

        for item in current_protection:
            protected[item] = current_protection[item]

        self.protected_snapshots.append((stage, protected))
        self.protection_checks += 1
        return protected

    def check_protected(self, protected) -> None:
        for item in protected:
            if self.inventory[item] < protected[item]:
                raise AssertionError("protected balance was consumed for " + str(item))

    def finish_action(self) -> None:
        self.power_after_actions.append((self.actions[-1], self.inventory[Items.Power]))

    def advance_time(self) -> None:
        self.record_action("wait")
        self.wait_count += 1
        self.inventory[Items.Power] -= 1

        if self.wait_count == 2:
            self.inventory[Items.Fertilizer] = 1
        self.finish_action()

    def farm_hay_cycle(self) -> bool:
        protected = self.capture_protected(Items.Hay)
        self.record_action("hay")
        self.inventory[Items.Hay] += 4
        self.check_protected(protected)
        self.finish_action()
        return True

    def farm_carrot_cycle(self) -> bool:
        if self.inventory[Items.Hay] < 4:
            return False

        protected = self.capture_protected(Items.Carrot)
        self.record_action("carrot")
        self.inventory[Items.Hay] -= 4
        self.inventory[Items.Carrot] += 4
        self.check_protected(protected)
        self.finish_action()
        return True

    def farm_pumpkin_cycle(self) -> bool:
        if self.inventory[Items.Carrot] < 4:
            return False

        protected = self.capture_protected(Items.Pumpkin)
        self.record_action("pumpkin")
        self.inventory[Items.Carrot] -= 4
        self.inventory[Items.Pumpkin] += 4
        self.check_protected(protected)
        self.finish_action()
        return True

    def farm_cactus_cycle(self, *args) -> bool:
        if self.inventory[Items.Pumpkin] < 4:
            return False

        protected = self.capture_protected(Items.Cactus)
        self.record_action("cactus")
        self.inventory[Items.Pumpkin] -= 4
        self.inventory[Items.Cactus] += 4

        weird_target = args[5]
        if (
            self.inventory[Items.Fertilizer] > 0
            and self.inventory[Items.Weird_Substance] < weird_target
        ):
            self.inventory[Items.Fertilizer] -= 1
            self.inventory[Items.Weird_Substance] += 8

        self.check_protected(protected)
        self.finish_action()
        return True

    def farm_sunflower_cycle(self) -> bool:
        if self.inventory[Items.Carrot] < 4:
            return False

        protected = self.capture_protected(Items.Power)
        self.record_action("power")
        self.inventory[Items.Carrot] -= 4
        self.inventory[Items.Power] += 16
        self.check_protected(protected)
        self.finish_action()
        return True

    def farm_tree_cycle(self) -> bool:
        if self.inventory[Items.Hay] < 4:
            return False

        protected = self.capture_protected(Items.Wood)
        self.record_action("wood")
        self.inventory[Items.Hay] -= 4
        if self.consume_protected_balance:
            self.inventory[Items.Power] = protected[Items.Power] - 1
        self.inventory[Items.Wood] += 4
        self.check_protected(protected)
        self.finish_action()
        return True

    def farm_mazes(self, gold_target, substance_reserve) -> bool:
        if self.inventory[Items.Weird_Substance] < 8 + substance_reserve:
            return False

        protected = self.capture_protected(Items.Gold)
        self.record_action("maze")
        self.inventory[Items.Weird_Substance] -= 8
        self.inventory[Items.Gold] += 8
        self.check_protected(protected)
        self.finish_action()
        return True

    def unlock(self, unlock) -> bool:
        self.unlock_calls += 1

        if not top_hat.can_afford_cost(self.top_hat_cost):
            return False

        self.record_action("unlock")
        self.unlocked = True
        return True


def test_realistic_planner_simulation() -> None:
    simulator = PlannerSimulation()
    simulator.install()

    if not top_hat.farm_top_hat():
        raise AssertionError("realistic planner simulation did not unlock")

    if len(simulator.actions) > 40:
        raise AssertionError("planner exceeded its bounded simulation action limit")
    if simulator.unlock_calls != 1 or simulator.actions[-1] != "unlock":
        raise AssertionError("simulation unlocked with an invalid action sequence")

    power_levels = []
    for action, power_amount in simulator.power_after_actions:
        if action == "power":
            power_levels.append(power_amount)

    if not power_levels or power_levels[0] < top_hat.POWER_HIGH_WATERMARK:
        raise AssertionError("initial Power action did not reach the high watermark")

    saw_between_watermarks = False
    for index, (action, power_amount) in enumerate(simulator.power_after_actions):
        if action != "wait":
            continue
        if not top_hat.POWER_LOW_WATERMARK < power_amount < top_hat.POWER_HIGH_WATERMARK:
            continue

        saw_between_watermarks = True
        if (
            index + 1 < len(simulator.power_after_actions)
            and simulator.power_after_actions[index + 1][0] == "power"
        ):
            raise AssertionError("between-watermark wait caused immediate Power work")

    if not saw_between_watermarks:
        raise AssertionError("simulation did not exercise between-watermark consumption")

    for required_action in (
        "power",
        "cactus",
        "wait",
        "maze",
        "carrot",
        "wood",
        "hay",
    ):
        if required_action not in simulator.actions:
            raise AssertionError("simulation omitted " + required_action + " work")

    for item in simulator.top_hat_cost:
        if simulator.inventory[item] < simulator.top_hat_cost[item]:
            raise AssertionError("simulation ended below the Top Hat cost")

    if simulator.protection_checks == 0:
        raise AssertionError("simulation did not evaluate protected balances")

    simulator.inventory[Items.Power] = 9
    crossing_actions = []

    def record_crossing(item, policy) -> bool:
        crossing_actions.append(item)
        return True

    top_hat.run_item_producer = record_crossing
    top_hat.perform_next_action = REAL_PERFORM_NEXT_ACTION
    if not top_hat.perform_next_action({Items.Wood: 1}):
        raise AssertionError("low Power crossing did not select a refill action")
    if crossing_actions[-1] != Items.Power:
        raise AssertionError("crossing the low watermark did not start Power work")


def test_faulty_producer_cannot_consume_saved_protected_balance() -> None:
    simulator = PlannerSimulation()
    simulator.install()
    simulator.inventory[Items.Power] = 20
    simulator.inventory[Items.Hay] = 4
    simulator.inventory[Items.Cactus] = 2
    simulator.inventory[Items.Gold] = 8
    simulator.inventory[Items.Carrot] = 3
    simulator.consume_protected_balance = True
    top_hat.POWER_STOCKPILE_ESTABLISHED = True
    top_hat.POWER_REFILL_ACTIVE = False

    try:
        top_hat.run_item_producer(Items.Wood, simulator.top_hat_cost)
    except AssertionError as error:
        if "protected balance was consumed for Power" not in str(error):
            raise AssertionError("faulty producer reported the wrong protection failure") from error
    else:
        raise AssertionError("faulty producer consumed a protected balance successfully")

    if simulator.actions != ["wood"]:
        raise AssertionError("protected-balance failure was not detected at the faulty action")


def test_missing_producer_stops_within_action_limit() -> None:
    simulator = PlannerSimulation()
    simulator.install()
    top_hat.farm_cactus_cycle = lambda *args: False

    if top_hat.farm_top_hat():
        raise AssertionError("planner succeeded after removing a required producer")

    if simulator.unlock_calls != 0:
        raise AssertionError("planner attempted unlock after producer failure")
    if len(simulator.actions) > 40:
        raise AssertionError("missing producer was not stopped by the bounded planner")
    if not any("failed" in message.lower() for message in simulator.messages):
        raise AssertionError("missing producer failure was not reported")


def main() -> None:
    test_already_unlocked_returns_immediately()
    test_empty_cost_stops_visibly()
    test_dynamic_costs_resample_and_allow_overshoot()
    test_no_progress_stops_after_repeated_action()
    test_unlock_failure_is_called_once()
    test_policy_priority()
    test_power_reaches_high_watermark_without_live_power_cost()
    test_initial_power_stockpile_precedes_later_stages()
    test_established_power_between_watermarks_uses_required_resource()
    test_power_refill_stays_active_until_high_watermark()
    test_fertilizer_wait_does_not_restart_power_refill()
    test_live_power_cost_overrides_watermark_policy()
    test_power_watermarks_adjust_from_observed_consumption()
    test_tree_budget_counts_checkerboard_tiles()
    test_protected_balance_plus_cycle_budget()
    test_missing_fertilizer_reports_wait()
    test_gold_and_cactus_receive_live_policy()
    test_cactus_cycle_ignores_missing_final_cactus_balance()
    test_gold_plans_positive_weird_substance_target()
    test_gold_resamples_after_weird_substance_production()
    test_weird_substance_action_stops_at_immediate_target()
    test_gold_complete_does_not_request_weird_substance()
    test_fertilizer_wait_resumes_planner()
    test_wait_diagnostics_are_rate_limited()
    test_power_boundary_uses_adaptive_target()
    test_adaptive_power_target_runs_full_cycle()
    test_direct_dependency_cycle_stops_cleanly()
    test_multi_item_dependency_cycle_stops_cleanly()
    test_blocked_dependency_allows_unrelated_resource_work()
    test_planner_simulation_matches_live_top_hat_cost_shape()
    test_realistic_planner_simulation()
    test_faulty_producer_cannot_consume_saved_protected_balance()
    test_missing_producer_stops_within_action_limit()
    print("Passed Top Hat planner policy, live-cost, safeguard, and routing tests")


if __name__ == "__main__":
    main()
