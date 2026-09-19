from farm_config import (
    BONE_TARGET,
    DINOSAUR_CACTUS_RESERVE,
    ENABLE_DINOSAUR_FARM,
)


def get_apple_cactus_cost() -> int:
    # Return zero when the Apple cost is unavailable or malformed.
    cost = get_cost(Entities.Apple)

    if cost == None:
        return 0

    for item in cost:
        if item == Items.Cactus:
            cactus_cost = cost[item]

            if cactus_cost > 0:
                return cactus_cost

    return 0


def get_full_run_cactus_cost(world_size: int, apple_cost: int) -> int:
    # Budget one apple for every tile in the field.
    return world_size * world_size * apple_cost


def can_fund_dinosaur_run(run_cost: int) -> bool:
    # Keep the configured cactus reserve untouched.
    return num_items(Items.Cactus) >= (run_cost + DINOSAUR_CACTUS_RESERVE)


def move_steps(direction, count: int) -> bool:
    # Let the failed move provide the termination signal.
    for _i in range(count):
        if not move(direction):
            return False

    return True


def traverse_dinosaur_cycle(world_size: int) -> bool:
    # Stream the fixed Hamiltonian cycle until the tail blocks movement.
    while True:
        if not move_steps(North, world_size - 1):
            return False

        for column in range(1, world_size):
            if not move_steps(East, 1):
                return False

            if column % 2:
                if not move_steps(South, world_size - 2):
                    return False

            else:
                if not move_steps(North, world_size - 2):
                    return False

        if not move_steps(South, 1):
            return False

        if not move_steps(West, world_size - 1):
            return False


def grow_full_dinosaur_tail(world_size: int) -> None:
    # Follow the cycle until the completed tail blocks the next move.
    traverse_dinosaur_cycle(world_size)


def run_dinosaur_once(world_size: int) -> bool:
    # Clear only after farm_dinosaurs has completed all safety checks.
    clear()
    change_hat(Hats.Dinosaur_Hat)

    if get_entity_type() != Entities.Apple:
        change_hat(Hats.Straw_Hat)
        return False

    grow_full_dinosaur_tail(world_size)
    change_hat(Hats.Straw_Hat)
    return True


def farm_dinosaurs() -> None:
    # Run isolated full-field dinosaur cycles until the bone target is met.
    if not ENABLE_DINOSAUR_FARM:
        return

    if num_items(Items.Bone) >= BONE_TARGET:
        return

    if num_unlocked(Unlocks.Dinosaurs) == 0:
        return

    apple_cost = get_apple_cactus_cost()

    if apple_cost <= 0:
        return

    world_size = get_world_size()

    if world_size < 2 or world_size % 2:
        return

    run_cost = get_full_run_cactus_cost(world_size, apple_cost)

    if not can_fund_dinosaur_run(run_cost):
        return

    while num_items(Items.Bone) < BONE_TARGET:
        if not can_fund_dinosaur_run(run_cost):
            return

        if not run_dinosaur_once(world_size):
            return
