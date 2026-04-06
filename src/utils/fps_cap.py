from settings import FPS, FPS_CAP_MIN


def detect_refresh_rate(default_fps: int = FPS) -> int:
    import pygame

    refresh_rate = pygame.display.get_current_refresh_rate()
    if refresh_rate <= 0:
        return default_fps
    return refresh_rate


def clamp_fps_cap(value: object, max_fps: int) -> int:
    upper_bound = max(FPS_CAP_MIN, int(max_fps))

    try:
        numeric_value = int(round(float(value)))
    except (TypeError, ValueError):
        numeric_value = upper_bound

    return max(FPS_CAP_MIN, min(upper_bound, numeric_value))
