import pygame
from src.weapons.base_weapon import BaseWeapon
from pygame.math import Vector2
import math
from src.utils.audio_manager import AudioManager

class FlameWhip(BaseWeapon):
    name = "Flame Whip"
    description = "Lashes a cone of fire in your facing direction."
    base_damage = 30.0
    base_cooldown = 1.5
    cone_range = 120
    cone_angle = 90  # degrees total arc
    burn_damage = 5.0  # per second
    burn_duration = 2.0  # seconds

    def __init__(self, owner, projectile_group, enemy_group):
        super().__init__(owner, projectile_group, enemy_group)

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"base_damage": 15},  # L2: +15 damage
            {"cone_range": 40},  # L3: +40 range
            {"burn_duration": 1.5},  # L4: +1.5 burn duration
            {"cone_angle": 30, "base_damage": 20}  # L5: wider cone, more damage
        ]

        # Track burning enemies: dict {enemy_id: remaining_burn_time}
        self.burning_enemies = {}

        # Store a swing_timer float
        self.swing_timer = 0.0

    def fire(self):
        """Lash a cone of fire in the player's facing direction."""
        AudioManager.instance().play_sfx(AudioManager.WEAPON_WHIP)
        # Get owner.facing direction
        facing = self.owner.facing

        # For each enemy in enemy_group:
        for enemy in self.enemy_group:
            # dist = distance from owner.pos to enemy.pos
            dist = (enemy.pos - self.owner.pos).length()

            # if dist > cone_range: skip
            if dist > self.cone_range:
                continue

            # angle_to_enemy = angle between owner.facing and direction to enemy
            direction_to_enemy = (enemy.pos - self.owner.pos).normalize()
            angle_to_enemy = facing.angle_to(direction_to_enemy)

            # if angle_to_enemy <= cone_angle/2: hit the enemy
            if abs(angle_to_enemy) <= self.cone_angle / 2:
                # deal base_damage * owner.damage_multiplier
                damage = self.base_damage * self.owner.damage_multiplier
                enemy.take_damage(damage)

                # apply burn (add to burn dict)
                self.burning_enemies[enemy.sprite_id] = self.burn_duration

        # Set swing timer to 0.2s (visible for 0.2s after firing)
        self.swing_timer = 0.2

    def update(self, dt):
        """Update the flame whip effect."""
        # Update cooldown timer
        super().update(dt)

        # Tick down swing timer
        self.swing_timer = max(0, self.swing_timer - dt)

        # Tick down burn timers and apply burn damage
        for enemy_id in list(self.burning_enemies.keys()):
            self.burning_enemies[enemy_id] -= dt
            if self.burning_enemies[enemy_id] > 0:
                # Apply burn damage
                enemy = None
                for e in self.enemy_group:
                    if e.sprite_id == enemy_id:
                        enemy = e
                        break
                if enemy:
                    enemy.take_damage(self.burn_damage * dt)
            else:
                # Remove expired burn
                del self.burning_enemies[enemy_id]

    def draw_effect(self, surface, camera_offset):
        """Draw a transparent orange fan shape for the duration of the swing."""
        if self.swing_timer > 0:
            # Draw a fan shape representing the flame whip
            center = self.owner.pos
            facing = self.owner.facing

            # Calculate the start and end angles for the cone
            start_angle = facing.angle_to(Vector2(1, 0)) - self.cone_angle / 2
            end_angle = facing.angle_to(Vector2(1, 0)) + self.cone_angle / 2

            # Create points for the fan shape
            points = [center]

            # Add points along the arc
            num_points = 10
            for i in range(num_points + 1):
                angle = start_angle + (end_angle - start_angle) * i / num_points
                point = center + Vector2(1, 0).rotate(angle) * self.cone_range
                points.append(point)

            # Draw the fan shape with transparency
            if len(points) >= 3:
                alpha = int(100 * (self.swing_timer / 0.2))  # Fade out as timer decreases
                color = (255, 100, 0, alpha)  # Orange with alpha
                pygame.draw.polygon(surface, color,
                                  [(p.x - camera_offset.x, p.y - camera_offset.y) for p in points])