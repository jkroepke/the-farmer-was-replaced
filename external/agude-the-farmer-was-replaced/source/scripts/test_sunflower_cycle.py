#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise full-field sunflower measurement, tier ordering, and barriers."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import parallel_farming  # noqa: E402
import sunflowers  # noqa: E402


class Items:
    Power = "Power"


sunflowers.Items = Items
sunflowers.POWER_TARGET = 1000
REAL_GROW_SUNFLOWER_ROW = sunflowers.grow_sunflower_row
recorded_rows = []
harvested_positions = []
replanted_positions = []


PETALS_BY_ROW = [
    [15, 7, 14, 7],
    [13, 12, 11, 10],
    [9, 8, 15, 14],
    [13, 12, 11, 10],
]


def row_measurements(row_y: int):
    buckets = [[], [], [], [], [], [], [], [], []]

    for x in range(4):
        petals = PETALS_BY_ROW[row_y][x]
        buckets[petals - sunflowers.SUNFLOWER_MIN_PETALS].append((x, row_y))

    return buckets


def record_row(row_y: int):
    recorded_rows.append(row_y)
    return row_measurements(row_y)


def record_harvest(position) -> bool:
    harvested_positions.append(position)
    return True


def record_replant(position) -> bool:
    replanted_positions.append(position)
    return True


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
        self.events = []

    def install(self) -> None:
        parallel_farming.spawn_drone = self.spawn_drone
        parallel_farming.wait_for = self.wait_for

    def spawn_drone(self, function, job_value):
        self.events.append(("spawn", job_value))

        if len(self.active_workers) >= self.child_capacity:
            return None

        worker = Worker(function, job_value)
        self.active_workers.append(worker)
        return worker

    def wait_for(self, worker):
        self.events.append(("wait", worker.job_value))
        result = worker.run()
        self.active_workers.remove(worker)
        return result


def install_recorded_cycle(child_capacity: int) -> DispatchSimulator:
    simulator = DispatchSimulator(child_capacity)
    simulator.install()
    recorded_rows.clear()
    harvested_positions.clear()
    replanted_positions.clear()
    sunflowers.get_world_size = lambda: 4
    sunflowers.num_items = lambda item: 0
    sunflowers.grow_sunflower_row = record_row
    sunflowers.harvest_sunflower_position = record_harvest
    sunflowers.replant_sunflower_position = record_replant
    return simulator


def test_full_cycle_orders_and_replants() -> None:
    expected_harvests = [
        (0, 0),
        (2, 2),
        (2, 0),
        (3, 2),
        (0, 1),
        (0, 3),
        (1, 1),
    ]

    for child_capacity in (0, 2, 8):
        simulator = install_recorded_cycle(child_capacity)

        if not sunflowers.farm_sunflower_cycle():
            raise AssertionError(f"capacity {child_capacity} reported failure")

        if sorted(recorded_rows) != [0, 1, 2, 3]:
            raise AssertionError(f"rows were skipped or repeated: {recorded_rows}")

        if set(harvested_positions) != set(expected_harvests):
            raise AssertionError(f"selected harvest positions changed: {harvested_positions}")

        harvested_petals = []
        for x, y in harvested_positions:
            harvested_petals.append(PETALS_BY_ROW[y][x])

        if harvested_petals != sorted(harvested_petals, reverse=True):
            raise AssertionError(f"global petal ordering changed: {harvested_petals}")

        if set(replanted_positions) != set(harvested_positions):
            raise AssertionError("replanting did not match selected harvests")

        first_replant = len(harvested_positions)
        if len(replanted_positions) != first_replant:
            raise AssertionError("replanting count did not leave nine flowers")

        if simulator.active_workers:
            raise AssertionError(f"capacity {child_capacity} left workers active")


def test_measurements_keep_all_rows() -> None:
    row_data = []
    for row_y in range(4):
        row_data.append(row_measurements(row_y))

    combined = sunflowers.combine_row_measurements(row_data)
    positions = []
    for bucket in combined:
        for position in bucket:
            positions.append(position)

    if len(positions) != 16 or len(set(positions)) != 16:
        raise AssertionError("worker measurement combination lost a sunflower")


def test_failed_row_stops_before_harvest() -> None:
    simulator = install_recorded_cycle(2)

    def fail_row(row_y: int):
        if row_y == 1:
            return None

        return row_measurements(row_y)

    sunflowers.grow_sunflower_row = fail_row
    if sunflowers.farm_sunflower_cycle():
        raise AssertionError("failed sunflower row reported cycle success")

    if harvested_positions or replanted_positions:
        raise AssertionError("failed measurement cycle harvested or replanted")

    if simulator.active_workers:
        raise AssertionError("failed measurement cycle returned before joining workers")


def test_full_cycle_ignores_static_target() -> None:
    install_recorded_cycle(2)
    sunflowers.num_items = lambda item: sunflowers.POWER_TARGET

    if not sunflowers.farm_sunflower_cycle():
        raise AssertionError("full-field cycle stopped at the static target")

    if sorted(recorded_rows) != [0, 1, 2, 3]:
        raise AssertionError("full-field cycle skipped work at the static target")


def test_real_row_returns_on_failed_plant() -> None:
    sunflowers.grow_sunflower_row = REAL_GROW_SUNFLOWER_ROW
    sunflowers.get_world_size = lambda: 1
    sunflowers.move_to = lambda x, y: None
    sunflowers.prepare_sunflower_tile = lambda: False

    if sunflowers.grow_sunflower_row(0) is not None:
        raise AssertionError("failed sunflower plant entered measurement")


def main() -> None:
    test_full_cycle_orders_and_replants()
    test_measurements_keep_all_rows()
    test_failed_row_stops_before_harvest()
    test_full_cycle_ignores_static_target()
    test_real_row_returns_on_failed_plant()
    print("Passed bounded sunflower cycle, measurement, ordering, and failure tests")


if __name__ == "__main__":
    main()
