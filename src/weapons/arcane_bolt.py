from pygame.math import Vector2
from settings import (
    ARCANE_BOLT_BASE_BOLT_COUNT,
    ARCANE_BOLT_BASE_COOLDOWN,
    ARCANE_BOLT_BASE_DAMAGE,
    ARCANE_BOLT_BASE_PIERCE,
    ARCANE_BOLT_PROJECTILE_COLOR,
    ARCANE_BOLT_PROJECTILE_SPEED,
    ARCANE_BOLT_SPREAD,
    ARCANE_BOLT_STAGGER,
    ARCANE_BOLT_TARGETING_RANGE,
    ARCANE_BOLT_UPGRADE_LEVELS,
)
from src.entities.projectile import Projectile
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon

class ArcaneBolt(BaseWeapon):
    name = "Arcane Bolt"
    description = "Fires homing bolts at the nearest enemy."
    base_damage = ARCANE_BOLT_BASE_DAMAGE
    base_cooldown = ARCANE_BOLT_BASE_COOLDOWN
    bolt_count = ARCANE_BOLT_BASE_BOLT_COUNT
    pierce = ARCANE_BOLT_BASE_PIERCE
    homing = True
    projectile_color = ARCANE_BOLT_PROJECTILE_COLOR
    IS_SPELL = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)

        # Bolts queued to fire after a short stagger delay
        # Each entry: {"delay": float, "direction": Vector2, "target": enemy}
        self.pending_bolts: list[dict] = []
        self.upgrade_levels = [dict(upgrade) for upgrade in ARCANE_BOLT_UPGRADE_LEVELS]

    def _spawn_bolt(self, direction: Vector2, target) -> None:
        """Spawn a single projectile in the given direction."""
        damage = self.base_damage * self.owner.damage_multiplier * (self.owner.spell_damage_multiplier if self.IS_SPELL else 1.0)
        Projectile(
            pos=self.owner.pos,
            direction=direction,
            speed=ARCANE_BOLT_PROJECTILE_SPEED,
            damage=damage,
            groups=self.projectile_group,
            enemy_group_ref=self.enemy_group,
            pierce=self.pierce,
            homing=self.homing,
            color=self.projectile_color,
            target_enemy=target,
            owner_crit_chance=self.owner.crit_chance,
            owner=self.owner,
        )

    def fire(self):
        """Fire homing bolts at the nearest enemy."""
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = ARCANE_BOLT_TARGETING_RANGE * ARCANE_BOLT_TARGETING_RANGE

        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq and distance_sq <= max_range_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if not nearest_enemy:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_ARCANE)

        base_direction = nearest_enemy.pos - self.owner.pos
        if base_direction.length_squared() > 0:
            base_direction = base_direction.normalize()
        elif self.owner.facing.length_squared() > 0:
            base_direction = self.owner.facing.normalize()
        else:
            base_direction = Vector2(1, 0)

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
