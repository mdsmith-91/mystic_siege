import pygame
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import STONE_GOLEM_ENEMY_DATA

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

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        # Scale to the settings-driven size to reflect the golem's mini-boss stature
        sheet = Spritesheet("assets/sprites/enemies/golem.png", 32, 32)
        _scale = STONE_GOLEM_ENEMY_DATA.get("sprite_scale", (32, 32))
        self._frames = {
            _DIR_DOWN:  pygame.transform.scale(sheet.get_frame(0, 0), _scale),
            _DIR_LEFT:  pygame.transform.scale(sheet.get_frame(1, 0), _scale),
            _DIR_RIGHT: pygame.transform.scale(sheet.get_frame(2, 0), _scale),
            _DIR_UP:    pygame.transform.scale(sheet.get_frame(3, 0), _scale),
        }

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

    def _frame_for_velocity(self) -> pygame.Surface:
        """Pick the directional frame that best matches current velocity."""
        if self.vel.length() < 1:
            return self._frames[_DIR_DOWN]
        if abs(self.vel.x) >= abs(self.vel.y):
            return self._frames[_DIR_RIGHT] if self.vel.x > 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.vel.y > 0 else self._frames[_DIR_UP]

    def update(self, dt):
        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)
