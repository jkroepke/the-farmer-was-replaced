#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise bounded hay cycles, mode transitions, and hat policy."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import hay  # noqa: E402
import parallel_farming  # noqa: E402


REAL_HARVEST_GRASS_ROW = hay.harvest_grass_row
recorded_rows = []


def record_row(row_y: int) -> None:
    recorded_rows.append(row_y)


class Entities:
    Grass = "Grass"
    Carrot = "Carrot"


class Grounds:
    Grassland = "Grassland"
    Soil = "Soil"


class Hats:
    Brown_Hat = "Brown Hat"
    Gray_Hat = "Gray Hat"
    Green_Hat = "Green Hat"
    Purple_Hat = "Purple Hat"
    Straw_Hat = "Straw Hat"


hay.Entities = Entities
hay.Grounds = Grounds
hay.Hats = Hats


class Worker:
    def __init__(self, function, job_value) -> None:
        self.function = function
        self.job_value = job_value

    def run(self):
        return self.function(self.job_value)


class DispatchSimulator:
    def __init__(self, child_capacity: int) -> None:
        self.child_capacity = child_capacity
        self.active_workers = []

    def install(self) -> None:
        parallel_farming.spawn_drone = self.spawn_drone
        parallel_farming.wait_for = self.wait_for

    def spawn_drone(self, function, job_value):
        if len(self.active_workers) >= self.child_capacity:
            return None

        worker = Worker(function, job_value)
        self.active_workers.append(worker)
        return worker

    def wait_for(self, worker):
        result = worker.run()
        self.active_workers.remove(worker)
        return result


class HayTileSimulator:
    def __init__(self, entity, ground, ready: bool) -> None:
        self.entity = entity
        self.ground = ground
        self.ready = ready
        self.events = []

    def install(self) -> None:
        hay.get_entity_type = self.get_entity_type
        hay.get_ground_type = self.get_ground_type
        hay.can_harvest = self.can_harvest
        hay.harvest = self.harvest
        hay.till = self.till
        hay.water_if_dry = self.water_if_dry

    def get_entity_type(self):
        return self.entity

    def get_ground_type(self):
        return self.ground

    def can_harvest(self) -> bool:
        return self.ready

    def harvest(self) -> None:
        self.events.append("harvest")
        self.entity = None
        self.ready = False

    def till(self) -> None:
        self.events.append("till")
        self.ground = Grounds.Grassland

    def water_if_dry(self, threshold) -> None:
        self.events.append("water")


def test_mode_transition_clears_and_tills() -> None:
    simulator = HayTileSimulator(Entities.Carrot, Grounds.Soil, False)
    simulator.install()

    hay.tend_hay_tile()

    if simulator.events != ["harvest", "till", "water"]:
        raise AssertionError(f"mode transition changed: {simulator.events}")

    if simulator.ground != Grounds.Grassland or simulator.entity is not None:
        raise AssertionError("mode transition did not produce empty grassland")


def test_grass_behavior() -> None:
    ready = HayTileSimulator(Entities.Grass, Grounds.Grassland, True)
    ready.install()
    hay.tend_hay_tile()

    if ready.events != ["harvest", "water"]:
        raise AssertionError(f"ready grass behavior changed: {ready.events}")

    soil_grass = HayTileSimulator(Entities.Grass, Grounds.Soil, False)
    soil_grass.install()
    hay.tend_hay_tile()

    if soil_grass.events != ["harvest", "till", "water"]:
        raise AssertionError(f"soil grass behavior changed: {soil_grass.events}")


def test_hat_policy() -> None:
    hay.random = lambda: 0
    hay.num_unlocked = lambda hat: hat in (Hats.Brown_Hat, Hats.Purple_Hat)

    if hay.random_color_hat() != Hats.Brown_Hat:
        raise AssertionError("unlocked color hats were not selected")

    hay.num_unlocked = lambda hat: False
    if hay.random_color_hat() != Hats.Straw_Hat:
        raise AssertionError("hay policy did not fall back to the straw hat")


def test_row_dispatch_with_reduced_capacity() -> None:
    for child_capacity in (0, 1, 3):
        simulator = DispatchSimulator(child_capacity)
        simulator.install()
        recorded_rows.clear()

        hay.get_world_size = lambda: 5
        hay.harvest_grass_row = record_row
        if not hay.farm_hay_cycle():
            raise AssertionError(f"capacity {child_capacity} reported failure")

        if sorted(recorded_rows) != list(range(5)):
            raise AssertionError(
                f"capacity {child_capacity} skipped or repeated rows: {recorded_rows}"
            )

        if simulator.active_workers:
            raise AssertionError(f"capacity {child_capacity} left workers active")


def test_finite_row() -> None:
    events = []
    hay.harvest_grass_row = REAL_HARVEST_GRASS_ROW
    hay.get_world_size = lambda: 4
    hay.move_to = lambda x, y: events.append(("move", x, y))
    hay.change_hat = lambda hat: events.append(("hat", hat))
    hay.random_color_hat = lambda: Hats.Brown_Hat
    hay.tend_hay_tile = lambda: events.append("tend")

    hay.harvest_grass_row(2)

    if events.count("tend") != 4:
        raise AssertionError(f"finite row tended an unexpected number of tiles: {events}")

    if events[0] != ("move", 0, 2) or events[1] != ("hat", Hats.Brown_Hat):
        raise AssertionError(f"row setup changed: {events}")


def main() -> None:
    test_mode_transition_clears_and_tills()
    test_grass_behavior()
    test_hat_policy()
    test_row_dispatch_with_reduced_capacity()
    test_finite_row()
    print("Passed bounded hay, transition, hat, and dispatch tests")


if __name__ == "__main__":
    main()
