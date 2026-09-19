# j4.lc TFWR source snapshot

## Upstream

- URL: https://g.j4.lc/general-stuff/the-farmer-was-replaced
- Type: website / source collection
- Snapshot supplied by: repository user
- Archived: 2026-09-19
- Upstream revision: not exposed by the source URL
- Supplied archive SHA-256: `6918c9718f9ef2b1d1ef38918e521a33103adb2ea7b16afea46718d44f7da0d0`
- License/redistribution status: snapshot was directly supplied by the user
- Snapshot status: complete contents of the supplied archive are mirrored unchanged under `source/`

## Snapshot contents

- `FarmingChecks.py`
- `FarmingUtils.py`
- `Helpers.py`
- `Main.py`
- `README.md`
- `ZeroToHero.py`
- `cactus.py`
- `maze.py`
- `replant.py`

## Summary

This snapshot is centered around a `Leaderboards.Fastest_Reset` / `ZeroToHero` run.

Notable areas:

- upgrade selection based on approximate total resource cost
- generic resource dispatch for Wood, Carrot, Pumpkin, Power, Cactus, Bone, Gold and Weird Substance
- a Dinosaur/Bone route embedded in `ZeroToHero.py`
- Cactus neighbor-swap sorting
- Maze wall-following plus an alternative explicit search implementation
- Pumpkin patch/replant tracking
- wrap-aware coordinate movement helpers

The upstream README explicitly states that the scripts are **not claimed to be optimal** and that some scripts were taken from other places. Treat this as a useful implementation/reference snapshot, not as an authoritative or proven fastest implementation.

Files under `source/` are preserved unchanged from the user-supplied archive. Local analysis belongs in this README.
