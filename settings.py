import pygame

# Mystic Siege - Game Constants
# All values defined here, never hardcode anywhere else

# SCREEN
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
FPS_CAP_MIN = 30
FPS_CAP_COARSE_STEP = 5
FPS_CAP_FINE_STEP = 1
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
WIZARD_CRIT_CHANCE_BONUS = 0.10
WIZARD_SPELL_DAMAGE_BONUS = 0.20  # Wizard passive: spells deal 20% more damage
RANGER_CRIT_CHANCE_BONUS = 0.10
RANGER_PROJECTILE_PIERCE_BONUS = 1

# XP
BASE_XP_REQUIRED = 50
XP_SCALE_FACTOR = 1.12
FRIAR_HEAL_PER_XP = 0.1  # HP healed per XP point collected

# WEAPONS
MAX_WEAPON_SLOTS = 6

# Arcane Bolt
ARCANE_BOLT_BASE_DAMAGE = 20.0
ARCANE_BOLT_BASE_COOLDOWN = 1.0
ARCANE_BOLT_BASE_BOLT_COUNT = 1
ARCANE_BOLT_BASE_PIERCE = 0
ARCANE_BOLT_TARGETING_RANGE = 350
ARCANE_BOLT_SPREAD = 20
ARCANE_BOLT_STAGGER = 0.25
ARCANE_BOLT_PROJECTILE_SPEED = 400
ARCANE_BOLT_PROJECTILE_COLOR = (160, 80, 255)
ARCANE_BOLT_UPGRADE_LEVELS = [
    {},
    {"base_damage": 10},
    {"bolt_count": 1},
    {"pierce": 1},
    {"bolt_count": 1, "base_damage": 15},
]

# Holy Nova
HOLY_NOVA_BASE_DAMAGE = 20.0
HOLY_NOVA_BASE_COOLDOWN = 2.0
HOLY_NOVA_BASE_RADIUS = 80
HOLY_NOVA_EXPAND_SPEED = 200
HOLY_NOVA_RING_WIDTH = 8
HOLY_NOVA_RING_COLOR = (255, 230, 100)
HOLY_NOVA_HIT_SPARK_COLOR = (255, 230, 100)
HOLY_NOVA_UPGRADE_LEVELS = [
    {},
    {"base_damage": 15},
    {"base_radius": 40},
    {"base_cooldown": -0.4},
    {"base_damage": 20, "ring_width": -4},
]
HOLY_NOVA_INNER_GLOW_COLOR       = (255, 245, 180)  # soft white-gold flash at cast origin
HOLY_NOVA_OUTER_BLOOM_COLOR      = (255, 215,  80)  # faint gold ring just outside primary ring
HOLY_NOVA_FLARE_COLOR            = (255, 255, 220)  # bright near-white for cardinal flare spikes
HOLY_NOVA_SPARK_COLOR            = (255, 240, 140)  # warm gold for radiant sparks
HOLY_NOVA_SPARK_COUNT            = 16               # spark particles spawned per ring cast
HOLY_NOVA_FLARE_COUNT            = 8                # flare spike points on ring edge
HOLY_NOVA_FLARE_LENGTH           = 14               # pixel length of each flare spike
HOLY_NOVA_PARTICLE_SPEED_VARIANCE = 40              # ±px/s variance on particle radial speed

# Spectral Blade
SPECTRAL_BLADE_BASE_DAMAGE = 18.0
SPECTRAL_BLADE_BASE_COOLDOWN = 0.0
SPECTRAL_BLADE_BASE_BLADE_COUNT = 2
SPECTRAL_BLADE_ORBIT_RADIUS = 20      # hilt offset: distance from player center to sword base
SPECTRAL_BLADE_ORBIT_SPEED = 180
SPECTRAL_BLADE_BLADE_LENGTH = 78      # sword length from hilt to tip
SPECTRAL_BLADE_BLADE_WIDTH = 5        # great sword blade width
SPECTRAL_BLADE_BLADE_COLOR = (100, 150, 255)
SPECTRAL_BLADE_OUTLINE_COLOR = (60, 90, 180)
SPECTRAL_BLADE_GRIP_LENGTH = 16       # two-handed grip length
SPECTRAL_BLADE_GRIP_WIDTH = 5         # two-handed grip thickness
SPECTRAL_BLADE_GUARD_HALF_WIDTH = 17  # long straight crossguard for great sword
SPECTRAL_BLADE_GUARD_THICKNESS = 4    # crossguard depth along blade axis
SPECTRAL_BLADE_TAPER_START = 0.72    # fraction of blade length where taper begins (rest is parallel body)
SPECTRAL_BLADE_GRIP_COLOR = (50, 70, 130)         # dark grip/handle color
SPECTRAL_BLADE_HIGHLIGHT_COLOR = (190, 215, 255)  # blade center highlight strip
SPECTRAL_BLADE_GUARD_COLOR = (160, 190, 255)      # crossguard outline + pommel fill accent
SPECTRAL_BLADE_POMMEL_RADIUS = 5                  # wheel pommel radius in pixels
SPECTRAL_BLADE_GLOW_COLOR = (140, 175, 255)       # outer glow triangle, lighter than blade
SPECTRAL_BLADE_GLOW_EXTRA_WIDTH = 3               # extra pixels added each side of blade for glow
SPECTRAL_BLADE_HIT_SPARK_COLOR = (100, 150, 255)
SPECTRAL_BLADE_HIT_COOLDOWN = 0.3
SPECTRAL_BLADE_UPGRADE_LEVELS = [
    {},
    {"blade_count": 1},
    {"orbit_speed": 60},
    {"orbit_radius": 20},
    {"blade_count": 1, "base_damage": 12},
]

# Flame Blast
FLAME_BLAST_BASE_DAMAGE = 25.0
FLAME_BLAST_BASE_COOLDOWN = 1.5
FLAME_BLAST_CONE_RANGE = 150
FLAME_BLAST_CONE_ANGLE = 90
FLAME_BLAST_BURN_DAMAGE = 5.0
FLAME_BLAST_BURN_DURATION = 2.0
FLAME_BLAST_EFFECT_COLOR = (255, 100, 0)
FLAME_BLAST_HIT_SPARK_COLOR = (255, 100, 0)
FLAME_BLAST_INNER_COLOR = (255, 180, 20)        # mid-range particle color (orange-yellow)
FLAME_BLAST_CORE_COLOR = (255, 240, 130)         # near-origin particle color (hot yellow)
FLAME_BLAST_PARTICLE_COUNT = 45                  # particles spawned per cast
FLAME_BLAST_PARTICLE_LIFETIME = 0.55             # max particle lifetime in seconds
FLAME_BLAST_PARTICLE_SPEED_MIN = 80              # slowest particle initial speed (px/s)
FLAME_BLAST_PARTICLE_SPEED_MAX = 430             # fastest particle initial speed (px/s)
FLAME_BLAST_PARTICLE_RADIUS_MAX = 6              # max particle circle radius (px)
FLAME_BLAST_UPGRADE_LEVELS = [
    {},
    {"base_damage": 15},
    {"cone_range": 40},
    {"burn_duration": 1.5},
    {"cone_angle": 30, "base_damage": 20},
]

# Frost Ring
FROST_RING_BASE_DAMAGE = 15.0
FROST_RING_BASE_COOLDOWN = 3.0
FROST_RING_SPEED = 80
FROST_RING_MAX_RADIUS = 200
FROST_RING_FREEZE_DURATION = 1.0
FROST_RING_HALF_WIDTH = 5
FROST_RING_DRAW_WIDTH = 3
FROST_RING_COLOR = (0, 200, 255)
FROST_RING_HIT_SPARK_COLOR = (0, 200, 255)
FROST_RING_UPGRADE_LEVELS = [
    {},
    {"freeze_duration": 0.5},
    {"base_damage": 10},
    {"ring_speed": 30},
    {"base_cooldown": -0.8, "max_radius": 80},
]

# Lightning Chain
LIGHTNING_CHAIN_BASE_DAMAGE = 30.0
LIGHTNING_CHAIN_BASE_COOLDOWN = 2.0
LIGHTNING_CHAIN_TARGETING_RANGE = 400
LIGHTNING_CHAIN_BASE_CHAIN_COUNT = 3
LIGHTNING_CHAIN_CHAIN_RANGE = 150
LIGHTNING_CHAIN_BASE_STUN_CHANCE = 0.0
LIGHTNING_CHAIN_STUN_DURATION = 0.5
LIGHTNING_CHAIN_HOP_DAMAGE_MULTIPLIER = 0.8
LIGHTNING_CHAIN_ARC_LIFETIME = 0.12
LIGHTNING_CHAIN_ARC_MIN_SEGMENTS = 3
LIGHTNING_CHAIN_ARC_MAX_SEGMENTS = 5
LIGHTNING_CHAIN_ARC_JITTER = 15
LIGHTNING_CHAIN_ARC_COLOR = (255, 255, 200)
LIGHTNING_CHAIN_ARC_WIDTH = 2
LIGHTNING_CHAIN_HIT_SPARK_COLOR = (255, 255, 100)
LIGHTNING_CHAIN_UPGRADE_LEVELS = [
    {},
    {"base_damage": 15},
    {"chain_count": 2},
    {"chain_range": 50},
    {"chain_count": 1, "stun_chance": 0.25},
]

# Longbow
LONGBOW_BASE_DAMAGE = 24.0
LONGBOW_BASE_COOLDOWN = 1.0
LONGBOW_TARGETING_RANGE = 520
LONGBOW_PROJECTILE_SPEED = 720
LONGBOW_PROJECTILE_LIFETIME = 0.9
LONGBOW_BASE_PIERCE = 0
LONGBOW_BASE_PROJECTILE_COUNT = 1
LONGBOW_SPREAD = 5
LONGBOW_BASE_CRIT_BONUS = 0.05
LONGBOW_PROJECTILE_COLOR = (170, 120, 60)
LONGBOW_PROJECTILE_SIZE = (20, 5)
LONGBOW_UPGRADE_LEVELS = [
    {},
    {"base_damage": 8.0},
    {"base_cooldown": -0.15},
    {"pierce": 1},
    {"projectile_count": 2, "crit_bonus": 0.10},
]

# ENEMIES
# Shared enemy runtime tunables
ENEMY_BASE_ATTACK_COOLDOWN = 1.0
ENEMY_MIN_SEPARATION = 30       # pixels — enemies push apart if closer than this
ENEMY_KNOCKBACK_FORCE = 180     # pixels/second — impulse applied to enemies on weapon hit
ENEMY_RETARGET_INTERVAL = 0.25  # seconds between nearest-player retarget scans
ENEMY_SPAWN_OFFSCREEN_MARGIN = 150
ENEMY_SPAWN_POSITION_ATTEMPTS = 8
ENEMY_WARNING_DURATION = 3.0
ENEMY_ELITE_HP_MULTIPLIER = 1.5
ENEMY_ELITE_DAMAGE_MULTIPLIER = 1.5

# Enemy archetype data
SKELETON_ENEMY_DATA = {
    "name": "Skeleton",
    "hp": 30,
    "speed": 80,
    "damage": 10,
    "xp_value": 3,
    "behavior": "chase",
    "wander_angle_max": 5.0,
    "wander_angle_change_interval": 0.5,
}

DARK_GOBLIN_ENEMY_DATA = {
    "name": "Goblin",
    "hp": 20,
    "speed": 160,
    "damage": 8,
    "xp_value": 3,
    "behavior": "chase",
}

WRAITH_ENEMY_DATA = {
    "name": "Wraith",
    "hp": 40,
    "speed": 120,
    "damage": 15,
    "xp_value": 5,
    "behavior": "chase",
    "lunge_cooldown": 3.0,
    "lunge_duration": 0.4,
    "lunge_speed_multiplier": 3.0,
}

PLAGUE_BAT_ENEMY_DATA = {
    "name": "Bat",
    "hp": 15,
    "speed": 220,
    "damage": 8,
    "xp_value": 3,
    "behavior": "chase",
    "split_chance": 0.4,
    "split_count": 2,
    "wave_frequency": 4.0,
    "wave_amplitude": 0.5,
    "sprite_scale": (20, 20),
}

MINI_BAT_ENEMY_DATA = {
    "name": "Mini Bat",
    "hp": 7,
    "speed": 280,
    "damage": 4,
    "xp_value": 1,
    "behavior": "chase",
    "split_chance": 0.0,
    "split_count": 0,
    "wave_frequency": PLAGUE_BAT_ENEMY_DATA["wave_frequency"],
    "wave_amplitude": PLAGUE_BAT_ENEMY_DATA["wave_amplitude"],
    "sprite_scale": (14, 14),
}

CURSED_KNIGHT_ENEMY_DATA = {
    "name": "Knight",
    "hp": 80,
    "speed": 110,
    "damage": 20,
    "xp_value": 10,
    "behavior": "chase",
    "shield_block_angle": 60.0,
    "shield_damage_multiplier": 0.2,
}

LICH_FAMILIAR_ENEMY_DATA = {
    "name": "Lich",
    "hp": 35,
    "speed": 90,
    "damage": 12,
    "xp_value": 10,
    "behavior": "orbit",
    "orbit_radius": 200,
    "orbit_angular_speed": 45.0,
    "fire_interval": 2.5,
    "projectile_speed": 120,
    "projectile_damage": 12,
    "projectile_lifetime": 4.0,
    "projectile_color": (187, 0, 0),
    "fire_range": 450,
}

STONE_GOLEM_ENEMY_DATA = {
    "name": "Golem",
    "hp": 500,
    "speed": 40,
    "damage": 40,
    "xp_value": 80,
    "behavior": "chase",
}

ENEMY_DATA_BY_ID = {
    "Skeleton": SKELETON_ENEMY_DATA,
    "Goblin": DARK_GOBLIN_ENEMY_DATA,
    "Wraith": WRAITH_ENEMY_DATA,
    "Bat": PLAGUE_BAT_ENEMY_DATA,
    "MiniBat": MINI_BAT_ENEMY_DATA,
    "Knight": CURSED_KNIGHT_ENEMY_DATA,
    "Lich": LICH_FAMILIAR_ENEMY_DATA,
    "Golem": STONE_GOLEM_ENEMY_DATA,
}

# Wave / spawn tunables
WAVE_INITIAL_ACTIVE_POOL = ["Skeleton"]
WAVE_INITIAL_SPAWN_RATE = 5.0
WAVE_INITIAL_BOSS_ACTIVE_POOL = []
WAVE_INITIAL_BOSS_SPAWN_RATE = 120.0
WAVE_SKELETON_PACK_MIN = 2
WAVE_SKELETON_PACK_MAX = 4
WAVE_GOBLIN_UNLOCK_TIME = 60
WAVE_GOBLIN_SPAWN_RATE = 4.0
WAVE_GOBLIN_PACK_MIN = 3
WAVE_GOBLIN_PACK_MAX = 5
WAVE_WRAITH_UNLOCK_TIME = 120
WAVE_WRAITH_SPAWN_RATE = 3.5
WAVE_WRAITH_PACK_MIN = 1
WAVE_WRAITH_PACK_MAX = 3
WAVE_BAT_UNLOCK_TIME = 180
WAVE_BAT_SPAWN_RATE = 3.0
WAVE_BAT_PACK_MIN = 3
WAVE_BAT_PACK_MAX = 6
WAVE_BAT_WARNING_TEXT = "BATS INCOMING!"
WAVE_GOLEM_EVENT_TIME = 300
WAVE_GOLEM_PACK_MIN = 1
WAVE_GOLEM_PACK_MAX = 3
WAVE_GOLEM_WARNING_TEXT = "GOLEM APPROACHES!"
WAVE_KNIGHT_LICH_UNLOCK_TIME = 240
WAVE_KNIGHT_LICH_SPAWN_RATE = 2.5
WAVE_LICH_PACK_MIN = 1
WAVE_LICH_PACK_MAX = 3
WAVE_KNIGHT_PACK_MIN = 1
WAVE_KNIGHT_PACK_MAX = 2
WAVE_ELITE_MODE_TIME = 600
WAVE_ELITE_SPAWN_RATE = 2.0
WAVE_ELITE_WARNING_TEXT = "ELITE ENEMIES ARISE!"
WAVE_FINAL_ASSAULT_TIME = 1200
WAVE_FINAL_ASSAULT_SPAWN_RATE = 1.0
WAVE_FINAL_ASSAULT_WARNING_TEXT = "FINAL ASSAULT!"
WAVE_VICTORY_TIME = 1800

# UI
HUD_FONT_SIZE = 24
SMALL_FONT_SIZE = 16
TITLE_FONT_SIZE = 72
CLASS_SELECT_TITLE_Y = 28
CLASS_SELECT_PROMPT_MARGIN_TOP = 12
HUD_EMPTY_SLOT_BG_COLOR = (40, 40, 40)
WEAPON_SLOT_LEVEL_BORDER_SEGMENTS = 4
WEAPON_SLOT_LEVEL_BORDER_WIDTH = 2
WEAPON_SLOT_LEVEL_BORDER_GAP = 4
WEAPON_SLOT_LEVEL_BORDER_FILLED_COLOR = (255, 215, 0)
WEAPON_SLOT_LEVEL_BORDER_EMPTY_COLOR = (80, 80, 80)
HUD_PANEL_PADDING = 10
HUD_PANEL_BAR_HEIGHT = 12
HUD_PANEL_WEAPON_SLOT_SIZE = 40
HUD_PANEL_WEAPON_SLOT_WIDTH = 40
HUD_PANEL_WEAPON_SLOT_GAP = 4
HUD_PANEL_CORNER_RADIUS = 6
HUD_REVIVE_RING_RADIUS = 28
HUD_REVIVE_RING_WIDTH = 4
SETTINGS_SLIDER_STEP_COARSE = 0.05
SETTINGS_SLIDER_STEP_FINE = 0.02
SETTINGS_ANALOG_ADJUST_REPEAT_DELAY = 0.2
SETTINGS_ANALOG_ADJUST_REPEAT_RATE = 0.08
SETTINGS_SLIDER_VALUE_X_OFFSET = 24
SETTINGS_BUTTON_WIDTH = 240
SETTINGS_BUTTON_HEIGHT = 50
SETTINGS_BUTTON_START_Y = 390
SETTINGS_BUTTON_ROW_GAP = 65
SETTINGS_BUTTON_COLUMN_GAP = 40
HUD_PANEL_TOP_LEFT = (20, 20, 320, 148)
HUD_PANEL_TUPLES = {
    1: {
        0: HUD_PANEL_TOP_LEFT,
    },
    2: {
        0: HUD_PANEL_TOP_LEFT,
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
CONTROLLER_START_BUTTONS = (7,)      # Default pause/start button; extend per-controller only if needed
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
CONTROLLER_HELP_LABELS = {
    "confirm": "Confirm",
    "back": "Back",
    "start": "Start",
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
PAUSE_CONFIRM_DIALOG_WIDTH = 420
PAUSE_CONFIRM_DIALOG_HEIGHT = 180
PAUSE_CONFIRM_DIALOG_BG_COLOR = (20, 15, 10)
PAUSE_CONFIRM_BUTTON_WIDTH = 150
PAUSE_CONFIRM_BUTTON_HEIGHT = 44
PAUSE_CONFIRM_MESSAGE_FONT_SIZE = 20
PAUSE_CONFIRM_BUTTON_Y_OFFSET = 112
PAUSE_CONFIRM_BUTTON_INSET = 36
PAUSE_CONFIRM_MESSAGE_Y_OFFSET = 34

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

# HERO_CLASSES list of hero dicts, each with keys:
# name, hp, speed, armor, passive_desc, starting_weapon, color (RGB for placeholder sprite),
# sprite, and passives (declarative gameplay modifiers used by Player/XP/collision systems)
HERO_CLASSES = [
    {
        "name": "Knight",
        "hp": 150,
        "speed": 180,
        "armor": 15,
        "passive_desc": "Takes 15% less damage. Immune to knockback.",
        "starting_weapon": "SpectralBlade",
        "color": (180, 140, 60),
        "sprite": "assets/sprites/heroes/knight.png",
        "passives": {
            "damage_taken_multiplier": 0.85,
            "knockback_immune": True,
        },
    },
    {
        "name": "Wizard",
        "hp": 80,
        "speed": 240,
        "armor": 0,
        "passive_desc": "Spells deal 20% more damage. +10% crit chance.",
        "starting_weapon": "ArcaneBolt",
        "color": (160, 60, 220),
        "sprite": "assets/sprites/heroes/wizard.png",
        "passives": {
            "crit_chance_bonus": WIZARD_CRIT_CHANCE_BONUS,
            "spell_damage_bonus_pct": WIZARD_SPELL_DAMAGE_BONUS,
        },
    },
    {
        "name": "Friar",
        "hp": 110,
        "speed": 210,
        "armor": 5,
        "passive_desc": "Heals 1 HP per 10 XP gained.",
        "starting_weapon": "HolyNova",
        "color": (200, 180, 120),
        "sprite": "assets/sprites/heroes/friar.png",
        "passives": {
            "heal_per_xp": FRIAR_HEAL_PER_XP,
        },
    },
    {
        "name": "Ranger",
        "hp": 95,
        "speed": 225,
        "armor": 3,
        "passive_desc": "Gain +10% crit chance. Arrows pierce 1 extra enemy.",
        "starting_weapon": "Longbow",
        "color": (90, 170, 110),
        "sprite": "assets/sprites/heroes/ranger.png",
        "passives": {
            "crit_chance_bonus": RANGER_CRIT_CHANCE_BONUS,
            "projectile_pierce_bonus": RANGER_PROJECTILE_PIERCE_BONUS,
        },
    }
]
