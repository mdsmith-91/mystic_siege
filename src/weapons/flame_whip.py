import pygame
import math
import random
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    FLAME_WHIP_BASE_COOLDOWN,
    FLAME_WHIP_BASE_DAMAGE,
    FLAME_WHIP_BURN_DAMAGE,
    FLAME_WHIP_BURN_DURATION,
    FLAME_WHIP_CONE_ANGLE,
    FLAME_WHIP_CONE_RANGE,
    FLAME_WHIP_EFFECT_COLOR,
    FLAME_WHIP_HIT_SPARK_COLOR,
    FLAME_WHIP_SWING_DURATION,
    FLAME_WHIP_SWING_POINT_COUNT,
    FLAME_WHIP_UPGRADE_LEVELS,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

class FlameWhip(BaseWeapon):
    name = "Flame Whip"
    description = "Lashes a cone of fire toward the nearest enemy."
    base_damage = FLAME_WHIP_BASE_DAMAGE
    base_cooldown = FLAME_WHIP_BASE_COOLDOWN
    cone_range = FLAME_WHIP_CONE_RANGE
    cone_angle = FLAME_WHIP_CONE_ANGLE
    burn_damage = FLAME_WHIP_BURN_DAMAGE
    burn_duration = FLAME_WHIP_BURN_DURATION
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in FLAME_WHIP_UPGRADE_LEVELS]

        # Track burning enemies by live enemy reference to avoid repeated id lookups.
        self.burning_enemies: dict[object, float] = {}

        # Swing timer counts down after firing — cone is visible while > 0
        self.swing_timer = 0.0

        # Direction the cone was last fired toward (for draw_effect)
        self.fire_direction: Vector2 = Vector2(1, 0)

    def fire(self):
        """Lash a cone of fire toward the nearest enemy."""
        if not self.enemy_group:
            return

        # Find nearest enemy to aim the cone at
        nearest_enemy = None
        nearest_distance_sq = float("inf")
        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_WHIP)

        # Aim the cone center at the nearest enemy
        self.fire_direction = (nearest_enemy.pos - self.owner.pos).normalize()
        cone_range_sq = self.cone_range * self.cone_range

        # Hit every enemy within cone_range that falls inside the cone arc
        for enemy in self.enemy_group:
            offset = enemy.pos - self.owner.pos
            dist_sq = offset.length_squared()
            if dist_sq == 0 or dist_sq > cone_range_sq:
                continue

            direction_to_enemy = offset * (1.0 / (dist_sq ** 0.5))
            angle_to_enemy = self.fire_direction.angle_to(direction_to_enemy)

            if abs(angle_to_enemy) <= self.cone_angle / 2:
                is_crit = random.random() < self.owner.crit_chance
                damage = self.base_damage * self.owner.damage_multiplier * (self.owner.spell_damage_multiplier if self.IS_SPELL else 1.0) * (CRIT_MULTIPLIER if is_crit else 1.0)
                enemy.take_damage(damage, hit_direction=-direction_to_enemy, attacker=self.owner)
                self.burning_enemies[enemy] = self.burn_duration
                if self.effect_group is not None:
                    from src.entities.effects import DamageNumber, HitSpark
                    DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                    HitSpark(enemy.pos, FLAME_WHIP_HIT_SPARK_COLOR, [self.effect_group])

        # Show swing visual for 0.2s
        self.swing_timer = FLAME_WHIP_SWING_DURATION

    def update(self, dt):
        """Update the flame whip effect."""
        super().update(dt)

        self.swing_timer = max(0, self.swing_timer - dt)

        # Tick burn timers and apply burn damage each frame
        for enemy in list(self.burning_enemies.keys()):
            remaining = self.burning_enemies[enemy] - dt
            if remaining <= 0 or not enemy.alive():
                del self.burning_enemies[enemy]
                continue
            self.burning_enemies[enemy] = remaining
            enemy.take_damage(self.burn_damage * dt, attacker=self.owner)

    def draw_effect(self, surface, camera_offset):
        """Draw a transparent orange fan shape for the duration of the swing."""
        if self.swing_timer <= 0:
            return

        center = self.owner.pos

        # Build the cone arc using the stored fire_direction
        base_angle = math.degrees(math.atan2(-self.fire_direction.y, self.fire_direction.x))
        start_angle = base_angle - self.cone_angle / 2
        end_angle = base_angle + self.cone_angle / 2

        points = [center]
        num_points = FLAME_WHIP_SWING_POINT_COUNT
        for i in range(num_points + 1):
            angle = start_angle + (end_angle - start_angle) * i / num_points
            point = center + Vector2(math.cos(math.radians(angle)), -math.sin(math.radians(angle))) * self.cone_range
            points.append(point)

        if len(points) >= 3:
            alpha = int(100 * (self.swing_timer / FLAME_WHIP_SWING_DURATION))  # fade out as timer decreases
            color = (*FLAME_WHIP_EFFECT_COLOR, alpha)
            pygame.draw.polygon(surface, color,
                                [(p.x - camera_offset.x, p.y - camera_offset.y) for p in points])
