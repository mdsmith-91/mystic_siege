import pygame

# Mystic Siege tuning reference.
# Keep gameplay, UI, audio, visual, and multiplayer tunables here so runtime code
# can stay free of hardcoded values.
#
# Comment style:
# - major section headers mark where to tune a subsystem
# - short tuning notes call out important coupling or expected usage
# - inline comments focus on units, category, and the effect of raising/lowering


# ============================================================================
# Display And World
# ============================================================================
# Core presentation and world-scale values. These affect window size, timing, and
# map dimensions shared across gameplay, UI placement, and camera behavior.
SCREEN_WIDTH = 1280   # pixels; larger values increase viewport size and UI span
SCREEN_HEIGHT = 720   # pixels; larger values increase viewport height and camera coverage
FPS = 60              # frames per second target; gameplay code still uses dt
FPS_CAP_MIN = 30      # minimum user-selectable cap in Settings (UI/system setting)
FPS_CAP_COARSE_STEP = 5   # FPS step when making larger cap adjustments in Settings
FPS_CAP_FINE_STEP = 1     # FPS step for precise cap tuning in Settings
TITLE = "Mystic Siege"    # window title text (UI-only)
TILE_SIZE = 32            # pixels per world tile; shared by map and spatial placement
WORLD_WIDTH = 3000        # world width in pixels; larger values increase traversal space
WORLD_HEIGHT = 3000       # world height in pixels; larger values increase traversal space


# ============================================================================
# Audio Init
# ============================================================================
# Mixer initialization defaults. These are audio-system tunables, not gameplay.
# Change with care because platform-specific values are chosen to avoid crackle
# and resampling artifacts.
AUDIO_FREQUENCY = 44100         # Hz on Windows/macOS; standard output rate
AUDIO_FREQUENCY_LINUX = 48000   # Hz on Linux; matches common PipeWire/PulseAudio native rate
AUDIO_SIZE = -16                # signed sample bit depth; negative means signed 16-bit audio
AUDIO_CHANNELS = 2              # channel count; 2 = stereo
AUDIO_BUFFER = 512              # samples per chunk on Windows/macOS; lower = lower latency, higher = safer playback
AUDIO_BUFFER_LINUX = 1024       # samples per chunk on Linux; tuned for 48kHz stability


# ============================================================================
# Shared Colors And Visual Tokens
# ============================================================================
# Reused colors live here so HUD, combat feedback, and menus can intentionally
# share a palette. These are visual-only unless a comment notes gameplay coupling.
WHITE = (255, 255, 255)           # RGB tuple; general-purpose light text/highlights
BLACK = (0, 0, 0)                 # RGB tuple; general-purpose outlines/shadows
RED = (255, 0, 0)                 # RGB tuple; danger/damage accent
GOLD = (212, 175, 55)             # RGB tuple; reward/upgrade accent
DARK_PURPLE = (45, 0, 75)         # RGB tuple; fantasy background/accent color
UI_BG = (20, 15, 30, 180)         # RGBA tuple; translucent panel background (UI-only)
XP_COLOR = (80, 220, 255)         # RGB tuple; XP bar/orb accent
HP_COLOR = (60, 200, 80)          # RGB tuple; healthy HP fill color
HP_MED_COLOR = (255, 255, 0)      # RGB tuple; mid-health warning color
HP_LOW_COLOR = (220, 60, 60)      # RGB tuple; low-health danger color
THREAT_ARROW_COLOR = (255, 60, 60)  # RGB tuple; offscreen enemy/downed-player indicator tint

# Threat-arrow safe zones keep edge arrows clear of fixed HUD chrome.
# If new HUD pieces are added to a screen edge, update these margins alongside
# the corresponding panel placement constants below.
HUD_SAFE_TOP = 45       # pixels from top edge; tuned to clear the top HUD bar area
HUD_SAFE_BOTTOM = 20    # pixels from bottom edge; tuned to clear the XP bar area
HUD_SAFE_LEFT = 0       # pixels from left edge; increase if new left-edge HUD appears
HUD_SAFE_RIGHT = 0      # pixels from right edge; increase if new right-edge HUD appears


# ============================================================================
# Player And Combat Foundations
# ============================================================================
# Baseline player runtime values used before hero-specific modifiers are applied.
# These are gameplay tunables shared by movement, pickup, and contact damage flow.
BASE_HP = 100                        # hit points; higher values increase survivability
BASE_SPEED = 200                     # pixels/second; higher values increase movement speed
PICKUP_RADIUS = 80                   # pixels; larger values vacuum XP from farther away
PLAYER_HIT_IFRAME_DURATION = 0.5     # seconds; longer values reduce repeated contact damage
PLAYER_HIT_KNOCKBACK_FORCE = 300     # pixels/second impulse; higher values push the player farther on hit


# ============================================================================
# Crit, XP, And Passive Math
# ============================================================================
# Shared progression/combat math. These are gameplay-facing values and also feed
# hero passive data in HERO_CLASSES, so keep them above that section.
CRIT_CHANCE_BASE = 0.05              # fraction; 0.05 = 5% baseline crit chance for all heroes
CRIT_MULTIPLIER = 2.0                # damage multiplier; higher values make crits hit harder
WIZARD_CRIT_CHANCE_BONUS = 0.10      # fraction added by Wizard passive
WIZARD_SPELL_DAMAGE_BONUS = 0.20     # fraction added to spell damage by Wizard passive
KNIGHT_ARMOR_BONUS_PCT = 0.10                # fraction added to effective armor by Knight passive
BARBARIAN_PHYSICAL_DAMAGE_BONUS = 0.20   # fraction added to physical damage by Barbarian passive
BARBARIAN_MAX_HP_BONUS_PCT = 0.10        # fraction added to max HP by Barbarian passive
RANGER_CRIT_CHANCE_BONUS = 0.10      # fraction added by Ranger passive
RANGER_ARROW_PIERCE_BONUS = 1        # extra enemies pierced by Ranger arrows

BASE_XP_REQUIRED = 50                # XP needed for the first level-up; higher values slow early progression
XP_SCALE_FACTOR = 1.12               # exponential growth factor per level; higher values steepen later leveling
FRIAR_HEAL_PER_XP = 0.1              # HP restored per XP gained; gameplay passive used by Friar
FRIAR_AREA_SIZE_BONUS_PCT = 0.20     # fraction added to area-based effects by Friar passive


# ============================================================================
# Weapons
# ============================================================================
# Tuning note:
# - Weapon ids and stats stay settings-driven so factories, hero starting weapons,
#   and upgrade rewards can all reference one source of truth.
# - Each weapon section is split into Gameplay, Upgrade Levels, and Visual so
#   balance knobs are easier to separate from presentation knobs.
# - Upgrade lists use index 0 for base level, then levels 2-5 as additive deltas.
MAX_WEAPON_SLOTS = 6   # gameplay inventory cap per player; UpgradeSystem should respect this limit


# Arcane Bolt ----------------------------------------------------------------
# Gameplay role: single-target spell projectile with homing, staggered volleys,
# and strong level scaling through extra bolts and pierce.
# Gameplay
ARCANE_BOLT_BASE_DAMAGE = 20.0        # damage per bolt; higher values improve single-hit spell damage
ARCANE_BOLT_BASE_COOLDOWN = 1.0       # seconds between casts; lower values fire more often
ARCANE_BOLT_BASE_BOLT_COUNT = 1       # bolts per cast at level 1
ARCANE_BOLT_BASE_PIERCE = 0           # enemies pierced per bolt before upgrades/passives
ARCANE_BOLT_TARGETING_RANGE = 350     # pixels; larger values let the weapon acquire targets farther away
ARCANE_BOLT_SPREAD = 20               # degrees between multiple bolts; higher values widen the volley
ARCANE_BOLT_STAGGER = 0.25            # seconds between bolts inside one cast; lower values make volleys land faster
ARCANE_BOLT_PROJECTILE_SPEED = 400    # pixels/second; higher values reduce travel time
ARCANE_BOLT_HITBOX_SIZE = (10, 10)    # pixels; gameplay collision rect for each bolt despite its visual-focused name

# Upgrade Levels
# Levels 2-5: +damage, +1 bolt, +1 pierce, then +1 bolt with another damage bump.
ARCANE_BOLT_UPGRADE_LEVELS = [
    {},
    {"base_damage": 10},
    {"bolt_count": 1},
    {"pierce": 1},
    {"bolt_count": 1, "base_damage": 15},
]

# Visual
# Projectile presentation only. Trail and glow knobs affect readability, not damage or targeting.
ARCANE_BOLT_PROJECTILE_SIZE = (22, 22)        # pixels; sprite surface bounds used for drawing
ARCANE_BOLT_PROJECTILE_COLOR = (160, 80, 255)  # RGB tint for the base projectile look
ARCANE_BOLT_OUTER_GLOW_RADIUS = 10            # pixels; larger values create a softer, wider bloom
ARCANE_BOLT_OUTER_GLOW_COLOR = (100, 30, 180)  # RGB outer bloom tint
ARCANE_BOLT_OUTER_GLOW_ALPHA = 80             # alpha 0-255; higher values make the outer glow brighter
ARCANE_BOLT_MID_GLOW_RADIUS = 7               # pixels; controls the saturated inner halo size
ARCANE_BOLT_MID_GLOW_COLOR = (160, 80, 255)   # RGB mid-glow tint
ARCANE_BOLT_MID_GLOW_ALPHA = 190              # alpha 0-255; higher values intensify the mid glow
ARCANE_BOLT_CORE_RADIUS = 4                   # pixels; controls bright core size
ARCANE_BOLT_CORE_COLOR = (210, 140, 255)      # RGB core tint
ARCANE_BOLT_CENTER_RADIUS = 2                 # pixels; tiny center sparkle radius
ARCANE_BOLT_CENTER_COLOR = (240, 210, 255)    # RGB center tint
ARCANE_BOLT_TRAIL_LENGTH = 7                  # samples; higher values leave a longer visible trail
ARCANE_BOLT_TRAIL_RECORD_INTERVAL = 0.02      # seconds between trail samples; lower values smooth the trail
ARCANE_BOLT_TRAIL_COLOR = (140, 60, 220)      # RGB trail tint
ARCANE_BOLT_TRAIL_MAX_ALPHA = 130             # alpha 0-255 of the newest trail segment
ARCANE_BOLT_TRAIL_MAX_RADIUS = 4              # pixels; size of the newest trail segment


# Holy Nova ------------------------------------------------------------------
# Gameplay role: radial burst spell with large area control and stronger value
# from radius/cooldown tuning than projectile speed.
# Gameplay
HOLY_NOVA_BASE_DAMAGE = 20.0          # damage per enemy hit by the ring
HOLY_NOVA_BASE_COOLDOWN = 2.0         # seconds between casts; lower values pulse more often
HOLY_NOVA_BASE_RADIUS = 80            # pixels; larger values increase total area covered
HOLY_NOVA_EXPAND_SPEED = 200          # pixels/second; higher values make the ring reach its radius sooner
HOLY_NOVA_RING_WIDTH = 8              # pixels; damaging band width, so this affects actual hit coverage

# Upgrade Levels
# Levels 2-5: +damage, +radius, faster cooldown, then more damage with a thinner ring.
HOLY_NOVA_UPGRADE_LEVELS = [
    {},
    {"base_damage": 15},
    {"base_radius": 40},
    {"base_cooldown": -0.4},
    {"base_damage": 20, "ring_width": -4},
]

# Visual
# Cast accents for the ring effect. These change readability and style, not ring damage or radius.
HOLY_NOVA_RING_COLOR = (255, 230, 100)     # RGB ring tint
HOLY_NOVA_HIT_SPARK_COLOR = (255, 230, 100)  # RGB hit feedback tint
HOLY_NOVA_INNER_GLOW_COLOR = (255, 245, 180)   # RGB flash at cast origin
HOLY_NOVA_OUTER_BLOOM_COLOR = (255, 215, 80)   # RGB outer halo tint
HOLY_NOVA_FLARE_COLOR = (255, 255, 220)        # RGB spike highlight tint
HOLY_NOVA_SPARK_COLOR = (255, 240, 140)        # RGB spark particle tint
HOLY_NOVA_SPARK_COUNT = 16                     # particles per cast; higher values look richer but cost more draw work
HOLY_NOVA_FLARE_COUNT = 8                      # flare spikes on the ring edge
HOLY_NOVA_FLARE_LENGTH = 14                    # pixels; larger values lengthen the flare spikes
HOLY_NOVA_PARTICLE_SPEED_VARIANCE = 40         # pixels/second variance; higher values create a noisier burst


# Spectral Blade -------------------------------------------------------------
# Gameplay role: continuous close-range orbiting melee. Damage uptime depends on
# blade count, orbit speed, and radius working together.
# Gameplay
SPECTRAL_BLADE_BASE_DAMAGE = 18.0      # damage per hit
SPECTRAL_BLADE_BASE_COOLDOWN = 0.0     # seconds; 0 keeps the blade orbit always active
SPECTRAL_BLADE_BASE_BLADE_COUNT = 2    # orbiting blades at level 1
SPECTRAL_BLADE_ORBIT_RADIUS = 20       # pixels from player center to hilt; larger values sweep a wider circle
SPECTRAL_BLADE_ORBIT_SPEED = 180       # degrees/second; higher values increase hit frequency on nearby enemies
SPECTRAL_BLADE_HIT_COOLDOWN = 0.3       # seconds per-enemy hit cooldown; lower values increase repeated hits

# Upgrade Levels
# Levels 2-5: +1 blade, faster orbit, wider orbit, then +1 blade with more damage.
SPECTRAL_BLADE_UPGRADE_LEVELS = [
    {},
    {"blade_count": 1},
    {"orbit_speed": 60},
    {"orbit_radius": 20},
    {"blade_count": 1, "base_damage": 12},
]

# Visual
# Sword geometry and colors only. These tune silhouette and readability, not hit cadence or orbit coverage.
SPECTRAL_BLADE_BLADE_LENGTH = 78       # pixels; sword length used for rendering
SPECTRAL_BLADE_BLADE_WIDTH = 5         # pixels; blade width
SPECTRAL_BLADE_BLADE_COLOR = (100, 150, 255)   # RGB blade body tint
SPECTRAL_BLADE_OUTLINE_COLOR = (60, 90, 180)   # RGB outline tint
SPECTRAL_BLADE_GRIP_LENGTH = 16        # pixels; hilt length
SPECTRAL_BLADE_GRIP_WIDTH = 5          # pixels; grip thickness
SPECTRAL_BLADE_GUARD_HALF_WIDTH = 17   # pixels; half-width of crossguard
SPECTRAL_BLADE_GUARD_THICKNESS = 4     # pixels; guard depth along the blade axis
SPECTRAL_BLADE_TAPER_START = 0.72      # fraction of blade length where the blade begins tapering
SPECTRAL_BLADE_GRIP_COLOR = (50, 70, 130)       # RGB grip tint
SPECTRAL_BLADE_HIGHLIGHT_COLOR = (190, 215, 255)  # RGB inner highlight tint
SPECTRAL_BLADE_GUARD_COLOR = (160, 190, 255)    # RGB guard/pommel accent tint
SPECTRAL_BLADE_POMMEL_RADIUS = 5       # pixels; pommel size
SPECTRAL_BLADE_GLOW_COLOR = (140, 175, 255)     # RGB outer glow tint
SPECTRAL_BLADE_GLOW_EXTRA_WIDTH = 3     # pixels added around the blade for glow thickness
SPECTRAL_BLADE_HIT_SPARK_COLOR = (100, 150, 255)  # RGB hit feedback tint


# Flame Blast ----------------------------------------------------------------
# Gameplay role: short-range cone burst with burn damage over time.
# Gameplay
FLAME_BLAST_BASE_DAMAGE = 25.0         # direct hit damage per affected enemy
FLAME_BLAST_BASE_COOLDOWN = 1.5        # seconds between casts; lower values improve DPS and control
FLAME_BLAST_CONE_RANGE = 150           # pixels; larger values extend the cone farther out
FLAME_BLAST_CONE_ANGLE = 90            # degrees; larger values widen coverage
FLAME_BLAST_BURN_DAMAGE = 5.0          # damage dealt per burn tick source
FLAME_BLAST_BURN_DURATION = 2.0        # seconds; longer values keep DOT active longer

# Upgrade Levels
# Levels 2-5: +damage, +range, longer burn, then wider cone with another damage bump.
FLAME_BLAST_UPGRADE_LEVELS = [
    {},
    {"base_damage": 15},
    {"cone_range": 40},
    {"burn_duration": 1.5},
    {"cone_angle": 30, "base_damage": 20},
]

# Visual
# Flame particles and color accents. These do not change cone size, burn duration, or damage.
FLAME_BLAST_EFFECT_COLOR = (255, 100, 0)      # RGB cone effect tint
FLAME_BLAST_HIT_SPARK_COLOR = (255, 100, 0)   # RGB hit feedback tint
FLAME_BLAST_INNER_COLOR = (255, 180, 20)      # RGB mid-range particle tint
FLAME_BLAST_CORE_COLOR = (255, 240, 130)      # RGB near-origin particle tint
FLAME_BLAST_PARTICLE_COUNT = 45               # particles per cast; higher values thicken the flame effect
FLAME_BLAST_PARTICLE_LIFETIME = 0.55          # seconds; longer values leave particles visible longer
FLAME_BLAST_PARTICLE_SPEED_MIN = 80           # pixels/second; minimum starting particle speed
FLAME_BLAST_PARTICLE_SPEED_MAX = 430          # pixels/second; maximum starting particle speed
FLAME_BLAST_PARTICLE_RADIUS_MAX = 6           # pixels; max particle size


# Frost Ring -----------------------------------------------------------------
# Gameplay role: radial crowd control with freeze duration as the defining knob.
# Gameplay
FROST_RING_BASE_DAMAGE = 15.0          # damage per enemy hit by the ring
FROST_RING_BASE_COOLDOWN = 3.0         # seconds between casts; lower values improve freeze uptime
FROST_RING_SPEED = 80                  # pixels/second; higher values make the ring expand faster
FROST_RING_MAX_RADIUS = 200            # pixels; larger values increase reach
FROST_RING_FREEZE_DURATION = 1.0       # seconds enemies stay frozen; higher values increase control
FROST_RING_HALF_WIDTH = 5              # pixels; damaging band half-width, so this changes actual hit coverage

# Upgrade Levels
# Levels 2-5: longer freeze, +damage, faster ring travel, then faster cooldown with larger radius.
FROST_RING_UPGRADE_LEVELS = [
    {},
    {"freeze_duration": 0.5},
    {"base_damage": 10},
    {"ring_speed": 30},
    {"base_cooldown": -0.8, "max_radius": 80},
]

# Visual
# Ring styling and secondary particles. These tune clarity and atmosphere, not freeze logic.
FROST_RING_DRAW_WIDTH = 3              # pixels; outline width when rendering the ring
FROST_RING_COLOR = (0, 200, 255)       # RGB ring tint
FROST_RING_HIT_SPARK_COLOR = (0, 200, 255)   # RGB hit feedback tint
FROST_RING_INNER_GLOW_COLOR = (200, 240, 255)   # RGB origin flash tint
FROST_RING_OUTER_BLOOM_COLOR = (80, 160, 220)   # RGB outer halo tint
FROST_RING_SHARD_COLOR = (220, 245, 255)        # RGB crystal shard tint
FROST_RING_MOTE_COLOR = (160, 220, 255)         # RGB mote particle tint
FROST_RING_SHARD_COUNT = 6              # shard spikes per cast; higher values increase edge detail
FROST_RING_SHARD_LENGTH = 12            # pixels; larger values lengthen ice shards
FROST_RING_MOTE_COUNT = 12              # particles per cast; higher values make the effect denser
FROST_RING_MOTE_SPEED_VARIANCE = 30     # pixels/second variance; higher values make motes scatter more


# Lightning Chain ------------------------------------------------------------
# Gameplay role: targeted burst spell that chains through groups. Chain count and
# chain range drive consistency; hop multiplier controls falloff.
# Gameplay
LIGHTNING_CHAIN_BASE_DAMAGE = 30.0     # damage on the first target hit
LIGHTNING_CHAIN_BASE_COOLDOWN = 2.0    # seconds between casts; lower values chain more often
LIGHTNING_CHAIN_TARGETING_RANGE = 400  # pixels; larger values acquire the first target from farther away
LIGHTNING_CHAIN_BASE_CHAIN_COUNT = 3   # total targets in the default chain, including the first hit
LIGHTNING_CHAIN_CHAIN_RANGE = 150      # pixels between hops; larger values connect wider enemy groups
LIGHTNING_CHAIN_BASE_STUN_CHANCE = 0.0 # fraction per hit; base chance to stun
LIGHTNING_CHAIN_STUN_DURATION = 0.5    # seconds; longer values increase control when stun applies
LIGHTNING_CHAIN_HOP_DAMAGE_MULTIPLIER = 0.8   # multiplier per hop; lower values increase damage falloff

# Upgrade Levels
# Levels 2-5: +damage, +2 chain targets, longer hop range, then +1 chain target with stun chance.
LIGHTNING_CHAIN_UPGRADE_LEVELS = [
    {},
    {"base_damage": 15},
    {"chain_count": 2},
    {"chain_range": 50},
    {"chain_count": 1, "stun_chance": 0.25},
]

# Visual
# Arc rendering and endpoint flashes. These affect the look and persistence of chain visuals only.
LIGHTNING_CHAIN_ARC_LIFETIME = 0.12    # seconds; visual arc duration on screen
LIGHTNING_CHAIN_ARC_MIN_SEGMENTS = 3   # minimum zig-zag segments per arc
LIGHTNING_CHAIN_ARC_MAX_SEGMENTS = 5   # maximum zig-zag segments per arc
LIGHTNING_CHAIN_ARC_JITTER = 15        # pixels; higher values make arcs look rougher/more erratic
LIGHTNING_CHAIN_ARC_COLOR = (255, 255, 200)   # RGB core arc tint
LIGHTNING_CHAIN_ARC_WIDTH = 2          # pixels; base core arc thickness
LIGHTNING_CHAIN_HIT_SPARK_COLOR = (255, 255, 100)  # RGB impact spark tint
LIGHTNING_CHAIN_ARC_OUTER_GLOW_COLOR = (80, 160, 255)   # RGB outer bloom tint
LIGHTNING_CHAIN_ARC_OUTER_GLOW_WIDTH = 5                # pixels; thicker glow reads brighter
LIGHTNING_CHAIN_ARC_OUTER_GLOW_ALPHA = 70               # alpha 0-255 at peak brightness
LIGHTNING_CHAIN_ARC_MID_COLOR = (180, 225, 255)         # RGB mid band tint
LIGHTNING_CHAIN_ARC_MID_WIDTH = 3                       # pixels; mid-layer thickness
LIGHTNING_CHAIN_ARC_MID_ALPHA = 160                     # alpha 0-255 at peak brightness
LIGHTNING_CHAIN_IMPACT_RADIUS = 6       # pixels; larger values make node flashes more pronounced
LIGHTNING_CHAIN_IMPACT_COLOR = (180, 220, 255)   # RGB impact flash tint
LIGHTNING_CHAIN_IMPACT_ALPHA = 200      # alpha 0-255 at peak brightness


# Longbow --------------------------------------------------------------------
# Gameplay role: precise ranged physical weapon with fast arrows and crit/pierce scaling.
# Gameplay
LONGBOW_BASE_DAMAGE = 24.0             # damage per arrow
LONGBOW_BASE_COOLDOWN = 1.0            # seconds between shots; lower values improve rate of fire
LONGBOW_TARGETING_RANGE = 520          # pixels; larger values let the player fire from farther away
LONGBOW_PROJECTILE_SPEED = 720         # pixels/second; higher values make arrows feel snappier
LONGBOW_PROJECTILE_LIFETIME = 0.9      # seconds before despawn; higher values extend effective reach
LONGBOW_BASE_PIERCE = 0                # enemies pierced per arrow before upgrades/passives
LONGBOW_BASE_PROJECTILE_COUNT = 1      # arrows per volley at level 1
LONGBOW_SPREAD = 5                     # degrees between multiple arrows; higher values widen the volley
LONGBOW_BASE_CRIT_BONUS = 0.05         # additive crit chance from the weapon itself

# Upgrade Levels
# Levels 2-5: +damage, faster cooldown, +1 pierce, then +1 arrow with extra crit chance.
LONGBOW_UPGRADE_LEVELS = [
    {},
    {"base_damage": 8.0},
    {"base_cooldown": -0.15},
    {"pierce": 1},
    {"projectile_count": 2, "crit_bonus": 0.10},
]

# Visual
# Arrow appearance only. Collision and reach are driven by projectile speed/lifetime, not these draw settings.
LONGBOW_PROJECTILE_COLOR = (170, 120, 60)  # RGB arrow tint
LONGBOW_PROJECTILE_SIZE = (20, 5)      # pixels; projectile footprint used for rendering


# Throwing Axes --------------------------------------------------------------
# Gameplay role: shorter-range physical burst with slower travel, harder hits,
# and a wider multi-projectile arc than Longbow.
# Gameplay
THROWING_AXES_BASE_DAMAGE = 28.0       # damage per axe; higher values emphasize burst
THROWING_AXES_BASE_COOLDOWN = 1.2      # seconds between throws; lower values improve sustained DPS
THROWING_AXES_TARGETING_RANGE = 380    # pixels; shorter than Longbow by design
THROWING_AXES_PROJECTILE_SPEED = 480   # pixels/second; lower values keep the weapon feeling heavier
THROWING_AXES_PROJECTILE_LIFETIME = 1.0   # seconds before despawn
THROWING_AXES_BASE_PIERCE = 0          # enemies pierced per axe before upgrades
THROWING_AXES_BASE_PROJECTILE_COUNT = 1    # axes per throw at level 1
THROWING_AXES_SPREAD = 12              # degrees between extra axes; higher values widen the fan
THROWING_AXES_BASE_CRIT_BONUS = 0.05   # additive crit chance from the weapon itself

# Upgrade Levels
# Levels 2-5: +damage, faster cooldown, +1 pierce, then +2 axes with extra crit chance.
THROWING_AXES_UPGRADE_LEVELS = [
    {},
    {"base_damage": 12.0},
    {"base_cooldown": -0.20},
    {"pierce": 1},
    {"projectile_count": 2, "crit_bonus": 0.10},
]

# Visual
# Axe silhouette and tumble presentation only. These do not change projectile travel, pierce, or crit behavior.
THROWING_AXES_SPIN_SPEED = 360.0       # degrees/second; tumble rate for rendering
THROWING_AXES_PROJECTILE_COLOR = (160, 160, 170)  # RGB blade tint
THROWING_AXES_PROJECTILE_SIZE = (18, 18)          # pixels; square keeps all spin angles readable
THROWING_AXES_HANDLE_COLOR = (90, 60, 30)         # RGB handle tint
THROWING_AXES_GUARD_COLOR = (75, 75, 85)          # RGB bolster tint
THROWING_AXES_OUTLINE_COLOR = (45, 45, 55)        # RGB silhouette outline tint
THROWING_AXES_OUTLINE_WIDTH = 1                   # pixels at 18x18 reference size; scales with projectile size
THROWING_AXES_EDGE_HIGHLIGHT_WIDTH = 2            # pixels at 18x18 reference size; bevel highlight thickness


# ============================================================================
# Enemies
# ============================================================================
# Tuning note:
# - Shared runtime values below affect many enemy classes at once.
# - Per-enemy dicts are intentionally plain data so enemy classes and the spawn
#   registry can read a single settings-driven source of truth.

# Shared enemy runtime tunables.
ENEMY_BASE_ATTACK_COOLDOWN = 1.0   # seconds between contact attacks; lower values increase enemy DPS
ENEMY_MIN_SEPARATION = 30          # pixels; larger values make packs spread out more
ENEMY_KNOCKBACK_FORCE = 180        # pixels/second impulse on hit; higher values push enemies farther
ENEMY_RETARGET_INTERVAL = 0.25     # seconds between nearest-player retarget scans; lower values track players more responsively
ENEMY_SPAWN_OFFSCREEN_MARGIN = 150  # pixels beyond screen bounds for spawn placement; higher values spawn farther offscreen
ENEMY_SPAWN_POSITION_ATTEMPTS = 8   # attempts to find a valid spawn point; higher values improve placement robustness
ENEMY_WARNING_DURATION = 3.0       # seconds warning text remains visible before major wave events
ENEMY_ELITE_HP_MULTIPLIER = 1.5    # multiplier used by elite mode; higher values increase elite durability
ENEMY_ELITE_DAMAGE_MULTIPLIER = 1.5  # multiplier used by elite mode; higher values increase elite threat


# Enemy archetype data -------------------------------------------------------
# Dict fields are gameplay-facing unless marked otherwise. Expected conventions:
# - hp / damage are raw numbers
# - speed values are pixels/second
# - timing fields use seconds
# - angles are degrees
# - RGB tuples are visual-only

# Skeleton: slow melee chaser with slight wander to keep packs from stacking perfectly.
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

# Goblin: fast melee chaser intended to pressure movement with pack spawns.
DARK_GOBLIN_ENEMY_DATA = {
    "name": "Goblin",
    "hp": 20,
    "speed": 160,
    "damage": 8,
    "xp_value": 3,
    "behavior": "chase",
}

# Wraith: medium-speed chaser with a periodic lunge burst.
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

# Plague Bat: fragile fast chaser with wave motion and death splitting.
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

# Mini Bat: follow-on split spawn only. Inherits the parent bat's wave motion knobs.
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

# Cursed Knight: durable melee chaser with a frontal shield damage reducer.
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

# Lich Familiar: orbiting ranged threat that fires slow enemy projectiles.
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

# Stone Golem: high-HP mini-boss with low movement speed and heavy contact damage.
STONE_GOLEM_ENEMY_DATA = {
    "name": "Golem",
    "hp": 500,
    "speed": 40,
    "damage": 40,
    "xp_value": 80,
    "behavior": "chase",
}

# Shared lookup used by the enemy registry/spawner. Keep ids stable because wave
# logic and constructors reference these exact string keys.
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


# ============================================================================
# Wave And Spawn Progression
# ============================================================================
# Global wave pacing. Unlock times use elapsed run seconds. Spawn-rate values are
# seconds between spawn events in WaveManager, so lower values mean denser waves.
WAVE_INITIAL_ACTIVE_POOL = ["Skeleton"]   # enemy ids active from run start
WAVE_INITIAL_SPAWN_RATE = 5.0             # seconds between base spawns at run start
WAVE_INITIAL_BOSS_ACTIVE_POOL = []        # reserved boss pool at run start
WAVE_INITIAL_BOSS_SPAWN_RATE = 120.0      # seconds between boss-pool checks/spawns
WAVE_SKELETON_PACK_MIN = 2                # minimum Skeletons per spawn event
WAVE_SKELETON_PACK_MAX = 4                # maximum Skeletons per spawn event
WAVE_GOBLIN_UNLOCK_TIME = 60              # seconds; Goblins join the wave pool at 1:00
WAVE_GOBLIN_SPAWN_RATE = 4.0              # seconds between Goblin spawn events
WAVE_GOBLIN_PACK_MIN = 3                  # minimum Goblins per spawn event
WAVE_GOBLIN_PACK_MAX = 5                  # maximum Goblins per spawn event
WAVE_WRAITH_UNLOCK_TIME = 120             # seconds; Wraiths join the wave pool at 2:00
WAVE_WRAITH_SPAWN_RATE = 3.5              # seconds between Wraith spawn events
WAVE_WRAITH_PACK_MIN = 1                  # minimum Wraiths per spawn event
WAVE_WRAITH_PACK_MAX = 3                  # maximum Wraiths per spawn event
WAVE_BAT_UNLOCK_TIME = 180                # seconds; Bats join the wave pool at 3:00
WAVE_BAT_SPAWN_RATE = 3.0                 # seconds between Bat spawn events
WAVE_BAT_PACK_MIN = 3                     # minimum Bats per spawn event
WAVE_BAT_PACK_MAX = 6                     # maximum Bats per spawn event
WAVE_BAT_WARNING_TEXT = "BATS INCOMING!"  # UI warning string for the bat event
WAVE_GOLEM_EVENT_TIME = 300               # seconds; golem event starts at 5:00
WAVE_GOLEM_PACK_MIN = 1                   # minimum Golems per event spawn
WAVE_GOLEM_PACK_MAX = 3                   # maximum Golems per event spawn
WAVE_GOLEM_WARNING_TEXT = "GOLEM APPROACHES!"  # UI warning string for the golem event
WAVE_KNIGHT_LICH_UNLOCK_TIME = 240        # seconds; Knights and Liches join at 4:00
WAVE_KNIGHT_LICH_SPAWN_RATE = 2.5         # seconds between Knight/Lich spawn events
WAVE_LICH_PACK_MIN = 1                    # minimum Liches per spawn event
WAVE_LICH_PACK_MAX = 3                    # maximum Liches per spawn event
WAVE_KNIGHT_PACK_MIN = 1                  # minimum Knights per spawn event
WAVE_KNIGHT_PACK_MAX = 2                  # maximum Knights per spawn event
WAVE_ELITE_MODE_TIME = 600                # seconds; elite scaling begins at 10:00
WAVE_ELITE_SPAWN_RATE = 2.0               # seconds between elite-mode spawn events
WAVE_ELITE_WARNING_TEXT = "ELITE ENEMIES ARISE!"   # UI warning for elite mode
WAVE_FINAL_ASSAULT_TIME = 1200            # seconds; final assault starts at 20:00
WAVE_FINAL_ASSAULT_SPAWN_RATE = 1.0       # seconds between final-assault spawn events
WAVE_FINAL_ASSAULT_WARNING_TEXT = "FINAL ASSAULT!"  # UI warning for final assault
WAVE_VICTORY_TIME = 1800                  # seconds; run victory at 30:00


# ============================================================================
# UI And Menu Layout
# ============================================================================
# Tuning note:
# - This section mixes shared UI chrome with menu layout values because the
#   current HUD/menu code reads a flat settings module.
# - Shared slot-panel constants intentionally drive both solo and multiplayer HUD.
HUD_FONT_SIZE = 24             # points; primary in-run HUD font size
SMALL_FONT_SIZE = 16           # points; supporting UI/body text size
TITLE_FONT_SIZE = 72           # points; large menu/title text size

# Main menu ember particles (visual-only).
MAIN_MENU_PARTICLE_INITIAL_COUNT = 60     # particles spawned on menu load
MAIN_MENU_PARTICLE_FADE_RATE = 80         # alpha/second; higher values fade particles faster
MAIN_MENU_PARTICLE_SPAWN_SIZE_MIN = 2     # pixels; minimum ember size
MAIN_MENU_PARTICLE_SPAWN_SIZE_MAX = 3     # pixels; maximum ember size
MAIN_MENU_PARTICLE_SPAWN_ALPHA_MIN = 30   # alpha 0-255; minimum ember opacity
MAIN_MENU_PARTICLE_SPAWN_ALPHA_MAX = 120  # alpha 0-255; maximum ember opacity

# Class select layout (UI-only). These tune card positioning and spacing.
CLASS_SELECT_TITLE_Y = 28             # pixels from top; title anchor
CLASS_SELECT_PROMPT_MARGIN_TOP = 2    # pixels; spacing above prompt text
CLASS_SELECT_GRID_TOP_Y = 160         # pixels from top; first row of hero cards — must clear title + prompt on all platforms
CLASS_SELECT_GRID_BOTTOM_MARGIN = 110 # pixels; gap reserved below card grid bottom for confirm/back buttons
CLASS_SELECT_CARD_WIDTH = 220         # pixels; hero card width
CLASS_SELECT_CARD_HEIGHT = 210        # pixels; hero card height — reduced to fit 2 rows (4+4) within the available vertical space
CLASS_SELECT_CARD_GAP_X = 24          # pixels between card columns
CLASS_SELECT_CARD_GAP_Y = 26          # pixels between card rows
CLASS_SELECT_MAX_COLUMNS = 4          # card columns before wrapping — 4-wide grid gives a 4+4 layout for up to 8 heroes
CLASS_SELECT_CARD_PADDING_X = 16      # pixels; inner horizontal card padding
CLASS_SELECT_COLOR_BAND_HEIGHT = 32   # pixels; color accent band height on each card

# Shared HUD chrome. HUD_EMPTY_SLOT_BG_COLOR is intentionally reused by empty
# weapon slots and HP/XP bar backgrounds so the slot-panel treatment stays matched.
HUD_EMPTY_SLOT_BG_COLOR = (40, 40, 40)    # RGB shared panel/slot background tint
WEAPON_SLOT_LEVEL_BORDER_SEGMENTS = 4     # segment count for level tracker (levels 2-5)
WEAPON_SLOT_LEVEL_BORDER_WIDTH = 2        # pixels; border thickness for slot tracker
WEAPON_SLOT_LEVEL_BORDER_GAP = 4          # pixels; inset between slot edge and tracker segments
WEAPON_SLOT_LEVEL_BORDER_FILLED_COLOR = (255, 215, 0)   # RGB earned-level segment color
WEAPON_SLOT_LEVEL_BORDER_EMPTY_COLOR = (80, 80, 80)     # RGB unearned segment color; intentionally matches empty-slot gray family

# In-run HUD panel layout. These affect both solo and multiplayer because the
# shared slot-panel renderer is used for all player counts.
HUD_PANEL_PADDING = 10              # pixels; inner panel padding
HUD_PANEL_BAR_HEIGHT = 12           # pixels; HP/XP bar height
HUD_PANEL_WEAPON_SLOT_SIZE = 40     # pixels; square slot footprint
HUD_PANEL_WEAPON_SLOT_WIDTH = 40    # pixels; kept separate for compatibility with current HUD code
HUD_PANEL_WEAPON_SLOT_GAP = 4       # pixels between weapon slots
HUD_PANEL_CORNER_RADIUS = 6         # pixels; rounded panel corners
HUD_REVIVE_RING_RADIUS = 28         # pixels; on-screen revive progress ring size
HUD_REVIVE_RING_WIDTH = 4           # pixels; on-screen revive ring stroke width

# Settings menu controls (UI-only). Slider step sizes here should stay readable
# with the FPS cap steps defined earlier in the file.
SETTINGS_SLIDER_STEP_COARSE = 0.05          # normalized slider value step for larger adjustments
SETTINGS_SLIDER_STEP_FINE = 0.02            # normalized slider value step for smaller adjustments
SETTINGS_ANALOG_ADJUST_REPEAT_DELAY = 0.2   # seconds before held analog adjustment repeats
SETTINGS_ANALOG_ADJUST_REPEAT_RATE = 0.08   # seconds between repeated analog adjustments
SETTINGS_SLIDER_VALUE_X_OFFSET = 24         # pixels; spacing between slider and displayed value
SETTINGS_BUTTON_WIDTH = 240                 # pixels; settings menu button width
SETTINGS_BUTTON_HEIGHT = 50                 # pixels; settings menu button height
SETTINGS_BUTTON_START_Y = 390               # pixels from top; first settings button row
SETTINGS_BUTTON_ROW_GAP = 65                # pixels between button rows
SETTINGS_BUTTON_COLUMN_GAP = 40             # pixels between button columns

# HUD panel rectangles keyed by player count, then PlayerSlot.index.
# Keep these tuples lightweight and deterministic; camera/HUD code expects fixed
# screen-space placements rather than computing them from live surfaces each frame.
HUD_PANEL_TOP_LEFT = (20, 20, 320, 148)     # x, y, width, height for the solo / top-left reference panel
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


# ============================================================================
# Input
# ============================================================================
# Controller defaults and keyboard ownership schemes. These are input/UI
# settings, but they also matter to multiplayer menu ownership behavior.
CONTROLLER_DEADZONE = 0.2              # analog magnitude 0-1; higher values ignore more stick drift
CONTROLLER_AXIS_REPEAT_DELAY = 0.4     # seconds before held axis starts repeating in menus
CONTROLLER_AXIS_REPEAT_RATE = 0.15     # seconds between repeated axis navigation events
CONTROLLER_CONFIRM_BUTTON = 0          # default confirm button index (A / Cross)
CONTROLLER_BACK_BUTTON = 1             # default back button index (B / Circle)
CONTROLLER_START_BUTTONS = (7,)        # tuple of default pause/start buttons; extend only for broader controller support

# Default binding payloads persisted by SaveSystem/InputManager.
CONTROLLER_BINDINGS_DEFAULT = {
    "confirm": CONTROLLER_CONFIRM_BUTTON,
    "back": CONTROLLER_BACK_BUTTON,
    "start": list(CONTROLLER_START_BUTTONS),
}
CONTROLLER_BINDINGS_SETTINGS_DEFAULT = {
    "global_bindings": dict(CONTROLLER_BINDINGS_DEFAULT),
    "profiles": {},
}

# Player-facing labels. Keep semantic wording here so menus do not expose raw button ids.
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

# Owned keyboard input schemes. These are shared by lobby, hero select, and
# other owned-menu flows, so do not add hardcoded per-player branches elsewhere.
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


# ============================================================================
# Mouse And Pause UI
# ============================================================================
# Presentation-only cursor and pause menu values.
MOUSE_HIDE_DELAY = 2.0   # seconds of no mouse movement before the cursor hides

# Pause menu button layout/colors (UI-only).
PAUSE_BUTTON_WIDTH = 240             # pixels; main pause button width
PAUSE_BUTTON_HEIGHT = 50             # pixels; main pause button height
PAUSE_BUTTON_SPACING = 18            # pixels between pause buttons
PAUSE_BUTTON_COLOR = (30, 20, 10)    # RGB default pause button color
PAUSE_BUTTON_HOVER_COLOR = (40, 30, 20)  # RGB hover color
PAUSE_BUTTON_TEXT_COLOR = (255, 255, 255)  # RGB button label color
PAUSE_CONFIRM_DIALOG_WIDTH = 420     # pixels; confirmation dialog width
PAUSE_CONFIRM_DIALOG_HEIGHT = 180    # pixels; confirmation dialog height
PAUSE_CONFIRM_DIALOG_BG_COLOR = (20, 15, 10)   # RGB dialog background color
PAUSE_CONFIRM_BUTTON_WIDTH = 150     # pixels; confirm/cancel button width
PAUSE_CONFIRM_BUTTON_HEIGHT = 44     # pixels; confirm/cancel button height
PAUSE_CONFIRM_MESSAGE_FONT_SIZE = 20  # points; confirm dialog text size
PAUSE_CONFIRM_BUTTON_Y_OFFSET = 112   # pixels from dialog top to button row
PAUSE_CONFIRM_BUTTON_INSET = 36       # pixels from dialog sides to button placement
PAUSE_CONFIRM_MESSAGE_Y_OFFSET = 34   # pixels from dialog top to message baseline area


# ============================================================================
# Multiplayer, Camera, And Revive
# ============================================================================
# Tuning note:
# - These values support local co-op but must still preserve 1P as the baseline.
# - Slot-indexed lists below are keyed by PlayerSlot.index and should not grow
#   new P1/P2-specific assumptions in code.
MAX_PLAYERS = 4   # local player cap; current architecture and HUD layouts assume up to 4

# Per-slot UI colors. Index must match PlayerSlot.index.
PLAYER_COLORS = [
    (100, 180, 255),   # slot 0 - blue
    (255, 140, 40),    # slot 1 - orange
    (80, 220, 120),    # slot 2 - green
    (255, 220, 60),    # slot 3 - yellow
]

# Spawn offsets relative to the party spawn anchor. Larger values spread players
# farther apart at run start and on regrouping-style spawns.
SPAWN_OFFSETS = [
    (-80, 0),   # slot 0
    (80, 0),    # slot 1
    (0, 80),    # slot 2
    (0, -80),   # slot 3
]

# Shared camera framing. Primarily multiplayer-facing, but solo camera behavior
# also reads these values through the same system.
CAMERA_ZOOM_MIN = 0.45     # minimum zoom scale; lower values zoom farther out for wider parties
CAMERA_ZOOM_LERP = 2.0     # interpolation speed; higher values make zoom react faster
CAMERA_PLAYER_MARGIN = 200  # pixels of padding around tracked players; larger values zoom out sooner

# Downed/revive runtime. These are gameplay/multiplayer settings used by Player
# and HUD systems, but solo still shares parts of the visual path.
REVIVE_RADIUS = 96             # pixels; teammate must stay within this range to revive
REVIVE_DURATION = 2.0          # seconds required to complete a revive
REVIVE_HEALTH_FRACTION = 0.5   # fraction of max HP restored on revive
REVIVE_IFRAME_DURATION = 2.0   # seconds of safety after revive; longer values reduce chain-downs
DOWNED_ALPHA = 100             # alpha 0-255 for downed player rendering; visual-only feedback


# ============================================================================
# Game State Ids
# ============================================================================
# Scene/state string constants shared across scene management and UI flow.
STATE_MENU = "menu"
STATE_CLASS_SELECT = "class_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"
STATE_VICTORY = "victory"
STATE_SETTINGS = "settings"
STATE_STATS = "stats"
STATE_LOBBY = "lobby"


# ============================================================================
# Hero Definitions
# ============================================================================
# HERO_CLASSES is the declarative source of truth for hero roster tuning.
# Each entry is intentionally a plain dict so lobby, class select, and gameplay
# can all consume the same lightweight data structure.
#
# Required keys:
# - name: display name
# - hp / speed / armor: gameplay baselines
# - passive_desc: player-facing UI text
# - starting_weapon: stable weapon id resolved through the weapon factory
# - color: placeholder-sprite accent (visual-only)
# - sprite: asset path
# - passives: declarative gameplay modifiers consumed by runtime systems
HERO_CLASSES = [
    {
        "name": "Knight",
        "hp": 150,
        "speed": 180,
        "armor": 15,
        "passive_desc": "+10% armor bonus.\nImmune to knockback.",
        "starting_weapon": "SpectralBlade",
        "color": (180, 140, 60),
        "sprite": "assets/sprites/heroes/knight.png",
        "passives": {
            "armor_bonus_pct": KNIGHT_ARMOR_BONUS_PCT,
            "knockback_immune": True,
        },
    },
    {
        "name": "Wizard",
        "hp": 80,
        "speed": 240,
        "armor": 0,
        "passive_desc": "+20% spell damage.\n+10% crit chance.",
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
        "passive_desc": "Heal 1 HP per 10 XP gained.\n+20% area size.",
        "starting_weapon": "HolyNova",
        "color": (200, 180, 120),
        "sprite": "assets/sprites/heroes/friar.png",
        "passives": {
            "heal_per_xp": FRIAR_HEAL_PER_XP,
            "area_size_bonus_pct": FRIAR_AREA_SIZE_BONUS_PCT,
        },
    },
    {
        "name": "Ranger",
        "hp": 95,
        "speed": 225,
        "armor": 3,
        "passive_desc": "+10% crit chance.\nArrows pierce 1 extra enemy.",
        "starting_weapon": "Longbow",
        "color": (90, 170, 110),
        "sprite": "assets/sprites/heroes/ranger.png",
        "passives": {
            "crit_chance_bonus": RANGER_CRIT_CHANCE_BONUS,
            "arrow_pierce_bonus": RANGER_ARROW_PIERCE_BONUS,
        },
    },
    {
        "name": "Barbarian",
        "hp": 120,
        "speed": 205,
        "armor": 8,
        "passive_desc": "+20% physical damage.\n+10% max HP.",
        "starting_weapon": "ThrowingAxes",
        "color": (170, 80, 45),
        "sprite": "assets/sprites/heroes/barbarian.png",
        "passives": {
            "physical_damage_bonus_pct": BARBARIAN_PHYSICAL_DAMAGE_BONUS,
            "max_hp_bonus_pct": BARBARIAN_MAX_HP_BONUS_PCT,
        },
    },
]
