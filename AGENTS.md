# Mystic Siege — Agent Guide

## Purpose

This file is the neutral agent-facing project guide for Mystic Siege. It is the
Codex-friendly entry point for repository rules and should stay aligned with
`CLAUDE.md`, `MULTIPLAYER_IMPLEMENTATION_V2.md`, and
`MULTIPLAYER_READINESS_AUDIT.md`.

## Project Summary

Mystic Siege is a top-down medieval fantasy survivor game built in Python 3.12.13
with pygame-ce. The stable baseline is single-player. Local co-op for 1–4 players
on one machine is fully implemented and runtime-verified. The remaining open work is
multiplayer balance tuning and spawn fairness, not core architecture. All changes
must continue to preserve the solo experience.

## Core Rules

1. Never hardcode values. Put tunables in `settings.py`.
2. Preserve single-player behavior while generalizing systems for multiplayer.
3. Do not rewrite working systems when a phased extension will do.
4. Read files in full before editing them.
5. Run `python run_check.py` after non-trivial changes.
6. Keep scene transition kwargs lightweight. No live sprites, surfaces, or file handles.
7. Be explicit about what was verified versus not verified.

HUD/UI note: shared HUD chrome should stay settings-driven. If HP/XP bars intentionally
match empty weapon slots, reuse the same `settings.py` constant instead of duplicating
the color in `src/ui/hud.py`. In the current HUD, solo and multiplayer use the same
slot-panel HUD treatment, including the 4-segment border tracker that fills clockwise
from the top and uses the empty-slot gray for unearned sections. Keep the shared HUD
render path allocation-aware as well: cache stable panel/weapon-slot geometry inside
`HUD`, reuse icon/text surfaces where practical, and cull offscreen revive-indicator
draws instead of rebuilding equivalent screen-space work every frame. Timed pickup
buff readouts belong in the optional stat-bonus area rather than the main panel
chrome, and right-side panels should mirror that buff column inward.

Weapon architecture note: weapon tunables should follow the same settings-driven
pattern as heroes and enemies. Keep weapon stats, upgrade deltas, and relevant
visual knobs in clearly grouped `settings.py` weapon sections first. Shared weapon
construction should go through `src/weapons/factory.py` via
`WEAPON_CLASS_REGISTRY` / `create_weapon()` instead of growing new constructor
chains in `game_scene.py`, `upgrade_system.py`, or other callers. Hero
`starting_weapon` fields and upgrade rewards should stay on stable string ids, and
package-level imports should continue to flow through `src/weapons/__init__.py`
when callers need the shared registry/helper surface. Player-facing weapon card
metadata should stay in `src/systems/upgrade_system.py` (`WEAPON_META` /
`WEAPON_CLASSES`) rather than being duplicated into gameplay constructors or hero
records.

Enemy architecture note: enemy tunables should now follow the same settings-driven
pattern as heroes and weapons. Keep enemy stats, per-enemy gameplay knobs, and
wave/spawn balance values in clearly grouped `settings.py` enemy sections first.
Concrete enemy classes should read those values instead of redefining local stat
dicts, and shared enemy spawning should go through the enemy registry/helper in
`src/entities/enemies/__init__.py` instead of growing new constructor chains in
`wave_manager.py`. Shared enemy runtime state such as targeting cadence, freeze /
stun timers, effective speed rebuilding, elite projectile scaling, and spawn retry
behavior near map edges should stay centralized in the base enemy / wave systems.
Subclass-specific movement should plug into the base enemy movement hook instead of
recomputing `self.vel` in a way that the parent class then overwrites.

## Multiplayer Rules

1. No new hard-coded P1/P2 architecture.
2. Prefer collections over named players.
3. Use `PlayerSlot` as the shared slot/session metadata abstraction.
4. Keep runtime combat state on `Player`, not on `PlayerSlot`.
5. Do not add networking architecture unless explicitly requested.
6. Keep 1P as the first verification path for every multiplayer refactor.

## Input Rules

1. Use `InputManager` for controller state.
2. Synthetic controller key events are acceptable for global menus.
3. Synthetic controller key events now carry source metadata, but they are still
   not sufficient on their own for owned multiplayer menus.
4. Owned multiplayer menus must deliberately route or reject synthetic events by
   device identity, or poll the assigned device directly.

## Authoritative References

- `MULTIPLAYER_IMPLEMENTATION_V2.md`: authoritative multiplayer design and phase plan
- `MULTIPLAYER_READINESS_AUDIT.md`: codebase audit (partially historical — written at 0% multiplayer implementation); current risk inventory and migration guidance
- `CLAUDE.md`: expanded project context and developer guidance

## Current Multiplayer Clarifications

1. The lobby now emits a concrete `input_config`, including in 1P.
2. `PlayerSlot` owns slot/session metadata such as index, input config, hero, and color.
3. `Player` owns runtime state such as HP, downed state, revive progress, and weapons.
4. The long-term player-count target remains 4, and the current hero roster now
   supports 4 unique simultaneous selections without duplicates.
5. Save/progression is still machine-local and aggregated across runs, including
   multiplayer runs; there is no per-person profile split yet.
6. XP orb collection is currently a shared pool, and equal-distance ties resolve
   to the lowest slot index.
7. World pickups are shared-world objects. Timed buff pickups stay on the collector,
   while `Magnet` retargets active XP orbs to the closest eligible player per orb.

## Review guidelines

- Prioritize correctness, regression risk, and maintainability over style nits.
- Preserve single-player behavior as the baseline.
- Flag any new hard-coded P1/P2 assumptions as high-priority issues.
- Verify multiplayer input ownership and menu device identity carefully.
- Treat stale README or misleading project documentation as a real issue.
- Call out unverified behavior explicitly instead of assuming it works.
- When reviewing, report findings first with file references, then risks, then verification gaps.
