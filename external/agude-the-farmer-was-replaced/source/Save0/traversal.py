from navigation import distance_to


def get_snake_positions(start_x: int, start_y: int, width: int, height: int):
    # Return a continuous west-to-east snake through a rectangular region.
    positions = []

    if width <= 0 or height <= 0:
        return positions

    for x in range(start_x, start_x + width):
        column = x - start_x

        if column % 2 == 0:
            for y in range(start_y, start_y + height):
                positions.append((x, y))
        else:
            for y in range(start_y + height - 1, start_y - 1, -1):
                positions.append((x, y))

    return positions


def should_scan_forward(positions, distance_function=None) -> bool:
    # Choose the endpoint with the shorter wrapped route from the drone.
    if len(positions) == 0:
        return True

    if distance_function == None:
        distance_function = distance_to

    first_x, first_y = positions[0]
    last_x, last_y = positions[len(positions) - 1]

    return distance_function(first_x, first_y) <= distance_function(last_x, last_y)
