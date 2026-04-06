# Multiplayer Readiness Audit — Mystic Siege

**Audit date:** 2026-04-03  
**Codebase state at audit time:** Single-player loop complete, 0% multiplayer implementation  
**Scope:** Local co-op 1–4 players, preserving the current single-player loop  
**Reference document:** MULTIPLAYER_IMPLEMENTATION_V2.md  

> Update note (2026-04-05): this document is now partially historical. The repo has
> since landed much of the slot-based multiplayer migration, including `PlayerSlot`,
> `LobbyScene`, queued `ClassSelect`, multiplayer `GameScene` plumbing, owned menu
> input work, revive/downed runtime support, reconnect/reclaim handling, and
> multi-player HUD/camera support. Read the findings below as original migration
> guidance plus a risk inventory, not as a statement of today's implementation
> percentage. For current status and remaining unverified behavior, defer to
> `README.md`, `CLAUDE.md`, and `MULTIPLAYER_READINESS_GATE_REVIEW.md`.

---

## 1. Executive Summary

The current codebase is a clean, well-structured single-player game. It was
not designed with multiplayer in mind, but the architecture is disciplined enough
that the migration is feasible without a full rewrite.

**The core problem is a single pervasive assumption: `self.player` (singular).**
It appears in 9 of the 12 key systems and at 20+ call sites in `game_scene.py`
alone. Every one of those sites must be touched before multiplayer can work.

**Nothing in the current codebase is already multiplayer-ready at the system level.**
However, several systems were designed cleanly enough that they can be extended
with minimal surgery: `XPSystem`, `UpgradeSystem`, `BaseWeapon`, all weapon classes,
`BaseEntity`, `ResourceLoader`, and `AudioManager`.

**The four highest-risk refactors, in order of impact:**
1. `game_scene.py` — central hub; touches every other system through `self.player`
2. `enemy.py` / `wave_manager.py` — single `target` hardwired at construction
3. `player.py` — reads global input directly; no per-slot dispatch
4. `camera.py` — no zoom, no multi-target follow; complete rewrite required

**The V2 guide is directionally accurate about what needs to change** but
underspecifies several concerns: lethal-damage interception for downed state, menu
input source ownership, scene recreation for queued class selection, kill credit
attribution, XP orb ownership, body-blocking between players, balance scaling with
player count, and save-data behavior in multiplayer runs.

**Recommended starting point:** Implement `PlayerSlot` + per-joystick `InputManager`
extensions first, but also document the two hidden prerequisites up front:
1. revive/downed requires intercepting lethal damage before `BaseEntity.kill()`
2. owned multiplayer menus require preserving device identity, not just posting
plain synthetic `K_RETURN` / `K_ESCAPE` events
Then migrate `GameScene.__init__` to accept `slots: list[PlayerSlot]`. Every
subsequent phase is easier once those pieces are in place.

---

## 2. What the Current Codebase Already Does Well for Multiplayer

### 2.1 Per-instance XPSystem
`xp_system.py` is stateless-per-player by design. It receives a `player` reference
at `update()` call time, not at construction. Instantiating N `XPSystem` objects and
calling each one with its corresponding player requires zero changes to `XPSystem`.
This is exactly the right design.

Note: `xp_orb.py` collection is first-come-first-served (no owner binding). This is
structurally fine for co-op shared-pool XP, but the policy should be an explicit
design choice — see Section 6.2. The XPSystem itself is clean; the orb semantics are
the item to consciously decide.

### 2.2 Weapon owner binding
All six weapon classes (`arcane_bolt.py`, `holy_nova.py`, `spectral_blade.py`,
`flame_whip.py`, `frost_ring.py`, `lightning_chain.py`) bind `self.owner = owner`
at construction. Every stat access (`self.owner.damage_multiplier`,
`self.owner.crit_chance`, `self.owner.pos`) already works correctly per-player.
Weapons are created per-player and need no changes to function in multiplayer.

### 2.3 UpgradeSystem is already player-agnostic
`upgrade_system.py` receives a player reference only at `get_random_choices(player)`
and `apply_choice(choice, player)` call time. Calling it with different player
objects for each upgrade queue slot requires no internal changes.

### 2.4 BaseEntity is mostly clean (with one override required)
`base_entity.py` has `sprite_id = id(self)` for identity tracking, correct `hp/max_hp`
fields, and a standard `take_damage()` + `heal()` interface. It works for N players
without change.

**One exception:** `base_entity.py:66–69` defines `is_alive` as `return self.alive()`
(the pygame sprite group membership check). This is correct for enemies and XP orbs,
but incorrect for downed players — downed players stay in sprite groups (by design,
to allow revive), so `self.alive()` returns `True` for them. When `is_downed` is
added to `player.py` in Phase 10, `player.py` must **override** `is_alive` as:
`return self.alive() and not self.is_downed`. Failing to add this override means
downed players are treated as alive by all systems.

### 2.5 Sprite groups are not player-tied
The groups created in `game_scene.py` (`all_sprites`, `enemy_group`,
`projectile_group`, `xp_orb_group`, `effect_group`) are not bound to a player.
Shared groups for enemies and effects are correct for multiplayer. Only
`player_group` needs to be understood as a collection in multiplayer context.

### 2.6 Effects are position-based
`DamageNumber`, `HitSpark`, `DeathExplosion`, `LevelUpEffect` in `effects.py` all
take a world position. They have no owner reference and will work correctly for
N players with no changes.

### 2.7 ResourceLoader and AudioManager
Both are singletons with shared caches. This is the correct pattern for multiplayer;
no per-player resource loading is needed.

### 2.8 InputManager already tracks multiple joysticks
`input_manager.py` already stores `self._joysticks: dict[int, pygame.joystick.Joystick]`
and handles `JOYDEVICEADDED` / `JOYDEVICEREMOVED`. Per-joystick state tracking
(`_axis_dir`, `_axis_timer`, `_button_state`) is keyed by `(instance_id, axis/btn)`
tuples. Adding `get_movement_for_joystick(iid)` and `get_confirm_for_joystick(iid)`
methods is a small surgical addition, not a restructure.

### 2.9 Enemy separation logic
`collision.py`'s `check_enemy_separation()` is already O(N²) over enemies and does
not involve players. It works correctly for any number of players.

### 2.10 Scene transition pattern is already lightweight
`next_scene_kwargs` is already used for small in-memory handoff objects. The
pattern is safe for multiplayer as long as new code keeps kwargs lightweight and
free of runtime-only objects such as sprites, surfaces, or file handles. Plain
dataclasses like `PlayerSlot` are acceptable if their fields stay JSON-safe.

---

## 3. File-by-File Findings

### `src/game_scene.py` — CRITICAL

**Constructor (`__init__`, line 21):**
- Signature `def __init__(self, hero: dict)` — single hero dict. Must become
  `def __init__(self, slots: list[PlayerSlot])` (V2 Phase 4).
- `self.player = Player(...)` (line 34) — singular. Must become
  `self.players: list[Player]`.
- Starting weapon assignment (lines 41–64) is an `if/elif` chain keyed on a single
  `hero["starting_weapon"]`. Must become a loop over `slots`.
- `self.wave_manager = WaveManager(self.player, ...)` (line 70) — passes single player.
- `self.xp_system = XPSystem()` (line 73) — single XP instance. Must become
  `self.xp_systems: list[XPSystem]`, one per slot.
- `self.hud = HUD()` (line 96) — single HUD with no player-count awareness.
- `self.upgrade_menu = None` (line 99) — single upgrade menu slot. Must become a
  per-player upgrade queue (list of pending menus keyed by player).

**Update loop (lines 225–292):**
- `self.collision_system.check_all(self.player, ...)` (line 248) — single player.
- `self.xp_system.update(dt, self.player, ...)` (line 254) — single XP system.
- `self.camera.update(self.player.pos, dt)` (line 257) — single camera target.
- `if self.xp_system.levelup_count > 0 and self.upgrade_menu is None:` (line 260) —
  single level-up check. In multiplayer, every player has their own XP system and
  their own upgrade queue slot.
- `choices = self.upgrade_system.get_random_choices(self.player)` (line 261) —
  single player passed to upgrade system.
- `self.upgrade_menu = UpgradeMenu(choices, self.upgrade_system, self.player)` (line 262) —
  single upgrade menu created without queuing logic.
- Win condition (line 265): `self.wave_manager.victory_flag` is fine; stats aggregation
  assumes single player (`self.player.kill_count`, `self.xp_system.current_level`,
  `self.player.weapons` — lines 270–272).
- Loss condition (line 277): `if not self.player.is_alive:` — in multiplayer, defeat
  should trigger only when **all** players are dead (or all are downed with no revive
  possibility).
- `LevelUpEffect(self.player.pos, ...)` (line 290) — hardcoded to single player
  position; in multiplayer must use the leveling player's position.

**Draw loop (lines 294–354):**
- `sprite != self.player` (line 325) — enemy health bar exclusion check against
  single player. In multiplayer must exclude all players: `sprite not in self.player_group`.
- `for weapon in self.player.weapons:` (line 329) — only draws single player's
  weapon effects. Must loop all players.
- `self.hud.draw_threat_arrows(screen, self.player, ...)` (line 342) — single player.
- `self.hud.draw(screen, self.player, self.xp_system, ...)` (line 343) — single
  player, single XP system.

**Pause handling (lines 168–220):**
- Pause is toggled by `K_ESCAPE` on line 184. The `InputManager` posts synthetic
  `K_ESCAPE` events for all connected controllers simultaneously. Any player pressing
  pause will work — this is acceptable semantics, but it means all controllers can
  pause indiscriminately. For the initial 2P implementation this is fine; revisit for
  dedicated "menu owner" semantics later.
- `self.upgrade_menu.handle_events(events)` (line 223) — passes the global event list.
  All controllers post `K_RETURN` (confirm), so any player can confirm another
  player's upgrade menu. See Section 6 for the full risk.

---

### `src/entities/player.py` — HIGH RISK

**Input reading (lines 82–95):**
- `pygame.key.get_pressed()` reads the **global keyboard state** (lines 82–90).
  Every `Player` instance in multiplayer would read the same keyboard state.
  If two players both use keyboard (one WASD, one arrows), they would both respond
  to both sets of keys because `pygame.key.get_pressed()` returns all pressed keys.
- `InputManager.instance().get_movement()` (line 93) returns the first active
  joystick's input. Every player calls this and gets the same result.
- **Fix direction:** Add `slot: PlayerSlot` parameter to `__init__`. Inside
  `update()`, replace direct keyboard/InputManager reads with `self.slot.input_config`
  dispatch. V2 Section 4.1 defines the `input_config` shape.

**Death state (lines 135–147):**
- `self.dying` flag and death fade work correctly for single player.
- In multiplayer: death should trigger a "downed" state rather than immediate removal,
  allowing revive. The `super().kill()` on line 147 removes the sprite from all groups
  immediately. In multiplayer, a downed player should stay alive in the group (but
  unable to act) until the revive timer expires or a teammate revives them.
- Missing fields: `is_downed`, `revive_timer`, `revive_progress`.
- **More importantly:** `player.py` is not the first place that kills the player.
  `BaseEntity.take_damage()` kills immediately when HP reaches 0. That means the
  revive mechanic cannot be added only by changing the fade/death block in
  `Player.update()`. Lethal damage must be intercepted earlier, either in
  `Player.take_damage()` or by changing the base damage flow.

**Kill count (line 70):**
- `self.kill_count = 0` — per-player kill count exists, which is correct.
  Attribution (who gets the kill) is handled in `enemy.py` and is broken for
  multiplayer (see below).

---

### `src/entities/enemy.py` — HIGH RISK

**Constructor (line 9, 16):**
- Parameter `target` (singular `Player`). Stored as `self.target = target` (line 16).
- All enemy subclasses pass `self.player` from `wave_manager.py`. Changing
  `WaveManager` to pass `player_list` and `Enemy.__init__` to accept it is a
  coordinated change across at least 9 files (Enemy + 7 subclasses + WaveManager).

**Movement logic (lines 61–75):**
- Chase behavior: `direction = self.target.pos - self.pos` (line 62). This never
  re-evaluates which player is closest. In multiplayer an enemy assigned to a downed
  or distant player will chase that player forever, ignoring a nearby healthy player
  standing next to it. This makes multiplayer feel broken immediately.
- Missing `_pick_target(player_list)` method that returns the nearest alive player.

**Kill credit (line 104):**
- `self.target.kill_count += 1` — kill credit always goes to the initial target,
  regardless of which player actually dealt the killing blow. In multiplayer:
  - A skeleton targeting Player 1 but killed by Player 2's ArcaneBolt would credit
    Player 1 for the kill.
  - This is unambiguously wrong. Kill credit should go to the last attacker or the
    killing-blow dealer.
  - **Fix direction:** `enemy.py` needs to track `self.last_attacker` (updated in
    `take_damage()`), and award the kill to `self.last_attacker` on death rather
    than `self.target`.

---

### `src/systems/wave_manager.py` — HIGH RISK

**Constructor (line 24–25):**
- `self.player = player` — stores single Player reference.

**Spawn position calculation (`_get_spawn_pos`, lines 201–227):**
- `px, py = self.player.pos` (line 208) — spawn positions computed relative to
  single player. In 3–4 player games where players are spread across the map,
  enemies will spawn off-screen relative to the "anchor" player but on-screen
  (or even behind) relative to other players.
- **Fix direction:** Accept `player_list`, compute centroid of all alive players,
  use centroid as the spawn anchor.

**Enemy instantiation (lines 178–193):**
- All 7 enemy types receive `self.player` (singular). Each `_spawn_enemy` call must
  pass `player_list` instead.

**Wave scaling:**
- Spawn rates, enemy counts, and elite mode (1.5x HP/damage at 900s) are not scaled
  by player count. 4 players with the same spawn rate as 1 player is trivially easy.
- V2 does not address balance scaling. This is a deferred design decision (see
  Section 11), but it should be called out explicitly.

---

### `src/systems/collision.py` — HIGH RISK

**`check_all` signature (line 8):**
- `def check_all(self, player, enemy_group, projectile_group, effect_group=None):`
- Singular `player`. All four methods (`check_player_enemy_contact`, 
  `check_enemy_projectiles_player`, `check_weapon_hits`, `check_all`) assume one
  player. In multiplayer, only Player 1's damage would be registered.

**`check_player_enemy_contact` (lines 16–29):**
- Checks `player.rect.colliderect(enemy.rect)` (line 19) — single player.
- `player.iframes` check and knockback application — single player.

**`check_enemy_projectiles_player` (lines 40–58):**
- In 1P, the current logic is correct: a projectile is skipped for the player when
  that player has iframes.
- In multiplayer, the method must loop over all players per projectile rather than
  treating collision as a single-player check.

**`check_weapon_hits` (lines 60–65):**
- Currently a no-op pass. Area weapons handle their own collision internally.
- No changes needed here, but documenting that weapon-internal collision also
  assumes single-owner enemies hit-set tracking (which is already per-weapon, not
  per-player, so it's fine).

---

### `src/systems/camera.py` — HIGH RISK

**`update(target_pos: Vector2, dt)` (lines 12–27):**
- Accepts a single `Vector2`. Single lerp-follow to one position.
- No zoom field. No `screen_w` / `screen_h` scaling. World rendering uses
  `self.camera.offset` as a fixed pan with no zoom applied.
- **Cannot be extended incrementally.** The rendering pipeline in `game_scene.py`
  uses `camera.apply(sprite)` (line 321) which calls `entity.rect.move(-self.offset)`.
  Adding zoom requires scaling the entire world render, which changes how every
  sprite's screen position is computed. This is a complete rewrite of both
  `camera.py` and the draw section of `game_scene.py`.
- **No `update_multi()` method** as required by V2 Section 4.3.
- **Missing constants in `settings.py`:** `CAMERA_ZOOM_MIN`, `CAMERA_ZOOM_LERP`,
  `CAMERA_PLAYER_MARGIN`.

---

### `src/systems/xp_system.py` — ALREADY COMPATIBLE (with notes)

- Design is correct: per-instance state, player reference passed at call time.
- **One subtle issue:** `xp_orb.py` has no owner binding. Orbs are in a shared
  `xp_orb_group`. The current XP collection logic in `xp_system.py` (line 16) is:
  `dist = (player.pos - orb.rect.center).length()` — the first player within
  `pickup_radius` collects the orb. This is a first-come-first-served shared pool.
  Once collected (`orb.collected = True` → `orb.kill()`), it's gone.
  This is a reasonable co-op design, but it must be an explicit decision, not an
  accident. Two players could "race" for the same orb, and whichever XPSystem
  processes first gets it. If XP systems are updated in order 0,1,2,3 each frame,
  Player 0 always wins ties. V2 does not address this.

---

### `src/systems/upgrade_system.py` — ALREADY COMPATIBLE

- `get_random_choices(player)` and `apply_choice(choice, player)` work for any
  player reference. No changes needed to this class.
- **Duplicate hero prevention** (blocking two players from picking the same hero
  class) must happen at the `ClassSelect` / lobby level, not here.

---

### `src/systems/save_system.py` — LOW RISK

**`update_after_run` (lines 45–59):**
- Aggregates single run stats: kills, time, level, best time. These are total
  counts across the run.
- In multiplayer: kills should probably be summed across all players; level might
  be the highest level reached. The method signature accepts a `run_result: dict`
  — the calling code in `game_scene.py` / `game_over.py` constructs this dict.
- V2 Phase 8 mentions `player_results: list[dict]` for the game-over screen.
  The save system itself only needs small adjustments to accept aggregated stats.
- **Existing save files** contain `{"total_kills": N, "total_time_played": S, ...}`.
  No schema change is required if the aggregation happens at the caller level.

---

### `src/ui/hud.py` — HIGH RISK

**`draw` signature (line 81):**
- `def draw(self, screen, player, xp_system, wave_manager, show_fps=False, fps=0):`
- Single player, single XP system. The entire layout is designed for one player.

**HP bar (line 85):**
- `pygame.Rect(20, 20, 200, 20)` — hardcoded top-left position.

**XP bar (line 134):**
- `pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20)` — full-width bottom bar,
  single XP system.

**Kill counter + class label (lines 156–159):**
- Hardcoded top-right: `SCREEN_WIDTH - kill_text.get_width() - 10`.
- Single player's `kill_count` and `hero_class`.

**Weapon slots (lines 162–184):**
- `weapon_slots_x = SCREEN_WIDTH - (MAX_WEAPON_SLOTS * 45 + 5)` — hardcoded
  bottom-right for single player.

**Threat arrows (line 24–79):**
- Takes single `player` to determine camera boundaries. In multiplayer, threats
  are relative to the camera position (centroid-based), not any one player.
  This method signature needs `camera` only (already received), not `player`.

**`draw_threat_arrows` actually doesn't use `player` directly** — it uses
`camera.offset` for screen boundary calculations. The `player` parameter is
passed but not used inside `draw_threat_arrows` (it's used at the call site to
pass camera). **Verify:** looking at lines 26–29, `screen_left = camera.offset.x`,
`screen_right = camera.offset.x + SCREEN_WIDTH` — correct, `player` is not used.
The method signature has an unused `player` parameter. This is a cleanup item.

---

### `src/ui/upgrade_menu.py` — MEDIUM RISK

**Constructor (line 7):**
- `def __init__(self, choices, upgrade_system, player):` — single player.
- `self.player = player` (line 10) — stored reference.
- `self.upgrade_system.apply_choice(self.choices[index], self.player)` (line 78) —
  applies upgrade to single player.

**Input handling (lines 31–73):**
- Listens for global `K_1`, `K_2`, `K_3` (keyboard) and `K_RETURN` (controller
  confirm, posted as synthetic KEYDOWN by `InputManager`).
- **Input bleed risk:** If Player 1 is choosing an upgrade, Player 2 pressing
  their controller's A button also posts `K_RETURN` and will confirm the choice.
  Any controller can accidentally dismiss another player's upgrade menu.
- **Critical implementation note:** the current synthetic events do not preserve
  controller identity. `InputManager` posts plain `KEYDOWN` events with only a key
  code, so `UpgradeMenu` cannot tell which controller sent `K_RETURN`. "Filter by
  source device" is not possible until the event model changes or the menu polls
  the owning device directly.

**Header text (line 94):**
- `"LEVEL UP!"` — no per-player identity. In multiplayer, should display
  `"PLAYER 2 — LEVEL UP!"` or similar.

---

### `src/ui/class_select.py` — HIGH RISK

**Constructor (lines 6–17):**
- No parameters. `self.selected_class = None` (line 9) — single selection.
- `self.nav_index = 0` (line 11) — single keyboard nav cursor.

**Confirmation routing (lines 43–44):**
- `self.next_scene = "playing"`
- `self.next_scene_kwargs = {"hero": self.selected_class}` — single hero dict,
  single player.

**Hero hardcount (lines 102, 30–31):**
- `for i in range(3):` and `for i, hero in enumerate(HERO_CLASSES):` — iterates
  exactly `len(HERO_CLASSES)`. This is fine as long as hero count stays flexible.

**Duplicate prevention:**
- None. Two players could both select Knight if the scene were called twice.

**No slot-based routing:**
- The scene does not accept `slots: list[PlayerSlot]` or `confirmed_slots`.
- Complete redesign required to support sequential per-player hero selection.

**SceneManager coupling:**
- Even if `ClassSelect` is rewritten to accept `slots` and `confirmed_slots`, the
  current `SceneManager` caches `STATE_CLASS_SELECT` and instantiates it once with
  no kwargs. A slot-queue flow will not work until `STATE_CLASS_SELECT` is recreated
  fresh per transition or explicitly reinitialized with the queued kwargs.

**Input bleed (same risk as `UpgradeMenu`):**
- `handle_events()` processes `K_RETURN` from the global event queue. Any
  connected controller's A button posts `K_RETURN` via `InputManager`, so
  Player 2's controller can confirm Player 1's hero selection.
- **Fix direction:** Same as upgrade menu — but note that filtering plain
  `K_RETURN` events by device is not possible in the current code because source
  controller identity is discarded by `InputManager`.

---

### `src/ui/game_over.py` — LOW RISK

**Constructor (line 7):**
- `def __init__(self, victory: bool, stats: dict):` — single stats dict.
- Lines 109–114 display kill count, level, and weapons from a single dict.
- In multiplayer, per-player rows are needed: "PLAYER 1: Wizard, L12, 47 kills".

**Save update (lines 19–23):**
- `SaveSystem().update_after_run(...)` — runs immediately at construction. This is
  fine; just needs the aggregated multiplayer stats passed in.

---

### `src/utils/input_manager.py` — MEDIUM RISK

**`get_movement()` (lines 70–85):**
- Returns movement from the **first** joystick with non-zero input. If two
  controllers are connected, `get_movement()` always returns controller 0's input
  if it's non-zero, controller 1's only if controller 0 is centered.
- Every `Player.update()` calls `InputManager.instance().get_movement()` — both
  players would fight over the same input.

**Synthetic KEYDOWN events (lines 96–133, 155–173):**
- `_process_axes`, `_process_hats`, `_process_buttons` post `K_LEFT`, `K_RIGHT`,
  `K_UP`, `K_DOWN`, `K_RETURN`, `K_ESCAPE` events for **all connected controllers**.
- These events are indistinguishable from keyboard events and go into the global
  pygame event queue. `ClassSelect`, `UpgradeMenu`, and `GameScene` consume these
  events without knowing which device posted them.
- **Input bleed:** In multiplayer menus, any player's controller can navigate any
  menu. This is expected for pause (any player can pause) but problematic for
  upgrade menus and class selection where each player should only control their
  own UI.
- **Disconnect handling:** `JOYDEVICEREMOVED` (lines 57–63) cleanly removes state
  for the disconnected joystick. The `player_group` slot would need its own
  disconnect policy (pause? auto-resume with keyboard?).

**This is the hidden blocker for owned multiplayer menus:**
- The current event payload written by `_post_key()` / `_post_keyup()` contains no
  joystick instance ID. That means V2's "filter by device" guidance is not directly
  implementable with the current `InputManager` shape. Either custom event payloads
  or direct device polling are required.

**Missing per-joystick API (required by V2 Section 4.1):**
- `get_movement_for_joystick(iid: int) -> tuple[float, float]` — not implemented
- `get_confirm_for_joystick(iid: int) -> bool` — not implemented  
- `get_connected_joysticks() -> list[int]` — not implemented

---

### `src/entities/base_entity.py` — COMPATIBLE WITH ONE MAJOR CAVEAT

`sprite_id`, `hp/max_hp`, `heal()`, and the base interface are fine for multiplayer.
However, `take_damage()` kills the sprite immediately when HP reaches 0. That is
compatible for enemies, but incompatible with a player downed/revive flow. The base
class itself does not need a multiplayer rewrite, but the docs must treat this as a
hard prerequisite for revive.

### `src/weapons/*.py` — COMPATIBLE

All weapon classes use `self.owner` for position and stat references. Correct pattern.
No changes needed.

### `src/entities/xp_orb.py` — COMPATIBLE (shared-pool semantics)

No owner binding. First-come-first-served collection. This must be an explicit
design decision rather than an accident. Co-op shared XP pool is reasonable.

### `src/entities/effects.py` — COMPATIBLE

All effect types are position-based with no owner. Compatible with N players.

### `src/entities/enemies/*.py` — MEDIUM RISK (coordinated change)

All 7 enemy subclasses pass `self.player` (from WaveManager) to their superclass.
Once `WaveManager` passes `player_list` and `Enemy.__init__` accepts it, subclasses
inherit the fix automatically if they call `super().__init__()` correctly.
No per-subclass logic needs changing unless a subclass has its own targeting.

**LichFamiliar** orbits `self.target.pos` and fires at `self.target`. Verify that
its subclass `update()` uses inherited `self.target` — if so, fixing the base class
is sufficient.

---

## 4. Remaining Single-Player Assumptions in the Real Code

The following are concrete locations in the real code that assume exactly one player.
Every one of these must change before multiplayer works.

| # | File | Line(s) | Assumption | Impact |
|---|------|---------|------------|--------|
| 1 | `game_scene.py` | 21 | `__init__(self, hero: dict)` | 1P signature |
| 2 | `game_scene.py` | 34 | `self.player = Player(...)` | Singular player sprite |
| 3 | `game_scene.py` | 70 | `WaveManager(self.player, ...)` | Single wave target |
| 4 | `game_scene.py` | 73 | `self.xp_system = XPSystem()` | Single XP state |
| 5 | `game_scene.py` | 248 | `check_all(self.player, ...)` | Single collision check |
| 6 | `game_scene.py` | 254 | `xp_system.update(dt, self.player, ...)` | Single XP update |
| 7 | `game_scene.py` | 257 | `camera.update(self.player.pos, dt)` | Single camera target |
| 8 | `game_scene.py` | 260–262 | Single upgrade menu slot | No per-player queue |
| 9 | `game_scene.py` | 270–272 | Stats from `self.player.*` | Single player stats |
| 10 | `game_scene.py` | 277 | `if not self.player.is_alive:` | 1P loss condition |
| 11 | `game_scene.py` | 290 | `LevelUpEffect(self.player.pos, ...)` | 1P position |
| 12 | `game_scene.py` | 325 | `sprite != self.player` | Singular exclusion |
| 13 | `game_scene.py` | 329 | `for weapon in self.player.weapons:` | Single weapon draw |
| 14 | `game_scene.py` | 342–343 | `hud.draw*(..., self.player, ...)` | Single HUD |
| 15 | `player.py` | 82–90 | `pygame.key.get_pressed()` | Global keyboard |
| 16 | `player.py` | 93 | `InputManager.instance().get_movement()` | First joystick |
| 17 | `player.py` | 135–147 | Death → immediate kill | No downed state |
| 18 | `enemy.py` | 16 | `self.target = target` | Single target stored |
| 19 | `enemy.py` | 62, 67 | `self.target.pos` | Never retargets |
| 20 | `enemy.py` | 104 | `self.target.kill_count += 1` | Kill credit wrong |
| 21 | `wave_manager.py` | 25 | `self.player = player` | Single spawn anchor |
| 22 | `wave_manager.py` | 208 | `px, py = self.player.pos` | Single spawn pos |
| 23 | `wave_manager.py` | 178–193 | All enemies get `self.player` | Single target |
| 24 | `collision.py` | 8 | `check_all(self, player, ...)` | Single player param |
| 25 | `collision.py` | 19, 47 | `player.rect.colliderect(...)` | Single rect check |
| 26 | `camera.py` | 12 | `update(target_pos: Vector2, dt)` | Single position |
| 27 | `hud.py` | 81 | `draw(screen, player, xp_system, ...)` | Single player |
| 28 | `hud.py` | 85 | `pygame.Rect(20, 20, 200, 20)` | Hardcoded 1P position |
| 29 | `hud.py` | 134 | Full-width XP bar | Single XP system |
| 30 | `hud.py` | 156–159 | Top-right kill/class display | Single player |
| 31 | `hud.py` | 162 | Hardcoded bottom-right weapon slots | Single player |
| 32 | `class_select.py` | 43–44 | `next_scene_kwargs = {"hero": ...}` | Single hero |
| 33 | `upgrade_menu.py` | 7 | `__init__(..., player)` | Single player |
| 34 | `upgrade_menu.py` | 78 | `apply_choice(..., self.player)` | Single player |
| 35 | `input_manager.py` | 76–84 | Returns first joystick movement | No per-joystick |

---

## 5. Remaining Design Gaps or Risks in the V2 Guide

These are places where V2 itself still risks assuming exactly 2 players, or where
it underspecifies the N-player case.

### 5.1 LobbyScene layout
V2 (line 27) notes that V1's lobby laid out "exactly two side-by-side slots." V2
did not previously specify what the lobby layout looks like for 3 or 4 players.
The first implementation should define a concrete 4-slot layout up front
(recommended: 2×2 grid) so the UI work is not deferred until implementation.

### 5.2 Camera zoom formula
V2 Section 4.3 (around line 96–99) specifies "0.75–0.85x" for 2 players and
"dynamic zoom-out based on bounding box" for 3–4. The minimum zoom floor is
mentioned but the formula for computing zoom from bounding box area/diagonal is
not specified. This needs to be worked out before Phase 5.

### 5.3 Spawn positioning for 3–4 players
V2 (line 65) notes that spawning relative to a "single midpoint" is fine for 2
but breaks for 4 players near opposite corners. The fix (centroid spawning) is
correct but the edge case of 4 players maximally spread (near world corners) is
not resolved: enemies spawning relative to the centroid may be on-screen for some
players and off-screen for others.

### 5.4 Upgrade menu input disambiguation
V2 (line 66) says `player_index + 1` label "works for N but assumes a display
order." It does not address the input bleed problem where any controller's `K_RETURN`
event can confirm any upgrade menu. Sequential menus need either per-device input
routing or a "waiting for Player N's input" indication that ignores other devices.

### 5.5 Leash replacement
V2 removes the leash mechanic in favor of soft zoom. But if two players are at
opposite world corners (max separation ≈ 2828 units on a 2000×2000 world), the
minimum zoom floor may make both players invisible or unplayably tiny. The
acceptable minimum zoom level and what happens when players exceed it (teleport?
soft boundary?) is not specified.

### 5.6 Ready condition for lobby
V2 correctly removes "both slots filled" as the ready condition, but this must stay
explicit in the implementation guidance: minimum 1 joined slot, joined slots are
implicitly ready once they have claimed a device, and starting begins a run with
exactly the currently joined slots.

### 5.7 Cross-doc terminology to keep aligned
Two clarified assumptions should stay consistent across V2, this audit, and the
agent guide:
- `PlayerSlot` is lobby/session metadata, not runtime combat state. Downed/revive
  state belongs on `Player`.
- The final target is that the lobby emits a concrete `input_config` even for 1P.
  `input_config=None` is only a temporary migration shim for the pre-lobby 1P path.

---

## 6. Missing Multiplayer Considerations Not Fully Covered Yet

### 6.1 Kill credit attribution
`enemy.py` line 104: `self.target.kill_count += 1`. In multiplayer, kill credit
goes to the initial target, not the killing blow dealer. If Player 2 kills a
skeleton that was targeting Player 1, Player 1 gets the kill. This will always be
wrong. Fix: track `self.last_attacker` (updated in `take_damage()`) and award
kills there.

### 6.2 XP orb collection race condition
`xp_system.py` processes orbs in arrival order. With N XP systems updated
sequentially each frame, Player 0's system always wins orb collection ties.
This is not addressed in V2. Options: (a) accept shared-pool semantics, (b)
implement proximity priority per orb, (c) split orb value equally if two players
are within range simultaneously.

### 6.3 Wave/difficulty balance scaling
Spawn rates, enemy HP, elite mode timing, and boss thresholds do not scale with
player count. 4 players on the same wave schedule as 1 player is trivially easy.
V2 does not address this at all. This is a game design question, not an architecture
question, but it must be resolved before multiplayer is released.

### 6.4 Player body-blocking
`check_enemy_separation` prevents enemies from overlapping. No equivalent exists
for players. 4 players on the same spawn point will all start at the same world
pixel. Spawn offsets exist in V2 conceptually but are not specified for 3–4 players.
Additionally, players moving through each other is invisible (no sprite collisions),
which may or may not be desirable.

### 6.5 Off-screen downed player indicators
A downed player who wandered off-screen before going down is invisible to teammates.
V2 mentions "off-screen player indicators" but provides no layout spec. This is
needed for multiplayer to be playable.

### 6.6 Controller disconnect mid-game
`InputManager` handles `JOYDEVICEREMOVED` cleanly for the device tracking. But
what happens to the player whose controller disconnected? The V2 guide does not
specify whether they auto-pause, go to idle (stop moving), are treated as downed,
or trigger a reconnect prompt. A crash-safe fallback is needed.

### 6.7 Save data behavior in multiplayer runs
V2 Phase 8 mentions per-player game-over stats but does not specify what happens
to meta-progression (kills, time, highest level) in a multiplayer run. Should a
multiplayer run count toward individual players' progression? There is no player
identity concept in the current save system. If two different people play on the
same machine, their shared `saves/progress.json` will mix their stats.

### 6.8 Audio balance with multiple players
If 4 players are simultaneously taking damage, collecting orbs, and leveling up,
audio events will stack. `AudioManager` plays SFX through pygame's mixer with
multiple channels. There is no priority or throttle system. With 4 players this
could become audio spam. Consider adding a per-sound-type cooldown.

### 6.9 Upgrade menu timing: simultaneous level-ups
If Players 1, 2, and 3 all level up in the same frame, three upgrade menus need
to be shown. The current `if self.xp_system.levelup_count > 0 and self.upgrade_menu is None`
guard only handles one pending menu. The per-player queue approach in V2 is correct,
but the interaction between "game is paused during upgrade" and "multiple players
queued" needs to be explicit: each player gets their menu in sequence, game unpauses
only after all queued menus are dismissed.

### 6.10 Hero color / visual distinction
In multiplayer, players need visual differentiation. V2 requires `PLAYER_COLORS`
in `settings.py`. The player sprite is a monochrome 4-direction sheet with color
determined by the art asset. Options: (a) tint the sprite surface at construction
time, (b) draw a colored ring under the player, (c) use separate art per player.
The game's current `ResourceLoader` + `Spritesheet` pipeline does not include
tinting. This needs a concrete decision before Phase 4.

---

## 7. High-Risk Refactors

These are the changes most likely to introduce regressions in the current
single-player loop. Each must be followed immediately by a 1P verification pass.

### HR-1: `game_scene.py` — `self.player` → `self.players: list[Player]`
**Severity: HIGH**  
**Why it matters:** `self.player` is the root of 20+ downstream assumptions. Every
system call, stat aggregation, HUD draw, and win/loss check flows through it.  
**Affected files:** `game_scene.py`, `hud.py`, `wave_manager.py`, `collision.py`,
`xp_system.py`, `camera.py`, `upgrade_menu.py`  
**What could break:** Every 1P behavior if done wrong. The 1P path must be verified
after this change before anything else.  
**Fix direction:** Keep a `@property player(self) -> Player` that returns
`self.players[0]` as a 1P compatibility alias. Migrate call sites incrementally
from `self.player` to the appropriate player from the list.  
**Solve before 2P:** Yes — foundational.

### HR-2: `player.py` — Input reading
**Severity: HIGH**  
**Why it matters:** Currently reads global keyboard state. Two player instances
in the same process would share input.  
**Affected files:** `player.py`, `input_manager.py`, new `player_slot.py`  
**What could break:** 1P keyboard input if the dispatch logic is wrong. The
`pygame.key.get_pressed()` path must continue to work for 1P.  
**Fix direction:** Add `slot: PlayerSlot` parameter. `input_config=None` means
legacy 1P combined input (WASD + arrows + any controller). Any other `input_config`
routes to its specific device.  
**Solve before 2P:** Yes — no multiplayer input is possible without this.

### HR-3: `enemy.py` + `wave_manager.py` — Target list
**Severity: HIGH**  
**Why it matters:** All enemies are constructed with a single `target` at spawn
time and never retarget. Adding a second player does not change enemy behavior.  
**Affected files:** `enemy.py`, `wave_manager.py`, all 7 enemy subclasses  
**What could break:** Enemy movement and kill credit in 1P if the targeting
logic regresses.  
**Fix direction:** Coordinated change. `WaveManager` stores `player_list`.
`Enemy.__init__` accepts `player_list`. `enemy.update()` calls
`self._pick_target()` to find nearest alive player each frame (or on a throttled
interval for performance). Kill credit via `self.last_attacker`.

**Important — all 7 subclass `__init__` signatures need updating:** Verified from
`skeleton.py:14` — every subclass overrides `__init__` with a `target` parameter
that it passes to `super().__init__()`. The fix is the same in each: rename
`target` → `player_list` in the `__init__` signature and the `super().__init__()`
call. The subclasses' `update()` methods that reference `self.target` (e.g.
`skeleton.py:57`) do **not** need changes — `_pick_target()` in the parent updates
`self.target`, and subclasses inherit the current value automatically.

**`LichFamiliar` special case:** this subclass orbits `self.target.pos` and fires
at `self.target`. After the base class change, verify explicitly that `LichFamiliar`
uses the inherited `self.target` attribute (not a locally cached copy). If it does,
no further change is needed.  
**Solve before 2P:** Yes — enemies ignoring all but one player is non-functional.

### HR-4: `camera.py` — Zoom and multi-target follow
**Severity: HIGH**  
**Why it matters:** No zoom means either all players must stay near each other
(leash) or players can go completely off screen. The current `apply()` method
would need to support scaling for zoom. This touches the entire draw pipeline.  
**Affected files:** `camera.py`, `game_scene.py` (draw section), `settings.py`  
**What could break:** All world-space rendering if the offset math changes.
Background rendering (`game_scene.py` lines 298–308) uses `camera.offset` directly.
Enemy health bars (`base_entity.py:draw_health_bar`) compute screen positions from
`self.rect` and raw `offset` — wrong once zoom is applied. Threat arrows in
`hud.py` use `camera.offset` for screen boundary math and must be rechecked.  
**Fix direction:** Add `zoom: float = 1.0` to `Camera`. Add `update_multi(positions)`.
Update `apply()` to return a zoom-scaled `pygame.Rect` (not just offset-shifted).
Update `game_scene.py`'s draw loop to scale sprites to the zoomed rect size, OR
render the world to an off-screen surface and scale the entire surface once per
frame (recommended — one `transform.scale` call regardless of entity count).
Background tile rendering loop must also be updated to account for `camera.zoom`.
This is a complete camera rewrite.  
**Solve before 2P:** Yes for the centroid follow; zoom can be deferred to Phase 13.

### HR-5: `collision.py` — Multi-player collision
**Severity: HIGH**  
**Why it matters:** In multiplayer, player 2+ takes no contact damage and no
projectile damage because the collision system only checks `player` (singular).  
**Affected files:** `collision.py`, `game_scene.py` (call site)  
**What could break:** 1P collision behavior if the loop regresses.  
**Fix direction:** Change `check_all(player, ...)` to `check_all(players: list[Player], ...)`.
Internal methods loop over `players`. The call site in `game_scene.py` passes
`self.players`. This is a contained change with low blast radius if done cleanly.  
**Solve before 2P:** Yes — collision is broken without it.

---

## 8. Low-Risk Refactors

These changes have small blast radius and can be done without risking the 1P loop.

### LR-1: `InputManager` — Add per-joystick API methods
**Severity: LOW**  
Add `get_movement_for_joystick(iid)`, `get_confirm_for_joystick(iid)`,
`get_connected_joysticks()`. Existing `get_movement()` continues to work unchanged.
Pure additions; nothing is removed. Safe to do in Phase 10.

### LR-2: `settings.py` — Add multiplayer constants
**Severity: LOW**  
Add `PLAYER_COLORS`, `SPAWN_OFFSETS`, `CAMERA_ZOOM_MIN`, `CAMERA_ZOOM_LERP`,
`CAMERA_PLAYER_MARGIN`, `REVIVE_RADIUS`, `REVIVE_DURATION`, `MAX_PLAYERS`,
and `HUD_PANEL_TUPLES` (as plain `(x, y, w, h)` tuples — `settings.py` must not
import pygame, so `pygame.Rect` objects must not appear here; convert to `pygame.Rect`
inside `hud.py` at use time).

**Do not add** `PLAYER_COUNT`, `COOP_CAMERA_ZOOM`, or `COOP_LEASH_DISTANCE` —
these were V1 design artifacts that were never implemented in the codebase. V2
references removing them, but they do not currently exist in `settings.py`.

Pure additions; no existing code changes.

### LR-3: `hud.py` — Unused `player` param in `draw_threat_arrows`
**Severity: LOW**  
`player` parameter exists in the signature but is not used inside the method.
Remove it (or keep it for now — it doesn't break anything either way).

### LR-4: `game_over.py` — Add per-player results display
**Severity: LOW**  
Add optional `player_results: list[dict]` parameter. When present, display per-player
rows. When absent, display current single-player format. Fully backward-compatible.

### LR-5: `save_system.py` — Accept aggregated multiplayer stats
**Severity: LOW**  
The `update_after_run()` method receives a dict; the multiplayer caller will
aggregate stats before calling it. No changes to `save_system.py` are strictly
required unless per-player tracking is desired.

### LR-6: `upgrade_menu.py` — Add player identity header
**Severity: LOW**  
Add `slot_index: int = 0` parameter. Render `"PLAYER 1 — LEVEL UP!"` when
`slot_index > 0`. Backward-compatible with default value.

### LR-7: `class_select.py` — Add `BACK` to skip to menu if no lobby
**Severity: LOW**  
Current BACK button routes to `"menu"`. In a lobby flow, BACK should return to
the lobby. This is routing logic only and affects the single transition target.

### LR-8: `enemy.py` — Add `last_attacker` tracking
**Severity: LOW**  
Add `self.last_attacker = None` to `Enemy.__init__`. Update in `take_damage()`.
Award kill to `self.last_attacker` on death instead of `self.target`. This also
fixes kill credit in 1P (no regression risk, just a more correct attribution).

---

## 9. Recommended Implementation Order

This order is designed to preserve 1P at every checkpoint.

**Phase 10 — Foundation (no gameplay changes, safest possible start)**
1. Create `src/core/` directory. Add `PlayerSlot` dataclass to new
   `src/core/player_slot.py` (V2 Section 4.1 defines the schema — match it exactly).
   Update `CLAUDE.md` project structure to include `src/core/`.
2. Add per-joystick methods to `InputManager` (`LR-1`)
3. Add multiplayer constants to `settings.py` (`LR-2`)
4. Add `last_attacker` tracking to `enemy.py` (`LR-8`)
5. Add `slot: PlayerSlot | None = None` parameter to `Player.__init__`. Store
   `self.slot = slot`. Add `is_downed = False` and `revive_timer = 0.0`. Override
   `is_alive` property to `return self.alive() and not self.is_downed`.
   Condition death trigger on `self.slot is not None`. 1P path (`slot=None`) unchanged.
6. Run `python run_check.py`. Verify 1P still works end-to-end.

**Phase 11 — LobbyScene (new UI, isolated from gameplay)**
7. Create `src/ui/lobby_scene.py` with slot-joining and device assignment.
   All players — including the solo 1P — go through the lobby. No separate 1P
   shortcut path. A 1-slot lobby produces a 1-slot `PlayerSlot` list that feeds
   through `ClassSelect` → `GameScene` exactly like the 2–4P path.
   This unifies the code path and avoids maintaining two routes.
8. Wire `MainMenu` → `LobbyScene` → `ClassSelect` (update `main_menu.py` routing).
9. Extend `class_select.py` to accept `slots: list[PlayerSlot]` and
   `confirmed_slots: list[PlayerSlot]` parameters (additive — preserve current
   behavior when params are absent, so nothing breaks before step 11 completes).
10. Verify the full unified 1P path: `MainMenu → Lobby (1 slot) → ClassSelect →
    Game` is functionally identical to the previous direct 1P flow.
11. Verify the 2P path: sequential hero selects with duplicate hero lock-out.

**Phase 12 — GameScene core refactor (highest risk, most impactful)**
12. Change `GameScene.__init__` to accept `slots: list[PlayerSlot]`
13. Replace `self.player` with `self.players: list[Player]`, add `.player` alias
14. Add per-player `XPSystem` instances
15. Change `CollisionSystem.check_all` to accept player list (`HR-5`)
16. Change `WaveManager.__init__` to accept player list, fix spawn positions
17. Change `Enemy.__init__` + all 7 subclass `__init__` signatures to accept
    `player_list` instead of `target`; add `_pick_target()` to `Enemy` (`HR-3`).
    Verify `LichFamiliar` uses `self.target` (not a cached copy) after this change.
18. Verify 1P with 1-slot `PlayerSlot` list. Do not add 2P until 1P passes.

**Phase 13 — Camera + HUD + upgrade queue (world systems polish)**
19. Rewrite `camera.py` with zoom and `update_multi()` (`HR-4`).
    Update `game_scene.py` draw pipeline for zoom (off-screen surface scale
    recommended — one `transform.scale` per frame). Update background tile rendering.
    Update `draw_health_bar()` screen-position math in `base_entity.py`.
20. Redesign `hud.py` with `_draw_player_panel()` helper and N-player layout
    (convert `HUD_PANEL_TUPLES` from settings to `pygame.Rect` at use time).
    Remove unused `player` param from `draw_threat_arrows`.
21. Add per-player upgrade queue to `GameScene.update()` (`section 6.9`)
22. Update `UpgradeMenu` with slot index header (`LR-6`); add input device filter
    so only the active slot's device can confirm its own upgrade menu.
23. Revive mechanic: add `_update_revive()` to `game_scene.py` (`section 4.8`)
24. Verify 1P still works. Then verify 2P.

**Phase 14 — Game-over, save, polish**
24. Update `game_over.py` with per-player results (`LR-4`)
25. Update `save_system.py` aggregation for multiplayer runs (`LR-5`)
26. Add off-screen downed player indicators to `hud.py`
27. Add controller disconnect handling (pause/warning)
28. Address audio spam throttling (`section 6.8`)
29. Full regression test: 1P, 2P, 3P, 4P

---

## 10. Regression Test Strategy

### After every phase
1. **Run `python run_check.py`** — catches import errors immediately.
2. **Manual 1P smoke test:**
   - Before Phase 11: `Menu → Class Select → Game → collect XP → level up → pick upgrade → take damage → die → Game Over`
   - After Phase 11: `Menu → Lobby (1 slot) → ClassSelect → Game → collect XP → level up → pick upgrade → take damage → die → Game Over`
3. Verify save file updates correctly.

### After Phase 12 (GameScene refactor)
- 1P with `slots=[PlayerSlot(index=0, hero=HERO_CLASSES[0], input_config=None)]`
- All three hero classes
- Level-up upgrade menu appears and applies correctly
- Death triggers game-over correctly
- Victory at 1800s triggers correctly
- Pause and resume work

### After Phase 13 (Camera + HUD)
- 2P: both players visible on camera
- 2P: both HUD panels update correctly
- 2P: upgrade menus appear sequentially; correct player gets the upgrade
- 2P: revive mechanic works (player 1 goes down, player 2 revives)
- 1P: HUD still looks correct in 1-player mode
- 1P: camera behaves identically to the pre-refactor camera

### After Phase 14 (Game-over + save)
- Game-over screen shows per-player stats
- Save file updated with aggregated run data (not corrupted)
- Existing saves load correctly (backward compatibility)
- 4P: all four players can join, select heroes (no duplicates), and play

### Specific regression risks per phase
| Phase | What's most likely to break |
|-------|---------------------------|
| 10 | Nothing (additions only) |
| 11 | 1P scene routing if lobby insertion is wrong |
| 12 | All 1P gameplay — must retest exhaustively |
| 13 | Camera rendering artifacts; wrong player getting upgrades |
| 14 | Save file corruption if schema changes carelessly |

---

## 11. Deferred Decisions / Things Not Worth Solving Yet

### Defer: Wave balance scaling for player count
Designing 4-player balance requires playtesting. Add a stub constant
`PLAYER_COUNT_SPAWN_MULTIPLIER = 1.0` in `settings.py` to make scaling possible
later, but don't implement it until the 2P gameplay loop is playable.

### Defer: Competitive vs. cooperative XP orbs
Shared-pool is the simpler model and works fine for initial co-op. Don't split
orbs or implement ownership until the design calls for it.

### Defer: Player body-blocking collision
Players passing through each other is invisible and mostly harmless for a
survivor-style game. Add it only if playtesting identifies it as a problem.

### Defer: Per-player save / identity system
The current save system is machine-scoped, not per-person. Adding player identity
(accounts, profiles) is a significant scope expansion. Keep aggregated stats per
machine for now.

### Defer: Audio priority / throttling
Audio spam is a quality-of-life issue, not a functional one. Revisit after 2P
gameplay is working.

### Defer: 3–4 player HUD layout
Design the 2P HUD first. Extend to 3–4 after you've validated the panel-based
approach works. Don't overengineer a 4-player layout before the 2-player one is
playable.

### Defer: Online multiplayer infrastructure
V2 explicitly defers this. Do not add `NetworkManager`, rollback, or peer discovery.
Small determinism-friendly choices (centralized RNG, no state mutations outside
update flow) are good; dead framework code is not.

### Defer: Controller rebinding per player
Complicated UX with marginal benefit for local co-op where players typically just
use "whatever controller they grabbed." Defer until after launch.

---

## 12. Top 10 Issues to Fix Before Serious Multiplayer Implementation

---

### Issue 1: `PlayerSlot` dataclass does not exist

**Severity:** HIGH  
**Why it matters:** `PlayerSlot` is the foundational abstraction V2 builds on.
Without it, every subsequent phase has no type to refer to, and there is no clean
way to pass slot information through the scene transition chain.  
**Affected files:** New `src/core/player_slot.py`; will be imported by
`game_scene.py`, `class_select.py`, `lobby_scene.py`, `player.py`  
**What could break:** Nothing in 1P — it's an addition. But if not done first,
every multiplayer file will invent its own ad-hoc representation.  
**Recommended fix:** Create `src/core/player_slot.py` (V2 uses `src/core/` so it
is not in `src/entities/` — `PlayerSlot` is not a sprite). Create the `src/core/`
directory and update `CLAUDE.md`'s project structure listing. Use `@dataclass`.
Match the exact field names in V2 Section 4.1 (do not rename them — cross-phase
consistency is critical).  
**Solve before 2P:** Yes — Phase 10.

---

### Issue 2: `player.py` reads global input; two instances share one keyboard

**Severity:** HIGH  
**Why it matters:** `pygame.key.get_pressed()` returns all currently pressed keys.
If Player 1 uses WASD and Player 2 uses arrows, Player 1 would also respond to
arrow keys and Player 2 would also respond to WASD. Both players would share the
same controller input from `InputManager.instance().get_movement()`.  
**Affected files:** `player.py` (lines 82–95), `input_manager.py`, `player_slot.py`  
**What could break:** 1P keyboard control if the new dispatch path has bugs.  
**Recommended fix:** Add `slot: PlayerSlot` to `Player.__init__`. Inside `update()`,
dispatch movement reading through `self.slot.input_config`. When `input_config=None`,
use the current combined WASD+arrows+any-controller behavior (exact 1P compat).  
**Solve before 2P:** Yes — Phase 10/12.

---

### Issue 3: `enemy.py` targets one player forever, never retargets

**Severity:** HIGH  
**Why it matters:** Enemies assigned to Player 1 will ignore Player 2 standing
next to them. In multiplayer this is immediately noticeable and makes the game
feel broken.  
**Affected files:** `enemy.py`, `wave_manager.py`, all 7 enemy subclasses  
**What could break:** Enemy movement in 1P if targeting regression.  
**Recommended fix:** Accept `player_list: list[Player]`. Add `_pick_target()` that
returns the nearest alive player. Call on `update()` (or throttled to every 0.25s
for performance). Kill credit via `self.last_attacker` (see Issue 10).  
**Solve before 2P:** Yes — Phase 12.

---

### Issue 4: `collision.py` checks only one player

**Severity:** HIGH  
**Why it matters:** In multiplayer, Player 2+ takes no contact damage and no
projectile damage. The game is effectively 1P regardless of player count.  
**Affected files:** `collision.py` (all methods), `game_scene.py` (line 248)  
**What could break:** Damage application in 1P if the loop introduces a regression.  
**Recommended fix:** Change `check_all(player, ...)` to `check_all(players: list, ...)`.
Internal methods loop over the list. The call site passes `self.players`. Small,
contained change.  
**Solve before 2P:** Yes — Phase 12.

---

### Issue 5: `game_scene.py` has `self.player` singular at 20+ sites

**Severity:** HIGH  
**Why it matters:** `game_scene.py` is the hub. Every system is wired through
`self.player`. This is the root multiplayer refactor.  
**Affected files:** `game_scene.py`  
**What could break:** Everything in 1P if done wrong.  
**Recommended fix:** Change `self.player = Player(...)` to `self.players: list[Player]`.
Add `@property def player(self): return self.players[0]` as a compatibility alias.
Migrate high-priority call sites (update loop first, draw loop second, init third).
Do not remove the alias until all sites are migrated.  
**Solve before 2P:** Yes — Phase 12.

---

### Issue 6: `camera.py` has no zoom and no multi-target follow

**Severity:** HIGH  
**Why it matters:** Without zoom, 4 players who spread out will go off-screen.
The only alternative — a hard leash — is rejected by V2. The entire rendering
pipeline depends on `camera.offset` and `camera.apply()`.  
**Affected files:** `camera.py`, `game_scene.py` (draw section, lines 298–354)  
**What could break:** All world rendering if offset/zoom math is wrong.  
**Recommended fix:** Add `zoom: float = 1.0` to `Camera`. Add `update_multi(positions)`.
Update `apply()` to scale by zoom. Update `game_scene.draw()` to use zoomed
subsurface. Add constants to `settings.py`. This is a complete rewrite.  
**Solve before 2P:** Centroid follow yes (Phase 12); dynamic zoom can be Phase 13.

---

### Issue 7: No `LobbyScene` or input device assignment flow

**Severity:** HIGH  
**Why it matters:** Without a lobby, players have no way to join, claim a device,
or pick a hero independently. Single-player flows directly from `MainMenu` →
`ClassSelect`. Multiplayer needs an intermediate scene.  
**Affected files:** New `src/ui/lobby_scene.py`, `src/game.py` (scenes dict),
`src/ui/main_menu.py` (routing)  
**What could break:** 1P scene routing if the lobby insertion breaks the existing path.  
**Recommended fix:** Create `LobbyScene` as a new scene. Route `MainMenu` →
`LobbyScene` → `ClassSelect` for multiplayer, keeping `MainMenu` → `ClassSelect`
(or passing through lobby with 1 slot auto-filled) for 1P.  
**Solve before 2P:** Yes — Phase 11.

---

### Issue 8: `ClassSelect` has no duplicate prevention and no slot routing

**Severity:** HIGH  
**Why it matters:** Two players can both pick Knight (no lock-out). The scene
sends `{"hero": self.selected_class}` in `next_scene_kwargs` — a single hero dict
that is incompatible with multi-slot selection.  
**Affected files:** `class_select.py`, `game.py` (scene wiring), `game_scene.py`  
**What could break:** 1P routing if the additive approach is wrong.  
**Recommended fix:** Add optional `slots: list[PlayerSlot]` and `confirmed_slots`
parameters (V2 Phase 3). When absent, use current 1P behavior. When present,
pass slot context; gray out confirmed heroes; route to next unconfirmed slot or
to game when all slots are confirmed.  
**Solve before 2P:** Yes — Phase 11.

---

### Issue 9: Upgrade menu has input bleed — any controller confirms any menu

**Severity:** MEDIUM  
**Why it matters:** When Player 1's upgrade menu is open, Player 2 pressing
their controller's A button posts `K_RETURN`, which `UpgradeMenu.handle_events()`
processes as a confirm action. Player 2 chooses Player 1's upgrade.  
**Affected files:** `upgrade_menu.py`, `game_scene.py` (upgrade queue logic),
`input_manager.py`  
**What could break:** 1P upgrade selection (minimal risk; 1P has one controller
so bleed is same-device).  
**Recommended fix:** Either (a) pass `slot_index` to `UpgradeMenu` and route input
per device, or (b) use sequential menus with a clear visual indicator of whose
turn it is, and route controller input to only the active slot's device. Option (b)
is simpler and sufficient for local co-op.  
**Solve before 2P:** Yes, but can be done in Phase 13 (upgrade queue phase).

---

### Issue 10: Kill credit goes to initial target, not killing blow dealer

**Severity:** MEDIUM  
**Why it matters:** `enemy.py` line 104: `self.target.kill_count += 1`. In
multiplayer, if Player 2 kills an enemy targeting Player 1, Player 1 gets the kill.
This also affects single-player accuracy (though there's only one player so it
doesn't matter in 1P).  
**Affected files:** `enemy.py`, `src/entities/base_entity.py` (optional: add
`last_attacker` there)  
**What could break:** Kill count display in 1P (minimal risk — same player in 1P).  
**Recommended fix:** Add `self.last_attacker: Player | None = None` to
`Enemy.__init__`. Override `take_damage()` in `Enemy` to update `self.last_attacker`
before calling `super().take_damage()`. On death, credit `self.last_attacker`
(fall back to `self.target` if `last_attacker` is None for safety).  
**Solve before 2P:** Can be done in Phase 10 (safe, no gameplay change in 1P).

---

## Biggest Hidden Risks

1. **The upgrade menu input bleed problem is subtle and will be annoying in
   multiplayer.** Any controller's A button confirms any open menu. This interacts
   badly with simultaneous level-ups, where multiple menus would be in the queue
   and any player could dismiss them in any order.

2. **The camera rewrite touches the entire render pipeline.** Background rendering,
   enemy health bars, threat arrows, and sprite drawing all depend on `camera.offset`
   math. Adding zoom multiplies every screen-position calculation. A mistake here
   breaks all world rendering.

3. **Enemy targeting is a coordinated change across 9 files.** Getting it wrong
   in one subclass (especially `LichFamiliar` which has its own orbit + fire logic)
   is easy. The subclasses need individual verification after the base class changes.

4. **XP orb first-come-first-served collection is invisible behavior** that could
   produce confusing results in play (Player 1's XP system consistently wins ties
   because it's always updated first). This needs to be a deliberate design choice
   with explicit code, not a side effect of update order.

5. **The save system has no per-player identity.** If multiplayer runs are tracked
   in the same `progress.json`, all stats are merged. There is no way to distinguish
   which player contributed what. If this matters for the game's progression design,
   it needs to be decided before shipping multiplayer.

---

## Best Next Step

**Implement `PlayerSlot` in `src/core/player_slot.py` exactly as specified in
V2 Section 4.1. Create the `src/core/` directory. Update the project structure
in `CLAUDE.md`. Do not touch any other gameplay file.**

This is Phase 10 Step 1. It is zero-risk (pure addition), makes the dataclass
available for every subsequent phase, forces a concrete commitment to the field
names and types that all other phases will depend on, and gives you something to
verify immediately with `python run_check.py`.

Do not proceed to `InputManager` extensions, `LobbyScene`, or `ClassSelect`
changes until `PlayerSlot` is committed and `run_check.py` passes cleanly.
