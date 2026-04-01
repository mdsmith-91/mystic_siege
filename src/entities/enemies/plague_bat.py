import pygame
from pygame.math import Vector2
import random
import math
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class PlagueBat(Enemy):
    def __init__(self, pos, target, all_groups: tuple, xp_orb_group=None):
        enemy_data = {
            "name": "Bat",
            "hp": 15,
            "speed": 220,
            "damage": 8,
            "xp_value": 6,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data, xp_orb_group)

        # split_chance = 0.4  — on death, 40% chance to spawn 2 mini bats
        self.split_chance = 0.4

        # Override image: 20x20 dark purple rect
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.image.fill((80, 40, 80))  # Dark purple

        # Update rect
        self.rect = self.image.get_rect(center=pos)

        # Track elapsed time for arc movement
        self._t = 0.0

        # Flag to indicate if this is a mini bat (for inheritance purposes)
        self.is_mini = False

    def update(self, dt):
        # Track elapsed time
        self._t += dt

        # Movement: arc pattern — add sine wave offset perpendicular to direction
        if hasattr(self, 'target') and self.target:
            # Calculate direction to target
            direction = self.target.pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize()

                # Perpendicular direction (rotated 90 degrees)
                perpendicular = Vector2(-direction.y, direction.x)

                # Sine wave offset perpendicular to travel direction
                wave_offset = math.sin(self._t * 4)  # -1 to 1

                # Effective direction with wave offset
                effective_dir = direction + perpendicular * (wave_offset * 0.5)

                # Apply movement
                self.vel = effective_dir * self.speed
            else:
                self.vel = Vector2(0, 0)
        else:
            self.vel = Vector2(0, 0)

        # Call super.update() to handle movement and other updates
        super().update(dt)

    def on_death(self, xp_orb_group):
        """Handle plague bat death with chance to spawn mini bats."""
        super().on_death(xp_orb_group)

        if random.random() < self.split_chance and not self.is_mini:
            # Use stored all_groups (self.groups() is empty after kill())
            MiniBat(self.pos, self.target, self.all_groups, xp_orb_group)
            MiniBat(self.pos, self.target, self.all_groups, xp_orb_group)

class MiniBat(PlagueBat):
    """Mini bat spawned on PlagueBat death."""

    def __init__(self, pos, target, groups, xp_orb_group=None):
        super().__init__(pos, target, groups, xp_orb_group)
        self.is_mini = True

        # Override with mini bat stats (PlagueBat.__init__ hardcodes full bat stats)
        self.max_hp = 7
        self.hp = 7
        self.speed = 280
        self.damage = 4
        self.xp_value = 3

        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        self.image.fill((80, 40, 80))
        self.rect = self.image.get_rect(center=pos)