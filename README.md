# Mystic Siege

A top-down medieval fantasy survivor game built with Python and pygame-ce, inspired by Vampire Survivors and Brotato. Choose a hero, survive escalating waves, collect XP, level up, and build out a run over a 15–30 minute session.

[![CI](https://github.com/mdsmith-91/mystic_siege/actions/workflows/ci.yml/badge.svg)](https://github.com/mdsmith-91/mystic_siege/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12.13-blue)
![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5%2B-orange)
![License](https://img.shields.io/github/license/mdsmith-91/mystic_siege)

---

## What the Game Currently Is

Mystic Siege is a playable survivor-style action game with:

- 4 hero classes with unique passives and starting weapons
- 7 weapon types with 5 upgrade levels each
- 7 enemy types with distinct behaviors
- 30-minute wave progression with victory at 30:00
- persistent machine-local meta stats in `saves/progress.json`
- controller support, hot-plug detection, and remappable controller confirm/back/pause bindings

Current run flow:

```text
Main Menu -> Lobby -> queued Class Select -> Game -> Game Over -> Lobby or Menu
```

## Current Project Status

### Single-player

Single-player is the stable baseline. Solo runs now start through the same lobby-based scene flow as multiplayer, but the in-run solo gameplay path is still treated as the first regression path and is intended to preserve the legacy single-player feel.

### Local co-op

Local co-op is implemented and runtime-verified for 1–4 players. The codebase includes:

- slot-based lobby join/leave with `PlayerSlot`
- queued hero selection with duplicate-hero lockout
- multiplayer-capable `GameScene` plumbing
- per-player XP state and queued upgrade menus
- multi-player HUD panels, threat arrows, and camera zoom support
- downed / revive runtime support for multiplayer runs
- owned controller handling in lobby, class select, upgrade menus, and reconnect/reclaim flows
- controller binding settings with a global default profile plus per-controller overrides

Local co-op has been runtime-verified for 1P–4P. The remaining open items are balance tuning and spawn fairness under wide party spread, not core architecture.

### Verified vs unverified

Verified in runtime (1P–4P):

- full lobby join/leave and device ownership
- queued hero select with duplicate lockout
- upgrade queue ownership and menu isolation
- revive/downed behavior
- camera and HUD readability across 1–4 players
- controller disconnect/reclaim behavior
- save/progression updates after multiplayer runs

Verified in repo tooling:

- `python run_check.py` for import/environment integrity

Not yet verified:

- multiplayer balance/scaling (enemy density, wave pressure, and scaling for larger parties not yet tuned)
- spawn fairness under wide edge-spread party positions at high player counts

## Current Limitations

- The design target remains 1-4 local players, and the current hero roster now supports 4 practical local players because there are 4 heroes and duplicate picks are blocked.
- Multiplayer balance is not tuned yet. Enemy density, wave pressure, and scaling are not finalized for larger parties.
- Save/progression is machine-aggregated, not person-specific. Multiplayer runs still update one shared `saves/progress.json`.
- XP orb collection is shared-pool. On equal-distance ties, the lower slot index wins.
- Automated gameplay regression coverage is minimal; most meaningful verification is still manual.

## Hero Classes

| Hero | HP | Speed | Armor | Passive | Starting Weapon |
|------|----|-------|-------|---------|-----------------|
| Knight | 150 | 180 | 15 | 15% damage reduction, knockback immune | Spectral Blade |
| Wizard | 80 | 240 | 0 | +20% spell damage, +10% crit chance | Arcane Bolt |
| Friar | 110 | 210 | 5 | Heal based on XP gained (`FRIAR_HEAL_PER_XP`) | Holy Nova |
| Ranger | 95 | 225 | 3 | +10% crit chance, arrows pierce +1 enemy | Longbow |

## Hero Architecture

- `settings.py` is also the source of truth for hero definitions through `HERO_CLASSES`.
- Each hero record now includes declarative passive config in a `passives` dict, in addition to display text in `passive_desc`.
- Current runtime systems read those passive values instead of hardcoding hero-name checks for Knight, Wizard, Friar, and Ranger behavior.
- Hero records remain plain dicts so lobby, class select, and gameplay can keep using the current lightweight data flow.

## Weapon Architecture

- `settings.py` is the source of truth for weapon tunables, including base stats, relevant visual tunables, and per-level upgrade deltas.
- Weapon classes in `src/weapons/` reference those constants instead of hardcoding gameplay values locally.
- Shared weapon construction now goes through `src/weapons/factory.py` via `WEAPON_CLASS_REGISTRY` and `create_weapon()`.
- Hero `starting_weapon` values in `settings.HERO_CLASSES` are string ids, and `GameScene` resolves those ids through `create_weapon()` when building each player's starting loadout.
- Upgrade unlocks stay string-based as well: `UpgradeSystem` offers and applies weapon rewards by id, then resolves those ids through the same shared factory path.
- `src/weapons/__init__.py` re-exports the registry and constructor helper as the package-level weapon API.
- `src/systems/upgrade_system.py` owns upgrade-card metadata in `WEAPON_META` and the unlockable weapon-id list in `WEAPON_CLASSES`, while `settings.py` remains the source of truth for gameplay tunables.
- The intended ownership split is: `settings.py` for gameplay values, `src/weapons/factory.py` for id-to-class lookup, and `src/systems/upgrade_system.py` for player-facing card metadata.
- `GameScene` and `UpgradeSystem` should not grow new weapon-specific `if/elif` constructor chains. Register the weapon once in the factory and keep callers on the shared lookup path.
- Weapon ids remain string-based (`ArcaneBolt`, `HolyNova`, `SpectralBlade`, `FlameBlast`, `FrostRing`, `LightningChain`, `Longbow`) because hero data and upgrade choices reference them directly.
- Player-facing weapon names can differ from internal ids; for example, `FlameBlast` is shown in-game as `Flame Blast`.
- HUD styling that is intentionally derived from weapon-slot chrome is also centralized in `settings.py`; `HUD_EMPTY_SLOT_BG_COLOR` now drives both empty weapon slots and HP/XP bar backgrounds in `src/ui/hud.py`.
- The in-run HUD is now shared between solo and multiplayer: player panels use a 4-segment border tracker around occupied weapon slots that fills top, right, bottom, then left as levels 2–5 are earned. Unearned sections use the same gray baseline as empty weapon slots, and the segment tunables live in `settings.py`.
- The shared HUD renderer now caches stable panel rect conversion, weapon-slot row geometry, weapon icon surfaces, and text surfaces inside `src/ui/hud.py` rather than rebuilding equivalent data every frame. Offscreen downed-player revive rings are culled while teammate threat arrows remain active.

## Enemy Architecture

- `settings.py` is now the source of truth for enemy tunables as well, including shared enemy values, per-enemy config dicts, and wave/spawn balance data.
- Enemy classes in `src/entities/enemies/` read their gameplay stats and behavior knobs from those settings-driven configs instead of redefining local stat dicts.
- Shared enemy construction now goes through `src/entities/enemies/__init__.py` via `ENEMY_CLASS_REGISTRY` and `create_enemy()`.
- `src/systems/wave_manager.py` resolves enemy ids through that shared helper and should not grow new enemy-specific constructor chains.
- Enemy ids remain string-based (`Skeleton`, `Goblin`, `Wraith`, `Bat`, `Knight`, `Lich`, `Golem`) because wave pools and settings lookups reference them directly.
- Concrete enemy constructors now follow one shared call shape so the registry can instantiate them uniformly; optional dependencies such as `projectile_group` should only be consumed by enemies that need them.
- Shared enemy runtime state now lives in the base enemy / wave systems as well: retarget cadence, freeze / stun timers, effective speed rebuilding, elite projectile scaling, and spawn retry behavior near map edges are centralized instead of being ad hoc per subclass or per weapon.
- Enemy-specific movement should be expressed through the base enemy movement hook so subclass behaviors such as Skeleton wander and PlagueBat swoop remain active when the parent class updates targeting and movement each frame.
- `MiniBat` remains a plague-bat local follow-on spawned on death, not a top-level wave enemy.

## Getting Started

Requirements:

- Python 3.12.13
- dependencies from `requirements.txt`

```bash
git clone https://github.com/mdsmith-91/mystic_siege.git
cd mystic_siege
pip install -r requirements.txt
python main.py
```

Optional first-time helper:

```bash
python src/utils/placeholder_assets.py
```

## Controls

### Keyboard

| Action | Key |
|--------|-----|
| Join lobby | Press WASD keys or Arrow keys |
| Move in-game | Assigned scheme movement keys |
| Pause | ESC |
| Toggle FPS counter | F3 |
| Take screenshot | F12 |

Owned menu keyboard bindings:

- `WASD` slot: `A/D` navigate, `Space` confirm, `Left Shift` back
- `Arrows` slot: `Left/Right` navigate, `Enter` confirm, `Right Shift` back
- solo keyboard-owned menus still allow `Enter` as a compatibility confirm path

### Controller

Controllers are detected at startup and on hot-plug.

| Action | Input |
|--------|-------|
| Move | Left stick or D-pad |
| Confirm / Select | Configurable in Settings |
| Back / Cancel | Configurable in Settings |
| Pause | Configurable in Settings |
| Navigate menus | Left stick or D-pad |

Controller binding notes:

- `Settings -> Controller Bindings` exposes a `Global Default` profile and per-controller profiles.
- Synthetic controller key events now include source metadata, but owned multiplayer menus still must route or reject them deliberately to preserve device ownership.
- In-run controller disconnects pause gameplay until the affected slot is reclaimed or safely remapped.

## Development

Useful commands:

```bash
python main.py
python run_check.py
python src/utils/placeholder_assets.py
```

`run_check.py` validates imports and pygame-ce availability. It does not prove gameplay correctness.

## Verification

Baseline repo check:

```bash
python run_check.py
```

Recommended manual verification for the current state:

1. Start a 1P run through `Menu -> Lobby -> Class Select -> Game` and confirm movement, combat, level-up, death, and game-over behavior still work.
2. Start a 2P run with different devices, verify independent movement/input ownership, and confirm duplicate hero selection is blocked.
3. Trigger a multiplayer level-up and confirm only the owning slot can resolve its upgrade menu.
4. Disconnect and reclaim a controller mid-run and confirm gameplay stays safely paused until the slot is recovered.
5. Finish a multiplayer run and confirm the game-over screen shows party results while `saves/progress.json` updates aggregate run totals.

## Safe Next Work

Runtime verification is complete for 1P–4P. The next work is content and balance. In priority order:

1. Decide and implement multiplayer balance/scaling policy (enemy density, wave pressure for 2–4 players).
2. Validate spawn fairness under wide party spread near map edges.
3. Add new content (heroes, weapons, enemies) — the multiplayer foundation is now solid.

## Project Structure

```text
mystic_siege/
├── main.py
├── settings.py
├── run_check.py
├── src/
│   ├── game.py
│   ├── scene_manager.py
│   ├── game_scene.py
│   ├── core/player_slot.py
│   ├── entities/
│   ├── weapons/
│   │   ├── __init__.py
│   │   ├── factory.py
│   ├── systems/
│   ├── ui/
│   │   ├── lobby_scene.py
│   │   ├── class_select.py
│   │   ├── upgrade_menu.py
│   │   ├── hud.py
│   │   ├── game_over.py
│   │   ├── settings_menu.py
│   │   └── stats_menu.py
│   └── utils/
└── assets/
```

## Known Issues

- Multiplayer balance/scaling is not yet tuned for 2–4 player parties. Enemy density and wave pressure reflect the solo design.
- Wide-spread party positions near map edges may still need spawn fairness tuning under high player counts.
- Some older planning docs in the repo (e.g., `MULTIPLAYER_READINESS_AUDIT.md`) are partially historical and should not be treated as current implementation status.

## License

See [LICENSE](LICENSE).
