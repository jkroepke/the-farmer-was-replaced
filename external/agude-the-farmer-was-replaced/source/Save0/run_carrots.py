from carrots import farm_carrot_cycle


while True:
    if not farm_carrot_cycle():
        quick_print("Carrot cycle failed")
        break
