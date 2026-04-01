import pygame
from src.systems.save_system import SaveSystem

# Constants
BACKGROUND_COLOR = (25, 15, 35)
UI_COLOR = (180, 160, 200)
UI_HIGHLIGHT = (220, 200, 240)
TEXT_COLOR = (240, 230, 255)
SLIDER_TRACK_COLOR = (70, 60, 90)
SLIDER_HANDLE_COLOR = (150, 130, 180)
BUTTON_COLOR = (100, 80, 130)
BUTTON_HIGHLIGHT = (140, 120, 170)
CONFIRM_BG = (40, 30, 60)
CONFIRM_BORDER = (120, 100, 160)

class SettingsMenu:
    def __init__(self):
        self.save_system = SaveSystem()

        self.next_scene: str | None = None
        self.next_scene_kwargs: dict = {}

        # Initialize settings
        self.music_volume = self.save_system.get_setting("music_volume")
        self.sfx_volume = self.save_system.get_setting("sfx_volume")
        self.fullscreen = self.save_system.get_setting("fullscreen")
        self.show_fps = self.save_system.get_setting("show_fps")

        # UI elements
        self.confirm_dialog_open = False

        # Slider state
        self.dragging_slider = None
        self.sliders = {}

        # Button state
        self.buttons = {}

        # Initialize UI elements
        self._init_ui_elements()

    def _init_ui_elements(self):
        # Create slider rectangles
        y_offset = 150
        slider_height = 20
        slider_width = 300
        slider_y = y_offset

        self.sliders["music_volume"] = {
            "rect": pygame.Rect(150, slider_y, slider_width, slider_height),
            "handle_rect": pygame.Rect(150 + int(self.music_volume * slider_width), slider_y, 20, slider_height + 10),
            "value": self.music_volume
        }

        slider_y += 80
        self.sliders["sfx_volume"] = {
            "rect": pygame.Rect(150, slider_y, slider_width, slider_height),
            "handle_rect": pygame.Rect(150 + int(self.sfx_volume * slider_width), slider_y, 20, slider_height + 10),
            "value": self.sfx_volume
        }

        # Create toggle buttons
        button_width = 150
        button_height = 50
        button_y = slider_y + 100

        self.buttons["fullscreen"] = {
            "rect": pygame.Rect(150, button_y, button_width, button_height),
            "text": "Fullscreen: " + ("ON" if self.fullscreen else "OFF"),
            "value": self.fullscreen
        }

        button_y += 70
        self.buttons["show_fps"] = {
            "rect": pygame.Rect(150, button_y, button_width, button_height),
            "text": "Show FPS: " + ("ON" if self.show_fps else "OFF"),
            "value": self.show_fps
        }

        # Reset progress button
        button_y += 70
        self.buttons["reset"] = {
            "rect": pygame.Rect(150, button_y, button_width, button_height),
            "text": "Reset Progress",
            "value": None
        }

        # Back button
        button_y += 70
        self.buttons["back"] = {
            "rect": pygame.Rect(150, button_y, button_width, button_height),
            "text": "Back",
            "value": None
        }

        # Confirm dialog
        dialog_width = 300
        dialog_height = 150
        self.confirm_dialog = {
            "rect": pygame.Rect(
                (800 - dialog_width) // 2,
                (600 - dialog_height) // 2,
                dialog_width,
                dialog_height
            ),
            "text": "Are you sure? This cannot be undone.",
            "buttons": {
                "yes": {
                    "rect": pygame.Rect(
                        (800 - dialog_width) // 2 + 20,
                        (600 - dialog_height) // 2 + 90,
                        100,
                        40
                    ),
                    "text": "YES, RESET"
                },
                "cancel": {
                    "rect": pygame.Rect(
                        (800 - dialog_width) // 2 + 180,
                        (600 - dialog_height) // 2 + 90,
                        100,
                        40
                    ),
                    "text": "CANCEL"
                }
            }
        }

    def handle_events(self, events):
        for event in events:
            self._handle_event(event)

    def _handle_event(self, event):
        if self.confirm_dialog_open:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Check if "YES, RESET" was clicked
                if self.confirm_dialog["buttons"]["yes"]["rect"].collidepoint(mouse_pos):
                    self.save_system.reset()
                    self.confirm_dialog_open = False
                    # Reload settings after reset
                    self.music_volume = self.save_system.get_setting("music_volume")
                    self.sfx_volume = self.save_system.get_setting("sfx_volume")
                    self.fullscreen = self.save_system.get_setting("fullscreen")
                    self.show_fps = self.save_system.get_setting("show_fps")
                    self._init_ui_elements()

                # Check if "CANCEL" was clicked
                elif self.confirm_dialog["buttons"]["cancel"]["rect"].collidepoint(mouse_pos):
                    self.confirm_dialog_open = False
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.next_scene = "menu"
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Check if any slider handle was clicked
                for slider_name, slider_data in self.sliders.items():
                    if slider_data["handle_rect"].collidepoint(mouse_pos):
                        self.dragging_slider = slider_name
                        return

                # Check if any button was clicked
                for button_name, button_data in self.buttons.items():
                    if button_data["rect"].collidepoint(mouse_pos):
                        if button_name == "reset":
                            self.confirm_dialog_open = True
                        elif button_name == "back":
                            self.next_scene = "menu"
                        elif button_name in ["fullscreen", "show_fps"]:
                            # Toggle the setting
                            new_value = not button_data["value"]
                            self.buttons[button_name]["value"] = new_value
                            self.buttons[button_name]["text"] = button_name.capitalize() + ": " + ("ON" if new_value else "OFF")

                            # Save immediately
                            if button_name == "fullscreen":
                                self.fullscreen = new_value
                                self.save_system.set_setting("fullscreen", new_value)
                            elif button_name == "show_fps":
                                self.show_fps = new_value
                                self.save_system.set_setting("show_fps", new_value)
                        return

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.dragging_slider:
                    self.dragging_slider = None

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_slider:
                    mouse_x, _ = event.pos
                    slider = self.sliders[self.dragging_slider]
                    track = slider["rect"]

                    # Calculate new value based on mouse position
                    new_x = max(track.left, min(mouse_x, track.right))
                    new_value = (new_x - track.left) / track.width

                    # Update slider handle position and value
                    slider["handle_rect"].x = new_x - slider["handle_rect"].width // 2
                    slider["value"] = new_value

                    # Save the new volume value
                    if self.dragging_slider == "music_volume":
                        self.music_volume = new_value
                        self.save_system.set_setting("music_volume", new_value)
                    elif self.dragging_slider == "sfx_volume":
                        self.sfx_volume = new_value
                        self.save_system.set_setting("sfx_volume", new_value)

    def update(self, dt: float):
        # No update logic needed for this menu
        pass

    def draw(self, screen):
        # Draw background
        screen.fill(BACKGROUND_COLOR)

        # Draw title
        font = pygame.font.SysFont(None, 48)
        title = font.render("Settings", True, TEXT_COLOR)
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 50))

        # Draw sliders
        for slider_name, slider_data in self.sliders.items():
            track_rect = slider_data["rect"]
            handle_rect = slider_data["handle_rect"]

            # Draw track
            pygame.draw.rect(screen, SLIDER_TRACK_COLOR, track_rect, border_radius=10)

            # Draw handle
            pygame.draw.rect(screen, SLIDER_HANDLE_COLOR, handle_rect, border_radius=10)

            # Draw label
            font = pygame.font.SysFont(None, 24)
            if slider_name == "music_volume":
                label = font.render("Music Volume", True, TEXT_COLOR)
            else:
                label = font.render("SFX Volume", True, TEXT_COLOR)
            screen.blit(label, (track_rect.left - label.get_width() - 10, track_rect.top + 5))

        # Draw toggle buttons
        for button_name, button_data in self.buttons.items():
            if button_name in ("reset", "back"):
                continue  # drawn separately below

            rect = button_data["rect"]
            text = button_data["text"]

            # Draw button
            color = BUTTON_HIGHLIGHT if rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, UI_HIGHLIGHT, rect, 2, border_radius=10)

            # Draw text
            font = pygame.font.SysFont(None, 24)
            text_surf = font.render(text, True, TEXT_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

        # Draw reset and back buttons separately
        font = pygame.font.SysFont(None, 24)
        mouse_pos = pygame.mouse.get_pos()
        for key in ("reset", "back"):
            btn = self.buttons[key]
            rect = btn["rect"]
            color = BUTTON_HIGHLIGHT if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, UI_HIGHLIGHT, rect, 2, border_radius=10)
            text_surf = font.render(btn["text"], True, TEXT_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

        # Draw confirm dialog if open
        if self.confirm_dialog_open:
            dialog = self.confirm_dialog

            # Draw background
            pygame.draw.rect(screen, CONFIRM_BG, dialog["rect"], border_radius=10)
            pygame.draw.rect(screen, CONFIRM_BORDER, dialog["rect"], 2, border_radius=10)

            # Draw text
            font = pygame.font.SysFont(None, 24)
            text_surf = font.render(dialog["text"], True, TEXT_COLOR)
            screen.blit(text_surf, (dialog["rect"].centerx - text_surf.get_width() // 2, dialog["rect"].top + 20))

            # Draw buttons
            for button_name, button_data in dialog["buttons"].items():
                rect = button_data["rect"]
                text = button_data["text"]

                # Draw button
                color = BUTTON_HIGHLIGHT if rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
                pygame.draw.rect(screen, color, rect, border_radius=10)
                pygame.draw.rect(screen, UI_HIGHLIGHT, rect, 2, border_radius=10)

                # Draw text
                text_surf = font.render(text, True, TEXT_COLOR)
                screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))