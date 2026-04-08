import pygame
from pygame.math import Vector2
import random

from settings import (
    CRIT_MULTIPLIER,
    LIGHTNING_CHAIN_ARC_COLOR,
    LIGHTNING_CHAIN_ARC_JITTER,
    LIGHTNING_CHAIN_ARC_LIFETIME,
    LIGHTNING_CHAIN_ARC_MAX_SEGMENTS,
    LIGHTNING_CHAIN_ARC_MID_ALPHA,
    LIGHTNING_CHAIN_ARC_MID_COLOR,
    LIGHTNING_CHAIN_ARC_MID_WIDTH,
    LIGHTNING_CHAIN_ARC_MIN_SEGMENTS,
    LIGHTNING_CHAIN_ARC_OUTER_GLOW_ALPHA,
    LIGHTNING_CHAIN_ARC_OUTER_GLOW_COLOR,
    LIGHTNING_CHAIN_ARC_OUTER_GLOW_WIDTH,
    LIGHTNING_CHAIN_ARC_WIDTH,
    LIGHTNING_CHAIN_BASE_CHAIN_COUNT,
    LIGHTNING_CHAIN_BASE_COOLDOWN,
    LIGHTNING_CHAIN_BASE_DAMAGE,
    LIGHTNING_CHAIN_BASE_STUN_CHANCE,
    LIGHTNING_CHAIN_CHAIN_RANGE,
    LIGHTNING_CHAIN_HIT_SPARK_COLOR,
    LIGHTNING_CHAIN_HOP_DAMAGE_MULTIPLIER,
    LIGHTNING_CHAIN_IMPACT_ALPHA,
    LIGHTNING_CHAIN_IMPACT_COLOR,
    LIGHTNING_CHAIN_IMPACT_RADIUS,
    LIGHTNING_CHAIN_STUN_DURATION,
    LIGHTNING_CHAIN_TARGETING_RANGE,
    LIGHTNING_CHAIN_UPGRADE_LEVELS,
)
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

class LightningChain(BaseWeapon):
    name = "Lightning Chain"
    description = "Strikes the nearest enemy, then chains to nearby foes."
    base_damage = LIGHTNING_CHAIN_BASE_DAMAGE
    base_cooldown = LIGHTNING_CHAIN_BASE_COOLDOWN
    chain_count = LIGHTNING_CHAIN_BASE_CHAIN_COUNT
    chain_range = LIGHTNING_CHAIN_CHAIN_RANGE
    stun_chance = LIGHTNING_CHAIN_BASE_STUN_CHANCE
    stun_duration = LIGHTNING_CHAIN_STUN_DURATION
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in LIGHTNING_CHAIN_UPGRADE_LEVELS]

        # lightning_arcs: list of {"end": Vector2, "timer": float, "points": list[Vector2]}
        # Geometry frozen at fire time; timer counts down from ARC_LIFETIME then arc is removed.
        self.lightning_arcs = []
        self.stunned_enemies: dict[object, float] = {}

    def _build_arc_points(self, start: Vector2, end: Vector2) -> list[Vector2]:
        """Freeze the arc geometry once so draw() avoids per-frame random work."""
        direction_vector = end - start
        if direction_vector.length_squared() == 0:
            return [Vector2(start), Vector2(end)]

        direction = direction_vector.normalize()
        perpendicular = Vector2(-direction.y, direction.x)
        segment_length = direction_vector.length()
        points = [Vector2(start)]

        num_midpoints = random.randint(LIGHTNING_CHAIN_ARC_MIN_SEGMENTS, LIGHTNING_CHAIN_ARC_MAX_SEGMENTS)
        for i in range(1, num_midpoints):
            t = i / num_midpoints
            midpoint = start + direction * (t * segment_length)
            midpoint += perpendicular * random.randint(-LIGHTNING_CHAIN_ARC_JITTER, LIGHTNING_CHAIN_ARC_JITTER)
            points.append(midpoint)

        points.append(Vector2(end))
        return points

    def fire(self):
        """Strike the nearest enemy and chain to nearby foes."""
        # Find nearest enemy to owner
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = LIGHTNING_CHAIN_TARGETING_RANGE * LIGHTNING_CHAIN_TARGETING_RANGE

        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        if nearest_distance_sq > max_range_sq:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_CHAIN)

        # Build chain: start with nearest, find next closest enemy within chain_range
        # that hasn't been hit in this chain. Repeat up to chain_count times.
        chain = [nearest_enemy]
        enemies_hit = {nearest_enemy.sprite_id}

        chain_range_sq = self.chain_range * self.chain_range
        for _ in range(self.chain_count):
            closest_enemy = None
            closest_distance_sq = float("inf")

            for enemy in self.enemy_group:
                if enemy.sprite_id in enemies_hit:
                    continue

                distance_sq = (enemy.pos - chain[-1].pos).length_squared()
                if distance_sq <= chain_range_sq and distance_sq < closest_distance_sq:
                    closest_distance_sq = distance_sq
                    closest_enemy = enemy

            if closest_enemy:
                chain.append(closest_enemy)
                enemies_hit.add(closest_enemy.sprite_id)
            else:
                break

        # Damage each enemy in chain; diminish by hop multiplier and roll crit independently per target
        for i, enemy in enumerate(chain):
            # Diminish damage by 10% per hop, then roll crit independently per enemy
            damage_multiplier = LIGHTNING_CHAIN_HOP_DAMAGE_MULTIPLIER ** i
            is_crit = random.random() < self.owner.crit_chance
            damage = self.base_damage * damage_multiplier * self.owner.damage_multiplier * (self.owner.spell_damage_multiplier if self.IS_SPELL else 1.0) * (CRIT_MULTIPLIER if is_crit else 1.0)
            source_pos = self.owner.pos if i == 0 else chain[i - 1].pos
            diff = source_pos - enemy.pos
            hit_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
            enemy.take_damage(damage, hit_direction=hit_dir, attacker=self.owner)
            if self.effect_group is not None:
                from src.entities.effects import DamageNumber, HitSpark
                DamageNumber(enemy.pos - Vector2(0, 20), damage, [self.effect_group], is_crit=is_crit)
                HitSpark(enemy.pos, LIGHTNING_CHAIN_HIT_SPARK_COLOR, [self.effect_group])

            # Chance to stun: if random() < stun_chance: freeze enemy briefly
            if self.stun_chance > 0.0 and random.random() < self.stun_chance:
                enemy.freeze_timer = max(getattr(enemy, "freeze_timer", 0.0), self.stun_duration)
                if hasattr(enemy, "_refresh_speed"):
                    enemy._refresh_speed()
                self.stunned_enemies[enemy] = self.stun_duration

        # Store arc positions for drawing — first arc runs from player to initial target
        arc_start = Vector2(self.owner.pos)
        arc_end = Vector2(chain[0].pos)
        self.lightning_arcs.append({
            "end": arc_end,
            "timer": LIGHTNING_CHAIN_ARC_LIFETIME,
            "points": self._build_arc_points(arc_start, arc_end),
        })
        for i in range(len(chain) - 1):
            start = Vector2(chain[i].pos)
            end = Vector2(chain[i + 1].pos)
            self.lightning_arcs.append({
                "end": end,
                "timer": LIGHTNING_CHAIN_ARC_LIFETIME,
                "points": self._build_arc_points(start, end),
            })

    def update(self, dt):
        """Update the lightning chain effect."""
        super().update(dt)

        # Tick lightning arc timers, remove expired arcs
        i = 0
        while i < len(self.lightning_arcs):
            self.lightning_arcs[i]["timer"] -= dt
            if self.lightning_arcs[i]["timer"] <= 0:
                self.lightning_arcs.pop(i)
            else:
                i += 1

        # Tick stun timers only on currently stunned enemies.
        for enemy in list(self.stunned_enemies.keys()):
            remaining = self.stunned_enemies[enemy] - dt
            if remaining <= 0 or not enemy.alive():
                if enemy.alive() and hasattr(enemy, "_refresh_speed"):
                    enemy._refresh_speed()
                del self.stunned_enemies[enemy]
                continue

            self.stunned_enemies[enemy] = remaining
            enemy.freeze_timer = max(getattr(enemy, "freeze_timer", 0.0), remaining)

    def on_owner_inactive(self):
        self.lightning_arcs.clear()
        self.stunned_enemies.clear()

    def draw(self, surface, camera_offset):
        """Draw jagged lightning arcs with layered glow and per-node impact flashes."""
        if not self.lightning_arcs:
            return
        tmp = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for arc in self.lightning_arcs:
            fade = arc["timer"] / LIGHTNING_CHAIN_ARC_LIFETIME
            points = [
                (int(p.x - camera_offset.x), int(p.y - camera_offset.y))
                for p in arc["points"]
            ]
            if len(points) < 2:
                continue

            # Outer glow: wide electric-blue bloom
            ga = int(LIGHTNING_CHAIN_ARC_OUTER_GLOW_ALPHA * fade)
            pygame.draw.lines(
                tmp, (*LIGHTNING_CHAIN_ARC_OUTER_GLOW_COLOR, ga),
                False, points, LIGHTNING_CHAIN_ARC_OUTER_GLOW_WIDTH,
            )
            # Mid layer: pale blue-white
            ma = int(LIGHTNING_CHAIN_ARC_MID_ALPHA * fade)
            pygame.draw.lines(
                tmp, (*LIGHTNING_CHAIN_ARC_MID_COLOR, ma),
                False, points, LIGHTNING_CHAIN_ARC_MID_WIDTH,
            )
            # Core: original yellow-white, fades with arc timer
            ca = int(255 * fade)
            pygame.draw.lines(
                tmp, (*LIGHTNING_CHAIN_ARC_COLOR, ca),
                False, points, LIGHTNING_CHAIN_ARC_WIDTH,
            )

            # Impact flash at chain node (arc end-point)
            ia = int(LIGHTNING_CHAIN_IMPACT_ALPHA * fade)
            end = arc["end"]
            pygame.draw.circle(
                tmp, (*LIGHTNING_CHAIN_IMPACT_COLOR, ia),
                (int(end.x - camera_offset.x), int(end.y - camera_offset.y)),
                LIGHTNING_CHAIN_IMPACT_RADIUS,
            )
        surface.blit(tmp, (0, 0))
