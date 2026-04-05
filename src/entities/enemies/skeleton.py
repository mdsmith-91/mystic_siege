import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import WORLD_WIDTH, WORLD_HEIGHT

# Column indices matching DIRECTION_ORDER in generate_sprite.py
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class Skeleton(Enemy):
    def __init__(self, pos, player_list, all_groups: tuple, xp_orb_group=None, effect_group=None):
        enemy_data = {
            "name": "Skeleton",
            "hp": 30,
            "speed": 80,
            "damage": 10,
            "xp_value": 5,
            "behavior": "chase"
        }
        super().__init__(pos, player_list, all_groups, enemy_data, xp_orb_group, effect_group)

        # Add small random angle offset (±5 degrees, change every 0.5s) so they spread out
        self.angle_offset = 0.0
        self.angle_change_timer = 0.0

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

    def update(self, dt):
        # Add small random angle offset (±5 degrees, change every 0.5s) so they spread out
        self.angle_change_timer += dt
        if self.angle_change_timer >= 0.5:
            self.angle_offset = (pygame.time.get_ticks() % 1000) / 1000.0 * 10 - 5
            self.angle_change_timer = 0.0

        # Apply the angle offset to movement
        target = self.target
        if target is None:
            self.vel = Vector2(0, 0)
        else:
            direction = target.pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize().rotate(self.angle_offset)
                self.vel = direction * self.speed
            else:
                self.vel = Vector2(0, 0)

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)
