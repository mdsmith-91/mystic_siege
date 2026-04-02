# Mystic Siege — Project Context for Claude Code

## What This Project Is

Mystic Siege is a top-down medieval fantasy survivor game built in Python 3.12.13
with pygame-ce. Style: Vampire Survivors / Brotato. Players choose a hero, survive
escalating waves of enemies, collect XP orbs, level up, and pick upgrades — all in
15-30 minute sessions.

Two developers, AI-assisted workflow, small scope first.

---

## Tech Stack

- **Language:** Python 3.12.13
- **Framework:** pygame-ce (NOT standard pygame — never import pygame, always pygame-ce)
- **Dependencies:** pygame-ce>=2.5.0, pytmx>=3.32, numpy>=1.26
- **Version control:** Git
- **Run the game:** `python main.py`
- **Generate placeholder assets:** `python src/utils/placeholder_assets.py`
- **Check all imports:** `python run_check.py`

---

## Project Structure

```
mystic_siege/
├── main.py                        # Entry point
├── settings.py                    # ALL constants live here — never hardcode elsewhere
├── requirements.txt
├── requirements-dev.txt
├── run_check.py                   # Import checker + pygame version verifier
├── CLAUDE.md                      # This file
├── src/
│   ├── game.py                    # Main loop, delegates to SceneManager
│   ├── scene_manager.py           # Scene switching (menu/game/gameover)
│   ├── game_scene.py              # Main gameplay — wires all systems together
│   ├── entities/
│   │   ├── base_entity.py         # Base pygame.sprite.Sprite with hp/damage/movement
│   │   ├── player.py              # Player — WASD movement, weapons list, passives
│   │   ├── enemy.py               # Base enemy — chase/ranged behaviors, knockback
│   │   ├── projectile.py          # Projectile — homing, pierce, lifetime
│   │   ├── xp_orb.py              # XP orb — bobbing animation, auto-collect
│   │   ├── effects.py             # DamageNumber, HitSpark, DeathExplosion, LevelUpEffect
│   │   └── enemies/
│   │       ├── skeleton.py        # hp=30, slow, slight random wander
│   │       ├── dark_goblin.py     # hp=20, fast, spawns in groups
│   │       ├── wraith.py          # hp=40, phases walls, periodic lunge
│   │       ├── plague_bat.py      # hp=15, arc movement, splits on death
│   │       ├── cursed_knight.py   # hp=80, frontal shield blocks 80% damage
│   │       └── lich_familiar.py   # hp=35, orbits player, fires slow orbs
│   ├── weapons/
│   │   ├── base_weapon.py         # BaseWeapon — cooldown, upgrade(), fire() interface
│   │   ├── arcane_bolt.py         # Homing projectiles, 1-3 bolts, pierce at L4
│   │   ├── holy_nova.py           # Expanding ring, area damage, no projectile
│   │   ├── spectral_blade.py      # Orbiting swords, continuous, per-enemy cooldown
│   │   ├── flame_whip.py          # Cone sweep, burn DOT, swing visual
│   │   ├── frost_ring.py          # Expanding freeze ring, immobilizes enemies
│   │   └── lightning_chain.py     # Chains between enemies, jagged arc visual
│   ├── systems/
│   │   ├── wave_manager.py        # Enemy spawning timeline, elite mode, warnings
│   │   ├── xp_system.py           # XP collection, leveling, orb pickup radius
│   │   ├── upgrade_system.py      # Upgrade card pool, passive/weapon choices
│   │   ├── collision.py           # All collision detection — iframes, knockback
│   │   ├── camera.py              # Lerp follow camera, world bounds clamping
│   │   └── save_system.py         # JSON meta-progression in saves/progress.json
│   ├── ui/
│   │   ├── hud.py                 # HP bar, XP bar, timer, kill count, weapon slots
│   │   ├── upgrade_menu.py        # 3-card level-up overlay, keyboard 1/2/3
│   │   ├── main_menu.py           # Title screen with falling ember particles
│   │   ├── class_select.py        # Hero card selection, shows stats + passive
│   │   ├── game_over.py           # Victory/defeat screen with run stats
│   │   ├── settings_menu.py       # Volume sliders, fullscreen toggle, reset
│   │   └── stats_menu.py          # Meta-progression stats viewer
│   └── utils/
│       ├── timer.py               # Reusable countdown/interval timer
│       ├── resource_loader.py     # Singleton asset loader with fallback placeholders
│       ├── spritesheet.py         # Spritesheet frame/animation extractor
│       ├── audio_manager.py       # Singleton audio with silent fallback
│       ├── input_manager.py       # Singleton controller input — synthetic key events + analog movement
│       └── placeholder_assets.py  # Generates colored rect PNGs and sine-wave WAVs for all assets
└── assets/
    ├── sprites/heroes|enemies|projectiles|effects|ui/
    ├── audio/sfx|music/
    └── fonts/
```

---

## Core Coding Rules — Follow These Every Time

1. **Never hardcode values.** Every number, color, speed, and threshold lives in
   `settings.py`. Reference it from there.

2. **All entities inherit `pygame.sprite.Sprite`.** Use `pygame.sprite.Group` for
   all collections. Never manage entity lists manually.

3. **Every `update()` method accepts `dt: float`** (delta time in seconds).
   Movement is always `pos += velocity * dt`. Never use frame counts for timing.

4. **One class per file.** Small utility helpers may share a file.

5. **Python 3.12.13 syntax.** Use `list[int]`, `dict[str, int]`, `tuple[int, ...]`
   — no need to import from `typing`. Use `match/case` where it improves clarity.

6. **Never use `datetime.utcnow()`.** Use `datetime.now(timezone.utc)` instead
   (utcnow was deprecated in 3.12).

7. **Output complete files when editing.** Never leave placeholder comments like
   `# rest of code here` or `# same as before`. Always write every line.

8. **Comments describe intent, not mechanics.**
   Write: `# spawn enemy when timer fires`
   Not: `# if timer > 0`

---

## Key Design Decisions

### Hero Classes (defined in settings.HERO_CLASSES)
| Hero | HP | Speed | Armor | Starting Weapon |
|---|---|---|---|---|
| Knight of the Burning Crown | 150 | 180 | 15 | SpectralBlade |
| Witch of the Hollow Marsh | 80 | 240 | 0 | ArcaneBolt |
| Wandering Friar | 110 | 210 | 5 | HolyNova |

Knight passive: 15% damage reduction, knockback immune
Witch passive: +20% spell damage, +10% crit chance
Friar passive: heal 1 HP per 10 XP orbs collected

### Weapons (all have 5 upgrade levels)
- ArcaneBolt — homing projectiles, 1→3 bolts
- HolyNova — expanding damage ring, no projectile object
- SpectralBlade — orbiting swords, continuous collision
- FlameWhip — directional cone, burn DOT
- FrostRing — expanding freeze ring, immobilizes
- LightningChain — chains to up to 6 enemies

### Enemy Spawn Timeline (wave_manager.py)
- 0s: Skeletons only
- 60s: Add Goblins
- 120s: Add Wraiths
- 300s: Add Bats
- 480s: Stone Golem (one-time mini-boss)
- 600s: Add Knights + Liches
- 900s: Elite mode (1.5x HP/damage)
- 1200s: Final assault
- 1800s: Victory

### Game Loop
```
Menu → Class Select → Game → (die or 30min) → Game Over → Menu
```
- Time stops on level-up (upgrade menu open)
- ESC pauses
- F3 toggles FPS counter
- F11 toggles fullscreen
- F12 saves screenshot

### XP Formula
```python
xp_to_next = int(BASE_XP_REQUIRED * (XP_SCALE_FACTOR ** current_level))
# BASE_XP_REQUIRED = 50, XP_SCALE_FACTOR = 1.12
```

### Collision Rules
- Player contact damage: 0.5s iframes after each hit
- Projectiles: use `enemies_hit` set to track pierce
- SpectralBlade: per-enemy 0.5s hit cooldown dict
- HolyNova/FrostRing: `damage_done` set per ring instance

---

## Scene Transition Pattern

Scenes communicate transitions via `.next_scene` and `.next_scene_kwargs`:
```python
# In a scene:
self.next_scene = "game"
self.next_scene_kwargs = {"hero": selected_class_dict}

# SceneManager checks this each frame and calls switch_to()
```
GameScene is always re-instantiated fresh on each new run.

---

## Asset Loading Pattern

Always use `ResourceLoader` — never load assets directly:
```python
from src.utils.resource_loader import ResourceLoader
rl = ResourceLoader.instance()
image = rl.load_image("assets/sprites/heroes/knight.png", scale=(32, 32))
sound = rl.load_sound("assets/audio/sfx/player_hit.wav")
```
If the file doesn't exist, `load_image` returns a magenta 32x32 placeholder so
the game always runs even without real assets.

---

## Audio Pattern

Always use `AudioManager` — never call pygame.mixer directly:
```python
from src.utils.audio_manager import AudioManager
AudioManager.instance().play_sfx(AudioManager.PLAYER_HIT)
AudioManager.instance().play_music("assets/audio/music/main_theme.ogg")
```
All audio methods fail silently if files are missing or mixer isn't initialized.

---

## Controller / Input Pattern

Always use `InputManager` for controller state — never read `pygame.joystick` directly:
```python
from src.utils.input_manager import InputManager
# Analog movement vector (deadzone applied), returns (0.0, 0.0) if no controller
ax, ay = InputManager.instance().get_movement()
```
Controller button/D-pad presses are automatically translated into synthetic
`pygame.KEYDOWN` events and posted to the pygame event queue, so all menus work
with a controller without any extra code in the UI layer.

Call `InputManager.instance().scan()` once after `pygame.init()` to register
already-connected devices. Hot-plug is handled automatically via `JOYDEVICEADDED`.

Default button mapping (Xbox / PlayStation / Switch Pro):
- Left stick / D-pad → movement + menu navigation (with key-repeat on stick)
- A / Cross (btn 0) → confirm (K_RETURN)
- B / Circle (btn 1), Start / Options (btn 7/9) → back / pause (K_ESCAPE)

Tune deadzone and repeat timing in `settings.py`:
`CONTROLLER_DEADZONE`, `CONTROLLER_AXIS_REPEAT_DELAY`, `CONTROLLER_AXIS_REPEAT_RATE`

---

## Placeholder vs Real Assets

Real sprites can be swapped in at any time by placing a PNG at the correct path
in `assets/sprites/`. `ResourceLoader` will automatically use it over the
placeholder. No code changes needed — just drop the file in.

Real audio can be swapped in at any time by placing a WAV file at the correct
path in `assets/audio/sfx/`. `AudioManager` loads all SFX at `GameScene` init.
No code changes needed — just drop the file in.

Run `python src/utils/placeholder_assets.py` any time to regenerate placeholder
sprites and audio for any missing asset files.

---

## Common Tasks

**Run the game:**
```
python main.py
```

**Check for import errors:**
```
python run_check.py
```

**Regenerate placeholder assets:**
```
python src/utils/placeholder_assets.py
```

**Add a new enemy:**
1. Create `src/entities/enemies/newenemy.py` inheriting from `Enemy`
2. Add spawn data dict to `wave_manager.py`
3. Add to wave timeline in `wave_manager._check_timeline()`

**Add a new weapon:**
1. Create `src/weapons/newweapon.py` inheriting from `BaseWeapon`
2. Add class name string to `WEAPON_CLASSES` in `upgrade_system.py`

**Tune difficulty:**
- Edit wave timing and spawn rates in `wave_manager.py`
- Edit enemy stats in the DATA dicts at the top of `wave_manager.py`
- Edit hero/weapon base stats in `settings.py`

**Add a real sprite:**
- Drop PNG at the correct `assets/sprites/` path
- It loads automatically — no code changes needed

---

## What NOT to Do

- Don't import `pygame` — always import `pygame` via `pygame-ce` (same namespace,
  but the project depends on the CE fork specifically)
- Don't hardcode colors, speeds, or sizes anywhere outside `settings.py`
- Don't create new sprite groups — reuse the ones created in `game_scene.py`
- Don't call `pygame.mixer` directly — use `AudioManager`
- Don't load images directly — use `ResourceLoader`
- Don't add unrequested features when fixing a bug — fix only what's broken
- Don't use `List`, `Dict`, `Tuple` from `typing` — use lowercase built-in syntax

---

## Current Development Status

Track progress here as phases are completed:

- [x] Phase 1 — Project scaffold (settings, main, utils)
- [x] Phase 2 — Core entities (player, enemy, projectile, xp orb)
- [x] Phase 3 — Weapons (all 6)
- [x] Phase 4 — Systems (waves, xp, upgrades, camera, collision)
- [x] Phase 5 — UI (hud, menus, upgrade cards)
- [x] Phase 6 — Integration (game scene, scene wiring, run_check)
- [x] Phase 7 — Audio & placeholder assets
- [x] Phase 8 — Additional enemies & effects
- [x] Phase 9 — Polish & meta (save system, settings menu)

Update the checkboxes as you complete each phase.
