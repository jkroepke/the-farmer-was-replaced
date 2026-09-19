#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise bounded carrot rows, dispatch, and planting failure handling."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import carrots  # noqa: E402
import parallel_farming  # noqa: E402


class Entities:
    Carrot = "Carrot"


carrots.Entities = Entities
REAL_TEND_CARROT_ROW = carrots.tend_carrot_row
recorded_rows = []


def record_row(row_y: int) -> bool:
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


def test_rows_cover_world_with_reduced_capacity() -> None:
    for child_capacity in (0, 1, 4):
        simulator = DispatchSimulator(child_capacity)
        simulator.install()
        recorded_rows.clear()

        carrots.get_world_size = lambda: 5
        carrots.tend_carrot_row = record_row

        if not carrots.farm_carrot_cycle():
            raise AssertionError(f"capacity {child_capacity} reported failure")

        if sorted(recorded_rows) != list(range(5)):
            raise AssertionError(
                f"capacity {child_capacity} skipped or repeated rows: {recorded_rows}"
            )

        if simulator.active_workers:
            raise AssertionError(f"capacity {child_capacity} left workers active")


def test_row_is_finite_and_propagates_failure() -> None:
    events = []
    carrots.tend_carrot_row = REAL_TEND_CARROT_ROW
    carrots.get_world_size = lambda: 4
    carrots.move_to = lambda x, y: events.append(("move", x, y))

    def tend_successfully(target) -> bool:
        events.append(("tend", target))
        return True

    carrots.tend_regular_tile = tend_successfully
    if not carrots.tend_carrot_row(2):
        raise AssertionError("successful carrot row reported failure")

    if events.count(("tend", "Carrot")) != 4:
        raise AssertionError(f"carrot row did not tend every tile: {events}")

    calls = []

    def fail_on_second_tile(target) -> bool:
        calls.append(target)
        return len(calls) != 2

    carrots.tend_regular_tile = fail_on_second_tile
    if carrots.tend_carrot_row(2):
        raise AssertionError("failed carrot planting did not abort the row")

    if len(calls) != 2:
        raise AssertionError("carrot row continued after planting failure")


def test_regular_carrot_lifecycle_propagates_planting() -> None:
    import regular_farming

    regular_farming.can_harvest = lambda: False
    regular_farming.plant_target_entity = lambda target: False
    regular_farming.water_if_dry = lambda threshold: None

    if regular_farming.tend_regular_tile("Carrot"):
        raise AssertionError("regular carrot helper hid planting failure")


def main() -> None:
    test_rows_cover_world_with_reduced_capacity()
    test_row_is_finite_and_propagates_failure()
    test_regular_carrot_lifecycle_propagates_planting()
    print("Passed bounded carrot, dispatch, lifecycle, and failure tests")


if __name__ == "__main__":
    main()
