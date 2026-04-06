import pygame

# Mystic Siege - Game Constants
# All values defined here, never hardcode anywhere else

# SCREEN
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Mystic Siege"

# AUDIO INIT
AUDIO_FREQUENCY       = 44100   # Hz — Windows/macOS (DirectSound/CoreAudio resample cleanly)
AUDIO_FREQUENCY_LINUX = 48000   # Hz — matches PipeWire/PulseAudio native rate; eliminates resampling artifacts
AUDIO_SIZE            = -16     # 16-bit signed samples
AUDIO_CHANNELS        = 2       # stereo
AUDIO_BUFFER          = 512     # samples per chunk — Windows/macOS sweet spot
AUDIO_BUFFER_LINUX    = 1024    # 48kHz + no resampling = stable at half old buffer (~21ms latency)
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
HP_MED_COLOR = (255, 255, 0)
HP_LOW_COLOR = (220, 60, 60)
THREAT_ARROW_COLOR = (255, 60, 60)

# Threat arrow safe zones — keep arrows clear of edge UI elements.
# Update these when new HUD elements are added to screen edges.
HUD_SAFE_TOP    = 45   # clears HP bar (y=20, h=20) + gap
HUD_SAFE_BOTTOM = 20   # clears XP bar (h=20)
HUD_SAFE_LEFT   = 0
HUD_SAFE_RIGHT  = 0

# PLAYER BASE STATS
BASE_HP = 100
BASE_SPEED = 200
PICKUP_RADIUS = 80

# CRITICAL HITS
CRIT_CHANCE_BASE = 0.05   # 5% base crit chance for all heroes
CRIT_MULTIPLIER = 2.0     # crits deal 2x damage
WIZARD_SPELL_DAMAGE_BONUS = 0.20  # Wizard passive: spells deal 20% more damage

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

ENEMY_MIN_SEPARATION = 30       # pixels — enemies push apart if closer than this
ENEMY_KNOCKBACK_FORCE = 180     # pixels/second — impulse applied to enemies on weapon hit
ENEMY_RETARGET_INTERVAL = 0.25  # seconds between nearest-player retarget scans
LICH_FIRE_RANGE = 450           # pixels — lich only fires when within this distance of the player

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
HUD_PANEL_PADDING = 10
HUD_PANEL_BAR_HEIGHT = 12
HUD_PANEL_WEAPON_SLOT_SIZE = 40
HUD_PANEL_WEAPON_SLOT_WIDTH = 40
HUD_PANEL_WEAPON_SLOT_GAP = 4
HUD_REVIVE_RING_RADIUS = 28
HUD_REVIVE_RING_WIDTH = 4
SETTINGS_SLIDER_STEP_COARSE = 0.05
SETTINGS_SLIDER_STEP_FINE = 0.02
SETTINGS_ANALOG_ADJUST_REPEAT_DELAY = 0.2
SETTINGS_ANALOG_ADJUST_REPEAT_RATE = 0.08
HUD_PANEL_TUPLES = {
    1: {
        0: (20, 20, 360, 120),
    },
    2: {
        0: (20, 20, 320, 148),
        1: (940, 20, 320, 148),
    },
    3: {
        0: (20, 20, 280, 148),
        1: (980, 20, 280, 148),
        2: (20, 552, 280, 148),
    },
    4: {
        0: (20, 20, 280, 148),
        1: (980, 20, 280, 148),
        2: (20, 552, 280, 148),
        3: (980, 552, 280, 148),
    },
}

# CONTROLLER
CONTROLLER_DEADZONE = 0.2
CONTROLLER_AXIS_REPEAT_DELAY = 0.4   # seconds before held axis starts repeating
CONTROLLER_AXIS_REPEAT_RATE = 0.15   # seconds between repeats while axis is held
CONTROLLER_CONFIRM_BUTTON = 0        # A / Cross
CONTROLLER_BACK_BUTTON = 1           # B / Circle
CONTROLLER_START_BUTTONS = (7,)      # Start / Options; extend per-controller only if needed
CONTROLLER_BINDINGS_DEFAULT = {
    "confirm": CONTROLLER_CONFIRM_BUTTON,
    "back": CONTROLLER_BACK_BUTTON,
    "start": list(CONTROLLER_START_BUTTONS),
}
CONTROLLER_BINDINGS_SETTINGS_DEFAULT = {
    "global_bindings": dict(CONTROLLER_BINDINGS_DEFAULT),
    "profiles": {},
}
CONTROLLER_BINDING_LABELS = {
    "confirm": "Confirm",
    "back": "Back",
    "start": "Pause / Start",
}

# KEYBOARD INPUT SCHEMES
KEYBOARD_WASD_BINDINGS = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
    "confirm": pygame.K_SPACE,
    "back": pygame.K_LSHIFT,
}
KEYBOARD_ARROW_BINDINGS = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "confirm": pygame.K_RETURN,
    "back": pygame.K_RSHIFT,
}

# MOUSE CURSOR — hide after this many seconds of no movement
MOUSE_HIDE_DELAY = 2.0

# PAUSE MENU BUTTONS
PAUSE_BUTTON_WIDTH = 240
PAUSE_BUTTON_HEIGHT = 50
PAUSE_BUTTON_SPACING = 18
PAUSE_BUTTON_COLOR = (30, 20, 10)
PAUSE_BUTTON_HOVER_COLOR = (40, 30, 20)
PAUSE_BUTTON_TEXT_COLOR = (255, 255, 255)

# MULTIPLAYER
MAX_PLAYERS = 4
# Per-slot color badges — index matches PlayerSlot.index (0–3)
PLAYER_COLORS = [
    (100, 180, 255),   # slot 0 — blue
    (255, 140,  40),   # slot 1 — orange
    ( 80, 220, 120),   # slot 2 — green
    (255, 220,  60),   # slot 3 — yellow
]
SPAWN_OFFSETS = [
    (-80,   0),  # slot 0
    ( 80,   0),  # slot 1
    (  0,  80),  # slot 2
    (  0, -80),  # slot 3
]
CAMERA_ZOOM_MIN = 0.45
CAMERA_ZOOM_LERP = 2.0
CAMERA_PLAYER_MARGIN = 200
REVIVE_RADIUS = 96
REVIVE_DURATION = 2.0
REVIVE_HEALTH_FRACTION = 0.5
REVIVE_IFRAME_DURATION = 2.0
DOWNED_ALPHA = 100

# GAME STATES (string constants)
STATE_MENU = "menu"
STATE_CLASS_SELECT = "class_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"
STATE_VICTORY = "victory"
STATE_SETTINGS = "settings"
STATE_STATS = "stats"
STATE_LOBBY = "lobby"

# HERO_CLASSES list of 3 dicts, each with keys:
# name, hp, speed, armor, passive_desc, starting_weapon, color (RGB for placeholder sprite)
HERO_CLASSES = [
    {
        "name": "Knight",
        "hp": 150,
        "speed": 180,
        "armor": 15,
        "passive_desc": "Takes 15% less damage. Immune to knockback.",
        "starting_weapon": "SpectralBlade",
        "color": (180, 140, 60),
        "sprite": "assets/sprites/heroes/knight.png"
    },
    {
        "name": "Wizard",
        "hp": 80,
        "speed": 240,
        "armor": 0,
        "passive_desc": "Spells deal 20% more damage. +10% crit chance.",
        "starting_weapon": "ArcaneBolt",
        "color": (160, 60, 220),
        "sprite": "assets/sprites/heroes/wizard.png"
    },
    {
        "name": "Friar",
        "hp": 110,
        "speed": 210,
        "armor": 5,
        "passive_desc": "Heals 1 HP per 10 XP gained.",
        "starting_weapon": "HolyNova",
        "color": (200, 180, 120),
        "sprite": "assets/sprites/heroes/friar.png"
    }
]
