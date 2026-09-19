# Achievement helpers.
#
# Change MODE to select the achievement helper to run.

MODE = "stack-overflow"
TARGET_DRONES = 32


def cause_stack_overflow():
    cause_stack_overflow()


def flip_forever():
    while True:
        do_a_flip()


def master_acrobat():
    while num_drones() < TARGET_DRONES and num_drones() < max_drones():
        spawn_drone(flip_forever)

    quick_print("FLIP FARM", num_drones(), "drones")
    flip_forever()


if MODE == "stack-overflow":
    cause_stack_overflow()
elif MODE == "master-acrobat":
    master_acrobat()
else:
    quick_print("Unknown achievement mode:", MODE)
