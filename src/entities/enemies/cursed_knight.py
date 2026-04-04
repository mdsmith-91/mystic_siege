import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.utils.spritesheet import Spritesheet
from settings import WORLD_WIDTH, WORLD_HEIGHT

# Column indices matching direction order in knight_enemy_meta.json
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class CursedKnight(Enemy):
    def __init__(self, pos, player_list, all_groups: tuple, xp_orb_group=None, effect_group=None):
        enemy_data = {
            "name": "Knight",
            "hp": 80,
            "speed": 110,
            "damage": 20,
            "xp_value": 15,
            "behavior": "chase"
        }
        super().__init__(pos, player_list, all_groups, enemy_data, xp_orb_group, effect_group)

        # Shield mechanic — faces toward player each frame
        self.shield_facing = Vector2(1, 0)

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet("assets/sprites/enemies/knight_enemy.png", 32, 32)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
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

    def take_damage(self, amount, hit_direction=None, attacker=None):
        """Apply damage with frontal shield mechanic — 80% reduction when hit from the front."""
        if hit_direction is not None and hasattr(self, 'shield_facing'):
            angle = self.shield_facing.angle_to(hit_direction)
            if abs(angle) < 60:
                amount = amount * 0.2

        super().take_damage(amount, hit_direction=hit_direction, attacker=attacker)

    def update(self, dt):
        # Keep shield facing toward player
        if hasattr(self, 'target') and self.target:
            direction = self.target.pos - self.pos
            if direction.length() > 0:
                self.shield_facing = direction.normalize()
            else:
                self.shield_facing = Vector2(1, 0)

        super().update(dt)

        # Switch to the frame that matches movement direction
        self.image = self._frame_for_velocity()
        self.rect = self.image.get_rect(center=self.pos)
