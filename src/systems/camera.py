import pygame
from pygame.math import Vector2
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT

class Camera:
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.offset = Vector2(0, 0)
        self.lerp_speed = 5.0  # higher = snappier follow

    def update(self, target_pos: Vector2, dt: float):
        """Update camera position to follow target."""
        # target_offset = target_pos - Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        target_offset = target_pos - Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)

        # Clamp target_offset so camera never shows outside world bounds
        max_x = WORLD_WIDTH - SCREEN_WIDTH
        max_y = WORLD_HEIGHT - SCREEN_HEIGHT
        target_offset.x = max(0, min(max_x, target_offset.x))
        target_offset.y = max(0, min(max_y, target_offset.y))

        # self.offset = lerp(self.offset, target_offset, lerp_speed * dt)
        # (lerp: offset + (target - offset) * t, clamped so t doesn't exceed 1.0)
        t = self.lerp_speed * dt
        t = min(1.0, t)  # Clamp t so it doesn't exceed 1.0
        self.offset = self.offset + (target_offset - self.offset) * t

    def apply(self, entity) -> pygame.Rect:
        """Apply camera offset to an entity's rect."""
        return entity.rect.move(-self.offset)

    def apply_pos(self, world_pos: Vector2) -> Vector2:
        """Apply camera offset to a world position."""
        return world_pos - self.offset

    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """Convert screen position to world position."""
        return screen_pos + self.offset