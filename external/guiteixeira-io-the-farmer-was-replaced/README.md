# guiteixeira-io/the-farmer-was-replaced

## Upstream

- URL: https://github.com/guiteixeira-io/the-farmer-was-replaced
- Type: GitHub repository
- Mirrored: 2026-09-19
- Default branch: `main`
- Revision: `58bd5c5ba928548bc21035006551ca93854f16b9`
- Revision date: 2026-04-16
- Snapshot files: 12
- Snapshot size: 5207 bytes
- License metadata: no repository license is declared upstream
- Snapshot status: complete pinned repository mirrored unchanged under `source/`
- Snapshot verification: local `source/` tree SHA equals upstream tree SHA `df54494d954e4fbd472c9839186b55467605683f`

## Summary

This repository is primarily an educational/classroom repository rather than a performance-oriented TFWR reference.

The upstream README is written for student groups and explains:

- how to clone the repository
- how to create a per-student `.py` file
- basic Git usage
- a minimal overview of TFWR commands

The save folders correspond to class times:

- `Saves/8h/`
- `Saves/10h/`
- `Saves/12h/`
- `Saves/14h/`

Most checked-in game files are empty placeholders.

## Non-empty game scripts

### `Saves/12h/main.py`

The script:

1. equips `Hats.Purple_Hat`
2. performs one `do_a_flip()`
3. loops forever
4. harvests when possible
5. otherwise performs `do_a_flip()`

This is a minimal beginner loop.

### `Saves/14h/main.py`

The script:

1. equips `Hats.Purple_Hat`
2. performs one `do_a_flip()`
3. loops forever
4. harvests only when `can_harvest()`

The difference from the 12h variant is simply that it does not flip while waiting for maturity.

## Optimization relevance

There is no meaningful advanced material in the pinned revision for:

- Megafarm
- persistent workers
- Cactus sorting
- Maze
- Dinosaur
- Pumpkin
- Sunflower pathing
- Polyculture
- Fastest Reset
- tick-cost measurement

The repository should therefore not be searched before the stronger references when looking for optimization ideas.

Its value is mainly:

- provenance
- beginner-code examples
- a low-complexity harvest-loop baseline
- evidence that the repository is intended as a teaching exercise rather than an optimized solution set

## Current-game caveat

The README's command table includes `Entities.Wheat` and localized direction names in prose/examples. Treat that material as classroom documentation, not authoritative current API documentation.

Always use this project's current `builtins.py` and current game Tooltips for API names.

## Snapshot contents

The complete pinned source tree is mirrored under `source/`.

Revision:

`58bd5c5ba928548bc21035006551ca93854f16b9`

Tree:

`df54494d954e4fbd472c9839186b55467605683f`
