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
    SPECTRAL_BLADE_GLOW_COLOR,
    SPECTRAL_BLADE_GLOW_EXTRA_WIDTH,
    SPECTRAL_BLADE_GRIP_COLOR,
    SPECTRAL_BLADE_GRIP_LENGTH,
    SPECTRAL_BLADE_GRIP_WIDTH,
    SPECTRAL_BLADE_GUARD_COLOR,
    SPECTRAL_BLADE_GUARD_HALF_WIDTH,
    SPECTRAL_BLADE_GUARD_THICKNESS,
    SPECTRAL_BLADE_TAPER_START,
    SPECTRAL_BLADE_HIGHLIGHT_COLOR,
    SPECTRAL_BLADE_HIT_COOLDOWN,
    SPECTRAL_BLADE_HIT_SPARK_COLOR,
    SPECTRAL_BLADE_ORBIT_RADIUS,
    SPECTRAL_BLADE_ORBIT_SPEED,
    SPECTRAL_BLADE_OUTLINE_COLOR,
    SPECTRAL_BLADE_POMMEL_RADIUS,
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
        """Draw each orbiting blade: glow, grip, pommel, crossguard, blade, highlight."""
        hw = SPECTRAL_BLADE_BLADE_WIDTH / 2
        glow_hw = hw + SPECTRAL_BLADE_GLOW_EXTRA_WIDTH
        grip_hw = SPECTRAL_BLADE_GRIP_WIDTH / 2
        guard_hw = SPECTRAL_BLADE_GUARD_HALF_WIDTH
        g_thick = SPECTRAL_BLADE_GUARD_THICKNESS / 2
        pr = SPECTRAL_BLADE_POMMEL_RADIUS
        ox, oy = camera_offset.x, camera_offset.y

        def sc(v):
            return (v.x - ox, v.y - oy)

        for i in range(self.blade_count):
            angle = self.orbit_angle + (360 / self.blade_count * i)
            direction = Vector2(1, 0).rotate(angle)
            perp = direction.rotate(90)

            hilt = self.owner.pos + direction * self.orbit_radius
            guard = hilt + direction * SPECTRAL_BLADE_GRIP_LENGTH
            tip = self.owner.pos + direction * (self.orbit_radius + SPECTRAL_BLADE_BLADE_LENGTH)

            # Taper point: where the parallel body ends and the tip taper begins
            blade_body_len = (SPECTRAL_BLADE_BLADE_LENGTH - SPECTRAL_BLADE_GRIP_LENGTH) * SPECTRAL_BLADE_TAPER_START
            taper = guard + direction * blade_body_len

            # 1. Glow: wider 5-point shape matching blade silhouette — outer bloom illusion
            glow_pts = [
                sc(guard + perp * glow_hw),
                sc(taper + perp * glow_hw),
                sc(tip),
                sc(taper - perp * glow_hw),
                sc(guard - perp * glow_hw),
            ]
            pygame.draw.polygon(surface, SPECTRAL_BLADE_GLOW_COLOR, glow_pts)

            # 2. Grip: narrow dark handle bar from hilt to guard
            grip_pts = [
                sc(hilt + perp * grip_hw),
                sc(hilt - perp * grip_hw),
                sc(guard - perp * grip_hw),
                sc(guard + perp * grip_hw),
            ]
            pygame.draw.polygon(surface, SPECTRAL_BLADE_GRIP_COLOR, grip_pts)

            # 3. Pommel: filled wheel circle capping the hilt base
            pygame.draw.circle(surface, SPECTRAL_BLADE_GUARD_COLOR, sc(hilt), pr)
            pygame.draw.circle(surface, SPECTRAL_BLADE_OUTLINE_COLOR, sc(hilt), pr, 1)

            # 4. Crossguard: dark fill with lighter accent outline so guard edge is visible
            guard_pts = [
                sc(guard + perp * guard_hw - direction * g_thick),
                sc(guard - perp * guard_hw - direction * g_thick),
                sc(guard - perp * guard_hw + direction * g_thick),
                sc(guard + perp * guard_hw + direction * g_thick),
            ]
            pygame.draw.polygon(surface, SPECTRAL_BLADE_GRIP_COLOR, guard_pts)
            pygame.draw.polygon(surface, SPECTRAL_BLADE_GUARD_COLOR, guard_pts, 1)

            # 5. Blade: parallel body along most of the length, then taper to a point
            blade_pts = [
                sc(guard + perp * hw),
                sc(taper + perp * hw),
                sc(tip),
                sc(taper - perp * hw),
                sc(guard - perp * hw),
            ]
            pygame.draw.polygon(surface, SPECTRAL_BLADE_BLADE_COLOR, blade_pts)
            pygame.draw.polygon(surface, SPECTRAL_BLADE_OUTLINE_COLOR, blade_pts, 1)

            # 6. Fuller: 2px bright centerline simulating the blade's central groove
            pygame.draw.line(surface, SPECTRAL_BLADE_HIGHLIGHT_COLOR,
                             sc(guard + direction * 2), sc(tip - direction * 6), 2)
