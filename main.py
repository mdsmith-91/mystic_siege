import pygame
import sys
from src.game import Game

if __name__ == "__main__":
    # Initialize pygame-ce with mixer
    pygame.mixer.init()
    pygame.init()

    # Set display to SCREEN_WIDTH x SCREEN_HEIGHT with TITLE
    from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE
    from src.systems.save_system import SaveSystem
    is_fullscreen = SaveSystem().get_setting("fullscreen")
    flags = (pygame.FULLSCREEN if is_fullscreen else 0) | pygame.SCALED
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags, vsync=1)
    pygame.display.set_caption(TITLE)

    # Create pygame.time.Clock
    clock = pygame.time.Clock()

    # Cap to the monitor's refresh rate; fall back to 60 if undetectable
    refresh_rate = pygame.display.get_current_refresh_rate()
    if refresh_rate <= 0:
        refresh_rate = 60

    # Instantiate Game from src/game.py
    game = Game(screen, clock, refresh_rate)

    # Call game.run()
    try:
        game.run()
    finally:
        # Handle clean quit
        pygame.quit()
        sys.exit()