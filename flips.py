# Use all 32 drone slots to farm the flip achievement.
#
# The initial drone already counts towards max_drones(), so on a fully
# unlocked 32-drone farm this spawns 31 additional drones.

TARGET_DRONES = 32

def flip_forever():
    while True:
        do_a_flip()

while num_drones() < TARGET_DRONES and num_drones() < max_drones():
    spawn_drone(flip_forever)

quick_print("FLIP FARM", num_drones(), "drones")

# The initial drone is the final worker.
flip_forever()
