# msmith93/thefarmerwasreplaced — full_reset

## Upstream

- URL: https://github.com/msmith93/thefarmerwasreplaced/tree/full_reset/full_reset
- Type: GitHub repository branch/subdirectory
- Reviewed: 2026-09-19
- Branch: `full_reset`
- Upstream revision: `28544222a2b1531c915b0646f8eb74971f4cc615`
- License/redistribution status: no repository license was found during review

## Summary

This reference contains a pluggable Fastest Reset implementation.

The key orchestration idea is an explicit static `unlock_order` list. Each unlock step:

1. calls `get_cost(unlock)`
2. farms the required resources through crop-specific target functions
3. calls `unlock(unlock)`
4. continues to the next explicitly selected unlock/upgrade level

The worked `full_reset_solution.py` interleaves repeated levels of:

- Speed
- Expand
- Watering
- Fertilizer
- Carrots
- Trees
- Pumpkins
- Cactus
- Mazes
- Megafarm
- Dinosaurs
- Polyculture

and ends with `Unlocks.Leaderboard`.

This is useful evidence that Fastest Reset optimization benefits from an explicit unlock strategy instead of blindly iterating every `Unlocks` value.

## Relevance to this repository

Our normal persistent-game planner does not copy the exact reset sequence.

Instead, the useful pattern is adapted as:

- explicit dependency-aware unlock frontier
- static relative priority per unlock line
- dynamic live `get_cost()`
- dynamic resource choice based on current inventory
- lower-priority endgame goals that remain mandatory

Current-game unlocks added after or absent from the upstream reference, including `Unlocks.Top_Hat` and `Unlocks.The_Farmers_Remains`, must be sourced from current game documentation rather than inferred from this older reset plan.

## Redistribution

A full source mirror is intentionally absent because no redistribution license was found during review.

See `source/UPSTREAM.md` for the pinned upstream files used during analysis.
