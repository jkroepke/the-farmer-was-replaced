from trees import farm_tree_cycle


while True:
    if not farm_tree_cycle():
        quick_print("Tree cycle failed")
        break
