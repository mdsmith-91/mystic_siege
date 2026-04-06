import pygame
import sys
from src.game import Game
from src.utils.fps_cap import detect_refresh_rate

if __name__ == "__main__":
    # Pre-init mixer with explicit params before pygame.init() to avoid
    # Linux audio crackling caused by mismatched default buffer settings
    from settings import (AUDIO_FREQUENCY, AUDIO_FREQUENCY_LINUX,
                          AUDIO_SIZE, AUDIO_CHANNELS, AUDIO_BUFFER, AUDIO_BUFFER_LINUX)
    _is_linux   = sys.platform == "linux"
    _audio_freq = AUDIO_FREQUENCY_LINUX if _is_linux else AUDIO_FREQUENCY
    _audio_buf  = AUDIO_BUFFER_LINUX    if _is_linux else AUDIO_BUFFER
    pygame.mixer.pre_init(_audio_freq, AUDIO_SIZE, AUDIO_CHANNELS, _audio_buf)
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

    # Detect the current runtime ceiling from the active display; fall back to 60 if undetectable
    refresh_rate = detect_refresh_rate()

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
