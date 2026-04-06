import pygame
import math
import textwrap
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, TITLE_FONT_SIZE,
    CONTROLLER_AXIS_REPEAT_DELAY, CONTROLLER_AXIS_REPEAT_RATE,
)
from src.utils.input_manager import InputManager


class UpgradeMenu:
    def __init__(self, choices: list[dict], upgrade_system, player):
        self.choices = choices
        self.upgrade_system = upgrade_system
        self.player = player
        self.selected = -1
        self.hovered = 0  # shared mouse/keyboard highlight index
        self.keyboard_active = False
        self.done = False

        # Card layout parameters
        self.card_width = 260
        self.card_height = 360
        self.gap = 30
        self.start_x = (SCREEN_WIDTH - (3 * self.card_width + 2 * self.gap)) // 2

        # Cached surfaces and fonts
        self._overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))
        self.font_title = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        self.font_card_name = pygame.font.SysFont("serif", 24)
        self.font_desc = pygame.font.SysFont("serif", 14)
        self.font_symbol = pygame.font.SysFont("serif", 36)
        self.font_hint = pygame.font.SysFont("serif", 16)
        self._controller_nav_dir = 0
        self._controller_nav_timer = 0.0
        self._controller_confirm_was_pressed = False

    def _input_config(self) -> dict | None:
        slot = getattr(self.player, "slot", None)
        return None if slot is None else slot.input_config

    def _resolved_controller_id(self) -> int | None:
        cfg = self._input_config()
        if cfg is None or cfg.get("type") != "controller":
            return None

        input_manager = InputManager.instance()
        joystick_id = input_manager.resolve_joystick_id(
            cfg.get("joystick_id"),
            profile_key=cfg.get("profile_key"),
            guid=cfg.get("guid"),
            name=cfg.get("name"),
        )
        if joystick_id is not None and joystick_id != cfg.get("joystick_id"):
            self.player.slot.input_config = input_manager.build_controller_input_config(joystick_id)
        return joystick_id

    def _controller_reconnect_candidate_ids(self) -> list[int]:
        cfg = self._input_config()
        if cfg is None or cfg.get("type") != "controller":
            return []

        return InputManager.instance().get_reconnect_candidate_ids(
            joystick_id=cfg.get("joystick_id"),
            profile_key=cfg.get("profile_key"),
            guid=cfg.get("guid"),
            name=cfg.get("name"),
        )

    def _try_reclaim_controller(self, event: pygame.event.Event) -> bool:
        cfg = self._input_config()
        if cfg is None or cfg.get("type") != "controller":
            return False

        input_manager = InputManager.instance()
        if self._resolved_controller_id() is not None:
            return False
        if event.instance_id not in self._controller_reconnect_candidate_ids():
            return False

        if not (
            input_manager.button_matches("confirm", event.button, joystick_id=event.instance_id)
            or input_manager.button_matches("start", event.button, joystick_id=event.instance_id)
        ):
            return False

        self.player.slot.input_config = input_manager.build_controller_input_config(event.instance_id)
        self._controller_nav_dir = 0
        self._controller_nav_timer = 0.0
        self._controller_confirm_was_pressed = False
        return True

    def _mouse_input_enabled(self) -> bool:
        """Keep mouse upgrade selection as a solo-only compatibility path."""
        return not getattr(self.player, "supports_revive", False)

    def _solo_owned_keyboard_confirm_keys(self) -> set[int]:
        if not getattr(self.player, "supports_revive", False):
            return {pygame.K_RETURN, pygame.K_KP_ENTER}
        return set()

    def _keyboard_hint_text(self) -> str:
        cfg = self._input_config()
        if cfg is None:
            return "1 / 2 / 3, Arrow keys, A/D, or click  -  Enter confirms"

        if cfg["type"] != "keyboard":
            return "Use the owning input device to choose and confirm"

        if cfg.get("scheme") == "wasd":
            if not getattr(self.player, "supports_revive", False):
                return "A/D to choose  -  Enter confirms"
            return "A/D to choose  -  Space confirms"

        if cfg.get("scheme") == "arrows":
            return "Left/Right to choose  -  Enter confirms"

        return "Use your assigned keyboard controls to choose and confirm"

    def _controller_hint_text(self) -> str:
        cfg = self._input_config()
        if cfg is not None and cfg["type"] == "controller":
            joystick_id = self._resolved_controller_id()
            cfg = self._input_config()
            if joystick_id is None:
                return (
                    "Controller disconnected"
                    f"  -  reconnect and press {InputManager.instance().describe_help_binding('confirm')} or {InputManager.instance().describe_help_binding('start')} to reclaim"
                )
            return (
                f"Controller {joystick_id + 1}: stick or D-pad to choose"
                f"  -  {InputManager.instance().describe_help_binding('confirm')} confirms"
            )
        return "Choose and confirm with the owning input device"

    def _keyboard_event_matches_owner(self, event: pygame.event.Event) -> bool:
        cfg = self._input_config()

        # Owned multiplayer menus must not trust synthetic controller KEYDOWNs;
        # they can bleed into keyboard-owned upgrade selection.
        if getattr(event, "synthetic_controller_event", False):
            return False

        if cfg is None:
            return event.key in {
                pygame.K_LEFT,
                pygame.K_RIGHT,
                pygame.K_a,
                pygame.K_d,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_1,
                pygame.K_2,
                pygame.K_3,
            }

        if cfg["type"] != "keyboard":
            return False

        keys = cfg["keys"]
        return event.key in {
            keys["left"],
            keys["right"],
            keys["confirm"],
        } | self._solo_owned_keyboard_confirm_keys()

    def _handle_keyboard_event(self, event: pygame.event.Event) -> None:
        if not self._keyboard_event_matches_owner(event):
            return

        cfg = self._input_config()
        if cfg is None or cfg["type"] != "keyboard":
            left_keys = {pygame.K_LEFT, pygame.K_a}
            right_keys = {pygame.K_RIGHT, pygame.K_d}
            confirm_keys = {pygame.K_RETURN, pygame.K_KP_ENTER}
        else:
            keys = cfg["keys"]
            left_keys = {keys["left"]}
            right_keys = {keys["right"]}
            confirm_keys = {keys["confirm"]} | self._solo_owned_keyboard_confirm_keys()

        if event.key in left_keys:
            self.keyboard_active = True
            self.hovered = max(0, self.hovered - 1)
        elif event.key in right_keys:
            self.keyboard_active = True
            self.hovered = min(len(self.choices) - 1, self.hovered + 1)
        elif event.key in confirm_keys:
            self._apply_choice(self.hovered)
            self.done = True
        elif cfg is None and event.key == pygame.K_1:
            self._apply_choice(0)
            self.done = True
        elif cfg is None and event.key == pygame.K_2:
            self._apply_choice(1)
            self.done = True
        elif cfg is None and event.key == pygame.K_3:
            self._apply_choice(2)
            self.done = True

    def _handle_controller_button(self, event: pygame.event.Event) -> None:
        cfg = self._input_config()
        if cfg is None or cfg["type"] != "controller":
            return
        input_manager = InputManager.instance()
        joystick_id = self._resolved_controller_id()
        if joystick_id is None:
            self._try_reclaim_controller(event)
            return
        if event.instance_id != joystick_id:
            return
        if input_manager.button_matches("confirm", event.button, joystick_id=event.instance_id):
            self._apply_choice(self.hovered)
            self.done = True

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEMOTION and self._mouse_input_enabled():
                self.keyboard_active = False
                self.hovered = -1
                for i in range(3):
                    card_rect = pygame.Rect(self.start_x + i * (self.card_width + self.gap), 150, self.card_width, self.card_height)
                    if card_rect.collidepoint(mouse_pos):
                        self.hovered = i
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and self._mouse_input_enabled():
                if event.button == 1:  # Left mouse button
                    # Check if a card was clicked
                    for i in range(3):
                        card_rect = pygame.Rect(self.start_x + i * (self.card_width + self.gap), 150, self.card_width, self.card_height)
                        if card_rect.collidepoint(mouse_pos):
                            self._apply_choice(i)
                            self.done = True
                            return

            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard_event(event)
                if self.done:
                    return

            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_controller_button(event)
                if self.done:
                    return

    def _apply_choice(self, index):
        """Apply the chosen upgrade."""
        if 0 <= index < len(self.choices):
            self.upgrade_system.apply_choice(self.choices[index], self.player)

    def update(self, dt):
        """Update the upgrade menu state."""
        cfg = self._input_config()
        if cfg is None or cfg["type"] != "controller":
            return

        input_manager = InputManager.instance()
        joystick_id = self._resolved_controller_id()
        if joystick_id is None:
            self._controller_nav_dir = 0
            self._controller_nav_timer = 0.0
            self._controller_confirm_was_pressed = False
            return

        new_dir, _unused_y = input_manager.get_menu_navigation_for_joystick(
            joystick_id
        )

        if new_dir != self._controller_nav_dir:
            self._controller_nav_dir = new_dir
            if new_dir != 0:
                self._controller_nav_timer = CONTROLLER_AXIS_REPEAT_DELAY
                self.hovered = max(0, min(len(self.choices) - 1, self.hovered + new_dir))
            else:
                self._controller_nav_timer = 0.0
        elif new_dir != 0:
            self._controller_nav_timer -= dt
            if self._controller_nav_timer <= 0.0:
                self._controller_nav_timer += CONTROLLER_AXIS_REPEAT_RATE
                self.hovered = max(0, min(len(self.choices) - 1, self.hovered + new_dir))

        confirm_pressed = input_manager.get_confirm_for_joystick(joystick_id)
        if confirm_pressed and not self._controller_confirm_was_pressed:
            self._apply_choice(self.hovered)
            self.done = True
        self._controller_confirm_was_pressed = confirm_pressed

    def draw(self, screen):
        """Draw the upgrade menu overlay."""
        # 1. Semi-transparent dark overlay covering entire screen (alpha=160)
        screen.blit(self._overlay, (0, 0))

        # 2. "LEVEL UP!" text centered at top (y=80), large, GOLD, with pulse animation
        #    (scale the text size slightly with sin(pygame.time.get_ticks()/300))
        pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2  # Value between 0 and 1
        scale = 1.0 + pulse * 0.1  # Scale from 1.0 to 1.1
        slot = getattr(self.player, "slot", None)
        if slot is None:
            text = "LEVEL UP!"
        else:
            text = f"PLAYER {slot.index + 1} LEVEL UP!"
        text_surface = self.font_title.render(text, True, GOLD)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))

        # Apply scaling effect
        scaled_surface = pygame.transform.scale(text_surface,
                                               (int(text_rect.width * scale), int(text_rect.height * scale)))
        scaled_rect = scaled_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(scaled_surface, scaled_rect)

        # 3. For each card:

        for i, choice in enumerate(self.choices):
            # Calculate card position
            x = self.start_x + i * (self.card_width + self.gap)
            y = 150

            # Create card surface with scaling effect
            card_surface = pygame.Surface((self.card_width, self.card_height), pygame.SRCALPHA)

            # Scale up 3% on mouse hover or keyboard selection
            scale_factor = 1.03 if i == self.hovered else 1.0
            scaled_width = int(self.card_width * scale_factor)
            scaled_height = int(self.card_height * scale_factor)

            # Draw card background
            card_rect = pygame.Rect(0, 0, self.card_width, self.card_height)
            pygame.draw.rect(card_surface, (35, 30, 50), card_rect)  # Dark stone background

            # Top icon area (top 100px): filled with choice["icon_color"] or weapon color
            # with weapon initial or stat symbol centered
            icon_height = 100
            icon_rect = pygame.Rect(0, 0, self.card_width, icon_height)
            pygame.draw.rect(card_surface, choice.get("icon_color", (100, 100, 100)), icon_rect)

            # Draw weapon initial or stat symbol
            symbol_text = ""
            if "weapon_class" in choice:
                symbol_text = choice.get("symbol", choice["weapon_class"][:2])
            elif "stat" in choice:
                # Simple stat symbol based on stat type
                stat_symbols = {
                    "max_hp": "+HP",
                    "speed_pct": "SPD",
                    "pickup_radius_pct": "RNG",
                    "armor": "ARM",
                    "regen_rate": "REG",
                    "xp_multiplier_pct": "XP",
                    "cooldown_reduction": "CD",
                    "crit_chance": "CRIT",
                    "spell_damage_multiplier_pct": "SPL"
                }
                symbol_text = stat_symbols.get(choice["stat"], "?")

            if symbol_text:
                symbol_surface = self.font_symbol.render(symbol_text, True, (255, 255, 255))
                symbol_rect = symbol_surface.get_rect(center=(self.card_width // 2, icon_height // 2))
                card_surface.blit(symbol_surface, symbol_rect)

            # Upgrade name in bold centered in middle section
            name_y = icon_height + 20
            name = choice.get("name", "Upgrade")
            name_surface = self.font_card_name.render(name, True, (255, 255, 255))
            name_rect = name_surface.get_rect(center=(self.card_width // 2, name_y))
            card_surface.blit(name_surface, name_rect)

            # Description text (word-wrapped) in lower section
            desc_y = name_y + 40
            description = choice.get("description", "No description available")
            wrapped_text = textwrap.wrap(description, width=30)

            for j, line in enumerate(wrapped_text):
                line_surface = self.font_desc.render(line, True, (200, 200, 200))
                line_rect = line_surface.get_rect(center=(self.card_width // 2, desc_y + j * 20))
                card_surface.blit(line_surface, line_rect)

            # Gold border (2px normally, 4px when hovered)
            border_width = 4 if i == self.hovered else 2
            pygame.draw.rect(card_surface, (255, 215, 0),
                           (0, 0, self.card_width, self.card_height), border_width)

            # Apply scaling to card surface
            if scale_factor != 1.0:
                scaled_card = pygame.transform.scale(card_surface, (scaled_width, scaled_height))
                screen.blit(scaled_card, (x + (self.card_width - scaled_width) // 2, y + (self.card_height - scaled_height) // 2))
            else:
                screen.blit(card_surface, (x, y))

        # 4. Hint text at bottom
        cfg = self._input_config()
        if cfg is None:
            hint_text = self._keyboard_hint_text()
        elif cfg["type"] == "keyboard":
            hint_text = self._keyboard_hint_text()
        elif cfg["type"] == "controller":
            hint_text = self._controller_hint_text()
        else:
            hint_text = "Choose and confirm with the owning input device"
        hint_surface = self.font_hint.render(hint_text, True, (200, 200, 200))
        screen.blit(hint_surface, (SCREEN_WIDTH // 2 - hint_surface.get_width() // 2, SCREEN_HEIGHT - 40))
