import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import SKELETON_ENEMY_DATA

# Column indices matching DIRECTION_ORDER in generate_sprite.py
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class Skeleton(Enemy):
    def __init__(
        self,
        pos,
        player_list,
        all_groups: tuple,
        xp_orb_group=None,
        effect_group=None,
        pickup_group=None,
        projectile_group=None,
    ):
        super().__init__(pos, player_list, all_groups, SKELETON_ENEMY_DATA, xp_orb_group, effect_group, pickup_group)

        # Add small random angle offset (±5 degrees, change every 0.5s) so they spread out
        self.angle_offset = 0.0
        self.angle_change_timer = 0.0
        self.angle_change_interval = SKELETON_ENEMY_DATA["wander_angle_change_interval"]
        self.angle_variance = SKELETON_ENEMY_DATA["wander_angle_max"]

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/skeleton.png", 32, 32)
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

    def _compute_velocity(self, target: pygame.sprite.Sprite | None) -> Vector2:
        """Apply the slight wandering offset on top of chase movement."""
        if target is None:
            return Vector2(0, 0)
        direction = target.pos - self.pos
        if direction.length_squared() <= 0:
            return Vector2(0, 0)
        direction = direction.normalize().rotate(self.angle_offset)
        return direction * self.speed

    def update(self, dt):
        # Add small random angle offset (±5 degrees, change every 0.5s) so they spread out
        self.angle_change_timer += dt
        if self.angle_change_timer >= self.angle_change_interval:
            self.angle_offset = (pygame.time.get_ticks() % 1000) / 1000.0 * (self.angle_variance * 2) - self.angle_variance
            self.angle_change_timer = 0.0

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)
