import pygame
from src.systems.save_system import SaveSystem
from src.utils.audio_manager import AudioManager
from src.utils.input_manager import InputManager
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GOLD,
    CONTROLLER_BINDING_LABELS,
    FPS_CAP_MIN,
    FPS_CAP_COARSE_STEP,
    FPS_CAP_FINE_STEP,
    SETTINGS_SLIDER_STEP_COARSE,
    SETTINGS_SLIDER_STEP_FINE,
    SETTINGS_ANALOG_ADJUST_REPEAT_DELAY,
    SETTINGS_ANALOG_ADJUST_REPEAT_RATE,
    SETTINGS_SLIDER_VALUE_X_OFFSET,
    SETTINGS_BUTTON_WIDTH,
    SETTINGS_BUTTON_HEIGHT,
    SETTINGS_BUTTON_START_Y,
    SETTINGS_BUTTON_ROW_GAP,
    SETTINGS_BUTTON_COLUMN_GAP,
)
from src.utils.fps_cap import detect_refresh_rate, clamp_fps_cap


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
        self.show_stat_bonuses = self.save_system.get_setting("show_stat_bonuses")
        self.show_damage_numbers = self.save_system.get_setting("show_damage_numbers")
        self.fps_cap_limit = detect_refresh_rate()
        self.fps_cap = clamp_fps_cap(self.save_system.get_setting("fps_cap"), self.fps_cap_limit)

        # Keyboard nav index for buttons
        self.selected_index = 0
        self.keyboard_active = False
        self.controller_selected_index = 0
        self.controller_profile_index = 0
        self.selected_controller_profile_key: str | None = None

        self.confirm_dialog_open = False
        self.confirm_dialog_selected_index = 1
        self.controller_bindings_open = False
        self.controller_capture_action: str | None = None
        self.controller_capture_target: dict | None = None
        self._controller_capture_suppression: dict | None = None
        self.dragging_slider = None
        self._slider_adjust_dir = 0
        self._slider_adjust_timer = 0.0
        self.sliders = {}
        self.buttons = {}
        self.controller_buttons = {}

        self.font_title = pygame.font.SysFont("serif", 64)
        self.font_label = pygame.font.SysFont("serif", 20)
        self.font_button = pygame.font.SysFont("serif", 22)
        self.font_small = pygame.font.SysFont("serif", 16)

        self._init_ui_elements()

    @staticmethod
    def _main_menu_order() -> list[str]:
        return [
            "music_volume",
            "sfx_volume",
            "fps_cap",
            "controller_bindings",
            "show_fps",
            "reset",
            "show_stat_bonuses",
            "show_damage_numbers",
            "back",
        ]

    @staticmethod
    def _button_navigation() -> dict[str, dict[str, str]]:
        return {
            "controller_bindings": {"up": "fps_cap", "down": "reset", "right": "show_fps"},
            "show_fps": {"up": "fps_cap", "down": "show_stat_bonuses", "left": "controller_bindings"},
            "reset": {"up": "controller_bindings", "down": "back", "right": "show_stat_bonuses"},
            "show_stat_bonuses": {"up": "show_fps", "down": "show_damage_numbers", "left": "reset"},
            "show_damage_numbers": {"up": "show_stat_bonuses", "down": "back", "left": "back"},
            "back": {"up": "reset", "right": "show_damage_numbers"},
        }

    def _init_ui_elements(self):
        cx = SCREEN_WIDTH // 2
        slider_width  = 300
        slider_height = 20
        slider_x      = cx - slider_width // 2

        button_width = SETTINGS_BUTTON_WIDTH
        button_height = SETTINGS_BUTTON_HEIGHT
        left_button_x = cx - SETTINGS_BUTTON_COLUMN_GAP // 2 - button_width
        right_button_x = cx + SETTINGS_BUTTON_COLUMN_GAP // 2

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
        fps_cap_fraction = self._slider_fraction("fps_cap", self.fps_cap)
        self.sliders["fps_cap"] = {
            "rect":        pygame.Rect(slider_x, 325, slider_width, slider_height),
            "handle_rect": pygame.Rect(slider_x + int(fps_cap_fraction * slider_width), 320, 20, slider_height + 10),
            "value":       self.fps_cap,
            "label":       "FPS Cap",
        }

        # Buttons (navigable)
        self.buttons["show_fps"] = {
            "rect":  pygame.Rect(right_button_x, SETTINGS_BUTTON_START_Y, button_width, button_height),
            "text":  "Show FPS: " + ("ON" if self.show_fps else "OFF"),
            "value": self.show_fps,
        }
        self.buttons["show_stat_bonuses"] = {
            "rect":  pygame.Rect(
                right_button_x,
                SETTINGS_BUTTON_START_Y + SETTINGS_BUTTON_ROW_GAP,
                button_width,
                button_height,
            ),
            "text":  "Show Stats: " + ("ON" if self.show_stat_bonuses else "OFF"),
            "value": self.show_stat_bonuses,
        }
        self.buttons["show_damage_numbers"] = {
            "rect":  pygame.Rect(
                right_button_x,
                SETTINGS_BUTTON_START_Y + SETTINGS_BUTTON_ROW_GAP * 2,
                button_width,
                button_height,
            ),
            "text":  "Damage Numbers: " + ("ON" if self.show_damage_numbers else "OFF"),
            "value": self.show_damage_numbers,
        }
        self.buttons["controller_bindings"] = {
            "rect":  pygame.Rect(left_button_x, SETTINGS_BUTTON_START_Y, button_width, button_height),
            "text":  "Controller Bindings",
            "value": None,
        }
        self.buttons["reset"] = {
            "rect":  pygame.Rect(
                left_button_x,
                SETTINGS_BUTTON_START_Y + SETTINGS_BUTTON_ROW_GAP,
                button_width,
                button_height,
            ),
            "text":  "Reset Progress",
            "value": None,
        }
        self.buttons["back"] = {
            "rect":  pygame.Rect(
                left_button_x,
                SETTINGS_BUTTON_START_Y + SETTINGS_BUTTON_ROW_GAP * 2,
                button_width,
                button_height,
            ),
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
            self.confirm_dialog_selected_index = 1
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
        elif button_name == "show_stat_bonuses":
            new_value = not self.buttons["show_stat_bonuses"]["value"]
            self.buttons["show_stat_bonuses"]["value"] = new_value
            self.buttons["show_stat_bonuses"]["text"] = "Show Stats: " + ("ON" if new_value else "OFF")
            self.show_stat_bonuses = new_value
            self.save_system.set_setting("show_stat_bonuses", new_value)
        elif button_name == "show_damage_numbers":
            new_value = not self.buttons["show_damage_numbers"]["value"]
            self.buttons["show_damage_numbers"]["value"] = new_value
            self.buttons["show_damage_numbers"]["text"] = "Damage Numbers: " + ("ON" if new_value else "OFF")
            self.show_damage_numbers = new_value
            self.save_system.set_setting("show_damage_numbers", new_value)

    def _slider_min_value(self, slider_name: str) -> float:
        if slider_name == "fps_cap":
            return float(FPS_CAP_MIN)
        return 0.0

    def _slider_max_value(self, slider_name: str) -> float:
        if slider_name == "fps_cap":
            return float(self.fps_cap_limit)
        return 1.0

    def _slider_fraction(self, slider_name: str, value: float) -> float:
        min_value = self._slider_min_value(slider_name)
        max_value = self._slider_max_value(slider_name)
        if max_value <= min_value:
            return 0.0
        return (value - min_value) / (max_value - min_value)

    def _slider_value_from_fraction(self, slider_name: str, fraction: float) -> float:
        min_value = self._slider_min_value(slider_name)
        max_value = self._slider_max_value(slider_name)
        if max_value <= min_value:
            return min_value
        return min_value + max(0.0, min(1.0, fraction)) * (max_value - min_value)

    def _set_slider_value(self, slider_name: str, value: float) -> None:
        slider = self.sliders[slider_name]
        if slider_name == "fps_cap":
            clamped_value = float(clamp_fps_cap(value, self.fps_cap_limit))
        else:
            clamped_value = max(0.0, min(1.0, value))
        track = slider["rect"]
        handle = slider["handle_rect"]

        slider["value"] = clamped_value
        handle.centerx = track.left + int(self._slider_fraction(slider_name, clamped_value) * track.width)

        if slider_name == "music_volume":
            self.music_volume = clamped_value
            self.save_system.set_setting("music_volume", clamped_value)
            AudioManager.instance().set_music_volume(clamped_value)
        elif slider_name == "sfx_volume":
            self.sfx_volume = clamped_value
            self.save_system.set_setting("sfx_volume", clamped_value)
            AudioManager.instance().set_sfx_volume(clamped_value)
        elif slider_name == "fps_cap":
            self.fps_cap = int(clamped_value)
            self.save_system.set_setting("fps_cap", self.fps_cap)

    def _adjust_slider(self, slider_name: str, delta: float) -> None:
        if slider_name == "fps_cap":
            fine_adjust = abs(delta) <= SETTINGS_SLIDER_STEP_FINE + 1e-9
            step = FPS_CAP_FINE_STEP if fine_adjust else FPS_CAP_COARSE_STEP
            adjusted_value = self.sliders[slider_name]["value"] + (step if delta > 0 else -step)
        else:
            adjusted_value = round(self.sliders[slider_name]["value"] + delta, 4)
        self._set_slider_value(slider_name, adjusted_value)

    def _selected_main_item(self) -> str:
        return self._main_menu_order()[self.selected_index]

    def _move_button_selection(self, direction: str) -> bool:
        selected_item = self._selected_main_item()
        if selected_item not in self.buttons:
            return False

        destination = self._button_navigation().get(selected_item, {}).get(direction)
        if destination is None:
            return False

        self.selected_index = self._main_menu_order().index(destination)
        return True

    @staticmethod
    def _confirm_dialog_button_order() -> list[str]:
        return ["yes", "cancel"]

    def _activate_confirm_dialog_button(self, button_name: str) -> None:
        if button_name == "yes":
            self.save_system.reset()
            InputManager.instance().reload_bindings()
            self.confirm_dialog_open = False
            self.music_volume = self.save_system.get_setting("music_volume")
            self.sfx_volume = self.save_system.get_setting("sfx_volume")
            self.show_fps = self.save_system.get_setting("show_fps")
            self.show_stat_bonuses = self.save_system.get_setting("show_stat_bonuses")
            self.fps_cap = clamp_fps_cap(self.save_system.get_setting("fps_cap"), self.fps_cap_limit)
            self._init_ui_elements()
            self._slider_adjust_dir = 0
            self._slider_adjust_timer = 0.0
            return

        self.confirm_dialog_open = False

    def _interactive_mouse_target(self, mouse_pos: tuple[int, int]) -> str | None:
        for item_name in self._main_menu_order():
            if item_name in self.sliders:
                slider_data = self.sliders[item_name]
                if slider_data["rect"].inflate(12, 12).collidepoint(mouse_pos) or slider_data["handle_rect"].collidepoint(mouse_pos):
                    return item_name
            elif item_name in self.buttons and self.buttons[item_name]["rect"].collidepoint(mouse_pos):
                return item_name
        return None

    def _controller_hint_text(self) -> str:
        if self.confirm_dialog_open:
            return "Left/Right changes choice  -  Confirm selects  -  Back cancels"

        selected_item = self._selected_main_item()
        if selected_item in self.sliders:
            return "Up/Down selects  -  Left/Right adjusts setting  -  Stick hold fine-tunes"

        if selected_item in self.buttons:
            return "Up/Down selects  -  Left/Right moves across buttons  -  Confirm activates  -  Back returns"

        return "Up/Down selects  -  Confirm activates  -  Back returns"

    def _active_slider_controller_axis(self) -> int:
        input_manager = InputManager.instance()
        for joystick_id in input_manager.get_connected_joysticks():
            axis_x, _ = input_manager.get_movement_for_joystick(joystick_id)
            if axis_x < 0.0:
                return -1
            if axis_x > 0.0:
                return 1
        return 0

    def _update_slider_controller_adjustment(self, dt: float) -> None:
        if self.confirm_dialog_open or self.controller_bindings_open:
            self._slider_adjust_dir = 0
            self._slider_adjust_timer = 0.0
            return

        selected_item = self._selected_main_item()
        if selected_item not in self.sliders:
            self._slider_adjust_dir = 0
            self._slider_adjust_timer = 0.0
            return

        new_dir = self._active_slider_controller_axis()
        if new_dir != self._slider_adjust_dir:
            self._slider_adjust_dir = new_dir
            if new_dir != 0:
                self._slider_adjust_timer = SETTINGS_ANALOG_ADJUST_REPEAT_DELAY
                self._adjust_slider(selected_item, SETTINGS_SLIDER_STEP_FINE * new_dir)
            else:
                self._slider_adjust_timer = 0.0
            return

        if new_dir == 0:
            return

        self._slider_adjust_timer -= dt
        if self._slider_adjust_timer <= 0.0:
            self._slider_adjust_timer += SETTINGS_ANALOG_ADJUST_REPEAT_RATE
            self._adjust_slider(selected_item, SETTINGS_SLIDER_STEP_FINE * new_dir)

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
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    self.keyboard_active = True
                    self.confirm_dialog_selected_index = max(0, self.confirm_dialog_selected_index - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                    self.keyboard_active = True
                    self.confirm_dialog_selected_index = min(1, self.confirm_dialog_selected_index + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._activate_confirm_dialog_button(
                        self._confirm_dialog_button_order()[self.confirm_dialog_selected_index]
                    )
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                for index, button_name in enumerate(self._confirm_dialog_button_order()):
                    if self.confirm_dialog["buttons"][button_name]["rect"].collidepoint(mouse_pos):
                        self.keyboard_active = False
                        self.confirm_dialog_selected_index = index
                        break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for index, button_name in enumerate(self._confirm_dialog_button_order()):
                    if self.confirm_dialog["buttons"][button_name]["rect"].collidepoint(mouse_pos):
                        self.confirm_dialog_selected_index = index
                        self._activate_confirm_dialog_button(button_name)
                        break
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
            mouse_pos = pygame.mouse.get_pos()
            hovered_item = self._interactive_mouse_target(mouse_pos)
            if hovered_item is not None:
                self.keyboard_active = False
                self.selected_index = self._main_menu_order().index(hovered_item)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_scene = "menu"
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.keyboard_active = True
                if not self._move_button_selection("up"):
                    self.selected_index = max(0, self.selected_index - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.keyboard_active = True
                if not self._move_button_selection("down"):
                    self.selected_index = min(len(self._main_menu_order()) - 1, self.selected_index + 1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.keyboard_active = True
                selected_item = self._selected_main_item()
                if selected_item in self.sliders:
                    self._adjust_slider(selected_item, -SETTINGS_SLIDER_STEP_COARSE)
                else:
                    self._move_button_selection("left")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.keyboard_active = True
                selected_item = self._selected_main_item()
                if selected_item in self.sliders:
                    self._adjust_slider(selected_item, SETTINGS_SLIDER_STEP_COARSE)
                else:
                    self._move_button_selection("right")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                selected_item = self._selected_main_item()
                if selected_item in self.buttons:
                    self._activate_button(selected_item)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for index, item_name in enumerate(self._main_menu_order()):
                if item_name in self.sliders:
                    slider_data = self.sliders[item_name]
                    if slider_data["handle_rect"].collidepoint(mouse_pos):
                        self.selected_index = index
                        self.dragging_slider = item_name
                        return
            for index, item_name in enumerate(self._main_menu_order()):
                if item_name in self.buttons and self.buttons[item_name]["rect"].collidepoint(mouse_pos):
                    self.selected_index = index
                    self._activate_button(item_name)
                    return

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider:
                mouse_x, _ = event.pos
                slider = self.sliders[self.dragging_slider]
                track  = slider["rect"]
                new_x     = max(track.left, min(mouse_x, track.right))
                new_fraction = (new_x - track.left) / track.width
                new_value = self._slider_value_from_fraction(self.dragging_slider, new_fraction)
                self._set_slider_value(self.dragging_slider, new_value)

    def update(self, dt: float):
        self._update_slider_controller_adjustment(dt)

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
            slider_index = self._main_menu_order().index(slider_name)
            highlighted = track.collidepoint(mouse_pos) or handle.collidepoint(mouse_pos) or (
                self.keyboard_active and slider_index == self.selected_index
            )

            # Label centered above track
            label_color = GOLD if highlighted else LABEL_COLOR
            lbl = self.font_label.render(slider_data["label"], True, label_color)
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
            if highlighted:
                pygame.draw.rect(screen, GOLD, track.inflate(12, 12), 2, border_radius=10)
                pygame.draw.rect(screen, GOLD, handle.inflate(8, 8), 2, border_radius=8)

            # Percentage value to the right of track
            pct_color = GOLD if highlighted else TEXT_COLOR
            if slider_name == "fps_cap":
                value_text = f"{int(slider_data['value'])} FPS"
            else:
                value_text = f"{round(slider_data['value'] * 100)}%"
            pct = self.font_label.render(value_text, True, pct_color)
            screen.blit(pct, (track.right + SETTINGS_SLIDER_VALUE_X_OFFSET, track.centery - pct.get_height() // 2))

        # Buttons
        for i, item_name in enumerate(self._main_menu_order()):
            if item_name not in self.buttons:
                continue
            btn = self.buttons[item_name]
            rect = btn["rect"]
            highlighted = rect.collidepoint(mouse_pos) or (self.keyboard_active and i == self.selected_index)
            pygame.draw.rect(screen, BUTTON_HIGHLIGHT if highlighted else BUTTON_COLOR, rect, border_radius=6)
            pygame.draw.rect(screen, GOLD, rect, 2, border_radius=6)
            text_surf = self.font_button.render(btn["text"], True, TEXT_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                    rect.centery - text_surf.get_height() // 2))

        hint_surface = self.font_small.render(self._controller_hint_text(), True, LABEL_COLOR)
        screen.blit(
            hint_surface,
            (cx - hint_surface.get_width() // 2, SCREEN_HEIGHT - 32),
        )

        # Confirm dialog
        if self.confirm_dialog_open:
            dialog = self.confirm_dialog
            pygame.draw.rect(screen, CONFIRM_BG,  dialog["rect"], border_radius=8)
            pygame.draw.rect(screen, GOLD, dialog["rect"], 2, border_radius=8)

            msg = self.font_label.render(dialog["text"], True, TEXT_COLOR)
            screen.blit(msg, (dialog["rect"].centerx - msg.get_width() // 2,
                              dialog["rect"].top + 24))

            for index, button_name in enumerate(self._confirm_dialog_button_order()):
                btn_data = dialog["buttons"][button_name]
                rect = btn_data["rect"]
                highlighted = rect.collidepoint(mouse_pos) or (
                    self.keyboard_active and index == self.confirm_dialog_selected_index
                )
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
