# Drone memory semantics probe.
#
# Historical reference:
# nql1314/The-Farmer-Was-Replaced-AI-Code
# archived/ref_test.py
# archived/test_drone_memory.py
# archived/shared_memory_examples.py
# revision 688325db004607563e59535a15ce94fad092ff9f
#
# The historical engine allowed multiple drones to obtain the same mutable
# object through wait_for(source). Current TFWR documentation says each drone
# has its own memory and spawn arguments are copied.
#
# This probe separates those behaviors into deterministic, mostly sequential
# tests so scheduling races cannot make shared-memory behavior look isolated.


tests_total = 0
tests_passed = 0

global_counter = 0
source_handle = None


def report(name, passed, detail):
    global tests_total
    global tests_passed

    tests_total += 1

    if passed:
        tests_passed += 1
        quick_print(
            "DRONE_MEMORY",
            name,
            "PASS",
            detail
        )
    else:
        quick_print(
            "DRONE_MEMORY",
            name,
            "FAIL",
            detail
        )


def global_worker():
    global global_counter

    global_counter += 1

    return global_counter


def argument_list_worker(data):
    data.append(20)

    return data


def argument_nested_worker(data):
    data["items"].append(2)
    data["nested"]["value"] = 2

    return data


def create_closure_worker(data):
    def worker():
        data.append(6)

        return data

    return worker


def return_value_worker():
    return {
        "items": [1, 2],
        "nested": {
            "value": 3
        }
    }


def create_list_source():
    return []


def create_nested_source():
    return {
        "items": [],
        "nested": {
            "value": 0
        }
    }


def create_queue_source():
    return {
        "tasks": [1, 2, 3, 4],
        "results": {}
    }


def source_append_worker(marker):
    data = wait_for(
        source_handle
    )

    data.append(
        marker
    )

    return data


def source_repeat_worker():
    first = wait_for(
        source_handle
    )

    first.append(
        31
    )

    second = wait_for(
        source_handle
    )

    if len(second) == 0:
        return "copy-per-wait"

    if (
        len(second) == 1
        and second[0] == 31
    ):
        return "same-drone-alias"

    return "unexpected"


def source_nested_worker(marker):
    data = wait_for(
        source_handle
    )

    data["items"].append(
        marker
    )

    data["nested"]["value"] = marker

    return data


def source_queue_worker(marker):
    queue = wait_for(
        source_handle
    )

    if len(queue["tasks"]) == 0:
        return [
            marker,
            -1,
            0
        ]

    task = queue["tasks"][0]

    queue["tasks"] = queue["tasks"][1:]
    queue["results"][marker] = task

    return [
        marker,
        task,
        len(queue["tasks"])
    ]


def test_global_isolation():
    global global_counter

    global_counter = 0

    drone = spawn_drone(
        global_worker
    )

    if drone == None:
        report(
            "global",
            False,
            "spawn-failed"
        )
        return

    worker_result = wait_for(
        drone
    )

    report(
        "global",
        (
            worker_result == 1
            and global_counter == 0
        ),
        "worker-mutates-parent-stays-zero"
    )


def test_spawn_argument_list():
    data = [10]

    drone = spawn_drone(
        argument_list_worker,
        data
    )

    if drone == None:
        report(
            "spawn-arg-list",
            False,
            "spawn-failed"
        )
        return

    worker_result = wait_for(
        drone
    )

    passed = (
        len(data) == 1
        and data[0] == 10
        and len(worker_result) == 2
        and worker_result[0] == 10
        and worker_result[1] == 20
    )

    report(
        "spawn-arg-list",
        passed,
        "copied"
    )


def test_spawn_argument_nested():
    data = {
        "items": [1],
        "nested": {
            "value": 1
        }
    }

    drone = spawn_drone(
        argument_nested_worker,
        data
    )

    if drone == None:
        report(
            "spawn-arg-nested",
            False,
            "spawn-failed"
        )
        return

    worker_result = wait_for(
        drone
    )

    parent_unchanged = (
        len(data["items"]) == 1
        and data["items"][0] == 1
        and data["nested"]["value"] == 1
    )

    worker_changed = (
        len(worker_result["items"]) == 2
        and worker_result["items"][0] == 1
        and worker_result["items"][1] == 2
        and worker_result["nested"]["value"] == 2
    )

    report(
        "spawn-arg-nested",
        (
            parent_unchanged
            and worker_changed
        ),
        "deep-copied"
    )


def test_closure_isolation():
    parent_data = [5]

    worker = create_closure_worker(
        parent_data
    )

    drone = spawn_drone(
        worker
    )

    if drone == None:
        report(
            "closure-list",
            False,
            "spawn-failed"
        )
        return

    worker_result = wait_for(
        drone
    )

    passed = (
        len(parent_data) == 1
        and parent_data[0] == 5
        and len(worker_result) == 2
        and worker_result[0] == 5
        and worker_result[1] == 6
    )

    report(
        "closure-list",
        passed,
        "isolated"
    )


def test_return_value_communication():
    drone = spawn_drone(
        return_value_worker
    )

    if drone == None:
        report(
            "return-value",
            False,
            "spawn-failed"
        )
        return

    result = wait_for(
        drone
    )

    passed = (
        len(result["items"]) == 2
        and result["items"][0] == 1
        and result["items"][1] == 2
        and result["nested"]["value"] == 3
    )

    report(
        "return-value",
        passed,
        "worker-to-caller"
    )


def test_source_parent_repeat():
    global source_handle

    source_handle = spawn_drone(
        create_list_source
    )

    if source_handle == None:
        report(
            "source-parent-repeat",
            False,
            "spawn-failed"
        )
        return

    first = wait_for(
        source_handle
    )

    first.append(
        71
    )

    second = wait_for(
        source_handle
    )

    if len(second) == 0:
        report(
            "source-parent-repeat",
            True,
            "copy-per-wait"
        )
        return

    if (
        len(second) == 1
        and second[0] == 71
    ):
        report(
            "source-parent-repeat",
            True,
            "same-drone-alias"
        )
        return

    report(
        "source-parent-repeat",
        False,
        "unexpected"
    )


def test_source_worker_repeat():
    global source_handle

    source_handle = spawn_drone(
        create_list_source
    )

    if source_handle == None:
        report(
            "source-worker-repeat",
            False,
            "source-spawn-failed"
        )
        return

    wait_for(
        source_handle
    )

    drone = spawn_drone(
        source_repeat_worker
    )

    if drone == None:
        report(
            "source-worker-repeat",
            False,
            "worker-spawn-failed"
        )
        return

    result = wait_for(
        drone
    )

    report(
        "source-worker-repeat",
        (
            result == "copy-per-wait"
            or result == "same-drone-alias"
        ),
        result
    )


def test_source_parent_to_worker():
    global source_handle

    source_handle = spawn_drone(
        create_list_source
    )

    if source_handle == None:
        report(
            "source-parent-worker",
            False,
            "source-spawn-failed"
        )
        return

    parent_view = wait_for(
        source_handle
    )

    parent_view.append(
        99
    )

    drone = spawn_drone(
        source_append_worker,
        1
    )

    if drone == None:
        report(
            "source-parent-worker",
            False,
            "worker-spawn-failed"
        )
        return

    worker_result = wait_for(
        drone
    )

    passed = (
        len(worker_result) == 1
        and worker_result[0] == 1
    )

    report(
        "source-parent-worker",
        passed,
        "parent-mutation-not-visible"
    )


def test_source_worker_to_parent():
    global source_handle

    source_handle = spawn_drone(
        create_list_source
    )

    if source_handle == None:
        report(
            "source-worker-parent",
            False,
            "source-spawn-failed"
        )
        return

    wait_for(
        source_handle
    )

    drone = spawn_drone(
        source_append_worker,
        1
    )

    if drone == None:
        report(
            "source-worker-parent",
            False,
            "worker-spawn-failed"
        )
        return

    worker_result = wait_for(
        drone
    )

    parent_result = wait_for(
        source_handle
    )

    passed = (
        len(worker_result) == 1
        and worker_result[0] == 1
        and len(parent_result) == 0
    )

    report(
        "source-worker-parent",
        passed,
        "worker-mutation-not-visible"
    )


def test_source_worker_to_worker():
    global source_handle

    source_handle = spawn_drone(
        create_list_source
    )

    if source_handle == None:
        report(
            "source-worker-worker",
            False,
            "source-spawn-failed"
        )
        return

    initial = wait_for(
        source_handle
    )

    first_drone = spawn_drone(
        source_append_worker,
        1
    )

    if first_drone == None:
        report(
            "source-worker-worker",
            False,
            "first-worker-spawn-failed"
        )
        return

    first_result = wait_for(
        first_drone
    )

    second_drone = spawn_drone(
        source_append_worker,
        2
    )

    if second_drone == None:
        report(
            "source-worker-worker",
            False,
            "second-worker-spawn-failed"
        )
        return

    second_result = wait_for(
        second_drone
    )

    final = wait_for(
        source_handle
    )

    passed = (
        len(initial) == 0
        and len(first_result) == 1
        and first_result[0] == 1
        and len(second_result) == 1
        and second_result[0] == 2
        and len(final) == 0
    )

    report(
        "source-worker-worker",
        passed,
        "historical-exploit-isolated"
    )


def test_source_nested_worker_to_worker():
    global source_handle

    source_handle = spawn_drone(
        create_nested_source
    )

    if source_handle == None:
        report(
            "source-nested",
            False,
            "source-spawn-failed"
        )
        return

    wait_for(
        source_handle
    )

    first_drone = spawn_drone(
        source_nested_worker,
        1
    )

    if first_drone == None:
        report(
            "source-nested",
            False,
            "first-worker-spawn-failed"
        )
        return

    first_result = wait_for(
        first_drone
    )

    second_drone = spawn_drone(
        source_nested_worker,
        2
    )

    if second_drone == None:
        report(
            "source-nested",
            False,
            "second-worker-spawn-failed"
        )
        return

    second_result = wait_for(
        second_drone
    )

    final = wait_for(
        source_handle
    )

    first_ok = (
        len(first_result["items"]) == 1
        and first_result["items"][0] == 1
        and first_result["nested"]["value"] == 1
    )

    second_ok = (
        len(second_result["items"]) == 1
        and second_result["items"][0] == 2
        and second_result["nested"]["value"] == 2
    )

    final_ok = (
        len(final["items"]) == 0
        and final["nested"]["value"] == 0
    )

    report(
        "source-nested",
        (
            first_ok
            and second_ok
            and final_ok
        ),
        "deep-isolation"
    )


def test_historical_queue():
    global source_handle

    source_handle = spawn_drone(
        create_queue_source
    )

    if source_handle == None:
        report(
            "source-queue",
            False,
            "source-spawn-failed"
        )
        return

    wait_for(
        source_handle
    )

    first_drone = spawn_drone(
        source_queue_worker,
        1
    )

    if first_drone == None:
        report(
            "source-queue",
            False,
            "first-worker-spawn-failed"
        )
        return

    first_result = wait_for(
        first_drone
    )

    second_drone = spawn_drone(
        source_queue_worker,
        2
    )

    if second_drone == None:
        report(
            "source-queue",
            False,
            "second-worker-spawn-failed"
        )
        return

    second_result = wait_for(
        second_drone
    )

    final = wait_for(
        source_handle
    )

    workers_isolated = (
        first_result[1] == 1
        and first_result[2] == 3
        and second_result[1] == 1
        and second_result[2] == 3
    )

    source_unchanged = (
        len(final["tasks"]) == 4
        and final["tasks"][0] == 1
        and len(final["results"]) == 0
    )

    report(
        "source-queue",
        (
            workers_isolated
            and source_unchanged
        ),
        "historical-producer-consumer-isolated"
    )


def main():
    quick_print(
        "DRONE_MEMORY SUITE START"
    )

    test_global_isolation()
    test_spawn_argument_list()
    test_spawn_argument_nested()
    test_closure_isolation()
    test_return_value_communication()

    test_source_parent_repeat()
    test_source_worker_repeat()

    test_source_parent_to_worker()
    test_source_worker_to_parent()
    test_source_worker_to_worker()
    test_source_nested_worker_to_worker()
    test_historical_queue()

    quick_print(
        "DRONE_MEMORY SUMMARY",
        tests_passed,
        tests_total
    )

    if tests_passed == tests_total:
        quick_print(
            "DRONE_MEMORY RESULT",
            "PASS"
        )
    else:
        quick_print(
            "DRONE_MEMORY RESULT",
            "FAIL"
        )


if __name__ == "__main__":
    main()
