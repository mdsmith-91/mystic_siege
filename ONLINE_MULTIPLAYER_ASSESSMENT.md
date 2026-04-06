# Online Multiplayer Feasibility Assessment — Mystic Siege

**Assessment date:** 2026-04-06
**Codebase state at assessment:** Local co-op 1–4 players runtime-verified; single-player baseline stable.
**Scope:** Honest evaluation of online multiplayer feasibility and implementation path.
**Sources reviewed:** AGENTS.md, CLAUDE.md, MULTIPLAYER_IMPLEMENTATION_V2.md, MULTIPLAYER_READINESS_AUDIT.md, README.md, game_scene.py, wave_manager.py, xp_system.py, collision.py, player_slot.py, enemy.py, player.py, input_manager.py, lobby_scene.py, upgrade_system.py, save_system.py, camera.py, hud.py

---

## 1. Executive Summary

Online multiplayer is achievable for this project but it is a large, high-risk effort that would take significantly longer than the entire local multiplayer migration. The codebase is clean and disciplined, which helps, but it was never designed for network play and has no networking infrastructure at all. The local multiplayer work completed a necessary but not sufficient prerequisite: it generalized the architecture to N players. It did not do anything toward the harder problems of real-time state synchronization, RNG determinism, input serialization, or authority modeling that online play requires.

**The project is not a good candidate for full online multiplayer right now.** The most realistic near-term option for letting players play together over the internet is Steam Remote Play Together, which requires zero code changes and works on the existing local multiplayer today. If you want real networked play with independent clients, the lowest-risk technical path is a LAN/direct-connect prototype using a host-authoritative state sync model — but that is still a substantial multi-month effort even for an AI-assisted team.

---

## 2. Reality Check on Difficulty

### Why real-time online action is fundamentally harder than local multiplayer

Local multiplayer adds complexity to the UI layer (device assignment, menu ownership, HUD layout) and to some game systems (XP orb arbitration, enemy targeting, downed/revive). These are hard engineering problems but they operate within a single shared process with shared memory, deterministic execution order, and zero latency between players.

Online multiplayer breaks every one of those assumptions simultaneously:

**Latency is always present.** Even on a LAN, round-trip times are 0.5–5ms. Over the internet, 50–200ms is typical. A game running at 60 fps has a frame budget of ~16ms. A 100ms round-trip means the remote player's input arrives 6 frames late by default. This is not a code bug — it is physics. Every game design and implementation choice for networking flows from how you handle this latency.

**dt-based physics diverges.** Every entity moves with `pos += vel * dt`. On two different machines with different frame rates, different system load, and different timer resolution, dt values will differ slightly every frame. Those differences compound. After 30 seconds, two clients running the same simulation independently will have visibly different world states. This project has no fixed-timestep option.

**RNG is uncontrolled.** Three critical systems call `random.random()` / `random.randint()` / `random.sample()` with no seeding and no synchronization:
- `wave_manager.py` lines 161, 165, 244–256: enemy type, pack size, spawn position
- `upgrade_system.py` lines 207, 212, 224: upgrade card selection
- Weapon crit rolls in individual weapon classes

If two clients run these independently they will diverge immediately. If the host runs them and clients trust the results, every RNG call must be transmitted as an event.

**Entity identity is memory-local.** `base_entity.py` uses `id(self)` as `sprite_id`. Python's `id()` is a memory address. Two processes cannot share these identifiers. A network protocol that says "apply damage to entity 140234567890" cannot work without replacing entity IDs with stable, process-independent integers.

**The game state is implicit in sprite groups.** The full world state is spread across pygame.sprite.Group objects. There is no `WorldState` dataclass or snapshot mechanism. Synchronizing state over a network requires extracting all of this, serializing it, transmitting it, deserializing it, and applying it — none of which exists.

**The pygame event model is local.** `InputManager._post_key()` (lines 695–732) posts `pygame.event.Event` objects directly to the local pygame queue. This is the entire mechanism by which controller input drives menu navigation. There is no concept of "remote input" anywhere in the input system.

### The biggest hidden problems

1. **Fixed timestep is absent.** For any deterministic approach (lockstep, rollback) to work, the simulation must run at a fixed, consistent tick rate regardless of rendering frame rate. The entire game loop is variable-dt today. Converting to a fixed-tick loop with interpolated rendering is a multi-file architectural change.

2. **There is no world state serialization.** You cannot send what you cannot express as bytes. Before the first network packet can be written, a complete definition of serializable game state must exist. This requires systematically inventorying every field on every entity class.

3. **Upgrade selection RNG is server-critical.** `upgrade_system.py` generates choices using `random.sample()` with no seed. Online, a client should not be able to influence what choices are offered. This must run on the host and the result sent to the client — not re-run on the client.

4. **Death/downed state diverges easily.** Player death has two paths (`dying` → fade in solo, `is_downed` in multiplayer) controlled by `supports_revive`. A lag spike can cause client A to see a player as alive when the host has already marked them downed.

5. **Camera and HUD are already correct architecturally.** `camera.py` takes position lists (not sprites), and `hud.py` can be fed state snapshots rather than live sprites. These are the most network-ready files. Do not redesign them — just change what feeds them.

---

## 3. What Local Multiplayer Work Helps vs Does Not Help

### What helps online

| Local MP work | Why it helps online |
|---|---|
| `PlayerSlot` abstraction with stable `index` (0–3) | Slot index maps directly to a network player ID |
| Collections everywhere (`list[Player]`, `list[PlayerSlot]`) | Server can iterate the same collection of remote player states |
| Stateless `UpgradeSystem` (takes player at call time) | Can be fed a network state snapshot instead of a live sprite |
| Per-player `XPSystem` instances | Each client only needs its own XP tracked; host aggregates |
| `camera.py` accepts a list of positions | Camera needs no changes; just feed it server-provided positions |
| Weapon ownership per player (`self.owner = owner`) | Clean boundary for what belongs to each player |
| `PlayerSlot` is a plain dataclass | Can be the basis for a session description message |
| Scene transition kwargs are already lightweight | Network handoff of lobby state can reuse this pattern |
| Input device and player identity already decoupled | Removes one conceptual coupling for online mapping |

### What does not help online

| Local MP assumption | Why it does not solve online |
|---|---|
| Shared in-process sprite groups | Network clients cannot share a Python process's memory |
| Synthetic events posted to local pygame queue | Remote input cannot use this mechanism |
| `id(self)` as entity identity | Memory addresses differ across processes |
| Variable dt physics | Different machine speeds cause drift; no fixed timestep |
| All RNG local and unseeded | Three critical systems diverge immediately across clients |
| Controller instance IDs (SDL device handles) | Remote players have no local controller; IDs are transient |
| `save_system.py` is local filesystem | No per-player cloud or host-mediated storage |
| Zero network transport code | There is nothing to build on |
| Collision runs once per frame with full authority | No conflict resolution if clients disagree |
| Lobby scene tied to local device detection | Cannot enumerate remote players from joystick list |

**Blunt summary:** local MP reduced the UI complexity of showing N players on one screen. It did not touch the three deepest online problems: state synchronization, RNG centralization, and network transport.

---

## 4. Must-Decide-Now Decisions

These must be answered before a single line of network code is written.

### Decision 1: Networking model

**Deterministic lockstep:**
All clients run identical simulation steps driven by a shared input log. No state sync — just sync inputs every frame.
- Requires: fixed timestep, seeded RNG, input buffer, desync detection, game state checksums, resync on mismatch
- Risk for this project: **VERY HIGH.** Requires fixed timestep conversion, complete RNG seeding audit, removal of all platform-dependent behavior, and a resync mechanism. Python's float arithmetic adds additional desync risk.

**Host-authoritative state sync** *(recommended)*:
One machine (the host) runs the full simulation. Other clients send only their inputs to the host. The host runs the game, then broadcasts world state snapshots to clients.
- Requires: world state serialization, input serialization, a transport layer, client-side interpolation
- Latency: host has zero lag; clients see round-trip latency on their own inputs
- Risk for this project: **MEDIUM.** The host simulation is mostly unchanged. The work is the transport and state snapshot layers.

**Peer-to-peer:**
Each client simulates the world and syncs with peers. Requires either determinism (same as lockstep) or constant state correction. Not recommended for this project.

**Rollback netcode:**
Clients predict, execute locally, then roll back and replay when out-of-sync packets arrive.
- Risk for this project: **EXTREME.** Requires complete game state snapshot/restore in <1ms per rollback frame. Not realistic here.

### Decision 2: Online scope

Options in rough order of complexity:
1. **Steam Remote Play Together** — Zero code changes. Works on existing local MP today.
2. **LAN / direct connect** — Players on the same network enter the host's IP. No matchmaking.
3. **Internet with relay** — Players connect through a relay server. Requires a backend.
4. **Steam Steamworks / matchmaking** — Platform-managed lobbies. Requires Steamworks SDK.

These are different products, not just different complexities of the same product.

### Decision 3: Max player count online

2 is much simpler than 4. Every additional player doubles the state to sync. Start with 2 and design to expand.

### Decision 4: Acceptable latency targets

- LAN: <5ms round-trip — smooth with simple state sync
- Internet (same region): ~50ms — playable with client interpolation, some input lag
- Internet (cross-region): ~150ms+ — requires significant client-side prediction or the game feels bad

Survivors games are forgiving (no PvP) but real-time weapon fire timing will feel different at 150ms vs local.

### Decision 5: State sync vs input sync

**State sync** (recommended): host sends full world state to clients every N frames. Simpler to implement, higher bandwidth. A survivors game world is not enormous and can be reasonably compressed.

**Input sync (lockstep):** clients send only inputs, all clients simulate. Lower bandwidth, much harder to implement correctly.

---

## 5. Decisions That Can Wait

**Progression/save data ownership:** Host-owned is simplest — after an online run, the host's local save updates and clients get a summary screen. Per-player cloud sync is a later feature.

**Pause/upgrade flow online:** Keep the sequential upgrade menu. Just add a "waiting for [Player] to pick an upgrade" state visible to other clients. The existing queue logic supports this conceptually.

**Reconnect expectations:** For a first prototype, a disconnect ends the session. Reconnect support is a V2 feature.

**Cheat tolerance / trust model:** For invite-only / direct connect, trust is high. Host authority gives basic cheat resistance. No anti-cheat needed initially.

**Lobby/invite flow:** Can start with "enter host IP address" and a basic ready-check. Steam lobby integration or friend invites are polish.

**Controller/keyboard support online:** Clients can use whatever local input they want. Just ensure each client maps their local input to the same serialized input packet format.

**Spectator mode, replays, tournament support:** Defer indefinitely.

---

## 6. Recommended Networking Model

**Host-authoritative state sync, LAN/direct connect first.**

### Why this fits the project

1. The host runs the exact same simulation as today — almost no changes to `game_scene.py`, `wave_manager.py`, `enemy.py`, `collision.py`. All that code already works correctly.
2. Remote clients only need to: (a) send their local input to the host each frame, (b) receive the world state snapshot each frame, (c) render what they received.
3. RNG stays on the host. Upgrade choices, enemy spawns, and crits all happen on the host and the results are broadcast. No RNG synchronization problem.
4. Starting with LAN removes the relay infrastructure problem entirely.
5. The existing local multiplayer already handles 1P as a degenerate case of N-player. Online 2P is just a case where one slot is fed from a network input source instead of a local device.

### New infrastructure required (none of this exists)

- **Transport layer:** Python asyncio or plain TCP sockets. One server coroutine on the host, one client connection per remote player.
- **`WorldSnapshot` dataclass:** serializable capture of all player positions, HP, iframes, enemies, XP orbs, and wave state.
- **`InputPacket` format:** per-frame local input (move X/Y, actions triggered) from client to host.
- **Serialization:** `msgpack` or `json` with a manual schema is safer than `pickle` across versions.

### Refactors required before any of this works

- Replace `sprite_id = id(self)` in `base_entity.py` with a stable monotonic integer ID.
- Separate input reading from player state update in `player.py` — extract `_read_input()` into `apply_input(input_state: dict)`.
- Add `WorldSnapshot.capture()` and `WorldSnapshot.apply()` methods.
- Move upgrade RNG to host-only call; send result to client as a deterministic list.

---

## 7. Alternatives Considered

### Alternative A: Deterministic lockstep

**Why it's worse here:**
Requires converting the entire game to a fixed timestep, replacing all unseeded RNG calls with a synchronized PRNG, auditing all platform-dependent float behavior, and building desync detection and resync. A single desync corrupts both simulations permanently. Python is not well-suited for this — deterministic float arithmetic across platforms is still not guaranteed in practice. Total refactor risk: HIGH before the first packet can be sent.

### Alternative B: Steam Remote Play Together

**Why it might be the right answer anyway:**
Remote Play Together streams the host's screen and mirrors remote player input. It works out-of-the-box for a couch co-op game. Zero engineering cost, ships immediately. The local multiplayer camera already zooms to fit all players, so guests get a shared aggregated view. Requires Steam ownership / launch through Steam for both players.

**Limitation:** Not "real" online multiplayer. Guests cannot have an independent viewport.

### Alternative C: Rollback netcode

**Why it's worse here:**
Requires complete game state snapshot/restore in <1ms per rollback frame. The current architecture has no snapshot mechanism and dozens of mutable sprite objects. Not appropriate for a survivors genre — rollback is designed for competitive latency-sensitive games, not co-op. Complexity is extreme.

### Alternative D: LAN-first prototype, punt on internet

**Why this is the most pragmatic path:**
LAN latency (<5ms) means client-side prediction is optional — raw state sync looks acceptable. Gets you a playable online prototype quickly to evaluate whether it's worth investing in the internet infrastructure layer. If it feels bad even on LAN, you've learned that before spending months on relay servers.

---

## 8. System-by-System Impact Assessment

### Light refactor — mostly reusable as-is

| System | Why light | What needs touching |
|---|---|---|
| `src/systems/camera.py` | Takes position lists, not sprites | Feed it positions from server snapshot instead of live sprite refs |
| `src/ui/hud.py` | Already reads player state attributes | Feed it a `PlayerState` snapshot instead of live sprite; same attribute names |
| `src/systems/wave_manager.py` | Host-side only; broadcast state | Move all RNG to explicit host-only path; broadcast timeline events |
| `src/systems/xp_system.py` | Per-player, deterministic orb assignment | Collection happens on host; broadcast XP state updates |
| `src/systems/upgrade_system.py` | Stateless, correct architecture | Move `random.sample()` to host-only call; client just renders offered choices |
| `src/systems/save_system.py` | Keep local | Online runs update host's save; optionally broadcast summary to clients |
| `src/entities/effects.py` | Position-based, no owner state | Trigger effects from host events; or replicate trigger events |

### Medium refactor

| System | Why medium | What needs touching |
|---|---|---|
| `src/game_scene.py` | Central hub; currently single-process | Add host/client mode flags; host runs simulation; client applies received snapshot |
| `src/entities/enemy.py` | Targeting is deterministic | Runs on host only; broadcast positions/state; entity ID must become stable integer |
| `src/systems/collision.py` | Collision authority must be clear | Host-only execution; remove client-side damage application for remote entities |
| `src/entities/player.py` | Death/downed/revive state complex | Separate `_read_input()` from state update; add `apply_remote_input()` path |
| `src/ui/lobby_scene.py` | Device-to-slot mapping is local | Add "waiting for network players" state; slot assignment via host |

### Deep redesign required

| System | Why deep | What needs touching |
|---|---|---|
| `src/utils/input_manager.py` | Fundamentally local-device model | Add input serialization layer: local input → `InputPacket` → network → host applies it |
| `src/entities/base_entity.py` | `sprite_id = id(self)` | Replace with stable monotonic integer IDs shared across all clients |
| Networking transport | Does not exist | New module: asyncio server/client, serialization, connection management |
| World state snapshot | Does not exist | New module: `WorldSnapshot.capture()` and `WorldSnapshot.apply()` |

### Most dangerous existing code for networking

| File | Location | Problem |
|---|---|---|
| `src/entities/base_entity.py` | line 13 | `self.sprite_id = id(self)` — memory address as identity |
| `src/utils/input_manager.py` | lines 695–732 | `_post_key()` / `_post_keyup()` — local pygame event posting |
| `src/systems/wave_manager.py` | lines 161, 165, 244–256 | Unseeded `random.randint()` / `random.choice()` calls |
| `src/systems/upgrade_system.py` | lines 207, 212, 224 | Unseeded `random.sample()` calls |
| `src/entities/player.py` | lines 209–264 | `_read_input()` reads from local devices directly inside `update()` |
| Any collision file | — | `pygame.sprite.groupcollide()` / `spritecollide()` — requires shared in-process state |

---

## 9. Phased Implementation Plan

> Assumes host-authoritative state sync, LAN/direct connect first. Each phase has a stop/go checkpoint.

### Phase N0: Decision gate (prerequisite — no code)

Answer the must-decide-now questions in Section 4 in writing. Without these answers you cannot design the network protocol.

**Stop/go:** Written decisions on networking model, scope, player count, and latency targets.

---

### Phase N1: Networking-readiness refactors (no actual networking)

**Goal:** make the codebase amenable to networking without adding any network code. Solo and local multiplayer behavior must be completely preserved.

1. **Stable entity IDs** — Replace `self.sprite_id = id(self)` in `src/entities/base_entity.py` with a class-level monotonic counter. ID assigned at construction, stable, serializable.
2. **Decouple input reading from player update** — Extract `_read_input()` from `src/entities/player.py:update()` into an explicit `apply_input(input_state: dict)` method. `update()` calls this with local device state. Remote player updates call it with received network input.
3. **Seed centralized RNG** — Replace scattered `random.*` calls in `wave_manager.py`, `upgrade_system.py`, and weapon crit rolls with a single `GameRNG` wrapper seeded from a host-generated value at game start.
4. **WorldSnapshot skeleton** — Write a `WorldSnapshot` dataclass capturing essential mutable state: player positions/HP/facing/iframes/downed, enemy positions/HP/target_id, XP orb positions/collected, wave elapsed/spawn_timer/active_pool/elite_mode, per-player XP/level. Leave `capture()` and `apply()` stubbed.
5. **Verify** — `python run_check.py` passes. Solo 1P run completes end-to-end without regressions. Local MP still works.

**Stop/go:** All refactors clean, game still 100% playable solo and in local MP.

---

### Phase N2: Transport layer (LAN prototype, no gameplay sync)

**Goal:** working connection between host and one client; no gameplay synchronization yet.

1. Add a `NetworkManager` module wrapping Python asyncio TCP sockets. Host starts a server; clients connect by IP:port.
2. Implement `InputPacket` (move_x, move_y, action flags) and `LobbyPacket` (slot assignments, hero choices, initial seed).
3. Extend `lobby_scene.py` with an online mode: host advertises, clients connect and fill remote slots.
4. Add a scene transition handshake: host sends "game starting" with seed and slot assignments; clients confirm; host waits for all confirms before entering `GameScene`.

**Stop/go:** Two machines on LAN can connect, join lobby, pick heroes, and enter `GameScene` together. No gameplay sync yet.

---

### Phase N3: World state sync (host-authoritative gameplay)

**Goal:** clients render the host's world state.

1. Implement `WorldSnapshot.capture()` on host — walks all sprite groups, extracts fields.
2. Implement `WorldSnapshot.apply()` on client — updates or creates local entity representations using stable IDs to match entities.
3. Host sends `WorldSnapshot` to clients at configurable rate (start at 20 fps; evaluate bandwidth).
4. Clients apply snapshots and use linear interpolation for smooth rendering between states.
5. Clients send `InputPacket` to host each frame. Host applies remote inputs via `player.apply_input()`.
6. Host continues running full simulation: collision, spawning, damage, XP.

**Stop/go:** Two machines can play together. Remote client's character moves correctly. Host and client visually agree on enemy positions, player HP, and wave state. Acceptable latency on LAN (<10ms round-trip).

---

### Phase N4: Internet play (relay or NAT)

**Goal:** extend LAN prototype to work over the internet.

Options:
- (a) Simple relay server — a cheap VPS running a TCP relay
- (b) NAT punch-through — complex, unreliable
- (c) Steam Networking Sockets — if going the Steam route

Steps:
1. Add latency measurement and display (ping shown in HUD).
2. Add client-side input prediction for the local player: apply local input immediately for rendering, correct from host state when it arrives.
3. Test at realistic internet latencies (use traffic shaping or remote machines).

**Stop/go (the real go/no-go):** Does the game feel acceptable at 80ms round-trip? If not, decide whether client-side prediction needs more work or whether the genre can tolerate the latency before investing further.

---

### Phase N5: Robustness and UX

**Goal:** make online play reliable enough for actual use.

1. Disconnect handling: detect client disconnect, pause host game, allow 30s reconnect window.
2. Reconnect: client rejoins and receives a full state resync.
3. Progression: host-owned save updates after online run; clients see a summary screen.
4. Connection error UI: clear messages for "connection lost," "host ended session," etc.

---

## 10. Scope Recommendation

**Do not proceed with full online multiplayer now.**

Ranked by value vs cost:

**Option A: Steam Remote Play Together — do now, zero engineering cost.**
Works on existing code. Players on different machines can play together over the internet today. The host streams video; guests send input back via Steam infrastructure. For a couch co-op survivors game this is an entirely reasonable "online multiplayer" story.

**Option B: Phase N1 networking-readiness refactors only.**
The refactors in Phase N1 (stable entity IDs, decouple input reading, centralize RNG) are valuable engineering work regardless of whether online multiplayer ships. They make the code cleaner, reduce hidden coupling, and create the foundation for online play later. These can be done without committing to the full networking effort.

**Option C: LAN prototype (Phases N1–N3).**
The lowest-risk path to real networked play. Avoids the relay/matchmaking infrastructure problem and lets you evaluate gameplay feel before investing in internet infrastructure. Realistic effort for an AI-assisted two-developer team: 2–4 months of focused work.

**Option D: Full internet online multiplayer.**
A 6–12 month effort for this team on this codebase, including Phases N1–N5 plus backend infrastructure. Not a bad idea — just a large commitment.

**Opinionated recommendation:** Ship Steam Remote Play Together as the immediate "play online" answer. In parallel, do Phase N1 as good engineering practice. Revisit the LAN prototype decision in 3–6 months when content work (balance tuning, new enemies/weapons) is more complete and the game is more polished.

---

## 11. Questions to Answer Before Implementation Starts

### Blocking — must be answered before any networking code is written

1. **What does "online multiplayer" actually mean for this game?** Steam Remote Play (zero code) / LAN direct connect / internet with a relay backend / Steam Steamworks lobbies? These are four different products.

2. **What networking model?** Deterministic lockstep (hard, correct) vs host-authoritative state sync (simpler, host has advantage)? Or defer to recommendation in Section 6?

3. **How many players online?** 2 vs 4 is a significant complexity difference.

4. **What is acceptable input latency?** Same feel as local play, or is 100ms input lag acceptable for the "online" tier?

5. **Is Steam a requirement or optional?** Early decisions should account for Steamworks SDK if you eventually want matchmaking / friend invites / achievements.

### Important but deferrable

6. **What happens to progression after an online run?** Host keeps save and clients get nothing, or should clients' progress update too?

7. **What is the reconnect expectation?** Does a disconnect end the session, or should there be a rejoin window?

8. **Who can pause the game online?** Currently any joined player can pause. Online, this needs an explicit ownership rule.

9. **What is the cheat tolerance?** Host-authoritative gives basic cheat resistance. Sufficient, or do you need something stronger?

10. **Will you use a relay server?** If internet play is the goal, someone needs to run infrastructure or use a platform like Steam. Is there a preference or budget for this?

---

## Verification Note

All findings are based on direct code review of the files listed at the top of this document.

**Not verified at runtime:**
- Whether the game behaves identically across two different machines (relevant for float determinism)
- Actual bandwidth requirements for a `WorldSnapshot` at 60 fps
- Whether `random.random()` produces different sequences on different Python versions

**Inferred from architecture review (high confidence):**
- `id(self)` causes entity identity failures across processes — this is certain; it is a memory address
- dt-based physics causes visible divergence at realistic internet latencies — near-certain for enemies with complex behaviors
- The upgrade RNG issue is blocking for any approach that expects clients to agree on offered choices — certain
