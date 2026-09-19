#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise planting result propagation and failed-plant termination."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import cactus  # noqa: E402
import planting  # noqa: E402
import pumpkins  # noqa: E402
import sunflowers  # noqa: E402


class Entities:
    Cactus = "Cactus"
    Pumpkin = "Pumpkin"
    Dead_Pumpkin = "Dead Pumpkin"
    Sunflower = "Sunflower"
    Carrot = "Carrot"
    Tree = "Tree"


class Grounds:
    Soil = "Soil"


planting.Entities = Entities
planting.Grounds = Grounds
cactus.Entities = Entities
pumpkins.Entities = Entities
sunflowers.Entities = Entities


class PlantSimulator:
    def __init__(self, plant_result: bool) -> None:
        self.plant_result = plant_result
        self.entity = None
        self.plant_calls = []
        self.water_calls = 0

    def install(self) -> None:
        planting.get_entity_type = self.get_entity_type
        planting.get_ground_type = self.get_ground_type
        planting.till = self.till
        planting.plant = self.plant

        cactus.ensure_soil = self.ensure_soil
        cactus.plant = self.plant
        cactus.get_entity_type = self.get_entity_type
        cactus.water_if_dry = self.water_if_dry

        pumpkins.ensure_soil = self.ensure_soil
        pumpkins.plant = self.plant
        pumpkins.get_entity_type = self.get_entity_type
        pumpkins.water_if_dry = self.water_if_dry

        sunflowers.ensure_soil = self.ensure_soil
        sunflowers.plant = self.plant
        sunflowers.get_entity_type = self.get_entity_type
        sunflowers.water_if_dry = self.water_if_dry

    def get_entity_type(self):
        return self.entity

    def get_ground_type(self):
        return Grounds.Soil

    def till(self) -> None:
        pass

    def ensure_soil(self) -> None:
        pass

    def plant(self, entity) -> bool:
        self.plant_calls.append(entity)

        if not self.plant_result:
            return False

        self.entity = entity
        return True

    def water_if_dry(self, threshold) -> None:
        self.water_calls += 1

    def can_harvest(self) -> bool:
        return False


def test_generic_target_propagates_plant_result() -> None:
    simulator = PlantSimulator(False)
    simulator.install()

    if planting.plant_target_entity(Entities.Carrot):
        raise AssertionError("failed carrot planting reported success")

    if planting.plant_target_entity(Entities.Tree):
        raise AssertionError("failed tree planting reported success")

    simulator.entity = Entities.Carrot
    if not planting.plant_target_entity(Entities.Carrot):
        raise AssertionError("existing target was reported as failed")


def test_crop_plant_helpers_propagate_failure() -> None:
    simulator = PlantSimulator(False)
    simulator.install()

    if cactus.plant_cactus():
        raise AssertionError("failed cactus planting reported success")

    if pumpkins.plant_pumpkin():
        raise AssertionError("failed pumpkin planting reported success")

    if sunflowers.plant_sunflower():
        raise AssertionError("failed sunflower planting reported success")

    if simulator.water_calls != 0:
        raise AssertionError("failed sunflower planting was watered")


def test_readiness_stops_after_failed_plant() -> None:
    simulator = PlantSimulator(False)
    simulator.install()

    if pumpkins.pumpkin_is_ready() is not None:
        raise AssertionError("failed pumpkin replacement did not return failure")

    if cactus.maintain_cactus_tile() is not None:
        raise AssertionError("failed cactus replacement did not return failure")

    if sunflowers.prepare_sunflower_tile():
        raise AssertionError("failed sunflower preparation reported success")

    cactus.distance_to = lambda x, y: 0
    pumpkins.distance_to = lambda x, y: 0
    sunflowers.distance_to = lambda x, y: 0
    pumpkins.move_to = lambda x, y: None
    if pumpkins.wait_for_positions([(0, 0)]):
        raise AssertionError("pumpkin readiness loop ignored failed planting")

    cactus.move_to = lambda x, y: None
    if cactus.wait_for_cactuses([(0, 0)]):
        raise AssertionError("cactus readiness loop ignored failed planting")

    sunflowers.move_to = lambda x, y: None
    if sunflowers.plant_and_measure_sunflowers([(0, 0)]) is not None:
        raise AssertionError("sunflower preparation loop ignored failed planting")


def main() -> None:
    test_generic_target_propagates_plant_result()
    test_crop_plant_helpers_propagate_failure()
    test_readiness_stops_after_failed_plant()
    print("Passed planting failure propagation and termination tests")


if __name__ == "__main__":
    main()
