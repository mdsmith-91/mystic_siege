# Mystic Siege — Game Constants
# All values defined here, never hardcode anywhere else

# SCREEN
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Mystic Siege"
TILE_SIZE = 32
WORLD_WIDTH = 3000
WORLD_HEIGHT = 3000

# COLORS (as RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (212, 175, 55)
DARK_PURPLE = (45, 0, 75)
UI_BG = (20, 15, 30, 180)  # RGBA for semi-transparent panels
XP_COLOR = (80, 220, 255)
HP_COLOR = (60, 200, 80)
HP_LOW_COLOR = (220, 60, 60)

# PLAYER BASE STATS
BASE_HP = 100
BASE_SPEED = 200
PICKUP_RADIUS = 80

# XP
BASE_XP_REQUIRED = 50
XP_SCALE_FACTOR = 1.12
FRIAR_HEAL_PER_XP = 0.1  # HP healed per XP point collected

# WEAPONS
MAX_WEAPON_SLOTS = 6
ARCANE_BOLT_RANGE = 350         # max distance to target an enemy
ARCANE_BOLT_SPREAD = 20         # degrees between each bolt in a multi-bolt burst
ARCANE_BOLT_STAGGER = 0.3       # seconds between each bolt in a burst
LIGHTNING_CHAIN_RANGE = 400  # max distance to initial target for lightning chain

# SPAWNING
INITIAL_SPAWN_RATE = 3.0
MIN_SPAWN_RATE = 0.3

# UI
HUD_FONT_SIZE = 24
SMALL_FONT_SIZE = 16
TITLE_FONT_SIZE = 72
WEAPON_SLOT_PIP_COUNT = 5
WEAPON_SLOT_PIP_RADIUS = 3
WEAPON_SLOT_PIP_SPACING = 7
WEAPON_SLOT_PIP_Y_OFFSET = 6
WEAPON_SLOT_PIP_FILLED_COLOR = (255, 215, 0)
WEAPON_SLOT_PIP_EMPTY_COLOR = (80, 80, 80)

# CONTROLLER
CONTROLLER_DEADZONE = 0.2
CONTROLLER_AXIS_REPEAT_DELAY = 0.4   # seconds before held axis starts repeating
CONTROLLER_AXIS_REPEAT_RATE = 0.15   # seconds between repeats while axis is held

# PAUSE MENU BUTTONS
PAUSE_BUTTON_WIDTH = 240
PAUSE_BUTTON_HEIGHT = 50
PAUSE_BUTTON_SPACING = 18
PAUSE_BUTTON_COLOR = (30, 20, 10)
PAUSE_BUTTON_HOVER_COLOR = (40, 30, 20)
PAUSE_BUTTON_TEXT_COLOR = (255, 255, 255)

# GAME STATES (string constants)
STATE_MENU = "menu"
STATE_CLASS_SELECT = "class_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"
STATE_VICTORY = "victory"
STATE_SETTINGS = "settings"
STATE_STATS = "stats"

# HERO_CLASSES list of 3 dicts, each with keys:
# name, hp, speed, armor, passive_desc, starting_weapon, color (RGB for placeholder sprite)
HERO_CLASSES = [
    {
        "name": "Knight of the Burning Crown",
        "hp": 150,
        "speed": 180,
        "armor": 15,
        "passive_desc": "Takes 15% less damage. Immune to knockback.",
        "starting_weapon": "SpectralBlade",
        "color": (180, 140, 60)
    },
    {
        "name": "Witch of the Hollow Marsh",
        "hp": 80,
        "speed": 240,
        "armor": 0,
        "passive_desc": "Spells deal 20% more damage. +10% crit chance.",
        "starting_weapon": "ArcaneBolt",
        "color": (160, 60, 220)
    },
    {
        "name": "Wandering Friar",
        "hp": 110,
        "speed": 210,
        "armor": 5,
        "passive_desc": "Heals 1 HP per 10 XP gained.",
        "starting_weapon": "HolyNova",
        "color": (200, 180, 120)
    }
]