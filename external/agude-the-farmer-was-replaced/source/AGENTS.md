# Repository Instructions

## Runtime

Treat files under `Save*/` as The Farmer Was Replaced programs, not ordinary
Python. Follow `.agents/skills/farmer-was-replaced-python/SKILL.md` when reading
or changing them. Treat each save directory independently and do not edit
generated save-state files unless explicitly requested.

## Validation

Run `just check` before committing. It is the complete local equivalent of CI.

Ruff formats all Python files and applies defect-oriented lint rules. Do not
run lint autofixes on `Save*/`, and do not enable `SIM`, `RUF`, `UP`, or `C4`:
those rules can recommend syntax that the game interpreter does not support.
The `format` recipe applies lint autofixes only to the CPython tooling under
`scripts/`. The game-generated `Save0/__builtins__.py` remains ignored and
untouched. After the game regenerates it, run `just api-sync` to update
`game-api.json` and the marked Ruff globals block; do not edit either generated
section by hand. Ruff ignores `E711` for game scripts because the game
requires `== None` and `!= None`; `scripts/check_game_code.py` rejects `is
None` and `is not None` in `Save*/`.

This repository is a script collection, not a Python package. CI runs static
linting and repository-specific validation, but no type checker, runtime test
suite, coverage, build, release, or deployment jobs. Game behavior must be
validated in the game debugger or simulator. Python 3.12.3 is pinned only to
run repository tooling; the game uses its own interpreter.
