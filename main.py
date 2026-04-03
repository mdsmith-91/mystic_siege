import pygame
import sys
from src.game import Game

if __name__ == "__main__":
    # Pre-init mixer with explicit params before pygame.init() to avoid
    # Linux audio crackling caused by mismatched default buffer settings
    from settings import AUDIO_FREQUENCY, AUDIO_SIZE, AUDIO_CHANNELS, AUDIO_BUFFER
    pygame.mixer.pre_init(AUDIO_FREQUENCY, AUDIO_SIZE, AUDIO_CHANNELS, AUDIO_BUFFER)
    pygame.init()

    # Set display to SCREEN_WIDTH x SCREEN_HEIGHT with TITLE
    from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE
    from src.ui.settings_menu import _get_cursor_display_index
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED, vsync=1,
        display=_get_cursor_display_index(),
    )
    pygame.display.set_caption(TITLE)

    # Create pygame.time.Clock
    clock = pygame.time.Clock()

    # Cap to the monitor's refresh rate; fall back to 60 if undetectable
    refresh_rate = pygame.display.get_current_refresh_rate()
    if refresh_rate <= 0:
        refresh_rate = 60

    # Initialize controller support — scan for already-connected devices
    from src.utils.input_manager import InputManager
    InputManager.instance().scan()

    # Instantiate Game from src/game.py
    game = Game(screen, clock, refresh_rate)

    # Call game.run()
    try:
        game.run()
    finally:
        # Handle clean quit
        pygame.quit()