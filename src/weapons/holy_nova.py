import math
import pygame
import random
from pygame.math import Vector2

from settings import (
    CRIT_MULTIPLIER,
    HOLY_NOVA_BASE_COOLDOWN,
    HOLY_NOVA_BASE_DAMAGE,
    HOLY_NOVA_BASE_RADIUS,
    HOLY_NOVA_CONSECRATE_COLOR,
    HOLY_NOVA_CONSECRATE_DAMAGE,
    HOLY_NOVA_CONSECRATE_DURATION,
    HOLY_NOVA_CONSECRATE_TICK,
    HOLY_NOVA_EXPAND_SPEED,
    HOLY_NOVA_FLARE_COLOR,
    HOLY_NOVA_FLARE_COUNT,
    HOLY_NOVA_FLARE_LENGTH,
    HOLY_NOVA_HIT_SPARK_COLOR,
    HOLY_NOVA_INNER_GLOW_COLOR,
    HOLY_NOVA_OUTER_BLOOM_COLOR,
    HOLY_NOVA_PARTICLE_SPEED_VARIANCE,
    HOLY_NOVA_RING_COLOR,
    HOLY_NOVA_RING_WIDTH,
    HOLY_NOVA_SPARK_COLOR,
    HOLY_NOVA_SPARK_COUNT,
    HOLY_NOVA_UPGRADE_LEVELS,
)
from src.entities.effects import DamageNumber, HitSpark
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

_TWO_PI = math.pi * 2


class HolyNova(BaseWeapon):
    name = "Holy Nova"
    description = "Emits an expanding ring of holy light, damaging all enemies it touches."
    base_damage = HOLY_NOVA_BASE_DAMAGE
    base_cooldown = HOLY_NOVA_BASE_COOLDOWN
    base_radius = HOLY_NOVA_BASE_RADIUS
    expand_speed = HOLY_NOVA_EXPAND_SPEED
    ring_width = HOLY_NOVA_RING_WIDTH
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in HOLY_NOVA_UPGRADE_LEVELS]

        # Keep a list of active rings; each ring carries its own particle list
        self.rings = []
        # Consecration zones: each dict holds center, radius, remaining, tick_timer
        self.consecrate_zones: list[dict] = []
        # Stored as int so the generic upgrade() += delta path works; truthy at L5.
        self.consecrate = 0

    def _spawn_particles(self):
        """Build the initial spark particle list for a new ring cast."""
        particles = []
        variance = HOLY_NOVA_PARTICLE_SPEED_VARIANCE
        for _ in range(HOLY_NOVA_SPARK_COUNT):
            angle = random.random() * _TWO_PI
            speed = self.expand_speed + random.uniform(-variance, variance)
            particles.append({"angle": angle, "r": 0.0, "speed": speed})
        return particles

    @property
    def effective_base_radius(self) -> float:
        return self.base_radius * self.owner.area_size_multiplier

    def fire(self):
        """Emit a new ring of holy light."""
        AudioManager.instance().play_sfx(AudioManager.WEAPON_NOVA)
        # Random flare offset per cast so flares don't always align to the same angles
        flare_segment = _TWO_PI / HOLY_NOVA_FLARE_COUNT
        ring = {
            "radius": 0,
            "max_radius": self.effective_base_radius,
            "damage": self._scaled_damage(self.base_damage),
            "enemies_hit": set(),
            "particles": self._spawn_particles(),
            "flare_offset": random.uniform(0, flare_segment),
        }
        self.rings.append(ring)

    def update(self, dt):
        """Update all active rings."""
        super().update(dt)

        self._tick_zones(dt)

        i = 0
        while i < len(self.rings):
            ring = self.rings[i]

            # Expand the ring and its spark particles
            ring["radius"] += self.expand_speed * dt
            for p in ring["particles"]:
                p["r"] += p["speed"] * dt

            inner_radius = max(0, ring["radius"] - self.ring_width)
            outer_radius = ring["radius"] + self.ring_width
            inner_radius_sq = inner_radius * inner_radius
            outer_radius_sq = outer_radius * outer_radius

            for enemy in self.enemy_group:
                distance_sq = (enemy.pos - self.owner.pos).length_squared()
                if inner_radius_sq <= distance_sq <= outer_radius_sq:
                    if enemy.sprite_id not in ring["enemies_hit"]:
                        is_crit = random.random() < self.owner.crit_chance
                        damage = ring["damage"] * (CRIT_MULTIPLIER if is_crit else 1.0)
                        diff = self.owner.pos - enemy.pos
                        hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        enemy.take_damage(damage, hit_direction=hit_dir, attacker=self.owner)
                        ring["enemies_hit"].add(enemy.sprite_id)
                        if self.effect_group is not None:
                            DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                            HitSpark(enemy.pos, HOLY_NOVA_HIT_SPARK_COLOR, [self.effect_group])

            if ring["radius"] > ring["max_radius"]:
                # Consecration: leave a persistent damage zone when the ring expires.
                if self.consecrate:
                    self.consecrate_zones.append({
                        "center": ring["center"].copy(),
                        "radius": ring["max_radius"],
                        "remaining": HOLY_NOVA_CONSECRATE_DURATION,
                        "tick_timer": 0.0,
                    })
                self.rings.pop(i)
            else:
                i += 1

    def _tick_zones(self, dt: float) -> None:
        zone_damage = self._scaled_damage(HOLY_NOVA_CONSECRATE_DAMAGE)
        i = 0
        while i < len(self.consecrate_zones):
            zone = self.consecrate_zones[i]
            zone["remaining"] -= dt
            zone["tick_timer"] -= dt
            if zone["remaining"] <= 0:
                self.consecrate_zones.pop(i)
                continue
            if zone["tick_timer"] <= 0:
                zone["tick_timer"] = HOLY_NOVA_CONSECRATE_TICK
                center = zone["center"]
                radius_sq = zone["radius"] * zone["radius"]
                for enemy in self.enemy_group:
                    if enemy.alive() and (enemy.pos - center).length_squared() <= radius_sq:
                        diff = center - enemy.pos
                        hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        enemy.take_damage(zone_damage, hit_direction=hit_dir, attacker=self.owner)
            i += 1

    def on_owner_inactive(self):
        self.rings.clear()
        self.consecrate_zones.clear()

    def draw_under(self, surface: pygame.Surface, camera_offset: Vector2) -> None:
        """Draw persistent consecration zones beneath all sprites."""
        if not self.consecrate_zones:
            return
        tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for zone in self.consecrate_zones:
            cx = int(zone["center"].x - camera_offset.x)
            cy = int(zone["center"].y - camera_offset.y)
            progress = zone["remaining"] / HOLY_NOVA_CONSECRATE_DURATION
            alpha = int(100 * progress)
            pygame.draw.circle(tmp, (*HOLY_NOVA_CONSECRATE_COLOR, alpha), (cx, cy), int(zone["radius"]))
            pygame.draw.circle(tmp, (*HOLY_NOVA_CONSECRATE_COLOR, min(255, alpha + 60)), (cx, cy), int(zone["radius"]), 3)
        surface.blit(tmp, (0, 0))

    def draw(self, surface, camera_offset):
        """Draw the expanding holy rings with layered glow, flares, and sparks."""
        if not self.rings:
            return

        # One SRCALPHA surface shared across all active rings this frame
        tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        cx = int(self.owner.pos.x - camera_offset.x)
        cy = int(self.owner.pos.y - camera_offset.y)
        center = (cx, cy)

        for ring in self.rings:
            radius = int(ring["radius"])
            max_r = ring["max_radius"]
            progress = ring["radius"] / max_r if max_r > 0 else 1.0

            # --- Layer 1: inner light flash (fades out in first 50% of expansion) ---
            if progress < 0.5:
                flash_alpha = int(220 * (1.0 - progress * 2.0))
                flash_radius = max(4, int(radius * 0.6))
                glow_color = (*HOLY_NOVA_INNER_GLOW_COLOR, flash_alpha)
                pygame.draw.circle(tmp, glow_color, center, flash_radius)

            # --- Layer 2: outer bloom ring (soft halo just beyond the primary ring) ---
            bloom_radius = radius + self.ring_width + 3
            bloom_color = (*HOLY_NOVA_OUTER_BLOOM_COLOR, 60)
            pygame.draw.circle(tmp, bloom_color, center, bloom_radius, self.ring_width + 4)

            # --- Layer 3: primary ring ---
            if radius > 0:
                ring_color = (*HOLY_NOVA_RING_COLOR, 255)
                pygame.draw.circle(tmp, ring_color, center, radius, self.ring_width)

            # --- Layer 4: flare spikes radiating outward from ring edge ---
            if radius > 0:
                flare_color = (*HOLY_NOVA_FLARE_COLOR, 200)
                step = _TWO_PI / HOLY_NOVA_FLARE_COUNT
                for k in range(HOLY_NOVA_FLARE_COUNT):
                    angle = ring["flare_offset"] + k * step
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    x0 = cx + dx * radius
                    y0 = cy + dy * radius
                    x1 = cx + dx * (radius + HOLY_NOVA_FLARE_LENGTH)
                    y1 = cy + dy * (radius + HOLY_NOVA_FLARE_LENGTH)
                    pygame.draw.line(tmp, flare_color, (int(x0), int(y0)), (int(x1), int(y1)), 2)

            # --- Layer 5: spark particles riding along the expanding ring edge ---
            # Fade threshold is constant per ring — hoist out of the particle loop
            fade_start = max_r * 0.7
            fade_range = max_r - fade_start  # = max_r * 0.3
            for p in ring["particles"]:
                pr = p["r"]
                if pr > max_r:
                    continue
                spark_alpha = 255 if pr < fade_start else int(255 * (1.0 - (pr - fade_start) / fade_range))
                spark_alpha = max(0, spark_alpha)
                spark_color = (*HOLY_NOVA_SPARK_COLOR, spark_alpha)
                sx = int(cx + math.cos(p["angle"]) * pr)
                sy = int(cy + math.sin(p["angle"]) * pr)
                pygame.draw.circle(tmp, spark_color, (sx, sy), 2)

        surface.blit(tmp, (0, 0))
