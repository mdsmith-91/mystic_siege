import math
import random

import pygame
from pygame.math import Vector2

from settings import (
    BRAMBLE_SEEDS_BASE_COOLDOWN,
    BRAMBLE_SEEDS_BASE_DAMAGE,
    BRAMBLE_SEEDS_BASE_PROJECTILE_COUNT,
    BRAMBLE_SEEDS_HITBOX_SIZE,
    BRAMBLE_SEEDS_HIT_SPARK_COLOR,
    BRAMBLE_SEEDS_PATCH_ALPHA,
    BRAMBLE_SEEDS_PATCH_DURATION,
    BRAMBLE_SEEDS_PATCH_FILL_COLOR,
    BRAMBLE_SEEDS_PATCH_RADIUS,
    BRAMBLE_SEEDS_PATCH_RING_ALPHA,
    BRAMBLE_SEEDS_PATCH_RING_COLOR,
    BRAMBLE_SEEDS_PATCH_TENDRIL_COUNT,
    BRAMBLE_SEEDS_PATCH_THORN_COLOR,
    BRAMBLE_SEEDS_PATCH_THORN_COUNT,
    BRAMBLE_SEEDS_PROJECTILE_COLOR,
    BRAMBLE_SEEDS_PROJECTILE_CORE_COLOR,
    BRAMBLE_SEEDS_PROJECTILE_LIFETIME,
    BRAMBLE_SEEDS_PROJECTILE_SIZE,
    BRAMBLE_SEEDS_PROJECTILE_SPEED,
    BRAMBLE_SEEDS_SLOW_DURATION,
    BRAMBLE_SEEDS_SLOW_MULTIPLIER,
    BRAMBLE_SEEDS_SPREAD,
    BRAMBLE_SEEDS_TARGETING_RANGE,
    BRAMBLE_SEEDS_TICK_INTERVAL,
    BRAMBLE_SEEDS_UPGRADE_LEVELS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

_TWO_PI = math.pi * 2


class BrambleSeedProjectile(pygame.sprite.Sprite):
    """Thrown seed that sprouts into a bramble patch on impact or expiry."""

    def __init__(
        self,
        pos,
        direction: Vector2,
        speed: float,
        groups,
        weapon,
        lifetime: float,
    ):
        super().__init__(groups)
        self.weapon = weapon
        self.owner = weapon.owner
        self.direction = direction.normalize()
        self.speed = speed
        self.lifetime = lifetime
        self.pos = Vector2(pos)
        self.is_enemy_projectile = False
        self.enemies_hit = set()
        self._sprouted = False
        self.image = self._build_image()
        self.rect = pygame.Rect(0, 0, *BRAMBLE_SEEDS_HITBOX_SIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def _build_image(self) -> pygame.Surface:
        width, height = BRAMBLE_SEEDS_PROJECTILE_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        center = (width // 2, height // 2)
        pygame.draw.circle(surface, (*BRAMBLE_SEEDS_PROJECTILE_COLOR, 230), center, min(width, height) // 2)
        pygame.draw.circle(surface, (*BRAMBLE_SEEDS_PROJECTILE_CORE_COLOR, 255), center, max(2, min(width, height) // 4))
        pygame.draw.circle(surface, (40, 80, 35, 255), center, min(width, height) // 2, 1)
        return surface

    def _sprout(self, center: Vector2 | None = None) -> None:
        if self._sprouted:
            return
        self._sprouted = True
        self.weapon.spawn_patch(center or self.pos)
        self.kill()

    def update(self, dt: float) -> None:
        self.pos += self.direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.lifetime -= dt

        if (
            self.lifetime <= 0.0
            or self.pos.x < 0
            or self.pos.x > WORLD_WIDTH
            or self.pos.y < 0
            or self.pos.y > WORLD_HEIGHT
        ):
            self._sprout()

    def on_hit(self, enemy, effect_group=None) -> None:
        if enemy.sprite_id in self.enemies_hit:
            return
        self.enemies_hit.add(enemy.sprite_id)
        self._sprout(Vector2(enemy.pos))


class BrambleSeeds(BaseWeapon):
    name = "Bramble Seeds"
    description = "Throws seeds that grow thorn patches, damaging and slowing enemies inside."
    base_damage = BRAMBLE_SEEDS_BASE_DAMAGE
    base_cooldown = BRAMBLE_SEEDS_BASE_COOLDOWN
    projectile_count = BRAMBLE_SEEDS_BASE_PROJECTILE_COUNT
    patch_radius = BRAMBLE_SEEDS_PATCH_RADIUS
    patch_duration = BRAMBLE_SEEDS_PATCH_DURATION
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in BRAMBLE_SEEDS_UPGRADE_LEVELS]
        self.patches: list[dict] = []

    @property
    def effective_patch_radius(self) -> float:
        return self.patch_radius * self.owner.area_size_multiplier

    def _build_patch_visuals(self) -> tuple[list[float], list[tuple[float, float]]]:
        thorn_step = _TWO_PI / BRAMBLE_SEEDS_PATCH_THORN_COUNT
        thorn_angles = [
            i * thorn_step + random.uniform(-thorn_step * 0.25, thorn_step * 0.25)
            for i in range(BRAMBLE_SEEDS_PATCH_THORN_COUNT)
        ]
        tendrils = [
            (random.random() * _TWO_PI, random.uniform(0.25, 0.9))
            for _ in range(BRAMBLE_SEEDS_PATCH_TENDRIL_COUNT)
        ]
        return thorn_angles, tendrils

    def spawn_patch(self, center: Vector2) -> None:
        thorn_angles, tendrils = self._build_patch_visuals()
        self.patches.append({
            "center": Vector2(center),
            "radius": self.effective_patch_radius,
            "remaining": self.patch_duration,
            "duration": self.patch_duration,
            "tick_timer": 0.0,
            "damage": self._scaled_dot_damage(self.base_damage),
            "thorn_angles": thorn_angles,
            "tendrils": tendrils,
        })

    def _spawn_seed(self, direction: Vector2) -> None:
        BrambleSeedProjectile(
            pos=self.owner.pos,
            direction=direction,
            speed=BRAMBLE_SEEDS_PROJECTILE_SPEED,
            groups=self.projectile_group,
            weapon=self,
            lifetime=BRAMBLE_SEEDS_PROJECTILE_LIFETIME,
        )

    def fire(self) -> None:
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = BRAMBLE_SEEDS_TARGETING_RANGE * BRAMBLE_SEEDS_TARGETING_RANGE

        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq and distance_sq <= max_range_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if nearest_enemy is None:
            return

        base_direction = nearest_enemy.pos - self.owner.pos
        if base_direction.length_squared() == 0:
            base_direction = self.owner.facing if self.owner.facing.length_squared() > 0 else Vector2(1, 0)
        base_direction = base_direction.normalize()

        AudioManager.instance().play_sfx(AudioManager.WEAPON_BRAMBLE_SEEDS)

        for index in range(self.projectile_count):
            if self.projectile_count == 1:
                direction = base_direction
            else:
                angle_offset = (index - (self.projectile_count - 1) / 2) * BRAMBLE_SEEDS_SPREAD
                direction = base_direction.rotate(angle_offset)
            self._spawn_seed(direction)

    def _damage_patch_enemies(self, patch: dict) -> None:
        radius_sq = patch["radius"] * patch["radius"]
        center = patch["center"]
        tick_damage = patch["damage"]
        for enemy in self.enemy_group:
            if not enemy.alive():
                continue
            if (enemy.pos - center).length_squared() > radius_sq:
                continue
            to_attacker = self.owner.pos - enemy.pos
            hit_dir = to_attacker.normalize() if to_attacker.length_squared() > 0 else None
            enemy.take_damage(
                tick_damage,
                hit_direction=hit_dir,
                attacker=self.owner,
                knockback_force=0,
            )
            if hasattr(enemy, "apply_slow"):
                enemy.apply_slow(
                    BRAMBLE_SEEDS_SLOW_MULTIPLIER,
                    BRAMBLE_SEEDS_SLOW_DURATION,
                    source=self,
                )
            if self.effect_group is not None:
                from src.entities.effects import DamageNumber, HitSpark
                DamageNumber(enemy.pos - Vector2(0, 20), tick_damage, [self.effect_group])
                HitSpark(enemy.pos, BRAMBLE_SEEDS_HIT_SPARK_COLOR, [self.effect_group])

    def _tick_patches(self, dt: float) -> None:
        i = 0
        while i < len(self.patches):
            patch = self.patches[i]
            patch["remaining"] -= dt
            patch["tick_timer"] -= dt

            while patch["tick_timer"] <= 0.0 and patch["remaining"] > 0.0:
                self._damage_patch_enemies(patch)
                patch["tick_timer"] += BRAMBLE_SEEDS_TICK_INTERVAL

            if patch["remaining"] <= 0.0:
                self.patches.pop(i)
            else:
                i += 1

    def update(self, dt: float) -> None:
        super().update(dt)
        self._tick_patches(dt)

    def on_owner_inactive(self) -> None:
        self.patches.clear()
        for enemy in self.enemy_group:
            if hasattr(enemy, "remove_slow"):
                enemy.remove_slow(self)
        for projectile in list(self.projectile_group):
            if isinstance(projectile, BrambleSeedProjectile) and projectile.owner is self.owner:
                projectile.kill()

    def draw_under(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        if not self.patches:
            return

        temp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        width, height = surface.get_size()

        for patch in self.patches:
            radius = int(patch["radius"])
            center = patch["center"] - camera_offset
            cx = int(center.x)
            cy = int(center.y)
            if cx + radius < 0 or cx - radius > width or cy + radius < 0 or cy - radius > height:
                continue

            progress = patch["remaining"] / patch["duration"] if patch["duration"] > 0 else 0.0
            fill_alpha = int(BRAMBLE_SEEDS_PATCH_ALPHA * min(1.0, progress * 2.0))
            ring_alpha = int(BRAMBLE_SEEDS_PATCH_RING_ALPHA * min(1.0, progress * 2.0))

            pygame.draw.circle(temp, (*BRAMBLE_SEEDS_PATCH_FILL_COLOR, fill_alpha), (cx, cy), radius)
            pygame.draw.circle(temp, (*BRAMBLE_SEEDS_PATCH_RING_COLOR, ring_alpha), (cx, cy), radius, 3)

            for angle, scale in patch["tendrils"]:
                end_radius = radius * scale
                end_x = int(cx + math.cos(angle) * end_radius)
                end_y = int(cy + math.sin(angle) * end_radius)
                pygame.draw.line(temp, (*BRAMBLE_SEEDS_PATCH_RING_COLOR, ring_alpha), (cx, cy), (end_x, end_y), 2)

            for angle in patch["thorn_angles"]:
                inner = radius * 0.82
                outer = radius * 1.03
                x0 = int(cx + math.cos(angle) * inner)
                y0 = int(cy + math.sin(angle) * inner)
                x1 = int(cx + math.cos(angle) * outer)
                y1 = int(cy + math.sin(angle) * outer)
                pygame.draw.line(temp, (*BRAMBLE_SEEDS_PATCH_THORN_COLOR, ring_alpha), (x0, y0), (x1, y1), 2)

        surface.blit(temp, (0, 0))
