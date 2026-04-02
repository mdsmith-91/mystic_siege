import pygame
from src.weapons.base_weapon import BaseWeapon
from src.entities.projectile import Projectile
from pygame.math import Vector2
from settings import ARCANE_BOLT_RANGE, ARCANE_BOLT_SPREAD, ARCANE_BOLT_STAGGER
from src.utils.audio_manager import AudioManager

class ArcaneBolt(BaseWeapon):
    name = "Arcane Bolt"
    description = "Fires homing bolts at the nearest enemy."
    base_damage = 20.0
    base_cooldown = 1.2
    bolt_count = 1
    homing = True
    projectile_color = (160, 80, 255)

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)

        self.pierce = 0

        # Bolts queued to fire after a short stagger delay
        # Each entry: {"delay": float, "direction": Vector2, "target": enemy}
        self.pending_bolts: list[dict] = []

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"base_damage": 10},           # L2: +10 damage
            {"bolt_count": 1},             # L3: fire 2 bolts (spread slightly)
            {"pierce": 1},                 # L4: bolts pierce 1 enemy
            {"bolt_count": 1, "base_damage": 15}  # L5: 3 bolts, more damage
        ]

    def _spawn_bolt(self, direction: Vector2, target) -> None:
        """Spawn a single projectile in the given direction."""
        damage = self.base_damage * self.owner.damage_multiplier
        Projectile(
            pos=self.owner.pos,
            direction=direction,
            speed=400,
            damage=damage,
            groups=self.projectile_group,
            enemy_group_ref=self.enemy_group,
            pierce=self.pierce,
            homing=self.homing,
            color=self.projectile_color,
            target_enemy=target
        )

    def fire(self):
        """Fire homing bolts at the nearest enemy."""
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance = float('inf')

        for enemy in self.enemy_group:
            distance = (enemy.pos - self.owner.pos).length()
            if distance < nearest_distance and distance <= ARCANE_BOLT_RANGE:
                nearest_distance = distance
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_ARCANE)

        base_direction = (nearest_enemy.pos - self.owner.pos).normalize()

        for i in range(self.bolt_count):
            direction = base_direction
            if self.bolt_count > 1:
                angle_offset = (i - (self.bolt_count - 1) / 2) * ARCANE_BOLT_SPREAD
                direction = base_direction.rotate(angle_offset)

            delay = i * ARCANE_BOLT_STAGGER

            if delay == 0:
                self._spawn_bolt(direction, nearest_enemy)
            else:
                self.pending_bolts.append({
                    "delay": delay,
                    "direction": direction,
                    "target": nearest_enemy
                })

    def update(self, dt: float):
        """Update cooldown and fire any staggered pending bolts."""
        super().update(dt)

        i = 0
        while i < len(self.pending_bolts):
            bolt = self.pending_bolts[i]
            bolt["delay"] -= dt
            if bolt["delay"] <= 0:
                self._spawn_bolt(bolt["direction"], bolt["target"])
                self.pending_bolts.pop(i)
            else:
                i += 1
