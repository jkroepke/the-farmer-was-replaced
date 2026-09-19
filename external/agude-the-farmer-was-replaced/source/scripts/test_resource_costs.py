#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise live cost lookup, geometry budgets, and protected inventory."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import resource_costs  # noqa: E402


class Items:
    Carrot = "Carrot"
    Cactus = "Cactus"
    Wood = "Wood"
    Hay = "Hay"


class Unlocks:
    Top_Hat = "Top Hat"


resource_costs.Items = Items
resource_costs.Unlocks = Unlocks
inventory = {}
costs = {}
messages = []


def install() -> None:
    resource_costs.get_cost = lambda target: costs.get(target)
    resource_costs.num_items = lambda item: inventory.get(item, 0)
    resource_costs.quick_print = lambda message: messages.append(message)


def test_live_top_hat_cost() -> None:
    install()
    costs[Unlocks.Top_Hat] = {Items.Wood: 12, Items.Cactus: 7}

    first = resource_costs.get_top_hat_cost()
    if first != {Items.Wood: 12, Items.Cactus: 7}:
        raise AssertionError(f"live Top Hat cost was not returned: {first}")

    costs[Unlocks.Top_Hat] = {Items.Wood: 20}
    second = resource_costs.get_top_hat_cost()
    if second != {Items.Wood: 20}:
        raise AssertionError("Top Hat cost was cached instead of read live")


def test_planting_budget_uses_geometry() -> None:
    install()
    costs[Items.Carrot] = {Items.Carrot: 2, Items.Wood: 1}

    budget = resource_costs.get_planting_budget(Items.Carrot, 3, 4)
    if budget != {Items.Carrot: 24, Items.Wood: 12}:
        raise AssertionError(f"geometry did not scale planting budget: {budget}")


def test_protected_inventory_and_cycle_budget() -> None:
    install()
    cost = {Items.Cactus: 3, Items.Wood: 2}
    protected = {Items.Cactus: 5, Items.Hay: 7}
    cycle = {Items.Wood: 4, Items.Hay: 1}

    required = resource_costs.get_required_inventory(cost, protected, cycle)
    expected = {Items.Cactus: 8, Items.Wood: 6, Items.Hay: 8}
    if required != expected:
        raise AssertionError(f"inventory safeguards were not merged: {required}")

    inventory.clear()
    inventory.update(expected)
    if not resource_costs.can_afford_cost(cost, protected, cycle):
        raise AssertionError("exact protected and cycle inventory was rejected")

    inventory[Items.Wood] -= 1
    if resource_costs.can_afford_cost(cost, protected, cycle):
        raise AssertionError("underfunded protected inventory was accepted")


def test_invalid_costs_are_visible_failures() -> None:
    install()
    invalid_costs = [None, {}, {Items.Wood: 0}, {Items.Wood: -1}, {Items.Wood: None}]

    for invalid in invalid_costs:
        costs[Unlocks.Top_Hat] = invalid
        messages.clear()
        if resource_costs.get_top_hat_cost() is not None:
            raise AssertionError(f"invalid cost was accepted: {invalid}")
        if not messages:
            raise AssertionError(f"invalid cost was not reported: {invalid}")

    costs[Items.Carrot] = {Items.Carrot: 1}
    if resource_costs.get_planting_budget(Items.Carrot, 0, 4) is not None:
        raise AssertionError("empty planting region was accepted")

    costs[Items.Cactus] = {}
    if resource_costs.get_planting_budget(Items.Cactus, 4, 4) != {}:
        raise AssertionError("zero-cost entity was rejected")


def main() -> None:
    test_live_top_hat_cost()
    test_planting_budget_uses_geometry()
    test_protected_inventory_and_cycle_budget()
    test_invalid_costs_are_visible_failures()
    print("Passed live resource cost and inventory budget tests")


if __name__ == "__main__":
    main()
