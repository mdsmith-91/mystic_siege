import pygame
import random
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    FROST_RING_BASE_COOLDOWN,
    FROST_RING_BASE_DAMAGE,
    FROST_RING_COLOR,
    FROST_RING_DRAW_WIDTH,
    FROST_RING_FREEZE_DURATION,
    FROST_RING_HALF_WIDTH,
    FROST_RING_HIT_SPARK_COLOR,
    FROST_RING_MAX_RADIUS,
    FROST_RING_SPEED,
    FROST_RING_UPGRADE_LEVELS,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

class FrostRing(BaseWeapon):
    name = "Frost Ring"
    description = "Expands a freezing ring outward, temporarily immobilizing enemies."
    base_damage = FROST_RING_BASE_DAMAGE
    base_cooldown = FROST_RING_BASE_COOLDOWN
    ring_speed = FROST_RING_SPEED
    max_radius = FROST_RING_MAX_RADIUS
    freeze_duration = FROST_RING_FREEZE_DURATION
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in FROST_RING_UPGRADE_LEVELS]

        # Track frozen enemies by live enemy reference to avoid repeated group scans.
        self.frozen_enemies: dict[object, float] = {}

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
        for enemy in list(self.frozen_enemies.keys()):
            remaining = self.frozen_enemies[enemy] - dt
            if remaining <= 0 or not enemy.alive():
                if enemy.alive() and hasattr(enemy, 'max_speed'):
                    enemy.speed = enemy.max_speed
                del self.frozen_enemies[enemy]
                continue

            self.frozen_enemies[enemy] = remaining

        # Expand all rings and check for collisions
        i = 0
        while i < len(self.rings):
            ring = self.rings[i]

            # Expand the ring
            ring["radius"] += self.ring_speed * dt
            inner_radius = max(0, ring["radius"] - FROST_RING_HALF_WIDTH)
            outer_radius = ring["radius"] + FROST_RING_HALF_WIDTH
            inner_radius_sq = inner_radius * inner_radius
            outer_radius_sq = outer_radius * outer_radius

            # Check each ring against enemies (circle vs rect)
            for enemy in self.enemy_group:
                # Calculate distance from ring center to enemy center
                distance_sq = (enemy.pos - ring["center"]).length_squared()

                # Check if enemy is within the ring
                if inner_radius_sq <= distance_sq <= outer_radius_sq:

                    # Check if this enemy has already been damaged by this ring
                    if enemy.sprite_id not in ring["damage_done"]:
                        # Deal damage
                        is_crit = random.random() < self.owner.crit_chance
                        damage = self.base_damage * self.owner.damage_multiplier * (self.owner.spell_damage_multiplier if self.IS_SPELL else 1.0) * (CRIT_MULTIPLIER if is_crit else 1.0)
                        diff = ring["center"] - enemy.pos
                        hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        enemy.take_damage(damage, hit_direction=hit_dir, attacker=self.owner)
                        if self.effect_group is not None:
                            from src.entities.effects import DamageNumber, HitSpark
                            DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                            HitSpark(enemy.pos, FROST_RING_HIT_SPARK_COLOR, [self.effect_group])

                        # Freeze enemy — only save max_speed if not already frozen
                        self.frozen_enemies[enemy] = self.freeze_duration
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
            pygame.draw.circle(surface, FROST_RING_COLOR,
                             (int(center.x - camera_offset.x), int(center.y - camera_offset.y)),
                             int(radius), FROST_RING_DRAW_WIDTH)
