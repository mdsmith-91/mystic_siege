import pygame
from pygame.math import Vector2
import random
import math
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import WORLD_WIDTH, WORLD_HEIGHT

# Column indices matching direction order in bat_meta.json
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class PlagueBat(Enemy):
    def __init__(self, pos, target, all_groups: tuple, xp_orb_group=None, effect_group=None):
        enemy_data = {
            "name": "Bat",
            "hp": 15,
            "speed": 220,
            "damage": 8,
            "xp_value": 6,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data, xp_orb_group, effect_group)

        # split_chance = 0.4  — on death, 40% chance to spawn 2 mini bats
        self.split_chance = 0.4

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/bat.png", 32, 32)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

        # Track elapsed time for arc movement
        self._t = 0.0

        # Flag to indicate if this is a mini bat (for inheritance purposes)
        self.is_mini = False

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def update(self, dt):
        # Track elapsed time
        self._t += dt

        # Movement: arc pattern — add sine wave offset perpendicular to direction
        if hasattr(self, 'target') and self.target:
            direction = self.target.pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize()

                # Perpendicular direction (rotated 90 degrees)
                perpendicular = Vector2(-direction.y, direction.x)

                # Sine wave offset perpendicular to travel direction
                wave_offset = math.sin(self._t * 4)  # -1 to 1

                # Effective direction with wave offset
                effective_dir = direction + perpendicular * (wave_offset * 0.5)

                self.vel = effective_dir * self.speed
            else:
                self.vel = Vector2(0, 0)
        else:
            self.vel = Vector2(0, 0)

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)

    def on_death(self, xp_orb_group):
        """Handle plague bat death with chance to spawn mini bats."""
        super().on_death(xp_orb_group)

        if random.random() < self.split_chance and not self.is_mini:
            MiniBat(self.pos, self.target, self.all_groups, xp_orb_group, self.effect_group)
            MiniBat(self.pos, self.target, self.all_groups, xp_orb_group, self.effect_group)

class MiniBat(PlagueBat):
    """Mini bat spawned on PlagueBat death."""

    def __init__(self, pos, target, groups, xp_orb_group=None):
        super().__init__(pos, target, groups, xp_orb_group)
        self.is_mini = True

        # Override with mini bat stats
        self.max_hp = 7
        self.hp = 7
        self.speed = 280
        self.damage = 4
        self.xp_value = 3

        self.rect = self.image.get_rect(center=pos)
