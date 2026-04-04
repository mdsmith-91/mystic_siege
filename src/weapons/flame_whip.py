import pygame
from src.weapons.base_weapon import BaseWeapon
from pygame.math import Vector2
import math
import random
from src.utils.audio_manager import AudioManager
from settings import CRIT_MULTIPLIER

class FlameWhip(BaseWeapon):
    name = "Flame Whip"
    description = "Lashes a cone of fire toward the nearest enemy."
    base_damage = 30.0
    base_cooldown = 1.5
    cone_range = 120
    cone_angle = 90  # degrees total arc
    burn_damage = 5.0  # per second
    burn_duration = 2.0  # seconds
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"base_damage": 15},  # L2: +15 damage
            {"cone_range": 40},   # L3: +40 range
            {"burn_duration": 1.5},  # L4: +1.5 burn duration
            {"cone_angle": 30, "base_damage": 20}  # L5: wider cone, more damage
        ]

        # Track burning enemies: dict {enemy_id: remaining_burn_time}
        self.burning_enemies = {}

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
        nearest_distance = float('inf')
        for enemy in self.enemy_group:
            distance = (enemy.pos - self.owner.pos).length()
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_WHIP)

        # Aim the cone center at the nearest enemy
        self.fire_direction = (nearest_enemy.pos - self.owner.pos).normalize()

        # Hit every enemy within cone_range that falls inside the cone arc
        for enemy in self.enemy_group:
            dist = (enemy.pos - self.owner.pos).length()
            if dist > self.cone_range:
                continue

            direction_to_enemy = (enemy.pos - self.owner.pos).normalize()
            angle_to_enemy = self.fire_direction.angle_to(direction_to_enemy)

            if abs(angle_to_enemy) <= self.cone_angle / 2:
                is_crit = random.random() < self.owner.crit_chance
                damage = self.base_damage * self.owner.damage_multiplier * (self.owner.spell_damage_multiplier if self.IS_SPELL else 1.0) * (CRIT_MULTIPLIER if is_crit else 1.0)
                enemy.take_damage(damage, hit_direction=-direction_to_enemy, attacker=self.owner)
                self.burning_enemies[enemy.sprite_id] = self.burn_duration
                if self.effect_group is not None:
                    from src.entities.effects import DamageNumber, HitSpark
                    DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                    HitSpark(enemy.pos, (255, 100, 0), [self.effect_group])

        # Show swing visual for 0.2s
        self.swing_timer = 0.2

    def update(self, dt):
        """Update the flame whip effect."""
        super().update(dt)

        self.swing_timer = max(0, self.swing_timer - dt)

        # Tick burn timers and apply burn damage each frame
        for enemy_id in list(self.burning_enemies.keys()):
            self.burning_enemies[enemy_id] -= dt
            if self.burning_enemies[enemy_id] > 0:
                enemy = None
                for e in self.enemy_group:
                    if e.sprite_id == enemy_id:
                        enemy = e
                        break
                if enemy:
                    enemy.take_damage(self.burn_damage * dt, attacker=self.owner)
            else:
                del self.burning_enemies[enemy_id]

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
        num_points = 10
        for i in range(num_points + 1):
            angle = start_angle + (end_angle - start_angle) * i / num_points
            point = center + Vector2(math.cos(math.radians(angle)), -math.sin(math.radians(angle))) * self.cone_range
            points.append(point)

        if len(points) >= 3:
            alpha = int(100 * (self.swing_timer / 0.2))  # fade out as timer decreases
            color = (255, 100, 0, alpha)
            pygame.draw.polygon(surface, color,
                                [(p.x - camera_offset.x, p.y - camera_offset.y) for p in points])
