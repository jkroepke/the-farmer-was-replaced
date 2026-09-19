#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the game cactus sorter against a simulated grid."""

from __future__ import annotations

import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import cactus  # noqa: E402
import navigation  # noqa: E402


EAST = "East"
NORTH = "North"
SOUTH = "South"
WEST = "West"


@dataclass
class ActionCounts:
    world_size_queries: int = 0
    position_queries: int = 0
    move_actions: int = 0
    measure_actions: int = 0
    swap_actions: int = 0

    @property
    def api_actions(self) -> int:
        return (
            self.world_size_queries
            + self.position_queries
            + self.move_actions
            + self.measure_actions
            + self.swap_actions
        )

    @property
    def estimated_ticks(self) -> int:
        return (
            self.world_size_queries
            + self.position_queries
            + self.measure_actions
            + 200 * (self.move_actions + self.swap_actions)
        )


@dataclass(frozen=True)
class ActionLimits:
    max_moves: int
    max_measures: int
    max_api_actions: int
    max_estimated_ticks: int


PERFORMANCE_LIMITS = {
    "already sorted": ActionLimits(900, 900, 3100, 180_000),
    "reverse sorted": ActionLimits(2700, 5200, 17_500, 950_000),
    "worst-case diagonal": ActionLimits(3400, 7000, 23_500, 1_300_000),
    "checkerboard": ActionLimits(2000, 3400, 11_000, 500_000),
}

RANDOM_ACTION_LIMITS = ActionLimits(3000, 5600, 18_000, 900_000)


class GridSimulator:
    def __init__(self, values: list[list[int]], world_size: int) -> None:
        self.values = [row[:] for row in values]
        self.world_size = world_size
        self.x = 0
        self.y = 0
        self.actions = ActionCounts()

    def get_world_size(self) -> int:
        self.actions.world_size_queries += 1
        return self.world_size

    def get_pos_x(self) -> int:
        self.actions.position_queries += 1
        return self.x

    def get_pos_y(self) -> int:
        self.actions.position_queries += 1
        return self.y

    def move(self, direction: str) -> bool:
        if direction == EAST:
            self.x = (self.x + 1) % self.world_size
        elif direction == WEST:
            self.x = (self.x - 1) % self.world_size
        elif direction == NORTH:
            self.y = (self.y + 1) % self.world_size
        elif direction == SOUTH:
            self.y = (self.y - 1) % self.world_size
        else:
            raise AssertionError(f"Unknown direction: {direction}")

        self.actions.move_actions += 1
        return True

    def patch_index(self, x: int, y: int) -> tuple[int, int]:
        patch_x = x - cactus.CACTUS_START_X
        patch_y = y - cactus.CACTUS_START_Y

        if not 0 <= patch_x < cactus.CACTUS_SIZE:
            raise AssertionError(f"X coordinate {x} is outside the cactus patch")
        if not 0 <= patch_y < cactus.CACTUS_SIZE:
            raise AssertionError(f"Y coordinate {y} is outside the cactus patch")

        return patch_y, patch_x

    def neighbor(self, direction: str) -> tuple[int, int]:
        if direction == EAST:
            return self.x + 1, self.y
        if direction == WEST:
            return self.x - 1, self.y
        if direction == NORTH:
            return self.x, self.y + 1
        if direction == SOUTH:
            return self.x, self.y - 1

        raise AssertionError(f"Unknown direction: {direction}")

    def measure(self, direction: str | None = None) -> int:
        self.actions.measure_actions += 1

        if direction is None:
            x, y = self.x, self.y
        else:
            x, y = self.neighbor(direction)

        row, column = self.patch_index(x, y)
        return self.values[row][column]

    def swap(self, direction: str) -> None:
        neighbor_x, neighbor_y = self.neighbor(direction)
        current_row, current_column = self.patch_index(self.x, self.y)
        neighbor_row, neighbor_column = self.patch_index(neighbor_x, neighbor_y)

        self.values[current_row][current_column], self.values[neighbor_row][neighbor_column] = (
            self.values[neighbor_row][neighbor_column],
            self.values[current_row][current_column],
        )
        self.actions.swap_actions += 1


def install_simulator(simulator: GridSimulator) -> None:
    navigation.get_world_size = simulator.get_world_size
    navigation.get_pos_x = simulator.get_pos_x
    navigation.get_pos_y = simulator.get_pos_y
    navigation.move = simulator.move
    navigation.East = EAST
    navigation.North = NORTH
    navigation.South = SOUTH
    navigation.West = WEST

    cactus.measure = simulator.measure
    cactus.swap = simulator.swap
    cactus.East = EAST
    cactus.West = WEST
    cactus.North = NORTH
    cactus.South = SOUTH


def flatten(values: list[list[int]]) -> list[int]:
    flattened = []

    for row in values:
        for value in row:
            flattened.append(value)

    return flattened


def is_sorted(values: list[list[int]]) -> bool:
    size = len(values)

    for row in range(size):
        for column in range(size - 1):
            if values[row][column] > values[row][column + 1]:
                return False

    for row in range(size - 1):
        for column in range(size):
            if values[row][column] > values[row + 1][column]:
                return False

    return True


def sorted_grid() -> list[list[int]]:
    size = cactus.CACTUS_SIZE
    values = []

    for value in range(10):
        for _ in range((size * size) // 10):
            values.append(value)

    while len(values) < size * size:
        values.append(9)

    grid = []

    for row in range(size):
        start = row * size
        grid.append(values[start : start + size])

    return grid


def checkerboard_grid() -> list[list[int]]:
    size = cactus.CACTUS_SIZE
    grid = []

    for row in range(size):
        values = []

        for column in range(size):
            if (row + column) % 2:
                values.append(9)
            else:
                values.append(0)

        grid.append(values)

    return grid


def reverse_sorted_grid() -> list[list[int]]:
    grid = []

    for row in reversed(sorted_grid()):
        grid.append(list(reversed(row)))

    return grid


def worst_case_grid() -> list[list[int]]:
    # Values decrease eastward and northward, stressing both sort passes.
    size = cactus.CACTUS_SIZE
    grid = []

    for row in range(size):
        values = []

        for column in range(size):
            values.append(9 - ((row + column) * 10 // (2 * size - 1)))

        grid.append(values)

    return grid


def random_grid(generator: random.Random) -> list[list[int]]:
    size = cactus.CACTUS_SIZE
    grid = []

    for _ in range(size):
        row = []

        for _ in range(size):
            row.append(generator.randrange(10))

        grid.append(row)

    return grid


def assert_action_limits(name: str, actions: ActionCounts) -> None:
    limits = PERFORMANCE_LIMITS.get(name, RANDOM_ACTION_LIMITS)
    measurements = [
        ("moves", actions.move_actions, limits.max_moves),
        ("measurements", actions.measure_actions, limits.max_measures),
        ("API actions", actions.api_actions, limits.max_api_actions),
        ("estimated ticks", actions.estimated_ticks, limits.max_estimated_ticks),
    ]

    for label, actual, maximum in measurements:
        if actual > maximum:
            raise AssertionError(f"{name}: {label}={actual} exceeds limit {maximum}")


def run_case(name: str, values: list[list[int]]) -> ActionCounts:
    original_values = flatten(values)
    world_size = max(cactus.cactus_end_x(), cactus.cactus_end_y()) + 1
    simulator = GridSimulator(values, world_size)
    install_simulator(simulator)

    cactus.sort_cactuses()

    if not is_sorted(simulator.values):
        raise AssertionError(f"{name}: grid is not sorted")

    if Counter(flatten(simulator.values)) != Counter(original_values):
        raise AssertionError(f"{name}: cactus sizes changed")

    actions = simulator.actions
    assert_action_limits(name, actions)
    print(
        f"{name}: swaps={actions.swap_actions}, "
        f"moves={actions.move_actions}, measures={actions.measure_actions}, "
        f"api_actions={actions.api_actions}, estimated_ticks={actions.estimated_ticks}"
    )
    return actions


def main() -> None:
    generator = random.Random(20260914)
    cases = [
        ("already sorted", sorted_grid()),
        ("reverse sorted", reverse_sorted_grid()),
        ("worst-case diagonal", worst_case_grid()),
        ("checkerboard", checkerboard_grid()),
    ]

    for case_number in range(10):
        cases.append((f"random {case_number + 1}", random_grid(generator)))

    results = []

    for name, values in cases:
        results.append(run_case(name, values))

    swap_counts = [actions.swap_actions for actions in results]
    tick_counts = [actions.estimated_ticks for actions in results]

    print(
        f"Passed {len(results)} cases at {cactus.CACTUS_SIZE}x{cactus.CACTUS_SIZE}; "
        f"swap range={min(swap_counts)}..{max(swap_counts)}; "
        f"estimated tick range={min(tick_counts)}..{max(tick_counts)}"
    )


if __name__ == "__main__":
    main()
