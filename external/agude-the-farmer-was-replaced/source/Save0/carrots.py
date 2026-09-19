from navigation import move_to
from parallel_farming import dispatch_indexed_jobs
from regular_farming import tend_regular_tile


def tend_carrot_row(row_y: int) -> bool:
    # Tend every carrot tile in one finite row.
    size = get_world_size()
    move_to(0, row_y)

    for x in range(size):
        move_to(x, row_y)

        if not tend_regular_tile(Entities.Carrot):
            return False

    return True


def farm_carrot_cycle() -> bool:
    # Run one finite carrot pass over every world row.
    size = get_world_size()
    rows = []

    for row_y in range(size):
        rows.append(row_y)

    results = dispatch_indexed_jobs(rows, tend_carrot_row)

    for result in results:
        if not result:
            return False

    return True
