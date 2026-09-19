# Achievements

## Flip achievements

- The current game API exposes `do_a_flip()`; it takes 1 second and is not affected by speed upgrades.
- Steam lists `Master Acrobat` as requiring 1000 flips.
- The initial drone counts towards `num_drones()` / `max_drones()`. Therefore 32 active drones means spawning 31 additional workers when `max_drones() == 32`.
- `flips.py` fills the available drone slots up to 32 and makes every active drone call `do_a_flip()` forever. Stop the program after the achievement appears.
- No built-in API for querying Steam achievement completion was found, so the script cannot stop exactly when the achievement unlocks.
- [Unverified] I could not verify from official/current documentation whether flip achievement progress is aggregated across all spawned drones. The script deliberately uses all drones so this can be tested in-game.

Sources:
- Repository `builtins.py` for `do_a_flip()`, `spawn_drone()`, `num_drones()`, and `max_drones()`.
- Steam achievement page observed on 2026-09-19: `Master Acrobat — Do 1000 flips.`
