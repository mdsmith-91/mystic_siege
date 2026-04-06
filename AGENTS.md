# Mystic Siege — Agent Guide

## Purpose

This file is the neutral agent-facing project guide for Mystic Siege. It is the
Codex-friendly entry point for repository rules and should stay aligned with
`CLAUDE.md`, `MULTIPLAYER_IMPLEMENTATION_V2.md`, and
`MULTIPLAYER_READINESS_AUDIT.md`.

## Project Summary

Mystic Siege is a top-down medieval fantasy survivor game built in Python 3.12.13
with pygame-ce. The stable baseline is single-player. A local co-op migration is
partially implemented for 1–4 players on one machine, but it is still in an
incremental verification phase and must continue to preserve the solo experience.

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
draws instead of rebuilding equivalent screen-space work every frame.

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
- `MULTIPLAYER_READINESS_AUDIT.md`: codebase audit, risks, and implementation order
- `CLAUDE.md`: expanded project context and developer guidance

## Current Multiplayer Clarifications

1. The long-term target is that the lobby always emits a concrete `input_config`,
   including in 1P.
2. `input_config=None` is only a temporary migration shim for the old 1P path.
3. `PlayerSlot` owns slot/session metadata such as index, input config, hero, and color.
4. `Player` owns runtime state such as HP, downed state, revive progress, and weapons.
5. The long-term player-count target remains 4, and the current hero roster now
   supports 4 unique simultaneous selections without duplicates.
6. Save/progression is still machine-local and aggregated across runs, including
   multiplayer runs; there is no per-person profile split yet.
7. XP orb collection is currently a shared pool, and equal-distance ties resolve
   to the lowest slot index.

## Review guidelines

- Prioritize correctness, regression risk, and maintainability over style nits.
- Preserve single-player behavior as the baseline.
- Flag any new hard-coded P1/P2 assumptions as high-priority issues.
- Verify multiplayer input ownership and menu device identity carefully.
- Treat stale README or misleading project documentation as a real issue.
- Call out unverified behavior explicitly instead of assuming it works.
- When reviewing, report findings first with file references, then risks, then verification gaps.
