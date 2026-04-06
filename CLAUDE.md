# Mystic Siege — Project Context

## What This Project Is

Mystic Siege is a top-down medieval fantasy survivor game built in Python 3.12.13
with pygame-ce. Style: Vampire Survivors / Brotato. Players choose a hero, survive
escalating waves of enemies, collect XP orbs, level up, and pick upgrades — all in
15–30 minute sessions.

Two developers, AI-assisted workflow, small scope first.

**Current state:** the single-player baseline is playable, and the local multiplayer
migration is partially implemented. New runs currently flow through a lobby and queued
hero select, and the repo now includes slot-based lobby join/leave, duplicate-locked
hero select, multiplayer `GameScene` plumbing, multi-player HUD/camera support,
downed/revive runtime support, reconnect/reclaim handling, and controller-binding
settings. The main remaining gap is runtime verification and hardening, not missing
foundational architecture.
**Planned direction:** finish the local co-op migration through phased, low-regression
changes that continue to preserve the current single-player experience.

---

## Tech Stack

- **Language:** Python 3.12.13
- **Framework:** pygame-ce (NOT standard pygame — the project depends on the CE fork)
- **Dependencies:** pygame-ce>=2.5.0, pytmx>=3.32, numpy>=1.26
- **Version control:** Git
- **Run the game:** `python main.py`
- **Generate placeholder assets:** `python src/utils/placeholder_assets.py`
- **Check all imports:** `python run_check.py`

---

## Project Structure

```text
mystic_siege/
├── main.py                        # Entry point
├── settings.py                    # ALL constants live here — never hardcode elsewhere
├── requirements.txt
├── requirements-dev.txt
├── run_check.py                   # Import checker + pygame version verifier
├── CLAUDE.md                      # This file
├── src/
│   ├── game.py                    # Main loop, delegates to SceneManager
│   ├── scene_manager.py           # Scene switching (menu/lobby/class select/game/gameover)
│   ├── game_scene.py              # Main gameplay — wires all systems together
│   ├── core/                          # (created in Phase 10) Plain data types, no pygame dependency
│   │   └── player_slot.py         # PlayerSlot dataclass — slot index, input_config, hero_data, color
│   ├── entities/
│   │   ├── base_entity.py         # Base pygame.sprite.Sprite with hp/damage/movement
│   │   ├── player.py              # Player — WASD movement, weapons list, passives
│   │   ├── enemy.py               # Base enemy — chase/ranged behaviors, knockback
│   │   ├── projectile.py          # Projectile — homing, pierce, lifetime
│   │   ├── xp_orb.py              # XP orb — bobbing animation, auto-collect
│   │   ├── effects.py             # DamageNumber, HitSpark, DeathExplosion, LevelUpEffect
│   │   └── enemies/
│   │       ├── skeleton.py        # hp=30, slow, slight random wander; uses skeleton.png 4-dir sheet
│   │       ├── dark_goblin.py     # hp=20, fast, spawns in groups; uses goblin.png 4-dir sheet
│   │       ├── wraith.py          # hp=40, phases walls, periodic lunge; uses wraith.png 4-dir sheet
│   │       ├── plague_bat.py      # hp=15, arc movement, splits on death; uses bat.png 4-dir sheet
│   │       ├── cursed_knight.py   # hp=80, frontal shield blocks 80% damage; uses knight.png 4-dir sheet
│   │       ├── lich_familiar.py   # hp=35, orbits player, fires slow orbs; uses lich.png 4-dir sheet
│   │       └── stone_golem.py     # hp=500, mini-boss, very slow; uses golem.png 4-dir sheet
│   ├── weapons/
│   │   ├── __init__.py           # Re-exports weapon registry + create_weapon helper
│   │   ├── base_weapon.py         # BaseWeapon — cooldown, upgrade(), fire() interface
│   │   ├── factory.py             # Shared weapon registry + constructor helper used by gameplay systems
│   │   ├── arcane_bolt.py         # Homing projectiles, 1-3 bolts, pierce at L4
│   │   ├── holy_nova.py           # Expanding ring, area damage, no projectile
│   │   ├── spectral_blade.py      # Orbiting swords, continuous collision
│   │   ├── flame_blast.py         # Cone sweep, burn DOT, swing visual
│   │   ├── frost_ring.py          # Expanding freeze ring, immobilizes enemies
│   │   ├── lightning_chain.py     # Chains between enemies, jagged arc visual
│   │   └── longbow.py             # Physical arrow shots, straight-line ranged damage
│   ├── systems/
│   │   ├── wave_manager.py        # Enemy spawning timeline, elite mode, multiplayer spawn anchoring
│   │   ├── xp_system.py           # XP collection, leveling, orb pickup radius
│   │   ├── upgrade_system.py      # Upgrade card pool, passive/weapon choices
│   │   ├── collision.py           # All collision detection — iframes, knockback, multiplayer player loops
│   │   ├── camera.py              # Single-target follow + multi-target zoomed camera
│   │   └── save_system.py         # JSON meta-progression + controller binding persistence in saves/progress.json
│   ├── ui/
│   │   ├── hud.py                 # Shared in-run HUD panels, revive indicators, threat arrows
│   │   ├── upgrade_menu.py        # 3-card level-up overlay, owned-player input routing
│   │   ├── main_menu.py           # Title screen with falling ember particles
│   │   ├── lobby_scene.py         # Slot-based join/leave lobby with keyboard/controller claims
│   │   ├── class_select.py        # Hero card selection, shows stats + passive
│   │   ├── game_over.py           # Victory/defeat screen with run stats
│   │   ├── settings_menu.py       # Volume/FPS-cap sliders (mouse + controller), FPS toggle, reset, controller binding profiles
│   │   └── stats_menu.py          # Meta-progression stats viewer
│   └── utils/
│       ├── timer.py               # Reusable countdown/interval timer
│       ├── resource_loader.py     # Singleton asset loader with fallback placeholders
│       ├── spritesheet.py         # Spritesheet frame/animation extractor
│       ├── audio_manager.py       # Singleton audio with silent fallback
│       ├── input_manager.py       # Singleton controller input — owned routing, synthetic menu keys, per-profile bindings
│       └── placeholder_assets.py  # Generates stylized placeholder sprites/icons and sine-wave WAVs for missing assets
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
   (`utcnow` was deprecated in 3.12).

7. **No placeholder comments.** When editing existing files, apply targeted diffs —
   never leave stubs like `# rest of code here` or `# same as before`. When creating
   a new file from scratch, write every line completely.

8. **Comments describe intent, not mechanics.**
   Write: `# spawn enemy when timer fires`
   Not: `# if timer > 0`

---

## Key Design Decisions

### Hero Classes (defined in `settings.HERO_CLASSES`)

| Hero | HP | Speed | Armor | Starting Weapon |
|---|---:|---:|---:|---|
| Knight | 150 | 180 | 15 | SpectralBlade |
| Wizard | 80 | 240 | 0 | ArcaneBolt |
| Friar | 110 | 210 | 5 | HolyNova |
| Ranger | 95 | 225 | 3 | Longbow |

Knight passive: 15% damage reduction, knockback immune  
Wizard passive: +20% spell damage, +10% crit chance  
Friar passive: heal 0.1 HP per XP point gained (= `FRIAR_HEAL_PER_XP` in `settings.py`)
Ranger passive: +10% crit chance, arrows pierce +1 enemy

Current hero architecture rules:

- Hero definitions stay in `settings.HERO_CLASSES` as plain dicts used directly by
  `ClassSelect`, `GameScene`, and `Player`.
- Base stats, sprite path, starting weapon, passive text, and passive gameplay config
  should all be authored in the hero record first.
- Hero passive behavior is now declarative via each hero dict's `passives` mapping.
  Current passive keys include `damage_taken_multiplier`, `knockback_immune`,
  `crit_chance_bonus`, `spell_damage_bonus_pct`, `projectile_pierce_bonus`, and
  `heal_per_xp`.
- Do not add new hero-name `if/elif` passive branches in gameplay systems when a
  passive can be expressed as hero config and read by `Player`, `XPSystem`, or
  collision/runtime code.

### Weapons (all have 5 upgrade levels)

- ArcaneBolt — homing projectiles, 1→3 bolts
- HolyNova — expanding damage ring, no projectile object
- SpectralBlade — orbiting swords, continuous collision
- FlameBlast (`Flame Blast`) — directional cone, burn DOT
- FrostRing — expanding freeze ring, immobilizes
- LightningChain — chains to up to 6 enemies
- Longbow — fast physical arrows, cadence/pierce/crit upgrades

The weapon roster can exceed the simultaneous carry cap. `MAX_WEAPON_SLOTS` still
limits a player to 6 equipped weapons, and `UpgradeSystem` should not offer
`new_weapon` cards once that inventory is full.

Current weapon architecture rules:

- All weapon tunables live in clearly grouped `settings.py` sections first.
- Weapon classes should read class attributes and upgrade tables from `settings.py`
  instead of hardcoding gameplay values in the class body.
- Weapon creation by string id is centralized in `src/weapons/factory.py` through
  `WEAPON_CLASS_REGISTRY` and `create_weapon()`. `GameScene` resolves each
  hero's `starting_weapon` id through that path, and `UpgradeSystem` resolves
  new-weapon rewards through the same shared constructor.
- `src/weapons/__init__.py` re-exports `WEAPON_CLASS_REGISTRY` and `create_weapon`
  so callers can import the package-level API if needed.
- Upgrade-card presentation metadata is kept in `src/systems/upgrade_system.py`
  via `WEAPON_META`, while the list of unlockable weapon ids stays in `WEAPON_CLASSES`.
- Do not add new `if/elif` weapon factory chains in `GameScene`, `UpgradeSystem`,
  or other callers. Register the weapon once in `WEAPON_CLASS_REGISTRY` and keep
  hero data / upgrade rewards on string ids.
- Keep weapon ids stable (`ArcaneBolt`, `HolyNova`, `SpectralBlade`, `FlameBlast`,
  `FrostRing`, `LightningChain`, `Longbow`) because hero data and upgrade choices
  reference them by string.
- Keep player-facing weapon names in metadata / weapon classes aligned with those
  internal ids. `FlameBlast` currently uses the display name `Flame Blast`.
- HUD chrome that is visually tied to weapon slots should also stay settings-driven.
  The empty weapon-slot background now uses `HUD_EMPTY_SLOT_BG_COLOR`, and the HP/XP
  bar background reuses that same constant so 1P and multiplayer HUD panels keep a
  consistent baseline treatment without duplicating color literals in `src/ui/hud.py`.
- Weapon level HUD treatment is now shared across solo and multiplayer: player
  panels use a settings-driven 4-segment border tracker that fills clockwise from
  the top as levels 2–5 are earned; any unearned segments use the same gray
  baseline as empty weapon slots.
- The shared HUD renderer in `src/ui/hud.py` should keep caching stable data in the
  hot path: panel tuple-to-`pygame.Rect` conversion, weapon-slot row geometry,
  weapon icon surfaces, and repeated text surfaces should be reused rather than
  rebuilt every frame. Offscreen downed-player revive rings should be culled, while
  teammate threat arrows remain available as the offscreen signal.

### Enemy Spawn Timeline (`wave_manager.py`)

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

Current runtime:

```text
Menu → Lobby → Class Select → Game → (die or 30 min) → Game Over → Menu
```

Current multiplayer-capable flow:

```text
Menu → Lobby → Class Select (queued per joined slot) → Game → Game Over → Menu
```

- The solo baseline is preserved inside `GameScene`; a single joined slot still uses
  the single-player runtime path for movement and death behavior, but the in-run HUD
  now shares the same slot-panel renderer and weapon-slot treatment as multiplayer.
- The practical current party cap is 4 unique players because there are 4 heroes and
  duplicate hero picks are still blocked.
- Save/progression is still machine-local and aggregate; multiplayer runs update the
  shared `saves/progress.json`, not per-person profiles.
- XP orb collection is a shared pool. If two players are equally close, the lower
  slot index wins the tie.
- Owned multiplayer menu flows now enforce device identity:
  - lobby claims devices by slot and rejects duplicate controller claims
  - class select and upgrade menus route controller input by owned joystick instance
  - pause only responds to joined keyboard schemes and claimed controllers
  - disconnected claimed controllers are pruned in the lobby, and in-run controller claims now recover by safe remap or explicit reclaim instead of cross-controlling
  - while a claimed in-run controller is unresolved, gameplay stays paused until the affected slot is reclaimed
- Controller bindings are configurable from Settings:
  - `Global Default` is the fallback mapping for unknown / untouched controllers
  - controller profiles can override `Confirm`, `Back`, and `Pause / Start`
  - player-facing on-screen help should use semantic action names (`Confirm`,
    `Back`, `Start`) rather than raw button numbers such as `Btn 7`
  - profile bindings are saved in `saves/progress.json`
  - global menus consume synthetic controller key events generated directly from
    `JOYBUTTONDOWN` / `JOYBUTTONUP`; keep those mappings in sync with the
    controller binding settings so confirm/back/start work reliably in menus
  - the main Settings screen treats its sliders as global-menu controls:
    left/right adjusts the selected slider, and percentage/FPS display should
    round to the intended stepped value rather than truncating floating-point drift
  - if a menu or overlay is opened from raw `JOYBUTTONDOWN` while synthetic
    controller key events are also enabled, discard any queued synthetic confirm /
    back key events at that transition point so the opening button press does not
    immediately activate the first control in the new UI

- Time stops on level-up (upgrade menu open)
- ESC pauses, and controller `Back` unpauses from the pause menu like `ESC`
- F3 toggles FPS counter
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
- `enemy.take_damage(amount, hit_direction=None, attacker=None)` — all weapons and projectiles pass
  `hit_direction` (Vector2 from enemy back toward the attacker) so CursedKnight's
  frontal shield mechanic correctly reduces damage by 80% on hits from the front,
  and `attacker` enables correct kill credit attribution in multiplayer

---

## Scene Transition Pattern

Scenes communicate transitions via `.next_scene` and `.next_scene_kwargs`:

```python
# Lobby handoff:
self.next_scene = "class_select"
self.next_scene_kwargs = {"slots": filled_slots}

# ClassSelect -> GameScene handoff:
self.next_scene = "playing"
self.next_scene_kwargs = {"slots": resolved_slots}

# GameOver / replay path:
self.next_scene = "lobby"

# SceneManager checks this each frame and calls switch_to()
```

GameScene is always re-instantiated fresh on each new run and now accepts
`slots: list[PlayerSlot]` as its only constructor shape.

**Important:** `next_scene_kwargs` must stay lightweight and serialization-friendly.
Do not put live sprite references, `pygame.Surface` objects, open file handles,
or other runtime-only objects in scene kwargs. Plain dataclasses such as
`PlayerSlot` are acceptable if their fields stay JSON-safe.

---

## Asset Loading Pattern

Always use `ResourceLoader` — never load assets directly:

```python
from src.utils.resource_loader import ResourceLoader
rl = ResourceLoader.instance()
image = rl.load_image("assets/sprites/heroes/knight.png", scale=(32, 32))
sound = rl.load_sound("assets/audio/sfx/player_hit.wav")
```

If the file doesn't exist, `load_image` returns a magenta 32×32 placeholder so
the game always runs even without real assets.

---

## Audio Pattern

Always use `AudioManager` — never call `pygame.mixer` directly:

```python
from src.utils.audio_manager import AudioManager
AudioManager.instance().play_sfx(AudioManager.PLAYER_HIT)

---

## Controller Binding Notes

- `InputManager` is the single source of truth for controller button bindings.
- Runtime resolution order is:
  - controller-specific profile
  - global controller fallback
  - code defaults in `settings.py`
- Use `button_matches(..., joystick_id=...)`, `describe_binding(..., joystick_id=...)`,
  or `get_confirm_for_joystick()` instead of hardcoding controller button indices in scenes.
- Synthetic controller `KEYDOWN` events are still acceptable for global menus, but owned
  multiplayer menus must still handle ownership deliberately even though synthetic events
  now carry source metadata; preserving device identity in menu logic or polling the
  owning joystick directly are both valid approaches.
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
`pygame.KEYDOWN` events and posted to the pygame event queue, so global menus work
with a controller without any extra code in the UI layer. This is not sufficient
for owned multiplayer menus on its own: synthetic events now include source
metadata, but menu code still has to reject or route those events explicitly to
preserve ownership semantics.

Current migration note: owned multiplayer menus now bypass that limitation on a
case-by-case basis. `ClassSelect` and `UpgradeMenu` filter keyboard input to the
active slot's bound keys and use per-joystick polling / `JOYBUTTONDOWN` for the
active controller instead of trusting global synthetic confirm events. The current
keyboard ownership bindings are:

- `WASD`: `A/D` navigate, `Space` confirm, `Left Shift` back
- `Arrows`: `Left/Right` navigate, `Enter` confirm, `Right Shift` back
- Solo keyboard-owned menus still accept `Enter` as a compatibility confirm path
  for the single joined slot
- `ClassSelect` also accepts mouse hero selection / Confirm / Back clicks and `ESC`
  as UI-level overrides in both solo and multiplayer, while keeping owned keyboard
  and controller routing intact for normal slot input

Call `InputManager.instance().scan()` once after `pygame.init()` to register
already-connected devices. Hot-plug is handled automatically via `JOYDEVICEADDED`.

Default button mapping (Xbox / PlayStation / Switch Pro):

- Left stick / D-pad → movement + menu navigation (with key-repeat on stick)
- A / Cross (btn 0) → confirm (`K_RETURN`)
- B / Circle (btn 1) → back (`K_ESCAPE`) and unpause from the in-game pause menu
- Pause / Start (btn 7 by default) → pause toggle (`K_ESCAPE` in global menus)

Tune deadzone and repeat timing in `settings.py`:
`CONTROLLER_DEADZONE`, `CONTROLLER_AXIS_REPEAT_DELAY`, `CONTROLLER_AXIS_REPEAT_RATE`

---

## Placeholder vs Real Assets

Real sprites can be swapped in at any time by placing a PNG at the correct path
in `assets/sprites/`. `ResourceLoader` will automatically use it over the
placeholder. No code changes needed — just drop the file in.

Real audio can be swapped in at any time by placing files at the correct paths.
SFX use WAV format (`assets/audio/sfx/`); music tracks use OGG format
(`assets/audio/music/`). `AudioManager` loads all SFX at `GameScene` init.
No code changes needed — just drop the file in.

Run `python src/utils/placeholder_assets.py` any time to regenerate placeholder
sprites/icons and audio for any missing asset files. Audio placeholder generation
uses the normal project `numpy` dependency; if it is unavailable, the script fails
explicitly instead of silently skipping audio output.

---

## Common Tasks

**Run the game:**

```bash
python main.py
```

**Check for import errors:**

```bash
python run_check.py
```

**Regenerate placeholder assets:**

```bash
python src/utils/placeholder_assets.py
```

**Add a new enemy:**

1. Create `src/entities/enemies/newenemy.py` inheriting from `Enemy`
2. Add spawn data dict to `wave_manager.py`
3. Add to wave timeline in `wave_manager._check_timeline()`

**Add a new weapon:**

1. Create `src/weapons/newweapon.py` inheriting from `BaseWeapon`
2. Add all weapon tunables and upgrade deltas to a dedicated section in `settings.py`
3. Follow the existing settings-driven weapon pattern: class attributes and
   `upgrade_levels` should be sourced from `settings.py`, not hardcoded in the weapon class
4. Register the weapon id and class in `src/weapons/factory.py` (`WEAPON_CLASS_REGISTRY`)
5. Reference that weapon id from hero `starting_weapon` fields or upgrade rewards instead of
   instantiating the class directly in scene/system code
6. Export it from `src/weapons/__init__.py` if package-level imports should expose it
7. Add the weapon id to `WEAPON_CLASSES` and add card metadata to `WEAPON_META` in `upgrade_system.py`
8. If the weapon pool now exceeds `MAX_WEAPON_SLOTS`, keep `UpgradeSystem`
   from offering unusable `new_weapon` cards to players with full inventories

**Add a new hero class:**

1. Add a new dict entry to `HERO_CLASSES` in `settings.py` with `name`, `hp`, `speed`,
   `armor`, `starting_weapon`, `passive_desc`, `sprite`, and a `passives` dict
   when the hero has gameplay modifiers
2. Prefer declarative passive keys in the hero record over adding hero-name checks
   in runtime code
3. Update `class_select.py` if layout logic assumes a fixed hero count
4. Drop the hero sprite sheet at `assets/sprites/heroes/<name>.png`

**Tune difficulty:**

- Edit wave timing and spawn rates in `wave_manager.py`
- Edit enemy stats in the data dicts at the top of `wave_manager.py`
- Edit hero/weapon base stats in `settings.py`

**Add a real sprite:**

- Drop PNG at the correct `assets/sprites/` path
- It loads automatically — no code changes needed

---

## Development Principles

These rules govern how changes are made to the project — they are as important as
the coding rules above.

1. **Preserve single-player behavior.** Mystic Siege is a single-player-first game.
   Never modify core systems (collision, XP, wave timing, save data, scene flow)
   in ways that break or degrade the solo experience, even when adding optional features.

2. **Do not rewrite working systems.** If a system functions correctly, patch or extend
   it — do not replace it. Rewrites invalidate tested behavior, introduce regressions,
   and waste time recovering ground already covered.

3. **Prefer phased migration.** When a system needs significant change, do it in
   stages: (a) add the new code alongside the old, (b) migrate all callers, (c) remove
   the old code. Never do a big-bang swap in a single commit.

4. **Read before editing.** Always read a file in full before modifying it.
   Never edit based on assumptions about what it contains.

5. **Verify after every non-trivial change.** Run `python run_check.py` after any edit
   that touches imports, scene flow, or adds new files. Catch errors before they compound.

6. **Keep `settings.py` the source of truth.** When adding new tunable values for a
   feature, add them to `settings.py` first, then reference them. Never hardcode
   "temporary" values directly in game code.
   This includes HUD presentation values such as shared weapon-slot / bar background
   colors when the UI is intentionally reusing the same visual treatment, and
   multiplayer weapon-level border segment settings when the HUD chrome is used as
   the upgrade tracker.

7. **Commit working states.** Make a git commit whenever the game reaches a clean,
   runnable state. Never let a multi-day stretch pass without a checkpoint.
   *(This is a reminder for developers — the coding agent should only commit when explicitly asked.)*

8. **Favor maintainability over cleverness.** Prefer explicit, readable code and
   small safe abstractions over compact but fragile logic.

9. **Be honest about verification.** Do not claim gameplay behavior works unless the
   relevant code path was actually checked. If only static/import validation was run,
   say that clearly.

---

## Multiplayer Migration Rules

These rules apply to all multiplayer-related changes.

1. **No new hard-coded P1/P2 architecture.** Do not introduce new parameters or fields such as
   `hero_p1`, `hero_p2`, `p1_config`, `p2_config`, or logic branches tied to exactly two players.

2. **Prefer collections over named players.** Multiplayer systems should pass
   `list[PlayerSlot]`. The central abstraction is **`PlayerSlot`** (defined in
   MULTIPLAYER_IMPLEMENTATION_V2.md Section 4.1). All systems pass `list[PlayerSlot]`.
   Do not invent alternatives.

3. **Keep 1P as the baseline verification path.** Every multiplayer refactor must preserve
   the current single-player gameplay loop before expanding to 2P+.

4. **Scene transition data must stay lightweight and serialization-friendly.** See the Scene
   Transition Pattern section — the same constraint applies to multiplayer flows.

5. **Input must stay decoupled from player identity.** Do not assume a player is defined by
   keyboard, controller, or slot alone. Input device, slot, and hero choice are separate concepts.

6. **Do not add networking systems yet.** No `NetworkManager`, rollback, peer discovery,
   or netcode stubs unless explicitly requested.

7. **Be ruthless about removing single-player-only assumptions** from systems that are being
   generalized, but do not break the actual single-player runtime behavior while doing so.

> For concrete data structures (`PlayerSlot`, `input_config`), per-phase file lists,
> HUD layout, camera, revive mechanics, and the full verification checklist, see
> **MULTIPLAYER_IMPLEMENTATION_V2.md** — it is the authoritative design document for
> Phases 10–14. CLAUDE.md carries the principles; V2 carries the implementation detail.

---

## Verification Protocol

1. **Always run `python run_check.py` after non-trivial changes.**

2. **If gameplay code changes, also describe the exact manual test path** needed to verify
   the game still works in 1P:

   ```text
   Current 1P: Menu → Lobby → Class Select → Game → Level Up → Death/Game Over
   Planned multiplayer-capable path: Menu → Lobby → Class Select (queued) → Game → Level Up → Death/Game Over
   ```

3. **For multiplayer-related changes, verification order is mandatory:**
   - First prove 1P still works
   - Then verify 2P behavior
   - Only then discuss 3P/4P impact

4. **Do not claim a feature works unless the relevant code path was actually checked.**
   If runtime verification was not performed, say so explicitly.

5. **When changing scene flow, input handling, HUD, save data, camera behavior, or pause rules,**
   always include a short regression-risk note in the response.

6. **For large changes, include both:**
   - what was actually verified
   - what still remains unverified

---

## Save / Progression Safety

1. **Do not break existing save files casually.** When changing `save_system.py` or the shape
   of saved data, preserve backward compatibility where practical.

2. **Prefer additive save changes.** Add new fields with safe defaults rather than renaming
   or removing old fields immediately. The current `SaveSystem.load()` behavior deep-merges
   loaded JSON onto `DEFAULT_SAVE`, including nested `settings`, so older saves missing
   newer fields continue to load.

3. **If a save-data migration is required, state it explicitly** and keep the migration logic simple.

4. **Do not couple run-local multiplayer state to permanent meta-progression** unless explicitly requested.

5. **Never silently reset player progress** as a side effect of a feature change.

---

## Performance Rules for Hot Paths

1. **Treat `update()` and `draw()` as hot paths.** Avoid unnecessary allocations, repeated lookups,
   and debug prints inside per-frame loops.

2. **Prefer squared-distance comparisons** when exact distance is not required.

3. **Do not add expensive work to every entity every frame** if the same result can be cached,
   throttled, or computed at a higher level.

4. **Do not add logging spam inside gameplay loops.** If temporary debug output is needed,
   gate it behind a debug flag in `settings.py`.

5. **Be careful with camera, collision, and HUD changes.** These are likely to become more
   expensive first as multiplayer is added.

6. **Prefer one-pass resolution for shared gameplay systems.** If a mechanic evaluates the same
   shared world state for multiple players each frame (for example XP orbs, shared target queries,
   or other pickup ownership decisions), prefer a single deterministic pass at the system or scene
   level over repeated nested per-player scans.

7. **Cache stable UI render results and prefer cheaper transforms in gameplay rendering.** Reuse
   repeated HUD text surfaces where practical, and avoid expensive per-frame scaling/filtering in
   the world draw path unless the visual quality difference is important enough to justify the cost.

8. **Cull and reuse before rewriting the render path.** In gameplay rendering, first eliminate
   offscreen sprite/effect work and reuse cached world/UI surfaces before considering larger camera
   or pipeline rewrites. Full-frame zoom scaling is a known cost center, so changes there should be
   driven by real profiling rather than speculative refactors.

---

## Temporary Debug Code

1. **Temporary debug helpers are allowed only if clearly marked and easy to remove.**

2. **Prefer debug flags in `settings.py`** over one-off hardcoded debug behavior.

3. **Do not leave stray `print()` debugging in finished gameplay code.**

4. **When adding a temporary debug aid, mention whether it should remain or be removed**
   before the next clean commit.

---

## Determinism-Friendly Rules

1. **Avoid introducing unnecessary non-determinism** in gameplay systems.

2. **When randomness matters to gameplay outcomes, prefer centralized or seedable RNG**
   over scattered ad hoc random calls.

3. **Keep gameplay state mutations inside the normal update flow** rather than hiding them
   in UI code, loading code, or rendering code.

4. **Do not future-proof for networking with large speculative systems.**
   Small deterministic-friendly choices are good; dead framework code is not.

---

## Agent-Specific Response Notes

The project rules above are model-agnostic. The guidance below is agent-specific
workflow preference, not game architecture.

For non-trivial tasks, prefer this response order:

1. **Plan** — brief summary of intended change
2. **Files** — exact files to inspect or modify
3. **Risks** — likely regression points
4. **Implementation** — make the requested change only
5. **Verification** — commands run and what was or was not actually verified
6. **Next step** — the single best follow-up action, if relevant

Do not bundle multiple major refactors into one pass unless explicitly requested.

For audit/planning tasks, prefer this output order:

1. Executive summary
2. File-by-file findings
3. Risks
4. Recommended implementation order
5. Verification strategy

---

## Multiplayer Edge Cases to Remember

- 1P must still work through the multiplayer-capable flow
- Duplicate hero picks must be blocked cleanly
- Device claims must be unique
- Upgrade menus must not allow input bleed from non-active players
- Controller disconnects should fail safely, not crash, and should pause gameplay until players are ready; reconnects may auto-resume only on a unique strong match, otherwise the slot must be explicitly reclaimed
- HUD and camera changes must remain readable in 1P
- Save/progression behavior must remain sane if a multiplayer run is introduced later
- Pause/menu ownership should be explicit, not accidental
- **Revive/downed depends on `Player.take_damage()` intercepting lethal damage before `BaseEntity.kill()` runs.**
  `BaseEntity.take_damage()` calls `self.kill()` immediately when HP hits 0. The current
  `Player.take_damage()` override now branches by runtime mode: multiplayer players use
  the downed/revive path, while solo players enter the legacy dying/fade flow without
  delegating lethal damage to `BaseEntity.take_damage()`. Treat this override as a
  requirement whenever player death logic is touched.
- **InputManager synthetic events now carry source metadata, but owned-menu filtering is still
  required.** `_post_key()` / `_post_keyup()` include `synthetic_controller_event` and
  `source_instance_id` in the payload, but menu code must still reject or explicitly route those
  events to preserve ownership semantics. `ClassSelect` and `UpgradeMenu` currently protect their
  owned flows by filtering keyboard paths and using per-joystick polling / `JOYBUTTONDOWN` for the
  active controller instead of trusting global synthetic confirm events.
- **SceneManager caches ClassSelect — slot-queue routing requires a fresh instance per pass.**
  `STATE_CLASS_SELECT` is now in the always-create-fresh set, which is required for the slot-queue flow
  (ClassSelect visited N times, once per player). Keep it that way unless the scene is redesigned.

---

## What NOT to Do

- Don't import standard `pygame` if a change would break the pygame-ce requirement
- Don't hardcode colors, speeds, or sizes anywhere outside `settings.py`
- Don't create new sprite groups — reuse the ones created in `game_scene.py`
- Don't call `pygame.mixer` directly — use `AudioManager`
- Don't load images directly — use `ResourceLoader`
- Don't add unrequested features when fixing a bug — fix only what's broken
- Don't use `List`, `Dict`, `Tuple` from `typing` — use lowercase built-in syntax
- Don't restructure the scene graph or game loop unless explicitly asked — it touches everything
- Don't add `settings.py` constants speculatively — only add a constant when code actually needs it
- Don't silently change gameplay feel (speeds, damage, timing) while fixing unrelated bugs — those are separate PRs
- Don't add new hard-coded P1/P2 code while working on multiplayer migration
- Don't introduce networking architecture unless explicitly requested
- Don't leave temporary debug prints or cheat toggles in finished code
- Don't claim manual testing happened unless it actually happened
- Don't change save-data shape casually or without noting compatibility impact
- Don't implement `PlayerSlot` or `input_config` differently from the shape defined in
  MULTIPLAYER_IMPLEMENTATION_V2.md Section 4.1 — consistency across phases is critical

---

## Current Development Status

Track progress here as phases are completed:

- [x] Phase 1 — Project scaffold (settings, main, utils)
- [x] Phase 2 — Core entities (player, enemy, projectile, xp orb)
- [x] Phase 3 — Weapons (all 7)
- [x] Phase 4 — Systems (waves, xp, upgrades, camera, collision)
- [x] Phase 5 — UI (hud, menus, upgrade cards)
- [x] Phase 6 — Integration (game scene, scene wiring, run_check)
- [x] Phase 7 — Audio & placeholder assets
- [x] Phase 8 — Additional enemies & effects
- [x] Phase 9 — Polish & meta (save system, settings menu)

### Planned Multiplayer Phases
*(See MULTIPLAYER_IMPLEMENTATION_V2.md for per-phase file lists, pseudocode, and verification steps)*

- [x] Phase 10 — Multiplayer foundation (V2 Phase 1: PlayerSlot + input abstraction)
- [x] Phase 11 — Lobby scene (V2 Phase 2: LobbyScene + SceneManager wiring)
- [x] Phase 11a — Hero-selection slot queue (V2 Phase 3: duplicate prevention and active-slot input routing are implemented, and ClassSelect now always emits `slots` for gameplay handoff)
- [x] Phase 12 — Multiplayer GameScene/system integration (V2 Phase 4: GameScene accepts `slots`, spawns player collections from `PlayerSlot.index`, maintains per-player XP systems, and queues upgrades)
- [ ] Phase 13 — World systems, HUD, revive, and camera polish (mostly implemented; still open for runtime verification, spacing/readability tuning, and any revive/HUD cleanup surfaced by live testing)
- [ ] Phase 14 — Integration testing, cleanup, and regression hardening (partially implemented; still open because the readiness gate has not been cleared by 1P/2P/3P runtime verification)

### Current Multiplayer Status Snapshot

- Implemented in code:
  - lobby-based slot join/leave
  - queued hero select with duplicate lockout
  - multiplayer `GameScene`/HUD/camera plumbing
  - off-screen teammate HUD arrows, including live teammates and downed players
  - owned input handling for multiplayer-sensitive menus
  - downed/revive support
  - controller disconnect/reclaim support
  - aggregate party game-over results
- Still transitional:
  - `input_config=None` compatibility branches remain in parts of the flow
- Still unverified in runtime:
  - broad 1P, 2P, and 3P readiness coverage
  - multiplayer balance/scaling
  - spawn fairness and HUD/camera readability under edge spread

Update the checkboxes as phases are completed.
