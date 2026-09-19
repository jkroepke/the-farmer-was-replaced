#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise the sunflower lifecycle and petal-ordering algorithm."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import farm_layout  # noqa: E402
import sunflowers  # noqa: E402


class Entities:
    Cactus = "Cactus"
    Pumpkin = "Pumpkin"
    Dead_Pumpkin = "Dead Pumpkin"
    Sunflower = "Sunflower"
    Tree = "Tree"
    Bush = "Bush"
    Grass = "Grass"
    Carrot = "Carrot"


class Items:
    Power = "Power"


farm_layout.Entities = Entities
sunflowers.Entities = Entities
sunflowers.Items = Items


class SunflowerSimulator:
    def __init__(self, petals_by_scan_order, scan_reverse: bool) -> None:
        self.positions = sunflowers.get_sunflower_positions()

        if len(self.positions) != len(petals_by_scan_order):
            raise AssertionError("petal fixture does not match patch area")

        self.petals = {}
        for index in range(len(self.positions)):
            position = self.positions[index]
            self.petals[position] = petals_by_scan_order[index]

        self.tiles = {}
        for position in self.positions:
            self.tiles[position] = {
                "entity": None,
                "mature": False,
            }

        self.scan_reverse = scan_reverse
        self.current_position = None
        self.phase = "prepare"
        self.cycle_number = 0
        self.measurement_count = 0
        self.power = 0
        self.events = []
        self.measurement_records = []
        self.harvest_records = []
        self.plant_records = []
        self.fertilizer_calls = 0

    def start_cycle(self) -> None:
        self.cycle_number += 1
        self.measurement_count = 0

    def install(self) -> None:
        sunflowers.distance_to = self.distance_to
        sunflowers.move_to = self.move_to
        sunflowers.get_entity_type = self.get_entity_type
        sunflowers.plant = self.plant
        sunflowers.harvest = self.harvest
        sunflowers.measure = self.measure
        sunflowers.can_harvest = self.can_harvest
        sunflowers.water_if_dry = self.water_if_dry
        sunflowers.ensure_soil = self.ensure_soil
        sunflowers.num_items = self.num_items
        sunflowers.use_item = self.use_item

    def distance_to(self, x: int, y: int) -> int:
        if self.scan_reverse:
            return 100 - x - y

        return x + y

    def move_to(self, x: int, y: int) -> None:
        self.current_position = (x, y)
        self.events.append(("move", self.current_position, self.phase))

    def get_entity_type(self):
        return self.tiles[self.current_position]["entity"]

    def plant(self, entity) -> bool:
        tile = self.tiles[self.current_position]

        if len(self.harvest_records) > 0 and tile["entity"] is None:
            self.phase = "replant"

        tile["entity"] = entity
        tile["mature"] = False
        self.events.append(("plant", self.current_position, self.phase))
        self.plant_records.append((self.cycle_number, self.current_position))
        return True

    def harvest(self) -> None:
        remaining_petals = []

        for position in self.positions:
            tile = self.tiles[position]

            if tile["entity"] == Entities.Sunflower:
                if not tile["mature"]:
                    raise AssertionError("harvest happened before all flowers matured")

                remaining_petals.append(self.petals[position])

        if len(remaining_petals) < 10:
            raise AssertionError("harvest happened with fewer than ten flowers")

        if self.petals[self.current_position] != max(remaining_petals):
            raise AssertionError("harvested a sunflower below the current maximum")

        self.events.append(
            (
                "harvest",
                self.current_position,
                self.petals[self.current_position],
                self.cycle_number,
            )
        )
        self.harvest_records.append(
            (
                self.cycle_number,
                self.current_position,
                self.petals[self.current_position],
                len(remaining_petals),
                8,
            )
        )
        self.tiles[self.current_position]["entity"] = None
        self.tiles[self.current_position]["mature"] = False
        self.power += 8

    def measure(self):
        tile = self.tiles[self.current_position]

        if tile["entity"] != Entities.Sunflower:
            raise AssertionError("measured a tile before planting a sunflower")

        self.measurement_count += 1
        measured_before_maturity = not tile["mature"]
        self.events.append(("measure", self.current_position, measured_before_maturity))
        self.measurement_records.append(
            (self.cycle_number, self.current_position, measured_before_maturity)
        )

        if self.measurement_count == len(self.positions):
            self.phase = "wait"

        return self.petals[self.current_position]

    def can_harvest(self) -> bool:
        tile = self.tiles[self.current_position]
        return tile["entity"] == Entities.Sunflower and tile["mature"]

    def water_if_dry(self, threshold: float) -> None:
        self.events.append(("water", self.current_position, self.phase))

        if self.phase == "wait":
            self.tiles[self.current_position]["mature"] = True

    def ensure_soil(self) -> None:
        pass

    def num_items(self, item):
        if item == Items.Power:
            return self.power

        raise AssertionError(f"unexpected inventory item: {item}")

    def use_item(self, item):
        self.fertilizer_calls += 1
        self.events.append(("fertilize", item, self.phase))
        return True


def assert_cycle(
    simulator: SunflowerSimulator,
    cycle_number: int,
    expected_plant_count: int,
    name: str,
) -> None:
    if len(simulator.positions) < 10:
        raise AssertionError(f"{name}: patch has fewer than ten sunflowers")

    cycle_measurements = []
    for record in simulator.measurement_records:
        if record[0] == cycle_number:
            cycle_measurements.append(record)

    if len(cycle_measurements) != len(simulator.positions):
        raise AssertionError(f"{name}: not every sunflower was measured")

    measured_positions = []
    for record in cycle_measurements:
        measured_positions.append(record[1])

    if len(set(measured_positions)) != len(measured_positions):
        raise AssertionError(f"{name}: a sunflower was measured more than once")

    if not any(record[2] for record in cycle_measurements):
        raise AssertionError(f"{name}: measurement did not occur before maturity")

    cycle_harvests = []
    for record in simulator.harvest_records:
        if record[0] == cycle_number:
            cycle_harvests.append(record)

    expected_harvest_count = len(simulator.positions) - sunflowers.SUNFLOWER_MIN_REMAINING

    if len(cycle_harvests) != expected_harvest_count:
        raise AssertionError(f"{name}: incorrect batch harvest size")

    if cycle_harvests[-1][3] != 10:
        raise AssertionError(f"{name}: final harvest did not leave nine flowers")

    harvested_petals = []
    for record in cycle_harvests:
        harvested_petals.append(record[2])

    if harvested_petals != sorted(harvested_petals, reverse=True):
        raise AssertionError(f"{name}: harvest petal counts are not descending")

    expected_harvest_positions = []
    for petals in range(
        sunflowers.SUNFLOWER_MAX_PETALS,
        sunflowers.SUNFLOWER_MIN_PETALS - 1,
        -1,
    ):
        for position in measured_positions:
            if simulator.petals[position] == petals:
                expected_harvest_positions.append(position)

    actual_harvest_positions = []
    for record in cycle_harvests:
        actual_harvest_positions.append(record[1])

    if actual_harvest_positions != expected_harvest_positions[:expected_harvest_count]:
        raise AssertionError(f"{name}: measured positions lost their petal pairing")

    for record in cycle_harvests:
        if record[3] < 10:
            raise AssertionError(f"{name}: batch dropped below ten flowers")
        if record[4] != 8:
            raise AssertionError(f"{name}: harvest did not receive the 8x bonus")

    harvest_event_indexes = []
    for index in range(len(simulator.events)):
        event = simulator.events[index]

        if event[0] == "harvest" and event[3] == cycle_number:
            harvest_event_indexes.append(index)

    for event in simulator.events[harvest_event_indexes[0] : harvest_event_indexes[-1] + 1]:
        if event[0] == "plant":
            raise AssertionError(f"{name}: replanted before all harvests finished")

    cycle_plants = 0
    for record in simulator.plant_records:
        if record[0] == cycle_number:
            cycle_plants += 1

    if cycle_plants != expected_plant_count:
        raise AssertionError(f"{name}: unexpected planting count: {cycle_plants}")

    if simulator.fertilizer_calls != 0:
        raise AssertionError(f"{name}: fertilizer was used on sunflowers")


def test_patch_area() -> None:
    area = sunflowers.SUNFLOWER_WIDTH * sunflowers.SUNFLOWER_HEIGHT

    if area < 10:
        raise AssertionError(f"sunflower patch has too few tiles: {area}")


def test_cycle_in_both_scan_directions() -> None:
    petals = [7, 15, 9, 15, 8, 10, 7, 14, 11, 8, 15, 12, 9, 13, 7, 10]

    for scan_reverse in (False, True):
        simulator = SunflowerSimulator(petals, scan_reverse)
        simulator.install()
        simulator.start_cycle()
        sunflowers.farm_sunflower_patch()
        assert_cycle(
            simulator,
            1,
            len(simulator.positions)
            + len(simulator.positions)
            - sunflowers.SUNFLOWER_MIN_REMAINING,
            f"scan_reverse={scan_reverse}, cycle=1",
        )

        simulator.start_cycle()
        sunflowers.farm_sunflower_patch()
        assert_cycle(
            simulator,
            2,
            len(simulator.positions) - sunflowers.SUNFLOWER_MIN_REMAINING,
            f"scan_reverse={scan_reverse}, cycle=2",
        )


def test_power_target_skips_cycle() -> None:
    petals = [7] * (sunflowers.SUNFLOWER_WIDTH * sunflowers.SUNFLOWER_HEIGHT)
    simulator = SunflowerSimulator(petals, False)
    simulator.power = sunflowers.POWER_TARGET
    simulator.install()

    if sunflowers.needs_power():
        raise AssertionError("power target did not stop sunflower farming")

    sunflowers.farm_sunflower_patch()

    if simulator.events:
        raise AssertionError(f"power target still ran a sunflower cycle: {simulator.events}")


def test_disabled_patch_falls_through_to_grass() -> None:
    farm_layout.ENABLE_CACTUS_PATCH = True
    farm_layout.ENABLE_PUMPKIN_PATCH = True
    farm_layout.ENABLE_SUNFLOWER_PATCH = False
    farm_layout.ENABLE_TREE_BUSH_STRIP = True
    farm_layout.ENABLE_GRASS_STRIP = True
    farm_layout.ENABLE_CARROT_FILL = True

    positions = sunflowers.get_sunflower_positions()

    for x, y in positions:
        if not farm_layout.is_sunflower_region(x, y):
            raise AssertionError("sunflower position is outside its geometry")

        if farm_layout.target_entity_at(x, y) != Entities.Grass:
            raise AssertionError("disabled sunflower patch did not fall through")

    farm_layout.ENABLE_SUNFLOWER_PATCH = True


def main() -> None:
    test_patch_area()
    test_cycle_in_both_scan_directions()
    test_power_target_skips_cycle()
    test_disabled_patch_falls_through_to_grass()
    print("Passed sunflower lifecycle, ordering, pairing, power, and fallback tests")


if __name__ == "__main__":
    main()
