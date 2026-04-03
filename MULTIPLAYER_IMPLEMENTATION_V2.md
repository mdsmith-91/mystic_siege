# Local Multiplayer Implementation Guide — V2

Couch co-op for 1–4 players on one machine. Players join a lobby, assign their
own input devices, pick heroes (duplicates blocked), and play simultaneously.
Single-player behavior is completely unchanged. Online multiplayer is explicitly
out of scope for this guide but the architecture is designed to make it feasible later.

---

## 1. Critique of the V1 Guide

The V1 guide is well-structured and realistic for 2-player co-op, but it cannot
scale past two players without significant rework. The problems are:

**Hard-coded 2-player assumptions (see Section 2 for the full list):**
- `PLAYER_COUNT = 1 or 2` is a binary flag, not a slot count
- Named parameters `hero_p1 / hero_p2 / p1_config / p2_config` bake in exactly
  two players throughout the entire call chain from the lobby all the way into
  `GameScene.__init__`
- `ClassSelect` does exactly two sequential passes by checking `player_index == 1`
  or `== 2` and routing accordingly — adding a third player would require another
  hard-coded branch
- The leash mechanic (`if len(alive_players) == 2: p1.pos / p2.pos`) only works
  for exactly two named players
- Camera `update_midpoint` computes a 2-point midpoint; 3+ players need a centroid
- `InputAssignScene` lays out exactly two side-by-side slots
- HUD 2P layout hard-codes P1 left / P2 right with no provision for 3 or 4

**Missing design decisions:**
- No duplicate hero prevention mechanism
- No 3–4 player HUD layout
- No spawn positioning for more than 2 players
- No discussion of what "lobby minimum" is (can 1 player start without waiting
  for a second?)
- Leash is a strong constraint that breaks down conceptually with 3+ players
- No guidance on what to abstract now for future online support

**What works well:**
- Upgrade queue (sequential menus) generalizes to N players cleanly
- Per-player `XPSystem` and `input_config` concepts are correct
- `is_downed` / revive mechanic is sound
- `enemy.py` retargeting sketch in Phase 5 is the right idea

---

## 2. Two-Player Assumptions That Must Be Removed

Every item below must be replaced with a collection-based or slot-based equivalent.

| Location | V1 Assumption | Why It Breaks at 3–4 |
|---|---|---|
| `settings.py` | `PLAYER_COUNT = 1 or 2` | Can't express 3 or 4 |
| `game_scene.py __init__` | `hero_p1, hero_p2, p1_config, p2_config` params | Adding P3 requires a new named param |
| `game_scene.py` | `Player(center ± Vector2(80,0), ...)` — exactly 2 spawn offsets | Third player has no spawn position |
| `game_scene.py` | `self.player` property returns `players[0]` — used as "the" player | Fine as a convenience alias but must not drive logic |
| `class_select.py` | `player_index == 1` → route to pass 2; `player_index == 2` → route to game | Hard-coded terminal condition |
| `class_select.py` | No duplicate prevention | Two players could both pick Knight |
| `input_assign.py` | "Two side-by-side slots" layout | Visual layout doesn't accommodate 3–4 |
| `input_assign.py` | Ready condition: "both slots filled" | "Both" implies exactly 2 |
| `camera.py` | `update_midpoint(positions)` computes 2-point midpoint | Centroid of 3–4 is geometrically different and has a larger bounding box |
| `camera.py` | Fixed `COOP_CAMERA_ZOOM = 0.75` regardless of player spread | 4 players at opposite corners need a much wider view |
| `game_scene.py` | `_enforce_coop_constraints`: leash `p1.pos / p2.pos` named directly | Leash is undefined for 3 players |
| `hud.py` | `P1 left / P2 right` hard-coded positions | No layout for 3–4 |
| `collision.py` | `check_all(player, ...)` singular | Already fixed in V1 but the call sites in `game_scene` still pass a single player |
| `wave_manager.py` | `_nearest_alive_player` is in the right direction but spawning only offsets from a single midpoint | Fine for 2, but spawn spread for 4 players near opposite corners is wrong |
| `upgrade_menu.py` | `player_index + 1` label — works for N but assumes a display order | Correct approach; no change needed |

---

## 3. Revised Multiplayer Design Principles

1. **Player slots, not player count.** A `PlayerSlot` object binds together:
   slot index, hero data, input config, and UI identity metadata such as color.
   Runtime combat state such as alive/downed/revive progress belongs on the
   `Player` sprite, not the slot dataclass.
   Game systems iterate over `active_slots: list[PlayerSlot]`; they never check
   `PLAYER_COUNT` directly.

2. **Single-player is a lobby of one.** The long-term architecture is: the lobby
   always produces exactly one joined slot with a concrete `input_config`, even
   for 1P. During migration, `input_config=None` may remain as a temporary legacy
   compatibility shim for the old single-player path, but it should not remain the
   final lobby output shape. No special-casing, no `if PLAYER_COUNT == 1` guards.

3. **Separate the concepts.**
   - *Slot index*: 0–3, stable across the session, used for UI positioning.
   - *Player identity*: the `Player` sprite instance.
   - *Hero choice*: the hero data dict; locked at lobby close; duplicates blocked.
   - *Input device*: the `input_config` dict; chosen at lobby; can differ from
     hero choice.

4. **Collections everywhere.** Every system receives `players: list[Player]` or
   `slots: list[PlayerSlot]`. Named variables `p1` / `p2` / `hero_p1` / `hero_p2`
   are forbidden outside the lobby itself.

5. **Closest-enemy targeting.** Enemies pick the nearest living `Player` on every
   targeting decision. No sticky assignment; no hard-coded "player 1 is the target".

6. **Camera adapts to player count and spread.**
   - 1 player: standard single-player follow camera, no zoom change.
   - 2 players: centroid follow with mild zoom-out (0.75–0.85x depending on spread).
   - 3–4 players: dynamic zoom-out based on bounding box of all alive players, with
     a minimum zoom floor so the world doesn't become unreadable. Hard leash is
     **removed** in favor of soft zoom (see Section 4.3).

7. **Lobby minimum is 1.** The game can start with any number of joined players
   from 1 to 4. There is no mandatory second player.

8. **Hero selection may be simultaneous later, but the first implementation should
   be sequential.** The current repo already has a `ClassSelect` scene and a cached
   `SceneManager` flow. A slot queue through recreated `ClassSelect` scenes is the
   lowest-risk path for the first implementation. A fully simultaneous lobby-driven
   hero picker can be a later polish pass.

9. **Upgrades are sequential but clearly labeled.** When multiple players level up
   at the same time, a queue shows each menu one at a time. Each menu header names
   the player (`PLAYER 2 — LEVEL UP!`). All players are paused during any upgrade
   menu.

10. **Don't touch working code.** The XP system, orb collection, weapon mechanics,
    enemy behavior, and save system require only targeted changes. The goal is
    surgical abstraction, not a rewrite.

---

## 4. Revised Architecture Overview

### 4.1 PlayerSlot — The Central Abstraction

```python
# In settings.py or a new src/core/player_slot.py (simple dataclass, no pygame dependency)
from dataclasses import dataclass, field

@dataclass
class PlayerSlot:
    index: int                    # 0–3, stable for the session
    input_config: dict | None     # None only as a temporary 1P migration shim
    hero_data: dict | None = None # set during hero selection; None until locked
    color: tuple = (255, 255, 255)# player color badge used in UI
```

`PlayerSlot` is a plain data container. It is created in the lobby and passed
through the scene chain into `GameScene`. It is NOT a pygame sprite, and it does
not own runtime combat state such as HP, downed status, or revive progress.

The `Player` sprite receives its `PlayerSlot` at construction and stores a
reference back to it (`self.slot = slot`). This lets HUD, camera, and upgrade
menus look up slot metadata without coupling to the sprite internals.

### 4.2 Scene Flow

```
MainMenu
  └── LobbyScene (new — replaces InputAssignScene)
        Handles: join/leave, input assignment, device claims, start readiness
        Produces: list[PlayerSlot] with input_config filled
        ──→ ClassSelect (recreated once per joined slot)
              Handles: hero selection, duplicate prevention
              Produces: list[PlayerSlot] with all hero_data filled
              ──→ GameScene(slots: list[PlayerSlot])
                    ──→ GameOverScene (aggregated stats)
                          ──→ MainMenu
```

For the first implementation, `LobbyScene` replaces only the V1 `InputAssignScene`.
Hero selection stays in `ClassSelect`, but is routed through an N-slot queue
instead of the V1 two-pass branch chain. This is the lowest-risk path because it
reuses the existing scene and avoids combining lobby state, hero cursors, and
device assignment into one large new UI.

A fully integrated lobby-driven hero picker is still a valid later polish pass,
but it is not the recommended first architecture for this repo.

### 4.3 Camera Strategy

| Player count | Strategy | Notes |
|---|---|---|
| 1 | Existing single-player follow camera | Zero change |
| 2 | Centroid follow, zoom 0.80x | Very similar to V1 |
| 3–4 | Centroid follow, dynamic zoom | Zoom = `min(1.0, SCREEN_H / (bbox_h + MARGIN)) clamped to [ZOOM_MIN, 1.0]` |

**Why remove the hard leash for 3–4 players:**
The V1 leash pushes both players back when they separate. With 3 players this
becomes ambiguous (push which two back?). With 4 it breaks completely. A dynamic
zoom-out lets players spread further without a hard mechanical constraint, which
is also less frustrating. If the spread exceeds `ZOOM_MIN` * screen size, you
simply cannot see further — natural soft limit.

**Zoom floor (`ZOOM_MIN = 0.5`):** below 0.5x sprites are too small to read.
If all alive players are alive but very far apart, this is a gameplay consequence,
not a crash or bug.

**For 2 players only**, the optional soft leash can remain as a gameplay nudge
(a screen-edge warning, not a hard push) but it should not be the camera mechanism.

### 4.4 Input Assignment Model

```python
# Keyboard WASD — slot 0 default
{"type": "keyboard", "scheme": "wasd",
 "keys": {"up": K_w, "down": K_s, "left": K_a, "right": K_d, "confirm": K_RETURN}}

# Keyboard Arrows — slot 1 default
{"type": "keyboard", "scheme": "arrows",
 "keys": {"up": K_UP, "down": K_DOWN, "left": K_LEFT, "right": K_RIGHT, "confirm": K_RETURN}}

# Controller — one per joystick instance ID
{"type": "controller", "joystick_id": <int>}

# Temporary legacy 1P migration shim only (not final lobby output)
None
```

Rules:
- Each keyboard scheme (WASD, arrows) can only be claimed by one slot at a time.
- Each joystick instance ID can only be claimed by one slot at a time.
- A slot can be vacated (player leaves lobby before start).
- The lobby shows up to 4 slots. Any slot with no input device is inactive.
- Final target behavior: the lobby emits a concrete `input_config` for every
  joined slot, including 1P. `None` exists only so the migration can preserve
  the pre-lobby single-player path while scenes are being converted.

### 4.5 Hero Selection — Sequential Slot Queue With Duplicate Lock

For the first implementation, joined slots select heroes one at a time through a
recreated `ClassSelect` scene. This keeps the scene flow simple, keeps controller
ownership unambiguous, and avoids a large new shared-cursor UI while the rest of
the multiplayer plumbing is still being built.

The important rule is not "simultaneous"; it is "no hard-coded pass count." The
queue must work the same way for 1, 2, 3, or 4 joined slots.

Implementation options ranked by complexity:
1. **Modified `ClassSelect` driven by a slot queue** (lower risk, recommended for
   first implementation — see Phase 3).
2. **Single `LobbyScene` combining input assignment + hero selection** (one screen,
   left side = input, right side = hero; join then immediately navigate to a hero).
   Most polished; most implementation work.
3. **V1 sequential passes** (only works for exactly 2, already rejected).

Option 1 is recommended for the first implementation pass.

### 4.6 Enemy Targeting

```python
# In enemy.py update():
def _pick_target(self) -> Player | None:
    alive = [p for p in self.player_list if p.is_alive]
    if not alive:
        return None
    return min(alive, key=lambda p: (p.pos - self.pos).length_squared())
```

Called when:
- Enemy spawns (initial target).
- Current target becomes downed or dies.
- Optionally, every N seconds as a cheap retarget sweep (prevents enemies from
  ignoring a player who walks into point-blank range while chasing another).

`player_list` is passed in at construction from `WaveManager`, which holds a
reference to `GameScene`'s player list. No enemy stores a slot index — only a
direct Player reference (which may be replaced on retarget).

**Kill credit attribution:** The current code does `self.target.kill_count += 1`
on death — always crediting the initial target regardless of who dealt the killing
blow. Fix: add `self.last_attacker: Player | None = None` to `Enemy.__init__`.
Override `take_damage()` in `Enemy` to set `self.last_attacker = <the hitting player>`
before calling `super().take_damage()`. On death, credit `self.last_attacker`
(fall back to `self.target` if None). This also makes 1P kill counts more accurate
and is safe to add in Phase 1 (no gameplay regression).

**Important caveat for the current codebase:** the hit pipeline does not currently
pass attacker ownership into `Enemy.take_damage()`. For example, projectiles call
`enemy.take_damage(actual_damage, hit_direction=-self.direction)` in
`src/entities/projectile.py`, and several weapon classes call `enemy.take_damage(...)`
directly. To make kill credit attribution work, the implementation must thread the
attacking `Player` through those call sites or add an equivalent owner field to the
damage source.

### 4.7 HUD Layout for N Players

| Player count | Layout |
|---|---|
| 1 | Existing layout, completely unchanged |
| 2 | P1 top-left, P2 top-right; XP bar split at center |
| 3 | P1 top-left, P2 top-center, P3 top-right; shared XP bar bottom |
| 4 | 2×2 corners: P1 top-left, P2 top-right, P3 bottom-left, P4 bottom-right |

Draw each player's panel using a helper:
```python
def _draw_player_panel(screen, player, xp_system, rect: pygame.Rect, slot: PlayerSlot):
    # Draw HP bar, weapon slots, kill count inside rect
    # If player.is_downed: draw gray HP bar + "DOWNED" label
```

The panel rect is computed from slot index and total active player count.
This is the only place that knows about screen positions.

### 4.8 Downed / Revive / Game Over Rules

- **Downed**: HP hits 0 → sprite stays in groups at low alpha (40), weapons stop,
  `player.is_alive` returns False.
- **Revive**: any living player within `REVIVE_RADIUS` for `REVIVE_DURATION`
  seconds → revived at 50% HP with iframes. Any one rescuer is sufficient.
  Progress decays if the rescuer moves away.
- **Game over**: all `PlayerSlot`s have either a downed or dead player AND no one
  can revive them (all downed simultaneously, or last player dies outright in 1P).
- **1P game over**: existing behavior unchanged — `player.dying` → fade → kill.

**Critical prerequisite in the current repo:** this cannot be implemented only by
changing `Player.update()`. `BaseEntity.take_damage()` currently calls `self.kill()`
immediately when HP reaches 0, so a player would be removed from sprite groups before
any downed/revive state could begin. The implementation must intercept lethal damage
before `BaseEntity.kill()` runs, either by overriding `Player.take_damage()` or by
changing the base damage/death flow.

### 4.9 Pause / Menu Behavior

- Any player pressing ESC pauses the game. The pause menu is navigated by any input.
- Upgrade menus pause all players. The queuing mechanism from V1 is correct.
- During upgrade menu: other players' input is consumed (read and discarded) so
  buttons don't bleed into the menu navigation.

**Current InputManager limitation:** this repo's synthetic controller events are
posted as plain `KEYDOWN` / `KEYUP` events with no joystick instance ID attached.
That means menu code cannot reliably tell which controller generated a `K_RETURN`
or `K_ESCAPE`. Owned multiplayer menus therefore require one of two changes:
1. Preserve device metadata on synthetic events, using a custom event payload.
2. Bypass synthetic menu events for owned menus and poll the assigned device directly.
Without one of those, "filter by source device" is not implementable.

### 4.10 Device Disconnect / Hot-Plug

- Controller disconnect mid-game: the player's `input_config` remains set to the
  disconnected joystick ID. Movement returns `(0.0, 0.0)`, confirm returns False.
  The player stops moving. A small HUD icon can indicate the disconnection.
- Reconnect: `InputManager.update()` already handles `JOYDEVICEADDED`, and startup
  enumeration is done by `InputManager.scan()` in `main.py`. If the same physical
  controller reconnects with the same instance ID, input resumes automatically.
- Keyboard "disconnect" is not possible; no handling needed.

### 4.11 Open Decisions To Lock Before Release

These do not block Phase 1, but they should be decided explicitly before
multiplayer ships so behavior is intentional rather than accidental.

- **XP orb policy:** shared first-come-first-served is acceptable, but if kept,
  document the tie-break rule and whether update order bias is acceptable.
- **Balance scaling:** decide whether player count scales spawn rate, enemy HP,
  elite thresholds, or some combination.
- **Player body collision:** decide whether players can overlap freely or need soft
  separation during spawn and movement.
- **Save aggregation:** decide how multiplayer runs contribute to shared
  meta-progression totals in `saves/progress.json`.
- **Reconnect policy:** document what happens if a controller reconnects with a
  different joystick instance ID than the one originally claimed.
- **Player readability:** choose one visual distinction strategy now
  (recommended: colored ground ring plus HUD badge, not sprite tinting).

---

## 5. Revised Phased Implementation Plan

> **Phase numbering note:** These V2 phases (1–8) map to the project's CLAUDE.md
> numbered phases (10–14) as follows:
>
> | V2 Phase | CLAUDE.md Phase | Topic |
> |---|---|---|
> | 1 | 10 | Foundation: PlayerSlot + Input Abstraction |
> | 2–3 | 11 | Lobby Scene + Hero Selection (ClassSelect slot queue) |
> | 4 | 12 | GameScene Core Refactor |
> | 5–7 | 13 | World Systems, Camera, HUD, Revive |
> | 8   | 14 | Integration Test + Polish |

### Phase 1 — Foundation: PlayerSlot + Input Abstraction
**Goal:** Introduce `PlayerSlot`, generalize `Player._read_input()`, add per-joystick
InputManager methods. Zero gameplay change.

**Files:** `settings.py` (or new `src/core/player_slot.py`), `src/utils/input_manager.py`,
`src/entities/player.py`

Changes:
1. Define `PlayerSlot` dataclass (index, input_config, hero_data, color).
2. Add `MAX_PLAYERS = 4` and player color palette to `settings.py`.
3. Add per-joystick InputManager methods:
   - `get_movement_for_joystick(joystick_id: int) -> tuple[float, float]`
   - `get_confirm_for_joystick(joystick_id: int) -> bool`
   - `get_connected_joysticks() -> list[int]`
   Keep `get_movement()` unchanged for backward compatibility.
4. In `Player.__init__`: add `slot: PlayerSlot | None = None` parameter.
   Store `self.slot = slot`. If `slot` is None, behavior is exactly 1P legacy.
5. `Player._read_input()`: dispatch on `self.slot.input_config if self.slot else None`.
6. Add `self.is_downed = False` and `self.revive_timer = 0.0`.
7. **Override** `is_alive` in `player.py` (it already exists in `BaseEntity` as
   `return self.alive()`, but that returns `True` for downed players since they
   stay in sprite groups). The override in `player.py` must be:
   `return self.alive() and not self.is_downed`.
8. Death trigger during migration: if `slot` is not `None`, go downed instead of
   dying. If `slot` is `None` (temporary legacy 1P shim), keep existing dying
   behavior unchanged. Once the lobby path is authoritative for 1P too, this
   branch should be revisited so behavior is keyed on game mode/state rather than
   "slot exists vs does not exist".
9. Do not rely on `Player.update()` alone for downed state. The implementation must
   intercept lethal damage before `BaseEntity.take_damage()` removes the sprite from
   its groups.

**Regression risk:** Low. All changes are additive. 1P path taken when `slot=None`.

**Verification:** `python run_check.py`. Start game normally in 1P — must be identical.

---

### Phase 2 — Lobby Scene
**Goal:** New `LobbyScene` replaces `InputAssignScene`. Supports 1–4 player slots.
Produces a `list[PlayerSlot]` passed to the class selection chain.

**Files:** `src/ui/lobby_scene.py` (new), `src/scene_manager.py`, `src/ui/main_menu.py`

Changes:
1. Create `LobbyScene`:
   - Show up to 4 slots in a clear 2×2 grid.
   - Each slot starts as "Press any key/button to join".
   - Press any key/button → claims the slot with that device's `input_config`.
   - Press ESC / same button again → vacates the slot.
   - Conflict (device already taken): brief flash "Already taken".
   - Minimum 1 player to start.
   - A joined slot is implicitly ready once it has claimed a device.
   - "Press ENTER or any controller button to start" appears when at least 1 slot
     is filled. Starting begins a run with exactly the currently joined slots.
   - On start: produce `filled_slots: list[PlayerSlot]` for all claimed slots.
   - Assign stable slot indices (0–3) based on join order.
   - Assign default player colors from `PLAYER_COLORS` constant in `settings.py`.
   - `next_scene = STATE_CLASS_SELECT`, `next_scene_kwargs = {"slots": filled_slots}`.

2. In `SceneManager`: register `LobbyScene`. Add to always-create-fresh set.

3. In `settings.py`: add `STATE_LOBBY = "lobby"`.

4. In `MainMenu`: route "New Run" → `STATE_LOBBY` (not directly to `STATE_CLASS_SELECT`).

**Note on 1P path:** A single player joining and pressing start goes through the
lobby just like 2–4 players. The lobby with one slot is visually simple and does
not feel like overhead. This unifies the path and removes the `if PLAYER_COUNT >= 2`
branch that existed in V1's `main_menu.py`.

**Regression risk:** Low if the lobby gracefully produces a 1-slot list that feeds
into the existing `ClassSelect` → `GameScene` chain unchanged.

**Verification:** `python run_check.py`. Test 1 player through lobby → hero select →
game. Should be identical to pre-multiplayer 1P.

---

### Phase 3 — Hero Selection: Slot Queue
**Goal:** Route each slot through `ClassSelect` in sequence, preventing duplicate picks,
producing fully-resolved `PlayerSlot` list before entering `GameScene`.

**Files:** `src/ui/class_select.py`

Changes:
1. Modify `ClassSelect.__init__` to accept:
   ```python
   slots: list[PlayerSlot]           # all slots yet to pick
   confirmed_slots: list[PlayerSlot] # slots that have already picked
   ```
   Drop `player_index / hero_p1 / hero_p2 / p1_config / p2_config` entirely.

2. Current slot = `slots[0]`. Header: `f"PLAYER {current_slot.index + 1} — CHOOSE YOUR HERO"`.

3. Navigate using `current_slot.input_config` (dispatch same as `Player._read_input`).
   **Scene lifecycle requirement:** the current `SceneManager` caches `ClassSelect`.
   For slot-queue routing to work, `STATE_CLASS_SELECT` must be recreated fresh on
   every transition or explicitly reinitialized with the new kwargs. Without that,
   later queue passes will reuse stale scene state.

   **Input bleed risk:** The current `handle_events()` loop processes `K_RETURN` from
   the global event queue, and `InputManager` strips source device information when
   it posts synthetic key events. For controller-owned slot selection, do not rely on
   filtering plain `K_RETURN` events by source. Instead, either preserve `instance_id`
   in custom synthetic events or poll the assigned controller directly during this scene.

4. **Duplicate prevention:** collect `{slot.hero_data['name'] for slot in confirmed_slots}`.
   Render locked-out heroes with a gray overlay and the name of the player who
   picked them. Keyboard/controller cannot land on or confirm a locked hero.

5. On confirm:
   - Set `current_slot.hero_data = self.selected_class`.
   - remaining = `slots[1:]`
   - If remaining is non-empty:
     ```python
     self.next_scene = STATE_CLASS_SELECT
     self.next_scene_kwargs = {
         "slots": remaining,
         "confirmed_slots": confirmed_slots + [current_slot]
     }
     ```
   - If remaining is empty (last player):
     ```python
     self.next_scene = STATE_PLAYING
     self.next_scene_kwargs = {
         "slots": confirmed_slots + [current_slot]
     }
     ```

6. The 1P path works without special-casing: a single-slot list with `confirmed_slots=[]`
   follows the same code path as any other slot count — selects, remaining is empty,
   routes to game. No `PLAYER_COUNT` check needed.

**Why a queue, not a count:** adding a 4th player requires no code change — the
`slots` list just has 4 items. The routing logic is the same regardless.

**Regression risk:** Medium. `ClassSelect` is modified; test 1P and 2P thoroughly.

**Verification:** 1P: lobby → hero select → game. 2P: two sequential selects with
duplicate blocked on second pass. 4P: four sequential selects.

---

### Phase 4 — GameScene Core Refactor
**Goal:** `GameScene` accepts `slots: list[PlayerSlot]`, creates N players with
correct spawn positions, per-player XP systems, and upgrade queue.

**Files:** `src/game_scene.py`

Changes:
1. Change `__init__` signature to `def __init__(self, slots: list[PlayerSlot])`.
   For backward compatibility during transition, keep a shim:
   ```python
   # Temporary shim — remove after all scenes updated
   if "hero" in kwargs:
       from src.core.player_slot import PlayerSlot
       slots = [PlayerSlot(index=0, input_config=None, hero_data=kwargs["hero"])]
   ```

2. Spawn positions for N players:
   ```python
   center = Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
   SPAWN_OFFSETS = [
       Vector2(-80,   0),   # slot 0
       Vector2( 80,   0),   # slot 1
       Vector2(  0,  80),   # slot 2
       Vector2(  0, -80),   # slot 3
   ]
   self.players: list[Player] = []
   for slot in slots:
       offset = SPAWN_OFFSETS[slot.index]
       p = Player(center + offset, slot.hero_data,
                  (self.all_sprites, self.player_group),
                  slot=slot)
       self.players.append(p)
   ```
   Move `SPAWN_OFFSETS` to `settings.py`.

3. Keep `@property def player(self) -> Player: return self.players[0]` as a
   convenience alias for 1P-legacy code paths that still reference it. Audit and
   remove these references over time.

4. Per-player XP systems: `self.xp_systems: list[XPSystem] = [XPSystem() for _ in self.players]`

5. Upgrade queue: iterate `zip(self.players, self.xp_systems)`.
   Queue is a `list[UpgradeMenu]`; pop front when `active_upgrade_menu` is cleared.

6. Win/loss: `all(not p.is_alive for p in self.players)`.

7. Starting weapons: loop over `self.players`, init weapon from `slot.hero_data`.

8. Camera update: pass `[p.pos for p in self.players if p.is_alive]` — see Phase 5.

9. Weapon draw loop: loop over `self.players`.

10. HUD and collision: pass `self.players` as lists.

11. `LevelUpEffect`: use the leveling player's position, not a hardcoded `self.player.pos`.
    In the upgrade queue iteration, pass `p.pos` (the current player being leveled)
    when creating the `LevelUpEffect`.

12. Update `SceneManager` to instantiate `GameScene` and `ClassSelect` with kwargs
    in this new flow. The current `ClassSelect()` call with no kwargs is not enough.

**Regression risk:** High — this is the central file. Test 1P after every change.

**Verification:** `python run_check.py`. 1P: full run identical. 2P: both players spawn, move independently.

---

### Phase 5 — World Systems
**Goal:** Camera supports N players with dynamic zoom; WaveManager and enemies use
player list; collision loops over players.

**Files:** `src/systems/camera.py`, `src/systems/wave_manager.py`,
`src/entities/enemy.py`, `src/systems/collision.py`

**5a. Camera — dynamic zoom**

```python
# New method (replaces update_midpoint):
def update_multi(self, positions: list[Vector2], dt: float):
    if not positions:
        return
    if len(positions) == 1:
        self.update(positions[0], dt)   # existing 1P path
        return

    # Centroid
    centroid = sum(positions, Vector2()) / len(positions)

    # Bounding box of all players
    xs = [p.x for p in positions]
    ys = [p.y for p in positions]
    bbox_w = max(xs) - min(xs) + CAMERA_PLAYER_MARGIN
    bbox_h = max(ys) - min(ys) + CAMERA_PLAYER_MARGIN

    # Zoom so the bounding box fits the screen
    zoom_x = SCREEN_WIDTH  / bbox_w
    zoom_y = SCREEN_HEIGHT / bbox_h
    target_zoom = max(CAMERA_ZOOM_MIN, min(1.0, min(zoom_x, zoom_y)))

    # Lerp zoom toward target
    self.zoom += (target_zoom - self.zoom) * CAMERA_ZOOM_LERP * dt

    # Follow centroid
    target_offset = centroid - Vector2(SCREEN_WIDTH, SCREEN_HEIGHT) / (2 * self.zoom)
    self.offset += (target_offset - self.offset) * self.lerp_speed * dt
    # Clamp to world bounds
    ...
```

The `apply()` method must also be updated to incorporate zoom. The current
implementation is `entity.rect.move(-self.offset)` (a pure pan). With zoom,
every world-space position must be scaled before subtracting the offset:

```python
def apply(self, entity) -> pygame.Rect:
    # Scale entity position by zoom, then offset to screen space
    world_x = entity.rect.centerx
    world_y = entity.rect.centery
    screen_x = int((world_x - self.offset.x) * self.zoom)
    screen_y = int((world_y - self.offset.y) * self.zoom)
    w = int(entity.rect.width  * self.zoom)
    h = int(entity.rect.height * self.zoom)
    return pygame.Rect(screen_x - w // 2, screen_y - h // 2, w, h)
```

**Draw pipeline impact:** The `game_scene.py` draw section currently blits sprites
using `camera.apply(sprite)` for screen position but draws sprites at their
original (unscaled) size. With zoom < 1.0 that is wrong — sprites must also be
scaled. Two options:
- **Scale each sprite at draw time:** `pygame.transform.scale(sprite.image, (w, h))`
  applied in the draw loop. Simple but expensive at 60 fps with many sprites.
- **Scale the world surface:** render all world-space sprites onto an off-screen
  surface at 1:1, then `pygame.transform.scale` the entire surface to
  `(SCREEN_WIDTH * zoom, SCREEN_HEIGHT * zoom)` and blit to screen. One scale per
  frame regardless of entity count. Recommended.

Background tile rendering (`game_scene.py` lines 298–308) uses raw `camera.offset`
math directly and must also be updated to account for `camera.zoom`. Enemy health
bars (`draw_health_bar()` in `base_entity.py`) compute screen positions from
`self.rect` and `offset` — these will be wrong until the draw pipeline is unified.
Threat arrows in `hud.py` already use `camera.offset` for screen-boundary math and
must be rechecked after zoom is added.

Add to `settings.py`:
```python
CAMERA_ZOOM_MIN    = 0.45    # floor; sprites still readable
CAMERA_ZOOM_LERP   = 2.0     # zoom smoothing speed
CAMERA_PLAYER_MARGIN = 200   # padding around bounding box (pixels)
```

**Note:** `COOP_CAMERA_ZOOM` and `COOP_LEASH_DISTANCE` were V1 design artifacts that
were never added to `settings.py`. Do not add them; just do not create them.

**5b. WaveManager**

- Accept `player_list: list[Player]` (not a single player or an `isinstance` check).
- `_nearest_alive(pos: Vector2) -> Player | None`: returns closest alive player.
- Pass `player_list` (not a single target) to every enemy constructor.
- Spawn positions: offset from centroid of alive players.

**5c. Enemy**

- Accept `player_list: list[Player]` in `__init__`. Store as `self.player_list`.
  Set `self.target = self._pick_target()` at the end of `__init__`.
- **All 7 enemy subclasses** (`skeleton.py`, `dark_goblin.py`, `wraith.py`,
  `plague_bat.py`, `cursed_knight.py`, `lich_familiar.py`, `stone_golem.py`)
  override `__init__` and pass `target` to `super().__init__()`. Each one must be
  updated: rename the `target` parameter to `player_list` and pass `player_list`
  through to `super().__init__()`. The subclasses' `update()` methods that reference
  `self.target` do **not** need changes — they will automatically use the updated
  target set by `_pick_target()` in the parent class.
- `_pick_target()`: `min(alive, key=lambda p: (p.pos - self.pos).length_squared())`.
- Call `_pick_target()` at spawn and whenever current target is downed/dead.
- Optional periodic retarget every 2 seconds (cheap `length_squared` comparison).
- **Kill credit:** add `self.last_attacker: Player | None = None`. Update in
  `take_damage()` (override in `Enemy`, update `self.last_attacker` before calling
  `super().take_damage()`). On death, credit `self.last_attacker` with the kill;
  fall back to `self.target` if `last_attacker` is None.
- Because current damage calls do not pass attacker ownership, this phase must also
  thread attacker references through projectile and weapon hit paths.
- **`LichFamiliar` special case:** this subclass orbits `self.target.pos` and fires
  at `self.target`. Verify after the base class change that `self.target` is still
  being updated by `_pick_target()` and that orbit/fire logic in `lich_familiar.py`
  uses `self.target` (not a locally cached copy). No other change should be needed.

**5d. Collision**

- `check_all(players: list[Player], ...)` — already proposed in V1, confirmed here.
- Inner loop: `for player in players: if player.is_alive: ...`

**Regression risk:** Camera change affects rendering for everyone. Test 1P carefully —
`len(positions) == 1` must take the existing path with `self.zoom = 1.0`.

---

### Phase 6 — Revive Mechanic
**Goal:** Downed/revive works for any number of players.

**Files:** `src/game_scene.py`

```python
def _update_revive(self, dt: float):
    downed  = [p for p in self.players if p.is_downed]
    alive   = [p for p in self.players if p.is_alive]

    for pd in downed:
        # Check if any living player is close enough
        rescuer = next(
            (pl for pl in alive if (pl.pos - pd.pos).length() <= REVIVE_RADIUS),
            None
        )
        if rescuer:
            pd.revive_timer += dt
            if pd.revive_timer >= REVIVE_DURATION:
                pd.hp = pd.max_hp * 0.5
                pd.is_downed = False
                pd.image.set_alpha(255)
                pd.iframes = 2.0
                pd.revive_timer = 0.0
        else:
            pd.revive_timer = max(0.0, pd.revive_timer - dt)

    # Game over: everyone is downed or dead with no one to revive
    if downed and not alive:
        self._trigger_gameover()
```

Note: `downed and not alive` is the correct condition — "all downed simultaneously
with no living rescuer". This works for 1, 2, 3, or 4 players without modification.

**Soft leash (optional, 2P only):** If desired, a screen-edge warning (flashing arrow
toward the other player) can remain as a gameplay nudge without any hard position
correction. This is purely cosmetic and does not affect correctness.

---

### Phase 7 — HUD Scaling
**Goal:** HUD draws correctly for 1–4 players.

**Files:** `src/ui/hud.py`

Changes:
1. Change signature: `draw(screen, players, xp_systems, wave_manager, show_fps, fps, camera)`.
   Pass `camera` so revive arcs can be drawn in screen space.

2. Compute panel rects from `len(players)` and `slot.index`. Define the layout in
   `hud.py` (not `settings.py` — `pygame.Rect` objects require a pygame import that
   doesn't belong in `settings.py`). If you want the raw numbers in `settings.py`,
   store them as plain tuples and convert to `pygame.Rect` inside `hud.py`:

   ```python
   # In settings.py — plain tuples, no pygame import needed
   HUD_PANEL_TUPLES = {
       1: { 0: (10, 10, 300, 80) },
       2: { 0: (10, 10, 280, 80),
            1: (SCREEN_WIDTH-290, 10, 280, 80) },
       3: { 0: (10, 10, 220, 70),
            1: (SCREEN_WIDTH//2-110, 10, 220, 70),
            2: (SCREEN_WIDTH-230, 10, 220, 70) },
       4: { 0: (10, 10, 200, 65),
            1: (SCREEN_WIDTH-210, 10, 200, 65),
            2: (10, SCREEN_HEIGHT-75, 200, 65),
            3: (SCREEN_WIDTH-210, SCREEN_HEIGHT-75, 200, 65) },
   }
   # In hud.py — convert at use time
   # rect = pygame.Rect(HUD_PANEL_TUPLES[player_count][slot_index])
   ```

3. `_draw_player_panel(screen, player, xp_sys, rect, slot)` draws one panel.
   Downed: gray HP bar + "DOWNED" text + revive progress arc.

4. 1P path: draws only one panel at the existing position — identical to current HUD.

5. Shared info (wave timer, kill count if you want a combined count) drawn once,
   centered or top-center regardless of player count.

---

### Phase 8 — Integration Test + Polish
**Goal:** End-to-end test of all paths; remove temporary shims; update `GameOverScene`
to accept aggregated multi-player stats.

**Files:** `src/ui/game_over.py`, `src/game_scene.py` (remove shim)

Changes:
1. `GameOverScene`: accept `kills: int, level: int, time: float` as before but
   also optionally `player_results: list[dict]` for a per-player breakdown.
   Render breakdown if more than 1 player.
2. Aggregate stats in `GameScene._trigger_gameover()`:
   ```python
   kills = sum(p.kill_count for p in self.players)
   level = max(xs.current_level for xs in self.xp_systems)
   ```
3. Remove the `hero=` kwarg shim from `GameScene.__init__`.
4. Run full `run_check.py`.

---

## 6. System-by-System Change Recommendations

| File | Change Type | Notes |
|---|---|---|
| `settings.py` | Add constants | `MAX_PLAYERS`, `PLAYER_COLORS`, `SPAWN_OFFSETS`, `CAMERA_ZOOM_MIN`, `CAMERA_ZOOM_LERP`, `CAMERA_PLAYER_MARGIN`, `HUD_PANEL_TUPLES` (plain tuples, not `pygame.Rect`). **Do not add** `PLAYER_COUNT`, `COOP_CAMERA_ZOOM`, or `COOP_LEASH_DISTANCE` — these were V1 artifacts never built. |
| `src/core/player_slot.py` | New file | `PlayerSlot` dataclass. No pygame dependency — importable anywhere. Requires creating `src/core/` directory and updating `CLAUDE.md` project structure. |
| `src/utils/input_manager.py` | Additive | Add 3 per-joystick methods. Existing `get_movement()` unchanged. |
| `src/entities/player.py` | Modify | Add `slot` param, `_read_input()` dispatch, `is_downed`, `revive_timer`. **Override** `is_alive` property (already defined in `BaseEntity` as `self.alive()` — player must override to add `and not self.is_downed`). Death behavior conditioned on `self.slot is not None`. |
| `src/entities/enemy.py` | Modify | Add `player_list`, `_pick_target()`, `last_attacker` kill credit, periodic retarget. |
| `src/entities/enemies/*.py` | `__init__` signature only | All 7 subclasses override `__init__` with a `target` parameter passed to `super().__init__()`. Each must rename `target` → `player_list` and update the `super().__init__()` call. The `update()` methods that reference `self.target` do **not** need changes — `_pick_target()` in the parent keeps `self.target` current. |
| `src/weapons/*.py` | No change | Weapons operate on `self.player` reference already stored at construction. |
| `src/systems/camera.py` | Modify | Add `update_multi()`, `zoom` field, zoom-aware `apply()`. 1P path unchanged via `len==1` branch. |
| `src/systems/wave_manager.py` | Modify | Accept `player_list: list[Player]`, use `_nearest_alive()` for spawn targeting. |
| `src/systems/collision.py` | Modify | `check_all(players: list[Player], ...)` with inner loop. **High regression risk** — `check_all` is the hub for all iframes and damage interactions and has many callers in `game_scene.py`. Change it last within Phase 5, after camera and wave_manager are stable. |
| `src/systems/xp_system.py` | No change | Already stateless per-player, just iterate N instances. |
| `src/systems/upgrade_system.py` | No change | `get_random_choices(player)` already takes a Player reference. |
| `src/game_scene.py` | Major modify | Slot list, player loop, camera `update_multi`, revive method, weapon loop, HUD call. |
| `src/ui/lobby_scene.py` | New file | Replaces `input_assign.py` from V1. 1–4 slot join screen. |
| `src/ui/class_select.py` | Modify | Accept `slots / confirmed_slots` queue. Duplicate hero lock-out. |
| `src/ui/hud.py` | Modify | `_draw_player_panel()`, N-player layout from `HUD_PANEL_TUPLES` (convert tuples to `pygame.Rect` at use time). Remove unused `player` param from `draw_threat_arrows`. |
| `src/ui/upgrade_menu.py` | Minor modify | Header labels from `slot.index`, input dispatch from `slot.input_config`. |
| `src/ui/game_over.py` | Minor modify | Accept optional `player_results` list. |
| `src/ui/main_menu.py` | Minor modify | Route "New Run" to `STATE_LOBBY`. |
| `src/scene_manager.py` | Minor modify | Register `LobbyScene`; always-fresh set. |

---

## 7. Risks and Edge Cases

### 7.1 Regression Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| 1P path broken by `Player(slot=None)` dispatch change | Medium | Test 1P at end of every phase; `slot is None` must take original code path |
| Camera zoom affecting sprite pixel appearance | Low | `pygame.transform.scale` vs `smoothscale` — test that sprites aren't blurry at zoom < 1.0 |
| `class_select.py` queue routing breaks if `ClassSelect` is cached by SceneManager | Medium | Ensure `ClassSelect` is in the always-create-fresh set |
| `GameScene` shim removed too early | Low | Remove shim only after all `ClassSelect` → `GameScene` routes are updated |
| Upgrade menu input bleeds between players | Medium | Explicitly read and discard non-active-player input during upgrade menu |
| `ClassSelect` input bleeds between players during slot-queue hero selection | Medium | Filter `K_RETURN` and navigation events to the current slot's device; discard events from other devices during each selection pass |

### 7.2 Gameplay Edge Cases

- **XP orb collection is first-come-first-served (shared pool).** `xp_orb.py` has no owner binding. Whichever player reaches an orb first collects it. This is the intended co-op design — no per-player binding is required. It means players do not need to race for their "own" orbs, which is friendlier for co-op play. Do not add owner binding without an explicit design decision to change this policy.
- **All players downed within the same frame:** `_update_revive()` checks `downed and not alive` after processing all downed players in one call. Safe.
- **Player dies at exactly `REVIVE_RADIUS` boundary:** use `<=` for inclusive check. Boundary cases feel less frustrating than `<`.
- **4 players, 1 controller, 3 keyboards:** keyboard schemes WASD and arrows only cover 2 of 3 keyboard slots. Third keyboard player cannot join. Document this limit clearly in the lobby UI. Add a "Keyboard IJKL" scheme as a third keyboard option if needed.
- **Camera at ZOOM_MIN with very spread players:** sprites are small but the game remains functional. No crash. Consider a screen-edge indicator showing off-screen players.
- **Hero selection with 4 players and only 3 heroes available:** `ClassSelect` must prevent a situation where a later player has no valid choice. All 6 heroes should be available; document that 4-player co-op requires at least 4 distinct heroes to exist.
- **Level-up queue with 4 players all leveling simultaneously:** all 4 menus queue correctly; game stays paused throughout. With 4 players this can interrupt gameplay for a noticeable duration. Acceptable for now; parallel upgrade menus (4 simultaneous) are a future polish item.
- **Two players with the same keyboard scheme accidentally assigned:** lobby prevents duplicate input config claims, but must also handle the edge case where one slot vacates while another slot is being claimed on the same frame (process events sequentially, not concurrently).
- **Controller re-plugged mid-run:** `InputManager.scan()` on `JOYDEVICEADDED` handles this; instance ID stability depends on the OS. Document that controller reassignment after unplug is best-effort.
- **Revive while downed player is off-screen (4P dynamic zoom):** the downed player's sprite is still in `all_sprites` and processed normally. Proximity check is world-space, not screen-space. No issue.

### 7.3 Complexity Traps to Avoid

- Do not add per-player game timers or separate win conditions. Victory at 30 minutes is shared.
- Do not add separate difficulty scaling per player. All enemies share one global difficulty curve.
- Do not implement split-screen. Shared camera is the practical choice for couch co-op; split screen would require rendering the scene twice and is significantly more complex.
- Do not add AI-controlled players as a "fill slot" option. That is a separate feature with substantial AI work.
- Do not queue upgrade menus non-blocking (showing multiple menus simultaneously). The implementation complexity and UI overlap issues are not worth it at this stage.

---

## 8. Verification Checklist

```
# Import check — run after each phase
python run_check.py

# 1P regression — must be identical to pre-multiplayer at all times
python main.py
  ✓ Menu → Lobby (1 slot) → ClassSelect → Game → full session
  ✓ Player movement, weapons, XP, level-up, game-over all unchanged
  ✓ Camera zoom = 1.0 (no zoom in 1P)
  ✓ save/progress.json written correctly

# 2P co-op
python main.py
  ✓ Lobby: 2 slots claimed with different input devices
  ✓ Conflict: same device claimed twice → "Already taken" flash
  ✓ ClassSelect pass 1: P1 picks hero
  ✓ ClassSelect pass 2: P1's hero shown as locked; P2 cannot pick it
  ✓ Both players spawn at offset positions
  ✓ Each player controlled by their assigned device only
  ✓ Camera follows centroid and zooms out as players separate
  ✓ Dynamic zoom: zoom in when players converge, out when they separate
  ✓ Enemies retarget when current target is downed
  ✓ Each player levels up independently (upgrade menu labels correct player)
  ✓ Sequential upgrade queue: P1 menu → P2 menu (if both level simultaneously)
  ✓ P1 downed → sprite at low alpha, weapons stop
  ✓ P2 revives P1: stand nearby for REVIVE_DURATION → P1 back at 50% HP
  ✓ Both downed simultaneously → game over triggered
  ✓ Victory: combined kill count in game-over screen

# 3P co-op
python main.py
  ✓ Lobby: 3 slots filled
  ✓ Hero selection: 3rd player cannot pick heroes already claimed
  ✓ 3-player HUD top row layout
  ✓ Camera dynamic zoom handles 3-player spread
  ✓ 1 player downed, 2 alive → remaining 2 can revive
  ✓ 2 players downed, 1 alive → single rescuer can run between both

# 4P co-op (if 4 input devices available)
python main.py
  ✓ Lobby: 4 slots filled
  ✓ 4-corner HUD layout
  ✓ ZOOM_MIN floor reached when all 4 players spread to corners
  ✓ 3 players downed simultaneously with 1 alive → game continues

# Edge cases
  ✓ Start lobby, claim 1 slot, start immediately (1P via lobby path)
  ✓ Vacate a slot in lobby after claiming it
  ✓ Controller disconnect mid-run: player freezes, HUD shows disconnect icon
  ✓ python run_check.py clean after all phases complete
```

---

## 9. Future Online Support Preparation

This section describes what to design now so that adding online multiplayer later
is feasible. **Do not implement any networking in this pass.**

### 9.1 The Key Abstraction: Input Becomes a Message

Right now, input is read directly inside `Player._read_input()` by polling
`pygame.key.get_pressed()` or `InputManager`. For online multiplayer, remote
players cannot poll local hardware — their input must arrive as a message.

The `PlayerSlot.input_config` dict is already the right boundary. To support
online players later:
1. Add `{"type": "network", "peer_id": <int>}` as a valid `input_config` type.
2. `Player._read_input()` for a network player reads from a local buffer that the
   network layer fills. The Player sprite doesn't know or care how the buffer was
   populated.
3. The network layer (not designed here) writes `{"dx": float, "dy": float}` into
   this buffer each tick.

No other code changes are needed in the entities layer.

### 9.2 GameScene Tick Authority

For online play, one machine must be authoritative (or you use rollback). The local
multiplayer architecture can be structured to make this easier:
- All game state mutations happen in `GameScene.update(dt)` — already the case.
- `dt` is currently the real frame delta. For online, the authoritative machine
  sets `dt`; clients use the same fixed value. Using a fixed timestep
  (`dt = 1/60`) in future is worth planning for now.
- Avoid storing non-deterministic state (e.g., random floats from `random.random()`
  without a seeded RNG). Switch to `random.Random(seed)` with a shared seed now
  so a future authoritative simulation is deterministic.

### 9.3 Scene Transitions Must Be Serializable

Right now, `next_scene_kwargs` contains Python dicts and `PlayerSlot` dataclasses.
For an online lobby these must be shareable across a network.
- `PlayerSlot` is already a plain dataclass with JSON-safe fields (ints, dicts, tuples).
- Avoid putting `pygame.Surface` or live sprite references in `next_scene_kwargs`.
- Hero data dicts (from `HERO_CLASSES`) are already plain dicts — good.

### 9.4 Enemy Targeting Is Already Network-Friendly

Because enemies pick the nearest alive player on each frame (not a stored index),
retargeting is deterministic given the same world state. No change needed.

### 9.5 What NOT to Future-Proof Now

- Do not add a `NetworkManager` singleton.
- Do not add serialization code.
- Do not add rollback or lag compensation stubs.
- Do not add peer discovery or lobby code.
- Do not add authoritative server logic.

These are large features. Designing their interfaces now without implementing them
adds dead code and confusion. The structural decisions above (input buffer boundary,
deterministic RNG, serializable slot data) are small and low-cost. They are
sufficient preparation for now.

---

## Top 5 Architectural Changes

1. **Replace `hero_p1/hero_p2/p1_config/p2_config` named parameters with
   `slots: list[PlayerSlot]`.** This is the foundational change. Every call chain
   from lobby to hero select to GameScene passes one list, not N named variables.

2. **Introduce `PlayerSlot` as the single source of truth for player identity.**
   Slot index, input config, hero data, and color are bound together. Systems receive
   the slot or the player; they never receive four separate named arguments.

3. **Replace `ClassSelect` sequential two-pass routing with a slot queue.**
   `slots / confirmed_slots` lists generalize to any N without additional code.
   Duplicate prevention is a natural consequence of checking `confirmed_slots`.

4. **Replace the fixed 2-player midpoint camera with `update_multi()` using
   centroid + dynamic zoom.** Remove the hard leash. This is the change that makes
   3–4 players physically possible to see on screen simultaneously.

5. **Remove `PLAYER_COUNT` as a gating constant.** The number of active players is
   always `len(active_slots)`. Systems that check `if PLAYER_COUNT >= 2` become
   checks on the player list length, or disappear entirely because the N=1 and N>1
   paths are unified.

---

## What to Implement First

1. **`PlayerSlot` dataclass** — zero gameplay risk, no visual change, enables
   everything else. Ten lines of code.

2. **`Player.__init__` `slot` parameter + `_read_input()` dispatch** — the 1P
   legacy path (`slot=None`) must work identically. Test this before touching anything else.

3. **`LobbyScene` with 1-slot support** — get the new scene flow working for a single
   player first. If lobby → hero select → game works for 1P, the 2P path is just
   more slots through the same code.

4. **`ClassSelect` slot queue** — once the lobby produces a 1-slot list and routes
   it correctly, extend to 2 slots and test duplicate prevention.

5. **`GameScene` slot list + spawn positions** — the last hard-coded 2-player
   assumption. After this, the engine is truly N-player capable.

Camera, HUD polish, and revive mechanics can follow once the core loop works for
1–4 players.
