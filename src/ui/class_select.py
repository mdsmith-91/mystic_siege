import pygame
import textwrap
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, HERO_CLASSES, TITLE_FONT_SIZE, HUD_FONT_SIZE

class ClassSelect:
    def __init__(self):
        self.next_scene = None
        self.next_scene_kwargs = {}
        self.selected_class = None
        self.hovered_card = None
        self.nav_index = 0  # keyboard nav index for hero cards (0–2)
        self.keyboard_active = False

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if a hero card was clicked
                    card_width = 260
                    card_height = 380
                    spacing = 40
                    total_width = 3 * card_width + 2 * spacing
                    start_x = (SCREEN_WIDTH - total_width) // 2

                    for i in range(3):
                        card_rect = pygame.Rect(start_x + i * (card_width + spacing), 150, card_width, card_height)
                        if card_rect.collidepoint(mouse_pos):
                            self.selected_class = HERO_CLASSES[i]
                            return

                    # Check if "CONFIRM" button was clicked
                    if self.selected_class is not None:
                        confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
                        if confirm_rect.collidepoint(mouse_pos):
                            self.next_scene = "playing"
                            self.next_scene_kwargs = {"hero": self.selected_class}
                            return

                    # Check if "BACK" button was clicked
                    back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
                    if back_rect.collidepoint(mouse_pos):
                        self.next_scene = "menu"
                        return

            elif event.type == pygame.MOUSEMOTION:
                self.keyboard_active = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.keyboard_active = True
                    self.nav_index = max(0, self.nav_index - 1)
                    self.selected_class = HERO_CLASSES[self.nav_index]
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.keyboard_active = True
                    self.nav_index = min(2, self.nav_index + 1)
                    self.selected_class = HERO_CLASSES[self.nav_index]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.selected_class is not None:
                        self.next_scene = "playing"
                        self.next_scene_kwargs = {"hero": self.selected_class}
                elif event.key == pygame.K_ESCAPE:
                    self.next_scene = "menu"

            elif event.type == pygame.QUIT:
                pygame.quit()
                return

    def update(self, dt):
        """Update the class selection state."""
        # No update needed for this scene
        pass

    def draw(self, screen):
        """Draw the class selection screen."""
        # 1. Dark background (same as main menu)
        screen.fill((15, 10, 25))

        # 2. Title "CHOOSE YOUR HERO" at top, centered
        font = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        title = "CHOOSE YOUR HERO"
        title_surface = font.render(title, True, (255, 255, 255))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 50))

        # 3. For each of 3 HERO_CLASSES cards:
        card_width = 260
        card_height = 380
        spacing = 40
        total_width = 3 * card_width + 2 * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        font_large = pygame.font.SysFont("serif", 28)
        font_medium = pygame.font.SysFont("serif", 20)
        font_small = pygame.font.SysFont("serif", 16)

        for i, hero in enumerate(HERO_CLASSES):
            # Calculate card position
            x = start_x + i * (card_width + spacing)
            y = 150

            # Card rectangle
            card_rect = pygame.Rect(x, y, card_width, card_height)

            # Check hover state
            mouse_pos = pygame.mouse.get_pos()
            hovered = card_rect.collidepoint(mouse_pos)
            if hovered:
                self.hovered_card = i

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

            # Top band filled with hero["color"] (40px tall)
            color_band = pygame.Rect(x, y, card_width, 40)
            pygame.draw.rect(screen, hero["color"], color_band)

            # Hero name wrapped to fit card width
            name = hero["name"]
            name_lines = textwrap.wrap(name, width=20)
            for j, line in enumerate(name_lines):
                line_surface = font_medium.render(line, True, (255, 255, 255))
                screen.blit(line_surface, (x + card_width // 2 - line_surface.get_width() // 2, y + 50 + j * 24))

            # Stats grid: HP / SPD / ARM values
            stats_y = y + 120
            stats = [
                f"HP: {hero['hp']}",
                f"SPD: {hero['speed']}",
                f"ARM: {hero['armor']}"
            ]

            for j, stat in enumerate(stats):
                stat_surface = font_medium.render(stat, True, (255, 255, 255))
                screen.blit(stat_surface, (x + 20, stats_y + j * 30))

            # Passive ability text (wrapped to card width, 20px right padding)
            passive_y = y + 230
            passive_text = hero["passive_desc"]
            wrapped_text = textwrap.wrap(passive_text, width=26)

            for j, line in enumerate(wrapped_text):
                line_surface = font_small.render(line, True, (200, 200, 200))
                screen.blit(line_surface, (x + 20, passive_y + j * 20))

            # Starting weapon name wrapped to fit card width
            weapon_y = y + 305
            weapon_lines = textwrap.wrap(f"Starts with: {hero['starting_weapon']}", width=26)
            for j, line in enumerate(weapon_lines):
                weapon_surface = font_small.render(line, True, (255, 255, 255))
                screen.blit(weapon_surface, (x + 20, weapon_y + j * 20))

        # 4. "CONFIRM" button (only shown if a card is selected) at bottom center
        if self.selected_class is not None:
            confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            pygame.draw.rect(screen, (40, 30, 20), confirm_rect)
            pygame.draw.rect(screen, (255, 215, 0), confirm_rect, 2)  # Gold border

            confirm_text = font_medium.render("CONFIRM", True, (255, 255, 255))
            screen.blit(confirm_text, (SCREEN_WIDTH // 2 - confirm_text.get_width() // 2, SCREEN_HEIGHT - 70))

        # 5. "BACK" button bottom-left
        back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
        mouse_pos = pygame.mouse.get_pos()
        back_color = (80, 60, 30) if back_rect.collidepoint(mouse_pos) else (40, 30, 20)
        pygame.draw.rect(screen, back_color, back_rect)
        pygame.draw.rect(screen, (255, 215, 0), back_rect, 2)  # Gold border

        back_text = font_small.render("BACK", True, (255, 255, 255))
        screen.blit(back_text, (20 + 50 - back_text.get_width() // 2, SCREEN_HEIGHT - 50))