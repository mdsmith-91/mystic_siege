import pygame
import sys
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, TITLE_FONT_SIZE

class MainMenu:
    def __init__(self):
        self.next_scene = None
        self.next_scene_kwargs = {}
        self.selected_index = 0  # keyboard nav: 0=NEW RUN, 1=STATS, 2=SETTINGS, 3=QUIT
        self.keyboard_active = False
        self.particles = []

        # Initialize particles
        for _ in range(50):  # Start with some particles
            self.particles.append({
                "pos": pygame.Vector2(random.randint(0, SCREEN_WIDTH), random.randint(-SCREEN_HEIGHT, 0)),
                "vel": pygame.Vector2(random.uniform(-10, 10), random.uniform(50, 100)),
                "size": random.randint(1, 3),
                "alpha": random.randint(50, 255),
                "color": (random.randint(200, 255), random.randint(50, 150), random.randint(0, 50))  # Ember colors
            })

    def handle_events(self, events):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if "New Run" button was clicked
                    new_run_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 380, 240, 50)
                    if new_run_rect.collidepoint(mouse_pos):
                        self.next_scene = "class_select"
                        return

                    # Check if "Stats" button was clicked
                    stats_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 450, 240, 50)
                    if stats_rect.collidepoint(mouse_pos):
                        self.next_scene = "stats"
                        return

                    # Check if "Settings" button was clicked
                    settings_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 520, 240, 50)
                    if settings_rect.collidepoint(mouse_pos):
                        self.next_scene = "settings"
                        return

                    # Check if "Quit" button was clicked
                    quit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 590, 240, 50)
                    if quit_rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()

            elif event.type == pygame.MOUSEMOTION:
                self.keyboard_active = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.keyboard_active = True
                    self.selected_index = (self.selected_index - 1) % 4
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.keyboard_active = True
                    self.selected_index = (self.selected_index + 1) % 4
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    actions = ["class_select", "stats", "settings", None]
                    action = actions[self.selected_index]
                    if action:
                        self.next_scene = action
                    else:
                        pygame.quit()
                        sys.exit()

            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def update(self, dt):
        """Update the main menu state."""
        # Update particles
        for particle in self.particles:
            # Drift downward + slight random x drift
            particle["pos"] += particle["vel"] * dt

            # Fade out (alpha decreases)
            particle["alpha"] = max(0, particle["alpha"] - 100 * dt)

            # Spawn 2 new particles per frame at random x, top of screen
            if random.random() < 0.02:  # 2% chance per frame
                self.particles.append({
                    "pos": pygame.Vector2(random.randint(0, SCREEN_WIDTH), -10),
                    "vel": pygame.Vector2(random.uniform(-10, 10), random.uniform(50, 100)),
                    "size": random.randint(1, 3),
                    "alpha": random.randint(50, 255),
                    "color": (random.randint(200, 255), random.randint(50, 150), random.randint(0, 50))  # Ember colors
                })

        # Remove particles that are off-screen or have alpha <= 0
        self.particles = [p for p in self.particles if p["pos"].y < SCREEN_HEIGHT + 20 and p["alpha"] > 0]

    def draw(self, screen):
        """Draw the main menu."""
        # 1. Fill screen with very dark color (15, 10, 25)
        screen.fill((15, 10, 25))

        # 2. Draw particles as small colored circles
        for particle in self.particles:
            alpha = min(255, max(0, particle["alpha"]))
            color = (*particle["color"], alpha)
            pygame.draw.circle(screen, color, (int(particle["pos"].x), int(particle["pos"].y)), particle["size"])

        # 3. Title "MYSTIC SIEGE" centered at y=160, large font, GOLD color
        #    with dark glow/shadow offset by 3px
        font = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        title = "MYSTIC SIEGE"
        title_surface = font.render(title, True, GOLD)
        title_shadow = font.render(title, True, (0, 0, 0))
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2 + 3, 160))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 160))

        # 4. Subtitle "A Medieval Survivor" smaller, gray, below title
        subtitle_font = pygame.font.SysFont("serif", 24)
        subtitle = "A Medieval Survivor"
        subtitle_surface = subtitle_font.render(subtitle, True, (150, 150, 150))
        screen.blit(subtitle_surface, (SCREEN_WIDTH // 2 - subtitle_surface.get_width() // 2, 240))

        # 5. Buttons centered horizontally:
        #    "NEW RUN" at y=380
        #    "QUIT"    at y=450
        #    Each button: dark rect 240x50, gold border, white text
        #    Highlighted button: slightly lighter background
        mouse_pos = pygame.mouse.get_pos()

        buttons = [
            ("NEW RUN",  380),
            ("STATS",    450),
            ("SETTINGS", 520),
            ("QUIT",     590),
        ]
        for i, (label, y) in enumerate(buttons):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, y, 240, 50)
            highlighted = rect.collidepoint(mouse_pos) or (self.keyboard_active and i == self.selected_index)
            button_color = (40, 30, 20) if highlighted else (30, 20, 10)
            pygame.draw.rect(screen, button_color, rect)
            pygame.draw.rect(screen, GOLD, rect, 2)
            text_surf = subtitle_font.render(label, True, (255, 255, 255))
            screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y + 15))