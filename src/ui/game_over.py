import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, HP_LOW_COLOR, TITLE_FONT_SIZE

class GameOver:
    def __init__(self, victory: bool, stats: dict):
        self.next_scene = None
        self.victory = victory
        self.stats = stats

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if "PLAY AGAIN" button was clicked
                    play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 480, 200, 50)
                    if play_again_rect.collidepoint(mouse_pos):
                        self.next_scene = "class_select"
                        return

                    # Check if "MAIN MENU" button was clicked
                    main_menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 50)
                    if main_menu_rect.collidepoint(mouse_pos):
                        self.next_scene = "menu"
                        return

            elif event.type == pygame.QUIT:
                pygame.quit()
                return

    def update(self, dt):
        """Update the game over state."""
        # No update needed for this scene
        pass

    def draw(self, screen):
        """Draw the game over screen."""
        # 1. Dark background
        screen.fill((15, 10, 25))

        # 2. Large title: "VICTORY" (gold) or "DEFEATED" (red), centered, y=150
        #    with animated glow (alternate brightness each second)
        title = "VICTORY" if self.victory else "DEFEATED"
        title_color = GOLD if self.victory else HP_LOW_COLOR

        # Create animated glow effect
        time = pygame.time.get_ticks()
        pulse = (math.sin(time / 500) + 1) / 2  # Value between 0 and 1
        if not self.victory:
            # For defeated, make it more red/pulsing
            pulse = 0.5 + 0.5 * (math.sin(time / 300) + 1) / 2

        # Adjust color based on pulse
        if self.victory:
            final_color = (int(title_color[0] * (0.7 + 0.3 * pulse)),
                          int(title_color[1] * (0.7 + 0.3 * pulse)),
                          int(title_color[2] * (0.7 + 0.3 * pulse)))
        else:
            final_color = (int(255 * (0.7 + 0.3 * pulse)),
                          int(50 * (0.7 + 0.3 * pulse)),
                          int(50 * (0.7 + 0.3 * pulse)))

        font_large = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        title_surface = font_large.render(title, True, final_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)

        # 3. Stats block centered below title:
        #    "Time Survived: {time_str}"
        #    "Enemies Slain: {kills}"
        #    "Level Reached: {level}"
        #    "Weapons: {', '.join(weapons)}"
        font_medium = pygame.font.SysFont("serif", 20)
        stats_y = 250

        stats_text = [
            f"Time Survived: {self.stats['time_str']}",
            f"Enemies Slain: {self.stats['kills']}",
            f"Level Reached: {self.stats['level']}",
            f"Weapons: {', '.join(self.stats['weapons'])}"
        ]

        for i, text in enumerate(stats_text):
            text_surface = font_medium.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, stats_y + i * 30))

        # 4. Two buttons: "PLAY AGAIN" and "MAIN MENU", centered, y=480 and y=550
        font_small = pygame.font.SysFont("serif", 18)

        # PLAY AGAIN button
        play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 480, 200, 50)
        pygame.draw.rect(screen, (40, 30, 20), play_again_rect)
        pygame.draw.rect(screen, GOLD, play_again_rect, 2)  # Gold border

        play_again_text = font_small.render("PLAY AGAIN", True, (255, 255, 255))
        screen.blit(play_again_text, (SCREEN_WIDTH // 2 - play_again_text.get_width() // 2, 495))

        # MAIN MENU button
        main_menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 50)
        pygame.draw.rect(screen, (40, 30, 20), main_menu_rect)
        pygame.draw.rect(screen, GOLD, main_menu_rect, 2)  # Gold border

        main_menu_text = font_small.render("MAIN MENU", True, (255, 255, 255))
        screen.blit(main_menu_text, (SCREEN_WIDTH // 2 - main_menu_text.get_width() // 2, 565))