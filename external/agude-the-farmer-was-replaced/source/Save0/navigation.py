def distance_to(target_x: int, target_y: int) -> int:
    # Return wraparound Manhattan distance to a target position.
    size = get_world_size()

    dx = target_x - get_pos_x()
    if dx < 0:
        dx = -dx

    dy = target_y - get_pos_y()
    if dy < 0:
        dy = -dy

    if size - dx < dx:
        dx = size - dx

    if size - dy < dy:
        dy = size - dy

    return dx + dy


def move_axis(
    target: int,
    current: int,
    size: int,
    positive_direction,
    negative_direction,
) -> None:
    # Move along one wrapped axis using the shorter direction.
    positive_steps = (target - current) % size

    if positive_steps <= size // 2:
        direction = positive_direction
        steps = positive_steps
    else:
        direction = negative_direction
        steps = size - positive_steps

    for _ in range(steps):
        move(direction)


def move_to(target_x: int, target_y: int) -> None:
    # Move to a target using the shortest wrapped path on each axis.
    size = get_world_size()

    move_axis(target_x, get_pos_x(), size, East, West)
    move_axis(target_y, get_pos_y(), size, North, South)
