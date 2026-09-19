#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the standalone dinosaur route and farming safeguards."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import dinosaurs  # noqa: E402


class Entities:
    Apple = "Apple"


class Hats:
    Dinosaur_Hat = "Dinosaur Hat"
    Straw_Hat = "Straw Hat"


class Items:
    Bone = "Bone"
    Cactus = "Cactus"


class Unlocks:
    Dinosaurs = "Dinosaurs"


North = "North"
East = "East"
South = "South"
West = "West"
DEFAULT_APPLE_COST = object()


dinosaurs.Entities = Entities
dinosaurs.Hats = Hats
dinosaurs.Items = Items
dinosaurs.Unlocks = Unlocks
REAL_RUN_DINOSAUR_ONCE = dinosaurs.run_dinosaur_once


class RouteSimulator:
    def __init__(self, world_size: int, successful_move_limit: int) -> None:
        self.world_size = world_size
        self.successful_move_limit = successful_move_limit
        self.position = (0, 0)
        self.successful_moves = []
        self.move_attempts = 0
        self.out_of_bounds_attempts = 0

    def install(self) -> None:
        dinosaurs.North = North
        dinosaurs.East = East
        dinosaurs.South = South
        dinosaurs.West = West
        dinosaurs.move = self.move

    def move(self, direction) -> bool:
        self.move_attempts += 1

        if len(self.successful_moves) >= self.successful_move_limit:
            return False

        x, y = self.position

        if direction == North:
            y += 1
        elif direction == East:
            x += 1
        elif direction == South:
            y -= 1
        elif direction == West:
            x -= 1
        else:
            raise AssertionError(f"unknown direction: {direction}")

        if x < 0 or x >= self.world_size or y < 0 or y >= self.world_size:
            self.out_of_bounds_attempts += 1
            return False

        self.position = (x, y)
        self.successful_moves.append(self.position)
        return True


def assert_route_cycle(world_size: int) -> None:
    cycle_length = world_size * world_size
    simulator = RouteSimulator(world_size, cycle_length * 2)
    simulator.install()

    if dinosaurs.traverse_dinosaur_cycle(world_size):
        raise AssertionError("dinosaur traversal did not stop at a blocked move")

    if len(simulator.successful_moves) != cycle_length * 2:
        raise AssertionError("dinosaur traversal did not repeat the full cycle")

    first_cycle = simulator.successful_moves[:cycle_length]
    second_cycle = simulator.successful_moves[cycle_length:]

    if first_cycle != second_cycle:
        raise AssertionError(f"dinosaur route changed on repetition for size {world_size}")

    if first_cycle[-1] != (0, 0):
        raise AssertionError("dinosaur route did not return to the origin")

    visited_before_return = [(0, 0)] + first_cycle[:-1]
    expected_positions = []

    for x in range(world_size):
        for y in range(world_size):
            expected_positions.append((x, y))

    if len(set(visited_before_return)) != cycle_length:
        raise AssertionError(f"dinosaur route repeated a tile for size {world_size}")

    if set(visited_before_return) != set(expected_positions):
        raise AssertionError(f"dinosaur route missed a tile for size {world_size}")

    previous = (0, 0)
    for position in first_cycle:
        distance = abs(position[0] - previous[0]) + abs(position[1] - previous[1])

        if distance != 1:
            raise AssertionError(
                f"dinosaur route made a non-adjacent move: {previous} -> {position}"
            )

        previous = position

    if simulator.position != (0, 0):
        raise AssertionError("dinosaur traversal did not finish at the origin")

    if simulator.out_of_bounds_attempts != 0:
        raise AssertionError("dinosaur route attempted to cross a field boundary")

    if simulator.move_attempts != (cycle_length * 2) + 1:
        raise AssertionError("dinosaur traversal continued after its first failed move")


def test_routes() -> None:
    for world_size in (2, 4, 8, 32):
        assert_route_cycle(world_size)

    simulator = RouteSimulator(4, 2)
    simulator.install()

    if dinosaurs.move_steps(North, 4):
        raise AssertionError("move_steps ignored a failed movement")

    if len(simulator.successful_moves) != 2 or simulator.move_attempts != 3:
        raise AssertionError("move_steps did not stop on its first failed movement")


class FarmSimulator:
    def __init__(
        self,
        world_size: int = 4,
        bones: int = 0,
        cactus: int = 100,
        unlocked: int = 1,
        apple_cost=DEFAULT_APPLE_COST,
        bone_gain: int = 10,
    ) -> None:
        if apple_cost is DEFAULT_APPLE_COST:
            apple_cost = {Items.Cactus: 1}

        self.world_size = world_size
        self.inventory = {
            Items.Bone: bones,
            Items.Cactus: cactus,
        }
        self.unlocked = unlocked
        self.apple_cost = apple_cost
        self.bone_gain = bone_gain
        self.events = []
        self.run_calls = 0
        self.spawn_calls = 0

    def install(self) -> None:
        dinosaurs.num_items = self.num_items
        dinosaurs.num_unlocked = self.num_unlocked
        dinosaurs.get_cost = self.get_cost
        dinosaurs.get_world_size = self.get_world_size
        dinosaurs.clear = self.clear
        dinosaurs.run_dinosaur_once = self.run_dinosaur_once
        dinosaurs.spawn_drone = self.spawn_drone

    def num_items(self, item):
        return self.inventory[item]

    def num_unlocked(self, unlock) -> int:
        return self.unlocked

    def get_cost(self, entity):
        return self.apple_cost

    def get_world_size(self) -> int:
        return self.world_size

    def clear(self) -> None:
        self.events.append("clear")

    def run_dinosaur_once(self, world_size: int) -> bool:
        self.clear()
        self.events.append("run")
        self.run_calls += 1
        run_cost = dinosaurs.get_full_run_cactus_cost(
            world_size,
            self.apple_cost[Items.Cactus],
        )
        self.inventory[Items.Cactus] -= run_cost
        self.inventory[Items.Bone] += self.bone_gain
        return True

    def spawn_drone(self, function, *args) -> None:
        self.spawn_calls += 1


def configure_dinosaur_mode() -> None:
    dinosaurs.ENABLE_DINOSAUR_FARM = True
    dinosaurs.BONE_TARGET = 100
    dinosaurs.DINOSAUR_CACTUS_RESERVE = 0


def assert_no_actions(simulator: FarmSimulator, name: str) -> None:
    if simulator.events:
        raise AssertionError(f"{name} performed game actions: {simulator.events}")

    if simulator.spawn_calls != 0:
        raise AssertionError(f"{name} spawned a drone")


def test_startup_safeguards() -> None:
    configure_dinosaur_mode()

    disabled = FarmSimulator()
    disabled.install()
    dinosaurs.ENABLE_DINOSAUR_FARM = False
    dinosaurs.farm_dinosaurs()
    assert_no_actions(disabled, "disabled dinosaur mode")

    configure_dinosaur_mode()
    satisfied = FarmSimulator(bones=100)
    satisfied.install()
    dinosaurs.farm_dinosaurs()
    assert_no_actions(satisfied, "satisfied bone target")

    locked = FarmSimulator(unlocked=0)
    locked.install()
    dinosaurs.farm_dinosaurs()
    assert_no_actions(locked, "locked dinosaur upgrade")

    for world_size in (1, 3, 5):
        odd = FarmSimulator(world_size=world_size)
        odd.install()
        dinosaurs.farm_dinosaurs()
        assert_no_actions(odd, f"odd world size {world_size}")

    invalid_costs = [
        None,
        {},
        {Items.Cactus: 0},
        {Items.Cactus: -1},
        {Items.Bone: 1},
    ]

    for invalid_cost in invalid_costs:
        invalid = FarmSimulator(apple_cost=invalid_cost)
        invalid.install()
        dinosaurs.farm_dinosaurs()
        assert_no_actions(invalid, f"invalid apple cost {invalid_cost!r}")


def test_cost_and_reserve() -> None:
    configure_dinosaur_mode()
    dinosaurs.DINOSAUR_CACTUS_RESERVE = 1

    if dinosaurs.get_full_run_cactus_cost(4, 3) != 48:
        raise AssertionError("full dinosaur run cost was calculated incorrectly")

    insufficient = FarmSimulator(cactus=16)
    insufficient.install()
    dinosaurs.farm_dinosaurs()
    assert_no_actions(insufficient, "underfunded dinosaur run")

    funded = FarmSimulator(cactus=17, bone_gain=100)
    funded.install()
    dinosaurs.farm_dinosaurs()

    if funded.events != ["clear", "run"]:
        raise AssertionError(f"funded dinosaur run did not start once: {funded.events}")

    if funded.inventory[Items.Cactus] != 1:
        raise AssertionError("dinosaur run spent the configured cactus reserve")


class RunSimulator:
    def __init__(self, apple_present: bool) -> None:
        self.apple_present = apple_present
        self.events = []
        self.hat = Hats.Straw_Hat
        self.spawn_calls = 0

    def install(self) -> None:
        dinosaurs.clear = self.clear
        dinosaurs.change_hat = self.change_hat
        dinosaurs.get_entity_type = self.get_entity_type
        dinosaurs.traverse_dinosaur_cycle = self.traverse_dinosaur_cycle
        dinosaurs.run_dinosaur_once = REAL_RUN_DINOSAUR_ONCE
        dinosaurs.spawn_drone = self.spawn_drone

    def clear(self) -> None:
        self.hat = Hats.Straw_Hat
        self.events.append("clear")

    def change_hat(self, hat) -> None:
        self.hat = hat
        self.events.append(("hat", hat))

    def get_entity_type(self):
        self.events.append("check apple")

        if self.apple_present:
            return Entities.Apple

        return "Grass"

    def traverse_dinosaur_cycle(self, world_size: int) -> bool:
        self.events.append(("traverse", world_size))
        return False

    def spawn_drone(self, function, *args) -> None:
        self.spawn_calls += 1


def test_run_sequence() -> None:
    complete = RunSimulator(apple_present=True)
    complete.install()

    if not dinosaurs.run_dinosaur_once(4):
        raise AssertionError("complete dinosaur run reported failure")

    expected_events = [
        "clear",
        ("hat", Hats.Dinosaur_Hat),
        "check apple",
        ("traverse", 4),
        ("hat", Hats.Straw_Hat),
    ]

    if complete.events != expected_events:
        raise AssertionError(f"dinosaur run sequence changed: {complete.events}")

    if complete.spawn_calls != 0:
        raise AssertionError("dinosaur run spawned a drone")

    missing_apple = RunSimulator(apple_present=False)
    missing_apple.install()

    if dinosaurs.run_dinosaur_once(4):
        raise AssertionError("missing initial apple reported success")

    if missing_apple.events != [
        "clear",
        ("hat", Hats.Dinosaur_Hat),
        "check apple",
        ("hat", Hats.Straw_Hat),
    ]:
        raise AssertionError(f"missing apple did not restore the straw hat: {missing_apple.events}")


def test_repeated_runs_stop_at_target() -> None:
    configure_dinosaur_mode()
    simulator = FarmSimulator(cactus=100, bone_gain=10)
    simulator.install()
    dinosaurs.BONE_TARGET = 20
    dinosaurs.farm_dinosaurs()

    if simulator.run_calls != 2:
        raise AssertionError("dinosaur farming did not stop at the bone target")

    if simulator.events != ["clear", "run", "clear", "run"]:
        raise AssertionError(f"dinosaur farming ran an unexpected sequence: {simulator.events}")


def test_main_is_isolated() -> None:
    main_source = (SAVE_DIRECTORY / "main.py").read_text()

    if "dinosaur" in main_source.lower():
        raise AssertionError("main.py imports or references dinosaur mode")


def main() -> None:
    test_routes()
    test_startup_safeguards()
    test_cost_and_reserve()
    test_run_sequence()
    test_repeated_runs_stop_at_target()
    test_main_is_isolated()
    print("Passed dinosaur routes, policy safeguards, hat sequencing, and isolation tests")


if __name__ == "__main__":
    main()
