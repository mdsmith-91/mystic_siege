import pygame
from src.weapons.base_weapon import BaseWeapon
from src.entities.projectile import Projectile
from pygame.math import Vector2

class ArcaneBolt(BaseWeapon):
    name = "Arcane Bolt"
    description = "Fires homing bolts at the nearest enemy."
    base_damage = 20.0
    base_cooldown = 1.2
    bolt_count = 1
    homing = True
    projectile_color = (160, 80, 255)

    def __init__(self, owner, projectile_group, enemy_group):
        super().__init__(owner, projectile_group, enemy_group)

        self.pierce = 0

        # Define upgrade levels
        self.upgrade_levels = [
            {},  # Level 1 (no upgrade)
            {"base_damage": 10},           # L2: +10 damage
            {"bolt_count": 1},             # L3: fire 2 bolts (spread slightly)
            {"pierce": 1},                 # L4: bolts pierce 1 enemy
            {"bolt_count": 1, "base_damage": 15}  # L5: 3 bolts, more damage
        ]

    def fire(self):
        """Fire homing bolts at the nearest enemy."""
        # Find nearest enemy in enemy_group
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

        # Spawn bolt_count Projectiles at owner.pos, aimed at nearest enemy
        # (if bolt_count > 1, spread them ±10 degrees apart)
        for i in range(self.bolt_count):
            # Calculate direction with slight spread for multiple bolts
            direction = (nearest_enemy.pos - self.owner.pos).normalize()

            if self.bolt_count > 1:
                # Spread bolts ±10 degrees apart
                angle_offset = (i - (self.bolt_count - 1) / 2) * 10
                direction = direction.rotate(angle_offset)

            # All bolts use current damage * owner.damage_multiplier
            damage = self.base_damage * self.owner.damage_multiplier

            projectile = Projectile(
                pos=self.owner.pos,
                direction=direction,
                speed=400,  # Speed of the bolt
                damage=damage,
                groups=self.projectile_group,
                enemy_group_ref=self.enemy_group,
                pierce=self.pierce,
                homing=self.homing,
                color=self.projectile_color
            )