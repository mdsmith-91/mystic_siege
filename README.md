# Mystic Siege

A top-down medieval fantasy survivor game built with Python and pygame-ce, inspired by Vampire Survivors and Brotato. Choose a hero, survive escalating waves of enemies, collect XP, level up, and pick upgrades in 15–30 minute sessions.

[![CI](https://github.com/mdsmith-91/mystic_siege/actions/workflows/ci.yml/badge.svg)](https://github.com/mdsmith-91/mystic_siege/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12.13-blue)
![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5%2B-orange)
![License](https://img.shields.io/github/license/mdsmith-91/mystic_siege)

---

## Features

- 3 hero classes with unique passives and starting weapons
- 6 weapon types with 5 upgrade levels each
- 7 enemy types with distinct behaviors (melee, ranged, phasing, orbiting, splitting)
- AI-generated 4-direction spritesheets for all 7 enemy types
- CursedKnight frontal shield mechanic — all weapons pass hit direction for accurate 80% block
- Progressive wave difficulty scaling over 30 minutes
- XP orb collection and leveling system with 3-card upgrade choices
- Visual effects: damage numbers, hit sparks, death explosions, level-up burst
- Persistent meta-progression saved between sessions
- Controller support with hot-plug detection and owned input routing for multiplayer-sensitive menus
- Screenshot capture (F12), FPS counter (F3), always runs fullscreen for maximum compatibility
- Full audio system with silent fallback — runs without any audio files

---

## Current Status

- Single-player is the stable baseline and should be treated as the first regression path.
- Local multiplayer is partially implemented, not feature-complete.
- New runs currently use `Menu -> Lobby -> queued Class Select -> Game -> Game Over`.
- Multiplayer foundations currently in the codebase:
  - lobby scene and per-player `PlayerSlot` metadata
  - queued hero select with duplicate-hero prevention
  - multi-player `GameScene` plumbing, HUD panels, camera zoom, and per-player XP state
  - owned controller input in class select and upgrade menus
  - downed / revive scaffolding for multiplayer runs
- Still in progress or not fully verified:
  - broad 2P/3P runtime verification
  - overall multiplayer balance and spawn scaling
  - regression hardening around edge cases
  - full 4-player support, because the current roster only has 3 unique heroes

## Current Limitations

- The long-term target is 1–4 local players, but the current runtime cap is effectively 3 simultaneous players because duplicate heroes are blocked and only 3 heroes exist.
- Solo runs still start through the lobby flow, but the in-game solo path preserves the legacy single-player gameplay behavior.
- Automated regression coverage is minimal; most verification is still manual.

## Hero Classes

| Hero | HP | Speed | Armor | Passive | Starting Weapon |
|------|----|-------|-------|---------|-----------------|
| Knight | 150 | 180 | 15 | 15% damage reduction, knockback immune | Spectral Blade |
| Wizard | 80 | 240 | 0 | +20% spell damage, +10% crit chance | Arcane Bolt |
| Friar | 110 | 210 | 5 | Heal 1 HP per 10 XP orbs collected | Holy Nova |

---

## Getting Started

**Requirements:** Python 3.12.13 and the packages in `requirements.txt`

```bash
# Clone the repo
git clone https://github.com/mdsmith-91/mystic_siege.git
cd mystic_siege

# Install dependencies
pip install -r requirements.txt

# Optional: generate placeholder sprites and audio if you need to recreate missing assets
python src/utils/placeholder_assets.py

# Run the game
python main.py
```

---

## Controls

### Keyboard & Mouse

| Action | Key |
|--------|-----|
| Join lobby | WASD keys or Arrow keys |
| Move | Assigned movement keys in-game |
| Pause | ESC |
| Select Upgrade (solo legacy path) | 1, 2, 3 |
| Toggle FPS Counter | F3 |
| Take Screenshot | F12 |

### Controller (Xbox / PlayStation / Switch Pro)

Controllers are detected automatically at startup and on hot-plug.

| Action | Input |
|--------|-------|
| Move | Left stick or D-pad |
| Confirm / Select | A / Cross |
| Back / Cancel / Pause | B / Circle or Start / Options |
| Navigate menus | Left stick or D-pad (with key-repeat) |

---

## Weapons

| Weapon | Behavior |
|--------|----------|
| Arcane Bolt | Homing projectiles; 1 → 3 bolts, pierce at level 4 |
| Holy Nova | Expanding damage ring around the player |
| Spectral Blade | Orbiting swords with per-enemy hit cooldown |
| Flame Whip | Directional cone sweep with burn DOT |
| Frost Ring | Expanding freeze ring that immobilizes enemies |
| Lightning Chain | Bolt chains between up to 6 nearby enemies |

---

## Development

```bash
# Check all imports and verify pygame-ce version
python run_check.py

# Regenerate placeholder sprites and audio for any missing assets
python src/utils/placeholder_assets.py
```

`run_check.py` imports the placeholder-asset utilities, so it requires `numpy` from `requirements.txt`.

## Verification

Recommended verification for the current state:

```bash
# Static import / environment check
python run_check.py
```

Manual smoke checks:

1. Start a solo run from the lobby, play into combat, die once, and confirm solo death/game-over behavior still works.
2. Join two players with different input devices, pick two different heroes, start a run, and confirm both players move independently.
3. Trigger a level-up in multiplayer and confirm only the owning player can confirm the upgrade on keyboard/controller.
4. Back out of class select and confirm the flow returns to the lobby rather than dropping to an unrelated scene.

**Adding real sprites:** Drop a PNG at the correct path under `assets/sprites/` — `ResourceLoader` picks it up automatically. No code changes needed.

**Adding real audio:** Drop a WAV file at the correct path under `assets/audio/sfx/` — `AudioManager` loads it at game start automatically. No code changes needed.

**Adding a new enemy:** Create `src/entities/enemies/newenemy.py` inheriting from `Enemy`, add spawn data to `wave_manager.py`, and add it to the wave timeline in `_check_timeline()`.

**Adding a new weapon:** Create `src/weapons/newweapon.py` inheriting from `BaseWeapon` and add the class name to `WEAPON_CLASSES` in `upgrade_system.py`.

---

## Project Structure

```
mystic_siege/
├── main.py                  # Entry point
├── settings.py              # All constants — never hardcode elsewhere
├── run_check.py             # Import checker + pygame version verifier
├── src/
│   ├── game.py              # Main loop, delegates to SceneManager
│   ├── scene_manager.py     # Scene switching across menu, lobby, class select, game, and game over
│   ├── game_scene.py        # Gameplay — wires solo and multiplayer-capable systems together
│   ├── core/
│   │   └── player_slot.py   # Plain per-slot session metadata
│   ├── entities/            # Player, enemies, projectiles, XP orbs, effects
│   ├── weapons/             # 6 weapon implementations
│   ├── systems/             # Waves, XP, upgrades, collision, camera, saves
│   ├── ui/                  # HUD, menus, lobby, queued class select, game over
│   └── utils/               # ResourceLoader, AudioManager, InputManager, Spritesheet, Timer
└── assets/
    ├── sprites/             # heroes / enemies / projectiles / effects / ui
    ├── audio/               # sfx / music
    ├── backgrounds/
    └── fonts/
```

## Known Issues

- Multiplayer balance is not yet tuned for larger parties.
- The repo includes some historical ad hoc test scripts that no longer reflect the current constructors or scene flow.
- The long-term design targets 4 local players, but the current hero roster blocks that from being fully playable without allowing duplicates or adding another hero.

---

## License

See [LICENSE](LICENSE).
