import pygame
import textwrap
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HERO_CLASSES, TITLE_FONT_SIZE,
    STATE_MENU, STATE_CLASS_SELECT, STATE_PLAYING, STATE_LOBBY, PLAYER_COLORS,
    CONTROLLER_AXIS_REPEAT_DELAY, CONTROLLER_AXIS_REPEAT_RATE,
)
from src.core.player_slot import PlayerSlot
from src.utils.input_manager import InputManager

class ClassSelect:
    def __init__(
        self,
        slots: list[PlayerSlot] | None = None,
        confirmed_slots: list[PlayerSlot] | None = None,
    ):
        self.next_scene = None
        self.next_scene_kwargs = {}
        self.slots = list(slots or [])
        self.confirmed_slots = list(confirmed_slots or [])
        self.current_slot = self.slots[0] if self.slots else None
        self.slot_queue_active = self.current_slot is not None
        self.selected_class = None
        self.hovered_card = None
        self.nav_index = 0  # keyboard nav index for hero cards (0–2)
        self.keyboard_active = False
        self._controller_nav_dir = 0
        self._controller_nav_timer = 0.0

        self.font_title = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        self.font_large = pygame.font.SysFont("serif", 28)
        self.font_medium = pygame.font.SysFont("serif", 20)
        self.font_small = pygame.font.SysFont("serif", 16)

        initial_index = self._first_available_index()
        if self.slot_queue_active and initial_index is not None:
            self.nav_index = initial_index
            self.selected_class = HERO_CLASSES[initial_index]

    def _locked_hero_slots(self) -> dict[str, PlayerSlot]:
        locked: dict[str, PlayerSlot] = {}
        for slot in self.confirmed_slots:
            if slot.hero_data is not None:
                locked[slot.hero_data["name"]] = slot
        return locked

    def _is_hero_locked(self, hero: dict) -> bool:
        return hero["name"] in self._locked_hero_slots()

    def _first_available_index(self) -> int | None:
        for i, hero in enumerate(HERO_CLASSES):
            if not self._is_hero_locked(hero):
                return i
        return None

    def _move_selection(self, step: int) -> None:
        if self.selected_class is None:
            return

        for offset in range(1, len(HERO_CLASSES) + 1):
            next_index = (self.nav_index + step * offset) % len(HERO_CLASSES)
            if not self._is_hero_locked(HERO_CLASSES[next_index]):
                self.nav_index = next_index
                self.selected_class = HERO_CLASSES[next_index]
                return

    def _route_to_game_or_next_slot(self) -> None:
        if self.selected_class is None:
            return

        if not self.slot_queue_active:
            resolved_slot = PlayerSlot(
                index=0,
                input_config=None,
                hero_data=self.selected_class,
                color=PLAYER_COLORS[0],
            )
            self.next_scene = STATE_PLAYING
            self.next_scene_kwargs = {"slots": [resolved_slot]}
            return

        self.current_slot.hero_data = self.selected_class
        resolved_slots = self.confirmed_slots + [self.current_slot]
        remaining_slots = self.slots[1:]

        if remaining_slots:
            self.next_scene = STATE_CLASS_SELECT
            self.next_scene_kwargs = {
                "slots": remaining_slots,
                "confirmed_slots": resolved_slots,
            }
            return

        self.next_scene = STATE_PLAYING
        self.next_scene_kwargs = {"slots": resolved_slots}

    def _handle_back(self) -> None:
        self.next_scene = STATE_MENU if not self.slot_queue_active else STATE_LOBBY

    def _solo_owned_keyboard_confirm_keys(self) -> set[int]:
        total_slots = len(self.slots) + len(self.confirmed_slots)
        if total_slots == 1:
            return {pygame.K_RETURN, pygame.K_KP_ENTER}
        return set()

    def _keyboard_hint_text(self) -> str:
        if not self.slot_queue_active:
            return "Left/Right or A/D to choose  -  Enter or click confirms  -  ESC or Back click backs"

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "keyboard":
            return "Use your assigned controls or click  -  ESC backs"

        total_slots = len(self.slots) + len(self.confirmed_slots)
        if cfg.get("scheme") == "wasd":
            if total_slots == 1:
                return "A/D to choose  -  Enter or click confirms  -  ESC, Left Shift, or Back click backs"
            return "A/D to choose  -  Space or click confirms  -  ESC, Left Shift, or Back click backs"

        if cfg.get("scheme") == "arrows":
            return "Left/Right to choose  -  Enter or click confirms  -  ESC, Right Shift, or Back click backs"

        return "Use your assigned keyboard controls or click  -  ESC backs"

    def _controller_hint_text(self) -> str:
        cfg = self.current_slot.input_config
        if cfg is not None and cfg["type"] == "controller":
            return (
                f"Controller {cfg['joystick_id'] + 1}: stick or D-pad to choose"
                f"  -  A or click confirms  -  B, ESC, or Back click backs"
            )
        return "Use your assigned controls or click  -  ESC backs"

    def _keyboard_event_matches_current_slot(self, event: pygame.event.Event) -> bool:
        if not self.slot_queue_active:
            return True

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "keyboard":
            return False
        keys = cfg["keys"]
        return event.key in {
            keys["left"],
            keys["right"],
            keys["confirm"],
            keys["back"],
            pygame.K_ESCAPE,
        } | self._solo_owned_keyboard_confirm_keys()

    def _handle_keyboard_event(self, event: pygame.event.Event) -> None:
        if not self._keyboard_event_matches_current_slot(event):
            return

        if not self.slot_queue_active:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.keyboard_active = True
                self.nav_index = max(0, self.nav_index - 1)
                self.selected_class = HERO_CLASSES[self.nav_index]
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.keyboard_active = True
                self.nav_index = min(len(HERO_CLASSES) - 1, self.nav_index + 1)
                self.selected_class = HERO_CLASSES[self.nav_index]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._route_to_game_or_next_slot()
            elif event.key == pygame.K_ESCAPE:
                self._handle_back()
            return

        cfg = self.current_slot.input_config
        keys = cfg["keys"]
        confirm_keys = {keys["confirm"]} | self._solo_owned_keyboard_confirm_keys()
        if event.key == keys["left"]:
            self.keyboard_active = True
            self._move_selection(-1)
        elif event.key == keys["right"]:
            self.keyboard_active = True
            self._move_selection(1)
        elif event.key in confirm_keys:
            self._route_to_game_or_next_slot()
        elif event.key in {keys["back"], pygame.K_ESCAPE}:
            self._handle_back()

    def _handle_mouse_click(self, mouse_pos: tuple[int, int]) -> None:
        card_width = 260
        card_height = 380
        spacing = 40
        total_width = len(HERO_CLASSES) * card_width + (len(HERO_CLASSES) - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, hero in enumerate(HERO_CLASSES):
            card_rect = pygame.Rect(start_x + i * (card_width + spacing), 150, card_width, card_height)
            if card_rect.collidepoint(mouse_pos):
                self.selected_class = hero
                self.nav_index = i
                return

        if self.selected_class is not None:
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            if confirm_rect.collidepoint(mouse_pos):
                self._route_to_game_or_next_slot()
                return

        back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
        if back_rect.collidepoint(mouse_pos):
            self._handle_back()

    def _handle_controller_button(self, event: pygame.event.Event) -> None:
        if not self.slot_queue_active:
            return

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "controller":
            return
        if event.instance_id != cfg["joystick_id"]:
            return

        if event.button == 0:
            self._route_to_game_or_next_slot()
        elif event.button == 1:
            self._handle_back()

    def _poll_active_controller_navigation(self, dt: float) -> None:
        if not self.slot_queue_active:
            return

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "controller":
            return

        move_x, _move_y = InputManager.instance().get_movement_for_joystick(cfg["joystick_id"])
        if move_x <= -0.5:
            new_dir = -1
        elif move_x >= 0.5:
            new_dir = 1
        else:
            new_dir = 0

        if new_dir != self._controller_nav_dir:
            self._controller_nav_dir = new_dir
            if new_dir != 0:
                self._controller_nav_timer = CONTROLLER_AXIS_REPEAT_DELAY
                self._move_selection(new_dir)
            else:
                self._controller_nav_timer = 0.0
            return

        if new_dir == 0:
            return

        self._controller_nav_timer -= dt
        if self._controller_nav_timer <= 0.0:
            self._controller_nav_timer += CONTROLLER_AXIS_REPEAT_RATE
            self._move_selection(new_dir)

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self._handle_mouse_click(mouse_pos)
                    if self.next_scene is not None:
                        return

            elif event.type == pygame.MOUSEMOTION:
                self.keyboard_active = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard_event(event)
                if self.next_scene is not None:
                    return

            elif event.type == pygame.JOYBUTTONDOWN:
                self._handle_controller_button(event)
                if self.next_scene is not None:
                    return

            elif event.type == pygame.QUIT:
                # Do NOT call pygame.quit() here — see game_scene.py for explanation.
                # game.py handles QUIT by setting running=False; main.py's finally
                # block owns the single pygame.quit() call.
                return

    def update(self, dt):
        """Update the class selection state."""
        self._poll_active_controller_navigation(dt)

    def draw(self, screen):
        """Draw the class selection screen."""
        # 1. Dark background (same as main menu)
        screen.fill((15, 10, 25))

        # 2. Title at top, centered
        title = "CHOOSE YOUR HERO"
        if self.slot_queue_active:
            title = f"PLAYER {self.current_slot.index + 1} - CHOOSE YOUR HERO"
        title_surface = self.font_title.render(title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))

        # 3. For each of 3 HERO_CLASSES cards:
        card_width = 260
        card_height = 380
        spacing = 40
        total_width = len(HERO_CLASSES) * card_width + (len(HERO_CLASSES) - 1) * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        mouse_pos = pygame.mouse.get_pos()
        locked_hero_slots = self._locked_hero_slots()

        for i, hero in enumerate(HERO_CLASSES):
            # Calculate card position
            x = start_x + i * (card_width + spacing)
            y = 150

            # Card rectangle
            card_rect = pygame.Rect(x, y, card_width, card_height)

            # Check hover state
            hovered = (not self.slot_queue_active) and card_rect.collidepoint(mouse_pos)
            if hovered:
                self.hovered_card = i

            is_locked = hero["name"] in locked_hero_slots

            # Draw card background
            if self.selected_class == hero:
                # Brighter gold if selected
                pygame.draw.rect(screen, (100, 80, 40), card_rect)
            else:
                # Dark stone background
                pygame.draw.rect(screen, (40, 30, 20), card_rect)

            # Draw gold border if hovered, keyboard-navigated, or selected
            if hovered or self.selected_class == hero or (self.keyboard_active and i == self.nav_index):
                pygame.draw.rect(screen, (255, 215, 0), card_rect, 3)
            elif is_locked:
                pygame.draw.rect(screen, (110, 110, 110), card_rect, 3)

            # Top band filled with hero["color"] (40px tall)
            color_band = pygame.Rect(x, y, card_width, 40)
            pygame.draw.rect(screen, hero["color"], color_band)

            # Hero name wrapped to fit card width
            name = hero["name"]
            name_lines = textwrap.wrap(name, width=20)
            for j, line in enumerate(name_lines):
                line_surface = self.font_medium.render(line, True, (255, 255, 255))
                screen.blit(line_surface, (x + card_width // 2 - line_surface.get_width() // 2, y + 50 + j * 24))

            # Stats grid: HP / SPD / ARM values
            stats_y = y + 120
            stats = [
                f"HP: {hero['hp']}",
                f"SPD: {hero['speed']}",
                f"ARM: {hero['armor']}"
            ]

            for j, stat in enumerate(stats):
                stat_surface = self.font_medium.render(stat, True, (255, 255, 255))
                screen.blit(stat_surface, (x + 20, stats_y + j * 30))

            # Passive ability text (wrapped to card width, 20px right padding)
            passive_y = y + 230
            passive_text = hero["passive_desc"]
            wrapped_text = textwrap.wrap(passive_text, width=26)

            for j, line in enumerate(wrapped_text):
                line_surface = self.font_small.render(line, True, (200, 200, 200))
                screen.blit(line_surface, (x + 20, passive_y + j * 20))

            # Starting weapon name wrapped to fit card width
            weapon_y = y + 305
            weapon_lines = textwrap.wrap(f"Starts with: {hero['starting_weapon']}", width=26)
            for j, line in enumerate(weapon_lines):
                weapon_surface = self.font_small.render(line, True, (255, 255, 255))
                screen.blit(weapon_surface, (x + 20, weapon_y + j * 20))

            if is_locked:
                overlay = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                overlay.fill((40, 40, 40, 190))
                screen.blit(overlay, (x, y))

                owner_slot = locked_hero_slots[hero["name"]]
                locked_text = self.font_medium.render("LOCKED", True, (220, 220, 220))
                owner_text = self.font_small.render(
                    f"Picked by Player {owner_slot.index + 1}",
                    True,
                    owner_slot.color,
                )
                screen.blit(
                    locked_text,
                    (x + card_width // 2 - locked_text.get_width() // 2, y + 160),
                )
                screen.blit(
                    owner_text,
                    (x + card_width // 2 - owner_text.get_width() // 2, y + 192),
                )

        # 4. "CONFIRM" button (only shown if a card is selected) at bottom center
        if self.selected_class is not None:
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            confirm_color = (80, 60, 30) if confirm_rect.collidepoint(mouse_pos) else (40, 30, 20)
            pygame.draw.rect(screen, confirm_color, confirm_rect)
            pygame.draw.rect(screen, (255, 215, 0), confirm_rect, 2)  # Gold border

            confirm_text = self.font_medium.render("CONFIRM", True, (255, 255, 255))
            screen.blit(
                confirm_text,
                (
                    confirm_rect.centerx - confirm_text.get_width() // 2,
                    confirm_rect.centery - confirm_text.get_height() // 2,
                ),
            )

        # 5. "BACK" button bottom-left
        back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
        back_color = (80, 60, 30) if back_rect.collidepoint(mouse_pos) else (40, 30, 20)
        pygame.draw.rect(screen, back_color, back_rect)
        pygame.draw.rect(screen, (255, 215, 0), back_rect, 2)  # Gold border

        back_text = self.font_small.render("BACK", True, (255, 255, 255))
        screen.blit(
            back_text,
            (
                back_rect.centerx - back_text.get_width() // 2,
                back_rect.centery - back_text.get_height() // 2,
            ),
        )

        if self.slot_queue_active:
            cfg = self.current_slot.input_config
            if cfg is not None and cfg["type"] == "keyboard":
                prompt = self._keyboard_hint_text()
            elif cfg is not None and cfg["type"] == "controller":
                prompt = self._controller_hint_text()
            else:
                prompt = "Use your assigned controls to choose"
            prompt_surface = self.font_small.render(prompt, True, (180, 180, 180))
            screen.blit(
                prompt_surface,
                (SCREEN_WIDTH // 2 - prompt_surface.get_width() // 2, 108),
            )

            if self.selected_class is None:
                warning_surface = self.font_small.render(
                    "No heroes remain for this slot",
                    True,
                    (255, 120, 120),
                )
                screen.blit(
                    warning_surface,
                    (SCREEN_WIDTH // 2 - warning_surface.get_width() // 2, SCREEN_HEIGHT - 120),
                )
