# Mystic Siege — Project Context

## What This Project Is

Top-down medieval fantasy survivor (Vampire Survivors / Brotato style) built in Python 3.12.13 with pygame-ce. Players choose a hero, survive escalating waves, collect XP, level up, and pick upgrades — 15–30 minute sessions. Two developers, AI-assisted workflow.

**Current state:** single-player baseline is playable; local co-op is complete and runtime-verified for 1P–4P. All phases (1–14) are done. Remaining work is multiplayer balance/spawn-fairness tuning, not missing architecture.

---

## Tech Stack

- **Language:** Python 3.12.13
- **Framework:** pygame-ce (NOT standard pygame)
- **Dependencies:** pygame-ce>=2.5.0, pytmx>=3.32, numpy>=1.26
- **Run the game:** `python main.py`
- **Check all imports:** `python run_check.py`
- **Generate placeholder assets:** `python src/utils/placeholder_assets.py`

---

## Project Structure

```text
mystic_siege/
├── main.py / settings.py / run_check.py
├── src/
│   ├── game.py / scene_manager.py / game_scene.py
│   ├── core/player_slot.py
│   ├── entities/
│   │   ├── base_entity.py / player.py / enemy.py / projectile.py
│   │   ├── arcane_bolt_projectile.py / xp_orb.py / pickup.py / effects.py
│   │   └── enemies/  (skeleton, dark_goblin, wraith, plague_bat, cursed_knight,
│   │                   lich_familiar, stone_golem, __init__.py)
│   ├── weapons/
│   │   ├── base_weapon.py / factory.py / __init__.py
│   │   └── (arcane_bolt, bramble_seeds, caltrops, chain_flail, flame_blast,
│   │        frost_ring, hex_orb, holy_nova, lightning_chain, longbow,
│   │        shadow_knives, spear, sword, throwing_axes)
│   ├── systems/
│   │   └── wave_manager.py / xp_system.py / upgrade_system.py /
│   │       collision.py / camera.py / pickup_system.py / save_system.py
│   ├── ui/
│   │   └── hud.py / upgrade_menu.py / main_menu.py / lobby_scene.py /
│   │       class_select.py / game_over.py / settings_menu.py / stats_menu.py
│   └── utils/
│       └── timer.py / resource_loader.py / spritesheet.py / audio_manager.py /
│           input_manager.py / placeholder_assets.py / fps_cap.py
└── assets/sprites/ audio/ fonts/
```

---

## Core Coding Rules — Follow These Every Time

1. **Never hardcode values.** Every number, color, speed, and threshold lives in `settings.py`.

2. **All entities inherit `pygame.sprite.Sprite`.** Use `pygame.sprite.Group` for all collections.

3. **Every `update()` accepts `dt: float`** (seconds). Movement: `pos += velocity * dt`. Never use frame counts.

4. **One class per file.** Small utility helpers may share a file.

5. **Python 3.12.13 syntax.** Use `list[int]`, `dict[str, int]`, `tuple[int, ...]` — no `typing` imports needed. Use `match/case` where it helps.

6. **Never use `datetime.utcnow()`.** Use `datetime.now(timezone.utc)` (deprecated in 3.12).

7. **No placeholder comments.** Apply targeted diffs — never leave stubs like `# rest of code here`. New files must be written completely.

8. **Comments describe intent, not mechanics.** Write `# spawn enemy when timer fires`, not `# if timer > 0`.

---

## Key Design Decisions

### Hero Classes (defined in `settings.HERO_CLASSES`)

| Hero | HP | Speed | Armor | Starting Weapon |
|---|---:|---:|---:|---|
| Knight | 150 | 180 | 15 | Sword |
| Wizard | 80 | 240 | 2 | ArcaneBolt |
| Friar | 110 | 210 | 5 | HolyNova |
| Ranger | 95 | 225 | 3 | Longbow |
| Barbarian | 120 | 205 | 8 | ThrowingAxes |
| Rogue | 85 | 250 | 2 | ShadowKnives |
| Warlock | 90 | 215 | 2 | HexOrb |
| Druid | 105 | 220 | 4 | BrambleSeeds |

Hero architecture rules:
- Hero definitions stay in `settings.HERO_CLASSES` as plain dicts. Base stats, sprite, starting weapon, passive text, and `passives` dict all authored there first.
- Passive behavior is declarative via the hero dict's `passives` mapping. Do not add hero-name `if/elif` branches in gameplay code when a passive can be expressed as config.
- Class-select grid supports up to 8 heroes (4+4 rows) at current `CLASS_SELECT_MAX_COLUMNS = 4` — no layout changes needed until beyond 8.

### Weapons (all have 5 upgrade levels)

Stable ids: `ArcaneBolt`, `BrambleSeeds`, `Caltrops`, `ChainFlail`, `HolyNova`, `Sword`, `FlameBlast`, `FrostRing`, `HexOrb`, `LightningChain`, `Longbow`, `ShadowKnives`, `Spear`, `ThrowingAxes`.

Display-name aliases: `BrambleSeeds` → `Bramble Seeds`, `FlameBlast` → `Flame Blast`, `HexOrb` → `Hex Orb`, `ThrowingAxes` → `Throwing Axes`.

`MAX_WEAPON_SLOTS` limits a player to 6 equipped weapons. `UpgradeSystem` must not offer `new_weapon` cards to players with full inventories.

Weapon architecture rules:
- Tunables and upgrade deltas live in `settings.py`; weapon classes read from there.
- Construction is centralized in `src/weapons/factory.py` via `WEAPON_CLASS_REGISTRY` / `create_weapon()`. No new `if/elif` chains in `GameScene` or `UpgradeSystem`.
- `src/weapons/__init__.py` re-exports the registry and helper for package-level imports.
- **Ownership split:** `settings.py` owns gameplay values · `factory.py` owns id→class resolution · `upgrade_system.py` owns player-facing card metadata (`WEAPON_META`, `WEAPON_CLASSES`). Hero `starting_weapon` and upgrade rewards reference string ids only.
- HUD weapon slots: `HUD_EMPTY_SLOT_BG_COLOR` drives empty slots and HP/XP bar backgrounds. Occupied slots show a 4-segment clockwise border tracker (levels 2–5). The HUD renderer caches stable panel/slot geometry and icon/text surfaces; cull offscreen revive rings.

### Enemies

Stable ids: `Skeleton`, `Goblin`, `Wraith`, `Bat`, `Knight`, `Lich`, `Golem`.

Enemy architecture rules:
- Tunables live in `settings.py`; enemy classes read from there.
- Construction is centralized in `src/entities/enemies/__init__.py` via `ENEMY_CLASS_REGISTRY` / `create_enemy()`. No new constructor chains in `WaveManager`.
- Shared runtime state (retarget cadence, freeze/stun, elite scaling, edge spawn retry) stays in `enemy.py` and `wave_manager.py`, not per-subclass.
- Subclass movement plugs into the base movement hook; do not recompute `self.vel` in a way the parent overwrites. `MiniBat` is plague-bat local follow-on, not a wave enemy.

### Enemy Spawn Timeline (`wave_manager.py`)

| Time | Event |
|---:|---|
| 0s | Skeletons |
| 60s | + Goblins |
| 120s | + Wraiths |
| 180s | + Bats |
| 240s | + Knights, Liches |
| 300s | Stone Golem event |
| 600s | Elite mode (1.5× HP/damage) |
| 1800s | Victory |

### Game Loop

```text
Menu → Lobby → Class Select (queued per slot) → Game → Game Over → Lobby or Menu
```

- 1P and co-op use the same scene flow. Solo still uses the unified HUD/slot-panel renderer.
- Party cap: 4 local players. Duplicate hero picks are blocked.
- Save/progression: machine-local aggregate in `saves/progress.json`.
- XP orbs: shared pool; equal-distance tie goes to lowest slot index.
- World pickups: Health potions require missing HP; timed buffs affect only the collector; `Magnet` retargets active orbs to closest eligible player.
- Unresolved controller disconnect keeps gameplay paused until the slot is reclaimed.
- Controller bindings configurable from Settings; use semantic action names (`Confirm`, `Back`, `Start`) not raw button numbers in UI text.
- Time stops on level-up. ESC / controller `Start` toggles pause. F12 takes a screenshot. Controllers can trigger screenshots through the remappable `Screenshot / Select` binding.

### XP Formula

```python
xp_to_next = int(BASE_XP_REQUIRED * (XP_SCALE_FACTOR ** current_level))
# BASE_XP_REQUIRED = 50, XP_SCALE_FACTOR = 1.12
```

### Collision Rules

- Player contact damage: 0.5s iframes per hit.
- Projectiles: `enemies_hit` set tracks pierce. Sword: one hit per enemy per swing. HolyNova/FrostRing: `damage_done` set per ring.
- Same-frame projectile pierce collisions are ordered by projectile travel direction before `on_hit()` runs. Hit effects such as Hex Orb curse, Longbow Pin Shot, Shadow Knives venom, Arcane Bolt kill explosions, and Throwing Axes ricochet stay tied to actual pierce-budget hits only.
- `enemy.take_damage(amount, hit_direction=None, attacker=None)` — all weapons pass `hit_direction` (Vector2 from enemy toward attacker) so CursedKnight's frontal shield correctly reduces damage by 80%. `attacker` enables kill-credit attribution in multiplayer.

---

## Scene Transition Pattern

Scenes communicate via `.next_scene` and `.next_scene_kwargs`. `GameScene` is always re-instantiated fresh and accepts `slots: list[PlayerSlot]` as its only constructor shape.

**Critical:** `next_scene_kwargs` must stay lightweight and serialization-friendly. No live sprite references, `pygame.Surface` objects, or open file handles. Plain dataclasses like `PlayerSlot` are acceptable if their fields stay JSON-safe.

---

## Singleton Patterns

Always use the project singletons — never touch pygame subsystems directly.

- **`ResourceLoader.instance()`** — `load_image(path, scale=...)` returns a magenta 32×32 placeholder if the file is missing; `load_sound(path)`.
- **`AudioManager.instance()`** — `play_sfx(AudioManager.CONSTANT)`, `play_music(path)`. Fails silently if files or mixer are missing.
- **`InputManager.instance()`** — `get_movement()`, `button_matches(..., joystick_id=...)`, `describe_binding(...)`, `get_confirm_for_joystick()`. Never hardcode controller button indices. Call `scan()` once after `pygame.init()`; hot-plug via `JOYDEVICEADDED`. Controller presses generate synthetic `pygame.KEYDOWN` events for global menus; owned multiplayer menus must explicitly route or reject those by device identity, or poll directly.

Keyboard ownership: WASD (Space=confirm, Left Shift=back) and Arrows (Enter=confirm, Right Shift=back). Default controller: btn 0=confirm, btn 1=back, btn 6=screenshot/select, btn 7=pause.

Assets are drop-in: place PNG at `assets/sprites/<path>` or WAV/OGG at `assets/audio/sfx|music/` and they load automatically. Run `python src/utils/placeholder_assets.py` to regenerate missing placeholders.

---

## Common Tasks

**Add a new enemy:**
1. Create `src/entities/enemies/newenemy.py` inheriting from `Enemy`
2. Add tunables to `settings.py`
3. Register in `src/entities/enemies/__init__.py`
4. Add id to the relevant wave pool values in `settings.py`
5. Update `wave_manager.py` only where timeline behavior needs the new id

**Add a new weapon:**
1. Create `src/weapons/newweapon.py` inheriting from `BaseWeapon`; source all stats and `upgrade_levels` from `settings.py`
2. Add all tunables and upgrade deltas to `settings.py`
3. Register id → class in `src/weapons/factory.py` (`WEAPON_CLASS_REGISTRY`)
4. Export from `src/weapons/__init__.py`
5. Add id to `WEAPON_CLASSES` and card metadata to `WEAPON_META` in `upgrade_system.py`
6. Reference by string id in hero `starting_weapon` and upgrade rewards — never instantiate directly in scene code

**Add a new hero class:**
1. Add entry to `HERO_CLASSES` in `settings.py` with `name`, `hp`, `speed`, `armor`, `starting_weapon`, `passive_desc`, `sprite`, and `passives` dict
2. Prefer declarative passive keys over hero-name checks in runtime code
3. Drop sprite sheet at `assets/sprites/heroes/<name>.png`

---

## Development Principles

1. **Preserve single-player behavior.** Never modify collision, XP, wave timing, save data, or scene flow in ways that break the solo experience.

2. **Do not rewrite working systems.** Patch or extend; do not replace. Use phased migration for significant changes: add alongside, migrate callers, remove old.

3. **Read before editing.** Always read a file in full before modifying it.

4. **Verify after every non-trivial change.** Run `python run_check.py` after edits touching imports, scene flow, or new files.

5. **`settings.py` is the source of truth.** Add tunables there first — including HUD colors, border segment settings, and any value that might be reused across files. Never hardcode "temporary" values in game code.

6. **Favor maintainability over cleverness.** Explicit, readable code over compact but fragile logic.

7. **Debug code rules:** Gate debug output behind a flag in `settings.py`. No stray `print()` in finished code. Mark temp helpers clearly. Prefer centralized/seedable RNG over scattered `random` calls. Keep gameplay mutations in the normal update flow, not in UI or render code.

8. **Commit only when asked.** (Reminder for developers — the coding agent commits only on explicit request.)

---

## Multiplayer Architecture Rules

1. **No new hard-coded P1/P2 architecture.** No `hero_p1`, `p2_config`, or two-player-only branches.

2. **Prefer collections over named players.** Pass `list[PlayerSlot]`. The abstraction is `PlayerSlot` (`src/core/player_slot.py`). Do not invent alternatives.

3. **1P is the baseline verification path.** Every multiplayer change must preserve the solo loop first.

4. **Scene kwargs must stay lightweight and serialization-friendly.** (Same constraint as the Scene Transition Pattern.)

5. **Input must stay decoupled from player identity.** Device, slot, and hero choice are separate concepts.

6. **Do not add networking systems.** No `NetworkManager`, rollback, or netcode stubs unless explicitly requested.

> Design rationale for `PlayerSlot`/`input_config`, HUD layout, and revive/camera intent: **docs/MULTIPLAYER_IMPLEMENTATION_V2.md** (design reference, not current-status authority).

---

## Verification Protocol

1. **Always run `python run_check.py` after non-trivial changes.**

2. **If gameplay code changes, state the manual test path:** `Menu → Lobby → Class Select → Game → Level Up → Death/Game Over`.

3. **Multiplayer change order:** prove 1P works first, then 2P, then discuss 3P/4P.

4. **Do not claim a feature works unless the code path was actually checked.** If only static validation ran, say so.

5. **For scene flow, input, HUD, save data, camera, or pause changes:** include a short regression-risk note.

6. **For large changes:** state what was verified and what remains unverified.

---

## Save / Progression Safety

1. **Do not break existing saves casually.** Preserve backward compatibility when changing `save_system.py` or save shape.

2. **Prefer additive changes.** Add fields with safe defaults. `SaveSystem.load()` deep-merges onto `DEFAULT_SAVE`, so older saves missing new fields still load.

3. **If migration is required, state it explicitly** and keep the logic simple.

4. **Do not couple run-local multiplayer state to permanent meta-progression** unless explicitly requested.

5. **Never silently reset player progress** as a side effect of a feature change.

---

## Performance Rules

1. **`update()` and `draw()` are hot paths.** No unnecessary allocations, repeated lookups, or debug prints inside per-frame loops.

2. **Prefer squared-distance comparisons** when exact distance is not required.

3. **Do not add expensive work every frame** if it can be cached, throttled, or computed at a higher level. Cache stable HUD geometry, icon surfaces, and text surfaces; cull offscreen draws.

4. **Prefer one-pass resolution for shared systems.** For XP orbs, pickup ownership, or shared target queries, use a single deterministic pass at the system/scene level over repeated per-player scans.

5. **Cull and reuse before rewriting the render path.** Eliminate offscreen work and reuse cached surfaces before considering camera/pipeline rewrites. Full-frame zoom scaling is a known cost center — profile before changing it.

---

## Agent-Specific Response Notes

For non-trivial tasks, respond in this order: **Plan → Files → Risks → Implementation → Verification → Next step**. Do not bundle multiple major refactors into one pass unless explicitly requested.

For audit/planning tasks: **Executive summary → File-by-file findings → Risks → Implementation order → Verification strategy**.

---

## Multiplayer Edge Cases to Remember

- 1P must work through the multiplayer-capable flow
- Duplicate hero picks must be blocked cleanly
- Device claims must be unique; upgrade menus must not allow input bleed from non-active players
- Controller disconnects must fail safely (not crash) and pause gameplay until the slot is reclaimed; reconnects require a unique strong match or explicit reclaim
- HUD and camera changes must remain readable in 1P
- Pause/menu ownership must be explicit, not accidental

**Critical — revive/downed:** `Player.take_damage()` must intercept lethal damage before `BaseEntity.kill()` runs. `BaseEntity.take_damage()` calls `self.kill()` immediately at HP=0. The `Player` override branches by runtime mode: multiplayer → downed/revive path; solo → legacy dying/fade flow (does not delegate to `BaseEntity.take_damage()`). Treat this override as a requirement whenever player death logic is touched.

**Critical — ClassSelect caching:** `STATE_CLASS_SELECT` must remain in the always-create-fresh set in `SceneManager`. The slot-queue flow visits ClassSelect once per player; a cached instance breaks this. Do not change unless the scene is redesigned.

---

## What NOT to Do

- Don't import standard `pygame` — the project uses pygame-ce
- Don't call `pygame.mixer` directly — use `AudioManager`
- Don't load images directly — use `ResourceLoader`
- Don't add unrequested features when fixing a bug
- Don't restructure the scene graph or game loop unless explicitly asked
- Don't add `settings.py` constants speculatively — only when code actually needs them
- Don't silently change gameplay feel (speeds, damage, timing) while fixing unrelated bugs
- Don't add new hard-coded P1/P2 code — use `list[PlayerSlot]`
- Don't introduce networking architecture unless explicitly requested
- Don't leave temporary debug prints or cheat toggles in finished code
- Don't claim manual testing happened unless it actually happened
- Don't change save-data shape without noting compatibility impact
- Don't implement `PlayerSlot` or `input_config` differently from `src/core/player_slot.py`
