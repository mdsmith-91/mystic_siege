<!--
Best follow-up Codex prompt:

Read these files first and treat them as authoritative: AGENTS.md, CLAUDE.md, MULTIPLAYER_IMPLEMENTATION_V2.md, MULTIPLAYER_READINESS_AUDIT.md, and MULTIPLAYER_READINESS_GATE_REVIEW.md. Then inspect git status and git diff before doing anything else. Continue the multiplayer readiness-gate review as a strict pre-content checkpoint. Preserve single-player as the baseline. First verify the previously identified must-fix issue in src/ui/upgrade_menu.py and determine whether it is still present. Then verify all remaining readiness concerns, separating confirmed issues from unverified risks, and be explicit about what was runtime-tested versus only statically reviewed. Do not add new content work until multiplayer is clearly ready.
-->

# Multiplayer Readiness Gate Review

## Metadata

- Review date: 2026-04-05
- Branch: `multiplayer-improvments` (merged to `main` after this review was written)
- Worktree state: dirty (`src/ui/upgrade_menu.py` modified; `MULTIPLAYER_READINESS_GATE_REVIEW.md` untracked)
- `CODEX_REVIEW_FIX_PLAN.md`: not present
- Authoritative docs reviewed: `AGENTS.md`, `CLAUDE.md`, `MULTIPLAYER_IMPLEMENTATION_V2.md`, `MULTIPLAYER_READINESS_AUDIT.md`
- Repo state inspected before review: `git status --short --branch`, `git diff --stat`
- Static verification performed: `python run_check.py` passed
- Runtime/manual verification performed: none

## Readiness Verdict

**Updated (2026-04-06):** 1P–4P runtime verification has since been completed. The gate is now cleared. The `input_config=None` compatibility shim has been removed from `src/ui/class_select.py` and the defensive guards in `src/game_scene.py` have been simplified. The remaining open items are multiplayer balance/scaling and spawn fairness under wide party spread — not core architecture gaps.

The original pre-verification verdict is preserved below for historical context.

---

Multiplayer is structurally much improved and is mostly aligned with the documented slot-based design. The previously identified `UpgradeMenu` owned-input bug has now been fixed, and static verification remains clean.

That said, this branch should still not yet pass a strict multiplayer readiness gate. The remaining blocker is not a newly confirmed structural code defect from this pass; it is the absence of actual runtime verification for the major multiplayer gameplay paths. Until 1P, 2P, and 3P are exercised in-game, it is not safe to treat the multiplayer foundation as fully solid for further content expansion.

## Confirmed Status Before Adding More Content

### 1. Previously identified `UpgradeMenu` owned-input bug is fixed

Keyboard-owned upgrade menus now reject controller-origin synthetic `KEYDOWN` input before keyboard-owner matching.

- Fixed file: [src/ui/upgrade_menu.py](/Users/michael/Claude/mystic_siege/src/ui/upgrade_menu.py#L137)
- Current behavior:
  - `_keyboard_event_matches_owner()` now returns early for `synthetic_controller_event`
  - this matches the owned-menu rule already enforced by [src/ui/class_select.py](/Users/michael/Claude/mystic_siege/src/ui/class_select.py#L213)

Result:
- the specific keyboard-owned upgrade-menu bleed from controller synthetic confirm input is no longer present in code
- `python run_check.py` still passes after the fix

### 2. Readiness gate is still open due to missing runtime verification

The project guidance requires proving 1P first, then 2P, then 3P+ behavior. This review only confirmed code structure and import/static integrity.

Relevant guidance:
- [CLAUDE.md](/Users/michael/Claude/mystic_siege/CLAUDE.md#L451)
- [CLAUDE.md](/Users/michael/Claude/mystic_siege/CLAUDE.md#L626)

Until runtime verification is completed, multiplayer cannot be considered fully ready to build on.

## Should Improve Before Adding More Content

### 1. Remove remaining legacy compatibility branches

The long-term design says the lobby should emit a concrete `input_config` even for 1P, and `input_config=None` is only a temporary shim. That shim still exists in live code:

- [src/ui/class_select.py](/Users/michael/Claude/mystic_siege/src/ui/class_select.py#L141)
- [src/game_scene.py](/Users/michael/Claude/mystic_siege/src/game_scene.py#L380)

These branches are not necessarily breaking current behavior, but they leave architectural ambiguity in input ownership and solo-path handling.

### 2. Recheck spawn fairness near map edges

Enemy spawn positions are anchored from the alive-player centroid and then clamped to world bounds:

- [src/systems/wave_manager.py](/Users/michael/Claude/mystic_siege/src/systems/wave_manager.py#L204)

This is directionally correct, but wide player spread or edge/corner positions may still produce unfairly close or visible spawns for some players. This needs runtime verification.

### 3. Document the implemented multiplayer policies explicitly

Some multiplayer behavior is now real code but not clearly locked as intended policy:

- XP orb tie-break favors the lowest slot index on equal distance: [src/systems/xp_system.py](/Users/michael/Claude/mystic_siege/src/systems/xp_system.py#L20)
- Save/progression remains machine-aggregated, not per-person: [src/systems/save_system.py](/Users/michael/Claude/mystic_siege/src/systems/save_system.py#L86)
- Practical player cap is hero-count-limited in the lobby: [src/ui/lobby_scene.py](/Users/michael/Claude/mystic_siege/src/ui/lobby_scene.py#L77)

These are acceptable for now, but they should be documented intentionally before more content builds on them.

### 4. Decide multiplayer balance scaling before major content growth

The code is generalized enough that new enemies/weapons/classes can be added, but multiplayer balance scaling is still unresolved. Adding substantial content first is likely to create retuning work later.

## Architecture and Documentation Mismatches Still Remaining

### 1. Synthetic controller event docs are stale

The docs still describe synthetic controller events as lacking device identity:

- [AGENTS.md](/Users/michael/Claude/mystic_siege/AGENTS.md#L40)
- [CLAUDE.md](/Users/michael/Claude/mystic_siege/CLAUDE.md#L315)
- [CLAUDE.md](/Users/michael/Claude/mystic_siege/CLAUDE.md#L640)

But the implementation now includes metadata on synthetic events:

- [src/utils/input_manager.py](/Users/michael/Claude/mystic_siege/src/utils/input_manager.py#L689)

Practical note:
- The safe rule is still not to trust synthetic events for owned menus unless the menu code handles them deliberately.
- But the docs no longer accurately describe the event payload.

### 2. `input_config=None` is documented as temporary, but still exists in code

Docs:
- [AGENTS.md](/Users/michael/Claude/mystic_siege/AGENTS.md#L53)

Code still using the compatibility path:
- [src/ui/class_select.py](/Users/michael/Claude/mystic_siege/src/ui/class_select.py#L141)
- [src/game_scene.py](/Users/michael/Claude/mystic_siege/src/game_scene.py#L380)

### 3. Current 3-player HUD layout differs from V2 document intent

Current implementation uses:
- [settings.py](/Users/michael/Claude/mystic_siege/settings.py#L99)

The code places player 3 in the bottom-left, not in the V2 guide’s top-row arrangement. This is not necessarily wrong, but the docs and implementation are out of sync.

## What Content Addition Is Risky Right Now

Adding more classes, weapons, enemies, passives, or other gameplay content now is risky because:

- major multiplayer paths are still unverified in actual gameplay
- unresolved balance-scaling decisions may force retuning of new content later
- additional content will make remaining multiplayer regressions harder to isolate

The architecture is close enough that future content probably will not require a large multiplayer rewrite. The current risk is not “wrong architecture,” but “unfinished verification and a few correctness gaps.” That is still enough to justify blocking new content for now.

## Recommended Remaining Work Order

1. Run the real readiness matrix in order:
   - 1P first
   - 2P second
   - 3P next
2. Verify these paths explicitly:
   - lobby join/leave and device ownership
   - class select ownership and duplicate lockout
   - upgrade queue ownership
   - revive/downed behavior
   - camera and HUD readability/correctness
   - disconnect/reclaim behavior
   - save/progression updates after multiplayer runs
3. Fix only the specific regressions or correctness issues found during that runtime pass.
4. Remove remaining temporary compatibility branches once the unified lobby path is stable.
5. Update the authoritative docs so they match the code.
6. Only then resume content additions.
7. Add a 4th hero before treating 4P as a practical gameplay target.

## Verification Appendix

### Verified

- `AGENTS.md` read
- `CLAUDE.md` read
- `MULTIPLAYER_IMPLEMENTATION_V2.md` read
- `MULTIPLAYER_READINESS_AUDIT.md` read
- `git status --short --branch` checked
- `git diff --stat` checked
- `src/ui/upgrade_menu.py` rechecked after the previous review
- confirmed `UpgradeMenu` now rejects `synthetic_controller_event` for keyboard-owned slots
- `python run_check.py` passed

### Not Verified

- 1P gameplay through the current lobby-based path
- 2P gameplay
- 3P gameplay
- lobby ownership behavior in runtime
- class select ownership behavior in runtime
- upgrade queue behavior in runtime
- revive/downed behavior in runtime
- camera readability and zoom behavior in runtime
- HUD readability and panel correctness in runtime
- controller disconnect/reclaim behavior in runtime
- save/progression behavior after multiplayer runs in runtime

## Next Session Starting Point

Start by re-reading the authoritative docs plus this file, then inspect `git status` and `git diff`.

The first implementation task should be:

- run the first real 1P -> 2P -> 3P readiness verification pass before any content work
- fix only the specific issues surfaced by that pass
- keep the review explicit about what was actually runtime-tested versus only statically reviewed
