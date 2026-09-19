def dispatch_indexed_jobs(job_values, task):
    # Reserve one job for the parent drone so every dispatch has a fallback.
    results = []
    workers = []

    for _ in range(len(job_values)):
        results.append(None)

    if len(job_values) == 0:
        return results

    for index in range(len(job_values) - 1):
        job_value = job_values[index]
        worker = spawn_drone(task, job_value)

        if worker == None:
            # A failed spawn still completes its assigned job immediately.
            results[index] = task(job_value)
        else:
            workers.append((index, worker))

    parent_index = len(job_values) - 1
    results[parent_index] = task(job_values[parent_index])

    # Do not let dependent phases begin until every worker has completed.
    for index, worker in workers:
        results[index] = wait_for(worker)

    return results
