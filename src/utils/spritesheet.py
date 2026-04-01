import pygame
from src.utils.resource_loader import ResourceLoader

class Spritesheet:
    def __init__(self, path: str, tile_w: int, tile_h: int):
        self.path = path
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.image = None
        self._load_image()

    def _load_image(self):
        """Load the spritesheet image using ResourceLoader."""
        rl = ResourceLoader.instance()
        self.image = rl.load_image(self.path)

    def get_frame(self, col: int, row: int) -> pygame.Surface:
        """Extract a single frame from the spritesheet."""
        if self.image is None:
            # Return a placeholder if image not loaded
            placeholder = pygame.Surface((self.tile_w, self.tile_h), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255))  # Magenta placeholder
            return placeholder

        # Calculate source rectangle
        src_rect = pygame.Rect(col * self.tile_w, row * self.tile_h, self.tile_w, self.tile_h)

        # Create a new surface for the frame
        frame = pygame.Surface((self.tile_w, self.tile_h), pygame.SRCALPHA)
        frame.blit(self.image, (0, 0), src_rect)

        return frame

    def get_animation(self, frame_coords: list[tuple[int,int]]) -> list[pygame.Surface]:
        """Extract a sequence of frames for an animation."""
        return [self.get_frame(col, row) for col, row in frame_coords]