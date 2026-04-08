import random
import pygame
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    SPECTRAL_BLADE_BASE_BLADE_COUNT,
    SPECTRAL_BLADE_BASE_COOLDOWN,
    SPECTRAL_BLADE_BASE_DAMAGE,
    SPECTRAL_BLADE_BLADE_COLOR,
    SPECTRAL_BLADE_BLADE_LENGTH,
    SPECTRAL_BLADE_BLADE_WIDTH,
    SPECTRAL_BLADE_HIT_COOLDOWN,
    SPECTRAL_BLADE_HIT_SPARK_COLOR,
    SPECTRAL_BLADE_ORBIT_RADIUS,
    SPECTRAL_BLADE_ORBIT_SPEED,
    SPECTRAL_BLADE_OUTLINE_COLOR,
    SPECTRAL_BLADE_UPGRADE_LEVELS,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class SpectralBlade(BaseWeapon):
    name = "Spectral Blade"
    description = "Spectral swords orbit the player, passing through enemies."
    base_damage = SPECTRAL_BLADE_BASE_DAMAGE
    base_cooldown = SPECTRAL_BLADE_BASE_COOLDOWN
    blade_count = SPECTRAL_BLADE_BASE_BLADE_COUNT
    orbit_radius = SPECTRAL_BLADE_ORBIT_RADIUS  # hilt offset from player center
    orbit_speed = SPECTRAL_BLADE_ORBIT_SPEED
    orbit_angle = 0.0  # current rotation angle in degrees, increments each frame
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in SPECTRAL_BLADE_UPGRADE_LEVELS]

        # Per-enemy hit cooldown dict: {enemy_id: timer} — prevents rapid re-hits on the same enemy
        self.enemy_cooldowns = {}

    def fire(self):
        pass  # SpectralBlade deals damage via continuous orbital collision in update()

    def update(self, dt):
        """Rotate the blades and check for enemy collisions along each sword segment."""
        self.orbit_angle += self.orbit_speed * dt

        for i in range(self.blade_count):
            angle = self.orbit_angle + (360 / self.blade_count * i)
            direction = Vector2(1, 0).rotate(angle)

            # Sword extends from hilt (orbit_radius out) to tip (orbit_radius + blade_length out)
            hilt = self.owner.pos + direction * self.orbit_radius
            tip = self.owner.pos + direction * (self.orbit_radius + SPECTRAL_BLADE_BLADE_LENGTH)

            for enemy in self.enemy_group:
                if enemy.sprite_id in self.enemy_cooldowns:
                    continue

                # Sample five points along the blade segment for collision
                hit = False
                for t in (0.1, 0.3, 0.5, 0.7, 0.9):
                    pt = hilt.lerp(tip, t)
                    if enemy.rect.collidepoint(pt.x, pt.y):
                        hit = True
                        break

                if hit:
                    is_crit = random.random() < self.owner.crit_chance
                    damage = self.base_damage * self.owner.damage_multiplier * (CRIT_MULTIPLIER if is_crit else 1.0)
                    diff = self.owner.pos - enemy.pos
                    hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                    enemy.take_damage(damage, hit_direction=hit_dir, attacker=self.owner)
                    AudioManager.instance().play_sfx(AudioManager.WEAPON_BLADE)
                    if self.effect_group is not None:
                        from src.entities.effects import DamageNumber, HitSpark
                        DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                        HitSpark(enemy.pos, SPECTRAL_BLADE_HIT_SPARK_COLOR, [self.effect_group])

                    self.enemy_cooldowns[enemy.sprite_id] = SPECTRAL_BLADE_HIT_COOLDOWN

        # Tick down per-enemy hit cooldowns
        for enemy_id in list(self.enemy_cooldowns.keys()):
            self.enemy_cooldowns[enemy_id] -= dt
            if self.enemy_cooldowns[enemy_id] <= 0:
                del self.enemy_cooldowns[enemy_id]

    def draw(self, surface, camera_offset):
        """Draw each orbiting blade as a radially-oriented sword polygon (hilt near player, tip outward)."""
        hw = SPECTRAL_BLADE_BLADE_WIDTH / 2

        for i in range(self.blade_count):
            angle = self.orbit_angle + (360 / self.blade_count * i)
            direction = Vector2(1, 0).rotate(angle)
            perp = direction.rotate(90)

            hilt = self.owner.pos + direction * self.orbit_radius
            tip = self.owner.pos + direction * (self.orbit_radius + SPECTRAL_BLADE_BLADE_LENGTH)

            # Tapered blade: full width at hilt, 30% width at tip
            corners_world = [
                hilt + perp * hw,
                hilt - perp * hw,
                tip - perp * (hw * 0.3),
                tip + perp * (hw * 0.3),
            ]
            pts = [(p.x - camera_offset.x, p.y - camera_offset.y) for p in corners_world]
            pygame.draw.polygon(surface, SPECTRAL_BLADE_BLADE_COLOR, pts)
            pygame.draw.polygon(surface, SPECTRAL_BLADE_OUTLINE_COLOR, pts, 1)
