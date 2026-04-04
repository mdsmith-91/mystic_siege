import pygame
from settings import (CONTROLLER_DEADZONE, CONTROLLER_AXIS_REPEAT_DELAY,
                       CONTROLLER_AXIS_REPEAT_RATE)


class InputManager:
    """Singleton that bridges controller input to the rest of the game.

    Menus use pygame.KEYDOWN events — this class posts synthetic ones so no
    menu code needs to change.  Player movement reads get_movement() directly
    to get smooth analog values.

    Mapping (Xbox / PS style):
      Left stick axes 0/1  → player movement + menu navigation (with repeat)
      D-pad (HAT 0)        → menu navigation (discrete, change-only)
      Button 0  (A / Cross)        → K_RETURN  (confirm)
      Button 1  (B / Circle)       → K_ESCAPE  (back)
      Button 7  (Start / Options)  → K_ESCAPE  (pause)
      Button 9  (alt Start)        → K_ESCAPE  (pause on some pads)
    """

    _instance: "InputManager | None" = None

    @classmethod
    def instance(cls) -> "InputManager":
        if cls._instance is None:
            cls._instance = InputManager()
        return cls._instance

    def __init__(self) -> None:
        self._joysticks: dict[int, pygame.joystick.Joystick] = {}
        # Axis-based navigation: (instance_id, axis_index) -> current direction (-1, 0, 1)
        self._axis_dir: dict[tuple[int, int], int] = {}
        # Countdown until the next repeat event fires
        self._axis_timer: dict[tuple[int, int], float] = {}
        # Previous D-pad (HAT) value per joystick
        self._hat_state: dict[tuple[int, int], tuple[int, int]] = {}
        # Previous button-pressed state for edge detection
        self._button_state: dict[tuple[int, int], bool] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> None:
        """Enumerate joysticks already connected at startup."""
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            self._joysticks[joy.get_instance_id()] = joy

    def update(self, dt: float, events: list) -> None:
        """Process events and tick controller state.  Call once per frame."""
        for event in events:
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                self._joysticks[joy.get_instance_id()] = joy
            elif event.type == pygame.JOYDEVICEREMOVED:
                iid = event.instance_id
                self._joysticks.pop(iid, None)
                self._axis_dir   = {k: v for k, v in self._axis_dir.items()   if k[0] != iid}
                self._axis_timer = {k: v for k, v in self._axis_timer.items() if k[0] != iid}
                self._hat_state  = {k: v for k, v in self._hat_state.items()  if k[0] != iid}
                self._button_state = {k: v for k, v in self._button_state.items() if k[0] != iid}

        for joy in self._joysticks.values():
            self._process_axes(joy, dt)
            self._process_hats(joy)
            self._process_buttons(joy)

    def get_movement(self) -> tuple[float, float]:
        """Analog movement vector (dx, dy) from the first active left stick.

        Values in [-1, 1] with deadzone applied.  Returns (0.0, 0.0) when no
        controller is connected or the stick is centered.
        """
        for joy in self._joysticks.values():
            if joy.get_numaxes() < 2:
                continue
            x = joy.get_axis(0)
            y = joy.get_axis(1)
            x = x if abs(x) >= CONTROLLER_DEADZONE else 0.0
            y = y if abs(y) >= CONTROLLER_DEADZONE else 0.0
            if x != 0.0 or y != 0.0:
                return (x, y)
        return (0.0, 0.0)

    def get_movement_for_joystick(self, joystick_id: int) -> tuple[float, float]:
        """Analog movement vector for a specific joystick instance ID.

        Values in [-1, 1] with deadzone applied.  Returns (0.0, 0.0) if the
        joystick is not connected or the stick is centered.
        """
        joy = self._joysticks.get(joystick_id)
        if joy is None or joy.get_numaxes() < 2:
            return (0.0, 0.0)
        x = joy.get_axis(0)
        y = joy.get_axis(1)
        x = x if abs(x) >= CONTROLLER_DEADZONE else 0.0
        y = y if abs(y) >= CONTROLLER_DEADZONE else 0.0
        return (x, y)

    def get_confirm_for_joystick(self, joystick_id: int) -> bool:
        """Return True if button 0 (A / Cross) is currently pressed on the given joystick."""
        joy = self._joysticks.get(joystick_id)
        if joy is None or joy.get_numbuttons() == 0:
            return False
        return bool(joy.get_button(0))

    def get_connected_joysticks(self) -> list[int]:
        """Return a list of currently connected joystick instance IDs."""
        return list(self._joysticks.keys())

    @property
    def connected(self) -> bool:
        """True if at least one controller is connected."""
        return bool(self._joysticks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_axes(self, joy: pygame.joystick.Joystick, dt: float) -> None:
        """Post navigation KEYDOWN events from the left analog stick with repeat."""
        iid = joy.get_instance_id()
        # axis index → (negative key, positive key)
        nav_map: dict[int, tuple[int, int]] = {
            0: (pygame.K_LEFT, pygame.K_RIGHT),
            1: (pygame.K_UP,   pygame.K_DOWN),
        }
        for axis_idx, (neg_key, pos_key) in nav_map.items():
            if joy.get_numaxes() <= axis_idx:
                continue
            raw = joy.get_axis(axis_idx)
            if abs(raw) < CONTROLLER_DEADZONE:
                new_dir = 0
            elif raw < 0:
                new_dir = -1
            else:
                new_dir = 1

            state_key = (iid, axis_idx)
            prev_dir = self._axis_dir.get(state_key, 0)

            if new_dir != prev_dir:
                # Direction changed
                self._axis_dir[state_key] = new_dir
                if new_dir != 0:
                    # Post immediately on first entry, then arm the repeat timer
                    self._axis_timer[state_key] = CONTROLLER_AXIS_REPEAT_DELAY
                    self._post_key(neg_key if new_dir < 0 else pos_key)
                else:
                    self._axis_timer.pop(state_key, None)
            elif new_dir != 0:
                # Still held — tick the repeat countdown
                timer = self._axis_timer.get(state_key, 0.0) - dt
                if timer <= 0.0:
                    timer += CONTROLLER_AXIS_REPEAT_RATE
                    self._post_key(neg_key if new_dir < 0 else pos_key)
                self._axis_timer[state_key] = timer

    def _process_hats(self, joy: pygame.joystick.Joystick) -> None:
        """Post navigation KEYDOWN events from the D-pad (HAT) on direction change."""
        iid = joy.get_instance_id()
        for hat_idx in range(joy.get_numhats()):
            hx, hy = joy.get_hat(hat_idx)
            state_key = (iid, hat_idx)
            prev_hx, prev_hy = self._hat_state.get(state_key, (0, 0))
            if (hx, hy) == (prev_hx, prev_hy):
                continue
            self._hat_state[state_key] = (hx, hy)
            # pygame HAT y: +1 = up, -1 = down (opposite of screen-space)
            if hx == -1:
                self._post_key(pygame.K_LEFT)
            elif hx == 1:
                self._post_key(pygame.K_RIGHT)
            if hy == 1:
                self._post_key(pygame.K_UP)
            elif hy == -1:
                self._post_key(pygame.K_DOWN)

    def _process_buttons(self, joy: pygame.joystick.Joystick) -> None:
        """Post KEYDOWN/KEYUP events for mapped buttons on state change."""
        button_map: dict[int, int] = {
            0: pygame.K_RETURN,   # A / Cross  → confirm
            1: pygame.K_ESCAPE,   # B / Circle → back / cancel
            7: pygame.K_ESCAPE,   # Start / Options → pause
            9: pygame.K_ESCAPE,   # Alternate Start mapping on some pads
        }
        iid = joy.get_instance_id()
        for btn_idx, mapped_key in button_map.items():
            if joy.get_numbuttons() <= btn_idx:
                continue
            pressed = bool(joy.get_button(btn_idx))
            state_key = (iid, btn_idx)
            was_pressed = self._button_state.get(state_key, False)
            if pressed and not was_pressed:
                self._post_key(mapped_key)
            elif not pressed and was_pressed:
                self._post_keyup(mapped_key)
            self._button_state[state_key] = pressed

    @staticmethod
    def _post_key(key: int) -> None:
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN,
            {"key": key, "mod": 0, "unicode": "", "scancode": 0},
        ))

    @staticmethod
    def _post_keyup(key: int) -> None:
        pygame.event.post(pygame.event.Event(
            pygame.KEYUP,
            {"key": key, "mod": 0, "unicode": "", "scancode": 0},
        ))
