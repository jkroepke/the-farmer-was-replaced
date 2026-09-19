#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise shared rectangular traversal and endpoint selection."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import cactus  # noqa: E402
import pumpkins  # noqa: E402
import sunflowers  # noqa: E402
import traversal  # noqa: E402


def expected_snake(start_x: int, start_y: int, width: int, height: int):
    positions = []

    for x in range(start_x, start_x + width):
        if (x - start_x) % 2 == 0:
            for y in range(start_y, start_y + height):
                positions.append((x, y))
        else:
            for y in range(start_y + height - 1, start_y - 1, -1):
                positions.append((x, y))

    return positions


def test_snake_regions() -> None:
    cases = [
        (0, 0, 3, 3, "square"),
        (2, 4, 4, 2, "rectangular"),
        (7, 9, 2, 4, "offset"),
        (5, 6, 1, 1, "single tile"),
    ]

    for start_x, start_y, width, height, name in cases:
        actual = traversal.get_snake_positions(start_x, start_y, width, height)
        expected = expected_snake(start_x, start_y, width, height)

        if actual != expected:
            raise AssertionError(f"{name}: snake order changed: {actual}")

        if len(actual) != width * height:
            raise AssertionError(f"{name}: incorrect position count")


def test_empty_regions() -> None:
    for width, height in ((0, 3), (3, 0), (-1, 2), (2, -1)):
        if traversal.get_snake_positions(0, 0, width, height) != []:
            raise AssertionError("empty region returned positions")


def test_nearer_endpoint() -> None:
    distances = {(0, 0): 8, (3, 3): 2, (1, 2): 4, (4, 5): 4}

    def fake_distance(x: int, y: int) -> int:
        return distances[(x, y)]

    if traversal.should_scan_forward([(0, 0), (3, 3)], fake_distance):
        raise AssertionError("farther first endpoint was selected")

    if not traversal.should_scan_forward([(1, 2), (4, 5)], fake_distance):
        raise AssertionError("equal endpoints did not preserve forward order")

    if not traversal.should_scan_forward([], fake_distance):
        raise AssertionError("empty endpoint list was not handled")


def test_existing_patch_order() -> None:
    for module, start_x, start_y, width, height, name in (
        (
            cactus,
            cactus.CACTUS_START_X,
            cactus.CACTUS_START_Y,
            cactus.CACTUS_SIZE,
            cactus.CACTUS_SIZE,
            "cactus",
        ),
        (
            pumpkins,
            pumpkins.PUMPKIN_START_X,
            pumpkins.PUMPKIN_START_Y,
            pumpkins.PUMPKIN_SIZE,
            pumpkins.PUMPKIN_SIZE,
            "pumpkin",
        ),
        (
            sunflowers,
            sunflowers.SUNFLOWER_START_X,
            sunflowers.SUNFLOWER_START_Y,
            sunflowers.SUNFLOWER_WIDTH,
            sunflowers.SUNFLOWER_HEIGHT,
            "sunflower",
        ),
    ):
        expected = expected_snake(start_x, start_y, width, height)
        actual = module.get_cactus_positions() if module is cactus else None

        if module is pumpkins:
            actual = module.get_pumpkin_positions()
        elif module is sunflowers:
            actual = module.get_sunflower_positions()

        if actual != expected:
            raise AssertionError(f"{name}: existing patch order changed")


def main() -> None:
    test_snake_regions()
    test_empty_regions()
    test_nearer_endpoint()
    test_existing_patch_order()
    print("Passed shared traversal and endpoint-selection tests")


if __name__ == "__main__":
    main()
