import pygame
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import WRAITH_ENEMY_DATA

# Column indices matching DIRECTION_ORDER in generate_sprite.py
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class Wraith(Enemy):
    def __init__(
        self,
        pos,
        player_list,
        all_groups: tuple,
        xp_orb_group=None,
        effect_group=None,
        projectile_group=None,
    ):
        super().__init__(pos, player_list, all_groups, WRAITH_ENEMY_DATA, xp_orb_group, effect_group)

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/wraith.png", 32, 32)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

        # lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
        # (lunge_active: bool, lunge_duration countdown)
        self.lunge_timer = WRAITH_ENEMY_DATA["lunge_cooldown"]
        self.lunge_active = False
        self.lunge_duration = 0.0

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def update(self, dt):
        # lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
        # (lunge_active: bool, lunge_duration countdown)
        if not self.lunge_active:
            self.lunge_timer -= dt
            if self.lunge_timer <= 0:
                # Start lunge
                self.lunge_active = True
                self.lunge_duration = WRAITH_ENEMY_DATA["lunge_duration"]
                self.speed *= WRAITH_ENEMY_DATA["lunge_speed_multiplier"]
        else:
            # During lunge
            self.lunge_duration -= dt
            if self.lunge_duration <= 0:
                # End lunge — restore speed and reset timer for next lunge
                self.lunge_active = False
                self.speed /= WRAITH_ENEMY_DATA["lunge_speed_multiplier"]
                self.lunge_timer = WRAITH_ENEMY_DATA["lunge_cooldown"]

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)

        # Note: Wraith ignores wall collision (no clamping to world bounds in update)
        # This means it can pass through walls, which is the intended behavior
