# The Farmer Was Replaced Scripts

This repository tracks automation scripts from The Farmer Was Replaced. The
game runs a restricted Python-like language rather than CPython.

## Static checks

Install the managed Python interpreter and run all checks:

```sh
just sync
just check
```

Install the optional pre-commit hook with `just hooks-install`.

The checks run a constrained Ruff ruleset, check formatting for all Python
files, reject syntax unsupported by the game interpreter, verify that game
imports resolve within their save, and validate repository Agent Skills. Lint
autofixes remain limited to the CPython tools under `scripts/`. Static checks
do not replace testing in the game debugger or simulator. Ruff ignores `E711`
for game scripts because the game requires `== None` and `!= None`; the game
code checker rejects identity comparisons with `None`.

GitHub Actions runs the same `just lint` recipe. This repository has no
continuous-deployment step because the active local game save cannot be chosen
or updated safely by hosted CI.

## Game API metadata

The game-generated `Save0/__builtins__.py` is an ignored editor stub and is not
run as Python. `game-api.json` records its public functions, positional call
limits, enum members, and injected globals so hosted CI can validate scripts
without access to the local save metadata.

After a game update regenerates the stub, refresh the committed metadata and
Ruff globals, then run all checks:

```sh
just api-sync
just check
```

Do not edit the manifest or the marked Ruff globals block by hand.
