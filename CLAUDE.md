# Mystic Siege — Project Context

## What This Project Is

Mystic Siege is a top-down medieval fantasy survivor game built in Python 3.12.13
with pygame-ce. Style: Vampire Survivors / Brotato. Players choose a hero, survive
escalating waves of enemies, collect XP orbs, level up, and pick upgrades — all in
15–30 minute sessions.

Two developers, AI-assisted workflow, small scope first.

**Current state:** the existing playable loop is single-player.
**Planned direction:** local multiplayer may be added later, but only through a phased,
low-regression migration that preserves the current single-player experience.

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
│   ├── scene_manager.py           # Scene switching (menu/game/gameover)
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
│   │   ├── base_weapon.py         # BaseWeapon — cooldown, upgrade(), fire() interface
│   │   ├── arcane_bolt.py         # Homing projectiles, 1-3 bolts, pierce at L4
│   │   ├── holy_nova.py           # Expanding ring, area damage, no projectile
│   │   ├── spectral_blade.py      # Orbiting swords, continuous collision
│   │   ├── flame_whip.py          # Cone sweep, burn DOT, swing visual
│   │   ├── frost_ring.py          # Expanding freeze ring, immobilizes enemies
│   │   └── lightning_chain.py     # Chains between enemies, jagged arc visual
│   ├── systems/
│   │   ├── wave_manager.py        # Enemy spawning timeline, elite mode, multiplayer spawn anchoring
│   │   ├── xp_system.py           # XP collection, leveling, orb pickup radius
│   │   ├── upgrade_system.py      # Upgrade card pool, passive/weapon choices
│   │   ├── collision.py           # All collision detection — iframes, knockback, multiplayer player loops
│   │   ├── camera.py              # Single-target follow + multi-target zoomed camera
│   │   └── save_system.py         # JSON meta-progression in saves/progress.json
│   ├── ui/
│   │   ├── hud.py                 # HP bar, XP bar, timer, kill count, weapon slots
│   │   ├── upgrade_menu.py        # 3-card level-up overlay, keyboard 1/2/3
│   │   ├── main_menu.py           # Title screen with falling ember particles
│   │   ├── class_select.py        # Hero card selection, shows stats + passive
│   │   ├── game_over.py           # Victory/defeat screen with run stats
│   │   ├── settings_menu.py       # Volume sliders, show FPS toggle, reset
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

Knight passive: 15% damage reduction, knockback immune  
Wizard passive: +20% spell damage, +10% crit chance  
Friar passive: heal 0.1 HP per XP point gained (= `FRIAR_HEAL_PER_XP` in `settings.py`)

### Weapons (all have 5 upgrade levels)

- ArcaneBolt — homing projectiles, 1→3 bolts
- HolyNova — expanding damage ring, no projectile object
- SpectralBlade — orbiting swords, continuous collision
- FlameWhip — directional cone, burn DOT
- FrostRing — expanding freeze ring, immobilizes
- LightningChain — chains to up to 6 enemies

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

Current single-player runtime:

```text
Menu → Class Select → Game → (die or 30 min) → Game Over → Menu
```

Planned multiplayer-capable flow:

```text
Menu → Lobby → Class Select (queued per joined slot) → Game → Game Over → Menu
```

- Time stops on level-up (upgrade menu open)
- ESC pauses
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
# Current single-player example:
self.next_scene = "game"
self.next_scene_kwargs = {"hero": selected_class_dict}

# Planned multiplayer example:
self.next_scene = "class_select"
self.next_scene_kwargs = {"slots": filled_slots}

# Current transitional GameScene handoff:
# preferred multiplayer-capable path
self.next_scene = "playing"
self.next_scene_kwargs = {"slots": resolved_slots}

# temporary 1P migration shim still accepted by GameScene
self.next_scene = "playing"
self.next_scene_kwargs = {"hero": selected_class_dict}

# SceneManager checks this each frame and calls switch_to()
```

GameScene is always re-instantiated fresh on each new run.

Current migration note: `GameScene` now accepts `slots: list[PlayerSlot]` as the
primary constructor shape and keeps a temporary `hero` kwarg shim for the legacy
single-slot handoff until the lobby/class-select path always emits concrete slots.

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
for owned multiplayer menus because the synthetic events do not preserve joystick
identity.

Call `InputManager.instance().scan()` once after `pygame.init()` to register
already-connected devices. Hot-plug is handled automatically via `JOYDEVICEADDED`.

Default button mapping (Xbox / PlayStation / Switch Pro):

- Left stick / D-pad → movement + menu navigation (with key-repeat on stick)
- A / Cross (btn 0) → confirm (`K_RETURN`)
- B / Circle (btn 1), Start / Options (btn 7/9) → back / pause (`K_ESCAPE`)

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
sprites and audio for any missing asset files.

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
2. Add class name string to `WEAPON_CLASSES` in `upgrade_system.py`

**Add a new hero class:**

1. Add a new dict entry to `HERO_CLASSES` in `settings.py` with `name`, `hp`, `speed`,
   `armor`, `starting_weapon`, and `passive_description`
2. Update `class_select.py` if layout logic assumes a fixed hero count
3. Drop the hero sprite sheet at `assets/sprites/heroes/<name>.png`

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
   Current 1P: Menu → Class Select → Game → Level Up → Death/Game Over
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
   or removing old fields immediately.

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
- Controller disconnects should fail safely, not crash
- HUD and camera changes must remain readable in 1P
- Save/progression behavior must remain sane if a multiplayer run is introduced later
- Pause/menu ownership should be explicit, not accidental
- **Revive/downed depends on `Player.take_damage()` intercepting lethal damage before `BaseEntity.kill()` runs.**
  `BaseEntity.take_damage()` calls `self.kill()` immediately when HP hits 0. The current
  `Player.take_damage()` override now sets `is_downed = True` for slot-backed players instead,
  keeping the sprite in its groups so Phase 13 revive flow can operate. Treat this override as a
  requirement whenever player death logic is touched.
- **InputManager synthetic events carry no joystick identity (hidden menu blocker).** `_post_key()` /
  `_post_keyup()` emit plain `KEYDOWN`/`KEYUP` events with no `joystick_id` in the payload. Menu code
  cannot tell which controller fired `K_RETURN` or `K_ESCAPE`. Owned multiplayer menus (ClassSelect
  slot-queue, UpgradeMenu) require either (a) a custom event payload that preserves device metadata,
  or (b) bypassing synthetic events for owned menus and polling the assigned device directly.
- **SceneManager caches ClassSelect — slot-queue routing requires a fresh instance per pass.**
  The current `SceneManager` instantiates `STATE_CLASS_SELECT` once and reuses it. A slot-queue flow
  (ClassSelect visited N times, once per player) will silently malfunction until `STATE_CLASS_SELECT`
  is in the always-create-fresh set. Address this in Phase 11 before the queue routing is wired.

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
- [x] Phase 3 — Weapons (all 6)
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
- [ ] Phase 11a — Hero-selection slot queue (V2 Phase 3; partial: duplicate prevention and active-slot input routing are implemented, but the final 1P handoff still uses `hero` instead of always emitting `slots`)
- [x] Phase 12 — Multiplayer GameScene/system integration (V2 Phase 4: GameScene now accepts `slots`, spawns player collections from `PlayerSlot.index`, maintains per-player XP systems, and queues upgrades; legacy `hero` constructor support remains as a temporary compatibility shim)
- [ ] Phase 13 — World systems, HUD, revive, and camera polish (V2 Phases 5–7; partial: Phase 5 world systems are implemented, including multi-target camera zoom, player-list WaveManager/enemy targeting, multiplayer collision loops, and attacker-based kill credit. Phase 6 revive logic is now implemented in `GameScene` with downed-state recovery and revive-triggered defeat checks, while HUD layout scaling and revive feedback/polish remain open)
- [ ] Phase 14 — Integration testing, cleanup, and regression hardening (V2 Phase 8)

Update the checkboxes as phases are completed.
