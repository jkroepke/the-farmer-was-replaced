#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise fresh-maze creation, wall following, and stopping conditions."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import maze  # noqa: E402


class Entities:
    Bush = "Bush"
    Hedge = "Hedge"
    Treasure = "Treasure"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Items:
    Gold = "Gold"
    Weird_Substance = "Weird Substance"


class Unlocks:
    Mazes = "Mazes"


maze.Entities = Entities
maze.Grounds = Grounds
maze.Items = Items
maze.Unlocks = Unlocks


class MazePathSimulator:
    def __init__(self) -> None:
        self.position = (0, 0)
        self.treasure_position = (0, 2)
        self.harvest_calls = 0
        self.move_attempts = []
        self.successful_moves = []
        self.edges = {
            (0, 0): {"East": (1, 0)},
            (1, 0): {"West": (0, 0), "East": (2, 0)},
            (2, 0): {"West": (1, 0), "North": (2, 1)},
            (2, 1): {
                "South": (2, 0),
                "North": (2, 2),
                "West": (1, 1),
            },
            (2, 2): {"South": (2, 1)},
            (1, 1): {"East": (2, 1), "West": (0, 1)},
            (0, 1): {"East": (1, 1), "North": (0, 2)},
            (0, 2): {"South": (0, 1)},
        }

    def install(self) -> None:
        maze.North = "North"
        maze.East = "East"
        maze.South = "South"
        maze.West = "West"
        maze.get_entity_type = self.get_entity_type
        maze.move = self.move
        maze.harvest = self.harvest

    def get_entity_type(self):
        if self.position == self.treasure_position:
            return Entities.Treasure

        return Entities.Hedge

    def move(self, direction) -> bool:
        self.move_attempts.append(direction)
        next_position = self.edges[self.position].get(direction)

        if next_position is None:
            return False

        self.position = next_position
        self.successful_moves.append((direction, self.position))
        return True

    def harvest(self) -> None:
        if self.get_entity_type() != Entities.Treasure:
            raise AssertionError("maze solver harvested a non-treasure tile")

        self.harvest_calls += 1


def test_right_hand_solver() -> None:
    simulator = MazePathSimulator()
    simulator.install()

    if not maze.solve_maze():
        raise AssertionError("right-hand solver failed to reach treasure")

    expected_moves = [
        ("East", (1, 0)),
        ("East", (2, 0)),
        ("North", (2, 1)),
        ("North", (2, 2)),
        ("South", (2, 1)),
        ("West", (1, 1)),
        ("West", (0, 1)),
        ("North", (0, 2)),
    ]

    if simulator.successful_moves != expected_moves:
        raise AssertionError(f"right-hand decisions changed: {simulator.successful_moves}")

    if simulator.harvest_calls != 1:
        raise AssertionError("solver did not harvest exactly one treasure")

    if hasattr(maze, "move_to"):
        raise AssertionError("maze module exposes move_to navigation")


class FarmSimulator:
    def __init__(
        self,
        maze_level: int = 2,
        world_size: int = 8,
        weird_substance: int = 40,
        gold: int = 0,
        plant_result: bool = True,
        use_item_result: bool = True,
    ) -> None:
        self.maze_level = maze_level
        self.world_size = world_size
        self.inventory = {
            Items.Weird_Substance: weird_substance,
            Items.Gold: gold,
        }
        self.plant_result = plant_result
        self.use_item_result = use_item_result
        self.ground = Grounds.Grassland
        self.events = []
        self.clear_calls = 0
        self.plant_calls = 0
        self.use_item_calls = []
        self.solve_calls = 0

    def install(self) -> None:
        maze.clear = self.clear
        maze.get_ground_type = self.get_ground_type
        maze.get_world_size = self.get_world_size
        maze.num_items = self.num_items
        maze.num_unlocked = self.num_unlocked
        maze.plant = self.plant
        maze.till = self.till
        maze.use_item = self.use_item
        maze.solve_maze = self.solve_maze

    def clear(self) -> None:
        self.clear_calls += 1
        self.events.append("clear")
        self.ground = Grounds.Grassland

    def get_ground_type(self):
        return self.ground

    def get_world_size(self) -> int:
        return self.world_size

    def num_items(self, item):
        return self.inventory[item]

    def num_unlocked(self, unlock) -> int:
        return self.maze_level

    def plant(self, entity) -> bool:
        self.plant_calls += 1
        self.events.append("plant")
        return self.plant_result

    def till(self) -> None:
        self.ground = Grounds.Soil
        self.events.append("till")

    def use_item(self, item, amount) -> bool:
        self.use_item_calls.append((item, amount))
        self.events.append("use_item")

        if not self.use_item_result:
            return False

        if self.inventory[item] < amount:
            return False

        self.inventory[item] -= amount
        return True

    def solve_maze(self) -> bool:
        self.solve_calls += 1
        self.events.append("solve")
        self.inventory[Items.Gold] += 64
        return True


def configure_maze_mode() -> None:
    pass


def test_cost_and_repeated_fresh_mazes() -> None:
    configure_maze_mode()
    simulator = FarmSimulator()
    simulator.install()

    if maze.get_maze_substance_cost() != 16:
        raise AssertionError("maze cost did not apply the upgrade exponent")

    maze.farm_mazes(128, 0)

    if simulator.clear_calls != 1:
        raise AssertionError("fresh maze farming did not clear exactly once")
    if simulator.plant_calls != 2 or simulator.solve_calls != 2:
        raise AssertionError("fresh maze farming did not repeat to the gold target")
    if simulator.use_item_calls != [
        (Items.Weird_Substance, 16),
        (Items.Weird_Substance, 16),
    ]:
        raise AssertionError(f"incorrect Weird Substance costs: {simulator.use_item_calls}")
    if simulator.inventory[Items.Gold] != 128:
        raise AssertionError("maze farming did not stop at the gold target")
    if simulator.inventory[Items.Weird_Substance] != 8:
        raise AssertionError("maze farming consumed the wrong amount of substance")


def test_unlock_and_inventory_safeguards() -> None:
    configure_maze_mode()

    locked = FarmSimulator(maze_level=0, weird_substance=100)
    locked.install()

    if maze.get_maze_substance_cost() != 0:
        raise AssertionError("locked maze level produced a substance cost")
    maze.farm_mazes(128, 0)

    if locked.events:
        raise AssertionError(f"locked maze mode performed actions: {locked.events}")

    insufficient = FarmSimulator(weird_substance=15)
    insufficient.install()
    maze.farm_mazes(128, 0)

    if insufficient.events:
        raise AssertionError(f"insufficient inventory did not stop cleanly: {insufficient.events}")

    reserved = FarmSimulator(weird_substance=16)
    reserved.install()
    maze.farm_mazes(128, 1)

    if reserved.events:
        raise AssertionError("maze mode spent the configured substance reserve")


def test_creation_checks_action_results() -> None:
    configure_maze_mode()

    failed_plant = FarmSimulator(plant_result=False)
    failed_plant.install()
    maze.farm_mazes(128, 0)

    if failed_plant.use_item_calls or failed_plant.solve_calls:
        raise AssertionError("maze mode continued after plant failure")

    failed_use = FarmSimulator(use_item_result=False)
    failed_use.install()
    maze.farm_mazes(128, 0)

    if failed_use.solve_calls:
        raise AssertionError("maze mode continued after substance-use failure")


def test_gold_target_skips_farm() -> None:
    configure_maze_mode()
    simulator = FarmSimulator(gold=128)
    simulator.install()
    maze.farm_mazes(128, 0)

    if simulator.events:
        raise AssertionError("gold target did not skip maze farming")


def test_partial_batch_reports_maze_progress() -> None:
    configure_maze_mode()
    simulator = FarmSimulator(weird_substance=16)
    simulator.install()

    if not maze.farm_mazes(128, 0):
        raise AssertionError("completed maze was reported as no progress")

    if simulator.solve_calls != 1:
        raise AssertionError("maze batch did not stop after substance exhaustion")
    if simulator.inventory[Items.Gold] != 64:
        raise AssertionError("partial maze progress was not retained")


def main() -> None:
    test_right_hand_solver()
    test_cost_and_repeated_fresh_mazes()
    test_unlock_and_inventory_safeguards()
    test_creation_checks_action_results()
    test_gold_target_skips_farm()
    test_partial_batch_reports_maze_progress()
    print("Passed maze wall-following, cost, safeguards, and stopping tests")


if __name__ == "__main__":
    main()
