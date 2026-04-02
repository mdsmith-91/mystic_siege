import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import WORLD_WIDTH, WORLD_HEIGHT

# Column indices matching direction order in goblin_meta.json
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class DarkGoblin(Enemy):
    def __init__(self, pos, target, all_groups: tuple, xp_orb_group=None, effect_group=None):
        enemy_data = {
            "name": "Goblin",
            "hp": 20,
            "speed": 160,
            "damage": 8,
            "xp_value": 4,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data, xp_orb_group, effect_group)

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/goblin.png", 32, 32)
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
        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)
