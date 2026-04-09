import math
import random

import pygame
from pygame.math import Vector2

from settings import (
    CHAIN_FLAIL_BASE_COOLDOWN,
    CHAIN_FLAIL_BASE_DAMAGE,
    CHAIN_FLAIL_CHAIN_COLOR,
    CHAIN_FLAIL_CHAIN_LENGTH,
    CHAIN_FLAIL_CHAIN_SAMPLE_COUNT,
    CHAIN_FLAIL_CHAIN_WIDTH,
    CHAIN_FLAIL_EXTEND_DURATION,
    CHAIN_FLAIL_HEAD_COLOR,
    CHAIN_FLAIL_HEAD_HIGHLIGHT_COLOR,
    CHAIN_FLAIL_HEAD_OUTLINE_COLOR,
    CHAIN_FLAIL_HEAD_RADIUS,
    CHAIN_FLAIL_HIT_SPARK_COLOR,
    CHAIN_FLAIL_KNOCKBACK_FORCE,
    CHAIN_FLAIL_RETRACT_DURATION,
    CHAIN_FLAIL_SWEEP_ANGLE,
    CHAIN_FLAIL_SWEEP_DURATION,
    CHAIN_FLAIL_UPGRADE_LEVELS,
    CRIT_MULTIPLIER,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class ChainFlail(BaseWeapon):
    name = "Chain Flail"
    description = "Extends a tethered flail, sweeps through an arc, then retracts."
    base_damage = CHAIN_FLAIL_BASE_DAMAGE
    base_cooldown = CHAIN_FLAIL_BASE_COOLDOWN
    chain_length = CHAIN_FLAIL_CHAIN_LENGTH
    head_radius = CHAIN_FLAIL_HEAD_RADIUS
    sweep_angle = CHAIN_FLAIL_SWEEP_ANGLE
    extend_duration = CHAIN_FLAIL_EXTEND_DURATION
    sweep_duration = CHAIN_FLAIL_SWEEP_DURATION
    retract_duration = CHAIN_FLAIL_RETRACT_DURATION
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in CHAIN_FLAIL_UPGRADE_LEVELS]
        self.active_swings: list[dict] = []

    @property
    def effective_chain_length(self) -> float:
        return self.chain_length * self.owner.area_size_multiplier

    def _get_target_direction(self) -> Vector2:
        nearest_enemy = None
        nearest_distance_sq = float("inf")

        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if nearest_enemy is not None:
            target_direction = nearest_enemy.pos - self.owner.pos
            if target_direction.length_squared() > 0:
                return target_direction.normalize()

        if self.owner.facing.length_squared() > 0:
            return self.owner.facing.normalize()
        return Vector2(1, 0)

    def fire(self) -> None:
        if self.active_swings:
            return

        facing = self._get_target_direction()
        facing_angle = math.degrees(math.atan2(facing.y, facing.x))
        half_sweep = self.sweep_angle / 2
        AudioManager.instance().play_sfx(AudioManager.WEAPON_CHAIN_FLAIL)
        self.active_swings.append({
            "timer": 0.0,
            "total_duration": self.extend_duration + self.sweep_duration + self.retract_duration,
            "start_angle": facing_angle - half_sweep,
            "end_angle": facing_angle + half_sweep,
            "hit_enemies": set(),
            "head_pos": Vector2(self.owner.pos),
            "previous_head_pos": Vector2(self.owner.pos),
        })

    def update(self, dt: float) -> None:
        self.cooldown_timer -= dt
        if self.cooldown_timer <= 0.0 and not self.active_swings:
            self.fire()
            self.cooldown_timer = self._get_effective_cooldown()

        i = 0
        while i < len(self.active_swings):
            swing = self.active_swings[i]
            swing["timer"] += dt
            swing["previous_head_pos"] = Vector2(swing["head_pos"])

            phase_time = swing["timer"]
            extend_end = self.extend_duration
            sweep_end = extend_end + self.sweep_duration
            total_duration = swing["total_duration"]

            if phase_time < extend_end:
                progress = phase_time / self.extend_duration if self.extend_duration > 0 else 1.0
                radius = self.effective_chain_length * progress
                angle = swing["start_angle"]
            elif phase_time < sweep_end:
                progress = (phase_time - extend_end) / self.sweep_duration if self.sweep_duration > 0 else 1.0
                radius = self.effective_chain_length
                angle = swing["start_angle"] + (swing["end_angle"] - swing["start_angle"]) * progress
            else:
                progress = (phase_time - sweep_end) / self.retract_duration if self.retract_duration > 0 else 1.0
                radius = self.effective_chain_length * max(0.0, 1.0 - progress)
                angle = swing["end_angle"]

            direction = Vector2(1, 0).rotate(angle)
            swing["head_pos"] = self.owner.pos + direction * radius
            self._damage_enemies(swing)

            if phase_time >= total_duration:
                self.active_swings.pop(i)
            else:
                i += 1

    def _damage_enemies(self, swing: dict) -> None:
        head_pos = swing["head_pos"]
        previous_head_pos = swing["previous_head_pos"]
        head_radius_sq = self.head_radius * self.head_radius

        for enemy in self.enemy_group:
            if enemy.sprite_id in swing["hit_enemies"]:
                continue

            hit = False
            if (enemy.pos - head_pos).length_squared() <= head_radius_sq:
                hit = True
            else:
                for sample_index in range(1, CHAIN_FLAIL_CHAIN_SAMPLE_COUNT + 1):
                    t = sample_index / CHAIN_FLAIL_CHAIN_SAMPLE_COUNT
                    sample_pos = self.owner.pos.lerp(head_pos, t)
                    if enemy.rect.collidepoint(sample_pos.x, sample_pos.y):
                        hit = True
                        break
                if not hit:
                    for sample_index in range(1, CHAIN_FLAIL_CHAIN_SAMPLE_COUNT + 1):
                        t = sample_index / CHAIN_FLAIL_CHAIN_SAMPLE_COUNT
                        sample_pos = previous_head_pos.lerp(head_pos, t)
                        if enemy.rect.collidepoint(sample_pos.x, sample_pos.y):
                            hit = True
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
                knockback_force=CHAIN_FLAIL_KNOCKBACK_FORCE,
            )
            swing["hit_enemies"].add(enemy.sprite_id)

            if self.effect_group is not None:
                from src.entities.effects import DamageNumber, HitSpark
                DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                HitSpark(enemy.pos, CHAIN_FLAIL_HIT_SPARK_COLOR, [self.effect_group])

    def on_owner_inactive(self) -> None:
        self.active_swings.clear()

    def draw(self, surface, camera_offset) -> None:
        for swing in self.active_swings:
            head_pos = swing["head_pos"] - camera_offset
            owner_pos = self.owner.pos - camera_offset
            pygame.draw.line(
                surface,
                CHAIN_FLAIL_CHAIN_COLOR,
                (int(owner_pos.x), int(owner_pos.y)),
                (int(head_pos.x), int(head_pos.y)),
                CHAIN_FLAIL_CHAIN_WIDTH,
            )
            pygame.draw.circle(
                surface,
                CHAIN_FLAIL_HEAD_COLOR,
                (int(head_pos.x), int(head_pos.y)),
                self.head_radius,
            )
            pygame.draw.circle(
                surface,
                CHAIN_FLAIL_HEAD_OUTLINE_COLOR,
                (int(head_pos.x), int(head_pos.y)),
                self.head_radius,
                2,
            )
            highlight = Vector2(-self.head_radius * 0.35, -self.head_radius * 0.35)
            pygame.draw.circle(
                surface,
                CHAIN_FLAIL_HEAD_HIGHLIGHT_COLOR,
                (int(head_pos.x + highlight.x), int(head_pos.y + highlight.y)),
                max(3, self.head_radius // 3),
            )
