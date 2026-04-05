import pygame
import math
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, HP_LOW_COLOR, TITLE_FONT_SIZE, STATE_LOBBY, STATE_MENU
from src.systems.save_system import SaveSystem

class GameOver:
    def __init__(self, victory: bool, stats: dict, player_results: list[dict] | None = None):
        self.next_scene = None
        self.selected_index = 0  # keyboard nav: 0=PLAY AGAIN, 1=MAIN MENU
        self.keyboard_active = False
        self.victory = victory
        self.stats = stats
        self.player_results = player_results

        self.font_title = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        self.font_medium = pygame.font.SysFont("serif", 20)
        self.font_small = pygame.font.SysFont("serif", 18)

        # Persist run stats to save file
        SaveSystem().update_after_run({
            "kills": stats["kills"],
            "time_survived": stats["time_survived"],
            "level": stats["level"],
        })

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if "PLAY AGAIN" button was clicked
                    play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 480, 200, 50)
                    if play_again_rect.collidepoint(mouse_pos):
                        self.next_scene = STATE_LOBBY
                        return

                    # Check if "MAIN MENU" button was clicked
                    main_menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 550, 200, 50)
                    if main_menu_rect.collidepoint(mouse_pos):
                        self.next_scene = STATE_MENU
                        return

            elif event.type == pygame.MOUSEMOTION:
                self.keyboard_active = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.keyboard_active = True
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.keyboard_active = True
                    self.selected_index = min(1, self.selected_index + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.selected_index == 0:
                        self.next_scene = STATE_LOBBY
                    else:
                        self.next_scene = STATE_MENU

            elif event.type == pygame.QUIT:
                # Do NOT call pygame.quit() here — see game_scene.py for explanation.
                # game.py handles QUIT by setting running=False; main.py's finally
                # block owns the single pygame.quit() call.
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

        title_surface = self.font_title.render(title, True, final_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)

        # 3. Stats block centered below title:
        #    "Time Survived: {time_str}"
        #    "Enemies Slain: {kills}"
        #    "Level Reached: {level}"
        #    "Weapons: {', '.join(weapons)}"
        stats_y = 250

        if self.player_results:
            summary_text = [
                f"Time Survived: {self.stats.get('time_str', '0:00')}",
                f"Party Kills: {self.stats.get('kills', 0)}    Highest Level: {self.stats.get('level', 1)}",
            ]

            for i, text in enumerate(summary_text):
                text_surface = self.font_medium.render(text, True, (255, 255, 255))
                screen.blit(
                    text_surface,
                    (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, stats_y + i * 30),
                )

            header_y = stats_y + len(summary_text) * 30 + 20
            header_surface = self.font_medium.render("Party Results", True, GOLD)
            screen.blit(
                header_surface,
                (SCREEN_WIDTH // 2 - header_surface.get_width() // 2, header_y),
            )

            for i, result in enumerate(self.player_results):
                weapons = ", ".join(result.get("weapons", [])) or "None"
                line = (
                    f"P{result['slot_index'] + 1} {result['hero_name']}  "
                    f"L{result['level']}  {result['kills']} kills  {weapons}"
                )
                line_surface = self.font_small.render(line, True, result.get("color", (255, 255, 255)))
                screen.blit(
                    line_surface,
                    (SCREEN_WIDTH // 2 - line_surface.get_width() // 2, header_y + 35 + i * 24),
                )
        else:
            stats_text = [
                f"Time Survived: {self.stats.get('time_str', '0:00')}",
                f"Enemies Slain: {self.stats.get('kills', 0)}",
                f"Level Reached: {self.stats.get('level', 1)}",
                f"Weapons: {', '.join(self.stats.get('weapons', []))}",
            ]

            for i, text in enumerate(stats_text):
                text_surface = self.font_medium.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, stats_y + i * 30))

        # 4. Two buttons: "PLAY AGAIN" and "MAIN MENU", centered, y=480 and y=550
        mouse_pos = pygame.mouse.get_pos()
        go_buttons = [("PLAY AGAIN", 480), ("MAIN MENU", 550)]
        for i, (label, y) in enumerate(go_buttons):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, y, 200, 50)
            highlighted = rect.collidepoint(mouse_pos) or (self.keyboard_active and i == self.selected_index)
            pygame.draw.rect(screen, (60, 45, 25) if highlighted else (40, 30, 20), rect)
            pygame.draw.rect(screen, GOLD, rect, 2)
            text_surf = self.font_small.render(label, True, (255, 255, 255))
            screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y + 15))
