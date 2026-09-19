# Achievements

## Helper script

- Achievement helpers live in `archivments.py`.
- Select the helper with the `MODE` constant.
- Keep achievement entry points in this shared file instead of creating one user-facing script per achievement.
- `Circular Import` needs two tiny helper modules because an actual import cycle requires modules to import each other.

## Stack Overflow

- Steam lists `Stack Overflow` with the requirement: `Cause a stack overflow.`
- `MODE = "stack-overflow"` calls `cause_stack_overflow()` recursively without a base case, intentionally exhausting the call stack.
- The resulting runtime failure is intentional for this achievement.

## Master Acrobat

- The current game API exposes `do_a_flip()`; it takes 1 second and is not affected by speed upgrades.
- Steam lists `Master Acrobat` as requiring 1000 flips.
- The initial drone counts towards `num_drones()` / `max_drones()`. Therefore 32 active drones means spawning 31 additional workers when `max_drones() == 32`.
- `MODE = "master-acrobat"` fills the available drone slots up to 32 and makes every active drone call `do_a_flip()` forever. Stop the program after the achievement appears.
- No built-in API for querying Steam achievement completion was found.
- [Unverified] I could not verify from official/current documentation whether flip achievement progress is aggregated across all spawned drones.

## Wrong Order

- Steam lists `Wrong Order` as: `Sort a full field of cacti the wrong way round.`
- Current Cactus mechanics define normal order as non-decreasing toward North and East, and non-increasing toward South and West.
- The helper requires a 32x32 field, clears it, plants all 1024 tiles with Cacti, waits for maturity, then sorts every row and every column in descending order.
- Rows are processed in parallel by 32 drones, followed by columns in parallel by 32 drones.
- Historical developer/community reports from October 2025 say the achievement originally triggered only on harvest. A community report identified coordinate `(0, 31)` as a reliable harvest trigger, so the helper harvests there after reverse sorting.
- Later community reports say the achievement began triggering immediately after the reverse sort. Keeping the final harvest is harmless for the one-shot achievement helper.

## Healer

- Steam lists `Healer` as: `Cure an infected plant.`
- Current Fertilizer mechanics: using Fertilizer on a plant infects it.
- Current Weird Substance mechanics: using Weird Substance on a non-Bush plant toggles infection state for that plant and its adjacent plants.
- `MODE = "healer"` plants a Carrot, infects it with Fertilizer, then cures it with Weird Substance.
- If no Fertilizer is available, the helper falls back to using Weird Substance twice on the same Carrot: first infect, then cure.

## Circular Import

- Steam lists `Circular Import` as: `Create an import cycle.`
- `MODE = "circular-import"` imports `archivments_cycle_a`.
- `archivments_cycle_a.py` imports `archivments_cycle_b.py`, and `archivments_cycle_b.py` imports `archivments_cycle_a.py`.
- The two helper files intentionally contain no other behavior.

## Sources

- Repository `builtins.py` for game API behavior.
- Current wiki Cactus page: https://thefarmerwasreplaced.wiki.gg/wiki/Cactus
- Current wiki Fertilizer page: https://thefarmerwasreplaced.wiki.gg/wiki/Fertilizer
- Current wiki Import page: https://thefarmerwasreplaced.wiki.gg/wiki/Import
- Steam global achievements: https://steamcommunity.com/stats/2060160/achievements
- Steam discussion `Wrong Order achievement not registering` for the historical harvest-trigger behavior and `(0, 31)` report.
