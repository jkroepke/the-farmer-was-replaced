#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the farm layout classifier against every feature configuration."""

from __future__ import annotations

import itertools
import sys
from collections import Counter
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import farm_layout  # noqa: E402


class Entities:
    Cactus = "Cactus"
    Pumpkin = "Pumpkin"
    Sunflower = "Sunflower"
    Tree = "Tree"
    Bush = "Bush"
    Grass = "Grass"
    Carrot = "Carrot"


farm_layout.Entities = Entities

FEATURE_NAMES = (
    "ENABLE_CACTUS_PATCH",
    "ENABLE_PUMPKIN_PATCH",
    "ENABLE_SUNFLOWER_PATCH",
    "ENABLE_TREE_BUSH_STRIP",
    "ENABLE_GRASS_STRIP",
    "ENABLE_CARROT_FILL",
)

WORLD_SIZE = 32


def set_features(enabled_features: tuple[bool, ...]) -> None:
    for name, enabled in zip(FEATURE_NAMES, enabled_features, strict=True):
        setattr(farm_layout, name, enabled)


def count_targets() -> Counter:
    targets = []

    for x in range(WORLD_SIZE):
        for y in range(WORLD_SIZE):
            targets.append(farm_layout.target_entity_at(x, y))

    return Counter(targets)


def assert_counts(name: str, expected: dict) -> None:
    actual = count_targets()

    if actual != Counter(expected):
        raise AssertionError(f"{name}: expected {expected}, got {dict(actual)}")


def test_all_features_enabled() -> None:
    set_features((True, True, True, True, True, True))
    assert_counts(
        "all features enabled",
        {
            Entities.Cactus: 225,
            Entities.Pumpkin: 289,
            Entities.Sunflower: 16,
            Entities.Grass: 443,
            Entities.Tree: 25,
            Entities.Bush: 26,
        },
    )


def test_cactus_disabled() -> None:
    set_features((False, True, True, True, True, True))
    assert_counts(
        "cactus disabled",
        {
            Entities.Pumpkin: 289,
            Entities.Sunflower: 16,
            Entities.Grass: 623,
            Entities.Tree: 48,
            Entities.Bush: 48,
        },
    )


def test_pumpkin_disabled() -> None:
    set_features((True, False, True, True, True, True))
    assert_counts(
        "pumpkin disabled",
        {
            Entities.Cactus: 225,
            Entities.Sunflower: 16,
            Entities.Grass: 732,
            Entities.Tree: 25,
            Entities.Bush: 26,
        },
    )


def test_tree_bush_disabled() -> None:
    set_features((True, True, True, False, True, True))
    assert_counts(
        "tree/bush strip disabled",
        {
            Entities.Cactus: 225,
            Entities.Pumpkin: 289,
            Entities.Sunflower: 16,
            Entities.Grass: 494,
        },
    )


def test_grass_disabled() -> None:
    set_features((True, True, True, True, False, True))
    assert_counts(
        "grass strip disabled",
        {
            Entities.Cactus: 225,
            Entities.Pumpkin: 289,
            Entities.Sunflower: 16,
            Entities.Carrot: 443,
            Entities.Tree: 25,
            Entities.Bush: 26,
        },
    )


def test_carrot_disabled() -> None:
    set_features((True, True, True, True, True, False))
    assert_counts(
        "carrot fill disabled",
        {
            Entities.Cactus: 225,
            Entities.Pumpkin: 289,
            Entities.Sunflower: 16,
            Entities.Grass: 443,
            Entities.Tree: 25,
            Entities.Bush: 26,
        },
    )


def test_sunflower_disabled() -> None:
    set_features((True, True, False, True, True, True))
    assert_counts(
        "sunflower disabled",
        {
            Entities.Cactus: 225,
            Entities.Pumpkin: 289,
            Entities.Grass: 459,
            Entities.Tree: 25,
            Entities.Bush: 26,
        },
    )


def test_all_features_disabled() -> None:
    set_features((False, False, False, False, False, False))
    assert_counts("all features disabled", {None: 1024})


def test_every_configuration_covers_world() -> None:
    for enabled_features in itertools.product((False, True), repeat=len(FEATURE_NAMES)):
        set_features(enabled_features)
        counts = count_targets()

        if sum(counts.values()) != WORLD_SIZE * WORLD_SIZE:
            raise AssertionError(f"{enabled_features}: world coverage is incomplete")


def test_geometry_ignores_flags() -> None:
    coordinates = []

    for x in range(-1, WORLD_SIZE + 1):
        for y in range(-1, WORLD_SIZE + 1):
            coordinates.append((x, y))

    set_features((True, True, True, True, True, True))
    expected_geometry = []

    for x, y in coordinates:
        expected_geometry.append(
            (
                farm_layout.is_cactus_region(x, y),
                farm_layout.is_pumpkin_region(x, y),
                farm_layout.is_sunflower_region(x, y),
            )
        )

    for enabled_features in itertools.product((False, True), repeat=len(FEATURE_NAMES)):
        set_features(enabled_features)

        for index in range(len(coordinates)):
            x, y = coordinates[index]
            actual_geometry = (
                farm_layout.is_cactus_region(x, y),
                farm_layout.is_pumpkin_region(x, y),
                farm_layout.is_sunflower_region(x, y),
            )

            if actual_geometry != expected_geometry[index]:
                raise AssertionError(f"geometry changed for {enabled_features} at {(x, y)}")


def main() -> None:
    test_all_features_enabled()
    test_cactus_disabled()
    test_pumpkin_disabled()
    test_tree_bush_disabled()
    test_grass_disabled()
    test_carrot_disabled()
    test_sunflower_disabled()
    test_all_features_disabled()
    test_every_configuration_covers_world()
    test_geometry_ignores_flags()
    set_features((True, True, True, True, True, True))
    print("Passed farm layout counts, fallthrough, coverage, and geometry tests")


if __name__ == "__main__":
    main()
