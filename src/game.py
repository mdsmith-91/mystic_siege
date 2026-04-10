import pygame
from src.scene_manager import SceneManager
from src.utils.input_manager import InputManager
from settings import (
    STATE_MENU, MOUSE_HIDE_DELAY, SCREENSHOT_DIR, SCREEN_WIDTH, WHITE,
    HUD_READOUT_FONT_PATH, SCREENSHOT_NOTICE_TEXT, SCREENSHOT_NOTICE_DURATION,
    SCREENSHOT_NOTICE_FADE_DURATION, SCREENSHOT_NOTICE_Y, SCREENSHOT_NOTICE_FONT_SIZE,
)
from datetime import datetime, timezone
from pathlib import Path
from src.systems.save_system import SaveSystem
from src.utils.fps_cap import clamp_fps_cap
from src.utils.resource_loader import ResourceLoader

class Game:
    def __init__(self, screen, clock, refresh_rate: int = 60):
        self.screen = screen
        self.clock = clock
        self.max_refresh_rate = refresh_rate
        self.save_system = SaveSystem()
        self.refresh_rate = clamp_fps_cap(
            self.save_system.get_setting("fps_cap"),
            self.max_refresh_rate,
        )
        self.scene_manager = SceneManager()
        self.scene_manager.switch_to(STATE_MENU)
        self._mouse_idle = 0.0
        self._cursor_visible = True
        self._default_cursor = pygame.mouse.get_cursor()
        _invis_surf = pygame.Surface((1, 1), pygame.SRCALPHA)
        _invis_surf.fill((0, 0, 0, 0))
        self._invisible_cursor = pygame.cursors.Cursor((0, 0), _invis_surf)
        pygame.mouse.set_cursor(self._default_cursor)
        self._screenshot_notice_timer = 0.0
        self._screenshot_notice_font = ResourceLoader.instance().load_font(
            HUD_READOUT_FONT_PATH,
            SCREENSHOT_NOTICE_FONT_SIZE,
        )
        self._screenshot_notice_surface = self._screenshot_notice_font.render(
            SCREENSHOT_NOTICE_TEXT,
            True,
            WHITE,
        ).convert_alpha()

    def _save_screenshot(self) -> None:
        screenshot_dir = Path(SCREENSHOT_DIR)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        filename = f"screenshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
        filepath = screenshot_dir / filename
        pygame.image.save(self.screen, filepath)
        print(f"Screenshot saved: {filepath}")
        self._screenshot_notice_timer = SCREENSHOT_NOTICE_DURATION

    def _update_screenshot_notice(self, dt: float) -> None:
        if self._screenshot_notice_timer > 0.0:
            self._screenshot_notice_timer = max(0.0, self._screenshot_notice_timer - dt)

    def _draw_screenshot_notice(self, screen: pygame.Surface) -> None:
        if self._screenshot_notice_timer <= 0.0:
            return

        alpha = 255
        if SCREENSHOT_NOTICE_FADE_DURATION > 0:
            alpha = int(
                255
                * min(1.0, self._screenshot_notice_timer / SCREENSHOT_NOTICE_FADE_DURATION)
            )

        notice = self._screenshot_notice_surface.copy()
        notice.set_alpha(max(0, min(255, alpha)))
        notice_rect = notice.get_rect(midtop=(SCREEN_WIDTH // 2, SCREENSHOT_NOTICE_Y))
        screen.blit(notice, notice_rect)

    def _controller_screenshot_suppressed(self) -> bool:
        scene = self.scene_manager.current_scene
        settings_menu = None
        if getattr(scene, "controller_bindings_open", False):
            settings_menu = scene
        elif getattr(scene, "_settings_open", False):
            settings_menu = getattr(scene, "_settings_menu", None)

        if settings_menu is None:
            return False

        return (
            getattr(settings_menu, "controller_bindings_open", False)
            or getattr(settings_menu, "controller_capture_action", None) is not None
        )

    def run(self):
        running = True
        while running:
            self.save_system.reload_if_changed()
            self.refresh_rate = clamp_fps_cap(
                self.save_system.get_setting("fps_cap"),
                self.max_refresh_rate,
            )

            # Collect events once per frame so nothing is dropped
            events = pygame.event.get()
            mouse_moved = False
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_moved = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F12:
                        self._save_screenshot()
                elif event.type == pygame.JOYBUTTONDOWN:
                    if (
                        InputManager.instance().button_matches(
                            "screenshot",
                            event.button,
                            joystick_id=event.instance_id,
                        )
                        and not self._controller_screenshot_suppressed()
                    ):
                        self._save_screenshot()

            # Update with dt capped at 0.05 to prevent spiral-of-death on lag spikes
            dt = self.clock.tick(self.refresh_rate) / 1000.0
            if dt > 0.05:
                dt = 0.05
            self._update_screenshot_notice(dt)

            # Hide cursor after inactivity; restore immediately on any mouse movement
            if mouse_moved:
                self._mouse_idle = 0.0
                if not self._cursor_visible:
                    pygame.mouse.set_cursor(self._default_cursor)
                    self._cursor_visible = True
            else:
                self._mouse_idle += dt
                if self._cursor_visible and self._mouse_idle >= MOUSE_HIDE_DELAY:
                    pygame.mouse.set_cursor(self._invisible_cursor)
                    self._cursor_visible = False

            # Translate controller state into synthetic keyboard events before scenes process them
            InputManager.instance().update(dt, events)

            # Update and draw — pass the already-collected events so the queue isn't drained twice
            display_surface = pygame.display.get_surface() or self.screen
            self.scene_manager.update(dt, events)
            self.scene_manager.draw(display_surface)
            self._draw_screenshot_notice(display_surface)

            # Update display
            pygame.display.flip()
