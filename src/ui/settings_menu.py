import pygame
from src.systems.save_system import SaveSystem
from src.utils.audio_manager import AudioManager
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD


def _sdl_display_bounds() -> list[tuple[int, int, int, int]]:
    """Return (x, y, w, h) for every SDL display via ctypes. Returns [] on failure."""
    import sys
    import ctypes
    from ctypes.util import find_library
    try:
        lib = find_library("SDL2")
        if not lib:
            lib = {"win32": "SDL2.dll", "darwin": "libSDL2.dylib"}.get(
                sys.platform, "libSDL2-2.0.so.0"
            )
        sdl2 = ctypes.CDLL(lib)

        class _Rect(ctypes.Structure):
            _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int),
                        ("w", ctypes.c_int), ("h", ctypes.c_int)]

        sdl2.SDL_GetNumVideoDisplays.restype = ctypes.c_int
        sdl2.SDL_GetDisplayBounds.restype = ctypes.c_int
        sdl2.SDL_GetDisplayBounds.argtypes = [ctypes.c_int, ctypes.POINTER(_Rect)]

        result = []
        for i in range(sdl2.SDL_GetNumVideoDisplays()):
            r = _Rect()
            if sdl2.SDL_GetDisplayBounds(i, ctypes.byref(r)) == 0:
                result.append((r.x, r.y, r.w, r.h))
        return result
    except Exception:
        return []


def _get_cursor_display_index() -> int:
    """Return the SDL display index the mouse cursor is currently on.

    Uses SDL_GetGlobalMouseState so it works before any window is created.
    Falls back to 0 on failure.
    """
    import sys
    import ctypes
    from ctypes.util import find_library
    try:
        lib = find_library("SDL2")
        if not lib:
            lib = {"win32": "SDL2.dll", "darwin": "libSDL2.dylib"}.get(
                sys.platform, "libSDL2-2.0.so.0"
            )
        sdl2 = ctypes.CDLL(lib)
        sdl2.SDL_GetGlobalMouseState.restype = ctypes.c_uint32
        sdl2.SDL_GetGlobalMouseState.argtypes = [
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        ]
        mx, my = ctypes.c_int(0), ctypes.c_int(0)
        sdl2.SDL_GetGlobalMouseState(ctypes.byref(mx), ctypes.byref(my))
        bounds = _sdl_display_bounds()
        for i, (dx, dy, dw, dh) in enumerate(bounds):
            if dx <= mx.value < dx + dw and dy <= my.value < dy + dh:
                return i
    except Exception:
        pass
    return 0



BACKGROUND_COLOR    = (15, 10, 25)
TEXT_COLOR          = (255, 255, 255)
LABEL_COLOR         = (180, 160, 140)
BUTTON_COLOR        = (30, 20, 10)
BUTTON_HIGHLIGHT    = (40, 30, 20)
SLIDER_TRACK_COLOR  = (50, 40, 30)
SLIDER_HANDLE_COLOR = (180, 150, 80)
CONFIRM_BG          = (20, 15, 10)


class SettingsMenu:
    def __init__(self):
        self.save_system = SaveSystem()

        self.next_scene: str | None = None
        self.next_scene_kwargs: dict = {}

        self.music_volume = self.save_system.get_setting("music_volume")
        self.sfx_volume   = self.save_system.get_setting("sfx_volume")
        self.show_fps     = self.save_system.get_setting("show_fps")

        # Keyboard nav index for buttons (0=show_fps, 1=reset, 2=back)
        self.selected_index = 0
        self.keyboard_active = False

        self.confirm_dialog_open = False
        self.dragging_slider = None
        self.sliders = {}
        self.buttons = {}

        self.font_title = pygame.font.SysFont("serif", 64)
        self.font_label = pygame.font.SysFont("serif", 20)
        self.font_button = pygame.font.SysFont("serif", 22)

        self._init_ui_elements()

    def _init_ui_elements(self):
        cx = SCREEN_WIDTH // 2
        slider_width  = 300
        slider_height = 20
        slider_x      = cx - slider_width // 2

        button_width  = 240
        button_height = 50
        button_x      = cx - button_width // 2

        # Sliders
        self.sliders["music_volume"] = {
            "rect":        pygame.Rect(slider_x, 165, slider_width, slider_height),
            "handle_rect": pygame.Rect(slider_x + int(self.music_volume * slider_width), 160, 20, slider_height + 10),
            "value":       self.music_volume,
            "label":       "Music Volume",
        }
        self.sliders["sfx_volume"] = {
            "rect":        pygame.Rect(slider_x, 245, slider_width, slider_height),
            "handle_rect": pygame.Rect(slider_x + int(self.sfx_volume * slider_width), 240, 20, slider_height + 10),
            "value":       self.sfx_volume,
            "label":       "SFX Volume",
        }

        # Buttons (navigable, 0–2)
        self.buttons["show_fps"] = {
            "rect":  pygame.Rect(button_x, 340, button_width, button_height),
            "text":  "Show FPS: " + ("ON" if self.show_fps else "OFF"),
            "value": self.show_fps,
        }
        self.buttons["reset"] = {
            "rect":  pygame.Rect(button_x, 410, button_width, button_height),
            "text":  "Reset Progress",
            "value": None,
        }
        self.buttons["back"] = {
            "rect":  pygame.Rect(button_x, 480, button_width, button_height),
            "text":  "Back",
            "value": None,
        }

        # Confirm dialog
        dw, dh = 360, 160
        dx = cx - dw // 2
        dy = SCREEN_HEIGHT // 2 - dh // 2
        self.confirm_dialog = {
            "rect": pygame.Rect(dx, dy, dw, dh),
            "text": "Reset all progress? This cannot be undone.",
            "buttons": {
                "yes":    {"rect": pygame.Rect(dx + 30,       dy + 100, 130, 40), "text": "YES, RESET"},
                "cancel": {"rect": pygame.Rect(dx + dw - 160, dy + 100, 130, 40), "text": "CANCEL"},
            },
        }

    def _activate_button(self, button_name: str):
        """Fire the action for the named button — shared by mouse click and keyboard ENTER."""
        if button_name == "reset":
            self.confirm_dialog_open = True
        elif button_name == "back":
            self.next_scene = "menu"
        elif button_name == "show_fps":
            new_value = not self.buttons["show_fps"]["value"]
            self.buttons["show_fps"]["value"] = new_value
            self.buttons["show_fps"]["text"] = "Show FPS: " + ("ON" if new_value else "OFF")
            self.show_fps = new_value
            self.save_system.set_setting("show_fps", new_value)

    def handle_events(self, events):
        for event in events:
            self._handle_event(event)

    def _handle_event(self, event):
        if self.confirm_dialog_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.confirm_dialog_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.confirm_dialog["buttons"]["yes"]["rect"].collidepoint(mouse_pos):
                    self.save_system.reset()
                    self.confirm_dialog_open = False
                    self.music_volume = self.save_system.get_setting("music_volume")
                    self.sfx_volume   = self.save_system.get_setting("sfx_volume")
                    self.show_fps     = self.save_system.get_setting("show_fps")
                    self._init_ui_elements()
                elif self.confirm_dialog["buttons"]["cancel"]["rect"].collidepoint(mouse_pos):
                    self.confirm_dialog_open = False
            return

        if event.type == pygame.MOUSEMOTION:
            self.keyboard_active = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_scene = "menu"
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.keyboard_active = True
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.keyboard_active = True
                self.selected_index = min(2, self.selected_index + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                btn_keys = ["show_fps", "reset", "back"]
                self._activate_button(btn_keys[self.selected_index])
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for slider_name, slider_data in self.sliders.items():
                if slider_data["handle_rect"].collidepoint(mouse_pos):
                    self.dragging_slider = slider_name
                    return
            btn_keys = ["show_fps", "reset", "back"]
            for i, button_name in enumerate(btn_keys):
                if self.buttons[button_name]["rect"].collidepoint(mouse_pos):
                    self.selected_index = i
                    self._activate_button(button_name)
                    return

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider:
                mouse_x, _ = event.pos
                slider = self.sliders[self.dragging_slider]
                track  = slider["rect"]
                new_x     = max(track.left, min(mouse_x, track.right))
                new_value = (new_x - track.left) / track.width
                slider["handle_rect"].x = new_x - slider["handle_rect"].width // 2
                slider["value"]         = new_value
                if self.dragging_slider == "music_volume":
                    self.music_volume = new_value
                    self.save_system.set_setting("music_volume", new_value)
                    AudioManager.instance().set_music_volume(new_value)
                elif self.dragging_slider == "sfx_volume":
                    self.sfx_volume = new_value
                    self.save_system.set_setting("sfx_volume", new_value)
                    AudioManager.instance().set_sfx_volume(new_value)

    def update(self, dt: float):
        pass

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        # Title
        title_surf   = self.font_title.render("SETTINGS", True, GOLD)
        title_shadow = self.font_title.render("SETTINGS", True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        screen.blit(title_shadow, (cx - title_surf.get_width() // 2 + 3, 53))
        screen.blit(title_surf,   (cx - title_surf.get_width() // 2,     50))

        mouse_pos = pygame.mouse.get_pos()

        # Sliders
        for slider_name, slider_data in self.sliders.items():
            track  = slider_data["rect"]
            handle = slider_data["handle_rect"]

            # Label centered above track
            lbl = self.font_label.render(slider_data["label"], True, LABEL_COLOR)
            screen.blit(lbl, (cx - lbl.get_width() // 2, track.top - 28))

            # Track
            pygame.draw.rect(screen, SLIDER_TRACK_COLOR, track, border_radius=6)
            # Filled portion
            fill_w = handle.centerx - track.left
            if fill_w > 0:
                pygame.draw.rect(screen, SLIDER_HANDLE_COLOR,
                                 pygame.Rect(track.left, track.top, fill_w, track.height), border_radius=6)
            # Handle
            pygame.draw.rect(screen, SLIDER_HANDLE_COLOR, handle, border_radius=6)
            pygame.draw.rect(screen, GOLD, handle, 1, border_radius=6)

            # Percentage value to the right of track
            pct = self.font_label.render(f"{int(slider_data['value'] * 100)}%", True, TEXT_COLOR)
            screen.blit(pct, (track.right + 12, track.centery - pct.get_height() // 2))

        # Buttons
        btn_keys = ["show_fps", "reset", "back"]
        for i, key in enumerate(btn_keys):
            btn  = self.buttons[key]
            rect = btn["rect"]
            highlighted = rect.collidepoint(mouse_pos) or (self.keyboard_active and i == self.selected_index)
            pygame.draw.rect(screen, BUTTON_HIGHLIGHT if highlighted else BUTTON_COLOR, rect, border_radius=6)
            pygame.draw.rect(screen, GOLD, rect, 2, border_radius=6)
            text_surf = self.font_button.render(btn["text"], True, TEXT_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                    rect.centery - text_surf.get_height() // 2))

        # Confirm dialog
        if self.confirm_dialog_open:
            dialog = self.confirm_dialog
            pygame.draw.rect(screen, CONFIRM_BG,  dialog["rect"], border_radius=8)
            pygame.draw.rect(screen, GOLD, dialog["rect"], 2, border_radius=8)

            msg = self.font_label.render(dialog["text"], True, TEXT_COLOR)
            screen.blit(msg, (dialog["rect"].centerx - msg.get_width() // 2,
                              dialog["rect"].top + 24))

            for btn_data in dialog["buttons"].values():
                rect = btn_data["rect"]
                highlighted = rect.collidepoint(mouse_pos)
                pygame.draw.rect(screen, BUTTON_HIGHLIGHT if highlighted else BUTTON_COLOR, rect, border_radius=6)
                pygame.draw.rect(screen, GOLD, rect, 2, border_radius=6)
                t = self.font_button.render(btn_data["text"], True, TEXT_COLOR)
                screen.blit(t, (rect.centerx - t.get_width() // 2,
                                rect.centery - t.get_height() // 2))
