import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.entities.effects import DamageNumber, ExpandingRingEffect
from src.utils.spritesheet import Spritesheet
from settings import PLAYER_HIT_IFRAME_DURATION, STONE_GOLEM_ENEMY_DATA

# Column indices matching direction order in golem_meta.json
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class StoneGolem(Enemy):
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
        super().__init__(pos, player_list, all_groups, STONE_GOLEM_ENEMY_DATA, xp_orb_group, effect_group, pickup_group)

        # Load the native 4-direction spritesheet: cols = [down, left, right, up]
        frame_width, frame_height = STONE_GOLEM_ENEMY_DATA["spritesheet_frame_size"]
        sheet = Spritesheet("assets/sprites/enemies/golem.png", frame_width, frame_height)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)
        self.shockwave_cooldown = STONE_GOLEM_ENEMY_DATA["shockwave_cooldown"]
        self.shockwave_cooldown_timer = self.shockwave_cooldown
        self.shockwave_windup = STONE_GOLEM_ENEMY_DATA["shockwave_windup"]
        self.shockwave_windup_timer = 0.0
        self.shockwave_trigger_range = STONE_GOLEM_ENEMY_DATA["shockwave_trigger_range"]
        self.shockwave_radius = STONE_GOLEM_ENEMY_DATA["shockwave_radius"]
        self.shockwave_damage = STONE_GOLEM_ENEMY_DATA["shockwave_damage"]
        self.shockwave_ring_width = STONE_GOLEM_ENEMY_DATA["shockwave_ring_width"]
        self.is_casting = False

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def _shockwave_ready_target(self):
        target = self.target
        if target is None:
            return None
        if (target.pos - self.pos).length_squared() > self.shockwave_trigger_range * self.shockwave_trigger_range:
            return None
        return target

    def _start_shockwave_cast(self) -> None:
        self.is_casting = True
        self.shockwave_windup_timer = self.shockwave_windup
        self.shockwave_cooldown_timer = self.shockwave_cooldown
        if self.effect_group is not None:
            ExpandingRingEffect(
                self.pos,
                self.shockwave_radius,
                STONE_GOLEM_ENEMY_DATA["shockwave_telegraph_color"],
                [self.effect_group],
                lifetime=STONE_GOLEM_ENEMY_DATA["shockwave_telegraph_lifetime"],
                ring_width=self.shockwave_ring_width,
                start_radius=self.shockwave_radius * 0.35,
                alpha=STONE_GOLEM_ENEMY_DATA["shockwave_telegraph_alpha"],
            )

    def _release_shockwave(self) -> None:
        if self.effect_group is not None:
            ExpandingRingEffect(
                self.pos,
                self.shockwave_radius,
                STONE_GOLEM_ENEMY_DATA["shockwave_blast_color"],
                [self.effect_group],
                lifetime=STONE_GOLEM_ENEMY_DATA["shockwave_blast_lifetime"],
                ring_width=self.shockwave_ring_width,
                start_radius=0.0,
                alpha=STONE_GOLEM_ENEMY_DATA["shockwave_blast_alpha"],
            )

        radius_sq = self.shockwave_radius * self.shockwave_radius
        for player in self.player_list:
            if not player.is_alive:
                continue
            if (player.pos - self.pos).length_squared() > radius_sq:
                continue
            actual_damage = player.take_damage(self.shockwave_damage)
            player.iframes = PLAYER_HIT_IFRAME_DURATION
            if self.effect_group is not None:
                DamageNumber(
                    player.pos - Vector2(0, 30),
                    actual_damage,
                    [self.effect_group],
                    is_player_damage=True,
                )

    def _compute_velocity(self, target) -> Vector2:
        if self.is_casting:
            return Vector2(0, 0)
        return super()._compute_velocity(target)

    def update(self, dt):
        self.shockwave_cooldown_timer = max(0.0, self.shockwave_cooldown_timer - dt)

        if self.is_casting:
            self.shockwave_windup_timer = max(0.0, self.shockwave_windup_timer - dt)
            if self.shockwave_windup_timer <= 0.0:
                self.is_casting = False
                self._release_shockwave()
        elif self.shockwave_cooldown_timer <= 0.0 and self._shockwave_ready_target() is not None:
            self._start_shockwave_cast()

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)
