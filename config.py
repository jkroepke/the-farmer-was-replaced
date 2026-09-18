# ==================================================
# NORMALE FARM
# ==================================================

# Mit 3.2 Wasser/s können wir aggressiv bewässern.
# Unter 0.75 wird jeweils ein Tank (+0.25) verwendet.
WATER_LIMIT = 0.75

# 6x6 Sonnenblumen zentral.
# Auf großen Farmen liefert das mehr Energie für mehrere Drohnen.
SUNFLOWER_SIZE = 6

# Karottenring direkt um die Sonnenblumen.
CARROT_RING_WIDTH = 1

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


# ==================================================
# SPEZIALJOBS
# ==================================================

MAZE_EVERY = 2

PUMPKIN_EVERY = 5

CACTUS_EVERY = 7

# Reserve für tote Kürbisse.
PUMPKIN_COST_FACTOR = 2


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
    Unlocks.Watering
]
