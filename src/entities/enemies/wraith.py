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

class Wraith(Enemy):
    def __init__(self, pos, target, all_groups: tuple, xp_orb_group=None):
        enemy_data = {
            "name": "Wraith",
            "hp": 40,
            "speed": 120,
            "damage": 15,
            "xp_value": 10,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data, xp_orb_group)

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/wraith.png", 32, 32)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

        # lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
        # (lunge_active: bool, lunge_duration countdown)
        self.lunge_timer = 3.0
        self.lunge_active = False
        self.lunge_duration = 0.0

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def update(self, dt):
        # lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
        # (lunge_active: bool, lunge_duration countdown)
        if not self.lunge_active:
            self.lunge_timer -= dt
            if self.lunge_timer <= 0:
                # Start lunge
                self.lunge_active = True
                self.lunge_duration = 0.4
                self.speed *= 3  # Triple speed
        else:
            # During lunge
            self.lunge_duration -= dt
            if self.lunge_duration <= 0:
                # End lunge — restore speed and reset timer for next lunge
                self.lunge_active = False
                self.speed /= 3
                self.lunge_timer = 3.0

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)

        # Note: Wraith ignores wall collision (no clamping to world bounds in update)
        # This means it can pass through walls, which is the intended behavior