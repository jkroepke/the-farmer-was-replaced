---
name: farmer-was-replaced-python
description: Maintains Python-like scripts for The Farmer Was Replaced, including navigation, planting, watering, pumpkins, drones, simulation, and editor sync. Use when reading, debugging, optimizing, or editing code in a The Farmer Was Replaced save directory; do not use for ordinary Python projects.
---

# The Farmer Was Replaced Python

Treat `.py` files in a game save as programs for The Farmer Was Replaced, not
CPython. Python parsing and editor types can catch mistakes but cannot prove
that code works in the game's custom interpreter.

## Workflow

1. Resolve the target save from the requested path or files. Treat separate
   `Save*` directories as independent; compare before copying between them. If
   a game-side test depends on the active slot and the target is ambiguous,
   have the user confirm it.
2. Read the target modules and only the relevant definitions or docstrings in
   that save's generated `__builtins__.py`. Never commit `__builtins__.py`.
3. Preserve the existing module and import structure unless the task requires
   a change. Keep import-time movement and farming out of helper modules.
4. Make the smallest coherent change. Do not edit `save.json` unless the user
   explicitly requests save-state work. Back up the complete save before
   save-state edits or destructive game-side experiments; tracked code edits
   rely on Git for recovery.
5. Validate statically, then state what still requires an in-game check.

The game generates `__builtins__.py` as an approximate editor stub for its
current API. It is local input, not repository source: keep it ignored and do
not format, lint, or edit it. In this repository, `game-api.json` is the
committed, portable API manifest used by CI. After the game regenerates the
stub, run `just api-sync`, review changes to the manifest and the generated
Ruff globals block, then run `just check`.

For disputed or version-sensitive behavior, use this source order:

1. The installed game's in-game documentation.
2. The target save's `__builtins__.py` for the installed API surface.
3. [Official Steam announcements](https://steamcommunity.com/app/2060160/announcements/).
4. The maintained [community wiki](https://thefarmerwasreplaced.wiki.gg/).
5. Community code as a pattern, never as a compatibility guarantee.

Research only when the task crosses a version boundary or the local sources
do not answer it.

## Interpreter constraints

- Do not introduce classes, lambdas, comprehensions, ternary expressions,
  `async`/`await`, named arguments, standard-library imports, or unsupported
  collection methods. Confirm any less common language feature locally.
- Type annotations are accepted by current builds and useful to external
  editors, but they do not expand the game language or validate runtime
  behavior.
- Use names from the target save's stubs. Current names include
  `Entities.Carrot`, `Grounds.Grassland`, `Items.Water`, `get_tick_count()`, and
  `set_world_size()`; older examples often use superseded names.
- `spawn_drone(function, *args)` is supported by current builds. Do not copy
  older closure workarounds without checking the installed signature.
- Compare missing values with `== None` or `!= None`, not `is None` or
  `is not None`; this is required by the game interpreter.
- Use `quick_print()` for diagnostics. `print()` adds visible and timing
  overhead.

## Game-specific invariants

- Coordinates start at `(0, 0)` in the southwest. X increases with `East`, Y
  increases with `North`, and ordinary farm movement wraps. Derive dimensions
  from `get_world_size()`.
- `till()` toggles grassland and soil. Check `get_ground_type()` before using it
  as an ensure-soil operation.
- Planting and watering affect the current tile. Check the ground and account
  for occupied tiles, unlocks, and inventory when `plant()` failure matters.
- Water evaporates. Apply threshold-based watering while visiting a tile.
- Normal harvesting must be guarded by `can_harvest()`; unready crops are
  destroyed. Unguarded `harvest()` is only for intentional clearing or a
  separately proven postcondition.
- A giant pumpkin requires every tile in its square to mature. Replant empty
  or `Entities.Dead_Pumpkin` tiles and do not harvest individual mature
  pumpkins while waiting for the merge. Treat `measure()` heuristics as
  implementation details, not documented pumpkin state.

## Performance

Game operations have tick costs. Optimize from measurements or a specific hot
path: reduce movement, redundant scans, repeated sensor calls, and busy waits.
Do not add cached state unless its invalidation is clear. Use
`get_tick_count()` for local comparisons and `simulate()` when its unlock,
inventory, globals, seed, and speed inputs are known.

## Validation

1. Inspect the diff and run `just check`. It verifies formatting, compatible
   syntax, local imports, installed API call arity and enum members, the API
   manifest, Ruff globals, and repository skills. Treat CPython results as
   supplementary.
2. For behavior, use the game debugger, `quick_print()`, slower execution, or
   a reduced test world. `set_world_size()` clears the farm and resets the
   drone, so use it only in an intentional test.
3. After external-editor edits, confirm File Watcher/reload behavior and that
   the game is executing the intended file in the intended save.
4. Report static checks separately from unperformed game-side checks.
