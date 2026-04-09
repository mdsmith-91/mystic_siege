import pygame

from settings import (
    CLASS_SELECT_CARD_GAP_X,
    CLASS_SELECT_CARD_GAP_Y,
    CLASS_SELECT_CARD_HEIGHT,
    CLASS_SELECT_CARD_PADDING_X,
    CLASS_SELECT_CARD_WIDTH,
    CLASS_SELECT_COLOR_BAND_HEIGHT,
    CLASS_SELECT_GRID_BOTTOM_MARGIN,
    CLASS_SELECT_GRID_TOP_Y,
    CLASS_SELECT_MAX_COLUMNS,
    CLASS_SELECT_PROMPT_MARGIN_TOP,
    CLASS_SELECT_TITLE_Y,
    CONTROLLER_AXIS_REPEAT_DELAY,
    CONTROLLER_AXIS_REPEAT_RATE,
    HERO_CLASSES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_CLASS_SELECT,
    STATE_LOBBY,
    STATE_MENU,
    STATE_PLAYING,
    TITLE_FONT_SIZE,
)
from src.core.player_slot import PlayerSlot
from src.utils.input_manager import InputManager

_WEAPON_DISPLAY_NAMES = {
    "ArcaneBolt": "Arcane Bolt",
    "HolyNova": "Holy Nova",
    "SpectralBlade": "Spectral Blade",
    "FlameBlast": "Flame Blast",
    "FrostRing": "Frost Ring",
    "HexOrb": "Hex Orb",
    "LightningChain": "Lightning Chain",
    "Longbow": "Longbow",
    "ShadowKnives": "Shadow Knives",
    "ThrowingAxes": "Throwing Axes",
}


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
        self.nav_index = 0
        self.keyboard_active = False
        self._controller_nav_vector = (0, 0)
        self._controller_nav_timer = 0.0

        self.font_title = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        self.font_large = pygame.font.SysFont("serif", 28)
        self.font_medium = pygame.font.SysFont("serif", 20)
        self.font_small = pygame.font.SysFont("serif", 16)

        initial_index = self._first_available_index()
        if initial_index is not None:
            self._set_selection(initial_index)

    def _controller_cfg(self) -> dict | None:
        if not self.slot_queue_active:
            return None
        cfg = self.current_slot.input_config
        if cfg is None or cfg.get("type") != "controller":
            return None
        return cfg

    def _resolved_controller_id(self) -> int | None:
        cfg = self._controller_cfg()
        if cfg is None:
            return None

        input_manager = InputManager.instance()
        joystick_id = input_manager.resolve_joystick_id(
            cfg.get("joystick_id"),
            profile_key=cfg.get("profile_key"),
            guid=cfg.get("guid"),
            name=cfg.get("name"),
        )
        if joystick_id is not None and joystick_id != cfg.get("joystick_id"):
            self.current_slot.input_config = input_manager.build_controller_input_config(joystick_id)
        return joystick_id

    def _controller_reconnect_candidate_ids(self) -> list[int]:
        cfg = self._controller_cfg()
        if cfg is None:
            return []

        return InputManager.instance().get_reconnect_candidate_ids(
            joystick_id=cfg.get("joystick_id"),
            profile_key=cfg.get("profile_key"),
            guid=cfg.get("guid"),
            name=cfg.get("name"),
        )

    def _try_reclaim_controller(self, event: pygame.event.Event) -> bool:
        cfg = self._controller_cfg()
        if cfg is None:
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

        self.current_slot.input_config = input_manager.build_controller_input_config(event.instance_id)
        self._controller_nav_vector = (0, 0)
        self._controller_nav_timer = 0.0
        return True

    def _mouse_input_enabled(self) -> bool:
        return True

    def _mouse_button_input_enabled(self) -> bool:
        return True

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

    def _grid_dimensions(self) -> tuple[int, int]:
        hero_count = max(1, len(HERO_CLASSES))
        columns = min(CLASS_SELECT_MAX_COLUMNS, hero_count)
        rows = (hero_count + columns - 1) // columns
        return columns, rows

    def _card_rects(self) -> list[pygame.Rect]:
        columns, rows = self._grid_dimensions()
        total_width = columns * CLASS_SELECT_CARD_WIDTH + (columns - 1) * CLASS_SELECT_CARD_GAP_X
        total_height = rows * CLASS_SELECT_CARD_HEIGHT + (rows - 1) * CLASS_SELECT_CARD_GAP_Y
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = CLASS_SELECT_GRID_TOP_Y
        start_y = min(start_y, SCREEN_HEIGHT - total_height - CLASS_SELECT_GRID_BOTTOM_MARGIN)

        rects: list[pygame.Rect] = []
        for index in range(len(HERO_CLASSES)):
            row = index // columns
            col = index % columns
            rects.append(
                pygame.Rect(
                    start_x + col * (CLASS_SELECT_CARD_WIDTH + CLASS_SELECT_CARD_GAP_X),
                    start_y + row * (CLASS_SELECT_CARD_HEIGHT + CLASS_SELECT_CARD_GAP_Y),
                    CLASS_SELECT_CARD_WIDTH,
                    CLASS_SELECT_CARD_HEIGHT,
                )
            )
        return rects

    def _wrap_text_to_pixel_width(
        self,
        text: str,
        font: pygame.font.Font,
        max_width: int,
    ) -> list[str]:
        words = text.split()
        if not words:
            return [""]

        lines: list[str] = []
        current_line = words[0]
        for word in words[1:]:
            candidate = f"{current_line} {word}"
            if font.size(candidate)[0] <= max_width:
                current_line = candidate
                continue

            lines.append(current_line)
            current_line = word

        lines.append(current_line)
        return lines

    def _wrap_multiline_text_to_pixel_width(
        self,
        text: str,
        font: pygame.font.Font,
        max_width: int,
    ) -> list[str]:
        lines: list[str] = []
        for paragraph in text.splitlines():
            wrapped_lines = self._wrap_text_to_pixel_width(paragraph, font, max_width)
            lines.extend(wrapped_lines)
        return lines or [""]

    def _line_limit_for_height(self, max_height: int, line_height: int) -> int:
        if max_height <= 0 or line_height <= 0:
            return 0
        return max_height // line_height

    def _index_to_row_col(self, index: int) -> tuple[int, int]:
        columns, _unused_rows = self._grid_dimensions()
        return index // columns, index % columns

    def _row_col_to_index(self, row: int, col: int) -> int | None:
        columns, rows = self._grid_dimensions()
        if row < 0 or row >= rows or col < 0 or col >= columns:
            return None
        index = row * columns + col
        if index >= len(HERO_CLASSES):
            return None
        return index

    def _set_selection(self, index: int) -> None:
        self.nav_index = index
        self.selected_class = HERO_CLASSES[index]

    def _move_selection_horizontal(self, step: int) -> None:
        if self.selected_class is None:
            return

        for offset in range(1, len(HERO_CLASSES) + 1):
            next_index = (self.nav_index + step * offset) % len(HERO_CLASSES)
            if not self._is_hero_locked(HERO_CLASSES[next_index]):
                self._set_selection(next_index)
                return

    def _nearest_unlocked_in_row(self, row: int, preferred_col: int) -> int | None:
        columns, _unused_rows = self._grid_dimensions()
        candidate_indices: list[int] = []
        for col in range(columns):
            index = self._row_col_to_index(row, col)
            if index is None:
                continue
            if self._is_hero_locked(HERO_CLASSES[index]):
                continue
            candidate_indices.append(index)

        if not candidate_indices:
            return None

        return min(
            candidate_indices,
            key=lambda index: (
                abs(self._index_to_row_col(index)[1] - preferred_col),
                index,
            ),
        )

    def _move_selection_vertical(self, step: int) -> None:
        if self.selected_class is None:
            return

        row, col = self._index_to_row_col(self.nav_index)
        _columns, rows = self._grid_dimensions()
        next_row = row + step
        while 0 <= next_row < rows:
            candidate = self._nearest_unlocked_in_row(next_row, col)
            if candidate is not None:
                self._set_selection(candidate)
                return
            next_row += step

    def _move_selection(self, horizontal: int = 0, vertical: int = 0) -> None:
        if horizontal != 0:
            self._move_selection_horizontal(horizontal)
        elif vertical != 0:
            self._move_selection_vertical(vertical)

    def _can_confirm_selected_class(self) -> bool:
        return self.selected_class is not None and not self._is_hero_locked(self.selected_class)

    def _route_to_game_or_next_slot(self) -> None:
        if not self._can_confirm_selected_class():
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
            return "Arrow keys or WASD to choose  -  Enter or click confirms  -  ESC or Back click backs"

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "keyboard":
            return "Use your assigned controls or click to choose  -  Click Confirm/Back or press ESC"

        total_slots = len(self.slots) + len(self.confirmed_slots)
        if cfg.get("scheme") == "wasd":
            if total_slots == 1:
                return "WASD to move  -  Space, Enter, or click confirms  -  ESC, Left Shift, or Back click backs"
            return "WASD or click to choose  -  Space or click confirms  -  ESC, Left Shift, or Back click backs"

        if cfg.get("scheme") == "arrows":
            return "Arrow keys or click to choose  -  Enter or click confirms  -  ESC, Right Shift, or Back click backs"

        return "Use your assigned keyboard controls or click to choose  -  Click Confirm/Back or press ESC"

    def _controller_hint_text(self) -> str:
        cfg = self.current_slot.input_config
        if cfg is not None and cfg["type"] == "controller":
            input_manager = InputManager.instance()
            joystick_id = self._resolved_controller_id()
            cfg = self.current_slot.input_config
            if joystick_id is None:
                return (
                    f"Player {self.current_slot.index + 1}: controller disconnected"
                    f"  -  reconnect and press {input_manager.describe_help_binding('confirm')} or {input_manager.describe_help_binding('start')} to reclaim"
                )
            return (
                f"Controller {joystick_id + 1}: stick, D-pad, or click to choose"
                f"  -  {input_manager.describe_help_binding('confirm')} or click confirms"
                f"  -  {input_manager.describe_help_binding('back')}, ESC, or Back click backs"
            )
        return "Use your assigned controls or click to choose  -  Click Confirm/Back or press ESC"

    def _keyboard_event_matches_current_slot(self, event: pygame.event.Event) -> bool:
        if not self.slot_queue_active:
            return True

        if getattr(event, "synthetic_controller_event", False):
            return False

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "keyboard":
            return False
        keys = cfg["keys"]
        return event.key in {
            keys["left"],
            keys["right"],
            keys["up"],
            keys["down"],
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
                self._move_selection(horizontal=-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.keyboard_active = True
                self._move_selection(horizontal=1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.keyboard_active = True
                self._move_selection(vertical=-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.keyboard_active = True
                self._move_selection(vertical=1)
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
            self._move_selection(horizontal=-1)
        elif event.key == keys["right"]:
            self.keyboard_active = True
            self._move_selection(horizontal=1)
        elif event.key == keys["up"]:
            self.keyboard_active = True
            self._move_selection(vertical=-1)
        elif event.key == keys["down"]:
            self.keyboard_active = True
            self._move_selection(vertical=1)
        elif event.key in confirm_keys:
            self._route_to_game_or_next_slot()
        elif event.key in {keys["back"], pygame.K_ESCAPE}:
            self._handle_back()

    def _handle_mouse_click(self, mouse_pos: tuple[int, int]) -> None:
        card_rects = self._card_rects()

        if self._mouse_input_enabled():
            for i, (hero, card_rect) in enumerate(zip(HERO_CLASSES, card_rects)):
                if card_rect.collidepoint(mouse_pos):
                    if self._is_hero_locked(hero):
                        return
                    self._set_selection(i)
                    return

        if self._mouse_button_input_enabled() and self.selected_class is not None:
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            if confirm_rect.collidepoint(mouse_pos):
                self._route_to_game_or_next_slot()
                return

        if self._mouse_button_input_enabled():
            back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
            if back_rect.collidepoint(mouse_pos):
                self._handle_back()

    def _weapon_display_name(self, weapon_id: str) -> str:
        return _WEAPON_DISPLAY_NAMES.get(weapon_id, weapon_id)

    def _handle_controller_button(self, event: pygame.event.Event) -> None:
        if not self.slot_queue_active:
            return

        cfg = self.current_slot.input_config
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
            self._route_to_game_or_next_slot()
        elif input_manager.button_matches("back", event.button, joystick_id=event.instance_id):
            self._handle_back()

    def _controller_nav_step(self, horizontal_dir: int, vertical_dir: int) -> tuple[int, int]:
        if horizontal_dir != 0:
            return horizontal_dir, 0
        if vertical_dir != 0:
            return 0, vertical_dir
        return 0, 0

    def _poll_active_controller_navigation(self, dt: float) -> None:
        if not self.slot_queue_active:
            return

        cfg = self.current_slot.input_config
        if cfg is None or cfg["type"] != "controller":
            return

        joystick_id = self._resolved_controller_id()
        if joystick_id is None:
            self._controller_nav_vector = (0, 0)
            self._controller_nav_timer = 0.0
            return

        horizontal_dir, vertical_dir = InputManager.instance().get_menu_navigation_for_joystick(
            joystick_id
        )
        new_vector = self._controller_nav_step(horizontal_dir, vertical_dir)

        if new_vector != self._controller_nav_vector:
            self._controller_nav_vector = new_vector
            if new_vector != (0, 0):
                self._controller_nav_timer = CONTROLLER_AXIS_REPEAT_DELAY
                self._move_selection(horizontal=new_vector[0], vertical=new_vector[1])
            else:
                self._controller_nav_timer = 0.0
            return

        if new_vector == (0, 0):
            return

        self._controller_nav_timer -= dt
        if self._controller_nav_timer <= 0.0:
            self._controller_nav_timer += CONTROLLER_AXIS_REPEAT_RATE
            self._move_selection(horizontal=new_vector[0], vertical=new_vector[1])

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self._mouse_button_input_enabled():
                    self._handle_mouse_click(mouse_pos)
                    if self.next_scene is not None:
                        return

            elif event.type == pygame.MOUSEMOTION:
                if self._mouse_input_enabled():
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
                return

    def update(self, dt):
        self._poll_active_controller_navigation(dt)

    def draw(self, screen):
        screen.fill((15, 10, 25))

        title = "CHOOSE YOUR HERO"
        if self.slot_queue_active:
            title = f"PLAYER {self.current_slot.index + 1} - CHOOSE YOUR HERO"
        title_surface = self.font_title.render(title, True, (255, 255, 255))
        title_y = CLASS_SELECT_TITLE_Y
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, title_y))

        mouse_pos = pygame.mouse.get_pos()
        locked_hero_slots = self._locked_hero_slots()
        card_rects = self._card_rects()
        self.hovered_card = None

        for i, (hero, card_rect) in enumerate(zip(HERO_CLASSES, card_rects)):
            hovered = card_rect.collidepoint(mouse_pos)
            if hovered:
                self.hovered_card = i

            is_locked = hero["name"] in locked_hero_slots
            is_selected = self.selected_class == hero
            is_keyboard_focus = self.keyboard_active and i == self.nav_index

            bg_color = (100, 80, 40) if is_selected else (40, 30, 20)
            pygame.draw.rect(screen, bg_color, card_rect, border_radius=8)

            if hovered or is_selected or is_keyboard_focus:
                border_color = (255, 215, 0)
                border_width = 3
            elif is_locked:
                border_color = (110, 110, 110)
                border_width = 3
            else:
                border_color = (85, 70, 45)
                border_width = 1

            color_band = pygame.Rect(
                card_rect.x,
                card_rect.y,
                card_rect.width,
                CLASS_SELECT_COLOR_BAND_HEIGHT,
            )
            pygame.draw.rect(
                screen,
                hero["color"],
                color_band,
                border_top_left_radius=8,
                border_top_right_radius=8,
            )

            content_left = card_rect.x + CLASS_SELECT_CARD_PADDING_X
            content_right = card_rect.right - CLASS_SELECT_CARD_PADDING_X
            center_x = card_rect.centerx

            content_width = content_right - content_left

            name_font = self.font_medium
            name_lines = self._wrap_text_to_pixel_width(hero["name"], name_font, content_width)
            if len(name_lines) > 1:
                name_font = self.font_small
                name_lines = self._wrap_text_to_pixel_width(hero["name"], name_font, content_width)

            name_line_height = name_font.get_linesize()
            name_block_height = len(name_lines) * name_line_height
            name_top = color_band.y + (color_band.height - name_block_height) // 2
            for j, line in enumerate(name_lines):
                line_surface = name_font.render(line, True, (255, 255, 255))
                screen.blit(
                    line_surface,
                    (center_x - line_surface.get_width() // 2, name_top + j * name_line_height),
                )

            stats_top = color_band.bottom + 10
            column_width = (card_rect.width - CLASS_SELECT_CARD_PADDING_X * 2) // 3
            stats = [("HP", hero["hp"]), ("SPD", hero["speed"]), ("ARM", hero["armor"])]
            for j, (label, value) in enumerate(stats):
                cell_center_x = content_left + j * column_width + column_width // 2
                label_surface = self.font_small.render(label, True, (200, 180, 140))
                value_surface = self.font_medium.render(str(value), True, (255, 255, 255))
                screen.blit(label_surface, (cell_center_x - label_surface.get_width() // 2, stats_top))
                screen.blit(value_surface, (cell_center_x - value_surface.get_width() // 2, stats_top + 18))

            stats_bottom = stats_top + 18 + self.font_medium.get_linesize()
            passive_label = self.font_small.render("Passive", True, (255, 215, 0))
            passive_label_y = stats_bottom + 10
            screen.blit(passive_label, (content_left, passive_label_y))

            weapon_name = self._weapon_display_name(hero["starting_weapon"])
            weapon_lines = self._wrap_text_to_pixel_width(
                weapon_name,
                self.font_small,
                content_width,
            )
            weapon_label = self.font_small.render("Starting Weapon", True, (255, 215, 0))
            text_line_height = self.font_small.get_linesize()
            weapon_line_limit = self._line_limit_for_height(
                card_rect.bottom - CLASS_SELECT_CARD_PADDING_X - (passive_label_y + 18 + text_line_height),
                text_line_height,
            )
            weapon_lines = weapon_lines[: max(1, weapon_line_limit)]
            weapon_label_y = card_rect.bottom - CLASS_SELECT_CARD_PADDING_X - (
                18 + len(weapon_lines) * text_line_height
            )

            passive_lines = self._wrap_multiline_text_to_pixel_width(
                hero["passive_desc"],
                self.font_small,
                content_width,
            )
            passive_top = passive_label_y + 18
            passive_line_limit = self._line_limit_for_height(
                weapon_label_y - passive_top,
                text_line_height,
            )
            for j, line in enumerate(passive_lines[:passive_line_limit]):
                line_surface = self.font_small.render(line, True, (210, 210, 210))
                screen.blit(line_surface, (content_left, passive_top + j * text_line_height))

            screen.blit(weapon_label, (content_left, weapon_label_y))

            for j, line in enumerate(weapon_lines):
                weapon_surface = self.font_small.render(line, True, (255, 255, 255))
                screen.blit(weapon_surface, (content_left, weapon_label_y + 18 + j * text_line_height))

            if is_locked:
                overlay = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                overlay.fill((40, 40, 40, 190))
                screen.blit(overlay, card_rect.topleft)

                owner_slot = locked_hero_slots[hero["name"]]
                locked_text = self.font_medium.render("LOCKED", True, (220, 220, 220))
                owner_text = self.font_small.render(
                    f"Picked by Player {owner_slot.index + 1}",
                    True,
                    owner_slot.color,
                )
                screen.blit(
                    locked_text,
                    (center_x - locked_text.get_width() // 2, card_rect.centery - 20),
                )
                screen.blit(
                    owner_text,
                    (center_x - owner_text.get_width() // 2, card_rect.centery + 8),
                )

            pygame.draw.rect(screen, border_color, card_rect, border_width, border_radius=8)

        if self._can_confirm_selected_class():
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            confirm_color = (80, 60, 30) if confirm_rect.collidepoint(mouse_pos) else (40, 30, 20)
            pygame.draw.rect(screen, confirm_color, confirm_rect, border_radius=6)
            pygame.draw.rect(screen, (255, 215, 0), confirm_rect, 2, border_radius=6)

            confirm_text = self.font_medium.render("CONFIRM", True, (255, 255, 255))
            screen.blit(
                confirm_text,
                (
                    confirm_rect.centerx - confirm_text.get_width() // 2,
                    confirm_rect.centery - confirm_text.get_height() // 2,
                ),
            )

        back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
        back_color = (80, 60, 30) if back_rect.collidepoint(mouse_pos) else (40, 30, 20)
        pygame.draw.rect(screen, back_color, back_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 215, 0), back_rect, 2, border_radius=6)

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
            prompt_y = title_y + title_surface.get_height() + CLASS_SELECT_PROMPT_MARGIN_TOP
            screen.blit(
                prompt_surface,
                (SCREEN_WIDTH // 2 - prompt_surface.get_width() // 2, prompt_y),
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
