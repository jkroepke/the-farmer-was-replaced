#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Exercise bounded indexed drone dispatch and result collection."""

from __future__ import annotations

import sys
from pathlib import Path


SAVE_DIRECTORY = Path(__file__).resolve().parents[1] / "Save0"
sys.path.insert(0, str(SAVE_DIRECTORY))

import parallel_farming  # noqa: E402


class Worker:
    def __init__(self, function, job_value) -> None:
        self.function = function
        self.job_value = job_value
        self.result = None
        self.completed = False

    def run(self):
        self.result = self.function(self.job_value)
        self.completed = True
        return self.result


class DispatcherSimulator:
    def __init__(self, child_capacity: int, failed_spawn_indexes=None) -> None:
        self.child_capacity = child_capacity
        self.failed_spawn_indexes = set(failed_spawn_indexes or [])
        self.spawn_attempts = 0
        self.active_workers = []
        self.completed_workers = []
        self.events = []

    def install(self) -> None:
        parallel_farming.spawn_drone = self.spawn_drone
        parallel_farming.wait_for = self.wait_for

    def spawn_drone(self, function, job_value):
        spawn_index = self.spawn_attempts
        self.spawn_attempts += 1
        self.events.append(("spawn", job_value))

        if spawn_index in self.failed_spawn_indexes:
            return None

        if len(self.active_workers) >= self.child_capacity:
            return None

        worker = Worker(function, job_value)
        self.active_workers.append(worker)
        return worker

    def wait_for(self, worker):
        if worker not in self.active_workers:
            raise AssertionError("dispatcher waited for an unknown worker")

        self.events.append(("wait", worker.job_value))
        result = worker.run()
        self.active_workers.remove(worker)
        self.completed_workers.append(worker)
        return result


def record_job(simulator: DispatcherSimulator, job_value: int) -> int:
    simulator.events.append(("run", job_value))
    return job_value * 10


def assert_dispatch(child_capacity: int, job_values: list[int], name: str) -> None:
    simulator = DispatcherSimulator(child_capacity)
    simulator.install()

    results = parallel_farming.dispatch_indexed_jobs(
        job_values,
        lambda job_value: record_job(simulator, job_value),
    )

    expected_results = []
    for job_value in job_values:
        expected_results.append(job_value * 10)

    if results != expected_results:
        raise AssertionError(f"{name}: results changed: {results}")

    run_values = []
    for event in simulator.events:
        if event[0] == "run":
            run_values.append(event[1])

    if sorted(run_values) != sorted(job_values):
        raise AssertionError(f"{name}: jobs were not run exactly once: {run_values}")

    if len(simulator.active_workers) != 0:
        raise AssertionError(f"{name}: workers remained active")


def test_capacity_variants() -> None:
    assert_dispatch(0, [2, 4, 6, 8], "zero child capacity")
    assert_dispatch(2, [2, 4, 6, 8], "partial child capacity")
    assert_dispatch(4, [2, 4, 6, 8], "full child capacity")


def test_failed_spawn_runs_job_synchronously() -> None:
    job_values = [10, 20, 30, 40, 50]
    simulator = DispatcherSimulator(5, failed_spawn_indexes=[2])
    simulator.install()

    results = parallel_farming.dispatch_indexed_jobs(
        job_values,
        lambda job_value: record_job(simulator, job_value),
    )

    if results != [100, 200, 300, 400, 500]:
        raise AssertionError(f"failed spawn changed result collection: {results}")

    run_values = []
    for event in simulator.events:
        if event[0] == "run":
            run_values.append(event[1])

    if sorted(run_values) != sorted(job_values):
        raise AssertionError(f"failed spawn dropped or repeated a job: {run_values}")

    if simulator.events.index(("run", 30)) > simulator.events.index(("spawn", 40)):
        raise AssertionError("failed spawn did not run synchronously")


def test_empty_dispatch() -> None:
    simulator = DispatcherSimulator(2)
    simulator.install()

    results = parallel_farming.dispatch_indexed_jobs(
        [],
        lambda job_value: record_job(simulator, job_value),
    )

    if results != []:
        raise AssertionError(f"empty dispatch returned unexpected results: {results}")

    if simulator.events:
        raise AssertionError(f"empty dispatch performed work: {simulator.events}")


def main() -> None:
    test_capacity_variants()
    test_failed_spawn_runs_job_synchronously()
    test_empty_dispatch()
    print("Passed indexed drone dispatch tests")


if __name__ == "__main__":
    main()
