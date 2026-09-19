# Upstream source reference

Repository:

https://github.com/msmith93/thefarmerwasreplaced

Reviewed branch:

`full_reset`

Pinned revision:

`28544222a2b1531c915b0646f8eb74971f4cc615`

Reviewed paths:

- `full_reset/README.md`
- `full_reset/full_reset.py`
- `full_reset/full_reset_solution.py`
- `full_reset/leaderboard.py`
- `full_reset/simulate.py`

The source body is not mirrored here because no redistribution license was found during review.

Notable upstream behavior:

- `full_reset_solution.py` contains an explicit repeated `unlock_order`
- the sequence is designed for `Leaderboards.Fastest_Reset`
- it ends after buying `Unlocks.Leaderboard`
- `leaderboard.py` runs `Leaderboards.Fastest_Reset` against that solution
