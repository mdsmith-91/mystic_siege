# Local Multiplayer Implementation Guide

Couch co-op for 2 players on one machine. Players choose their input device (keyboard-WASD, keyboard-arrows, or any connected controller) at a new Input Assignment screen before hero selection. Both players share a zoomed-out midpoint camera with a leash and can revive each other when downed.

**Single-player is preserved** by `PLAYER_COUNT = 1` in `settings.py` — set to `2` to enable co-op.

---

## Architecture Decisions

| Concern | Decision |
|---|---|
| Camera | Shared midpoint + 0.75x zoom; leash clamps gap at 700px |
| Input routing | `input_config` dict per player (keyboard keys or joystick instance ID) |
| Multiple controllers | Supported; InputManager exposes per-joystick-ID queries |
| XP/upgrades | Separate per player; orb contention already handled by `orb.collected` flag |
| Upgrade menus | Sequential queue (P1 picks → P2 picks); both paused, cards use 1/2/3 keys |
| Hero selection | Two sequential passes through existing `ClassSelect` scene |
| Death | Revive mechanic — ghost at alpha 40, 3s proximity revive at 50% HP |
| Game over | Fires when both players are downed simultaneously (no one left to revive) |

### Input Config Format
```python
# Keyboard WASD
{"type": "keyboard", "keys": {"left": K_a, "right": K_d, "up": K_w, "down": K_s, "confirm": K_RETURN}}

# Keyboard Arrows
{"type": "keyboard", "keys": {"left": K_LEFT, "right": K_RIGHT, "up": K_UP, "down": K_DOWN, "confirm": K_RETURN}}

# Controller (tracked by pygame instance ID, stable per session)
{"type": "controller", "joystick_id": <int>}

# 1P fallback (None = current combined WASD+arrows+controller0 behavior)
None
```

---

## Phase 1 — Foundation
**Scope:** Constants, per-joystick InputManager methods, Player `input_config` + `is_downed`

**Files:** `settings.py`, `src/utils/input_manager.py`, `src/entities/player.py`

```
Implement Phase 1 of local multiplayer for Mystic Siege.

1. In settings.py, add these constants at the bottom:
   PLAYER_COUNT = 1
   COOP_LEASH_DISTANCE = 700
   COOP_CAMERA_ZOOM = 0.75
   REVIVE_RADIUS = 80
   REVIVE_DURATION = 3.0
   STATE_INPUT_ASSIGN = "input_assign"

2. In src/utils/input_manager.py, add three new methods:
   - get_movement_for_joystick(joystick_id: int) -> tuple[float, float]
     Returns left-stick axis for the specific pygame joystick instance ID.
     Returns (0.0, 0.0) if not connected. Apply CONTROLLER_DEADZONE.
   - get_confirm_for_joystick(joystick_id: int) -> bool
     Returns True if button 0 is currently pressed on that joystick.
   - get_connected_joysticks() -> list[int]
     Returns a list of instance IDs for all currently-connected joysticks.
   Keep get_movement() as an alias for backward compatibility.

3. In src/entities/player.py:
   - Add input_config: dict = None to __init__ (after groups param).
     Store as self.input_config = input_config.
   - Add self.is_downed = False and self.revive_timer = 0.0.
   - Add an is_alive property override:
       @property
       def is_alive(self):
           return self.alive() and not self.is_downed
     (The sprite stays in groups while downed, so self.alive() alone is incorrect.)
   - Extract a _read_input(self) -> Vector2 method from update():
     - If self.input_config is None (1P): read WASD + arrows + InputManager.get_movement()
       (identical to current behavior — no regression)
     - If type == "keyboard": read only the keys in input_config["keys"]
     - If type == "controller": call InputManager.get_movement_for_joystick(config["joystick_id"])
   - Replace the inline keyboard block in update() with direction = self._read_input()
   - Change the death trigger (the "if self.hp <= 0 and not self.dying" block):
     - When PLAYER_COUNT >= 2: set self.is_downed = True, self.image.set_alpha(40),
       play PLAYER_DEATH sound — do NOT set dying or call kill() (sprite must stay in groups)
     - When PLAYER_COUNT == 1: existing behavior unchanged (dying = True → fade → kill)
   - In update(), after the death trigger check, add:
       if self.is_downed:
           return  # skip movement, regen, and weapon updates

Run python run_check.py to verify no import errors.
```

---

## Phase 2 — Input Assignment Scene + Routing
**Scope:** New InputAssign scene; SceneManager wiring; MainMenu routing

**Files:** `src/ui/input_assign.py` (new), `src/scene_manager.py`, `src/ui/main_menu.py`

```
Implement Phase 2 of local multiplayer for Mystic Siege: the Input Assignment screen
and scene routing changes.

1. Create src/ui/input_assign.py — a new scene class InputAssignScene.
   Layout: two side-by-side slots ("PLAYER 1" left, "PLAYER 2" right), each showing
   "Press any key or button to join" until claimed.

   Claim logic (listen to pygame events):
   - KEYDOWN with key in {K_w, K_a, K_s, K_d} → builds keyboard-WASD config; assigns
     to next open slot; rejects if the other slot already holds keyboard-WASD
   - KEYDOWN with key in {K_UP, K_DOWN, K_LEFT, K_RIGHT} → keyboard-arrows config
   - JOYBUTTONDOWN → controller config using event.instance_id; rejects if already taken
   - Claimed slot shows device name (e.g. "Keyboard (WASD)" or the joystick.get_name())
     and player color badge
   - "Already taken" flash for 1 second on conflict

   Ready: once both slots are filled, show "Press ENTER or any controller button to start".
   On confirm:
     self.next_scene = STATE_CLASS_SELECT
     self.next_scene_kwargs = {
         "player_index": 1,
         "p1_config": <config for slot 1>,
         "p2_config": <config for slot 2>,
     }

2. In src/scene_manager.py:
   - Import InputAssignScene from src.ui.input_assign
   - Add STATE_INPUT_ASSIGN to self.scenes dict (initial value None)
   - Add STATE_INPUT_ASSIGN and STATE_CLASS_SELECT to the always-create-fresh set
     (currently only STATE_PLAYING and STATE_GAMEOVER are in that set)
   - In the scene creation block, add:
       elif scene_name == STATE_INPUT_ASSIGN:
           self.scenes[scene_name] = InputAssignScene()
   - Change ClassSelect instantiation from ClassSelect() to ClassSelect(**kwargs)

3. In src/ui/main_menu.py:
   - Import PLAYER_COUNT and STATE_INPUT_ASSIGN from settings
   - Wherever next_scene is set to "class_select" (New Run button, keyboard confirm),
     change to:
       self.next_scene = STATE_INPUT_ASSIGN if PLAYER_COUNT >= 2 else "class_select"

Run python run_check.py to verify no import errors.
```

---

## Phase 3 — Class Selection Two-Pass
**Scope:** ClassSelect accepts `player_index`, `hero_p1`, `p1_config`, `p2_config`; relays kwargs between passes

**Files:** `src/ui/class_select.py`

```
Implement Phase 3 of local multiplayer for Mystic Siege: two-pass hero selection.

Modify src/ui/class_select.py:

Add four optional parameters to __init__:
  player_index: int = 1
  hero_p1: dict = None
  p1_config: dict = None
  p2_config: dict = None

When PLAYER_COUNT >= 2:
- Change the title/header to f"PLAYER {player_index} — CHOOSE YOUR HERO"
- Navigate with the current player's input config:
  - If p1_config (player_index == 1) or p2_config (player_index == 2) is type "controller":
    use InputManager.instance().get_confirm_for_joystick(config["joystick_id"]) to detect confirm
    (D-pad/stick synthetic key events from InputManager already handle navigation)
  - If type "keyboard": listen for the config's confirm key in KEYDOWN events
- On confirm:
  - If player_index == 1:
      self.next_scene = STATE_CLASS_SELECT
      self.next_scene_kwargs = {
          "player_index": 2,
          "hero_p1": self.selected_class,
          "p1_config": p1_config,
          "p2_config": p2_config,
      }
  - If player_index == 2:
      self.next_scene = STATE_PLAYING
      self.next_scene_kwargs = {
          "hero_p1": hero_p1,
          "hero_p2": self.selected_class,
          "p1_config": p1_config,
          "p2_config": p2_config,
      }

When PLAYER_COUNT == 1: existing behavior completely unchanged
(the default player_index=1, p1_config=None path goes straight to STATE_PLAYING
with {"hero": selected_class} as before).

Run python run_check.py to verify no import errors.
```

---

## Phase 4 — GameScene Core Refactor
**Scope:** Player list, per-player XPSystems, upgrade queue, weapon init, win/loss, weapon draw loops

**Files:** `src/game_scene.py`

```
Implement Phase 4 of local multiplayer for Mystic Siege: refactor GameScene to support
a player list.

Read src/game_scene.py in full before making changes.

1. Change __init__ signature to:
   def __init__(self, hero_p1: dict = None, hero_p2: dict = None,
                hero: dict = None, p1_config: dict = None, p2_config: dict = None)
   - If hero is provided (legacy 1P call), treat it as hero_p1.
   - Default p1_config = None means the Player uses current combined WASD+arrows+controller0.

2. Create players list:
   center = Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
   self.players = []
   self.players.append(Player(center + Vector2(-80, 0), hero_p1,
                              (self.all_sprites, self.player_group),
                              input_config=p1_config))
   if hero_p2:
       self.players.append(Player(center + Vector2(80, 0), hero_p2,
                                  (self.all_sprites, self.player_group),
                                  input_config=p2_config))
   Add a property: @property def player(self): return self.players[0]

3. Add per-player XP systems:
   self.xp_systems = [XPSystem() for _ in self.players]
   Replace single self.xp_system with this list everywhere.

4. Add upgrade queue:
   self.upgrade_menu_queue: list[tuple] = []
   self.active_upgrade_menu = None
   In update(): replace single xp_system check with:
     for i, (player, xp_sys) in enumerate(zip(self.players, self.xp_systems)):
         xp_sys.update(dt, player, self.xp_orb_group)
         if xp_sys.levelup_pending:
             choices = self.upgrade_system.get_random_choices(player)
             menu = UpgradeMenu(choices, self.upgrade_system, player,
                                player_index=i, input_config=player.input_config)
             self.upgrade_menu_queue.append((menu, i))
             xp_sys.consume_levelup()
     if self.active_upgrade_menu is None and self.upgrade_menu_queue:
         self.active_upgrade_menu, _ = self.upgrade_menu_queue.pop(0)
   Replace all references to self.upgrade_menu with self.active_upgrade_menu.

5. Win/loss: replace single player check with:
   all_out = all(p.is_downed or not p.alive() for p in self.players)
   if all_out: # trigger game over
   Aggregate stats: kills=sum(p.kill_count for p in self.players),
                   level=max(xs.current_level for xs in self.xp_systems)

6. Starting weapon init: loop over each player using their hero_class_data.

7. Weapon draw loop (in draw()):
   for player in self.players:
       for weapon in player.weapons:
           if hasattr(weapon, 'draw'): weapon.draw(screen, self.camera.offset)
           if hasattr(weapon, 'draw_effect'): weapon.draw_effect(screen, self.camera.offset)

8. Update HUD call: pass self.players and self.xp_systems (lists).
   Update collision call: pass self.players (list).

Run python run_check.py to verify no import errors. Test with PLAYER_COUNT=1 first.
```

---

## Phase 5 — World Systems (Camera, WaveManager, Enemy, Collision)
**Scope:** Zoom camera, midpoint follow, multi-player spawn targeting, enemy retargeting, collision loop

**Files:** `src/systems/camera.py`, `src/systems/wave_manager.py`, `src/entities/enemy.py`, `src/systems/collision.py`

```
Implement Phase 5 of local multiplayer for Mystic Siege: world systems.

Read each file fully before modifying.

1. src/systems/camera.py:
   - Add self.zoom = 1.0 to __init__.
   - Add update_midpoint(self, positions: list, dt: float):
     Computes midpoint of provided positions, lerps toward it (same lerp_speed logic),
     sets self.zoom = COOP_CAMERA_ZOOM. Clamp bounds using WORLD_W - SCREEN_W/zoom etc.
   - Modify apply(entity) and any apply_pos() methods to multiply by self.zoom:
     screen_x = (world_x - self.offset.x) * self.zoom
     screen_y = (world_y - self.offset.y) * self.zoom

   In src/game_scene.py update():
   - When PLAYER_COUNT >= 2: call self.camera.update_midpoint(
         [p.pos for p in self.players if p.is_alive or p.is_downed], dt)
   - 1P: existing self.camera.update(self.player.pos, dt) unchanged

   Background rendering in game_scene.draw() with zoom:
   Compute a crop rect in world space:
     visible_w = int(SCREEN_WIDTH / self.camera.zoom)
     visible_h = int(SCREEN_HEIGHT / self.camera.zoom)
     crop = pygame.Rect(self.camera.offset.x, self.camera.offset.y, visible_w, visible_h)
   Blit the world background subsurface (or tile region) for that crop onto a
   temporary surface of size (visible_w, visible_h), then scale it up to
   (SCREEN_WIDTH, SCREEN_HEIGHT) using pygame.transform.scale before drawing to screen.
   Sprites rendered via camera.apply() already account for zoom — no change needed there.

2. src/systems/wave_manager.py:
   - Change __init__ to accept players (single Player or list — wrap single in list).
   - Store as self.players = players if isinstance(players, list) else [players].
   - In _get_spawn_pos() (or equivalent): spawn relative to midpoint of alive players.
   - Add _nearest_alive_player(self, pos: Vector2) -> Player:
       alive = [p for p in self.players if p.is_alive]
       return min(alive, key=lambda p: (p.pos - pos).length()) if alive else self.players[0]
   - Pass _nearest_alive_player(spawn_pos) as the target when instantiating each enemy.

3. src/entities/enemy.py:
   - Add player_list: list = None to __init__.
   - Store as self.player_list = player_list or [self.target].
   - In update(): if self.target is None or self.target.is_downed or not self.target.is_alive:
       alive = [p for p in self.player_list if p.is_alive]
       if alive: self.target = min(alive, key=lambda p: (p.pos - self.pos).length())

4. src/systems/collision.py:
   - Change check_all(self, player, ...) to check_all(self, players: list, ...)
   - Loop: for player in players: if player.is_alive: <existing per-player checks>
   - The projectile vs enemy check (not player-specific) stays as-is.

Run python run_check.py. Test with PLAYER_COUNT=2 and two heroes selected.
```

---

## Phase 6 — Leash + Revive
**Scope:** Coop constraint enforcement in GameScene; HUD revive arc

**Files:** `src/game_scene.py`, `src/ui/hud.py`

```
Implement Phase 6 of local multiplayer for Mystic Siege: leash and revive mechanics.

Read src/game_scene.py in full before modifying.

In src/game_scene.py, add a private method _enforce_coop_constraints(self, dt):
Call it in update() after all_sprites.update(dt), only when PLAYER_COUNT >= 2.

Leash:
  If len(alive_players) == 2:
    gap = p2.pos - p1.pos
    dist = gap.length()
    if dist > COOP_LEASH_DISTANCE:
        excess = dist - COOP_LEASH_DISTANCE
        direction = gap.normalize()
        # Push the lagging player (the one moving away) back by excess/2 each
        p1.pos -= direction * (excess / 2)
        p2.pos += direction * (excess / 2)
        p1.rect.center = p1.pos
        p2.rect.center = p2.pos

Revive:
  For each downed player pd:
    For each living player pl:
      if (pl.pos - pd.pos).length() <= REVIVE_RADIUS:
        pd.revive_timer += dt
        if pd.revive_timer >= REVIVE_DURATION:
          pd.hp = pd.max_hp * 0.5
          pd.is_downed = False
          pd.image.set_alpha(255)
          pd.iframes = 2.0
          pd.revive_timer = 0.0
        break  # only need one rescuer
    else:
      pd.revive_timer = max(0.0, pd.revive_timer - dt)  # decay if no one nearby

Both downed:
  if all(p.is_downed for p in self.players):
      trigger game over (set self._trigger_gameover())

In src/ui/hud.py, in the 2P draw path, for each downed player:
  - Draw their HP bar in gray with "DOWNED" label
  - Draw a revive progress arc near their screen-space position:
      screen_pos = camera.apply_pos(downed_player.pos)  # use camera offset
      progress = downed_player.revive_timer / REVIVE_DURATION
      rect = pygame.Rect(screen_pos.x - 20, screen_pos.y - 40, 40, 40)
      pygame.draw.arc(screen, (255, 255, 100), rect,
                      math.pi / 2, math.pi / 2 + progress * 2 * math.pi, 4)

Run python run_check.py. Test: down one player, verify ghost; revive; down both, verify game over.
```

---

## Phase 7 — UI Polish
**Scope:** Two-player HUD layout; UpgradeMenu player label + input routing

**Files:** `src/ui/hud.py`, `src/ui/upgrade_menu.py`

```
Implement Phase 7 of local multiplayer for Mystic Siege: UI polish.

Read both files fully before modifying.

1. src/ui/hud.py:
   Change signature: draw(self, screen, players, xp_systems, wave_manager, show_fps, fps)
   When len(players) == 1: existing 1P layout completely unchanged.
   When len(players) == 2:
     - P1 HP bar + stats: top-left (same position as current 1P layout)
     - P2 HP bar + stats: top-right corner, right-aligned to SCREEN_WIDTH - 20
     - XP bar: split at horizontal center — left half P1, right half P2, thin white divider
     - Weapon slots: P1 bottom-left, P2 bottom-right
     - Kill count: P1 below-left stats, P2 below-right stats
     - Wave timer: centered at top (shared, unchanged)
     - Downed player: gray HP bar + "DOWNED" label (revive arc drawn in Phase 6)
   Update the call site in game_scene.draw() to pass self.players and self.xp_systems.

2. src/ui/upgrade_menu.py:
   Add player_index: int = 0 and input_config: dict = None to __init__.
   - Change the header/title to f"PLAYER {player_index + 1} — LEVEL UP!"
   - For card selection: keep 1/2/3 number keys working for all players
     (both players can always press 1, 2, or 3 regardless of input config — simplest approach)
   - For controller players: InputManager already posts synthetic K_1/K_2/K_3 events
     for buttons A/B/X — if not mapped already, map button 0 → confirm currently
     highlighted card (add highlight state: self.highlighted = 0, navigate with
     input_config left/right, confirm with config's confirm key or K_1/K_2/K_3)
   - Keep existing mouse click selection unchanged

Run python run_check.py.
Run full end-to-end test:
  - PLAYER_COUNT=1: full run, single-player identical to before
  - PLAYER_COUNT=2: input assign → class select × 2 → game → both level up
    → sequential upgrade menus → one player downed → revived → victory
```

---

## Verification Checklist

```
python run_check.py                         # no import errors at any phase
PLAYER_COUNT=1 python main.py               # 1P unchanged
PLAYER_COUNT=2 python main.py               # 2P full flow
  ✓ Input assign screen shows 2 slots
  ✓ WASD claims P1, arrows claims P2
  ✓ Two controllers: each claims a slot
  ✓ Conflict (same device): "Already taken" flash
  ✓ Class select: P1 picks, P2 picks
  ✓ In-game: both players visible on zoomed-out view
  ✓ Each player controlled by their assigned device
  ✓ Leash kicks in at 700px gap
  ✓ P1 levels up → "PLAYER 1 — LEVEL UP!", P2 paused
  ✓ P2 levels up after P1's menu clears
  ✓ P1 downed → ghost at low alpha
  ✓ P2 revives P1 → 50% HP, 2s iframes
  ✓ Both downed simultaneously → instant game over
  ✓ 30-min victory → combined kill count shown
```
