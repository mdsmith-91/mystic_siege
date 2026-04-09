import math
import random

import pygame
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    SWORD_ARC_SAMPLE_COUNT,
    SWORD_BASE_COOLDOWN,
    SWORD_BASE_DAMAGE,
    SWORD_BLADE_COLOR,
    SWORD_BLADE_LENGTH,
    SWORD_BLADE_SAMPLE_COUNT,
    SWORD_BLADE_WIDTH,
    SWORD_GUARD_COLOR,
    SWORD_GUARD_HALF_WIDTH,
    SWORD_GUARD_THICKNESS,
    SWORD_GRIP_COLOR,
    SWORD_GRIP_LENGTH,
    SWORD_GRIP_WIDTH,
    SWORD_HAND_OFFSET,
    SWORD_HIGHLIGHT_COLOR,
    SWORD_HIT_SPARK_COLOR,
    SWORD_KNOCKBACK_FORCE,
    SWORD_L5_SECOND_DELAY,
    SWORD_OUTLINE_COLOR,
    SWORD_POMMEL_RADIUS,
    SWORD_RECOVERY_DURATION,
    SWORD_SWEEP_ANGLE,
    SWORD_SWEEP_DURATION,
    SWORD_SWING_TRAIL_COLOR,
    SWORD_SWING_TRAIL_WIDTH,
    SWORD_TAPER_START,
    SWORD_TARGETING_RANGE,
    SWORD_UPGRADE_LEVELS,
    SWORD_WINDUP_DURATION,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class Sword(BaseWeapon):
    name = "Sword"
    description = "Sweeps a steel blade through nearby enemies with deliberate, heavy slashes."
    base_damage = SWORD_BASE_DAMAGE
    base_cooldown = SWORD_BASE_COOLDOWN
    targeting_range = SWORD_TARGETING_RANGE
    hand_offset = SWORD_HAND_OFFSET
    blade_length = SWORD_BLADE_LENGTH
    sweep_angle = SWORD_SWEEP_ANGLE
    windup_duration = SWORD_WINDUP_DURATION
    sweep_duration = SWORD_SWEEP_DURATION
    recovery_duration = SWORD_RECOVERY_DURATION
    knockback_force = SWORD_KNOCKBACK_FORCE
    double_slash_count = 0
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in SWORD_UPGRADE_LEVELS]
        self.active_swings: list[dict] = []
        self._pending_followup: tuple[float, Vector2] | None = None

    @property
    def effective_targeting_range(self) -> float:
        return self.targeting_range * self.owner.area_size_multiplier

    @property
    def effective_hand_offset(self) -> float:
        return self.hand_offset * self.owner.area_size_multiplier

    @property
    def effective_blade_length(self) -> float:
        return self.blade_length * self.owner.area_size_multiplier

    @property
    def effective_grip_length(self) -> float:
        return SWORD_GRIP_LENGTH * self.owner.area_size_multiplier

    def _get_target_direction(self) -> Vector2 | None:
        nearest_enemy = None
        nearest_dist_sq = float("inf")
        max_range_sq = self.effective_targeting_range * self.effective_targeting_range

        for enemy in self.enemy_group:
            dist_sq = (enemy.pos - self.owner.pos).length_squared()
            if dist_sq <= max_range_sq and dist_sq < nearest_dist_sq:
                nearest_enemy = enemy
                nearest_dist_sq = dist_sq

        if nearest_enemy is None:
            return None

        diff = nearest_enemy.pos - self.owner.pos
        if diff.length_squared() <= 0:
            return None
        return diff.normalize()

    def _spawn_swing(self, direction: Vector2, reverse: bool = False) -> None:
        center_angle = math.degrees(math.atan2(direction.y, direction.x))
        half_sweep = self.sweep_angle / 2
        start_angle = center_angle - half_sweep
        end_angle = center_angle + half_sweep
        if reverse:
            start_angle, end_angle = end_angle, start_angle

        total_duration = self.windup_duration + self.sweep_duration + self.recovery_duration
        self.active_swings.append(
            {
                "timer": 0.0,
                "start_angle": start_angle,
                "end_angle": end_angle,
                "current_angle": start_angle,
                "previous_angle": start_angle,
                "current_extension": 0.0,
                "previous_extension": 0.0,
                "hit_enemies": set(),
                "total_duration": total_duration,
            }
        )

    def fire(self) -> bool:
        direction = self._get_target_direction()
        if direction is None:
            return False

        AudioManager.instance().play_sfx(AudioManager.WEAPON_SWORD)
        self._spawn_swing(direction, reverse=False)
        if self.double_slash_count > 0:
            self._pending_followup = (SWORD_L5_SECOND_DELAY, Vector2(direction))
        return True

    def update(self, dt: float) -> None:
        self.cooldown_timer -= dt
        if self.cooldown_timer <= 0.0 and not self.active_swings and self._pending_followup is None:
            if self.fire():
                self.cooldown_timer = self._get_effective_cooldown()

        if self._pending_followup is not None:
            delay, direction = self._pending_followup
            delay -= dt
            if delay <= 0.0:
                AudioManager.instance().play_sfx(AudioManager.WEAPON_SWORD)
                self._spawn_swing(direction, reverse=True)
                self._pending_followup = None
            else:
                self._pending_followup = (delay, direction)

        swing_index = 0
        while swing_index < len(self.active_swings):
            swing = self.active_swings[swing_index]
            swing["timer"] += dt
            self._update_swing_pose(swing)
            self._damage_enemies(swing)

            if swing["timer"] >= swing["total_duration"]:
                self.active_swings.pop(swing_index)
            else:
                swing_index += 1

    def _update_swing_pose(self, swing: dict) -> None:
        swing["previous_angle"] = swing["current_angle"]
        swing["previous_extension"] = swing["current_extension"]

        timer = swing["timer"]
        windup_end = self.windup_duration
        swing_end = windup_end + self.sweep_duration

        if timer < windup_end:
            progress = timer / self.windup_duration if self.windup_duration > 0 else 1.0
            swing["current_angle"] = swing["start_angle"]
            swing["current_extension"] = self.effective_blade_length * (0.45 + 0.55 * progress)
            swing["is_active"] = False
        elif timer < swing_end:
            progress = (timer - windup_end) / self.sweep_duration if self.sweep_duration > 0 else 1.0
            swing["current_angle"] = swing["start_angle"] + (
                (swing["end_angle"] - swing["start_angle"]) * progress
            )
            swing["current_extension"] = self.effective_blade_length
            swing["is_active"] = True
        else:
            progress = (timer - swing_end) / self.recovery_duration if self.recovery_duration > 0 else 1.0
            swing["current_angle"] = swing["end_angle"]
            swing["current_extension"] = self.effective_blade_length * max(0.35, 1.0 - progress)
            swing["is_active"] = False

    def _pose_points(self, angle: float, extension: float) -> tuple[Vector2, Vector2, Vector2]:
        direction = Vector2(1, 0).rotate(angle)
        hilt = self.owner.pos + direction * self.effective_hand_offset
        guard = hilt + direction * self.effective_grip_length
        tip = guard + direction * extension
        return hilt, guard, tip

    def _damage_enemies(self, swing: dict) -> None:
        if not swing["is_active"]:
            return

        start_angle = swing["previous_angle"]
        end_angle = swing["current_angle"]
        start_extension = swing["previous_extension"]
        end_extension = swing["current_extension"]

        for enemy in self.enemy_group:
            if enemy.sprite_id in swing["hit_enemies"]:
                continue

            hit = False
            for arc_index in range(SWORD_ARC_SAMPLE_COUNT + 1):
                t_arc = arc_index / max(1, SWORD_ARC_SAMPLE_COUNT)
                angle = start_angle + (end_angle - start_angle) * t_arc
                extension = start_extension + (end_extension - start_extension) * t_arc
                _hilt, guard, tip = self._pose_points(angle, extension)
                for blade_index in range(1, SWORD_BLADE_SAMPLE_COUNT + 1):
                    t_blade = blade_index / SWORD_BLADE_SAMPLE_COUNT
                    point = guard.lerp(tip, t_blade)
                    if enemy.rect.collidepoint(point.x, point.y):
                        hit = True
                        break
                if hit:
                    break

            if not hit:
                continue

            is_crit = random.random() < self.owner.crit_chance
            damage = self._scaled_damage(self.base_damage) * (CRIT_MULTIPLIER if is_crit else 1.0)
            diff = self.owner.pos - enemy.pos
            hit_dir = diff.normalize() if diff.length_squared() > 0 else Vector2(1, 0)
            enemy.take_damage(
                damage,
                hit_direction=hit_dir,
                attacker=self.owner,
                knockback_force=self.knockback_force,
            )
            swing["hit_enemies"].add(enemy.sprite_id)

            if self.effect_group is not None:
                from src.entities.effects import DamageNumber, HitSpark

                DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                HitSpark(enemy.pos, SWORD_HIT_SPARK_COLOR, [self.effect_group])

    def on_owner_inactive(self) -> None:
        self.active_swings.clear()
        self._pending_followup = None

    def draw(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        blade_half_width = SWORD_BLADE_WIDTH / 2
        grip_half_width = SWORD_GRIP_WIDTH / 2
        guard_half_width = SWORD_GUARD_HALF_WIDTH
        guard_half_thickness = SWORD_GUARD_THICKNESS / 2

        def screen_space(point: Vector2) -> tuple[float, float]:
            return point.x - camera_offset.x, point.y - camera_offset.y

        for swing in self.active_swings:
            current_angle = swing["current_angle"]
            previous_angle = swing["previous_angle"]
            direction = Vector2(1, 0).rotate(current_angle)
            perpendicular = direction.rotate(90)
            hilt, grip_end, tip = self._pose_points(current_angle, swing["current_extension"])
            taper = grip_end + direction * (swing["current_extension"] * SWORD_TAPER_START)

            previous_hilt, _previous_guard, previous_tip = self._pose_points(previous_angle, swing["previous_extension"])
            pygame.draw.line(
                surface,
                SWORD_SWING_TRAIL_COLOR,
                screen_space(previous_tip),
                screen_space(tip),
                SWORD_SWING_TRAIL_WIDTH,
            )
            pygame.draw.line(
                surface,
                SWORD_SWING_TRAIL_COLOR,
                screen_space(previous_hilt),
                screen_space(hilt),
                1,
            )

            grip_points = [
                screen_space(hilt + perpendicular * grip_half_width),
                screen_space(hilt - perpendicular * grip_half_width),
                screen_space(grip_end - perpendicular * grip_half_width),
                screen_space(grip_end + perpendicular * grip_half_width),
            ]
            pygame.draw.polygon(surface, SWORD_GRIP_COLOR, grip_points)
            pygame.draw.polygon(surface, SWORD_OUTLINE_COLOR, grip_points, 1)

            pygame.draw.circle(surface, SWORD_GUARD_COLOR, screen_space(hilt), SWORD_POMMEL_RADIUS)
            pygame.draw.circle(surface, SWORD_OUTLINE_COLOR, screen_space(hilt), SWORD_POMMEL_RADIUS, 1)

            guard_points = [
                screen_space(grip_end + perpendicular * guard_half_width - direction * guard_half_thickness),
                screen_space(grip_end - perpendicular * guard_half_width - direction * guard_half_thickness),
                screen_space(grip_end - perpendicular * guard_half_width + direction * guard_half_thickness),
                screen_space(grip_end + perpendicular * guard_half_width + direction * guard_half_thickness),
            ]
            pygame.draw.polygon(surface, SWORD_GUARD_COLOR, guard_points)
            pygame.draw.polygon(surface, SWORD_OUTLINE_COLOR, guard_points, 1)

            blade_points = [
                screen_space(grip_end + perpendicular * blade_half_width),
                screen_space(taper + perpendicular * blade_half_width),
                screen_space(tip),
                screen_space(taper - perpendicular * blade_half_width),
                screen_space(grip_end - perpendicular * blade_half_width),
            ]
            pygame.draw.polygon(surface, SWORD_BLADE_COLOR, blade_points)
            pygame.draw.polygon(surface, SWORD_OUTLINE_COLOR, blade_points, 1)

            highlight_start = grip_end + direction * 2
            highlight_end = tip - direction * 5
            pygame.draw.line(
                surface,
                SWORD_HIGHLIGHT_COLOR,
                screen_space(highlight_start),
                screen_space(highlight_end),
                1,
            )
