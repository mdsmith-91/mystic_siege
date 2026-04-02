import pygame
from src.weapons.base_weapon import BaseWeapon
from pygame.math import Vector2
import math
import random
from src.utils.audio_manager import AudioManager
from settings import CRIT_MULTIPLIER

class SpectralBlade(BaseWeapon):
    name = "Spectral Blade"
    description = "Spectral swords orbit the player, passing through enemies."
    base_damage = 18.0
    base_cooldown = 0.0  # no cooldown — orbiting continuously
    blade_count = 2
    orbit_radius = 90
    orbit_speed = 180  # degrees per second
    blade_size = (24, 8)
    orbit_angle = 0.0  # current rotation, increments each frame
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"blade_count": 1},      # L2: 3 blades
            {"orbit_speed": 60},     # L3: faster rotation
            {"orbit_radius": 20},    # L4: wider orbit
            {"blade_count": 1, "base_damage": 12}  # L5: 4 blades, more damage
        ]

        # Per-enemy hit cooldown dict: {enemy_id: timer} — each enemy can only be hit once per 0.5s
        self.enemy_cooldowns = {}

    def fire(self):
        pass  # SpectralBlade deals damage via continuous orbital collision in update()

    def update(self, dt):
        """Update the orbiting blades and check for enemy collisions."""
        # orbit_angle += orbit_speed * dt
        self.orbit_angle += self.orbit_speed * dt

        # For each blade index i in range(blade_count):
        for i in range(self.blade_count):
            # angle = orbit_angle + (360/blade_count * i)
            angle = self.orbit_angle + (360 / self.blade_count * i)

            # blade_pos = owner.pos + Vector2 rotated by angle at orbit_radius
            blade_pos = self.owner.pos + Vector2(1, 0).rotate(angle) * self.orbit_radius

            # Create a rect at blade_pos (using blade_size)
            blade_rect = pygame.Rect(0, 0, self.blade_size[0], self.blade_size[1])
            blade_rect.center = blade_pos

            # Check rect against each enemy in enemy_group
            for enemy in self.enemy_group:
                # If hit and not in cooldown: deal damage, start 0.5s cooldown for that enemy
                if blade_rect.colliderect(enemy.rect):
                    # Check if enemy is in cooldown
                    if enemy.sprite_id not in self.enemy_cooldowns:
                        # Deal damage
                        is_crit = random.random() < self.owner.crit_chance
                        damage = self.base_damage * self.owner.damage_multiplier * (CRIT_MULTIPLIER if is_crit else 1.0)
                        diff = self.owner.pos - enemy.pos
                        hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        enemy.take_damage(damage, hit_direction=hit_dir)
                        AudioManager.instance().play_sfx(AudioManager.WEAPON_BLADE)
                        if self.effect_group is not None:
                            from src.entities.effects import DamageNumber, HitSpark
                            DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                            HitSpark(enemy.pos, (100, 150, 255), [self.effect_group])

                        # Start 0.5s cooldown for that enemy
                        self.enemy_cooldowns[enemy.sprite_id] = 0.5

        # Update cooldown timers
        for enemy_id in list(self.enemy_cooldowns.keys()):
            self.enemy_cooldowns[enemy_id] -= dt
            if self.enemy_cooldowns[enemy_id] <= 0:
                del self.enemy_cooldowns[enemy_id]

    def draw(self, surface, camera_offset):
        """Draw the orbiting blades."""
        # Draw each blade
        for i in range(self.blade_count):
            # angle = orbit_angle + (360/blade_count * i)
            angle = self.orbit_angle + (360 / self.blade_count * i)

            # blade_pos = owner.pos + Vector2 rotated by angle at orbit_radius
            blade_pos = self.owner.pos + Vector2(1, 0).rotate(angle) * self.orbit_radius

            # Create a rect at blade_pos (using blade_size)
            blade_rect = pygame.Rect(0, 0, self.blade_size[0], self.blade_size[1])
            blade_rect.center = blade_pos

            # Draw the blade (simple rectangle for now)
            pygame.draw.rect(surface, (100, 150, 255),
                           (blade_rect.x - camera_offset.x, blade_rect.y - camera_offset.y,
                            blade_rect.width, blade_rect.height))