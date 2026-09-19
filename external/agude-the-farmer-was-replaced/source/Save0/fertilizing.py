from farm_config import (
    ENABLE_WEIRD_SUBSTANCE_PRODUCTION,
    FERTILIZER_RESERVE,
    WEIRD_SUBSTANCE_TARGET,
)


def should_produce_weird_substance(
    weird_substance_target=None,
    fertilizer_reserve=None,
    production_enabled=None,
) -> bool:
    if production_enabled == None:
        production_enabled = ENABLE_WEIRD_SUBSTANCE_PRODUCTION

    if not production_enabled:
        return False

    if weird_substance_target == None:
        weird_substance_target = WEIRD_SUBSTANCE_TARGET

    if fertilizer_reserve == None:
        fertilizer_reserve = FERTILIZER_RESERVE

    if num_items(Items.Weird_Substance) >= weird_substance_target:
        return False

    return num_items(Items.Fertilizer) > fertilizer_reserve


def fertilize_before_harvest(
    weird_substance_target=None,
    fertilizer_reserve=None,
    production_enabled=None,
) -> bool:
    if not should_produce_weird_substance(
        weird_substance_target,
        fertilizer_reserve,
        production_enabled,
    ):
        return False

    return use_item(Items.Fertilizer)
