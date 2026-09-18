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


# ==================================================
# SPEZIALJOBS
# ==================================================

MAZE_EVERY = 2

PUMPKIN_EVERY = 5

CACTUS_EVERY = 7

# Dinosaur läuft etwas seltener als Cactus.
# So kann vorher wieder Cactus als Apple-Währung produziert werden.
DINOSAUR_EVERY = 8

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
    Unlocks.Watering
]
