import pygame
import math
import random
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    DOT_DISPLAY_TICK_INTERVAL,
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
    FLAME_BLAST_PARTICLE_FADE_THRESHOLD,
    FLAME_BLAST_PARTICLE_RADIUS_MAX,
    FLAME_BLAST_PARTICLE_SPEED_MAX,
    FLAME_BLAST_PARTICLE_SPEED_MIN,
    FLAME_BLAST_POOL_COLOR,
    FLAME_BLAST_POOL_DURATION,
    FLAME_BLAST_POOL_RADIUS,
    FLAME_BLAST_POOL_TICK_INTERVAL,
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

        # Inferno pools: each dict holds center, remaining, tick_timer
        self.pools: list[dict] = []
        # Stored as int so the generic upgrade() += delta path works; truthy at L5.
        self.inferno_pool = 0
        self._burn_display_timers: dict[object, float] = {}
        self._burn_crit_states: dict[object, bool] = {}

    @property
    def effective_cone_range(self) -> float:
        return self.cone_range * self.owner.area_size_multiplier

    def fire(self):
        """Lash a cone of fire toward the nearest enemy."""
        if not self.enemy_group:
            return

        # Find nearest enemy to aim the cone at
        nearest_enemy = None
        nearest_distance_sq = float("inf")
        cone_range = self.effective_cone_range
        cone_range_sq = cone_range * cone_range
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

        # Inferno Pool: leave a lingering fire zone at the far end of the cone.
        if self.inferno_pool:
            pool_center = self.owner.pos + self.fire_direction * self.effective_cone_range * 0.7
            self.pools.append({
                "center": pool_center,
                "remaining": FLAME_BLAST_POOL_DURATION,
                "tick_timer": 0.0,
            })

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

    def _tick_pools(self, dt: float) -> None:
        pool_damage = self._scaled_dot_damage(self.burn_damage)
        radius_sq = FLAME_BLAST_POOL_RADIUS * FLAME_BLAST_POOL_RADIUS
        i = 0
        while i < len(self.pools):
            pool = self.pools[i]
            pool["remaining"] -= dt
            pool["tick_timer"] -= dt
            if pool["remaining"] <= 0:
                self.pools.pop(i)
                continue
            if pool["tick_timer"] <= 0:
                pool["tick_timer"] = FLAME_BLAST_POOL_TICK_INTERVAL
                center = pool["center"]
                for enemy in self.enemy_group:
                    if enemy.alive() and (enemy.pos - center).length_squared() <= radius_sq:
                        is_crit = random.random() < self.owner.crit_chance
                        actual_pool_damage = pool_damage * (CRIT_MULTIPLIER if is_crit else 1.0)
                        enemy.take_damage(actual_pool_damage, hit_direction=None, attacker=self.owner, knockback_force=0)
                        self.burning_enemies[enemy] = self.burn_duration
                        if self.effect_group is not None:
                            from src.entities.effects import DamageNumber
                            DamageNumber(enemy.pos - Vector2(0, 20), actual_pool_damage, [self.effect_group], is_crit=is_crit)
            i += 1

    def update(self, dt):
        """Update the flame blast effect."""
        super().update(dt)

        # Advance explosion particles and cull expired ones
        for p in self.effect_particles:
            p['pos'] += p['vel'] * dt
            p['life'] -= dt
        self.effect_particles = [p for p in self.effect_particles if p['life'] > 0]

        # Tick burn timers and apply burn damage each frame
        burn_damage_rate = self._scaled_dot_damage(self.burn_damage)
        for enemy in list(self.burning_enemies.keys()):
            remaining = self.burning_enemies[enemy] - dt
            if remaining <= 0 or not enemy.alive():
                del self.burning_enemies[enemy]
                self._burn_display_timers.pop(enemy, None)
                self._burn_crit_states.pop(enemy, None)
                continue
            self.burning_enemies[enemy] = remaining
            is_crit = self._burn_crit_states.get(enemy, False)
            to_attacker = self.owner.pos - enemy.pos
            hit_dir = to_attacker.normalize() if to_attacker.length_squared() > 0 else None
            enemy.take_damage(
                burn_damage_rate * dt * (CRIT_MULTIPLIER if is_crit else 1.0),
                hit_direction=hit_dir,
                attacker=self.owner,
                knockback_force=0,
            )
            if self.effect_group is not None:
                elapsed = self._burn_display_timers.get(enemy, DOT_DISPLAY_TICK_INTERVAL) + dt
                if elapsed >= DOT_DISPLAY_TICK_INTERVAL:
                    new_crit = random.random() < self.owner.crit_chance
                    self._burn_crit_states[enemy] = new_crit
                    display_damage = burn_damage_rate * DOT_DISPLAY_TICK_INTERVAL * (CRIT_MULTIPLIER if new_crit else 1.0)
                    from src.entities.effects import DamageNumber
                    DamageNumber(enemy.pos - Vector2(0, 20), display_damage, [self.effect_group], is_crit=new_crit)
                    elapsed -= DOT_DISPLAY_TICK_INTERVAL
                self._burn_display_timers[enemy] = elapsed

        self._tick_pools(dt)

    def on_owner_inactive(self):
        self.burning_enemies.clear()
        self._burn_display_timers.clear()
        self._burn_crit_states.clear()
        self.effect_particles.clear()
        self.pools.clear()

    def draw_under(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Draw lingering inferno pools beneath all sprites."""
        if not self.pools:
            return
        tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for pool in self.pools:
            cx = int(pool["center"].x - camera_offset.x)
            cy = int(pool["center"].y - camera_offset.y)
            alpha = int(160 * (pool["remaining"] / FLAME_BLAST_POOL_DURATION))
            pygame.draw.circle(tmp, (*FLAME_BLAST_POOL_COLOR, alpha), (cx, cy), FLAME_BLAST_POOL_RADIUS)
            pygame.draw.circle(tmp, (255, 200, 50, min(255, alpha + 40)), (cx, cy), FLAME_BLAST_POOL_RADIUS // 2)
        surface.blit(tmp, (0, 0))

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
        size = int(self.effective_cone_range * 2 + 20)
        half = size // 2
        origin_x = int(center_sx - half)
        origin_y = int(center_sy - half)

        temp = pygame.Surface((size, size), pygame.SRCALPHA)

        for p in self.effect_particles:
            # Hold full alpha for first 60% of lifetime; fade in the last 40%
            t = p['life'] / p['max_life']
            alpha = int(255 * min(1.0, t / FLAME_BLAST_PARTICLE_FADE_THRESHOLD))
            px = int(p['pos'].x - camera_offset.x) - origin_x
            py = int(p['pos'].y - camera_offset.y) - origin_y
            if 0 <= px < size and 0 <= py < size:
                pygame.draw.circle(temp, (*p['color'], alpha), (px, py), p['radius'])

        surface.blit(temp, (origin_x, origin_y))
