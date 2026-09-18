# ==================================================
# NORMALE FARM
# ==================================================

# Mit 3.2 Wasser/s können wir aggressiv bewässern.
# Unter 0.75 wird jeweils ein Tank (+0.25) verwendet.
WATER_LIMIT = 0.75

# Sonnenblumen bleiben als permanentes L am linken und oberen Rand.
#
# Bei 16x16 und Breite 1:
#   linke Spalte + obere Reihe = 31 Sonnenblumen.
#
# Durch Wrap-around ist die obere Reihe von y=0 aus nur
# einen Schritt South entfernt.
SUNFLOWER_EDGE_WIDTH = 1

# Direkt neben dem Sonnenblumen-L liegt ein Karotten-L,
# damit dauerhaft Nachschub für neue Sonnenblumen vorhanden ist.
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
# Mazes absichtlich nicht automatisch upgraden:
# höhere Maze-Level erhöhen auch die benötigte
# Weird_Substance-Menge.
# ==================================================

AUTO_UNLOCKS = [
    Unlocks.Speed,
    Unlocks.Expand,
    Unlocks.Watering,
    Unlocks.Grass,
    Unlocks.Cactus,
    Unlocks.Plant,
    Unlocks.Carrots,
    Unlocks.Trees,
    Unlocks.Pumpkins,
    Unlocks.Polyculture,
    Unlocks.Dinosaurs,
    Unlocks.Megafarm
]
