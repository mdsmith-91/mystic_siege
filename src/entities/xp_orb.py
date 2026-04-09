import pygame
from pygame.math import Vector2
import math
from settings import (
    MAGNET_PULL_ACCELERATION,
    MAGNET_PULL_GRACE_RADIUS,
    MAGNET_PULL_REFRESH_DURATION,
    MAGNET_PULL_SPEED_MAX,
    MAGNET_PULL_SPEED_MIN,
    XP_COLOR,
)

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
        self.magnet_target = None
        self.magnet_timer = 0.0
        self.magnet_speed = 0.0

    def magnetize(self, player) -> None:
        self.magnet_target = player
        self.magnet_timer = MAGNET_PULL_REFRESH_DURATION
        self.magnet_speed = max(self.magnet_speed, MAGNET_PULL_SPEED_MIN)

    def update(self, dt):
        """Update the XP orb with bobbing animation."""
        # float_offset += float_speed * dt
        self.float_offset += self.float_speed * dt
        if (
            self.magnet_target is not None
            and getattr(self.magnet_target, "can_collect_xp", self.magnet_target.is_alive)
            and self.magnet_timer > 0.0
        ):
            direction = self.magnet_target.pos - self.pos
            if direction.length_squared() > 0:
                distance = direction.length()
                if distance <= MAGNET_PULL_GRACE_RADIUS:
                    self.pos = Vector2(self.magnet_target.pos)
                else:
                    self.magnet_speed = min(
                        MAGNET_PULL_SPEED_MAX,
                        self.magnet_speed + (MAGNET_PULL_ACCELERATION * dt),
                    )
                    self.pos += direction.normalize() * self.magnet_speed * dt
            self.magnet_timer = max(0.0, self.magnet_timer - dt)
        else:
            self.magnet_target = None
            self.magnet_timer = 0.0
            self.magnet_speed = 0.0

        # draw_y = sin(float_offset) * 3 (visual only — rect.centery stays at world pos for collision)
        draw_y = math.sin(self.float_offset) * 3

        # Update rect position with the bobbing effect
        self.rect.center = (self.pos.x, self.pos.y + draw_y)
