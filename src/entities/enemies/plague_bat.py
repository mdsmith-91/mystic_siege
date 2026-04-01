import pygame
from pygame.math import Vector2
import random
import math
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class PlagueBat(Enemy):
    def __init__(self, pos, target, all_groups: tuple):
        # enemy_data = {name:"Bat", hp:15, speed:220, damage:8, xp_value:6, behavior:"chase"}
        enemy_data = {
            "name": "Bat",
            "hp": 15,
            "speed": 220,
            "damage": 8,
            "xp_value": 6,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data)

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
        # Call super().on_death() to spawn XP orb
        super().on_death(xp_orb_group)

        # If random() < split_chance and not self.is_mini:
        if random.random() < self.split_chance and not self.is_mini:
            # Spawn 2 MiniBat at self.pos
            # MiniBat is a nested subclass with hp=7, speed=280
            mini_bat1 = MiniBat(self.pos, self.target, self.groups())
            mini_bat2 = MiniBat(self.pos, self.target, self.groups())

            # Add to groups
            for group in self.groups():
                mini_bat1.add(group)
                mini_bat2.add(group)

class MiniBat(PlagueBat):
    """Nested subclass for mini bats that spawn on death."""

    def __init__(self, pos, target, groups):
        # Mini bat with hp=7, speed=280
        enemy_data = {
            "name": "MiniBat",
            "hp": 7,
            "speed": 280,
            "damage": 4,  # Reduced damage for mini bats
            "xp_value": 3,  # Reduced XP
            "behavior": "chase"
        }
        super().__init__(pos, target, groups)
        self.is_mini = True

        # Override image for mini bat
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        self.image.fill((80, 40, 80))  # Dark purple

        # Update rect
        self.rect = self.image.get_rect(center=pos)