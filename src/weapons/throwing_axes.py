from pygame.math import Vector2

from settings import (
    THROWING_AXES_BASE_COOLDOWN,
    THROWING_AXES_BASE_CRIT_BONUS,
    THROWING_AXES_BASE_DAMAGE,
    THROWING_AXES_BASE_PIERCE,
    THROWING_AXES_BASE_PROJECTILE_COUNT,
    THROWING_AXES_PROJECTILE_COLOR,
    THROWING_AXES_PROJECTILE_LIFETIME,
    THROWING_AXES_PROJECTILE_SIZE,
    THROWING_AXES_PROJECTILE_SPEED,
    THROWING_AXES_SPIN_SPEED,
    THROWING_AXES_SPREAD,
    THROWING_AXES_TARGETING_RANGE,
    THROWING_AXES_UPGRADE_LEVELS,
)
from src.entities.projectile import Projectile
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class ThrowingAxes(BaseWeapon):
    name = "Throwing Axes"
    description = "Hurls a spinning axe at the nearest enemy."
    base_damage = THROWING_AXES_BASE_DAMAGE
    base_cooldown = THROWING_AXES_BASE_COOLDOWN
    projectile_count = THROWING_AXES_BASE_PROJECTILE_COUNT
    pierce = THROWING_AXES_BASE_PIERCE
    crit_bonus = THROWING_AXES_BASE_CRIT_BONUS
    IS_SPELL = False

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in THROWING_AXES_UPGRADE_LEVELS]

    def _spawn_axe(self, direction: Vector2) -> None:
        Projectile(
            pos=self.owner.pos,
            direction=direction,
            speed=THROWING_AXES_PROJECTILE_SPEED,
            damage=self._scaled_damage(self.base_damage),
            groups=self.projectile_group,
            enemy_group_ref=self.enemy_group,
            pierce=self.pierce + getattr(self.owner, "projectile_pierce_bonus", 0),
            color=THROWING_AXES_PROJECTILE_COLOR,
            owner_crit_chance=min(1.0, self.owner.crit_chance + self.crit_bonus),
            owner=self.owner,
            lifetime=THROWING_AXES_PROJECTILE_LIFETIME,
            size=THROWING_AXES_PROJECTILE_SIZE,
            draw_shape="axe",
            rotate_to_direction=True,
            spin_speed=THROWING_AXES_SPIN_SPEED,
        )

    def fire(self):
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = THROWING_AXES_TARGETING_RANGE * THROWING_AXES_TARGETING_RANGE

        for enemy in self.enemy_group:
            distance_sq = (enemy.pos - self.owner.pos).length_squared()
            if distance_sq < nearest_distance_sq and distance_sq <= max_range_sq:
                nearest_distance_sq = distance_sq
                nearest_enemy = enemy

        if nearest_enemy is None:
            return

        base_direction = nearest_enemy.pos - self.owner.pos
        if base_direction.length_squared() == 0:
            return

        AudioManager.instance().play_sfx(AudioManager.WEAPON_THROWING_AXES)
        base_direction = base_direction.normalize()

        for index in range(self.projectile_count):
            if self.projectile_count == 1:
                direction = base_direction
            else:
                angle_offset = (index - (self.projectile_count - 1) / 2) * THROWING_AXES_SPREAD
                direction = base_direction.rotate(angle_offset)
            self._spawn_axe(direction)
