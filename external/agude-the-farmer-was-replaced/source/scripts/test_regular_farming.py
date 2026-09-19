#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise regular target selection and traversal together."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import farm_layout  # noqa: E402
import regular_farming  # noqa: E402


class Entities:
    Cactus = "Cactus"
    Pumpkin = "Pumpkin"
    Sunflower = "Sunflower"
    Tree = "Tree"
    Bush = "Bush"
    Grass = "Grass"
    Carrot = "Carrot"


farm_layout.Entities = Entities

WORLD_SIZE = 32
visited_positions = []
tended_targets = []


def get_world_size() -> int:
    return WORLD_SIZE


def distance_to(x: int, y: int) -> int:
    return x + y


def record_position(x: int, y: int) -> None:
    visited_positions.append((x, y))


def record_target(target) -> None:
    tended_targets.append(target)


def install_simulator() -> None:
    regular_farming.get_world_size = get_world_size
    regular_farming.distance_to = distance_to
    regular_farming.move_to = record_position
    regular_farming.tend_regular_tile = record_target


def assert_traversal(expected_positions, expected_targets, name: str) -> None:
    visited_positions.clear()
    tended_targets.clear()

    regular_farming.farm_regular_tiles()

    if visited_positions != expected_positions:
        raise AssertionError(f"{name}: position traversal changed")

    if tended_targets != expected_targets:
        raise AssertionError(f"{name}: target propagation changed")


def test_forward_traversal() -> None:
    positions = regular_farming.get_regular_positions()

    if len(positions) != WORLD_SIZE * WORLD_SIZE:
        raise AssertionError(
            f"expected {WORLD_SIZE * WORLD_SIZE} regular positions, got {len(positions)}"
        )

    expected_positions = []
    expected_targets = []

    for x, y, target in positions:
        expected_positions.append((x, y))
        expected_targets.append(target)

    assert_traversal(expected_positions, expected_targets, "forward traversal")


def test_reverse_traversal() -> None:
    def reverse_distance_to(x: int, y: int) -> int:
        return WORLD_SIZE * 2 - x - y

    regular_farming.distance_to = reverse_distance_to
    positions = regular_farming.get_regular_positions()
    expected_positions = []
    expected_targets = []

    for index in range(len(positions) - 1, -1, -1):
        x, y, target = positions[index]
        expected_positions.append((x, y))
        expected_targets.append(target)

    assert_traversal(expected_positions, expected_targets, "reverse traversal")


def main() -> None:
    install_simulator()
    test_forward_traversal()
    test_reverse_traversal()
    print("Passed regular traversal target-propagation tests")


if __name__ == "__main__":
    main()
