from farm_config import POWER_TARGET
from sunflowers import farm_sunflower_cycle


while num_items(Items.Power) < POWER_TARGET:
    if not farm_sunflower_cycle():
        quick_print("Sunflower cycle failed")
        break
