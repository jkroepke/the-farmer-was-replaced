#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise bounded cactus phases, region geometry, sorting, and barriers."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import cactus  # noqa: E402
import parallel_farming  # noqa: E402


class Entities:
    Cactus = "Cactus"
    Pumpkin = "Pumpkin"
    Dead_Pumpkin = "Dead Pumpkin"


cactus.Entities = Entities
cactus.FERTILIZE_CACTUS_HARVEST = False
REAL_GROW_CACTUS_ROW_JOB = cactus.grow_cactus_row_job
recorded_jobs = []


def record_growth(job) -> bool:
    recorded_jobs.append(("grow", job))
    return True


def record_row_sort(job) -> bool:
    recorded_jobs.append(("row", job))
    return True


def record_column_sort(job) -> bool:
    recorded_jobs.append(("column", job))
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


def setup_recorded_cycle(child_capacity: int) -> DispatchSimulator:
    simulator = DispatchSimulator(child_capacity)
    simulator.install()
    recorded_jobs.clear()
    cactus.get_world_size = lambda: 5
    cactus.grow_cactus_row_job = record_growth
    cactus.sort_cactus_row_job = record_row_sort
    cactus.sort_cactus_column_job = record_column_sort
    cactus.move_to = lambda x, y: simulator.events.append(("move", x, y))
    cactus.can_harvest = lambda: True
    cactus.harvest = lambda: simulator.events.append("harvest")
    return simulator


def test_region_geometry_and_capacity() -> None:
    for child_capacity in (0, 1, 4):
        simulator = setup_recorded_cycle(child_capacity)

        if not cactus.farm_cactus_cycle(2, 3, 4, 3, False):
            raise AssertionError(f"capacity {child_capacity} reported failure")

        growth_jobs = []
        row_jobs = []
        column_jobs = []
        for phase, job in recorded_jobs:
            if phase == "grow":
                growth_jobs.append(job)
            elif phase == "row":
                row_jobs.append(job)
            else:
                column_jobs.append(job)

        if len(growth_jobs) != 3 or len(row_jobs) != 3 or len(column_jobs) != 4:
            raise AssertionError("cactus region phase coverage changed")

        for job in growth_jobs + row_jobs:
            if job[0] not in (3, 4, 5) or job[1:5] != (2, 3, 4, 3):
                raise AssertionError(f"row geometry was not explicit: {job}")

        for job in column_jobs:
            if job[0] not in (2, 3, 4, 5) or job[1:5] != (2, 3, 4, 3):
                raise AssertionError(f"column geometry was not explicit: {job}")

        if simulator.events.count("harvest") != 1:
            raise AssertionError("cactus cycle did not bulk harvest exactly once")

        if simulator.active_workers:
            raise AssertionError(f"capacity {child_capacity} left workers active")


def test_phase_barriers() -> None:
    simulator = setup_recorded_cycle(2)

    if not cactus.farm_cactus_cycle(0, 0, 2, 2, True):
        raise AssertionError("reverse cactus cycle reported failure")

    harvest_index = simulator.events.index("harvest")
    last_wait = -1
    for index in range(harvest_index):
        if simulator.events[index][0] == "wait":
            last_wait = index

    if last_wait == -1:
        raise AssertionError("cactus cycle did not wait for workers")

    for event in simulator.events[last_wait + 1 : harvest_index]:
        if event[0] == "wait":
            raise AssertionError("cactus harvest started before all waits completed")

    reverse_flags = []
    for phase, job in recorded_jobs:
        if phase != "grow":
            reverse_flags.append(job[-1])

    if reverse_flags != [True] * len(reverse_flags):
        raise AssertionError("reverse sort policy was not passed to every sort job")


def test_failed_phase_aborts_after_join() -> None:
    simulator = setup_recorded_cycle(2)

    def fail_row_sort(job) -> bool:
        recorded_jobs.append(("row", job))
        return job[0] != 1

    cactus.sort_cactus_row_job = fail_row_sort
    if cactus.farm_cactus_cycle(0, 0, 2, 3, False):
        raise AssertionError("failed cactus row sort reported success")

    if "harvest" in simulator.events:
        raise AssertionError("failed cactus phase harvested partial work")

    if simulator.active_workers:
        raise AssertionError("failed cactus phase returned before joining workers")


def test_real_growth_job_is_bounded() -> None:
    cactus.grow_cactus_row_job = REAL_GROW_CACTUS_ROW_JOB
    cactus.move_to = lambda x, y: None
    cactus.distance_to = lambda x, y: 0
    cactus.maintain_cactus_tile = lambda: True

    if not cactus.grow_cactus_row_job((0, 0, 0, 1, 1, False)):
        raise AssertionError("mature single-tile cactus job reported failure")


def main() -> None:
    test_region_geometry_and_capacity()
    test_phase_barriers()
    test_failed_phase_aborts_after_join()
    test_real_growth_job_is_bounded()
    print("Passed bounded cactus region, sorting, barriers, and failure tests")


if __name__ == "__main__":
    main()
