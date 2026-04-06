from pygame.math import Vector2
from settings import (
    DARK_GOBLIN_ENEMY_DATA,
    ENEMY_DATA_BY_ID,
    ENEMY_ELITE_DAMAGE_MULTIPLIER,
    ENEMY_ELITE_HP_MULTIPLIER,
    ENEMY_SPAWN_OFFSCREEN_MARGIN,
    ENEMY_SPAWN_POSITION_ATTEMPTS,
    ENEMY_WARNING_DURATION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STONE_GOLEM_ENEMY_DATA,
    WAVE_BAT_SPAWN_RATE,
    WAVE_BAT_UNLOCK_TIME,
    WAVE_BAT_WARNING_TEXT,
    WAVE_ELITE_MODE_TIME,
    WAVE_ELITE_SPAWN_RATE,
    WAVE_ELITE_WARNING_TEXT,
    WAVE_FINAL_ASSAULT_SPAWN_RATE,
    WAVE_FINAL_ASSAULT_TIME,
    WAVE_FINAL_ASSAULT_WARNING_TEXT,
    WAVE_GOBLIN_PACK_MAX,
    WAVE_GOBLIN_PACK_MIN,
    WAVE_GOBLIN_SPAWN_RATE,
    WAVE_GOBLIN_UNLOCK_TIME,
    WAVE_GOLEM_COUNT,
    WAVE_GOLEM_EVENT_TIME,
    WAVE_GOLEM_WARNING_TEXT,
    WAVE_INITIAL_ACTIVE_POOL,
    WAVE_INITIAL_SPAWN_RATE,
    WAVE_KNIGHT_LICH_SPAWN_RATE,
    WAVE_KNIGHT_LICH_UNLOCK_TIME,
    WAVE_VICTORY_TIME,
    WAVE_WRAITH_SPAWN_RATE,
    WAVE_WRAITH_UNLOCK_TIME,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from src.entities.enemies import create_enemy
import random

class WaveManager:
    def __init__(self, players, all_sprites, enemy_group, xp_orb_group, projectile_group=None, effect_group=None):
        self.players = players
        self.all_sprites = all_sprites
        self.enemy_group = enemy_group
        self.xp_orb_group = xp_orb_group
        self.projectile_group = projectile_group
        self.effect_group = effect_group

        # elapsed: float = 0.0
        self.elapsed = 0.0

        # spawn_timer: float = 0.0
        self.spawn_timer = 0.0

        # spawn_rate: float = INITIAL_SPAWN_RATE
        self.spawn_rate = WAVE_INITIAL_SPAWN_RATE

        # active_pool: list = ["Skeleton"]  — names of currently spawnable enemies
        self.active_pool = list(WAVE_INITIAL_ACTIVE_POOL)

        # elite_mode: bool = False
        self.elite_mode = False

        # warning_text: str = ""
        self.warning_text = ""

        # warning_timer: float = 0.0
        self.warning_timer = 0.0

        # Track triggered events to avoid duplicate triggers
        self.triggered_events = set()

        # Victory flag
        self.victory_flag = False

    def update(self, dt):
        """Update the wave manager."""
        # elapsed += dt
        self.elapsed += dt

        # Check timeline triggers
        self._check_timeline()

        # spawn_timer -= dt; if <= 0: _spawn_wave(); reset spawn_timer
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self._spawn_wave()
            self.spawn_timer = self.spawn_rate

        # Tick warning_timer
        if self.warning_timer > 0:
            self.warning_timer = max(0, self.warning_timer - dt)

    def _check_timeline(self):
        """Check wave timeline triggers."""
        # 0s:    active_pool = ["Skeleton"], spawn_rate = 3.0
        if 0 not in self.triggered_events and self.elapsed >= 0:
            self.active_pool = list(WAVE_INITIAL_ACTIVE_POOL)
            self.spawn_rate = WAVE_INITIAL_SPAWN_RATE
            self.triggered_events.add(0)

        # 60s:   add "Goblin", spawn_rate = 2.5
        if WAVE_GOBLIN_UNLOCK_TIME not in self.triggered_events and self.elapsed >= WAVE_GOBLIN_UNLOCK_TIME:
            self.active_pool.append("Goblin")
            self.spawn_rate = WAVE_GOBLIN_SPAWN_RATE
            self.triggered_events.add(WAVE_GOBLIN_UNLOCK_TIME)

        # 120s:  add "Wraith", spawn_rate = 2.0
        if WAVE_WRAITH_UNLOCK_TIME not in self.triggered_events and self.elapsed >= WAVE_WRAITH_UNLOCK_TIME:
            self.active_pool.append("Wraith")
            self.spawn_rate = WAVE_WRAITH_SPAWN_RATE
            self.triggered_events.add(WAVE_WRAITH_UNLOCK_TIME)

        # 300s:  add "Bat", spawn_rate = 1.5,  show warning "BATS INCOMING!"
        if WAVE_BAT_UNLOCK_TIME not in self.triggered_events and self.elapsed >= WAVE_BAT_UNLOCK_TIME:
            self.active_pool.append("Bat")
            self.spawn_rate = WAVE_BAT_SPAWN_RATE
            self.warning_text = WAVE_BAT_WARNING_TEXT
            self.warning_timer = ENEMY_WARNING_DURATION
            self.triggered_events.add(WAVE_BAT_UNLOCK_TIME)

        # 480s:  spawn 1 Golem (one-time event), show warning "GOLEM APPROACHES!"
        if WAVE_GOLEM_EVENT_TIME not in self.triggered_events and self.elapsed >= WAVE_GOLEM_EVENT_TIME:
            self._spawn_enemy(STONE_GOLEM_ENEMY_DATA, count=WAVE_GOLEM_COUNT)
            self.warning_text = WAVE_GOLEM_WARNING_TEXT
            self.warning_timer = ENEMY_WARNING_DURATION
            self.triggered_events.add(WAVE_GOLEM_EVENT_TIME)

        # 600s:  add "Knight", add "Lich", spawn_rate = 1.0
        if WAVE_KNIGHT_LICH_UNLOCK_TIME not in self.triggered_events and self.elapsed >= WAVE_KNIGHT_LICH_UNLOCK_TIME:
            self.active_pool.append("Knight")
            self.active_pool.append("Lich")
            self.spawn_rate = WAVE_KNIGHT_LICH_SPAWN_RATE
            self.triggered_events.add(WAVE_KNIGHT_LICH_UNLOCK_TIME)

        # 900s:  elite_mode = True, spawn_rate = 0.7, warning "ELITE ENEMIES ARISE!"
        if WAVE_ELITE_MODE_TIME not in self.triggered_events and self.elapsed >= WAVE_ELITE_MODE_TIME:
            self.elite_mode = True
            self.spawn_rate = WAVE_ELITE_SPAWN_RATE
            self.warning_text = WAVE_ELITE_WARNING_TEXT
            self.warning_timer = ENEMY_WARNING_DURATION
            self.triggered_events.add(WAVE_ELITE_MODE_TIME)

        # 1200s: spawn_rate = 0.5, show warning "FINAL ASSAULT!"
        if WAVE_FINAL_ASSAULT_TIME not in self.triggered_events and self.elapsed >= WAVE_FINAL_ASSAULT_TIME:
            self.spawn_rate = WAVE_FINAL_ASSAULT_SPAWN_RATE
            self.warning_text = WAVE_FINAL_ASSAULT_WARNING_TEXT
            self.warning_timer = ENEMY_WARNING_DURATION
            self.triggered_events.add(WAVE_FINAL_ASSAULT_TIME)

        # 1800s: set a victory_flag = True
        if WAVE_VICTORY_TIME not in self.triggered_events and self.elapsed >= WAVE_VICTORY_TIME:
            self.victory_flag = True
            self.triggered_events.add(WAVE_VICTORY_TIME)

    def _spawn_wave(self):
        """Spawn a wave of enemies."""
        # pick random enemy type from active_pool
        enemy_type = random.choice(self.active_pool)

        # Special: Goblin spawns in groups of 3-5
        if enemy_type == "Goblin":
            count = random.randint(WAVE_GOBLIN_PACK_MIN, WAVE_GOBLIN_PACK_MAX)
            for _ in range(count):
                self._spawn_enemy(DARK_GOBLIN_ENEMY_DATA)
        else:
            self._spawn_enemy(self._get_enemy_data(enemy_type))

    def _get_enemy_data(self, enemy_name):
        """Get enemy data by name."""
        return ENEMY_DATA_BY_ID.get(enemy_name, ENEMY_DATA_BY_ID["Skeleton"])

    def _spawn_enemy(self, data: dict, count: int = 1):
        """Spawn an enemy at a random edge of the world."""
        for _ in range(count):
            pos = self._get_spawn_pos()

            groups = (self.all_sprites, self.enemy_group)
            enemy_id = self._get_enemy_id(data)
            enemy = create_enemy(
                enemy_id=enemy_id,
                pos=pos,
                players=self.players,
                all_groups=groups,
                enemy_data=data,
                xp_orb_group=self.xp_orb_group,
                effect_group=self.effect_group,
                projectile_group=self.projectile_group,
            )

            # If elite_mode: multiply hp and damage by 1.5
            if self.elite_mode:
                enemy.max_hp = int(enemy.max_hp * ENEMY_ELITE_HP_MULTIPLIER)
                enemy.hp = enemy.max_hp
                enemy.damage = int(enemy.damage * ENEMY_ELITE_DAMAGE_MULTIPLIER)
                if hasattr(enemy, "projectile_damage"):
                    enemy.projectile_damage = int(enemy.projectile_damage * ENEMY_ELITE_DAMAGE_MULTIPLIER)

    def _get_enemy_id(self, enemy_data: dict) -> str:
        """Resolve the registry id for the provided settings-backed enemy data."""
        for enemy_id, registered_data in ENEMY_DATA_BY_ID.items():
            if registered_data is enemy_data:
                return enemy_id
        return enemy_data["name"]

    def _alive_players(self):
        return [player for player in self.players if player.is_alive]

    def _spawn_visibility_score(self, pos: Vector2, alive_players: list) -> float:
        """Higher scores are farther outside every alive player's local screen rect."""
        if not alive_players:
            return 0.0

        half_w = SCREEN_WIDTH / 2
        half_h = SCREEN_HEIGHT / 2
        score = float("inf")
        for player in alive_players:
            dx = abs(pos.x - player.pos.x)
            dy = abs(pos.y - player.pos.y)
            offscreen_margin = max(dx - half_w, dy - half_h)
            score = min(score, offscreen_margin)
        return score

    def _get_spawn_pos(self) -> Vector2:
        """Get a random point just outside the visible screen, relative to alive players."""
        # Margin beyond the screen half-extents so enemies spawn off-screen
        margin = ENEMY_SPAWN_OFFSCREEN_MARGIN
        half_w = SCREEN_WIDTH // 2 + margin
        half_h = SCREEN_HEIGHT // 2 + margin

        alive_players = self._alive_players()
        if alive_players:
            anchor = sum((player.pos for player in alive_players), Vector2()) / len(alive_players)
        else:
            anchor = Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
        px, py = anchor

        best_candidate = Vector2(px, py)
        best_score = float("-inf")

        for _ in range(ENEMY_SPAWN_POSITION_ATTEMPTS):
            edge = random.randint(0, 3)
            if edge == 0:  # Top
                x = px + random.randint(-half_w, half_w)
                y = py - half_h
            elif edge == 1:  # Right
                x = px + half_w
                y = py + random.randint(-half_h, half_h)
            elif edge == 2:  # Bottom
                x = px + random.randint(-half_w, half_w)
                y = py + half_h
            else:  # Left
                x = px - half_w
                y = py + random.randint(-half_h, half_h)

            candidate = Vector2(
                max(0, min(WORLD_WIDTH, x)),
                max(0, min(WORLD_HEIGHT, y)),
            )
            score = self._spawn_visibility_score(candidate, alive_players)
            if score > best_score:
                best_candidate = candidate
                best_score = score
            if score > 0:
                return candidate

        return best_candidate

    def get_elapsed_str(self) -> str:
        """Return elapsed time formatted as MM:SS."""
        minutes = int(self.elapsed // 60)
        seconds = int(self.elapsed % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_warning(self) -> str:
        """Return warning text if warning_timer > 0 else empty string."""
        if self.warning_timer > 0:
            return self.warning_text
        return ""
