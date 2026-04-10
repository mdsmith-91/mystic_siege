# Mystic Siege — Project Tracker

This file is the repo-level planning guide for a lightweight GitHub Issues workflow.
It intentionally avoids GitHub Projects and focuses on issue reporting, labeling,
milestones, and simple status tracking inside issues themselves.

## Lightweight Issue Setup

Use these five planning/reporting files together:

1. `PROJECT_TRACKER.md`
2. `.github/ISSUE_TEMPLATE/bug_report.yml`
3. `.github/ISSUE_TEMPLATE/feature_or_content.yml`
4. `.github/ISSUE_TEMPLATE/balance_tuning.yml`
5. `.github/ISSUE_TEMPLATE/tech_debt_or_docs.yml`

Goal: keep tracking simple enough to use consistently while still capturing the
information that matters for Mystic Siege.

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

### Optional Status Labels
If you want lightweight status tracking without GitHub Projects, use labels such as:
- `status:ready`
- `status:in-progress`
- `status:blocked`
- `status:in-review`
- `status:verify`

These are optional. If they feel like overhead, skip them and rely on open/closed state,
milestones, and comments.

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
- the issue is closed with a short summary of what changed

## Issue Reporting Workflow

### 1. Pick the right issue form
Use the closest matching issue file:
- `bug_report.yml` for defects and regressions
- `feature_or_content.yml` for heroes, weapons, enemies, pickups, UI additions, and gameplay features
- `balance_tuning.yml` for tuning-only work such as scaling, spawn fairness, pacing, and difficulty
- `tech_debt_or_docs.yml` for cleanup, documentation, refactors, and repo hygiene

### 2. Apply a small label set
Try to keep each issue to a few useful labels:
- one `type:*`
- one `priority:*`
- one `area:*`
- one `scope:*`
- one `verify:*` if helpful

### 3. Add a milestone only when it helps
Attach a milestone when the issue belongs to a bigger outcome bucket.
Do not force milestones onto every small issue.

### 4. Track progress in the issue itself
Use issue comments and, if desired, a lightweight `status:*` label.
A simple comment trail is enough:
- what was found
- what changed
- what was verified
- what remains risky or unverified

### 5. Close issues with verification notes
When closing an issue, add a short closing note with:
- fix summary
- verification performed
- remaining follow-up, if any

## Minimum Information For Every Issue

Recommended minimum issue content:
- clear title
- player-facing problem or goal
- relevant constraints or design notes
- acceptance criteria or expected outcome
- verification expectation
- labels
- milestone if part of larger work

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
- `Add weapon issue labels and verification workflow`
- `Document content pipeline for heroes / weapons / enemies`

Bad issue title examples:
- `multiplayer`
- `fix stuff`
- `cleanup`
- `weapon bugs and ui and balance`

## Simple Working Rhythm

Use three planning buckets inside this file and your milestones:
- **Now**: current priority work
- **Next**: queued important work
- **Later**: useful but not urgent

Suggested current focus:

### Now
- multiplayer balance/scaling
- spawn fairness
- regression-safe bug fixing

### Next
- UI / HUD polish
- documentation cleanup
- targeted content additions

### Later
- deeper performance profiling
- release prep and packaging cleanup

## Notes

This tracker should reflect the codebase as it exists now, not older planning docs.
Keep the workflow lightweight enough that opening and closing issues stays easy.
