# Mystic Siege — Project Tracker

This file is the repo-level planning guide for issues, board usage, and day-to-day tracking.

## Project Snapshot

Mystic Siege is a top-down medieval fantasy survivor built in Python 3.12.13 with pygame-ce.

Current known state:
- Single-player is still the baseline experience.
- Local co-op is implemented and runtime-verified for 1–4 players.
- Current content baseline includes 8 heroes, 14 weapons, and 7 enemy types.
- The next highest-value work is multiplayer balance/scaling, spawn fairness, and then additional content.

## Tracking Principles

1. **Protect solo first.** Any issue that touches multiplayer must still verify the 1P path.
2. **Use `settings.py` for tunables.** Avoid hardcoded gameplay or UI numbers.
3. **Prefer targeted changes.** Fix or extend systems instead of rewriting working architecture.
4. **Be explicit about verification.** Distinguish between static verification and runtime/manual verification.
5. **No accidental netcode work.** Do not create networking tasks unless explicitly planned.
6. **Document regression risk.** Especially for HUD, camera, input, pause, progression, and scene flow.

## Recommended Labels

### Type
- `type:bug`
- `type:feature`
- `type:balance`
- `type:content`
- `type:docs`
- `type:refactor`
- `type:performance`
- `type:test`
- `type:chore`

### Priority
- `priority:P0`
- `priority:P1`
- `priority:P2`
- `priority:P3`

### Area
- `area:gameplay`
- `area:multiplayer`
- `area:weapons`
- `area:heroes`
- `area:enemies`
- `area:ui-hud`
- `area:input-controller`
- `area:performance`
- `area:audio`
- `area:docs`
- `area:tooling`
- `area:save-progression`

### Verification
- `verify:static`
- `verify:manual`
- `verify:runtime`
- `verify:needs-retest`

### Risk / Scope
- `risk:low`
- `risk:medium`
- `risk:high`
- `scope:solo`
- `scope:co-op`
- `scope:both`

## Milestones

Use milestones for bigger outcome buckets, not every small task.

Suggested starting milestones:
- `Next - Multiplayer Balance`
- `Next - Spawn Fairness`
- `Next - Content Expansion`
- `Next - UI / HUD Polish`
- `Next - Docs / Repo Hygiene`
- `Later - Performance Profiling`
- `Later - Release Prep`

## Definition Of Ready

An issue is ready when it has:
- a clear problem or goal
- affected system(s)
- expected behavior or acceptance criteria
- verification notes
- priority and area labels

## Definition Of Done

An issue is done when:
- code and docs are updated together when needed
- new tunables are added to `settings.py` if appropriate
- `python run_check.py` passes for non-trivial code changes
- manual verification is listed when gameplay/UI/input changed
- remaining risks or unverified paths are called out

## Board Workflow

Status flow:
`Inbox -> Ready -> In Progress -> Blocked -> In Review -> Verify -> Done`

Status meanings:
- **Inbox**: newly captured, not yet triaged
- **Ready**: scoped, labeled, and ready to implement
- **In Progress**: actively being worked on
- **Blocked**: waiting on decision, art, testing, or another issue
- **In Review**: implementation exists and needs review
- **Verify**: merged or near-merge, waiting on runtime/manual confirmation
- **Done**: accepted and verified as complete

## Required Fields For Every Issue

Minimum recommended fields:
- Title
- Type label
- Priority label
- Area label
- Scope label (`solo`, `co-op`, or `both`)
- Status
- Verification expectation
- Milestone when part of a larger goal

## Suggested Project Views

### 1. Triage Board
Group by `Status`.
Use this as the default working board.

### 2. Bugs View
Filter:
`label:"type:bug"`
Sort by priority descending.

### 3. Balance / Tuning View
Filter:
`label:"type:balance"`
Useful for multiplayer scaling and spawn fairness work.

### 4. Content Pipeline View
Filter:
`label:"type:content" OR label:"type:feature"`
Good for heroes, weapons, enemies, pickups, and visuals.

### 5. Docs + Refactor View
Filter:
`label:"type:docs" OR label:"type:refactor" OR label:"type:chore"`

### 6. Verification Queue
Filter:
`label:"verify:needs-retest" OR status:Verify`
Use this to avoid “done but not truly checked.”

## Initial Backlog Recommendations

Create these first as seed issues:

1. **Define multiplayer balance/scaling policy for 2–4 players**
   - decide scaling knobs
   - document intended behavior
   - identify likely tuning constants in `settings.py`

2. **Audit enemy spawn fairness near map edges with wide party spread**
   - reproduce edge cases
   - define fairness expectations
   - verify 1P, 2P, and high-spread multiplayer behavior

3. **Create repeatable gameplay verification checklist issue**
   - standardize 1P and 2P smoke test path
   - include lobby, class select, level-up, death/game over, reconnect, and pickups

4. **Tag and normalize open technical debt by system area**
   - weapons
   - enemies
   - HUD/UI
   - input/controller
   - save/progression

5. **Track next content batch**
   - new hero ideas
   - new weapon ideas
   - new enemy/content additions

6. **Repo hygiene pass for docs and planning files**
   - keep README accurate
   - keep project docs aligned with codebase reality
   - avoid stale planning docs being treated as current state

## Issue Writing Rules

When opening issues:
- describe the player-facing problem first
- then describe the technical constraints
- include exact systems/files only if known
- keep one issue focused on one outcome
- split implementation from design discussion when needed

Good issue title examples:
- `Balance enemy density for 3P and 4P runs`
- `Fix controller input bleed in owned upgrade menus`
- `Add new enemy issue template labels and verification workflow`
- `Document content pipeline for heroes / weapons / enemies`

Bad issue title examples:
- `multiplayer`
- `fix stuff`
- `cleanup`
- `weapon bugs and ui and balance`

## Release Buckets

When you want a lightweight release rhythm, use three active buckets:
- **Now**: current sprint / immediate work
- **Next**: important queued work
- **Later**: useful, but not worth interrupting current priorities

## Notes

This tracker should reflect the codebase as it exists now, not older planning docs.
