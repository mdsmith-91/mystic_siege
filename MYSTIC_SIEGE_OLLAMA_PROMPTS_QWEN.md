# MYSTIC SIEGE — AI CODING PROMPTS (Optimized for qwen-coder via Ollama)
# Python 3.12.13 | pygame-ce | Ollama + qwen2.5-coder
# ============================================================
# HOW TO USE THIS FILE:
#   1. Paste the SYSTEM CONTEXT block into your Ollama system prompt field
#      (in Open WebUI: the "System" field | CLI: your Modelfile)
#   2. Use the SESSION PRIMER at the start of every new chat session
#   3. Send ONE prompt block at a time — never combine multiple prompts
#   4. If output is cut off mid-file, send: "Continue from where you left off"
#   5. Work through phases in order — each builds on the last
#   6. Phases 1-4 = runnable game. Phases 5-6 = full experience. 7-9 = polish.
# ============================================================


==============================================================
SYSTEM CONTEXT
(Put this in your Modelfile or Open WebUI system prompt field.
Do NOT paste this as a user message — it belongs in the system slot.)
==============================================================

You are an expert Python game developer helping build "Mystic Siege" —
a top-down medieval fantasy survivor game (Vampire Survivors / Brotato style)
using Python 3.12.13 and pygame-ce.

Critical output rules — follow these exactly, every time:
- NEVER truncate code. If a file is long, output it in parts but NEVER use
  placeholder comments like "# ... rest of code ...", "# same as before",
  or "# continue implementation". Always output every line.
- Output ONE file at a time. After each file, stop and wait for confirmation.
- If a file would exceed your output limit, say "Outputting Part 1 of N"
  and wait for me to say "continue" before outputting the next part.
- Never add unrequested features or refactor code I didn't ask you to change.
- If something is ambiguous, implement the most sensible default and add a
  comment noting your assumption — do not ask for clarification unless blocked.

Code standards:
- Use pygame-ce (not standard pygame)
- All entity classes inherit from pygame.sprite.Sprite
- Use pygame.sprite.Group for all sprite collections
- Always accept delta time as dt (float, seconds) in update() methods
- All constants live in settings.py — never hardcode magic numbers in logic
- One class per file (small utility classes may share a file)
- Add a one-line docstring to every class and every public method
- Use Python 3.12 type hint syntax: list[int] not List[int], dict[str,int] not Dict[str,int],
  tuple[int,...] not Tuple[int,...] — no need to import from typing for these
- Use match/case statements where they improve clarity over long if/elif chains

Project file structure:
mystic_siege/
├── main.py
├── settings.py
├── requirements.txt
├── requirements-dev.txt
├── run_check.py
├── .python-version          (contains "3.12.13" — created by pyenv)
├── src/
│   ├── __init__.py
│   ├── game.py
│   ├── scene_manager.py
│   ├── game_scene.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── base_entity.py
│   │   ├── player.py
│   │   ├── enemy.py
│   │   ├── projectile.py
│   │   ├── xp_orb.py
│   │   ├── effects.py
│   │   └── enemies/
│   │       ├── __init__.py
│   │       ├── skeleton.py
│   │       ├── dark_goblin.py
│   │       ├── wraith.py
│   │       ├── plague_bat.py
│   │       ├── cursed_knight.py
│   │       └── lich_familiar.py
│   ├── weapons/
│   │   ├── __init__.py
│   │   ├── base_weapon.py
│   │   ├── arcane_bolt.py
│   │   ├── holy_nova.py
│   │   ├── spectral_blade.py
│   │   ├── flame_blast.py
│   │   ├── frost_ring.py
│   │   └── lightning_chain.py
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── wave_manager.py
│   │   ├── xp_system.py
│   │   ├── upgrade_system.py
│   │   ├── collision.py
│   │   ├── camera.py
│   │   └── save_system.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── hud.py
│   │   ├── upgrade_menu.py
│   │   ├── main_menu.py
│   │   ├── class_select.py
│   │   ├── game_over.py
│   │   └── settings_menu.py
│   └── utils/
│       ├── __init__.py
│       ├── timer.py
│       ├── resource_loader.py
│       ├── spritesheet.py
│       ├── audio_manager.py
│       └── placeholder_assets.py
└── assets/
    ├── sprites/
    ├── audio/
    └── fonts/


==============================================================
SESSION PRIMER
(Paste this at the START of every new Ollama chat session,
before any phase prompt. Update the last two lines each time.)
==============================================================

We are building "Mystic Siege" — a top-down medieval fantasy survivor game
in Python 3.12.13 + pygame-ce. Follow all rules from your system prompt exactly.

Remember:
- Output complete files only — no truncation, no placeholders
- One file per message, then wait for me to confirm before continuing
- If a file is too long for one message, say "Part 1 of N" and wait for "continue"
- Never hardcode values — all constants go in settings.py
- All entities inherit pygame.sprite.Sprite and accept dt in update()
- Use Python 3.12 type syntax: list[int], dict[str,int] — no typing module imports needed
- Do not use datetime.utcnow() — use datetime.now(timezone.utc) instead

Current phase: [REPLACE THIS with e.g. "Phase 2 — Core Entities"]
Last completed: [REPLACE THIS with e.g. "Prompt 1C — Utility Classes"]
Next task: [PASTE THE PROMPT BLOCK YOU WANT TO WORK ON BELOW THIS LINE]


==============================================================
PHASE 1 — PROJECT SCAFFOLD
==============================================================

--- PROMPT 1A — Requirements, Init Files & Settings ---
(Send this alone as your first message after the session primer)

Generate requirements.txt (just the file, nothing else):
- pygame-ce>=2.5.0
- pytmx>=3.32
- numpy>=1.26

Wait for confirmation, then generate requirements-dev.txt:
- pyinstaller>=6.0

Wait for confirmation, then generate a .python-version file containing just the text:
3.12.13

Wait for confirmation, then generate ALL __init__.py files in a single response
(they are trivial — each contains only one comment line):
  src/__init__.py                  → # Mystic Siege — source package
  src/entities/__init__.py         → # Entities package
  src/entities/enemies/__init__.py → # Enemy subclasses
  src/weapons/__init__.py          → # Weapon classes
  src/systems/__init__.py          → # Game systems
  src/ui/__init__.py               → # UI scenes and overlays
  src/utils/__init__.py            → # Utility helpers
Output them all together labeled by path.

Wait for confirmation, then generate settings.py with ALL of these constants:

Python 3.12.13 is being used — ensure all code is compatible. Do not use any
APIs removed in 3.12 (e.g. use datetime.now(timezone.utc) not datetime.utcnow()).
Use modern type hint syntax: list[int], dict[str,int], tuple[int,...] — no typing imports needed.

SCREEN:
  SCREEN_WIDTH = 1280
  SCREEN_HEIGHT = 720
  FPS = 60
  TITLE = "Mystic Siege"
  TILE_SIZE = 32
  WORLD_WIDTH = 3000
  WORLD_HEIGHT = 3000

COLORS (as RGB tuples):
  WHITE, BLACK, RED, GOLD = (212, 175, 55), DARK_PURPLE = (45, 0, 75)
  UI_BG = (20, 15, 30, 180)  # RGBA for semi-transparent panels
  XP_COLOR = (80, 220, 255)
  HP_COLOR = (60, 200, 80)
  HP_LOW_COLOR = (220, 60, 60)

PLAYER BASE STATS:
  BASE_HP = 100
  BASE_SPEED = 200
  PICKUP_RADIUS = 80

XP:
  BASE_XP_REQUIRED = 50
  XP_SCALE_FACTOR = 1.12

SPAWNING:
  INITIAL_SPAWN_RATE = 3.0
  MIN_SPAWN_RATE = 0.3

UI:
  HUD_FONT_SIZE = 24
  SMALL_FONT_SIZE = 16
  TITLE_FONT_SIZE = 72

GAME STATES (string constants):
  STATE_MENU = "menu"
  STATE_CLASS_SELECT = "class_select"
  STATE_PLAYING = "playing"
  STATE_PAUSED = "paused"
  STATE_GAMEOVER = "gameover"
  STATE_VICTORY = "victory"

HERO_CLASSES list of 3 dicts, each with keys:
  name, hp, speed, armor, passive_desc, starting_weapon, color (RGB for placeholder sprite)

  Hero 1 — "Knight":
    hp=150, speed=180, armor=15, color=(180,140,60)
    passive_desc="Takes 15% less damage. Immune to knockback."
    starting_weapon="SpectralBlade"

  Hero 2 — "Wizard":
    hp=80, speed=240, armor=0, color=(160,60,220)
    passive_desc="Spells deal 20% more damage. +10% crit chance."
    starting_weapon="ArcaneBolt"

  Hero 3 — "Friar":
    hp=110, speed=210, armor=5, color=(200,180,120)
    passive_desc="Heals 1 HP per 10 XP orbs collected."
    starting_weapon="HolyNova"

Output requirements.txt, wait for confirmation, then output settings.py.


--- PROMPT 1B — Entry Point & Game Shell ---
(One file at a time — send this after 1A is confirmed)

Generate main.py:
- Initialize pygame-ce with mixer
- Set display to SCREEN_WIDTH x SCREEN_HEIGHT with TITLE
- Create pygame.time.Clock
- Instantiate Game from src/game.py
- Call game.run()
- Handle clean quit in a try/finally block

Wait for confirmation, then generate src/game.py — Game class:
- __init__: create screen, clock, SceneManager, set initial state to STATE_MENU
- run(): main loop — handle events, update(dt), draw(), clock.tick(FPS)
- dt capped at 0.05 to prevent spiral-of-death on lag spikes
- F11 toggles fullscreen
- Delegates all scene logic to SceneManager

Wait for confirmation, then generate src/scene_manager.py — SceneManager:
- Holds scene instances: main_menu, class_select, game_scene, game_over
- Scenes are created lazily (game_scene only created when a run starts, to get fresh state)
- switch_to(scene_name, **kwargs) — passes kwargs to scene constructor if needed
- current scene receives: handle_events(events), update(dt), draw(screen)
- Scene objects communicate transitions via a .next_scene attribute (None = no change)

One file per message. Wait for my "ok" between each.


--- PROMPT 1C — Utility Classes ---
(Send each file request separately if output gets cut off)

Generate src/utils/timer.py — Timer class:
- __init__(self, duration: float, repeat: bool = False)
- update(self, dt: float) -> bool  — returns True the frame the timer fires
- reset(self), pause(self), resume(self)
- is_finished property
- elapsed property (seconds since last reset)

Wait for confirmation, then generate src/utils/resource_loader.py — ResourceLoader singleton:
- Accessed via ResourceLoader.instance() class method
- load_image(path, scale=None, colorkey=None) -> pygame.Surface
  Returns a magenta 32x32 placeholder rect if file not found (game runs without assets)
- load_sound(path) -> pygame.mixer.Sound or None if file not found
- load_font(name, size) -> pygame.font.Font (falls back to pygame default font)
- Internal dict cache keyed by (path, scale, colorkey)

Wait for confirmation, then generate src/utils/spritesheet.py — Spritesheet:
- __init__(self, path: str, tile_w: int, tile_h: int)
- get_frame(self, col: int, row: int) -> pygame.Surface
- get_animation(self, frame_coords: list[tuple[int,int]]) -> list[pygame.Surface]
- Uses ResourceLoader internally for the base image

One file per message.


==============================================================
PHASE 2 — CORE ENTITIES
==============================================================

--- PROMPT 2A — Base Entity ---

Generate src/entities/base_entity.py — BaseEntity(pygame.sprite.Sprite):
- __init__(self, pos: tuple, groups: tuple)
- Attributes: pos (pygame.math.Vector2), vel (Vector2), hp, max_hp, speed
- image and rect must be set by subclasses before calling super().__init__
- update(self, dt: float): pos += vel * dt, sync rect.center to pos
- take_damage(self, amount: float): subtract armor if present, floor at 0 hp, call kill() if dead
- heal(self, amount: float): add hp, clamp to max_hp
- draw_health_bar(self, surface, offset: pygame.math.Vector2):
    small bar above sprite, green when >50% hp, yellow >25%, red otherwise
    only draw if hp < max_hp
- is_alive property: returns self.alive (set False when hp reaches 0)

Output the complete file only. Wait for confirmation.


--- PROMPT 2B — Player ---

Generate src/entities/player.py — Player(BaseEntity):

__init__(self, pos, hero_class_data: dict, groups):
- Read hp, speed, armor from hero_class_data
- Placeholder image: 32x32 surface filled with hero_class_data["color"], label "P" centered
- Active weapons list (max 6 slots)
- Passive stats as instance variables:
    armor = hero_class_data["armor"]
    regen_rate = 0.0       # HP per second
    xp_multiplier = 1.0
    pickup_radius = PICKUP_RADIUS  (from settings)
    cooldown_reduction = 0.0       # 0.0 to 0.9 max
    crit_chance = 0.0
    damage_multiplier = 1.0
- iframes: float = 0.0  (countdown timer for invincibility frames)
- facing: Vector2 = Vector2(1, 0)  (updated each frame from movement)
- kill_count: int = 0
- orbs_collected: int = 0  (for Friar passive)

update(self, dt):
1. Read WASD/arrow input, build direction vector, normalize if non-zero
2. Update facing if moving
3. pos += direction * speed * dt
4. Clamp pos to world bounds (WORLD_WIDTH, WORLD_HEIGHT from settings)
5. Regen tick: heal(regen_rate * dt)
6. Iframe countdown: iframes = max(0, iframes - dt)
7. Update all weapons: for w in weapons: w.update(dt)
8. Sync rect

add_weapon(self, weapon_instance): append if len < 6
upgrade_weapon(self, weapon_class_name: str): find weapon by class name, call weapon.upgrade()
apply_passive(self, stat: str, value: float): add value to named stat attribute

Output the complete file. Wait for confirmation.


--- PROMPT 2C — Enemy Base & Two Starter Enemies ---

Generate src/entities/enemy.py — Enemy(BaseEntity):

__init__(self, pos, target, all_groups: tuple, enemy_data: dict):
- target = player reference
- enemy_data keys: name, hp, speed, damage, xp_value, behavior ("chase" or "ranged")
- Placeholder image: 32x32 surface filled with RED, first letter of name centered in WHITE
- attack_timer: float = 0.0
- attack_cooldown: float = 1.0
- knockback_vel: Vector2 = Vector2(0,0)  (decays each frame)
- xp_value from enemy_data

update(self, dt):
1. If behavior == "chase": direction toward target, move
2. If behavior == "ranged": stop at 200px from target, face target
3. Apply knockback: pos += knockback_vel * dt, knockback_vel *= (1 - 8*dt) clamped to 0
4. Attack timer counts down; when 0 and overlapping target: target.take_damage(damage), reset timer
5. Sync rect

apply_knockback(self, direction: Vector2, force: float): knockback_vel = direction * force
on_death(self, xp_orb_group): import and spawn XPOrb at self.pos with self.xp_value

Output enemy.py. Wait for confirmation.

Then generate src/entities/enemies/skeleton.py — Skeleton(Enemy):
- enemy_data = {name:"Skeleton", hp:30, speed:80, damage:10, xp_value:5, behavior:"chase"}
- In update: add small random angle offset (±5 degrees, change every 0.5s) so they spread out
- Image: 28x28 light gray rect on 32x32 transparent surface

Wait for confirmation, then generate src/entities/enemies/dark_goblin.py — DarkGoblin(Enemy):
- enemy_data = {name:"Goblin", hp:20, speed:160, damage:8, xp_value:4, behavior:"chase"}
- Image: 24x24 green rect on 32x32 transparent surface (smaller = feels faster)

One file per message.


--- PROMPT 2D — Projectile & XP Orb ---

Generate src/entities/projectile.py — Projectile(pygame.sprite.Sprite):

__init__(self, pos, direction: Vector2, speed: float, damage: float,
         groups, enemy_group_ref, pierce: int = 0, homing: bool = False,
         color: tuple = (200, 100, 255)):
- image: 10x10 circle surface with given color
- direction normalized on init
- enemies_hit: set() — tracks enemy ids already hit (for pierce)
- lifetime: float = 4.0  (auto-destroy after 4 seconds)

update(self, dt):
1. If homing and enemy_group_ref has sprites:
   - Find nearest enemy
   - Steer direction toward it by max 120 degrees/sec (gradual curve)
2. pos += direction * speed * dt
3. lifetime -= dt; if <= 0: kill()
4. If pos outside world bounds: kill()
5. Sync rect

on_hit(self, enemy):
- If enemy.sprite_id in enemies_hit: return (already hit this enemy)
- Add to enemies_hit
- enemy.take_damage(damage)
- If pierce <= 0: kill() else: pierce -= 1

Output projectile.py. Wait for confirmation.

Then generate src/entities/xp_orb.py — XPOrb(pygame.sprite.Sprite):
- __init__(self, pos, value: int, groups)
- image: 12x12 circle, gold color (212, 175, 55) on transparent surface
- float_offset: float = 0.0  (sine wave for bobbing animation)
- float_speed = 3.0
- update(self, dt): float_offset += float_speed * dt; draw_y = sin(float_offset) * 3
  (visual only — rect.centery stays at world pos for collision)
- collected: bool = False

One file per message.


==============================================================
PHASE 3 — WEAPONS
(Each weapon is its own prompt — send one at a time)
==============================================================

--- PROMPT 3A — Base Weapon ---

Generate src/weapons/base_weapon.py — BaseWeapon:

__init__(self, owner, projectile_group, enemy_group):
- owner = Player reference
- level: int = 1  (1-5)
- cooldown_timer: float = 0.0
- upgrade_levels: list[dict] = []  (defined by subclasses)
- Subclasses must set: name, description, base_damage, base_cooldown

update(self, dt: float):
- cooldown_timer -= dt
- If cooldown_timer <= 0: fire(); reset timer with _get_effective_cooldown()

_get_effective_cooldown(self) -> float:
- return base_cooldown * (1.0 - owner.cooldown_reduction)

upgrade(self):
- If level >= 5: return
- Apply self.upgrade_levels[level] dict to self attributes
- level += 1

fire(self): raise NotImplementedError

Output the complete file. Wait for confirmation.


--- PROMPT 3B — Arcane Bolt ---

Generate src/weapons/arcane_bolt.py — ArcaneBolt(BaseWeapon):

name = "Arcane Bolt"
description = "Fires homing bolts at the nearest enemy."
base_damage = 20.0
base_cooldown = 1.2
bolt_count = 1
homing = True
projectile_color = (160, 80, 255)

upgrade_levels (applied at levels 2-5):
  L2: {"base_damage": 10}           — +10 damage
  L3: {"bolt_count": 1}             — fire 2 bolts (spread slightly)
  L4: {"pierce": 1}                 — bolts pierce 1 enemy
  L5: {"bolt_count": 1, "base_damage": 15}  — 3 bolts, more damage

fire(self):
- Find nearest enemy in enemy_group
- If none: return
- Spawn bolt_count Projectiles at owner.pos, aimed at nearest enemy
  (if bolt_count > 1, spread them ±10 degrees apart)
- All bolts use current damage * owner.damage_multiplier

Output the complete file. Wait for confirmation.


--- PROMPT 3C — Holy Nova ---

Generate src/weapons/holy_nova.py — HolyNova(BaseWeapon):

name = "Holy Nova"
description = "Emits an expanding ring of holy light, damaging all enemies it touches."
base_damage = 25.0
base_cooldown = 2.0
base_radius = 80
expand_speed = 200  # px per second
ring_width = 8

upgrade_levels:
  L2: {"base_damage": 15}
  L3: {"base_radius": 40}
  L4: {"base_cooldown": -0.4}
  L5: {"base_damage": 20, "ring_width": 6}  — wider ring, more damage

This weapon doesn't use Projectile. It manages its own ring hitbox:
- Keep a list of active rings, each a dict: {radius, max_radius, damage, enemies_hit: set}
- fire(): append new ring dict
- update(dt): expand all active rings, check circle-vs-rect overlap against each enemy,
  deal damage once per enemy per ring, remove rings that exceed max_radius

Output the complete file. Wait for confirmation.


--- PROMPT 3D — Spectral Blade ---

Generate src/weapons/spectral_blade.py — SpectralBlade(BaseWeapon):

name = "Spectral Blade"
description = "Spectral swords orbit the player, passing through enemies."
base_damage = 18.0
base_cooldown = 0.0  (no cooldown — orbiting continuously)
blade_count = 2
orbit_radius = 90
orbit_speed = 180  # degrees per second
blade_size = (24, 8)
orbit_angle: float = 0.0  (current rotation, increments each frame)

Per-enemy hit cooldown dict: {enemy_id: timer} — each enemy can only be hit once per 0.5s.

update(self, dt):
1. orbit_angle += orbit_speed * dt
2. For each blade index i in range(blade_count):
   - angle = orbit_angle + (360/blade_count * i)
   - blade_pos = owner.pos + Vector2 rotated by angle at orbit_radius
   - Create a rect at blade_pos
   - Check rect against each enemy in enemy_group
   - If hit and not in cooldown: deal damage, start 0.5s cooldown for that enemy
3. Draw blades directly in draw(surface, offset) method

upgrade_levels:
  L2: {"blade_count": 1}      — 3 blades
  L3: {"orbit_speed": 60}     — faster rotation
  L4: {"orbit_radius": 20}    — wider orbit
  L5: {"blade_count": 1, "base_damage": 12}  — 4 blades, more damage

Note: SpectralBlade overrides update() fully — base class fire() is not used.
Include a draw(surface, camera_offset) method called from game_scene.

Output the complete file. Wait for confirmation.


--- PROMPT 3E — Flame Blast ---

Generate src/weapons/flame_blast.py — FlameBlast(BaseWeapon):

name = "Flame Blast"
description = "Blasts a cone of fire toward the nearest enemy."
base_damage = 30.0
base_cooldown = 1.5
cone_range = 150
cone_angle = 90  # degrees total arc
burn_damage = 5.0  # per second
burn_duration = 2.0  # seconds

Track burning enemies: dict {enemy_id: remaining_burn_time}
On update: tick down burn timers, apply burn_damage * dt to still-burning enemies.

fire(self):
- Find nearest enemy and aim the cone toward it
- For each enemy in enemy_group:
    dist = distance from owner.pos to enemy.pos
    if dist > cone_range: skip
    angle_to_enemy = angle between the stored fire direction and direction to enemy
    if angle_to_enemy <= cone_angle/2: hit the enemy
      - deal base_damage * owner.damage_multiplier
      - apply burn (add to burn dict)

upgrade_levels:
  L2: {"base_damage": 15}
  L3: {"cone_range": 40}
  L4: {"burn_duration": 1.5}
  L5: {"cone_angle": 30, "base_damage": 20}  — wider cone, more damage

Include a draw_effect(surface, camera_offset) that draws a transparent orange fan shape
for the duration of the swing (visible for 0.2s after firing). Store a swing_timer float.

Output the complete file. Wait for confirmation.


--- PROMPT 3F — Frost Ring ---

Generate src/weapons/frost_ring.py — FrostRing(BaseWeapon):

name = "Frost Ring"
description = "Expands a freezing ring outward, temporarily immobilizing enemies."
base_damage = 15.0
base_cooldown = 3.0
ring_speed = 80  # px per second outward
max_radius = 200
freeze_duration = 1.5

Track frozen enemies: dict {enemy_id: remaining_freeze_time}
While frozen: enemy.speed = 0 (restore on unfreeze).

Active rings list: each ring is {radius: float, damage_done: set()}
fire(): append new ring
update(dt):
- Tick freeze timers, restore speed when timer hits 0
- Expand all rings
- Check each ring against enemies (circle vs rect)
- If hit and enemy not in ring's damage_done: deal damage, freeze enemy, add to done set
- Remove rings exceeding max_radius

upgrade_levels:
  L2: {"freeze_duration": 0.5}
  L3: {"base_damage": 10}
  L4: {"ring_speed": 30}
  L5: {"base_cooldown": -0.8, "max_radius": 80}  — more frequent, bigger reach

Draw ring as a cyan circle outline (pygame.draw.circle with width=3).

Output the complete file. Wait for confirmation.


--- PROMPT 3G — Lightning Chain ---

Generate src/weapons/lightning_chain.py — LightningChain(BaseWeapon):

name = "Lightning Chain"
description = "Strikes the nearest enemy, then chains to nearby foes."
base_damage = 35.0
base_cooldown = 1.8
chain_count = 3    # max enemies to chain to after initial target
chain_range = 150  # max distance between chain jumps
stun_chance = 0.0  # 0.0-1.0
stun_duration = 0.5

lightning_arcs: list — each arc is {"start": Vector2, "end": Vector2, "timer": float}
  Timer counts down from 0.12s — arcs are drawn for that long then removed.

fire(self):
1. Find nearest enemy to owner
2. If none: return
3. Build chain: start with nearest, find next closest enemy within chain_range
   that hasn't been hit in this chain. Repeat up to chain_count times.
4. For each enemy in chain: deal base_damage * owner.damage_multiplier (diminish by 10% per hop)
   Chance to stun: if random() < stun_chance: freeze enemy briefly
5. Store arc positions for drawing

update(dt):
- Call super().update(dt)
- Tick lightning arc timers, remove expired arcs

Draw arcs as jagged yellow/white lines (zigzag between start and end with 3-4 midpoints
randomly offset ±15px perpendicular).

upgrade_levels:
  L2: {"base_damage": 15}
  L3: {"chain_count": 2}       — chains to 5 enemies
  L4: {"chain_range": 50}
  L5: {"chain_count": 1, "stun_chance": 0.25}  — 6 chains, stun added

Output the complete file. Wait for confirmation.


==============================================================
PHASE 4 — GAME SYSTEMS
(One file per prompt — send one at a time)
==============================================================

--- PROMPT 4A — Wave Manager ---

Generate src/systems/wave_manager.py — WaveManager:

Manages enemy spawning and difficulty over time.

__init__(self, player, all_sprites, enemy_group, xp_orb_group):
- elapsed: float = 0.0
- spawn_timer: float = 0.0
- spawn_rate: float = INITIAL_SPAWN_RATE
- active_pool: list = ["Skeleton"]  — names of currently spawnable enemies
- elite_mode: bool = False
- warning_text: str = ""
- warning_timer: float = 0.0

Enemy data — define as module-level dicts (not classes yet):
  SKELETON_DATA    = {name:"Skeleton",  hp:30,  speed:80,  damage:10, xp_value:5,  behavior:"chase"}
  GOBLIN_DATA      = {name:"Goblin",    hp:20,  speed:160, damage:8,  xp_value:4,  behavior:"chase"}
  WRAITH_DATA      = {name:"Wraith",    hp:40,  speed:120, damage:15, xp_value:10, behavior:"chase"}
  BAT_DATA         = {name:"Bat",       hp:15,  speed:220, damage:8,  xp_value:6,  behavior:"chase"}
  GOLEM_DATA       = {name:"Golem",     hp:500, speed:40,  damage:40, xp_value:80, behavior:"chase"}
  KNIGHT_DATA      = {name:"Knight",    hp:80,  speed:110, damage:20, xp_value:15, behavior:"chase"}
  LICH_DATA        = {name:"Lich",      hp:35,  speed:90,  damage:12, xp_value:12, behavior:"ranged"}

Wave timeline (check elapsed >= threshold, trigger once using a set of already-triggered events):
  0s:    active_pool = ["Skeleton"], spawn_rate = 3.0
  60s:   add "Goblin", spawn_rate = 2.5
  120s:  add "Wraith", spawn_rate = 2.0
  300s:  add "Bat", spawn_rate = 1.5,  show warning "BATS INCOMING!"
  480s:  spawn 1 Golem (one-time event), show warning "GOLEM APPROACHES!"
  600s:  add "Knight", add "Lich", spawn_rate = 1.0
  900s:  elite_mode = True, spawn_rate = 0.7, warning "ELITE ENEMIES ARISE!"
  1200s: spawn_rate = 0.5, show warning "FINAL ASSAULT!"
  1800s: set a victory_flag = True

update(self, dt):
- elapsed += dt
- Check timeline triggers
- spawn_timer -= dt; if <= 0: _spawn_wave(); reset spawn_timer
- Tick warning_timer

_spawn_wave(self): pick random enemy type from active_pool, call _spawn_enemy
  Special: Goblin spawns in groups of 3-5

_spawn_enemy(self, data: dict, count: int = 1):
- For each: pick random edge of world, 100px outside screen view
- Import correct class based on data["name"] (Skeleton, DarkGoblin, or Enemy base for others)
- If elite_mode: multiply hp and damage by 1.5
- Add to all_sprites and enemy_group

_get_spawn_pos(self) -> Vector2: random point on one of 4 world edges

get_elapsed_str(self) -> str: return "MM:SS" formatted string

get_warning(self) -> str: return warning_text if warning_timer > 0 else ""

Output the complete file. Wait for confirmation.


--- PROMPT 4B — XP System ---

Generate src/systems/xp_system.py — XPSystem:

Handles XP collection, leveling, and orb pickup.

__init__(self):
- current_xp: float = 0.0
- current_level: int = 1
- xp_to_next: float = BASE_XP_REQUIRED
- levelup_pending: bool = False

update(self, dt, player, xp_orb_group):
- For each orb in xp_orb_group:
    dist = distance from player.pos to orb.rect.center
    if dist <= player.pickup_radius and not orb.collected:
        collect_orb(orb, player)

collect_orb(self, orb, player):
- orb.collected = True
- orb.kill()
- gained = orb.value * player.xp_multiplier
- current_xp += gained
- player.orbs_collected += 1
- Check Friar passive: if player has "Friar" class and orbs_collected % 10 == 0:
    player.heal(1)
- check_levelup()

check_levelup(self) -> bool:
- While current_xp >= xp_to_next:
    current_xp -= xp_to_next
    current_level += 1
    xp_to_next = int(BASE_XP_REQUIRED * (XP_SCALE_FACTOR ** current_level))
    levelup_pending = True
- return levelup_pending

consume_levelup(self): levelup_pending = False

xp_progress(self) -> float: return current_xp / xp_to_next  (0.0 to 1.0)

Output the complete file. Wait for confirmation.


--- PROMPT 4C — Upgrade System ---

Generate src/systems/upgrade_system.py — UpgradeSystem:

Manages the upgrade card pool and level-up choices.

Define PASSIVE_UPGRADES as a module-level list of dicts:
  Each dict: {name, description, stat, value, icon_color (RGB)}
  Include all 7:
    +20 Max HP          → stat="max_hp",          value=20,   color=(60,200,80)
    +5% Move Speed      → stat="speed_pct",        value=0.05, color=(100,200,255)
    +10% Pickup Radius  → stat="pickup_radius_pct",value=0.10, color=(212,175,55)
    +5 Armor            → stat="armor",             value=5,    color=(160,160,160)
    +0.5 HP/s Regen     → stat="regen_rate",        value=0.5,  color=(120,255,120)
    +10% XP Gain        → stat="xp_multiplier_pct", value=0.10, color=(80,220,255)
    +5% Cooldown Reduc  → stat="cooldown_reduction",value=0.05, color=(255,140,60)

Define WEAPON_CLASSES as module-level list of weapon class names (strings):
  ["ArcaneBolt","HolyNova","SpectralBlade","FlameBlast","FrostRing","LightningChain"]

get_random_choices(self, player) -> list[dict]:
- Build candidate list:
    - Weapons player does NOT have (offer as "new weapon" card)
    - Weapons player HAS but not at level 5 (offer as "upgrade" card)
    - All passive upgrades always available
- Return 3 randomly selected without duplicates
- Always ensure at least 1 passive is included
- If player has all weapons at max level: return 3 passives

apply_choice(self, choice: dict, player):
- If choice has "weapon_class" key:
    Import and instantiate the weapon, call player.add_weapon(weapon)
    Or if it's an upgrade: player.upgrade_weapon(choice["weapon_class"])
- If choice has "stat" key: call _apply_passive(choice, player)

_apply_passive(self, choice, player):
  Handle each stat type:
  - "max_hp": player.max_hp += value; player.hp += value
  - "speed_pct": player.speed *= (1 + value)
  - "pickup_radius_pct": player.pickup_radius *= (1 + value)
  - "armor": player.armor += value
  - "regen_rate": player.regen_rate += value
  - "xp_multiplier_pct": player.xp_multiplier *= (1 + value)
  - "cooldown_reduction": player.cooldown_reduction = min(0.9, player.cooldown_reduction + value)

Output the complete file. Wait for confirmation.


--- PROMPT 4D — Camera ---

Generate src/systems/camera.py — Camera:

Smooth-following camera clamped to world bounds.

__init__(self, screen_w: int, screen_h: int):
- offset: Vector2 = Vector2(0, 0)
- lerp_speed: float = 5.0  (higher = snappier follow)

update(self, target_pos: Vector2, dt: float):
- target_offset = target_pos - Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
- Clamp target_offset so camera never shows outside world bounds
- self.offset = lerp(self.offset, target_offset, lerp_speed * dt)
  (lerp: offset + (target - offset) * t, clamped so t doesn't exceed 1.0)

apply(self, entity) -> pygame.Rect:
  return entity.rect.move(-self.offset)

apply_pos(self, world_pos: Vector2) -> Vector2:
  return world_pos - self.offset

screen_to_world(self, screen_pos: Vector2) -> Vector2:
  return screen_pos + self.offset

Output the complete file. Wait for confirmation.


--- PROMPT 4E — Collision System ---

Generate src/systems/collision.py — CollisionSystem:

Handles all collision detection for the game.

IFRAME_DURATION = 0.5  # seconds of invincibility after player takes a hit

check_all(self, player, enemy_group, projectile_group):
- Call all three check methods below

check_player_enemy_contact(self, player, enemy_group):
- For each enemy in enemy_group:
    if player.rect.colliderect(enemy.rect) and player.iframes <= 0:
        player.take_damage(enemy.damage)
        player.iframes = IFRAME_DURATION
        knockback_dir = (player.pos - enemy.pos).normalize()
        player.vel = knockback_dir * 300  # brief knockback
        (vel decays: add player velocity decay in Player.update — vel *= max(0, 1 - 8*dt))

check_projectile_enemies(self, projectile_group, enemy_group):
- Use pygame.sprite.groupcollide(projectile_group, enemy_group, False, False)
- For each (projectile, enemy_list) in result:
    for enemy in enemy_list: projectile.on_hit(enemy)

check_weapon_hits(self, player, enemy_group):
- For orbit weapons (SpectralBlade): handled internally in weapon.update()
- For area weapons (HolyNova, FrostRing): handled internally in weapon.update()
- This method is a hook for any weapon that needs external collision checking

Output the complete file. Wait for confirmation.


==============================================================
PHASE 5 — UI & SCENES
(One file per prompt)
==============================================================

--- PROMPT 5A — HUD ---

Generate src/ui/hud.py — HUD:

Draws all in-game overlay UI in screen space (no camera offset).

draw(self, screen, player, xp_system, wave_manager, show_fps=False, fps=0):

1. HP Bar (top-left, x=20, y=20):
   - Background rect 200x20, dark
   - Fill rect scaled to hp/max_hp ratio
   - Color: HP_COLOR if >50%, yellow if >25%, HP_LOW_COLOR otherwise
   - Text: "HP  85 / 150" to the right of bar

2. XP Bar (bottom of screen, full width, y=SCREEN_HEIGHT-30, height=20):
   - Background full-width dark rect
   - Fill rect scaled to xp_system.xp_progress()
   - Color: XP_COLOR with glow (draw twice, outer with alpha 80)
   - Text: "LVL 7" on left side of bar

3. Timer (top-center):
   - wave_manager.get_elapsed_str() in large font, white with dark shadow

4. Kill counter (top-right):
   - "✦ {player.kill_count}" right-aligned

5. Weapon slots (bottom-right, 6 slots of 40x40):
   - Dark background per slot
   - Gold border on occupied slots
   - First letter of weapon name centered in slot
   - Slot color = weapon's projectile_color or a default per weapon type

6. Wave warning (center screen, fades out):
   - wave_manager.get_warning() if non-empty
   - Large red/orange text centered horizontally at y=200

7. FPS counter (top-left corner, small, if show_fps): f"FPS: {fps:.0f}"

Use semi-transparent surfaces (convert_alpha) for bar backgrounds.
Use pygame.font.SysFont("serif", size) as fallback — no external font required.

Output the complete file. Wait for confirmation.


--- PROMPT 5B — Main Menu ---

Generate src/ui/main_menu.py — MainMenu scene:

Attributes:
  next_scene: str = None  (set when transitioning)
  next_scene_kwargs: dict = {}
  particles: list  (falling ember/spark dots)

Particle: dict with keys pos, vel, size, alpha, color
  - Spawn 2 new particles per frame at random x, top of screen
  - Drift downward + slight random x drift
  - Fade out (alpha decreases)
  - Remove when off-screen or alpha <= 0

handle_events(self, events):
  - Click "New Run" → next_scene = "class_select"
  - Click "Quit" → pygame.quit() + sys.exit()
  - Hover detection: track mouse pos, highlight button under cursor

update(self, dt): update particles

draw(self, screen):
  1. Fill screen with very dark color (15, 10, 25)
  2. Draw particles as small colored circles
  3. Title "MYSTIC SIEGE" centered at y=160, large font, GOLD color
     with dark glow/shadow offset by 3px
  4. Subtitle "A Medieval Survivor" smaller, gray, below title
  5. Buttons centered horizontally:
     "NEW RUN" at y=380
     "QUIT"    at y=450
     Each button: dark rect 240x50, gold border, white text
     Highlighted button: slightly lighter background

Output the complete file. Wait for confirmation.


--- PROMPT 5C — Class Select ---

Generate src/ui/class_select.py — ClassSelect scene:

next_scene: str = None
selected_class: dict = None

Lays out 3 hero cards horizontally centered on screen.
Card size: 260x380. Spacing: 40px between cards.

handle_events(self, events):
  - Click on a card: selected_class = HERO_CLASSES[i]
  - Click "CONFIRM" (shown after selection): next_scene="game", next_scene_kwargs={"hero":selected_class}
  - Click "BACK": next_scene="menu"
  - Hover: track hovered card index

draw(self, screen):
  1. Dark background (same as main menu)
  2. Title "CHOOSE YOUR HERO" at top, centered
  3. For each of 3 HERO_CLASSES cards:
     - Dark stone background rect
     - Top band filled with hero["color"] (40px tall)
     - Hero name (bold, large) below color band
     - Stats grid: HP / SPD / ARM values
     - Passive ability text (wrapped to card width)
     - Starting weapon name
     - Gold border if hovered, brighter gold if selected
  4. "CONFIRM" button (only shown if a card is selected) at bottom center
  5. "BACK" button bottom-left

Output the complete file. Wait for confirmation.


--- PROMPT 5D — Upgrade Menu ---

Generate src/ui/upgrade_menu.py — UpgradeMenu:

This is an overlay (not a full scene). Called from game_scene when leveling up.

__init__(self, choices: list[dict], upgrade_system, player):
  choices = list of 3 upgrade dicts from UpgradeSystem
  selected: int = -1
  hovered: int = -1
  done: bool = False  (set True after selection, game_scene checks this)

Card layout: 3 cards side by side, centered on screen
  Card size: 260x360. Gap: 30px.
  Cards start at x = (SCREEN_WIDTH - (3*260 + 2*30)) / 2

handle_events(self, events):
  - Mouse move: update hovered
  - Click on card i: apply choice, set done = True
  - Key 1/2/3: same as clicking card 1/2/3

draw(self, screen):
  1. Semi-transparent dark overlay covering entire screen (alpha=160)
  2. "LEVEL UP!" text centered at top (y=80), large, GOLD, with pulse animation
     (scale the text size slightly with sin(pygame.time.get_ticks()/300))
  3. For each card:
     - Draw background rect (dark stone: 35, 30, 50)
     - Top icon area (top 100px): filled with choice["icon_color"] or weapon color
       with weapon initial or stat symbol centered
     - Upgrade name in bold centered in middle section
     - Description text (word-wrapped) in lower section
     - Gold border (2px normally, 4px when hovered)
     - Scale up 3% on hover (use pygame.transform.scale for the card surface)
  4. "Press 1 / 2 / 3 or click to choose" hint text at bottom

Output the complete file. Wait for confirmation.


--- PROMPT 5E — Game Over Screen ---

Generate src/ui/game_over.py — GameOver scene:

next_scene: str = None

__init__(self, victory: bool, stats: dict):
  victory: bool
  stats keys: time_str, kills, level, weapons (list of names)

handle_events(self, events):
  "PLAY AGAIN" → next_scene = "class_select"
  "MAIN MENU"  → next_scene = "menu"

draw(self, screen):
  1. Dark background
  2. Large title: "VICTORY" (gold) or "DEFEATED" (red), centered, y=150
     with animated glow (alternate brightness each second)
  3. Stats block centered below title:
     "Time Survived: {time_str}"
     "Enemies Slain: {kills}"
     "Level Reached: {level}"
     "Weapons: {', '.join(weapons)}"
  4. Two buttons: "PLAY AGAIN" and "MAIN MENU", centered, y=480 and y=550

Output the complete file. Wait for confirmation.


==============================================================
PHASE 6 — INTEGRATION
==============================================================

--- PROMPT 6A — Game Scene ---

Generate src/game_scene.py — GameScene:

This wires all systems together into the main gameplay loop.

__init__(self, hero: dict):
  Create groups: all_sprites, player_group, enemy_group, projectile_group,
                 xp_orb_group, effect_group
  
  Instantiate in this order:
  1. player = Player(center_of_world, hero, (all_sprites, player_group))
  2. Give player its starting weapon:
     Import the correct weapon class from hero["starting_weapon"]
     Instantiate it with (player, projectile_group, enemy_group)
     player.add_weapon(weapon)
  3. camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
  4. wave_manager = WaveManager(player, all_sprites, enemy_group, xp_orb_group)
  5. xp_system = XPSystem()
  6. upgrade_system = UpgradeSystem()
  7. collision_system = CollisionSystem()
  8. hud = HUD()
  9. upgrade_menu = None  (created when leveling up)
  10. paused = False
  11. next_scene: str = None
  12. next_scene_kwargs: dict = {}
  13. show_fps = False
  14. background = generate a 3000x3000 surface tiled with 32x32 dark gray/green rects
      (checkerboard of (30,35,25) and (25,30,20) to suggest ground tiles)
      Do this efficiently: draw a small tile pattern then scale — NOT 3000*3000 loops

handle_events(self, events):
  - ESC: toggle paused
  - F3: toggle show_fps
  - If upgrade_menu and not upgrade_menu.done: pass events to upgrade_menu
  - If upgrade_menu and upgrade_menu.done: upgrade_system.apply_choice(choice, player)
    then set upgrade_menu = None, xp_system.consume_levelup()

update(self, dt):
  If paused or upgrade_menu: return
  all_sprites.update(dt)  — this updates player, enemies, projectiles, orbs
  wave_manager.update(dt)
  collision_system.check_all(player, enemy_group, projectile_group)
  xp_system.update(dt, player, xp_orb_group)
  camera.update(player.pos, dt)
  
  Check levelup:
    if xp_system.levelup_pending and upgrade_menu is None:
        choices = upgrade_system.get_random_choices(player)
        upgrade_menu = UpgradeMenu(choices, upgrade_system, player)
  
  Check win: if wave_manager.victory_flag: transition to game_over with victory=True
  Check lose: if not player.is_alive: transition to game_over with victory=False

draw(self, screen):
  1. Blit background with camera offset (only the visible portion — use subsurface or clip)
  2. For each sprite in all_sprites (sorted by rect.bottom for depth):
       screen.blit(sprite.image, camera.apply(sprite))
       sprite.draw_health_bar(screen, camera.offset) if enemy
  3. Draw weapon effects that need explicit draw calls (SpectralBlade, FlameBlast arc, etc.)
  4. hud.draw(screen, player, xp_system, wave_manager, show_fps, clock_fps)
  5. If upgrade_menu: upgrade_menu.draw(screen)
  6. If paused: draw "PAUSED" centered in large text with semi-transparent overlay

Output the complete file. Wait for confirmation.


--- PROMPT 6B — Integration Wiring & Run Check ---

Review and update src/game.py and src/scene_manager.py to:
1. Import GameScene, MainMenu, ClassSelect, GameOver correctly
2. Create scenes lazily: GameScene is re-instantiated on each new run
3. Pass hero dict: ClassSelect sets next_scene_kwargs={"hero": selected_class}
   SceneManager passes this to GameScene constructor
4. Pass end-of-run stats: GameScene sets next_scene_kwargs={"victory":..., "stats":{...}}
5. Full transition chain: menu → class_select → game → game_over → menu (or class_select)
6. Global F11 fullscreen toggle handled in Game.run(), not in scenes

Output updated game.py. Wait for confirmation.
Output updated scene_manager.py. Wait for confirmation.

Then generate run_check.py:
- Try importing every module in the project
- Print "OK: {module}" or "FAIL: {module} — {error}" for each
- At end: initialize pygame, print pygame version, print Python version,
  confirm Python version is 3.12.x (warn if not), print "All checks passed" or list failures
- Run with: python run_check.py

Output run_check.py. Wait for confirmation.


==============================================================
PHASE 7 — AUDIO & PLACEHOLDER ASSETS
==============================================================

--- PROMPT 7A — Audio Manager ---

Generate src/utils/audio_manager.py — AudioManager singleton:

Class-level constants for SFX names:
  PLAYER_HIT = "player_hit"
  PLAYER_DEATH = "player_death"
  ENEMY_DEATH = "enemy_death"
  XP_PICKUP = "xp_pickup"
  LEVEL_UP = "level_up"
  WEAPON_ARCANE = "arcane_bolt"
  WEAPON_NOVA = "holy_nova"
  WEAPON_FLAME_BLAST = "flame_blast"
  WEAPON_BLADE = "spectral_blade"
  WEAPON_CHAIN = "lightning_chain"
  WEAPON_FROST = "frost_ring"

instance() class method returns singleton.

All methods fail silently (try/except) if pygame.mixer not initialized or file missing.

load_sfx(name: str, path: str): load into _sfx_cache dict
load_music(path: str): pygame.mixer.music.load
play_sfx(name: str, volume: float = 1.0): play from cache if exists
play_music(path: str, loop: bool = True, fade_ms: int = 500)
stop_music(), pause_music(), resume_music()
set_master_volume(v: float): sets both sfx and music volume
set_sfx_volume(v: float): stored, applied to all cached sounds
set_music_volume(v: float): pygame.mixer.music.set_volume

Output the complete file. Wait for confirmation.


--- PROMPT 7B — Placeholder Asset Generator ---

Generate src/utils/placeholder_assets.py — standalone script:

When run (python src/utils/placeholder_assets.py):
1. Initialize pygame (headless: os.environ["SDL_VIDEODRIVER"] = "dummy")
2. Create all asset directories:
   assets/sprites/heroes/
   assets/sprites/enemies/
   assets/sprites/projectiles/
   assets/sprites/effects/
   assets/sprites/ui/
   assets/audio/sfx/
   assets/audio/music/
   assets/fonts/
3. Generate and save PNG files using pygame.draw:

Heroes (32x32):
  knight.png   — (180,140,60) filled rect, "K" label
  wizard.png   — (160,60,220) filled rect, "W" label
  friar.png    — (200,180,120) filled rect, "F" label

Enemies (32x32):
  skeleton.png    — (200,200,200) rect, "S"
  goblin.png      — (60,160,60) rect, "G"
  wraith.png      — (100,100,180) rect with alpha 180, "W"
  bat.png         — (80,40,80) rect, "B"
  golem.png       — (120,100,80) rect 48x48, "G" (larger)
  knight_e.png    — (100,100,140) rect, "K"
  lich.png        — (140,60,160) rect, "L"

Projectiles (16x16 circles):
  arcane.png   — purple (160,80,255)
  nova.png     — gold (212,175,55)
  fire.png     — orange (255,100,20)
  frost.png    — cyan (80,200,255)
  lightning.png — yellow (255,240,60)

XP Orb (12x12):
  xp_orb.png  — gold circle

UI weapon icons (32x32): one per weapon, use matching projectile color

4. Print "Generated {count} placeholder assets to assets/"
5. Print "Run 'python main.py' to start the game"

Output the complete file. Wait for confirmation.


==============================================================
PHASE 8 — ADDITIONAL ENEMIES & VISUAL EFFECTS
(One file per prompt)
==============================================================

--- PROMPT 8A — Visual Effects ---

Generate src/entities/effects.py — four effect sprite classes:

1. DamageNumber(pygame.sprite.Sprite):
   __init__(self, pos, amount: float, groups, is_player_damage=False):
   - Text: str(int(amount))
   - Color: (255,80,80) if is_player_damage, (255,220,60) if amount > 40, else WHITE
   - Font size: 18 + min(int(amount/10), 14)  (bigger hits = bigger text)
   - Velocity: Vector2(random -20 to 20, -80)
   - lifetime = 0.8
   update(dt): pos += vel*dt; vel.y += 40*dt (gravity); lifetime -= dt; kill() when done
   Alpha fades out in last 0.3s.

2. HitSpark(pygame.sprite.Sprite):
   __init__(self, pos, color: tuple, groups):
   - 6 particles: list of dicts {pos, vel (random outward), radius, lifetime}
   - image: transparent surface sized to contain all particles
   - Total lifetime = 0.25s
   update(dt): move particles, shrink radius, fade

3. DeathExplosion(pygame.sprite.Sprite):
   __init__(self, pos, radius: int, color: tuple, groups):
   - Expanding circle, starts at radius/4, expands to radius over 0.4s
   - Alpha fades from 200 to 0
   update(dt): expand, fade, kill when done

4. LevelUpEffect(pygame.sprite.Sprite):
   __init__(self, pos, groups):
   - Ring of 12 gold particles orbiting outward
   - lifetime = 1.5s
   - Particles expand outward then fade

All effects: image is a transparent surface, updated each frame.

Output the complete file. Wait for confirmation.


--- PROMPT 8B — Wraith ---

Generate src/entities/enemies/wraith.py — Wraith(Enemy):

enemy_data = {name:"Wraith", hp:40, speed:120, damage:15, xp_value:10, behavior:"chase"}

Overrides:
- image: 28x28 semi-transparent blue-gray surface (alpha=180)
- Ignores wall collision (no clamping to world bounds in update — passes through)
- lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
  (lunge_active: bool, lunge_duration countdown)
- update(dt): call super but after movement, handle lunge timing

Output the complete file. Wait for confirmation.


--- PROMPT 8C — Plague Bat ---

Generate src/entities/enemies/plague_bat.py — PlagueBat(Enemy):

enemy_data = {name:"Bat", hp:15, speed:220, damage:8, xp_value:6, behavior:"chase"}
split_chance = 0.4  — on death, 40% chance to spawn 2 mini bats

Overrides:
- image: 20x20 dark purple rect
- Movement: arc pattern — add sine wave offset perpendicular to direction
  wave_offset = sin(elapsed * 4) * 50  (elapsed tracked in self._t)
  perpendicular = direction rotated 90 degrees
  effective_dir = direction + perpendicular * wave_offset_normalized

on_death(self, xp_orb_group):
  - Call super().on_death() to spawn XP orb
  - If random() < split_chance and not self.is_mini:
      spawn 2 MiniBat at self.pos (MiniBat is a nested subclass with hp=7, speed=280)

Output the complete file. Wait for confirmation.


--- PROMPT 8D — Cursed Knight ---

Generate src/entities/enemies/cursed_knight.py — CursedKnight(Enemy):

enemy_data = {name:"Knight", hp:80, speed:110, damage:20, xp_value:15, behavior:"chase"}

Shield mechanic:
- shield_facing: Vector2  — points toward player each frame
- take_damage(amount): 
    angle = angle between shield_facing and direction of incoming hit
    if angle < 60 degrees (frontal): apply 20% of damage (80% reduction)
    else: apply full damage
- Caller must pass hit_direction to take_damage — override signature:
    take_damage(self, amount, hit_direction=None)

Visually: 32x32 steel-gray rect with a small blue square on the "front"
  (shield_facing determines which side to draw the blue square on)

update(dt): call super(); update shield_facing = (target.pos - self.pos).normalize()

Output the complete file. Wait for confirmation.


--- PROMPT 8E — Lich Familiar ---

Generate src/entities/enemies/lich_familiar.py — LichFamiliar(Enemy):

enemy_data = {name:"Lich", hp:35, speed:90, damage:12, xp_value:12, behavior:"ranged"}

Behavior:
- Maintains orbit distance of ~200px from player
  orbit_angle: float — increments each frame at 45 deg/sec
  target_pos = player.pos + Vector2 at orbit_angle at radius 200
  Moves toward target_pos rather than player directly

- fire_timer: float — fires a slow magic orb every 2.5s at player
  Orb: Projectile(pos, direction_to_player, speed=120, damage=12, pierce=0, homing=False, color=(200,60,255))

update(dt):
  1. Update orbit_angle
  2. Move toward orbit target pos
  3. Tick fire_timer, spawn orb when fires

image: 28x28 purple rect

Output the complete file. Wait for confirmation.


==============================================================
PHASE 9 — POLISH & META
==============================================================

--- PROMPT 9A — Save System ---

Generate src/systems/save_system.py — SaveSystem:

Simple JSON persistence in saves/progress.json.

DEFAULT_SAVE = {
  "total_runs": 0,
  "total_kills": 0,
  "total_time_played": 0.0,
  "highest_level": 1,
  "best_time_survived": 0.0,
  "unlocked_heroes": ["Knight"],
  "settings": {
    "music_volume": 0.5,
    "sfx_volume": 0.8,
    "fullscreen": False,
    "show_fps": False
  }
}

Methods:
  load() -> dict: load from file or return copy of DEFAULT_SAVE if not found
  save(data: dict): write to saves/progress.json (create dir if needed)
  update_after_run(self, run_result: dict):
    run_result keys: kills, level, time_survived, victory
    Merge into persistent stats and save.
  reset(): overwrite with DEFAULT_SAVE
  get_setting(key: str): shortcut for data["settings"][key]
  set_setting(key: str, value): update and save immediately

Output the complete file. Wait for confirmation.


--- PROMPT 9B — Settings Menu ---

Generate src/ui/settings_menu.py — SettingsMenu scene:

next_scene: str = None
Uses SaveSystem to persist changes immediately.

Settings to show:
  Music Volume   — horizontal slider 0-100
  SFX Volume     — horizontal slider 0-100
  Fullscreen     — toggle button (ON / OFF)
  Show FPS       — toggle button (ON / OFF)
  Reset Progress — button (opens a confirmation sub-dialog)

Slider implementation:
  Each slider: a track rect + a handle rect
  On mouse down on handle: dragging = True
  While dragging: update value based on mouse x position within track
  On mouse up: dragging = False
  Value saves on mouse up

Confirmation dialog for Reset Progress:
  Small centered panel: "Are you sure? This cannot be undone."
  Buttons: "YES, RESET" and "CANCEL"
  confirm_dialog_open: bool flag

draw style: same dark medieval aesthetic as other menus

Output the complete file. Wait for confirmation.


--- PROMPT 9C — Final Polish Additions ---

These are targeted additions — output each as a diff/patch showing only what to add.

ADDITION 1 — Player iframe flash (add to src/entities/player.py):
In update(), when iframes > 0: toggle self.image alpha between 255 and 80
every 0.1s using a flash_timer counter.

ADDITION 2 — Player death fade (add to src/entities/player.py):
When hp <= 0: set dying=True, death_timer=1.0
In update() while dying: death_timer -= dt; set image alpha = int(255 * death_timer)
When death_timer <= 0: call super().kill() and set is_alive=False

ADDITION 3 — Wave incoming arrows (add to src/ui/hud.py):
New method draw_threat_arrows(screen, player, enemy_group, camera):
  For each enemy more than 400px offscreen, draw a small arrow at the screen edge
  pointing toward that enemy. Use enemy type color. Show max 8 arrows.
  Call this from hud.draw().

ADDITION 4 — F12 screenshot (add to src/game.py):
In handle_events: if key F12 pressed:
  from datetime import datetime, timezone
  filename = f"screenshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
  pygame.image.save(self.screen, filename)
  print(f"Screenshot saved: {filename}")

ADDITION 5 — README.md (create at project root):
  # Mystic Siege
  Brief description, screenshot placeholder note, install instructions,
  run instructions, controls table (WASD/Arrows=move, ESC=pause, F11=fullscreen,
  F3=FPS, F12=screenshot, 1/2/3=upgrade select), asset credits section.

Output each addition clearly labeled. Wait for confirmation between each.


==============================================================
ITERATION PROMPTS
(Use these anytime during development — they work independently)
==============================================================

--- BUG FIX ---
I'm getting this error:
[PASTE FULL TRACEBACK HERE]

It happens when: [DESCRIBE THE SITUATION]

Here is the relevant file:
[PASTE THE COMPLETE FILE]

Diagnose the issue, then output the complete corrected file.
Do not make any other changes — only fix the bug.


--- ADD NEW ENEMY ---
Add a new enemy to Mystic Siege called [NAME].

Stats: hp=[X], speed=[X], damage=[X], xp_value=[X]
Behavior: [DESCRIBE — chase / ranged / orbit / etc.]
Special mechanic: [DESCRIBE any unique behavior]
Visual: [DESCRIBE color/size for placeholder]
Appears at: [X] seconds into the run

Create src/entities/enemies/[filename].py as a complete file.
Then show me only the lines to add to src/systems/wave_manager.py
(the import and the timeline entry).


--- ADD NEW WEAPON ---
Add a new weapon to Mystic Siege called [NAME].

Type: [projectile / orbit / area / cone / chain / etc.]
Behavior: [DESCRIBE what it does]
Level 1 stats: damage=[X], cooldown=[X]s, [other relevant stats]
Upgrade path (levels 2-5): [DESCRIBE what each upgrade improves]
Visual: color=[RGB], projectile/effect shape=[DESCRIBE]

Create src/weapons/[filename].py as a complete file.
Then show me only the lines to add to src/systems/upgrade_system.py
(add the weapon class name to WEAPON_CLASSES).


--- BALANCE PASS ---
I've been playtesting and the balance feels off.
Here are my observations: [DESCRIBE what feels wrong]

Review these stats and suggest adjustments:
[PASTE relevant sections of settings.py or enemy/weapon data]

Show me your analysis, then output only the changed values.
Do not rewrite entire files — just the specific values to change and where.


--- PERFORMANCE INVESTIGATION ---
The game is dropping to [X] FPS with approximately [Y] enemies on screen.

Here is my current game_scene.py update() method:
[PASTE THE METHOD]

Identify the most likely bottleneck and suggest the fix.
If it's collision detection: implement spatial hashing.
If it's sprite drawing: implement dirty rect rendering.
If it's enemy AI: implement update culling for offscreen enemies.
Show complete implementation of whichever fix is needed.


--- REPLACE PLACEHOLDER ASSET ---
I have a real sprite at assets/sprites/[path/to/file.png].
It is [W]x[H] pixels. [Single frame / Spritesheet with [N] frames at [tile_w]x[tile_h]].

Update [src/entities/FILE.py] to load this image instead of the placeholder rect.
Use ResourceLoader to load it.
[If animated: use Spritesheet and add an animation list + frame timer to update().]

Show me only the changed lines in [FILE.py].


==============================================================
CREATIVE FREEDOM NOTES
==============================================================

These are intentionally left open for your team to decide — the code
scaffolds them but doesn't dictate the specifics:

HERO BALANCE — The stat numbers in HERO_CLASSES are starting points.
  After playtesting, adjust freely in settings.py without touching any other file.

MAP LAYOUT — The background is a procedural tile grid for MVP.
  When you're ready, use Tiled editor to create a real .tmx map.
  The Camera and ResourceLoader are already set up for pytmx.

ASSET PIPELINE — Swap any placeholder at any time.
  ResourceLoader.load_image() returns a fallback if the file doesn't exist,
  so real assets can be added one at a time without breaking anything.

AUDIO — AudioManager is wired up but no .wav/.ogg files are required.
  Add files to assets/audio/ and call AudioManager.instance().load_sfx()
  in game_scene.__init__() whenever you're ready.

DIFFICULTY CURVE — Wave timeline values in wave_manager.py are tunable.
  The thresholds, spawn rates, and enemy mix are the primary feel levers.
  Adjust them after playtesting — no other files need to change.

NEW HERO CLASSES — Add a new dict to HERO_CLASSES in settings.py.
  ClassSelect reads the list dynamically. It's a one-line addition.

==============================================================
END OF PROMPT FILE
==============================================================
