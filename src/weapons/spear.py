import math
import random

import pygame
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    SPEAR_BASE_COOLDOWN,
    SPEAR_BASE_DAMAGE,
    SPEAR_BASE_PIERCE,
    SPEAR_BUTT_COLOR,
    SPEAR_EXTEND_DURATION,
    SPEAR_HEAD_COLOR,
    SPEAR_HEAD_HALF_WIDTH,
    SPEAR_HEAD_LENGTH,
    SPEAR_HEAD_OUTLINE_COLOR,
    SPEAR_HIGHLIGHT_COLOR,
    SPEAR_HIT_SPARK_COLOR,
    SPEAR_HOLD_DURATION,
    SPEAR_KNOCKBACK_FORCE,
    SPEAR_L5_SECOND_DELAY,
    SPEAR_RETRACT_DURATION,
    SPEAR_SAMPLE_COUNT,
    SPEAR_SHAFT_COLOR,
    SPEAR_SHAFT_HALF_WIDTH,
    SPEAR_SHAFT_OUTLINE_COLOR,
    SPEAR_HAND_OFFSET,
    SPEAR_TARGETING_RANGE,
    SPEAR_THRUST_LENGTH,
    SPEAR_UPGRADE_LEVELS,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class Spear(BaseWeapon):
    name = "Spear"
    description = "Thrusts a spear forward in a narrow lane, piercing through enemies in line."
    base_damage = SPEAR_BASE_DAMAGE
    base_cooldown = SPEAR_BASE_COOLDOWN
    thrust_length = SPEAR_THRUST_LENGTH
    pierce = SPEAR_BASE_PIERCE
    double_thrust_count = 0  # incremented to 1 at L5 by the upgrade system
    crit_bonus = 0.0          # additive crit chance added at L5
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(u) for u in SPEAR_UPGRADE_LEVELS]
        self.active_thrusts: list[dict] = []
        self._pending_second_thrust: tuple[float, Vector2] | None = None

    @property
    def _effective_thrust_length(self) -> float:
        return self.thrust_length * self.owner.area_size_multiplier

    def _get_target_direction(self) -> Vector2 | None:
        nearest_enemy = None
        nearest_dist_sq = float("inf")
        max_range_sq = SPEAR_TARGETING_RANGE * SPEAR_TARGETING_RANGE

        for enemy in self.enemy_group:
            dist_sq = (enemy.pos - self.owner.pos).length_squared()
            if dist_sq < nearest_dist_sq and dist_sq <= max_range_sq:
                nearest_dist_sq = dist_sq
                nearest_enemy = enemy

        if nearest_enemy is None:
            return None
        diff = nearest_enemy.pos - self.owner.pos
        return diff.normalize() if diff.length_squared() > 0 else None

    def _spawn_thrust(self, direction: Vector2) -> None:
        total = SPEAR_EXTEND_DURATION + SPEAR_HOLD_DURATION + SPEAR_RETRACT_DURATION
        self.active_thrusts.append({
            "timer": 0.0,
            "direction": Vector2(direction),
            "hit_enemies": set(),
            "total_duration": total,
        })

    def fire(self) -> None:
        direction = self._get_target_direction()
        if direction is None:
            return
        AudioManager.instance().play_sfx(AudioManager.WEAPON_SPEAR)
        self._spawn_thrust(direction)
        if self.double_thrust_count > 0:
            if self._pending_second_thrust is not None:
                # Cooldown fired before the prior second stab could execute — fire it now
                _, prev_dir = self._pending_second_thrust
                self._spawn_thrust(prev_dir)
                AudioManager.instance().play_sfx(AudioManager.WEAPON_SPEAR)
            self._pending_second_thrust = (SPEAR_L5_SECOND_DELAY, Vector2(direction))

    def update(self, dt: float) -> None:
        self.cooldown_timer -= dt
        if self.cooldown_timer <= 0.0:
            self.fire()
            self.cooldown_timer = self._get_effective_cooldown()

        # Tick the L5 follow-up thrust
        if self._pending_second_thrust is not None:
            delay, direction = self._pending_second_thrust
            delay -= dt
            if delay <= 0.0:
                self._spawn_thrust(direction)
                AudioManager.instance().play_sfx(AudioManager.WEAPON_SPEAR)
                self._pending_second_thrust = None
            else:
                self._pending_second_thrust = (delay, direction)

        # Advance all active thrusts
        i = 0
        while i < len(self.active_thrusts):
            thrust = self.active_thrusts[i]
            thrust["timer"] += dt
            self._damage_enemies(thrust)
            if thrust["timer"] >= thrust["total_duration"]:
                self.active_thrusts.pop(i)
            else:
                i += 1

    def _tip_pos(self, thrust: dict) -> tuple[Vector2, bool]:
        """Return (tip world position, is_active_phase).

        Active phase is extend + hold; retract is visual-only.
        Origin tracks the player's current right-hand position each frame.
        """
        timer = thrust["timer"]
        direction = thrust["direction"]
        perp = direction.rotate(90)
        origin = self.owner.pos + perp * SPEAR_HAND_OFFSET
        length = self._effective_thrust_length

        extend_end = SPEAR_EXTEND_DURATION
        hold_end = extend_end + SPEAR_HOLD_DURATION
        total = thrust["total_duration"]

        if timer < extend_end:
            progress = timer / SPEAR_EXTEND_DURATION if SPEAR_EXTEND_DURATION > 0 else 1.0
            return origin + direction * (length * progress), True
        elif timer < hold_end:
            return origin + direction * length, True
        else:
            progress = (timer - hold_end) / SPEAR_RETRACT_DURATION if SPEAR_RETRACT_DURATION > 0 else 1.0
            return origin + direction * (length * max(0.0, 1.0 - progress)), False

    def _damage_enemies(self, thrust: dict) -> None:
        tip, is_active = self._tip_pos(thrust)
        if not is_active:
            return

        direction = thrust["direction"]
        origin = self.owner.pos + direction.rotate(90) * SPEAR_HAND_OFFSET

        for enemy in self.enemy_group:
            if len(thrust["hit_enemies"]) > self.pierce:
                break
            if enemy.sprite_id in thrust["hit_enemies"]:
                continue

            hit = False
            for sample in range(1, SPEAR_SAMPLE_COUNT + 1):
                t = sample / SPEAR_SAMPLE_COUNT
                pt = origin.lerp(tip, t)
                if enemy.rect.collidepoint(pt.x, pt.y):
                    hit = True
                    break

            if not hit:
                continue

            is_crit = random.random() < min(1.0, self.owner.crit_chance + self.crit_bonus)
            damage = self._scaled_damage(self.base_damage) * (CRIT_MULTIPLIER if is_crit else 1.0)
            diff = self.owner.pos - enemy.pos
            hit_dir = diff.normalize() if diff.length_squared() > 0 else Vector2(1, 0)
            enemy.take_damage(
                damage,
                hit_direction=hit_dir,
                attacker=self.owner,
                knockback_force=SPEAR_KNOCKBACK_FORCE,
            )
            thrust["hit_enemies"].add(enemy.sprite_id)

            if self.effect_group is not None:
                from src.entities.effects import DamageNumber, HitSpark
                DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                HitSpark(enemy.pos, SPEAR_HIT_SPARK_COLOR, [self.effect_group])

    def on_owner_inactive(self) -> None:
        self.active_thrusts.clear()
        self._pending_second_thrust = None

    def draw(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        for thrust in self.active_thrusts:
            tip, _ = self._tip_pos(thrust)
            direction = thrust["direction"]
            perp = direction.rotate(90)

            # Screen-space tip and hand position (tracks player each frame)
            hand_pos = self.owner.pos + perp * SPEAR_HAND_OFFSET
            tip_s = tip - camera_offset
            origin_s = hand_pos - camera_offset

            # Shaft: from butt (slightly behind origin) to socket (where head begins)
            # Socket is at tip - direction * HEAD_LENGTH
            socket = tip - direction * SPEAR_HEAD_LENGTH
            socket_s = socket - camera_offset

            shw = SPEAR_SHAFT_HALF_WIDTH
            shaft_pts = [
                (origin_s + perp * shw).xy,
                (origin_s - perp * shw).xy,
                (socket_s - perp * shw).xy,
                (socket_s + perp * shw).xy,
            ]
            pygame.draw.polygon(surface, SPEAR_SHAFT_COLOR, shaft_pts)
            pygame.draw.polygon(surface, SPEAR_SHAFT_OUTLINE_COLOR, shaft_pts, 1)

            # Spearhead: isoceles triangle — base at socket, apex at tip
            hhw = SPEAR_HEAD_HALF_WIDTH
            head_pts = [
                tip_s.xy,
                (socket_s + perp * hhw).xy,
                (socket_s - perp * hhw).xy,
            ]
            pygame.draw.polygon(surface, SPEAR_HEAD_COLOR, head_pts)
            pygame.draw.polygon(surface, SPEAR_HEAD_OUTLINE_COLOR, head_pts, 1)

            # Blade highlight: a thin centerline from socket toward tip
            hl_start = socket_s + direction * 3
            hl_end = tip_s - direction * 4
            pygame.draw.line(surface, SPEAR_HIGHLIGHT_COLOR,
                             (int(hl_start.x), int(hl_start.y)),
                             (int(hl_end.x), int(hl_end.y)), 1)

            # Metal butt cap at origin
            pygame.draw.circle(surface, SPEAR_BUTT_COLOR,
                                (int(origin_s.x), int(origin_s.y)), SPEAR_SHAFT_HALF_WIDTH + 1)
            pygame.draw.circle(surface, SPEAR_HEAD_OUTLINE_COLOR,
                                (int(origin_s.x), int(origin_s.y)), SPEAR_SHAFT_HALF_WIDTH + 1, 1)
