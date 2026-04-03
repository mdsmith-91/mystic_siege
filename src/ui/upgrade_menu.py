import pygame
import math
import textwrap
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, TITLE_FONT_SIZE

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

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.keyboard_active = False
                self.hovered = -1
                for i in range(3):
                    card_rect = pygame.Rect(self.start_x + i * (self.card_width + self.gap), 150, self.card_width, self.card_height)
                    if card_rect.collidepoint(mouse_pos):
                        self.hovered = i
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if a card was clicked
                    for i in range(3):
                        card_rect = pygame.Rect(self.start_x + i * (self.card_width + self.gap), 150, self.card_width, self.card_height)
                        if card_rect.collidepoint(mouse_pos):
                            self._apply_choice(i)
                            self.done = True
                            return

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.keyboard_active = True
                    self.hovered = max(0, self.hovered - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.keyboard_active = True
                    self.hovered = min(len(self.choices) - 1, self.hovered + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._apply_choice(self.hovered)
                    self.done = True
                elif event.key == pygame.K_1:
                    self._apply_choice(0)
                    self.done = True
                elif event.key == pygame.K_2:
                    self._apply_choice(1)
                    self.done = True
                elif event.key == pygame.K_3:
                    self._apply_choice(2)
                    self.done = True

    def _apply_choice(self, index):
        """Apply the chosen upgrade."""
        if 0 <= index < len(self.choices):
            self.upgrade_system.apply_choice(self.choices[index], self.player)

    def update(self, dt):
        """Update the upgrade menu state."""
        # No update needed for this menu
        pass

    def draw(self, screen):
        """Draw the upgrade menu overlay."""
        # 1. Semi-transparent dark overlay covering entire screen (alpha=160)
        screen.blit(self._overlay, (0, 0))

        # 2. "LEVEL UP!" text centered at top (y=80), large, GOLD, with pulse animation
        #    (scale the text size slightly with sin(pygame.time.get_ticks()/300))
        pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2  # Value between 0 and 1
        scale = 1.0 + pulse * 0.1  # Scale from 1.0 to 1.1
        text = "LEVEL UP!"
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
        hint_text = "1 / 2 / 3  or  Arrow keys / click  •  Enter to confirm"
        hint_surface = self.font_hint.render(hint_text, True, (200, 200, 200))
        screen.blit(hint_surface, (SCREEN_WIDTH // 2 - hint_surface.get_width() // 2, SCREEN_HEIGHT - 40))