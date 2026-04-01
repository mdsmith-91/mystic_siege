import pygame
import os
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


def _get_base_path() -> str:
    """Return the root directory for asset loading.

    When running as a PyInstaller bundle, files are unpacked to sys._MEIPASS.
    In development, resolve 2 levels up from src/utils/ to reach the project root.
    """
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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

        full_path = os.path.join(_get_base_path(), path)
        try:
            image = pygame.image.load(full_path).convert_alpha()

            if scale is not None:
                image = pygame.transform.scale(image, scale)

            if colorkey is not None:
                image.set_colorkey(colorkey)

            self.cache[cache_key] = image
            return image

        except pygame.error:
            placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255))  # Magenta placeholder
            self.cache[cache_key] = placeholder
            return placeholder

    def load_sound(self, path) -> pygame.mixer.Sound:
        """Load a sound from path, returning None if file not found."""
        full_path = os.path.join(_get_base_path(), path)
        try:
            return pygame.mixer.Sound(full_path)
        except pygame.error:
            return None

    def load_font(self, name, size) -> pygame.font.Font:
        """Load a font file by path, falling back to the pygame default font."""
        try:
            font_path = os.path.join(_get_base_path(), name) if name else None
            return pygame.font.Font(font_path, size)
        except pygame.error:
            return pygame.font.SysFont(None, size)
