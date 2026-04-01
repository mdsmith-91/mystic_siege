import pygame
from src.weapons.base_weapon import BaseWeapon
from pygame.math import Vector2
import random
from src.utils.audio_manager import AudioManager
from settings import LIGHTNING_CHAIN_RANGE

class LightningChain(BaseWeapon):
    name = "Lightning Chain"
    description = "Strikes the nearest enemy, then chains to nearby foes."
    base_damage = 35.0
    base_cooldown = 1.8
    chain_count = 3    # max enemies to chain to after initial target
    chain_range = 150  # max distance between chain jumps
    stun_chance = 0.0  # 0.0-1.0
    stun_duration = 0.5

    def __init__(self, owner, projectile_group, enemy_group):
        super().__init__(owner, projectile_group, enemy_group)

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"base_damage": 15},  # L2: +15 damage
            {"chain_count": 2},   # L3: chains to 5 enemies
            {"chain_range": 50},  # L4: +50 chain range
            {"chain_count": 1, "stun_chance": 0.25}  # L5: 6 chains, stun added
        ]

        # lightning_arcs: list — each arc is {"start": Vector2, "end": Vector2, "timer": float}
        # Timer counts down from 0.12s — arcs are drawn for that long then removed.
        self.lightning_arcs = []

    def fire(self):
        """Strike the nearest enemy and chain to nearby foes."""
        # Find nearest enemy to owner
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance = float('inf')

        for enemy in self.enemy_group:
            distance = (enemy.pos - self.owner.pos).length()
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        if nearest_distance > LIGHTNING_CHAIN_RANGE:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_CHAIN)

        # Build chain: start with nearest, find next closest enemy within chain_range
        # that hasn't been hit in this chain. Repeat up to chain_count times.
        chain = [nearest_enemy]
        enemies_hit = {nearest_enemy.sprite_id}

        for _ in range(self.chain_count):
            closest_enemy = None
            closest_distance = float('inf')

            for enemy in self.enemy_group:
                if enemy.sprite_id in enemies_hit:
                    continue

                distance = (enemy.pos - chain[-1].pos).length()
                if distance <= self.chain_range and distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy

            if closest_enemy:
                chain.append(closest_enemy)
                enemies_hit.add(closest_enemy.sprite_id)
            else:
                break

        # For each enemy in chain: deal base_damage * owner.damage_multiplier (diminish by 10% per hop)
        # Chance to stun: if random() < stun_chance: freeze enemy briefly
        for i, enemy in enumerate(chain):
            # Diminish damage by 10% per hop
            damage_multiplier = 0.9 ** i
            damage = self.base_damage * damage_multiplier * self.owner.damage_multiplier
            enemy.take_damage(damage)

            # Chance to stun: if random() < stun_chance: freeze enemy briefly
            if random.random() < self.stun_chance:
                # Only save max_speed if not already frozen (speed > 0)
                if enemy.speed > 0:
                    enemy.max_speed = enemy.speed
                enemy.speed = 0
                enemy.freeze_timer = self.stun_duration

        # Store arc positions for drawing — first arc runs from player to initial target
        self.lightning_arcs.append({
            "start": Vector2(self.owner.pos),
            "end": Vector2(chain[0].pos),
            "timer": 0.12
        })
        for i in range(len(chain) - 1):
            start = chain[i].pos
            end = chain[i + 1].pos
            self.lightning_arcs.append({
                "start": start,
                "end": end,
                "timer": 0.12
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

        # Tick stun timers on all enemies and restore speed when stun expires
        for enemy in self.enemy_group:
            if getattr(enemy, 'freeze_timer', 0) > 0:
                enemy.freeze_timer -= dt
                if enemy.freeze_timer <= 0:
                    enemy.freeze_timer = 0
                    if hasattr(enemy, 'max_speed'):
                        enemy.speed = enemy.max_speed

    def draw(self, surface, camera_offset):
        """Draw jagged lightning arcs."""
        for arc in self.lightning_arcs:
            start = arc["start"]
            end = arc["end"]

            # Draw jagged yellow/white lines (zigzag between start and end with 3-4 midpoints
            # randomly offset ±15px perpendicular)

            # Calculate direction and perpendicular
            direction_vector = end - start
            # Check if the vector is zero-length to avoid normalization error
            if direction_vector.length() == 0:
                continue

            direction = direction_vector.normalize()
            perpendicular = Vector2(-direction.y, direction.x)

            # Create points for the arc
            points = [start]

            # Add 3-4 midpoints with random offsets
            num_midpoints = 3 + random.randint(0, 2)  # 3-5 midpoints
            for i in range(1, num_midpoints):
                t = i / num_midpoints
                midpoint = start + direction * (t * (end - start).length())

                # Add random offset perpendicular to the direction
                offset = perpendicular * (random.randint(-15, 15))
                midpoint += offset

                points.append(midpoint)

            points.append(end)

            # Draw the arc
            pygame.draw.lines(surface, (255, 255, 200), False,  # Yellow/white color
                            [(p.x - camera_offset.x, p.y - camera_offset.y) for p in points], 2)