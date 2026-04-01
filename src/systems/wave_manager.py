import pygame
from pygame.math import Vector2
from settings import INITIAL_SPAWN_RATE, WORLD_WIDTH, WORLD_HEIGHT
from src.entities.enemies.skeleton import Skeleton
from src.entities.enemies.dark_goblin import DarkGoblin
from src.entities.enemy import Enemy
from src.entities.enemies.wraith import Wraith
from src.entities.enemies.plague_bat import PlagueBat
from src.entities.enemies.cursed_knight import CursedKnight
from src.entities.enemies.lich_familiar import LichFamiliar
from src.entities.enemies.stone_golem import StoneGolem
import random

# Enemy data — define as module-level dicts (not classes yet)
SKELETON_DATA = {"name":"Skeleton", "hp":30, "speed":80, "damage":10, "xp_value":5, "behavior":"chase"}
GOBLIN_DATA = {"name":"Goblin", "hp":20, "speed":160, "damage":8, "xp_value":4, "behavior":"chase"}
WRAITH_DATA = {"name":"Wraith", "hp":40, "speed":120, "damage":15, "xp_value":10, "behavior":"chase"}
BAT_DATA = {"name":"Bat", "hp":15, "speed":220, "damage":8, "xp_value":6, "behavior":"chase"}
GOLEM_DATA = {"name":"Golem", "hp":500, "speed":40, "damage":40, "xp_value":80, "behavior":"chase"}
KNIGHT_DATA = {"name":"Knight", "hp":80, "speed":110, "damage":20, "xp_value":15, "behavior":"chase"}
LICH_DATA = {"name":"Lich", "hp":35, "speed":90, "damage":12, "xp_value":12, "behavior":"ranged"}

class WaveManager:
    def __init__(self, player, all_sprites, enemy_group, xp_orb_group, projectile_group=None):
        self.player = player
        self.all_sprites = all_sprites
        self.enemy_group = enemy_group
        self.xp_orb_group = xp_orb_group
        self.projectile_group = projectile_group

        # elapsed: float = 0.0
        self.elapsed = 0.0

        # spawn_timer: float = 0.0
        self.spawn_timer = 0.0

        # spawn_rate: float = INITIAL_SPAWN_RATE
        self.spawn_rate = INITIAL_SPAWN_RATE

        # active_pool: list = ["Skeleton"]  — names of currently spawnable enemies
        self.active_pool = ["Skeleton"]

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
            self.active_pool = ["Skeleton"]
            self.spawn_rate = 3.0
            self.triggered_events.add(0)

        # 60s:   add "Goblin", spawn_rate = 2.5
        if 60 not in self.triggered_events and self.elapsed >= 60:
            self.active_pool.append("Goblin")
            self.spawn_rate = 2.5
            self.triggered_events.add(60)

        # 120s:  add "Wraith", spawn_rate = 2.0
        if 120 not in self.triggered_events and self.elapsed >= 120:
            self.active_pool.append("Wraith")
            self.spawn_rate = 2.0
            self.triggered_events.add(120)

        # 300s:  add "Bat", spawn_rate = 1.5,  show warning "BATS INCOMING!"
        if 300 not in self.triggered_events and self.elapsed >= 300:
            self.active_pool.append("Bat")
            self.spawn_rate = 1.5
            self.warning_text = "BATS INCOMING!"
            self.warning_timer = 3.0  # Show warning for 3 seconds
            self.triggered_events.add(300)

        # 480s:  spawn 1 Golem (one-time event), show warning "GOLEM APPROACHES!"
        if 480 not in self.triggered_events and self.elapsed >= 480:
            self._spawn_enemy(GOLEM_DATA, count=1)
            self.warning_text = "GOLEM APPROACHES!"
            self.warning_timer = 3.0  # Show warning for 3 seconds
            self.triggered_events.add(480)

        # 600s:  add "Knight", add "Lich", spawn_rate = 1.0
        if 600 not in self.triggered_events and self.elapsed >= 600:
            self.active_pool.append("Knight")
            self.active_pool.append("Lich")
            self.spawn_rate = 1.0
            self.triggered_events.add(600)

        # 900s:  elite_mode = True, spawn_rate = 0.7, warning "ELITE ENEMIES ARISE!"
        if 900 not in self.triggered_events and self.elapsed >= 900:
            self.elite_mode = True
            self.spawn_rate = 0.7
            self.warning_text = "ELITE ENEMIES ARISE!"
            self.warning_timer = 3.0  # Show warning for 3 seconds
            self.triggered_events.add(900)

        # 1200s: spawn_rate = 0.5, show warning "FINAL ASSAULT!"
        if 1200 not in self.triggered_events and self.elapsed >= 1200:
            self.spawn_rate = 0.5
            self.warning_text = "FINAL ASSAULT!"
            self.warning_timer = 3.0  # Show warning for 3 seconds
            self.triggered_events.add(1200)

        # 1800s: set a victory_flag = True
        if 1800 not in self.triggered_events and self.elapsed >= 1800:
            self.victory_flag = True
            self.triggered_events.add(1800)

    def _spawn_wave(self):
        """Spawn a wave of enemies."""
        # pick random enemy type from active_pool
        enemy_type = random.choice(self.active_pool)

        # Special: Goblin spawns in groups of 3-5
        if enemy_type == "Goblin":
            count = random.randint(3, 5)
            for _ in range(count):
                self._spawn_enemy(GOBLIN_DATA)
        else:
            self._spawn_enemy(self._get_enemy_data(enemy_type))

    def _get_enemy_data(self, enemy_name):
        """Get enemy data by name."""
        if enemy_name == "Skeleton":
            return SKELETON_DATA
        elif enemy_name == "Goblin":
            return GOBLIN_DATA
        elif enemy_name == "Wraith":
            return WRAITH_DATA
        elif enemy_name == "Bat":
            return BAT_DATA
        elif enemy_name == "Golem":
            return GOLEM_DATA
        elif enemy_name == "Knight":
            return KNIGHT_DATA
        elif enemy_name == "Lich":
            return LICH_DATA
        else:
            return SKELETON_DATA  # Default fallback

    def _spawn_enemy(self, data: dict, count: int = 1):
        """Spawn an enemy at a random edge of the world."""
        for _ in range(count):
            pos = self._get_spawn_pos()

            # Import correct class based on data["name"]
            groups = (self.all_sprites, self.enemy_group)
            if data["name"] == "Skeleton":
                enemy = Skeleton(pos, self.player, groups)
            elif data["name"] == "Goblin":
                enemy = DarkGoblin(pos, self.player, groups)
            elif data["name"] == "Wraith":
                enemy = Wraith(pos, self.player, groups)
            elif data["name"] == "Bat":
                enemy = PlagueBat(pos, self.player, groups)
            elif data["name"] == "Golem":
                enemy = StoneGolem(pos, self.player, groups)
            elif data["name"] == "Knight":
                enemy = CursedKnight(pos, self.player, groups)
            elif data["name"] == "Lich":
                enemy = LichFamiliar(pos, self.player, groups, self.projectile_group)
            else:
                enemy = Enemy(pos, self.player, groups, data)

            # If elite_mode: multiply hp and damage by 1.5
            if self.elite_mode:
                enemy.max_hp = int(enemy.max_hp * 1.5)
                enemy.hp = enemy.max_hp
                enemy.damage = int(enemy.damage * 1.5)

            # Add to all_sprites and enemy_group
            enemy.add(self.all_sprites)
            enemy.add(self.enemy_group)

    def _get_spawn_pos(self) -> Vector2:
        """Get a random point on one of 4 world edges, 100px outside screen view."""
        # Choose edge (0=top, 1=right, 2=bottom, 3=left)
        edge = random.randint(0, 3)

        if edge == 0:  # Top
            x = random.randint(-100, WORLD_WIDTH + 100)
            y = -100
        elif edge == 1:  # Right
            x = WORLD_WIDTH + 100
            y = random.randint(-100, WORLD_HEIGHT + 100)
        elif edge == 2:  # Bottom
            x = random.randint(-100, WORLD_WIDTH + 100)
            y = WORLD_HEIGHT + 100
        else:  # Left
            x = -100
            y = random.randint(-100, WORLD_HEIGHT + 100)

        return Vector2(x, y)

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