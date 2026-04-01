import pygame
import os
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class ResourceLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = {}
        return cls._instance

    @classmethod
    def instance(cls):
        """Access the ResourceLoader singleton."""
        return cls()

    def load_image(self, path, scale=None, colorkey=None) -> pygame.Surface:
        """Load an image from path, with optional scaling and colorkey."""
        cache_key = (path, scale, colorkey)
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Try to load the image
            image = pygame.image.load(path).convert_alpha()

            # Apply scaling if requested
            if scale is not None:
                image = pygame.transform.scale(image, scale)

            # Apply colorkey if requested
            if colorkey is not None:
                image.set_colorkey(colorkey)

            self.cache[cache_key] = image
            return image

        except pygame.error:
            # If file not found, return a magenta 32x32 placeholder rect
            placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255))  # Magenta placeholder
            self.cache[cache_key] = placeholder
            return placeholder

    def load_sound(self, path) -> pygame.mixer.Sound:
        """Load a sound from path, returning None if file not found."""
        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            return None

    def load_font(self, name, size) -> pygame.font.Font:
        """Load a font from path, falling back to pygame default font."""
        try:
            return pygame.font.Font(name, size)
        except pygame.error:
            # Fall back to pygame default font
            return pygame.font.SysFont(None, size)