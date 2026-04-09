import pygame
from pygame.math import Vector2
import random
import math
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import (
    ENEMY_ELITE_DAMAGE_MULTIPLIER,
    ENEMY_ELITE_HP_MULTIPLIER,
    MINI_BAT_ENEMY_DATA,
    PLAGUE_BAT_ENEMY_DATA,
)

# Column indices matching direction order in bat_meta.json
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class PlagueBat(Enemy):
    def __init__(
        self,
        pos,
        player_list,
        all_groups: tuple,
        xp_orb_group=None,
        effect_group=None,
        pickup_group=None,
        projectile_group=None,
    ):
        super().__init__(pos, player_list, all_groups, PLAGUE_BAT_ENEMY_DATA, xp_orb_group, effect_group, pickup_group)

        # split_chance = 0.4  — on death, 40% chance to spawn 2 mini bats
        self.split_chance = PLAGUE_BAT_ENEMY_DATA["split_chance"]
        self.split_count = PLAGUE_BAT_ENEMY_DATA["split_count"]
        self.wave_frequency = PLAGUE_BAT_ENEMY_DATA["wave_frequency"]
        self.wave_amplitude = PLAGUE_BAT_ENEMY_DATA["wave_amplitude"]

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        # Scaled to 20x20 — bats are smaller than standard enemies
        sheet = Spritesheet("assets/sprites/enemies/bat.png", 32, 32)
        sprite_scale = PLAGUE_BAT_ENEMY_DATA["sprite_scale"]
        self._frames = {
            _DIR_DOWN:  pygame.transform.scale(sheet.get_frame(0, 0), sprite_scale),
            _DIR_LEFT:  pygame.transform.scale(sheet.get_frame(1, 0), sprite_scale),
            _DIR_RIGHT: pygame.transform.scale(sheet.get_frame(2, 0), sprite_scale),
            _DIR_UP:    pygame.transform.scale(sheet.get_frame(3, 0), sprite_scale),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

        # Track elapsed time for arc movement
        self._t = 0.0

        # Flag to indicate if this is a mini bat (for inheritance purposes)
        self.is_mini = False

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def _compute_velocity(self, target: pygame.sprite.Sprite | None) -> Vector2:
        """Chase with a sinusoidal side-to-side swoop."""
        if target is None:
            return Vector2(0, 0)
        direction = target.pos - self.pos
        if direction.length_squared() <= 0:
            return Vector2(0, 0)
        direction = direction.normalize()
        perpendicular = Vector2(-direction.y, direction.x)
        wave_offset = math.sin(self._t * self.wave_frequency)
        effective_dir = direction + perpendicular * (wave_offset * self.wave_amplitude)
        return effective_dir * self.speed

    def update(self, dt):
        # Track elapsed time
        self._t += dt

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)

    def on_death(self, xp_orb_group):
        """Handle plague bat death with chance to spawn mini bats."""
        super().on_death(xp_orb_group)

        if random.random() < self.split_chance and not self.is_mini:
            for _ in range(self.split_count):
                mini_bat = MiniBat(self.pos, self.player_list, self.all_groups, xp_orb_group, self.effect_group)
                if self.is_elite:
                    mini_bat.apply_elite_scaling(
                        ENEMY_ELITE_HP_MULTIPLIER,
                        ENEMY_ELITE_DAMAGE_MULTIPLIER,
                        preserve_hp_ratio=False,
                    )

class MiniBat(PlagueBat):
    """Mini bat spawned on PlagueBat death."""

    def __init__(
        self,
        pos,
        player_list,
        groups,
        xp_orb_group=None,
        effect_group=None,
        pickup_group=None,
        projectile_group=None,
    ):
        super().__init__(
            pos,
            player_list,
            groups,
            xp_orb_group=xp_orb_group,
            effect_group=effect_group,
            pickup_group=pickup_group,
            projectile_group=projectile_group,
        )
        self.is_mini = True

        # Override with mini bat stats
        self.name = MINI_BAT_ENEMY_DATA["name"]
        self.max_hp = MINI_BAT_ENEMY_DATA["hp"]
        self.hp = MINI_BAT_ENEMY_DATA["hp"]
        self.base_speed = MINI_BAT_ENEMY_DATA["speed"]
        self.speed = MINI_BAT_ENEMY_DATA["speed"]
        self.damage = MINI_BAT_ENEMY_DATA["damage"]
        self.xp_value = MINI_BAT_ENEMY_DATA["xp_value"]
        self.split_chance = MINI_BAT_ENEMY_DATA["split_chance"]
        self.split_count = MINI_BAT_ENEMY_DATA["split_count"]
        self.wave_frequency = MINI_BAT_ENEMY_DATA["wave_frequency"]
        self.wave_amplitude = MINI_BAT_ENEMY_DATA["wave_amplitude"]

        # Mini bats are even smaller than regular bats
        mini_scale = MINI_BAT_ENEMY_DATA["sprite_scale"]
        self._frames = {k: pygame.transform.scale(v, mini_scale) for k, v in self._frames.items()}
        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)
