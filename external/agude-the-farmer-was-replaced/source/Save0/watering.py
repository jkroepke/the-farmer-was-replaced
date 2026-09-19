def water_if_dry(water_threshold: float = 0.2) -> None:
    # Water the current tile when its moisture is below the threshold.
    if get_water() < water_threshold:
        use_item(Items.Water)
