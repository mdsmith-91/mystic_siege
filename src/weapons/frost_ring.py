import pygame
from src.weapons.base_weapon import BaseWeapon
from pygame.math import Vector2
import math
from src.utils.audio_manager import AudioManager

class FrostRing(BaseWeapon):
    name = "Frost Ring"
    description = "Expands a freezing ring outward, temporarily immobilizing enemies."
    base_damage = 15.0
    base_cooldown = 3.0
    ring_speed = 80  # px per second outward
    max_radius = 200
    freeze_duration = 1.5

    def __init__(self, owner, projectile_group, enemy_group):
        super().__init__(owner, projectile_group, enemy_group)

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"freeze_duration": 0.5},  # L2: +0.5 freeze duration
            {"base_damage": 10},  # L3: +10 damage
            {"ring_speed": 30},  # L4: +30 ring speed
            {"base_cooldown": -0.8, "max_radius": 80}  # L5: more frequent, bigger reach
        ]

        # Track frozen enemies: dict {enemy_id: remaining_freeze_time}
        self.frozen_enemies = {}

        # Active rings list: each ring is {radius: float, damage_done: set(), center: Vector2}
        self.rings = []

    def fire(self):
        """Emit a new frost ring."""
        AudioManager.instance().play_sfx(AudioManager.WEAPON_FROST)
        # Append new ring dict with initial center position
        ring = {
            "radius": 0,
            "damage_done": set(),
            "center": self.owner.pos.copy()  # Store initial position where ring was cast
        }
        self.rings.append(ring)

    def update(self, dt):
        """Update all active rings and frozen enemies."""
        # Update cooldown timer
        super().update(dt)

        # Tick freeze timers, restore speed when timer hits 0
        for enemy_id in list(self.frozen_enemies.keys()):
            self.frozen_enemies[enemy_id] -= dt
            if self.frozen_enemies[enemy_id] <= 0:
                # Restore enemy speed
                enemy = None
                for e in self.enemy_group:
                    if e.sprite_id == enemy_id:
                        enemy = e
                        break
                if enemy:
                    if hasattr(enemy, 'max_speed'):
                        enemy.speed = enemy.max_speed  # Restore original speed
                del self.frozen_enemies[enemy_id]

        # Expand all rings and check for collisions
        i = 0
        while i < len(self.rings):
            ring = self.rings[i]

            # Expand the ring
            ring["radius"] += self.ring_speed * dt

            # Check each ring against enemies (circle vs rect)
            for enemy in self.enemy_group:
                # Calculate distance from ring center to enemy center
                distance = (enemy.pos - ring["center"]).length()

                # Check if enemy is within the ring
                if (distance >= ring["radius"] - 5 and  # Allow some overlap
                    distance <= ring["radius"] + 5):  # Allow some overlap

                    # Check if this enemy has already been damaged by this ring
                    if enemy.sprite_id not in ring["damage_done"]:
                        # Deal damage
                        damage = self.base_damage * self.owner.damage_multiplier
                        enemy.take_damage(damage)

                        # Freeze enemy — only save max_speed if not already frozen
                        self.frozen_enemies[enemy.sprite_id] = self.freeze_duration
                        if enemy.speed > 0:
                            enemy.max_speed = enemy.speed
                        enemy.speed = 0

                        # Add to done set
                        ring["damage_done"].add(enemy.sprite_id)

            # Remove rings exceeding max_radius
            if ring["radius"] > self.max_radius:
                self.rings.pop(i)
            else:
                i += 1

    def draw(self, surface, camera_offset):
        """Draw the frost rings."""
        for ring in self.rings:
            # Draw ring as a cyan circle outline (pygame.draw.circle with width=3)
            center = ring["center"]
            radius = ring["radius"]
            pygame.draw.circle(surface, (0, 200, 255),  # Cyan color
                             (int(center.x - camera_offset.x), int(center.y - camera_offset.y)),
                             int(radius), 3)  # Width = 3