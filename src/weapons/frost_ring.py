import math
import pygame
import random
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    FROST_RING_BASE_COOLDOWN,
    FROST_RING_BASE_DAMAGE,
    FROST_RING_COLOR,
    FROST_RING_FREEZE_DURATION,
    FROST_RING_HALF_WIDTH,
    FROST_RING_HIT_SPARK_COLOR,
    FROST_RING_INNER_GLOW_COLOR,
    FROST_RING_MAX_RADIUS,
    FROST_RING_MOTE_COLOR,
    FROST_RING_MOTE_COUNT,
    FROST_RING_MOTE_SPEED_VARIANCE,
    FROST_RING_OUTER_BLOOM_COLOR,
    FROST_RING_SHARD_COLOR,
    FROST_RING_SHARD_COUNT,
    FROST_RING_SHARD_LENGTH,
    FROST_RING_SPEED,
    FROST_RING_UPGRADE_LEVELS,
)
from src.entities.effects import DamageNumber, HitSpark
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

_TWO_PI = math.pi * 2
_SHARD_STEP = _TWO_PI / FROST_RING_SHARD_COUNT
_BLOOM_WIDTH = FROST_RING_HALF_WIDTH * 2 + 4


class FrostRing(BaseWeapon):
    name = "Frost Ring"
    description = "Expands a freezing ring outward, temporarily immobilizing enemies."
    base_damage = FROST_RING_BASE_DAMAGE
    base_cooldown = FROST_RING_BASE_COOLDOWN
    ring_speed = FROST_RING_SPEED
    max_radius = FROST_RING_MAX_RADIUS
    freeze_duration = FROST_RING_FREEZE_DURATION
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in FROST_RING_UPGRADE_LEVELS]

        # Track frozen enemies by live enemy reference to avoid repeated group scans.
        self.frozen_enemies: dict[object, float] = {}

        # Active rings list: each ring is {radius, damage_done, center, motes, shard_offset}
        self.rings = []

    @property
    def effective_max_radius(self) -> float:
        return self.max_radius * self.owner.area_size_multiplier

    def _spawn_motes(self) -> list[dict]:
        """Build the initial ice mote particle list for a new ring cast."""
        motes = []
        variance = FROST_RING_MOTE_SPEED_VARIANCE
        step = _TWO_PI / FROST_RING_MOTE_COUNT
        for i in range(FROST_RING_MOTE_COUNT):
            # Spread evenly with a small random jitter so motes don't clump
            angle = i * step + random.uniform(-step * 0.4, step * 0.4)
            speed = self.ring_speed + random.uniform(-variance, variance)
            motes.append({"angle": angle, "r": 0.0, "speed": speed})
        return motes

    def fire(self):
        """Emit a new frost ring."""
        AudioManager.instance().play_sfx(AudioManager.WEAPON_FROST)
        ring = {
            "radius": 0,
            "damage_done": set(),
            "center": self.owner.pos.copy(),
            "motes": self._spawn_motes(),
            "shard_offset": random.uniform(0, _SHARD_STEP),
        }
        self.rings.append(ring)

    def update(self, dt):
        """Update all active rings and frozen enemies."""
        super().update(dt)

        # Tick freeze timers, restore speed when timer hits 0
        for enemy in list(self.frozen_enemies.keys()):
            remaining = self.frozen_enemies[enemy] - dt
            if remaining <= 0 or not enemy.alive():
                if enemy.alive() and hasattr(enemy, "_refresh_speed"):
                    enemy._refresh_speed()
                del self.frozen_enemies[enemy]
                continue

            self.frozen_enemies[enemy] = remaining

        # Expand all rings and check for collisions
        i = 0
        while i < len(self.rings):
            ring = self.rings[i]

            # Expand the ring and its mote particles
            ring["radius"] += self.ring_speed * dt
            for p in ring["motes"]:
                p["r"] += p["speed"] * dt

            inner_radius = max(0, ring["radius"] - FROST_RING_HALF_WIDTH)
            outer_radius = ring["radius"] + FROST_RING_HALF_WIDTH
            inner_radius_sq = inner_radius * inner_radius
            outer_radius_sq = outer_radius * outer_radius

            # Check each ring against enemies (circle vs rect)
            for enemy in self.enemy_group:
                distance_sq = (enemy.pos - ring["center"]).length_squared()

                if inner_radius_sq <= distance_sq <= outer_radius_sq:
                    if enemy.sprite_id not in ring["damage_done"]:
                        is_crit = random.random() < self.owner.crit_chance
                        damage = self._scaled_damage(self.base_damage) * (CRIT_MULTIPLIER if is_crit else 1.0)
                        diff = ring["center"] - enemy.pos
                        hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        enemy.take_damage(damage, hit_direction=hit_dir, attacker=self.owner)
                        if self.effect_group is not None:
                            DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                            HitSpark(enemy.pos, FROST_RING_HIT_SPARK_COLOR, [self.effect_group])

                        # Freeze enemy through the shared enemy status timer so
                        # lunge/boss movement modifiers can coexist safely.
                        self.frozen_enemies[enemy] = self.freeze_duration
                        enemy.freeze_timer = max(getattr(enemy, "freeze_timer", 0.0), self.freeze_duration)
                        if hasattr(enemy, "_refresh_speed"):
                            enemy._refresh_speed()

                        ring["damage_done"].add(enemy.sprite_id)

            if ring["radius"] > self.effective_max_radius:
                self.rings.pop(i)
            else:
                i += 1

    def on_owner_inactive(self):
        self.frozen_enemies.clear()
        self.rings.clear()

    def draw(self, surface, camera_offset):
        """Draw the frost rings with layered glow, crystal shards, and ice motes."""
        if not self.rings:
            return

        # One SRCALPHA surface shared across all active rings this frame
        tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Fade constants depend on the current (possibly upgraded) max_radius
        max_r = self.effective_max_radius
        mote_fade_start = max_r * 0.7
        mote_fade_range = max_r * 0.3

        for ring in self.rings:
            radius = int(ring["radius"])
            progress = ring["radius"] / max_r if max_r > 0 else 1.0

            cx = int(ring["center"].x - camera_offset.x)
            cy = int(ring["center"].y - camera_offset.y)
            center = (cx, cy)

            # --- Layer 1: inner cold burst (fades out in first 40% of expansion) ---
            if progress < 0.4:
                flash_alpha = int(180 * (1.0 - progress / 0.4))
                flash_radius = max(4, radius // 2)
                pygame.draw.circle(tmp, (*FROST_RING_INNER_GLOW_COLOR, flash_alpha), center, flash_radius)

            # --- Layer 2: outer frost band (soft cold-blue halo beyond the primary ring) ---
            bloom_radius = radius + FROST_RING_HALF_WIDTH + 2
            pygame.draw.circle(tmp, (*FROST_RING_OUTER_BLOOM_COLOR, 50), center, bloom_radius, _BLOOM_WIDTH)

            # --- Layer 3: primary ring — translucent outer band + bright inner core ---
            if radius > 0:
                pygame.draw.circle(tmp, (*FROST_RING_COLOR, 160), center, radius, FROST_RING_HALF_WIDTH * 2 + 2)
                pygame.draw.circle(tmp, (*FROST_RING_COLOR, 255), center, radius, FROST_RING_HALF_WIDTH)

            # --- Layer 4: ice crystal shards radiating outward from ring edge ---
            if radius > 0:
                for k in range(FROST_RING_SHARD_COUNT):
                    angle = ring["shard_offset"] + k * _SHARD_STEP
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    x0 = cx + dx * radius
                    y0 = cy + dy * radius
                    x1 = cx + dx * (radius + FROST_RING_SHARD_LENGTH)
                    y1 = cy + dy * (radius + FROST_RING_SHARD_LENGTH)
                    pygame.draw.line(tmp, (*FROST_RING_SHARD_COLOR, 200), (int(x0), int(y0)), (int(x1), int(y1)), 1)

            # --- Layer 5: ice mote particles riding along the expanding ring edge ---
            for p in ring["motes"]:
                pr = p["r"]
                if pr > max_r:
                    continue
                mote_alpha = 255 if pr < mote_fade_start else int(255 * (1.0 - (pr - mote_fade_start) / mote_fade_range))
                mote_alpha = max(0, mote_alpha)
                mx = int(cx + math.cos(p["angle"]) * pr)
                my = int(cy + math.sin(p["angle"]) * pr)
                pygame.draw.circle(tmp, (*FROST_RING_MOTE_COLOR, mote_alpha), (mx, my), 2)

        surface.blit(tmp, (0, 0))
