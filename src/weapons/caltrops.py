import math

import pygame
from pygame.math import Vector2

from settings import (
    CALTROPS_BASE_COOLDOWN,
    CALTROPS_BASE_DAMAGE,
    CALTROPS_BASE_PROJECTILE_COUNT,
    CALTROPS_BLEED_COLOR,
    CALTROPS_BLEED_DAMAGE,
    CALTROPS_BLEED_DURATION,
    CALTROPS_HITBOX_SIZE,
    CALTROPS_PATCH_ALPHA,
    CALTROPS_PATCH_CALTROP_ALPHA,
    CALTROPS_PATCH_DURATION,
    CALTROPS_PATCH_FILL_COLOR,
    CALTROPS_PATCH_RADIUS,
    CALTROPS_PROJECTILE_COLOR,
    CALTROPS_PROJECTILE_EDGE_COLOR,
    CALTROPS_PROJECTILE_LIFETIME,
    CALTROPS_PROJECTILE_OUTLINE_COLOR,
    CALTROPS_PROJECTILE_SIZE,
    CALTROPS_SLOW_DURATION,
    CALTROPS_SLOW_MULTIPLIER,
    CALTROPS_SPREAD,
    CALTROPS_TARGETING_RANGE,
    CALTROPS_THROW_SPEED,
    CALTROPS_TICK_INTERVAL,
    CALTROPS_UPGRADE_LEVELS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


# Fixed scatter positions as (x_frac, y_frac) fractions of patch radius.
# Arranged to look like dropped caltrops, not a radial pattern.
_CALTROP_SCATTER_OFFSETS: list[tuple[float, float]] = [
    (0.0, -0.05),
    (0.38, -0.28),
    (-0.35, 0.30),
    (0.15, 0.40),
    (-0.42, -0.18),
]


class CaltropProjectile(pygame.sprite.Sprite):
    """Thrown caltrop that settles into a short-lived hazard."""

    def __init__(self, pos, direction: Vector2, speed: float, groups, weapon):
        super().__init__(groups)
        self.weapon = weapon
        self.owner = weapon.owner
        self.direction = direction.normalize()
        self.speed = speed
        self.lifetime = CALTROPS_PROJECTILE_LIFETIME
        self.pos = Vector2(pos)
        self.is_enemy_projectile = False
        self.enemies_hit = set()
        self.image = self._build_image()
        self.rect = pygame.Rect(0, 0, *CALTROPS_HITBOX_SIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def _build_image(self) -> pygame.Surface:
        width, height = CALTROPS_PROJECTILE_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        center = (width // 2, height // 2)
        arm = max(3, min(width, height) // 2 - 1)

        pygame.draw.line(
            surface,
            CALTROPS_PROJECTILE_OUTLINE_COLOR,
            (center[0] - arm, center[1] - arm),
            (center[0] + arm, center[1] + arm),
            3,
        )
        pygame.draw.line(
            surface,
            CALTROPS_PROJECTILE_OUTLINE_COLOR,
            (center[0] - arm, center[1] + arm),
            (center[0] + arm, center[1] - arm),
            3,
        )
        pygame.draw.line(
            surface,
            CALTROPS_PROJECTILE_COLOR,
            (center[0] - arm, center[1] - arm),
            (center[0] + arm, center[1] + arm),
            1,
        )
        pygame.draw.line(
            surface,
            CALTROPS_PROJECTILE_EDGE_COLOR,
            (center[0] - arm, center[1] + arm),
            (center[0] + arm, center[1] - arm),
            1,
        )
        return surface

    def _settle(self, center: Vector2 | None = None) -> None:
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
            self._settle()

    def on_hit(self, enemy, effect_group=None) -> None:
        if enemy.sprite_id in self.enemies_hit:
            return
        self.enemies_hit.add(enemy.sprite_id)
        self._settle(Vector2(enemy.pos))


class Caltrops(BaseWeapon):
    name = "Caltrops"
    description = "Scatters caltrops that slow enemies and apply a small bleed."
    base_damage = CALTROPS_BASE_DAMAGE
    base_cooldown = CALTROPS_BASE_COOLDOWN
    projectile_count = CALTROPS_BASE_PROJECTILE_COUNT
    patch_radius = CALTROPS_PATCH_RADIUS
    patch_duration = CALTROPS_PATCH_DURATION
    bleed_damage = CALTROPS_BLEED_DAMAGE
    bleed_duration = CALTROPS_BLEED_DURATION
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in CALTROPS_UPGRADE_LEVELS]
        self.patches: list[dict] = []
        self._enemy_hit_cooldowns: dict[int, float] = {}
        self._bleeding_enemies: dict[object, float] = {}
        self._draw_surface: pygame.Surface | None = None

    @property
    def effective_patch_radius(self) -> float:
        return self.patch_radius * self.owner.area_size_multiplier

    def _scaled_physical_dot_damage(self, base_damage: float) -> float:
        return (
            base_damage
            * self.owner.damage_multiplier
            * getattr(self.owner, "physical_damage_multiplier", 1.0)
        )

    def spawn_patch(self, center: Vector2) -> None:
        self.patches.append({
            "center": Vector2(center),
            "radius": self.effective_patch_radius,
            "remaining": self.patch_duration,
            "duration": self.patch_duration,
            "tick_timer": 0.0,
            "damage": self._scaled_damage(self.base_damage),
        })

    def _spawn_caltrop(self, direction: Vector2) -> None:
        CaltropProjectile(
            pos=self.owner.pos,
            direction=direction,
            speed=CALTROPS_THROW_SPEED,
            groups=self.projectile_group,
            weapon=self,
        )

    def fire(self) -> None:
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = CALTROPS_TARGETING_RANGE * CALTROPS_TARGETING_RANGE

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

        AudioManager.instance().play_sfx(AudioManager.WEAPON_CALTROPS)

        for index in range(self.projectile_count):
            if self.projectile_count == 1:
                direction = base_direction
            else:
                angle_offset = (index - (self.projectile_count - 1) / 2) * CALTROPS_SPREAD
                direction = base_direction.rotate(angle_offset)
            self._spawn_caltrop(direction)

    def _damage_patch_enemies(self, patch: dict) -> None:
        radius_sq = patch["radius"] * patch["radius"]
        center = patch["center"]
        tick_damage = patch["damage"]
        for enemy in self.enemy_group:
            if not enemy.alive():
                continue
            if (enemy.pos - center).length_squared() > radius_sq:
                continue

            can_damage = self._enemy_hit_cooldowns.get(enemy.sprite_id, 0.0) <= 0.0
            if can_damage:
                to_attacker = self.owner.pos - enemy.pos
                hit_dir = to_attacker.normalize() if to_attacker.length_squared() > 0 else None
                enemy.take_damage(
                    tick_damage,
                    hit_direction=hit_dir,
                    attacker=self.owner,
                    knockback_force=0,
                )
                self._enemy_hit_cooldowns[enemy.sprite_id] = CALTROPS_TICK_INTERVAL
                self._bleeding_enemies[enemy] = self.bleed_duration
                if self.effect_group is not None:
                    from src.entities.effects import DamageNumber, HitSpark
                    DamageNumber(enemy.pos - Vector2(0, 20), tick_damage, [self.effect_group])
                    HitSpark(enemy.pos, CALTROPS_BLEED_COLOR, [self.effect_group])

    def _tick_patches(self, dt: float) -> None:
        for enemy_id in list(self._enemy_hit_cooldowns.keys()):
            remaining = self._enemy_hit_cooldowns[enemy_id] - dt
            if remaining <= 0.0:
                del self._enemy_hit_cooldowns[enemy_id]
            else:
                self._enemy_hit_cooldowns[enemy_id] = remaining

        had_patches = bool(self.patches)
        if not had_patches:
            return

        i = 0
        while i < len(self.patches):
            patch = self.patches[i]
            patch["remaining"] -= dt
            patch["tick_timer"] -= dt

            # Per-frame: keep enemies slowed while inside the patch
            if patch["remaining"] > 0.0:
                radius_sq = patch["radius"] * patch["radius"]
                center = patch["center"]
                for enemy in self.enemy_group:
                    if enemy.alive() and (enemy.pos - center).length_squared() <= radius_sq:
                        if hasattr(enemy, "apply_slow"):
                            enemy.apply_slow(CALTROPS_SLOW_MULTIPLIER, CALTROPS_SLOW_DURATION, source=self)

            if patch["tick_timer"] <= 0.0 and patch["remaining"] > 0.0:
                self._damage_patch_enemies(patch)
                patch["tick_timer"] = CALTROPS_TICK_INTERVAL

            if patch["remaining"] <= 0.0:
                self.patches.pop(i)
            else:
                i += 1

        if had_patches and not self.patches:
            self._enemy_hit_cooldowns.clear()
            for enemy in self.enemy_group:
                if hasattr(enemy, "remove_slow"):
                    enemy.remove_slow(self)

    def _tick_bleeds(self, dt: float) -> None:
        tick_damage = self._scaled_physical_dot_damage(self.bleed_damage) * dt
        for enemy in list(self._bleeding_enemies.keys()):
            remaining = self._bleeding_enemies[enemy] - dt
            if remaining <= 0.0 or not enemy.alive():
                self._bleeding_enemies.pop(enemy, None)
                continue

            self._bleeding_enemies[enemy] = remaining
            to_attacker = self.owner.pos - enemy.pos
            hit_dir = to_attacker.normalize() if to_attacker.length_squared() > 0 else None
            enemy.take_damage(
                tick_damage,
                hit_direction=hit_dir,
                attacker=self.owner,
                knockback_force=0,
            )

    def update(self, dt: float) -> None:
        super().update(dt)
        self._tick_patches(dt)
        self._tick_bleeds(dt)

    def on_owner_inactive(self) -> None:
        self.patches.clear()
        self._enemy_hit_cooldowns.clear()
        self._bleeding_enemies.clear()
        for enemy in self.enemy_group:
            if hasattr(enemy, "remove_slow"):
                enemy.remove_slow(self)
        for projectile in list(self.projectile_group):
            if isinstance(projectile, CaltropProjectile) and projectile.owner is self.owner:
                projectile.kill()

    def draw_under(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        if not self.patches:
            return

        size = surface.get_size()
        if self._draw_surface is None or self._draw_surface.get_size() != size:
            self._draw_surface = pygame.Surface(size, pygame.SRCALPHA)
        self._draw_surface.fill((0, 0, 0, 0))
        temp = self._draw_surface
        width, height = size

        for patch in self.patches:
            radius = int(patch["radius"])
            center = patch["center"] - camera_offset
            cx = int(center.x)
            cy = int(center.y)
            if cx + radius < 0 or cx - radius > width or cy + radius < 0 or cy - radius > height:
                continue

            progress = patch["remaining"] / patch["duration"] if patch["duration"] > 0 else 0.0
            fade = min(1.0, progress * 2.0)
            fill_alpha = int(CALTROPS_PATCH_ALPHA * fade)
            shape_alpha = int(CALTROPS_PATCH_CALTROP_ALPHA * fade)

            # Subtle translucent area indicator
            pygame.draw.circle(temp, (*CALTROPS_PATCH_FILL_COLOR, fill_alpha), (cx, cy), radius)

            # Individual scattered caltrop shapes — look like dropped metal spikes
            arm = max(3, radius // 5)
            for ox, oy in _CALTROP_SCATTER_OFFSETS:
                sx = int(cx + ox * radius)
                sy = int(cy + oy * radius)
                pygame.draw.line(
                    temp,
                    (*CALTROPS_PROJECTILE_OUTLINE_COLOR, shape_alpha),
                    (sx - arm, sy - arm), (sx + arm, sy + arm), 3,
                )
                pygame.draw.line(
                    temp,
                    (*CALTROPS_PROJECTILE_OUTLINE_COLOR, shape_alpha),
                    (sx - arm, sy + arm), (sx + arm, sy - arm), 3,
                )
                pygame.draw.line(
                    temp,
                    (*CALTROPS_PROJECTILE_EDGE_COLOR, shape_alpha),
                    (sx - arm, sy - arm), (sx + arm, sy + arm), 1,
                )
                pygame.draw.line(
                    temp,
                    (*CALTROPS_PROJECTILE_COLOR, shape_alpha),
                    (sx - arm, sy + arm), (sx + arm, sy - arm), 1,
                )

        surface.blit(temp, (0, 0))
