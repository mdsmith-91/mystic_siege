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
    flags = pygame.FULLSCREEN if SaveSystem().get_setting("fullscreen") else 0
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption(TITLE)

    # Create pygame.time.Clock
    clock = pygame.time.Clock()

    # Instantiate Game from src/game.py
    game = Game(screen, clock)

    # Call game.run()
    try:
        game.run()
    finally:
        # Handle clean quit
        pygame.quit()
        sys.exit()