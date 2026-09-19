from cactus import farm_cactus_patch


while True:
    if not farm_cactus_patch():
        quick_print("Cactus cycle failed")
        break
