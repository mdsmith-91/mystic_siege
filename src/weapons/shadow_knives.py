from collections import deque
import random

import pygame
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    SHADOW_KNIVES_BASE_COOLDOWN,
    SHADOW_KNIVES_BASE_CRIT_BONUS,
    SHADOW_KNIVES_BASE_DAMAGE,
    SHADOW_KNIVES_BASE_PIERCE,
    SHADOW_KNIVES_BASE_PROJECTILE_COUNT,
    SHADOW_KNIVES_OUTWARD_DURATION,
    SHADOW_KNIVES_PROJECTILE_COLOR,
    SHADOW_KNIVES_PROJECTILE_EDGE_COLOR,
    SHADOW_KNIVES_PROJECTILE_HILT_COLOR,
    SHADOW_KNIVES_PROJECTILE_LIFETIME,
    SHADOW_KNIVES_PROJECTILE_OUTLINE_COLOR,
    SHADOW_KNIVES_PROJECTILE_SIZE,
    SHADOW_KNIVES_PROJECTILE_SPEED,
    SHADOW_KNIVES_RETURN_CATCH_RADIUS,
    SHADOW_KNIVES_RETURN_SPEED,
    SHADOW_KNIVES_RETURN_TRAIL_COLOR,
    SHADOW_KNIVES_RETURN_TRAIL_INTERVAL,
    SHADOW_KNIVES_RETURN_TRAIL_LENGTH,
    SHADOW_KNIVES_SPREAD,
    SHADOW_KNIVES_TARGETING_RANGE,
    SHADOW_KNIVES_UPGRADE_LEVELS,
)
from src.entities.projectile import Projectile
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class ShadowKnifeProjectile(Projectile):
    def __init__(
        self,
        pos,
        direction: Vector2,
        speed: float,
        damage: float,
        groups,
        enemy_group_ref,
        owner,
        pierce: int = 0,
        owner_crit_chance: float = 0.0,
        outward_duration: float = SHADOW_KNIVES_OUTWARD_DURATION,
        return_speed: float = SHADOW_KNIVES_RETURN_SPEED,
    ):
        self.is_returning = False
        self.outward_timer = outward_duration
        self.return_speed = return_speed
        self.catch_radius_sq = SHADOW_KNIVES_RETURN_CATCH_RADIUS * SHADOW_KNIVES_RETURN_CATCH_RADIUS
        self._trail = deque(maxlen=SHADOW_KNIVES_RETURN_TRAIL_LENGTH)
        self._trail_timer = 0.0
        super().__init__(
            pos=pos,
            direction=direction,
            speed=speed,
            damage=damage,
            groups=groups,
            enemy_group_ref=enemy_group_ref,
            pierce=pierce,
            color=SHADOW_KNIVES_PROJECTILE_COLOR,
            owner_crit_chance=owner_crit_chance,
            owner=owner,
            lifetime=SHADOW_KNIVES_PROJECTILE_LIFETIME,
            size=SHADOW_KNIVES_PROJECTILE_SIZE,
            draw_shape="shadow_knife",
            rotate_to_direction=False,
        )
        self._sync_image_rotation()

    def _build_image(self) -> pygame.Surface:
        width, height = SHADOW_KNIVES_PROJECTILE_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        blade_points = [
            (width - 1, height // 2),
            (width - 6, 1),
            (5, 1),
            (2, height // 2),
            (5, height - 2),
            (width - 6, height - 2),
        ]
        inner_blade_points = [
            (width - 2, height // 2),
            (width - 6, 2),
            (6, 2),
            (4, height // 2),
            (6, height - 3),
            (width - 6, height - 3),
        ]

        pygame.draw.polygon(surface, SHADOW_KNIVES_PROJECTILE_OUTLINE_COLOR, blade_points)
        pygame.draw.polygon(surface, self.color, inner_blade_points)
        pygame.draw.line(
            surface,
            SHADOW_KNIVES_PROJECTILE_EDGE_COLOR,
            (6, 2),
            (width - 4, height // 2),
            1,
        )
        pygame.draw.rect(surface, SHADOW_KNIVES_PROJECTILE_HILT_COLOR, pygame.Rect(0, 2, 4, height - 4), border_radius=1)
        return surface

    def _begin_return(self) -> None:
        if self.is_returning:
            return
        self.is_returning = True
        self.speed = self.return_speed

    def _sync_image_rotation(self) -> None:
        angle = -Vector2(1, 0).angle_to(self.direction)
        self.image = pygame.transform.rotate(self._base_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        if not self.is_returning:
            self.outward_timer -= dt
            if self.outward_timer <= 0.0:
                self._begin_return()
        elif self.owner is None or not self.owner.alive():
            self.kill()
            return
        else:
            owner_offset = self.owner.pos - self.pos
            if owner_offset.length_squared() <= self.catch_radius_sq:
                self.kill()
                return
            if owner_offset.length_squared() > 0:
                self.direction = owner_offset.normalize()
                self._sync_image_rotation()

            self._trail_timer += dt
            if self._trail_timer >= SHADOW_KNIVES_RETURN_TRAIL_INTERVAL:
                self._trail_timer = 0.0
                self._trail.append(Vector2(self.pos))

        super().update(dt)

    def on_hit(self, enemy, effect_group=None):
        if enemy.sprite_id in self.enemies_hit:
            return

        self.enemies_hit.add(enemy.sprite_id)

        is_crit = random.random() < self.owner_crit_chance
        actual_damage = self.damage * (CRIT_MULTIPLIER if is_crit else 1.0)

        if self.owner is not None:
            to_attacker = self.owner.pos - enemy.pos
            hit_direction = to_attacker.normalize() if to_attacker.length_squared() > 0 else -self.direction
        else:
            hit_direction = -self.direction
        enemy.take_damage(actual_damage, hit_direction=hit_direction, attacker=self.owner)

        if effect_group is not None:
            from src.entities.effects import DamageNumber, HitSpark
            DamageNumber(enemy.pos - Vector2(0, 20), actual_damage, [effect_group], is_crit=is_crit)
            HitSpark(enemy.pos, (255, 200, 50), [effect_group])

        if self.pierce <= 0:
            self.kill()
        else:
            self.pierce -= 1

    def draw_trail(self, trail_surface: pygame.Surface, camera_offset: Vector2) -> None:
        if not self.is_returning or not self._trail:
            return

        for index, trail_pos in enumerate(self._trail):
            fraction = (index + 1) / len(self._trail)
            alpha = int(110 * fraction)
            radius = max(1, int(3 * fraction))
            screen_pos = trail_pos - camera_offset
            pygame.draw.circle(
                trail_surface,
                (*SHADOW_KNIVES_RETURN_TRAIL_COLOR, alpha),
                (int(screen_pos.x), int(screen_pos.y)),
                radius,
            )


class ShadowKnives(BaseWeapon):
    name = "Shadow Knives"
    description = "Throw fast knives that return after a short outward flight."
    base_damage = SHADOW_KNIVES_BASE_DAMAGE
    base_cooldown = SHADOW_KNIVES_BASE_COOLDOWN
    projectile_count = SHADOW_KNIVES_BASE_PROJECTILE_COUNT
    pierce = SHADOW_KNIVES_BASE_PIERCE
    crit_bonus = SHADOW_KNIVES_BASE_CRIT_BONUS
    IS_SPELL = False
    USES_PROJECTILE_PIERCE_BONUS = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in SHADOW_KNIVES_UPGRADE_LEVELS]

    def _spawn_knife(self, direction: Vector2) -> None:
        ShadowKnifeProjectile(
            pos=self.owner.pos,
            direction=direction,
            speed=SHADOW_KNIVES_PROJECTILE_SPEED,
            damage=self._scaled_damage(self.base_damage),
            groups=self.projectile_group,
            enemy_group_ref=self.enemy_group,
            pierce=self._get_effective_projectile_pierce(),
            owner_crit_chance=min(1.0, self.owner.crit_chance + self.crit_bonus),
            owner=self.owner,
        )

    def fire(self):
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = SHADOW_KNIVES_TARGETING_RANGE * SHADOW_KNIVES_TARGETING_RANGE

        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq and distance_sq <= max_range_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if nearest_enemy is None:
            return

        base_direction = nearest_enemy.pos - self.owner.pos
        if base_direction.length_squared() == 0:
            if self.owner.facing.length_squared() == 0:
                return
            base_direction = self.owner.facing

        AudioManager.instance().play_sfx(AudioManager.WEAPON_SHADOW_KNIVES)
        base_direction = base_direction.normalize()

        for index in range(self.projectile_count):
            if self.projectile_count == 1:
                direction = base_direction
            else:
                angle_offset = (index - (self.projectile_count - 1) / 2) * SHADOW_KNIVES_SPREAD
                direction = base_direction.rotate(angle_offset)
            self._spawn_knife(direction)

    def on_owner_inactive(self):
        for projectile in list(self.projectile_group):
            if isinstance(projectile, ShadowKnifeProjectile) and projectile.owner is self.owner:
                projectile.kill()

    def draw_under(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        trail_surface = None
        for projectile in self.projectile_group:
            if isinstance(projectile, ShadowKnifeProjectile) and projectile.owner is self.owner:
                if projectile.is_returning and projectile._trail:
                    if trail_surface is None:
                        trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                    projectile.draw_trail(trail_surface, camera_offset)
        if trail_surface is not None:
            surface.blit(trail_surface, (0, 0))
