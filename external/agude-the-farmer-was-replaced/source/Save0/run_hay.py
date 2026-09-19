from hay import farm_hay_cycle


while True:
    if not farm_hay_cycle():
        quick_print("Hay cycle failed")
        break
