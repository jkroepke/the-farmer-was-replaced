#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise finite checkerboard tree farming and failure handling."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import parallel_farming  # noqa: E402
import trees  # noqa: E402


class Entities:
    Tree = "Tree"
    Bush = "Bush"


trees.Entities = Entities
REAL_TEND_TREE_ROW = trees.tend_tree_row
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


def test_checkerboard_targets() -> None:
    for y in range(4):
        for x in range(4):
            target = trees.get_tree_target(x, y)

            if x + 1 < 4 and target == trees.get_tree_target(x + 1, y):
                raise AssertionError("neighboring horizontal tiles share a target")

            if y + 1 < 4 and target == trees.get_tree_target(x, y + 1):
                raise AssertionError("neighboring vertical tiles share a target")


def test_rows_cover_world_with_reduced_capacity() -> None:
    trees.get_world_size = lambda: 5

    for child_capacity in (0, 1, 4):
        simulator = DispatchSimulator(child_capacity)
        simulator.install()
        recorded_rows.clear()
        trees.tend_tree_row = record_row

        if not trees.farm_tree_cycle():
            raise AssertionError(f"capacity {child_capacity} reported failure")

        if sorted(recorded_rows) != list(range(5)):
            raise AssertionError(
                f"capacity {child_capacity} skipped or repeated rows: {recorded_rows}"
            )

        if simulator.active_workers:
            raise AssertionError(f"capacity {child_capacity} left workers active")


def test_finite_row_preserves_lifecycle() -> None:
    events = []
    current_entity = {"value": None}
    trees.tend_tree_row = REAL_TEND_TREE_ROW
    trees.get_world_size = lambda: 3
    trees.move_to = lambda x, y: events.append(("move", x, y))
    trees.can_harvest = lambda: True
    trees.harvest = lambda: events.append("harvest")
    trees.get_entity_type = lambda: current_entity["value"]

    def plant_target(target) -> bool:
        events.append(("plant", target))
        current_entity["value"] = target
        return True

    trees.plant_target_entity = plant_target
    trees.water_if_dry = lambda threshold: events.append("water")

    if not trees.tend_tree_row(1):
        raise AssertionError("successful tree row reported failure")

    planted_targets = []
    for event in events:
        if event[0] == "plant":
            planted_targets.append(event[1])

    if planted_targets != [Entities.Tree, Entities.Bush, Entities.Tree]:
        raise AssertionError(f"checkerboard planting changed: {planted_targets}")

    if events.count("harvest") != 3 or events.count("water") != 3:
        raise AssertionError(f"tree row lifecycle changed: {events}")


def test_failed_plant_aborts_row() -> None:
    calls = []
    trees.get_world_size = lambda: 4
    trees.move_to = lambda x, y: None
    trees.can_harvest = lambda: False

    def fail_on_second_target(target) -> bool:
        calls.append(target)
        return len(calls) != 2

    trees.plant_target_entity = fail_on_second_target
    if trees.tend_tree_row(0):
        raise AssertionError("failed tree planting did not abort the row")

    if len(calls) != 2:
        raise AssertionError("tree row continued after planting failure")


def main() -> None:
    test_checkerboard_targets()
    test_rows_cover_world_with_reduced_capacity()
    test_finite_row_preserves_lifecycle()
    test_failed_plant_aborts_row()
    print("Passed bounded tree, checkerboard, dispatch, and failure tests")


if __name__ == "__main__":
    main()
