#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the fertilizer policy at each supported harvest boundary."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import cactus  # noqa: E402
import fertilizing  # noqa: E402
import pumpkins  # noqa: E402
import regular_farming  # noqa: E402


class Items:
    Fertilizer = "Fertilizer"
    Weird_Substance = "Weird Substance"


inventory = {}
events = []


def num_items(item):
    return inventory[item]


def use_item(item):
    if inventory[item] <= 0:
        return False

    inventory[item] -= 1
    events.append("fertilize")
    return True


def record_harvest() -> None:
    events.append("harvest")


def record_wait(*args) -> None:
    events.append("wait")
    return True


def record_sort() -> None:
    events.append("sort")


def crop_is_ready() -> bool:
    return True


def crop_is_not_ready() -> bool:
    return False


def no_op(*args) -> None:
    pass


def one_position():
    return [(0, 0)]


def reset_state(fertilizer: int = 5, weird_substance: int = 0) -> None:
    inventory.clear()
    inventory[Items.Fertilizer] = fertilizer
    inventory[Items.Weird_Substance] = weird_substance
    events.clear()

    fertilizing.ENABLE_WEIRD_SUBSTANCE_PRODUCTION = True
    fertilizing.WEIRD_SUBSTANCE_TARGET = 1000
    fertilizing.FERTILIZER_RESERVE = 0


def fertilizer_uses() -> int:
    return events.count("fertilize")


def assert_no_fertilizer(name: str) -> None:
    if fertilizer_uses() != 0:
        raise AssertionError(f"{name}: fertilizer was used")


def test_policy_thresholds() -> None:
    reset_state()
    fertilizing.ENABLE_WEIRD_SUBSTANCE_PRODUCTION = False

    if fertilizing.fertilize_before_harvest(1000, 0, False):
        raise AssertionError("disabled production unexpectedly fertilized")
    assert_no_fertilizer("disabled production")

    reset_state(weird_substance=1000)
    if fertilizing.fertilize_before_harvest(1000, 0, True):
        raise AssertionError("target inventory unexpectedly fertilized")
    assert_no_fertilizer("target inventory")

    reset_state(fertilizer=2)
    fertilizing.FERTILIZER_RESERVE = 2
    if fertilizing.fertilize_before_harvest(1000, 2, True):
        raise AssertionError("reserve inventory unexpectedly fertilized")
    assert_no_fertilizer("reserve inventory")

    reset_state(fertilizer=1)
    fertilizing.FERTILIZER_RESERVE = 2
    if fertilizing.fertilize_before_harvest(1000, 2, True):
        raise AssertionError("below-reserve inventory unexpectedly fertilized")
    assert_no_fertilizer("below-reserve inventory")


def test_policy_uses_one_fertilizer_below_target() -> None:
    reset_state(fertilizer=3)

    if not fertilizing.fertilize_before_harvest(1000, 0, True):
        raise AssertionError("fertilizer was not used below target")

    if fertilizer_uses() != 1:
        raise AssertionError(f"expected one fertilizer use, got {fertilizer_uses()}")
    if inventory[Items.Fertilizer] != 2:
        raise AssertionError("fertilizer inventory did not decrease by one")


def install_regular_stubs() -> None:
    regular_farming.harvest = record_harvest
    regular_farming.plant_target_entity = no_op
    regular_farming.water_if_dry = no_op


def test_regular_harvest_scope() -> None:
    install_regular_stubs()

    reset_state()
    regular_farming.FERTILIZE_REGULAR_HARVESTS = True
    regular_farming.can_harvest = crop_is_ready
    regular_farming.tend_regular_tile("Carrot")

    if events != ["fertilize", "harvest"]:
        raise AssertionError(f"regular harvest order changed: {events}")

    reset_state()
    regular_farming.FERTILIZE_REGULAR_HARVESTS = False
    regular_farming.tend_regular_tile("Carrot")

    if events != ["harvest"]:
        raise AssertionError(f"regular scope flag ignored: {events}")


def test_unharvestable_regular_crop_is_not_fertilized() -> None:
    install_regular_stubs()
    reset_state()
    regular_farming.FERTILIZE_REGULAR_HARVESTS = True
    regular_farming.can_harvest = crop_is_not_ready
    regular_farming.tend_regular_tile("Carrot")

    if events:
        raise AssertionError(f"unharvestable regular crop had harvest actions: {events}")


def install_pumpkin_stubs() -> None:
    pumpkins.get_pumpkin_positions = one_position
    pumpkins.wait_for_positions = record_wait
    pumpkins.harvest = record_harvest


def test_pumpkin_harvest_scope_and_limit() -> None:
    install_pumpkin_stubs()

    reset_state()
    pumpkins.FERTILIZE_PUMPKIN_HARVEST = True
    pumpkins.farm_pumpkin_patch()

    if events != ["wait", "fertilize", "harvest"]:
        raise AssertionError(f"pumpkin harvest order changed: {events}")
    if fertilizer_uses() > 1:
        raise AssertionError("pumpkin bulk harvest used multiple fertilizers")

    reset_state()
    pumpkins.FERTILIZE_PUMPKIN_HARVEST = False
    pumpkins.farm_pumpkin_patch()

    if events != ["wait", "harvest"]:
        raise AssertionError(f"pumpkin scope flag ignored: {events}")


def install_cactus_stubs() -> None:
    cactus.get_cactus_positions = one_position
    cactus.wait_for_cactuses = record_wait
    cactus.sort_cactuses = record_sort
    cactus.move_to = no_op
    cactus.can_harvest = crop_is_ready
    cactus.harvest = record_harvest

    def record_cactus_cycle(*args):
        record_wait()
        record_sort()
        return cactus.harvest_cactus()

    cactus.farm_cactus_cycle = record_cactus_cycle


def test_cactus_harvest_scope_and_limit() -> None:
    install_cactus_stubs()

    reset_state()
    cactus.FERTILIZE_CACTUS_HARVEST = True
    cactus.farm_cactus_patch()

    if events != ["wait", "sort", "fertilize", "harvest"]:
        raise AssertionError(f"cactus harvest order changed: {events}")
    if fertilizer_uses() > 1:
        raise AssertionError("cactus bulk harvest used multiple fertilizers")

    reset_state()
    cactus.FERTILIZE_CACTUS_HARVEST = False
    cactus.farm_cactus_patch()

    if events != ["wait", "sort", "harvest"]:
        raise AssertionError(f"cactus scope flag ignored: {events}")


def install_policy_stubs() -> None:
    fertilizing.Items = Items
    fertilizing.num_items = num_items
    fertilizing.use_item = use_item


def main() -> None:
    install_policy_stubs()
    test_policy_thresholds()
    test_policy_uses_one_fertilizer_below_target()
    test_regular_harvest_scope()
    test_unharvestable_regular_crop_is_not_fertilized()
    test_pumpkin_harvest_scope_and_limit()
    test_cactus_harvest_scope_and_limit()
    print("Passed fertilizer policy, scope, ordering, and one-use tests")


if __name__ == "__main__":
    main()
