#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise bounded full-field pumpkin growth and bulk harvest barriers."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import parallel_farming  # noqa: E402
import pumpkins  # noqa: E402


class Entities:
    Pumpkin = "Pumpkin"
    Dead_Pumpkin = "Dead Pumpkin"


pumpkins.Entities = Entities
pumpkins.FERTILIZE_PUMPKIN_HARVEST = False
REAL_GROW_PUMPKIN_ROW = pumpkins.grow_pumpkin_row_until_ready
recorded_rows = []


def record_successful_row(row_y: int) -> bool:
    recorded_rows.append(row_y)
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


def test_rows_cover_world_with_reduced_capacity() -> None:
    pumpkins.get_world_size = lambda: 5
    pumpkins.grow_pumpkin_row_until_ready = record_successful_row

    for child_capacity in (0, 1, 4):
        simulator = DispatchSimulator(child_capacity)
        simulator.install()
        recorded_rows.clear()
        pumpkins.move_to = lambda x, y: None
        pumpkins.can_harvest = lambda: True
        pumpkins.harvest = lambda: None

        if not pumpkins.farm_pumpkin_cycle():
            raise AssertionError(f"capacity {child_capacity} reported failure")

        if sorted(recorded_rows) != list(range(5)):
            raise AssertionError(
                f"capacity {child_capacity} skipped or repeated rows: {recorded_rows}"
            )

        if simulator.active_workers:
            raise AssertionError(f"capacity {child_capacity} left workers active")


def test_full_cycle_has_one_post_barrier_harvest() -> None:
    simulator = DispatchSimulator(2)
    simulator.install()
    pumpkins.get_world_size = lambda: 4
    pumpkins.grow_pumpkin_row_until_ready = record_successful_row
    pumpkins.move_to = lambda x, y: simulator.events.append(("move", x, y))
    pumpkins.can_harvest = lambda: True
    pumpkins.harvest = lambda: simulator.events.append("harvest")

    if not pumpkins.farm_pumpkin_cycle():
        raise AssertionError("successful pumpkin cycle reported failure")

    if simulator.events.count("harvest") != 1:
        raise AssertionError("pumpkin cycle harvested an unexpected number of times")

    harvest_index = simulator.events.index("harvest")
    for event in simulator.events[:harvest_index]:
        if event[0] == "spawn":
            continue
        if event[0] == "wait":
            continue
        if event[0] == "move":
            continue
        if event == "harvest":
            raise AssertionError("harvest happened before the barrier")

    if simulator.events[harvest_index - 1] != ("move", 3, 3):
        raise AssertionError("bulk harvest did not use the final world tile")


def test_failed_worker_aborts_before_harvest() -> None:
    simulator = DispatchSimulator(2)
    simulator.install()
    pumpkins.get_world_size = lambda: 4
    pumpkins.move_to = lambda x, y: simulator.events.append(("move", x, y))
    pumpkins.can_harvest = lambda: True
    pumpkins.harvest = lambda: simulator.events.append("harvest")

    def fail_row(row_y: int) -> bool:
        return row_y != 1

    pumpkins.grow_pumpkin_row_until_ready = fail_row
    if pumpkins.farm_pumpkin_cycle():
        raise AssertionError("failed pumpkin row reported cycle success")

    if "harvest" in simulator.events:
        raise AssertionError("failed pumpkin cycle harvested partial growth")

    if simulator.active_workers:
        raise AssertionError("failed pumpkin cycle returned before joining workers")


def test_real_row_is_bounded() -> None:
    pumpkins.grow_pumpkin_row_until_ready = REAL_GROW_PUMPKIN_ROW
    pumpkins.get_world_size = lambda: 1
    pumpkins.distance_to = lambda x, y: 0
    pumpkins.move_to = lambda x, y: None
    pumpkins.pumpkin_is_ready = lambda: True

    if not pumpkins.grow_pumpkin_row_until_ready(0):
        raise AssertionError("mature single-tile pumpkin row reported failure")


def main() -> None:
    test_rows_cover_world_with_reduced_capacity()
    test_full_cycle_has_one_post_barrier_harvest()
    test_failed_worker_aborts_before_harvest()
    test_real_row_is_bounded()
    print("Passed bounded pumpkin growth, barriers, harvest, and failure tests")


if __name__ == "__main__":
    main()
