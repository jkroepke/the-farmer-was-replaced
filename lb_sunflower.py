import sunflower_lb


# Measured winner from sunflower-v2-bounded7.
#
# Mode 9 averaged 371.54 s across seeds 1/2/3. It keeps only compact
# per-column petal counts, uses binary-tree worker fan-out, enforces a barrier
# between petal tiers, and leaves exactly nine Sunflowers before the next
# replant phase.
MODE = 9
TARGET_POWER = 100000


if not sunflower_lb.run(
    MODE,
    TARGET_POWER
):
    quick_print(
        "SUNFLOWER LEADERBOARD FAILED"
    )
