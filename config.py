# ==================================================
# NORMALE FARM
# ==================================================

# Mit 3.2 Wasser/s können wir aggressiv bewässern.
# Unter 0.75 wird jeweils ein Tank (+0.25) verwendet.
WATER_LIMIT = 0.75

# Legacy-L benchmark configuration.
# Production uses adaptive Sunflower columns; these widths remain only
# for farm.run_legacy() and historical benchmark reproduction.
SUNFLOWER_EDGE_WIDTH = 1
CARROT_SUPPORT_EDGE_WIDTH = 1

ENABLE_POLYCULTURE = True


# ==================================================
# DÜNGER / WEIRD SUBSTANCE
# ==================================================

ENABLE_FERTILIZER = True

# Bei 0.8 Dünger/s müssen wir kaum noch horten.
FERTILIZER_RESERVE = 10

# So viele Maze-Kosten als Weird_Substance bevorraten.
# Etwas mehr Weird_Substance puffern, weil Dünger
# jetzt standardmäßig aktiv genutzt wird.
MAZE_STOCKPILE = 5

# Adaptive parallel small-Maze production.
#
# At 32x32 / 32 drones, the benchmarked winner is 32 independent
# 4x4 Mazes using the zapakh-style ranked iterative DFS.
#
# Minimum relocations per worker before parallel Gold production may start.
# If more Weird Substance is already available, production automatically
# increases the relocation count up to MAZE_REUSE_LIMIT.
MAZE_PARALLEL_RELOCATIONS = 25
MAZE_PARALLEL_MIN_WORKERS = 2

# Reference tree-rebalancing Maze strategy.
#
# Source:
# https://pastebin.com/KzGvn6nc
#
# Benchmark results showed this strategy clearly ahead of fresh mazes,
# BFS, and our simpler tree variants.
MAZE_REUSE_LIMIT = 300
MAZE_GREEDY_AFTER = 30
MAZE_REROOT_AT = 40
MAZE_REBALANCE_FROM = 40
MAZE_REBALANCE_ACTIVE_UNTIL = 80
MAZE_REBALANCE_UNTIL = 140


# ==================================================
# RESSOURCEN-PLANUNG
# ==================================================
#
# Reihenfolge und Prioritäten basieren auf:
# https://github.com/Thorrdu/the-farmer-was-replaced/blob/main/parameters.py
#
# Die statischen "target"-Werte aus dem fremden Repository
# verwenden wir NICHT. Unser Ziel kommt dynamisch aus get_cost()
# des aktuell ausgewählten Upgrades.
# ==================================================

RESOURCE_PLANS = [
    {
        "item": Items.Power,
        "plant": Entities.Sunflower,
        "priority": 7
    },
    {
        "item": Items.Hay,
        "plant": Entities.Grass,
        "priority": 5
    },
    {
        "item": Items.Wood,
        "plant": Entities.Tree,
        "priority": 5
    },
    {
        "item": Items.Carrot,
        "plant": Entities.Carrot,
        "priority": 5
    },
    {
        "item": Items.Pumpkin,
        "plant": Entities.Pumpkin,
        "priority": 4
    },
    {
        "item": Items.Cactus,
        "plant": Entities.Cactus,
        "priority": 4
    },
    {
        "item": Items.Bone,
        "plant": None,
        "priority": 3
    },
    {
        "item": Items.Gold,
        "plant": None,
        "priority": 3
    },
    {
        "item": Items.Weird_Substance,
        "plant": None,
        "priority": 3
    }
]


# Reserve für tote Kürbisse.
PUMPKIN_COST_FACTOR = 2

# Billiger Corner-ID-Check.
PUMPKIN_ID_CHECK_INTERVAL = 0.25

# Nach der initialen Vollbepflanzung erst etwas wachsen lassen,
# bevor Problempositionen gesammelt werden.
PUMPKIN_INITIAL_WAIT = 1.0

# Bekannte Problempositionen werden deutlich häufiger geprüft,
# ohne die komplette 16x16-Farm erneut zu scannen.
PUMPKIN_PATCH_INTERVAL = 0.25


# ==================================================
# AUTOMATISCHE UNLOCKS
# ==================================================
#
# Dependency-aware progression order + relative priority.
#
# The order is still a frontier: next_target() considers all already
# reached entries plus the first never-unlocked entry, but never jumps
# beyond it.
#
# Within that candidate set, priority weights the remaining resource
# cost. A higher priority can therefore beat a somewhat cheaper lower
# priority target without forcing one line to be maxed before progress.
#
# Endgame goals intentionally use lower priority, but remain mandatory:
# Leaderboard -> Top_Hat -> The_Farmers_Remains.
#
# References:
# - msmith93/thefarmerwasreplaced full_reset solution
# - nql1314 staged unlock recommendations
# - current wiki unlock/cost data
# ==================================================

UNLOCK_PLANS = [
    {
        "unlock": Unlocks.Speed,
        "priority": 10
    },
    {
        "unlock": Unlocks.Expand,
        "priority": 10
    },
    {
        "unlock": Unlocks.Plant,
        "priority": 10
    },
    {
        "unlock": Unlocks.Carrots,
        "priority": 9
    },
    {
        "unlock": Unlocks.Watering,
        "priority": 8
    },
    {
        "unlock": Unlocks.Trees,
        "priority": 8
    },
    {
        "unlock": Unlocks.Grass,
        "priority": 8
    },
    {
        "unlock": Unlocks.Sunflowers,
        "priority": 9
    },
    {
        "unlock": Unlocks.Fertilizer,
        "priority": 8
    },
    {
        "unlock": Unlocks.Pumpkins,
        "priority": 8
    },
    {
        "unlock": Unlocks.Polyculture,
        "priority": 7
    },
    {
        "unlock": Unlocks.Cactus,
        "priority": 7
    },
    {
        "unlock": Unlocks.Mazes,
        "priority": 6
    },
    {
        "unlock": Unlocks.Megafarm,
        "priority": 9
    },
    {
        "unlock": Unlocks.Dinosaurs,
        "priority": 7
    },
    {
        "unlock": Unlocks.Hats,
        "priority": 3
    },
    {
        "unlock": Unlocks.Leaderboard,
        "priority": 3
    },
    {
        "unlock": Unlocks.Top_Hat,
        "priority": 1
    },
    {
        "unlock": Unlocks.The_Farmers_Remains,
        "priority": 1
    }
]
