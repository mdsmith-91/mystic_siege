import pygame
from pygame.math import Vector2
import math
from settings import XP_COLOR

class XPOrb(pygame.sprite.Sprite):
    def __init__(self, pos, value: int, groups):
        super().__init__(groups)

        # image: 12x12 circle, gold color (212, 175, 55) on transparent surface
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, XP_COLOR, (6, 6), 6)

        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)

        # float_offset: float = 0.0  (sine wave for bobbing animation)
        self.float_offset = 0.0

        # float_speed = 3.0
        self.float_speed = 3.0

        # value: int - XP value of the orb
        self.value = value

        # collected: bool = False
        self.collected = False

    def update(self, dt):
        """Update the XP orb with bobbing animation."""
        # float_offset += float_speed * dt
        self.float_offset += self.float_speed * dt

        # draw_y = sin(float_offset) * 3 (visual only — rect.centery stays at world pos for collision)
        draw_y = math.sin(self.float_offset) * 3

        # Update rect position with the bobbing effect
        self.rect.center = (self.pos.x, self.pos.y + draw_y)