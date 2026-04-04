import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.entities.projectile import Projectile
from src.utils.spritesheet import Spritesheet
from settings import WORLD_WIDTH, WORLD_HEIGHT, LICH_FIRE_RANGE

# Column indices matching direction order in lich_meta.json
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class LichFamiliar(Enemy):
    def __init__(self, pos, player_list, all_groups: tuple, projectile_group=None, xp_orb_group=None, effect_group=None):
        enemy_data = {
            "name": "Lich",
            "hp": 35,
            "speed": 90,
            "damage": 12,
            "xp_value": 12,
            "behavior": "orbit"
        }
        super().__init__(pos, player_list, all_groups, enemy_data, xp_orb_group, effect_group)

        # Maintains orbit distance of ~200px from player, fires slow orb every 2.5s
        self.projectile_group = projectile_group

        self.orbit_angle = 0.0
        self.orbit_radius = 200
        self.fire_timer = 0.0
        self.fire_interval = 2.5

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/lich.png", 32, 32)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def update(self, dt):
        # Increment orbit angle and move toward orbit position around player
        self.orbit_angle += 45 * dt  # 45 degrees per second

        target = self.target
        if target is None:
            self.vel = Vector2(0, 0)
            super().update(dt)
            self.image = self._frame_for_velocity()
            self.rect = self.image.get_rect(center=self.pos)
            return

        target_pos = target.pos + Vector2(1, 0).rotate(self.orbit_angle) * self.orbit_radius

        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.vel = direction * self.speed

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)

        # Fire a slow magic orb at player every 2.5s, but only when close enough for
        # the projectile (speed=120, lifetime=4s, range=480px) to actually reach them
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            dist = (target.pos - self.pos).length()
            if 0 < dist < LICH_FIRE_RANGE:
                direction_to_player = (target.pos - self.pos) / dist
                proj_groups = [self.projectile_group] if self.projectile_group is not None else []
                Projectile(
                    pos=self.pos,
                    direction=direction_to_player,
                    speed=120,
                    damage=12,
                    groups=proj_groups,
                    enemy_group_ref=None,
                    pierce=0,
                    homing=False,
                    color=(200, 60, 255),
                    is_enemy_projectile=True
                )
            self.fire_timer = self.fire_interval
