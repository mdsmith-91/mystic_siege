import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, MAX_PLAYERS, PLAYER_COLORS,
    HERO_CLASSES,
    KEYBOARD_WASD_BINDINGS, KEYBOARD_ARROW_BINDINGS,
    STATE_CLASS_SELECT, STATE_MENU,
)
from src.core.player_slot import PlayerSlot
from src.utils.input_manager import InputManager

_WASD_CONFIG: dict = {
    "type": "keyboard",
    "scheme": "wasd",
    "keys": dict(KEYBOARD_WASD_BINDINGS),
}
_ARROW_CONFIG: dict = {
    "type": "keyboard",
    "scheme": "arrows",
    "keys": dict(KEYBOARD_ARROW_BINDINGS),
}

_WASD_KEYS: frozenset = frozenset({pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d})
_ARROW_KEYS: frozenset = frozenset({pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT})

_FLASH_DURATION = 2.0   # seconds a flash message stays visible


class LobbyScene:
    """Lobby that handles join/leave, input-device assignment, and run start.

    Produces a list[PlayerSlot] passed to ClassSelect.
    Supports 1–4 players joining with keyboard (WASD / Arrows) or controllers.
    """

    def __init__(self) -> None:
        self.next_scene: str | None = None
        self.next_scene_kwargs: dict = {}

        # 4 slots; None = empty
        self.slots: list[PlayerSlot | None] = [None] * MAX_PLAYERS

        self.flash_message: str | None = None
        self.flash_timer: float = 0.0

        self.font_title = pygame.font.SysFont("serif", 48)
        self.font_large = pygame.font.SysFont("serif", 28)
        self.font_medium = pygame.font.SysFont("serif", 20)
        self.font_small = pygame.font.SysFont("serif", 16)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _slot_index_for_device(self, input_config: dict) -> int | None:
        """Return the slot index that owns this device, or None."""
        for i, slot in enumerate(self.slots[:self._supported_player_count()]):
            if slot is None:
                continue
            ic = slot.input_config
            if ic is None:
                continue
            if ic.get("type") == "keyboard" and input_config.get("type") == "keyboard":
                if ic.get("scheme") == input_config.get("scheme"):
                    return i
            elif ic.get("type") == "controller" and input_config.get("type") == "controller":
                if ic.get("joystick_id") == input_config.get("joystick_id"):
                    return i
        return None

    def _next_open_index(self) -> int | None:
        """Return the lowest empty slot index, or None if all full."""
        for i, slot in enumerate(self.slots[:self._supported_player_count()]):
            if slot is None:
                return i
        return None

    def _supported_player_count(self) -> int:
        return min(MAX_PLAYERS, len(HERO_CLASSES))

    def _flash(self, message: str) -> None:
        self.flash_message = message
        self.flash_timer = _FLASH_DURATION

    def _try_join(self, input_config: dict) -> None:
        """Toggle join/leave for the given device.

        If the device already owns a slot → vacate it.
        If not → claim the next open slot (or flash "Lobby is full").
        """
        existing = self._slot_index_for_device(input_config)
        if existing is not None:
            # Same device pressed again → leave
            self.slots[existing] = None
            return

        idx = self._next_open_index()
        if idx is None:
            self._flash(
                f"Current build supports up to {self._supported_player_count()} players "
                f"({len(HERO_CLASSES)} heroes available)"
            )
            return

        self.slots[idx] = PlayerSlot(
            index=idx,
            input_config=input_config,
            hero_data=None,
            color=PLAYER_COLORS[idx],
        )

    def _start_game(self) -> None:
        """Begin the run with all currently joined slots."""
        self._prune_disconnected_controllers()
        filled = [s for s in self.slots if s is not None]
        if not filled:
            return
        self.next_scene = STATE_CLASS_SELECT
        self.next_scene_kwargs = {"slots": filled}

    def _prune_disconnected_controllers(self) -> None:
        """Drop any controller-owned slot whose claimed joystick is no longer connected."""
        input_manager = InputManager.instance()
        removed_slots: list[int] = []
        for index, slot in enumerate(self.slots):
            if slot is None or slot.input_config is None:
                continue
            if slot.input_config.get("type") != "controller":
                continue
            joystick_id = slot.input_config.get("joystick_id")
            if input_manager.is_joystick_connected(joystick_id):
                continue
            self.slots[index] = None
            removed_slots.append(index)

        if removed_slots:
            removed_labels = ", ".join(f"P{index + 1}" for index in removed_slots)
            self._flash(f"Disconnected controller removed from {removed_labels}")

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def handle_events(self, events: list) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                return

            elif event.type == pygame.KEYDOWN:
                if getattr(event, "synthetic_controller_event", False):
                    # Controller-owned lobby actions are handled via JOYBUTTONDOWN,
                    # so synthetic controller key events must not claim keyboard
                    # schemes or trigger menu-level back/start behavior here.
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.next_scene = STATE_MENU
                    return
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._start_game()
                elif event.key in _WASD_KEYS:
                    self._try_join(dict(_WASD_CONFIG))
                elif event.key in _ARROW_KEYS:
                    self._try_join(dict(_ARROW_CONFIG))

            elif event.type == pygame.JOYDEVICEREMOVED:
                self._prune_disconnected_controllers()

            elif event.type == pygame.JOYBUTTONDOWN:
                input_manager = InputManager.instance()
                ic = input_manager.build_controller_input_config(event.instance_id)
                if input_manager.button_matches("back", event.button, joystick_id=event.instance_id):
                    # B / Circle — leave slot or go back to menu
                    existing = self._slot_index_for_device(ic)
                    if existing is not None:
                        self.slots[existing] = None
                    else:
                        self.next_scene = STATE_MENU
                elif input_manager.button_matches("confirm", event.button, joystick_id=event.instance_id):
                    # A / Cross — join or leave
                    self._try_join(ic)
                elif input_manager.button_matches("start", event.button, joystick_id=event.instance_id):
                    # Start / Options only begins the run for an already joined device.
                    if self._slot_index_for_device(ic) is not None:
                        self._start_game()

    def update(self, dt: float) -> None:
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_message = None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((15, 10, 25))

        # Title
        title_surf = self.font_title.render("LOBBY", True, GOLD)
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 30))

        input_manager = InputManager.instance()
        confirm_label = input_manager.describe_binding("confirm")
        back_label = input_manager.describe_binding("back")
        start_label = input_manager.describe_binding("start")

        # Instructions
        inst = f"Press WASD, Arrow keys, or controller {confirm_label} to join or leave"
        inst_surf = self.font_small.render(inst, True, (150, 150, 150))
        screen.blit(inst_surf, (SCREEN_WIDTH // 2 - inst_surf.get_width() // 2, 92))

        # 2×2 slot grid
        slot_w, slot_h = 560, 200
        gap = 30
        grid_w = slot_w * 2 + gap
        grid_x = (SCREEN_WIDTH - grid_w) // 2
        grid_y = 120

        positions = [
            (grid_x,              grid_y),
            (grid_x + slot_w + gap, grid_y),
            (grid_x,              grid_y + slot_h + gap),
            (grid_x + slot_w + gap, grid_y + slot_h + gap),
        ]

        for i in range(MAX_PLAYERS):
            px, py = positions[i]
            rect = pygame.Rect(px, py, slot_w, slot_h)
            slot = self.slots[i]
            supported = i < self._supported_player_count()

            if not supported:
                pygame.draw.rect(screen, (18, 18, 24), rect)
                pygame.draw.rect(screen, (55, 55, 65), rect, 2)
                p_surf = self.font_medium.render(f"PLAYER {i + 1}", True, (90, 90, 100))
                screen.blit(p_surf, (px + slot_w // 2 - p_surf.get_width() // 2, py + 52))
                limit_surf = self.font_small.render("Unavailable in current build", True, (130, 120, 120))
                screen.blit(limit_surf, (px + slot_w // 2 - limit_surf.get_width() // 2, py + 92))
                hero_surf = self.font_small.render("Need more unique heroes", True, (110, 100, 110))
                screen.blit(hero_surf, (px + slot_w // 2 - hero_surf.get_width() // 2, py + 118))
            elif slot is not None:
                # Filled slot
                pygame.draw.rect(screen, (30, 25, 40), rect)
                pygame.draw.rect(screen, slot.color, rect, 3)

                num_surf = self.font_large.render(f"PLAYER {i + 1}", True, slot.color)
                screen.blit(num_surf, (px + slot_w // 2 - num_surf.get_width() // 2, py + 28))

                ic = slot.input_config
                if ic["type"] == "keyboard":
                    device_label = f"Keyboard ({ic['scheme'].upper()})"
                else:
                    device_label = f"Controller {ic['joystick_id'] + 1}"
                dev_surf = self.font_medium.render(device_label, True, (200, 200, 200))
                screen.blit(dev_surf, (px + slot_w // 2 - dev_surf.get_width() // 2, py + 80))

                ready_surf = self.font_large.render("READY", True, (80, 220, 80))
                screen.blit(ready_surf, (px + slot_w // 2 - ready_surf.get_width() // 2, py + 122))

                hint_surf = self.font_small.render("Press same key/button to leave", True, (110, 100, 120))
                screen.blit(hint_surf, (px + slot_w // 2 - hint_surf.get_width() // 2, py + 168))
            else:
                # Empty slot
                pygame.draw.rect(screen, (20, 15, 25), rect)
                pygame.draw.rect(screen, (60, 50, 80), rect, 2)

                p_surf = self.font_medium.render(f"PLAYER {i + 1}", True, (80, 70, 100))
                screen.blit(p_surf, (px + slot_w // 2 - p_surf.get_width() // 2, py + 60))

                join_surf = self.font_small.render("Press key or button to join", True, (100, 90, 120))
                screen.blit(join_surf, (px + slot_w // 2 - join_surf.get_width() // 2, py + 100))

        # Start prompt — only shown when ≥1 slot is filled
        filled_count = sum(1 for s in self.slots if s is not None)
        if filled_count > 0:
            start_surf = self.font_medium.render(
                f"Press Enter or controller {start_label} to begin", True, GOLD
            )
            screen.blit(start_surf, (SCREEN_WIDTH // 2 - start_surf.get_width() // 2, 600))

        if self._supported_player_count() < MAX_PLAYERS:
            limit_surf = self.font_small.render(
                f"Current runtime cap: {self._supported_player_count()} players with unique heroes",
                True,
                (150, 140, 140),
            )
            screen.blit(limit_surf, (SCREEN_WIDTH // 2 - limit_surf.get_width() // 2, 624))

        # Flash message
        if self.flash_message:
            flash_surf = self.font_large.render(self.flash_message, True, (255, 80, 80))
            screen.blit(flash_surf, (SCREEN_WIDTH // 2 - flash_surf.get_width() // 2, 648))

        # Back hint
        back_surf = self.font_small.render(
            f"ESC or controller {back_label} - Back to Menu",
            True,
            (100, 100, 100),
        )
        screen.blit(back_surf, (20, SCREEN_HEIGHT - 28))
