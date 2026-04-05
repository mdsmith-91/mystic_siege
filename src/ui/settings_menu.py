import pygame
from src.systems.save_system import SaveSystem
from src.utils.audio_manager import AudioManager
from src.utils.input_manager import InputManager
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, CONTROLLER_BINDING_LABELS


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

        # Keyboard nav index for buttons
        self.selected_index = 0
        self.keyboard_active = False
        self.controller_selected_index = 0
        self.controller_profile_index = 0
        self.selected_controller_profile_key: str | None = None

        self.confirm_dialog_open = False
        self.controller_bindings_open = False
        self.controller_capture_action: str | None = None
        self.controller_capture_target: dict | None = None
        self._controller_capture_suppression: dict | None = None
        self.dragging_slider = None
        self.sliders = {}
        self.buttons = {}
        self.controller_buttons = {}

        self.font_title = pygame.font.SysFont("serif", 64)
        self.font_label = pygame.font.SysFont("serif", 20)
        self.font_button = pygame.font.SysFont("serif", 22)
        self.font_small = pygame.font.SysFont("serif", 16)

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

        # Buttons (navigable)
        self.buttons["show_fps"] = {
            "rect":  pygame.Rect(button_x, 340, button_width, button_height),
            "text":  "Show FPS: " + ("ON" if self.show_fps else "OFF"),
            "value": self.show_fps,
        }
        self.buttons["controller_bindings"] = {
            "rect":  pygame.Rect(button_x, 410, button_width, button_height),
            "text":  "Controller Bindings",
            "value": None,
        }
        self.buttons["reset"] = {
            "rect":  pygame.Rect(button_x, 480, button_width, button_height),
            "text":  "Reset Progress",
            "value": None,
        }
        self.buttons["back"] = {
            "rect":  pygame.Rect(button_x, 550, button_width, button_height),
            "text":  "Back",
            "value": None,
        }

        controller_button_x = cx - button_width // 2
        base_y = 240
        row_gap = 70
        self.controller_buttons = {
            "confirm": {"rect": pygame.Rect(controller_button_x, base_y, button_width, button_height)},
            "back": {"rect": pygame.Rect(controller_button_x, base_y + row_gap, button_width, button_height)},
            "start": {"rect": pygame.Rect(controller_button_x, base_y + row_gap * 2, button_width, button_height)},
            "reset_controller": {"rect": pygame.Rect(controller_button_x, base_y + row_gap * 3 + 20, button_width, button_height)},
            "controller_back": {"rect": pygame.Rect(controller_button_x, base_y + row_gap * 4 + 20, button_width, button_height)},
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
        elif button_name == "controller_bindings":
            self.controller_bindings_open = True
            self.controller_selected_index = 0
            self.controller_profile_index = 0
            self.selected_controller_profile_key = None
            self._materialize_selected_controller_profile()
        elif button_name == "back":
            self.next_scene = "menu"
        elif button_name == "show_fps":
            new_value = not self.buttons["show_fps"]["value"]
            self.buttons["show_fps"]["value"] = new_value
            self.buttons["show_fps"]["text"] = "Show FPS: " + ("ON" if new_value else "OFF")
            self.show_fps = new_value
            self.save_system.set_setting("show_fps", new_value)

    def _controller_button_order(self) -> list[str]:
        return ["confirm", "back", "start", "reset_controller", "controller_back"]

    def _controller_profile_options(self) -> list[dict]:
        return InputManager.instance().get_binding_profile_options()

    def _sync_controller_profile_selection(self) -> list[dict]:
        input_manager = InputManager.instance()
        if self.selected_controller_profile_key is not None:
            self.selected_controller_profile_key = input_manager.canonicalize_profile_key(
                self.selected_controller_profile_key
            )
        profiles = self._controller_profile_options()
        if not profiles:
            self.controller_profile_index = 0
            self.selected_controller_profile_key = None
            return profiles

        if self.selected_controller_profile_key is None:
            self.controller_profile_index = 0
            return profiles

        for index, profile in enumerate(profiles):
            if profile["profile_key"] == self.selected_controller_profile_key:
                self.controller_profile_index = index
                return profiles

        self.selected_controller_profile_key = None
        self.controller_profile_index = 0
        return profiles

    def _current_controller_profile(self) -> dict:
        profiles = self._sync_controller_profile_selection()
        if self.controller_profile_index >= len(profiles):
            self.controller_profile_index = max(0, len(profiles) - 1)
        return profiles[self.controller_profile_index]

    def _materialize_selected_controller_profile(self) -> None:
        current_profile = self._current_controller_profile()
        if current_profile["is_global"]:
            return
        input_manager = InputManager.instance()
        input_manager.ensure_profile_bindings(profile_key=current_profile["profile_key"])
        self.selected_controller_profile_key = input_manager.canonicalize_profile_key(
            current_profile["profile_key"]
        )

    @staticmethod
    def _controller_profile_label(profile: dict) -> str:
        if profile["is_global"]:
            return "Global Default"
        if profile["is_connected"]:
            return f"{profile['name']} (Connected)"
        if profile.get("guid"):
            return f"{profile['name']} (Saved Profile)"
        return profile["name"]

    def _controller_profile_arrow_rects(self, profile: dict) -> tuple[pygame.Rect, pygame.Rect]:
        label = self._controller_profile_label(profile)
        label_surface = self.font_label.render(f"Editing: {label}", True, GOLD)
        spacing = 16
        arrow_width = 40
        y = 196
        label_left = SCREEN_WIDTH // 2 - label_surface.get_width() // 2
        label_right = label_left + label_surface.get_width()
        return (
            pygame.Rect(label_left - spacing - arrow_width, y, arrow_width, 36),
            pygame.Rect(label_right + spacing, y, arrow_width, 36),
        )

    def _move_controller_profile(self, step: int) -> None:
        profiles = self._sync_controller_profile_selection()
        if not profiles:
            self.controller_profile_index = 0
            self.selected_controller_profile_key = None
            return
        self.controller_profile_index = (self.controller_profile_index + step) % len(profiles)
        self.selected_controller_profile_key = profiles[self.controller_profile_index]["profile_key"]
        self._materialize_selected_controller_profile()
        self._sync_controller_profile_selection()

    def _activate_controller_button(self, button_name: str) -> None:
        input_manager = InputManager.instance()
        profile_key = self._current_controller_profile()["profile_key"]
        if button_name in {"confirm", "back", "start"}:
            self.controller_capture_action = button_name
            current_profile = self._current_controller_profile()
            self.controller_capture_target = {
                "profile_key": current_profile["profile_key"],
                "is_global": current_profile["is_global"],
                "is_connected": current_profile["is_connected"],
            }
            self._controller_capture_suppression = None
        elif button_name == "reset_controller":
            input_manager.reset_bindings(profile_key=profile_key)
        elif button_name == "controller_back":
            self.controller_bindings_open = False
            self.controller_capture_action = None
            self.controller_capture_target = None
            self._controller_capture_suppression = None

    def _should_suppress_controller_capture_event(self, event) -> bool:
        suppression = self._controller_capture_suppression
        if suppression is None:
            return False

        if event.type == pygame.JOYBUTTONUP:
            if (
                getattr(event, "instance_id", None) == suppression["instance_id"]
                and getattr(event, "button", None) == suppression["button"]
            ):
                self._controller_capture_suppression = None
                return True
            return False

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            if not getattr(event, "synthetic_controller_event", False):
                return False
            if getattr(event, "source_instance_id", None) != suppression["instance_id"]:
                return False
            if getattr(event, "key", None) not in suppression["keys"]:
                return False
            if event.type == pygame.KEYUP:
                self._controller_capture_suppression = None
            return True

        return False

    def handle_events(self, events):
        for event in events:
            self._handle_event(event)

    def _handle_event(self, event):
        if self._should_suppress_controller_capture_event(event):
            return

        if self.confirm_dialog_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.confirm_dialog_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.confirm_dialog["buttons"]["yes"]["rect"].collidepoint(mouse_pos):
                    self.save_system.reset()
                    InputManager.instance().reload_bindings()
                    self.confirm_dialog_open = False
                    self.music_volume = self.save_system.get_setting("music_volume")
                    self.sfx_volume   = self.save_system.get_setting("sfx_volume")
                    self.show_fps     = self.save_system.get_setting("show_fps")
                    self._init_ui_elements()
                elif self.confirm_dialog["buttons"]["cancel"]["rect"].collidepoint(mouse_pos):
                    self.confirm_dialog_open = False
            return

        if self.controller_capture_action is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.controller_capture_action = None
                self.controller_capture_target = None
                self._controller_capture_suppression = None
            elif event.type == pygame.JOYBUTTONDOWN:
                input_manager = InputManager.instance()
                capture_target = self.controller_capture_target or {
                    "profile_key": self._current_controller_profile()["profile_key"],
                    "is_global": self._current_controller_profile()["is_global"],
                    "is_connected": self._current_controller_profile()["is_connected"],
                }
                profile_key = capture_target["profile_key"]
                connected_instance_ids = input_manager.get_connected_instance_ids_for_profile(profile_key)
                if (
                    capture_target["is_connected"]
                    and connected_instance_ids
                    and getattr(event, "instance_id", None) not in connected_instance_ids
                ):
                    return
                if profile_key is not None:
                    input_manager.ensure_profile_bindings(profile_key=profile_key)
                    self.selected_controller_profile_key = input_manager.canonicalize_profile_key(profile_key)
                input_manager.set_binding(
                    self.controller_capture_action,
                    event.button,
                    profile_key=profile_key,
                )
                self._controller_capture_suppression = {
                    "instance_id": getattr(event, "instance_id", None),
                    "button": event.button,
                    "keys": input_manager.get_synthetic_keys_for_button(
                        event.button,
                        joystick_id=getattr(event, "instance_id", None),
                    ),
                }
                self.controller_capture_action = None
                self.controller_capture_target = None
            return

        if self.controller_bindings_open:
            if event.type == pygame.MOUSEMOTION:
                self.keyboard_active = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.controller_bindings_open = False
                    self.controller_capture_target = None
                    self._controller_capture_suppression = None
                    return
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.keyboard_active = True
                    self._move_controller_profile(-1)
                    return
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.keyboard_active = True
                    self._move_controller_profile(1)
                    return
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.keyboard_active = True
                    self.controller_selected_index = max(0, self.controller_selected_index - 1)
                    return
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.keyboard_active = True
                    self.controller_selected_index = min(len(self._controller_button_order()) - 1, self.controller_selected_index + 1)
                    return
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._activate_controller_button(self._controller_button_order()[self.controller_selected_index])
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                left_rect, right_rect = self._controller_profile_arrow_rects(
                    self._current_controller_profile()
                )
                if left_rect.collidepoint(mouse_pos):
                    self._move_controller_profile(-1)
                    return
                if right_rect.collidepoint(mouse_pos):
                    self._move_controller_profile(1)
                    return
                for i, button_name in enumerate(self._controller_button_order()):
                    if self.controller_buttons[button_name]["rect"].collidepoint(mouse_pos):
                        self.controller_selected_index = i
                        self._activate_controller_button(button_name)
                        return
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
                self.selected_index = min(3, self.selected_index + 1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                btn_keys = ["show_fps", "controller_bindings", "reset", "back"]
                self._activate_button(btn_keys[self.selected_index])
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for slider_name, slider_data in self.sliders.items():
                if slider_data["handle_rect"].collidepoint(mouse_pos):
                    self.dragging_slider = slider_name
                    return
            btn_keys = ["show_fps", "controller_bindings", "reset", "back"]
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

        if self.controller_bindings_open:
            self._draw_controller_bindings(screen)
            return

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
        btn_keys = ["show_fps", "controller_bindings", "reset", "back"]
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

    def _draw_controller_bindings(self, screen):
        screen.fill(BACKGROUND_COLOR)

        title_surf = self.font_title.render("CONTROLLER", True, GOLD)
        title_shadow = self.font_title.render("CONTROLLER", True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        screen.blit(title_shadow, (cx - title_surf.get_width() // 2 + 3, 53))
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, 50))

        input_manager = InputManager.instance()
        mouse_pos = pygame.mouse.get_pos()
        controller_details = input_manager.get_connected_controller_details()
        current_profile = self._current_controller_profile()
        left_rect, right_rect = self._controller_profile_arrow_rects(current_profile)

        if controller_details:
            info_line = "Connected: " + " | ".join(
                f"{detail['name']} (ID {detail['instance_id']})"
                for detail in controller_details
            )
        else:
            info_line = "No controller connected"
        info_surface = self.font_small.render(info_line, True, LABEL_COLOR)
        screen.blit(info_surface, (cx - info_surface.get_width() // 2, 140))

        if self.controller_capture_action is not None:
            capture_target = self.controller_capture_target or current_profile
            if capture_target["is_global"]:
                target_name = "Global Default"
            else:
                display_profile = current_profile
                if (
                    capture_target.get("profile_key") is not None
                    and capture_target.get("profile_key") != current_profile["profile_key"]
                ):
                    for profile in self._controller_profile_options():
                        if profile["profile_key"] == capture_target["profile_key"]:
                            display_profile = profile
                            break
                if capture_target["is_connected"]:
                    target_name = f"{display_profile['name']} (Connected)"
                else:
                    target_name = f"{display_profile['name']} (Saved Profile)"
            capture_text = (
                f"{target_name}: press a controller button for {CONTROLLER_BINDING_LABELS[self.controller_capture_action]}"
                "  -  ESC cancels"
            )
            capture_surface = self.font_label.render(capture_text, True, GOLD)
            screen.blit(capture_surface, (cx - capture_surface.get_width() // 2, 175))
        else:
            helper_surface = self.font_small.render(
                "Left/Right changes target profile  -  Select an action, then press a controller button",
                True,
                LABEL_COLOR,
            )
            screen.blit(helper_surface, (cx - helper_surface.get_width() // 2, 178))

        pygame.draw.rect(screen, BUTTON_HIGHLIGHT if left_rect.collidepoint(mouse_pos) else BUTTON_COLOR, left_rect, border_radius=6)
        pygame.draw.rect(screen, GOLD, left_rect, 2, border_radius=6)
        pygame.draw.rect(screen, BUTTON_HIGHLIGHT if right_rect.collidepoint(mouse_pos) else BUTTON_COLOR, right_rect, border_radius=6)
        pygame.draw.rect(screen, GOLD, right_rect, 2, border_radius=6)

        left_text = self.font_button.render("<", True, TEXT_COLOR)
        right_text = self.font_button.render(">", True, TEXT_COLOR)
        screen.blit(left_text, (left_rect.centerx - left_text.get_width() // 2, left_rect.centery - left_text.get_height() // 2))
        screen.blit(right_text, (right_rect.centerx - right_text.get_width() // 2, right_rect.centery - right_text.get_height() // 2))

        target_label = self._controller_profile_label(current_profile)
        target_surface = self.font_label.render(f"Editing: {target_label}", True, GOLD)
        screen.blit(target_surface, (cx - target_surface.get_width() // 2, 202))

        for i, button_name in enumerate(self._controller_button_order()):
            rect = self.controller_buttons[button_name]["rect"]
            highlighted = rect.collidepoint(mouse_pos) or (self.keyboard_active and i == self.controller_selected_index)
            pygame.draw.rect(screen, BUTTON_HIGHLIGHT if highlighted else BUTTON_COLOR, rect, border_radius=6)
            pygame.draw.rect(screen, GOLD, rect, 2, border_radius=6)

            if button_name in CONTROLLER_BINDING_LABELS:
                label = (
                    f"{CONTROLLER_BINDING_LABELS[button_name]}: "
                    f"{input_manager.describe_binding(button_name, profile_key=current_profile['profile_key'])}"
                )
            elif button_name == "reset_controller":
                label = "Reset Global Default" if current_profile["is_global"] else "Reset This Profile"
            else:
                label = "Back"

            text_surf = self.font_button.render(label, True, TEXT_COLOR)
            screen.blit(
                text_surf,
                (rect.centerx - text_surf.get_width() // 2,
                 rect.centery - text_surf.get_height() // 2),
            )
