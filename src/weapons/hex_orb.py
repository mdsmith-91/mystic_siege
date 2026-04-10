from collections import deque
import random

import pygame
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    DOT_DISPLAY_TICK_INTERVAL,
    HEX_ORB_BASE_COOLDOWN,
    HEX_ORB_BASE_DAMAGE,
    HEX_ORB_BASE_PIERCE,
    HEX_ORB_BASE_PROJECTILE_COUNT,
    HEX_ORB_CORE_COLOR,
    HEX_ORB_CORE_RADIUS,
    HEX_ORB_CURSE_DAMAGE,
    HEX_ORB_CURSE_DURATION,
    HEX_ORB_CURSE_RADIUS,
    HEX_ORB_CURSE_TICK_COLOR,
    HEX_ORB_HIT_SPARK_COLOR,
    HEX_ORB_HITBOX_SIZE,
    HEX_ORB_MID_GLOW_ALPHA,
    HEX_ORB_MID_GLOW_COLOR,
    HEX_ORB_MID_GLOW_RADIUS,
    HEX_ORB_OUTER_GLOW_ALPHA,
    HEX_ORB_OUTER_GLOW_COLOR,
    HEX_ORB_OUTER_GLOW_RADIUS,
    HEX_ORB_PROJECTILE_COLOR,
    HEX_ORB_PROJECTILE_LIFETIME,
    HEX_ORB_PROJECTILE_SIZE,
    HEX_ORB_PROJECTILE_SPEED,
    HEX_ORB_SPREAD,
    HEX_ORB_STAGGER,
    HEX_ORB_TARGETING_RANGE,
    HEX_ORB_TRAIL_COLOR,
    HEX_ORB_TRAIL_LENGTH,
    HEX_ORB_TRAIL_MAX_ALPHA,
    HEX_ORB_TRAIL_MAX_RADIUS,
    HEX_ORB_TRAIL_RECORD_INTERVAL,
    HEX_ORB_UPGRADE_LEVELS,
)
from src.entities.projectile import Projectile
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class HexOrbProjectile(Projectile):
    """Slow curse orb that delegates curse application back to its weapon."""

    def __init__(
        self,
        pos,
        direction: Vector2,
        speed: float,
        damage: float,
        groups,
        enemy_group_ref,
        weapon,
        pierce: int = 0,
        owner_crit_chance: float = 0.0,
        owner=None,
    ):
        self.weapon = weapon
        self._trail: deque[Vector2] = deque(maxlen=HEX_ORB_TRAIL_LENGTH)
        self._trail_timer = 0.0
        super().__init__(
            pos=pos,
            direction=direction,
            speed=speed,
            damage=damage,
            groups=groups,
            enemy_group_ref=enemy_group_ref,
            pierce=pierce,
            color=HEX_ORB_PROJECTILE_COLOR,
            owner_crit_chance=owner_crit_chance,
            owner=owner,
            lifetime=HEX_ORB_PROJECTILE_LIFETIME,
            size=HEX_ORB_PROJECTILE_SIZE,
        )
        self.rect = pygame.Rect(0, 0, *HEX_ORB_HITBOX_SIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def _build_image(self) -> pygame.Surface:
        width, height = HEX_ORB_PROJECTILE_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        center = (width // 2, height // 2)

        pygame.draw.circle(
            surface,
            (*HEX_ORB_OUTER_GLOW_COLOR, HEX_ORB_OUTER_GLOW_ALPHA),
            center,
            HEX_ORB_OUTER_GLOW_RADIUS,
        )
        pygame.draw.circle(
            surface,
            (*HEX_ORB_MID_GLOW_COLOR, HEX_ORB_MID_GLOW_ALPHA),
            center,
            HEX_ORB_MID_GLOW_RADIUS,
        )
        pygame.draw.circle(surface, (*HEX_ORB_PROJECTILE_COLOR, 255), center, HEX_ORB_MID_GLOW_RADIUS - 2)
        pygame.draw.circle(surface, (*HEX_ORB_CORE_COLOR, 255), center, HEX_ORB_CORE_RADIUS)
        return surface

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.alive():
            self._trail_timer += dt
            if self._trail_timer >= HEX_ORB_TRAIL_RECORD_INTERVAL:
                self._trail_timer = 0.0
                self._trail.append(Vector2(self.pos))

    def on_hit(self, enemy, effect_group=None):
        if enemy.sprite_id in self.enemies_hit:
            return

        self.enemies_hit.add(enemy.sprite_id)

        is_crit = random.random() < self.owner_crit_chance
        actual_damage = self.damage * (CRIT_MULTIPLIER if is_crit else 1.0)
        enemy.take_damage(actual_damage, hit_direction=-self.direction, attacker=self.owner)
        self.weapon.apply_curse(enemy, effect_group)

        if effect_group is not None:
            from src.entities.effects import DamageNumber, HitSpark
            DamageNumber(enemy.pos - Vector2(0, 20), actual_damage, [effect_group], is_crit=is_crit)
            HitSpark(enemy.pos, HEX_ORB_HIT_SPARK_COLOR, [effect_group])

        if self.pierce <= 0:
            self.kill()
        else:
            self.pierce -= 1

    def draw_trail(self, trail_surface: pygame.Surface, camera_offset: Vector2) -> None:
        if not self._trail:
            return

        for index, trail_pos in enumerate(self._trail):
            fraction = (index + 1) / HEX_ORB_TRAIL_LENGTH
            alpha = int(HEX_ORB_TRAIL_MAX_ALPHA * fraction)
            radius = max(1, int(HEX_ORB_TRAIL_MAX_RADIUS * fraction))
            screen_pos = trail_pos - camera_offset
            pygame.draw.circle(
                trail_surface,
                (*HEX_ORB_TRAIL_COLOR, alpha),
                (int(screen_pos.x), int(screen_pos.y)),
                radius,
            )


class HexOrb(BaseWeapon):
    name = "Hex Orb"
    description = "Fires slow curse orbs that damage enemies over time."
    base_damage = HEX_ORB_BASE_DAMAGE
    base_cooldown = HEX_ORB_BASE_COOLDOWN
    projectile_count = HEX_ORB_BASE_PROJECTILE_COUNT
    pierce = HEX_ORB_BASE_PIERCE
    curse_damage = HEX_ORB_CURSE_DAMAGE
    curse_duration = HEX_ORB_CURSE_DURATION
    curse_radius = HEX_ORB_CURSE_RADIUS
    IS_SPELL = True
    USES_PROJECTILE_PIERCE_BONUS = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in HEX_ORB_UPGRADE_LEVELS]
        self.cursed_enemies: dict[object, float] = {}
        self._curse_display_timers: dict[object, float] = {}
        self._curse_crit_states: dict[object, bool] = {}
        self.pending_orbs: list[dict] = []

    def apply_curse(self, enemy, effect_group=None) -> None:
        if not enemy.alive():
            return

        self.cursed_enemies[enemy] = self.curse_duration
        if effect_group is not None:
            from src.entities.effects import HitSpark
            HitSpark(enemy.pos, HEX_ORB_CURSE_TICK_COLOR, [effect_group])

        if self.curse_radius <= 0:
            return

        radius_sq = self.curse_radius * self.curse_radius
        for nearby_enemy in self.enemy_group:
            if nearby_enemy is enemy:
                continue
            if not nearby_enemy.alive():
                continue
            if (nearby_enemy.pos - enemy.pos).length_squared() <= radius_sq:
                self.cursed_enemies[nearby_enemy] = self.curse_duration

    def _tick_curses(self, dt: float) -> None:
        curse_damage_rate = self._scaled_dot_damage(self.curse_damage)
        for enemy in list(self.cursed_enemies.keys()):
            remaining = self.cursed_enemies[enemy] - dt
            if remaining <= 0.0 or not enemy.alive():
                del self.cursed_enemies[enemy]
                self._curse_display_timers.pop(enemy, None)
                self._curse_crit_states.pop(enemy, None)
                continue

            self.cursed_enemies[enemy] = remaining
            is_crit = self._curse_crit_states.get(enemy, False)
            to_attacker = self.owner.pos - enemy.pos
            hit_dir = to_attacker.normalize() if to_attacker.length_squared() > 0 else None
            enemy.take_damage(
                curse_damage_rate * dt * (CRIT_MULTIPLIER if is_crit else 1.0),
                hit_direction=hit_dir,
                attacker=self.owner,
                knockback_force=0,
            )
            if not enemy.alive():
                self.cursed_enemies.pop(enemy, None)
                self._curse_display_timers.pop(enemy, None)
                self._curse_crit_states.pop(enemy, None)
                continue

            if self.effect_group is not None:
                elapsed = self._curse_display_timers.get(enemy, DOT_DISPLAY_TICK_INTERVAL) + dt
                if elapsed >= DOT_DISPLAY_TICK_INTERVAL:
                    new_crit = random.random() < self.owner.crit_chance
                    self._curse_crit_states[enemy] = new_crit
                    display_damage = curse_damage_rate * DOT_DISPLAY_TICK_INTERVAL * (CRIT_MULTIPLIER if new_crit else 1.0)
                    from src.entities.effects import DamageNumber
                    DamageNumber(enemy.pos - Vector2(0, 20), display_damage, [self.effect_group], is_crit=new_crit)
                    elapsed -= DOT_DISPLAY_TICK_INTERVAL
                self._curse_display_timers[enemy] = elapsed

    def _spawn_orb(self, direction: Vector2) -> None:
        HexOrbProjectile(
            pos=self.owner.pos,
            direction=direction,
            speed=HEX_ORB_PROJECTILE_SPEED,
            damage=self._scaled_damage(self.base_damage),
            groups=self.projectile_group,
            enemy_group_ref=self.enemy_group,
            weapon=self,
            pierce=self._get_effective_projectile_pierce(),
            owner_crit_chance=self.owner.crit_chance,
            owner=self.owner,
        )

    def fire(self):
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = HEX_ORB_TARGETING_RANGE * HEX_ORB_TARGETING_RANGE

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

        AudioManager.instance().play_sfx(AudioManager.WEAPON_HEX_ORB)
        base_direction = base_direction.normalize()

        for index in range(self.projectile_count):
            if self.projectile_count == 1:
                direction = base_direction
            else:
                angle_offset = (index - (self.projectile_count - 1) / 2) * HEX_ORB_SPREAD
                direction = base_direction.rotate(angle_offset)
            delay = index * HEX_ORB_STAGGER
            if delay == 0:
                self._spawn_orb(direction)
            else:
                self.pending_orbs.append({"delay": delay, "direction": direction})

    def update(self, dt: float) -> None:
        super().update(dt)
        i = 0
        while i < len(self.pending_orbs):
            orb = self.pending_orbs[i]
            orb["delay"] -= dt
            if orb["delay"] <= 0.0:
                self._spawn_orb(orb["direction"])
                self.pending_orbs.pop(i)
            else:
                i += 1
        self._tick_curses(dt)

    def on_owner_inactive(self):
        self.pending_orbs.clear()
        self.cursed_enemies.clear()
        self._curse_display_timers.clear()
        self._curse_crit_states.clear()
        for projectile in list(self.projectile_group):
            if isinstance(projectile, HexOrbProjectile) and projectile.owner is self.owner:
                projectile.kill()

    def draw_under(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        trail_surface = None
        for projectile in self.projectile_group:
            if isinstance(projectile, HexOrbProjectile) and projectile.owner is self.owner and projectile._trail:
                if trail_surface is None:
                    trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                projectile.draw_trail(trail_surface, camera_offset)
        if trail_surface is not None:
            surface.blit(trail_surface, (0, 0))
