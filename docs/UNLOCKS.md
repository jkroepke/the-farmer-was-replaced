# Automatic Unlock Planner

This document is the canonical reference for automatic research progression.

Read it before changing:

- `config.UNLOCK_PLANS`
- `unlocks.next_target()`
- planner-related logic in `main.py`

## Why the planner uses an explicit plan

Iterating every value in `Unlocks` is not a useful progression strategy.

The enum includes:

- language/tooling unlocks
- crop/resource progression
- repeatable production upgrades
- leaderboard access
- hidden/late-game goals

Those nodes are not equally important to the running automation.

Community references also use explicit progression rather than enum order:

- `external/msmith93-full-reset/`
  - Fastest Reset reference
  - explicit repeated `unlock_order`
  - ends at `Unlocks.Leaderboard`
- `external/nql1314-the-farmer-was-replaced-ai-code/`
  - staged progression recommendations
  - explicitly treats Leaderboard as the Fastest Reset completion condition

Current game documentation:

- https://thefarmerwasreplaced.wiki.gg/wiki/Unlocks
- https://thefarmerwasreplaced.wiki.gg/wiki/Unlocks_Data
- https://thefarmerwasreplaced.wiki.gg/wiki/Tooltips_Code

## Frontier model

`config.UNLOCK_PLANS` is ordered.

`unlocks.next_target()` considers:

1. every plan entry that has already been unlocked at least once
2. the first plan entry that has never been unlocked
3. nothing after that first never-unlocked entry

This preserves dependency progression while still allowing cheap upgrades from already-open lines to compete.

## Priority model

Every plan entry has a relative numeric priority.

For each reachable candidate:

```text
effective score = remaining resource cost / priority
```

Lower score wins.

The implementation compares cross products instead of doing division:

```text
candidate_remaining * best_priority
<
best_remaining * candidate_priority
```

This means priority is a preference, not an absolute lock.

A high-priority production upgrade may beat a somewhat cheaper low-priority endgame unlock, but a sufficiently cheap reachable target can still win.

## Current plan

| Frontier order | Unlock | Priority | Role |
| ---: | --- | ---: | --- |
| 1 | `Unlocks.Speed` | 10 | execution speed |
| 2 | `Unlocks.Expand` | 10 | farm size |
| 3 | `Unlocks.Plant` | 10 | basic crop progression |
| 4 | `Unlocks.Carrots` | 9 | resource chain |
| 5 | `Unlocks.Watering` | 8 | growth acceleration |
| 6 | `Unlocks.Trees` | 8 | Wood throughput |
| 7 | `Unlocks.Grass` | 8 | Hay throughput |
| 8 | `Unlocks.Sunflowers` | 9 | Power |
| 9 | `Unlocks.Fertilizer` | 8 | growth + Weird Substance |
| 10 | `Unlocks.Pumpkins` | 8 | Pumpkin chain |
| 11 | `Unlocks.Polyculture` | 7 | yield multiplier |
| 12 | `Unlocks.Cactus` | 7 | Cactus chain |
| 13 | `Unlocks.Mazes` | 6 | Gold chain |
| 14 | `Unlocks.Megafarm` | 9 | drone parallelism |
| 15 | `Unlocks.Dinosaurs` | 7 | Bone chain |
| 16 | `Unlocks.Hats` | 3 | late utility/cosmetic prerequisite |
| 17 | `Unlocks.Leaderboard` | 3 | leaderboard access |
| 18 | `Unlocks.Top_Hat` | 1 | very large late-game resource gate |
| 19 | `Unlocks.The_Farmers_Remains` | 1 | hidden/final late-game goal |

The final three goals deliberately have lower priority but are still part of the frontier. Therefore the planner must not report completion while they remain reachable and unfinished.

## Current late-game costs

Do not hard-code these values into planner code. They are recorded only to explain why their priorities are low.

At the time of review, current wiki data reports:

```text
Leaderboard:
    Bone 2,000,000
    Gold 1,000,000

Top_Hat:
    Hay 1,000,000,000
    Wood 10,000,000,000
    Carrot 1,000,000,000
    Cactus 1,000,000,000
    Gold 100,000,000

The_Farmers_Remains:
    Bone 100,000,000
```

Always use live `get_cost()` in production.

## Maze bootstrap

The first Maze unlock itself requires Weird Substance.

Before `Unlocks.Mazes` is unlocked, normal `farm.weird_substance_target()` therefore uses the live Maze unlock cost as its target. Otherwise the automatic planner could request Weird Substance while fertilizer logic simultaneously decided that zero Weird Substance was needed.

After Mazes is unlocked, the normal reusable-maze stockpile calculation takes over.

## Planner output

`main.py` prints a plan change only when Goal or Focus changes:

```text
PLAN goal Unlocks.Leaderboard focus Items.Bone
PLAN goal Unlocks.Top_Hat focus Items.Gold
```

`PLAN goal None focus None` should now mean every configured target is maxed/unlocked or currently has no actionable live cost. It must not merely mean that an incomplete endgame target was omitted from configuration.

## Fastest Reset is separate future work

The normal infinite automation planner is not yet the Fastest Reset leaderboard implementation.

The msmith reference demonstrates a different optimization problem:

- start from zero
- buy a deliberately tuned exact sequence of unlock levels
- stop when Leaderboard is reached

That should be benchmarked separately later rather than making the normal long-running planner mimic a leaderboard reset route.
