from pumpkins import farm_pumpkin_cycle


while True:
    if not farm_pumpkin_cycle():
        quick_print("Pumpkin cycle failed")
        break
