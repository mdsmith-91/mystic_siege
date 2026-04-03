# 🏰 MYSTIC SIEGE — Game Design Document
**A Medieval Fantasy Survivor (Vampire Survivors / Brotato-style)**
*Built with Python + Pygame | Team of 2 | Vibe-coded with Ollama + Claude*

---

## 1. VISION STATEMENT

Mystic Siege is a top-down auto-battler survivor game set in a collapsing medieval kingdom overrun by dark magic. Players choose a hero class, survive endless waves of enemies, collect spells and relics, and grow exponentially powerful — all in 15–30 minute run sessions.

**Core feel:** *"Tower defense meets bullet hell meets deck-building — but you ARE the tower."*

---

## 2. SCOPE (MVP FIRST)

### Phase 1 — Playable Core (MVP)
- 1 map (castle courtyard)
- 3 hero classes
- 6 weapons/spells
- 8 enemy types
- Basic upgrade system (level-up choices)
- Simple audio (placeholder/CC0)

### Phase 2 — Content Expansion
- 2 additional maps
- 3 more hero classes
- 10+ more weapons/spells
- Boss enemies
- Passive relic system
- Meta-progression (unlocks)

### Phase 3 — Polish
- Animated sprites (AI-generated or CC0 assets)
- Full audio
- Main menu, settings, achievements
- Save/load runs

---

## 3. TECH STACK

| Component | Tool |
|---|---|
| Language | Python 3.12.13 |
| Game Framework | Pygame-CE (community edition) |
| Asset Gen | DALL-E / Stable Diffusion / Kenney.nl / OpenGameArt |
| AI Coding | Ollama + Claude (claude-sonnet) |
| Version Control | Git + GitHub |
| Audio | CC0 from freesound.org / opengameart.org |

**Dependencies (requirements.txt):**
```
pygame-ce>=2.5.0
pytmx>=3.32
numpy>=1.26
```

---

## 4. PROJECT STRUCTURE

```
mystic_siege/
├── main.py                  # Entry point
├── settings.py              # Global constants & config
├── requirements.txt
├── README.md
│
├── assets/
│   ├── sprites/
│   │   ├── heroes/
│   │   ├── enemies/
│   │   ├── projectiles/
│   │   ├── effects/
│   │   └── ui/
│   ├── maps/
│   │   └── courtyard.tmx
│   ├── audio/
│   │   ├── sfx/
│   │   └── music/
│   └── fonts/
│
├── src/
│   ├── __init__.py
│   ├── game.py              # Main game loop & state manager
│   ├── scene_manager.py     # Scene switching (menu, game, gameover)
│   │
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── base_entity.py   # Base sprite class
│   │   ├── player.py        # Player controller
│   │   ├── enemy.py         # Base enemy class
│   │   ├── projectile.py    # Projectile base class
│   │   ├── xp_orb.py        # XP orb with auto-collect
│   │   ├── effects.py       # DamageNumber, HitSpark, DeathExplosion, LevelUpEffect
│   │   └── enemies/         # Specific enemy types
│   │       ├── skeleton.py
│   │       ├── dark_goblin.py
│   │       ├── wraith.py
│   │       ├── plague_bat.py
│   │       ├── cursed_knight.py
│   │       ├── lich_familiar.py
│   │       └── stone_golem.py
│   │
│   ├── weapons/
│   │   ├── __init__.py
│   │   ├── base_weapon.py
│   │   ├── arcane_bolt.py
│   │   ├── holy_nova.py
│   │   ├── flame_whip.py
│   │   ├── spectral_blade.py
│   │   ├── frost_ring.py
│   │   └── lightning_chain.py
│   │
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── wave_manager.py  # Enemy spawning & difficulty scaling
│   │   ├── xp_system.py     # XP collection, leveling
│   │   ├── upgrade_system.py# Level-up choices UI
│   │   ├── collision.py     # Collision detection
│   │   ├── camera.py        # Camera / scrolling
│   │   └── save_system.py   # JSON meta-progression
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── hud.py           # In-game HUD (HP, XP bar, timer, weapon icons)
│   │   ├── upgrade_menu.py  # Level-up selection screen
│   │   ├── main_menu.py
│   │   ├── class_select.py  # Hero selection screen
│   │   ├── game_over.py
│   │   ├── settings_menu.py # Volume sliders, show FPS toggle, reset
│   │   └── stats_menu.py    # Meta-progression stats viewer
│   │
│   └── utils/
│       ├── __init__.py
│       ├── spritesheet.py        # Sprite sheet parser
│       ├── timer.py              # Reusable countdown/interval timer
│       ├── resource_loader.py    # Centralized asset loading with fallback placeholders
│       ├── audio_manager.py      # Singleton audio with silent fallback
│       ├── input_manager.py      # Controller input with hot-plug and synthetic key events
│       └── placeholder_assets.py # Generates placeholder PNGs and WAVs
```

---

## 5. HERO CLASSES

### Knight
- **HP:** 150 | **Speed:** Medium | **Armor:** High
- **Passive:** Takes 15% less damage, knockback immune
- **Starting Weapon:** Spectral Blade (orbiting swords)
- **Playstyle:** Tank — survives by being a wall

### Wizard
- **HP:** 80 | **Speed:** High | **Armor:** None
- **Passive:** Spells deal 20% more damage, crit chance +10%
- **Starting Weapon:** Arcane Bolt (homing projectiles)
- **Playstyle:** Glass cannon — high risk, max damage

### Friar
- **HP:** 110 | **Speed:** Medium-High | **Armor:** Low
- **Passive:** Heals 1 HP per 10 XP orbs collected
- **Starting Weapon:** Holy Nova (area pulse)
- **Playstyle:** Sustain — snowballs with orb pickups

---

## 6. WEAPONS / SPELLS

| Name | Type | Behavior |
|---|---|---|
| Arcane Bolt | Projectile | Auto-fires homing bolts at nearest enemy |
| Holy Nova | Area Pulse | Expands ring of light around player, damages all in range |
| Flame Whip | Cone | Sweeping fire arc in front of movement direction |
| Spectral Blade | Orbit | 2–4 swords orbit player and pass through enemies |
| Frost Ring | Zone | Ice ring expands slowly, freezes enemies briefly |
| Lightning Chain | Chain | Bolt jumps between up to 6 enemies |

Each weapon has **5 upgrade levels** (damage, speed, area, count, special).

---

## 7. ENEMY TYPES (Phase 1)

| Enemy | HP | Speed | Behavior |
|---|---|---|---|
| Skeleton Grunt | 30 | Slow | Walks toward player |
| Dark Goblin | 20 | Fast | Swarms in groups of 3–5 |
| Wraith | 40 | Medium | Phases through walls, periodic lunge |
| Plague Bat | 15 | Very Fast | Swoops in arcs, splits on death |
| Stone Golem | 500 | Very Slow | One-time mini-boss, high HP |
| Cursed Knight | 80 | Medium | Frontal shield blocks 80% damage |
| Lich Familiar | 35 | Medium | Orbits player, fires slow magic orbs |

---

## 8. GAME LOOP

```
[Main Menu]
    ↓
[Class Select]
    ↓
[Game starts — 0:00]
    ↓ (loop)
[Player moves + auto-attacks]
[Enemies spawn from waves]
[Collect XP orbs from kills]
[Reach XP threshold → LEVEL UP]
[Choose 1 of 3 upgrades]
[Repeat — scaling difficulty every 60s]
    ↓
[Die OR Survive 30 minutes → Game Over / Victory Screen]
```

---

## 9. WAVE SCALING

| Time | Event |
|---|---|
| 0:00 | Skeleton Grunts only |
| 1:00 | Add Dark Goblins |
| 2:00 | Add Wraiths |
| 5:00 | Add Plague Bats — "BATS INCOMING!" warning |
| 8:00 | Mini-boss: Stone Golem (one-time) — "GOLEM APPROACHES!" warning |
| 10:00 | Add Cursed Knights + Lich Familiars |
| 15:00 | Elite mode (1.5× HP/damage) — "ELITE ENEMIES ARISE!" warning |
| 20:00 | Final assault (fastest spawn rate) — "FINAL ASSAULT!" warning |
| 30:00 | Victory condition |

---

## 10. UPGRADE SYSTEM

On level-up, player is shown 3 cards drawn from a weighted pool:
- New weapon (if slots available, max 6)
- Upgrade existing weapon (if owned)
- Passive stat boost (HP, speed, pickup radius, armor, regen)

**Passive Boosts Pool:**
- +20 Max HP
- +5% Movement Speed
- +10% Pickup Radius
- +5 Armor
- +0.5 HP/sec Regen
- +10% XP Gain
- +5% Cooldown Reduction

---

## 11. XP & PROGRESSION

- Enemies drop XP orbs on death
- Orbs are auto-collected when player is within pickup radius
- XP bar fills → triggers level-up pause (time stops)
- XP required scales: `next_level_xp = base_xp * (1.12 ^ level)`

---

## 12. MAP DESIGN (Phase 1)

**Castle Courtyard:**
- Walled arena, ~3000x3000 pixels (camera scrolls)
- Breakable/impassable wall segments
- Decorative props (barrels, crates, torch pillars)
- 4 enemy spawn points (N/S/E/W edges)
- Ambient: night sky, flickering torches

---

## 13. AUDIO PLAN

**SFX (CC0 sources: freesound.org, opengameart.org):**
- Player hit, player death
- Each weapon fire sound
- Enemy death (2-3 variants)
- XP pickup
- Level up chime
- Boss roar

**Music (CC0 from opengameart.org):**
- Main menu theme (medieval ambient)
- In-game track 1 (tense medieval)
- Boss battle track
- Victory / Game over stingers

---

## 14. ART DIRECTION

**Style:** Top-down 32x32 AI-generated sprites

**Palette:** Dark desaturated base (navy, charcoal, stone gray) with high-contrast magical accent colors (gold, cyan, purple, blood red)

**Enemy Sprites (implemented):** All 7 enemy types have AI-generated 4-direction spritesheets
(32×32 px, 4 cols: down/left/right/up, 1 row). Files live in `assets/sprites/enemies/` with
accompanying `*_meta.json` metadata. Each enemy selects a directional frame each frame based
on movement velocity via `_frame_for_velocity()`.

**Recommended Free Asset Sources:**
- https://kenney.nl (free game assets)
- https://opengameart.org
- https://itch.io (many free CC0 packs)
- AI generation: Stable Diffusion with pixel art LoRA

---

## 15. CODING CONVENTIONS (for AI-assisted dev)

- All classes use `pygame.sprite.Sprite` as base
- Use `pygame.sprite.Group` for batch updates/draws
- Game state uses a simple string enum: `"menu"`, `"playing"`, `"paused"`, `"gameover"`
- Delta time (`dt`) passed to all update methods
- Settings/constants in `settings.py` only — never hardcoded in logic files
- Comments: write intent, not mechanics ("# spawn enemy if timer fires" not "# if timer > 0")
