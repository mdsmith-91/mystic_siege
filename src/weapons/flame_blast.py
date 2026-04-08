import pygame
import math
import random
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    FLAME_BLAST_BASE_COOLDOWN,
    FLAME_BLAST_BASE_DAMAGE,
    FLAME_BLAST_BURN_DAMAGE,
    FLAME_BLAST_BURN_DURATION,
    FLAME_BLAST_CONE_ANGLE,
    FLAME_BLAST_CONE_RANGE,
    FLAME_BLAST_CORE_COLOR,
    FLAME_BLAST_EFFECT_COLOR,
    FLAME_BLAST_HIT_SPARK_COLOR,
    FLAME_BLAST_INNER_COLOR,
    FLAME_BLAST_PARTICLE_COUNT,
    FLAME_BLAST_PARTICLE_LIFETIME,
    FLAME_BLAST_PARTICLE_RADIUS_MAX,
    FLAME_BLAST_PARTICLE_SPEED_MAX,
    FLAME_BLAST_PARTICLE_SPEED_MIN,
    FLAME_BLAST_UPGRADE_LEVELS,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

class FlameBlast(BaseWeapon):
    name = "Flame Blast"
    description = "Blasts a cone of fire toward the nearest enemy."
    base_damage = FLAME_BLAST_BASE_DAMAGE
    base_cooldown = FLAME_BLAST_BASE_COOLDOWN
    cone_range = FLAME_BLAST_CONE_RANGE
    cone_angle = FLAME_BLAST_CONE_ANGLE
    burn_damage = FLAME_BLAST_BURN_DAMAGE
    burn_duration = FLAME_BLAST_BURN_DURATION
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in FLAME_BLAST_UPGRADE_LEVELS]

        # Track burning enemies by live enemy reference to avoid repeated id lookups.
        self.burning_enemies: dict[object, float] = {}

        # Direction the cone was last fired toward (for draw_effect)
        self.fire_direction: Vector2 = Vector2(1, 0)

        # Live explosion particles — each dict holds pos, vel, life, max_life, radius, color
        self.effect_particles: list[dict] = []

    def fire(self):
        """Lash a cone of fire toward the nearest enemy."""
        if not self.enemy_group:
            return

        # Find nearest enemy to aim the cone at
        nearest_enemy = None
        nearest_distance_sq = float("inf")
        cone_range_sq = self.cone_range * self.cone_range
        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq and distance_sq <= cone_range_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        raw = nearest_enemy.pos - self.owner.pos
        if raw.length_squared() == 0:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_FLAME_BLAST)

        # Aim the cone center at the nearest enemy
        self.fire_direction = raw.normalize()

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
                damage = self._scaled_damage(self.base_damage) * (CRIT_MULTIPLIER if is_crit else 1.0)
                enemy.take_damage(damage, hit_direction=-direction_to_enemy, attacker=self.owner)
                self.burning_enemies[enemy] = self.burn_duration
                if self.effect_group is not None:
                    from src.entities.effects import DamageNumber, HitSpark
                    DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                    HitSpark(enemy.pos, FLAME_BLAST_HIT_SPARK_COLOR, [self.effect_group])

        # Spawn explosion particles spreading within the cone
        base_angle = math.degrees(math.atan2(-self.fire_direction.y, self.fire_direction.x))
        half_cone = self.cone_angle / 2
        speed_range = FLAME_BLAST_PARTICLE_SPEED_MAX - FLAME_BLAST_PARTICLE_SPEED_MIN
        self.effect_particles = []
        for _ in range(FLAME_BLAST_PARTICLE_COUNT):
            angle = base_angle + random.uniform(-half_cone, half_cone)
            speed = random.uniform(FLAME_BLAST_PARTICLE_SPEED_MIN, FLAME_BLAST_PARTICLE_SPEED_MAX)
            direction = Vector2(math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
            # slight lateral jitter for turbulence
            perp = Vector2(-direction.y, direction.x)
            vel = direction * speed + perp * random.uniform(-speed * 0.15, speed * 0.15)
            # color by speed: slow particles stay near origin (hot yellow), fast ones streak out (orange)
            speed_frac = (speed - FLAME_BLAST_PARTICLE_SPEED_MIN) / speed_range
            if speed_frac < 0.33:
                color = FLAME_BLAST_CORE_COLOR
            elif speed_frac < 0.67:
                color = FLAME_BLAST_INNER_COLOR
            else:
                color = FLAME_BLAST_EFFECT_COLOR
            lifetime = random.uniform(FLAME_BLAST_PARTICLE_LIFETIME * 0.6, FLAME_BLAST_PARTICLE_LIFETIME)
            self.effect_particles.append({
                'pos': Vector2(self.owner.pos),
                'vel': vel,
                'life': lifetime,
                'max_life': lifetime,
                'radius': min(random.randint(1, FLAME_BLAST_PARTICLE_RADIUS_MAX),
                          random.randint(1, FLAME_BLAST_PARTICLE_RADIUS_MAX)),
                'color': color,
            })

    def update(self, dt):
        """Update the flame blast effect."""
        super().update(dt)

        # Advance explosion particles and cull expired ones
        for p in self.effect_particles:
            p['pos'] += p['vel'] * dt
            p['life'] -= dt
        self.effect_particles = [p for p in self.effect_particles if p['life'] > 0]

        # Tick burn timers and apply burn damage each frame
        for enemy in list(self.burning_enemies.keys()):
            remaining = self.burning_enemies[enemy] - dt
            if remaining <= 0 or not enemy.alive():
                del self.burning_enemies[enemy]
                continue
            self.burning_enemies[enemy] = remaining
            enemy.take_damage(self.burn_damage * dt, attacker=self.owner)

    def on_owner_inactive(self):
        self.burning_enemies.clear()
        self.effect_particles.clear()

    def draw_effect(self, surface, camera_offset):
        """Draw the particle explosion blast.

        Particles hold full opacity for the first 60% of their lifetime then
        fade out, so they read clearly before disappearing.  Rendered onto a
        single temporary SRCALPHA surface per frame — the world surface is
        .convert() and drops alpha on direct draws.
        """
        if not self.effect_particles:
            return

        center_sx = self.owner.pos.x - camera_offset.x
        center_sy = self.owner.pos.y - camera_offset.y
        size = int(self.cone_range * 2 + 20)
        half = size // 2
        origin_x = int(center_sx - half)
        origin_y = int(center_sy - half)

        temp = pygame.Surface((size, size), pygame.SRCALPHA)

        for p in self.effect_particles:
            # Hold full alpha for first 60% of lifetime; fade in the last 40%
            t = p['life'] / p['max_life']
            alpha = int(255 * min(1.0, t / 0.4))
            px = int(p['pos'].x - camera_offset.x) - origin_x
            py = int(p['pos'].y - camera_offset.y) - origin_y
            if 0 <= px < size and 0 <= py < size:
                pygame.draw.circle(temp, (*p['color'], alpha), (px, py), p['radius'])

        surface.blit(temp, (origin_x, origin_y))
