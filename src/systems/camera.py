import pygame
from pygame.math import Vector2
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    CAMERA_ZOOM_MIN,
    CAMERA_ZOOM_LERP,
    CAMERA_PLAYER_MARGIN,
)

class Camera:
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.offset = Vector2(0, 0)
        self.lerp_speed = 5.0  # higher = snappier follow
        self.zoom = 1.0

    def _view_size_for_zoom(self, zoom: float) -> Vector2:
        return Vector2(self.screen_w / zoom, self.screen_h / zoom)

    def get_view_size(self) -> Vector2:
        return self._view_size_for_zoom(self.zoom)

    def _clamp_offset(self, target_offset: Vector2, zoom: float) -> Vector2:
        view_size = self._view_size_for_zoom(zoom)
        max_x = max(0.0, WORLD_WIDTH - view_size.x)
        max_y = max(0.0, WORLD_HEIGHT - view_size.y)
        return Vector2(
            max(0.0, min(max_x, target_offset.x)),
            max(0.0, min(max_y, target_offset.y)),
        )

    def get_view_rect(self) -> pygame.Rect:
        view_size = self.get_view_size()
        return pygame.Rect(
            int(self.offset.x),
            int(self.offset.y),
            int(view_size.x),
            int(view_size.y),
        )

    def update(self, target_pos: Vector2, dt: float):
        """Update camera position to follow target."""
        self.zoom = 1.0
        target_offset = target_pos - Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        target_offset = self._clamp_offset(target_offset, self.zoom)

        # self.offset = lerp(self.offset, target_offset, lerp_speed * dt)
        # (lerp: offset + (target - offset) * t, clamped so t doesn't exceed 1.0)
        t = self.lerp_speed * dt
        t = min(1.0, t)  # Clamp t so it doesn't exceed 1.0
        self.offset = self.offset + (target_offset - self.offset) * t

    def update_multi(self, positions: list[Vector2], dt: float):
        """Update camera to fit multiple world positions."""
        if not positions:
            return
        if len(positions) == 1:
            self.update(positions[0], dt)
            return

        min_x = max_x = positions[0].x
        min_y = max_y = positions[0].y
        sum_x = 0.0
        sum_y = 0.0
        for pos in positions:
            x = pos.x
            y = pos.y
            sum_x += x
            sum_y += y
            if x < min_x:
                min_x = x
            elif x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            elif y > max_y:
                max_y = y

        centroid = Vector2(sum_x / len(positions), sum_y / len(positions))
        bbox_w = max_x - min_x + CAMERA_PLAYER_MARGIN
        bbox_h = max_y - min_y + CAMERA_PLAYER_MARGIN

        zoom_x = self.screen_w / max(1.0, bbox_w)
        zoom_y = self.screen_h / max(1.0, bbox_h)
        target_zoom = max(CAMERA_ZOOM_MIN, min(1.0, min(zoom_x, zoom_y)))

        zoom_t = min(1.0, CAMERA_ZOOM_LERP * dt)
        self.zoom += (target_zoom - self.zoom) * zoom_t

        target_offset = centroid - self._view_size_for_zoom(self.zoom) / 2
        target_offset = self._clamp_offset(target_offset, self.zoom)

        move_t = min(1.0, self.lerp_speed * dt)
        self.offset += (target_offset - self.offset) * move_t

    def apply(self, entity) -> pygame.Rect:
        """Apply camera offset to an entity's rect."""
        return entity.rect.move(-self.offset)

    def apply_pos(self, world_pos: Vector2) -> Vector2:
        """Apply camera offset to a world position."""
        return (world_pos - self.offset) * self.zoom

    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """Convert screen position to world position."""
        return (screen_pos / self.zoom) + self.offset

    def world_to_screen(self, world_pos: Vector2) -> Vector2:
        """Convert world position to screen position."""
        return self.apply_pos(world_pos)
