from pygame.math import Vector2

from settings import (
    LONGBOW_BASE_COOLDOWN,
    LONGBOW_BASE_CRIT_BONUS,
    LONGBOW_BASE_DAMAGE,
    LONGBOW_BASE_PIERCE,
    LONGBOW_BASE_PROJECTILE_COUNT,
    LONGBOW_PROJECTILE_COLOR,
    LONGBOW_PROJECTILE_LIFETIME,
    LONGBOW_PROJECTILE_SIZE,
    LONGBOW_PROJECTILE_SPEED,
    LONGBOW_SPREAD,
    LONGBOW_TARGETING_RANGE,
    LONGBOW_UPGRADE_LEVELS,
)
from src.entities.projectile import Projectile
from src.utils.audio_manager import AudioManager
from src.weapons.base_weapon import BaseWeapon


class Longbow(BaseWeapon):
    name = "Longbow"
    description = "Fires precise arrows at the nearest enemy."
    base_damage = LONGBOW_BASE_DAMAGE
    base_cooldown = LONGBOW_BASE_COOLDOWN
    projectile_count = LONGBOW_BASE_PROJECTILE_COUNT
    pierce = LONGBOW_BASE_PIERCE
    crit_bonus = LONGBOW_BASE_CRIT_BONUS
    IS_SPELL = False
    USES_PROJECTILE_PIERCE_BONUS = True
    USES_ARROW_PIERCE_BONUS = True

    def __init__(self, owner, projectile_group, enemy_group, effect_group=None):
        super().__init__(owner, projectile_group, enemy_group, effect_group)
        self.upgrade_levels = [dict(upgrade) for upgrade in LONGBOW_UPGRADE_LEVELS]

    def _spawn_arrow(self, direction: Vector2) -> None:
        Projectile(
            pos=self.owner.pos,
            direction=direction,
            speed=LONGBOW_PROJECTILE_SPEED,
            damage=self._scaled_damage(self.base_damage),
            groups=self.projectile_group,
            enemy_group_ref=self.enemy_group,
            pierce=self._get_effective_projectile_pierce(),
            color=LONGBOW_PROJECTILE_COLOR,
            owner_crit_chance=min(1.0, self.owner.crit_chance + self.crit_bonus),
            owner=self.owner,
            lifetime=LONGBOW_PROJECTILE_LIFETIME,
            size=LONGBOW_PROJECTILE_SIZE,
            draw_shape="arrow",
            rotate_to_direction=True,
        )

    def fire(self):
        if not self.enemy_group:
            return

        nearest_enemy = None
        nearest_distance_sq = float("inf")
        max_range_sq = LONGBOW_TARGETING_RANGE * LONGBOW_TARGETING_RANGE

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

        AudioManager.instance().play_sfx(AudioManager.WEAPON_LONGBOW)
        base_direction = base_direction.normalize()

        for index in range(self.projectile_count):
            if self.projectile_count == 1:
                direction = base_direction
            else:
                angle_offset = (index - (self.projectile_count - 1) / 2) * LONGBOW_SPREAD
                direction = base_direction.rotate(angle_offset)
            self._spawn_arrow(direction)
