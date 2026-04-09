import pygame
import random
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GOLD,
    TITLE_FONT_SIZE,
    STATE_LOBBY,
    MAIN_MENU_PARTICLE_INITIAL_COUNT,
    MAIN_MENU_PARTICLE_FADE_RATE,
    MAIN_MENU_PARTICLE_SPAWN_SIZE_MIN,
    MAIN_MENU_PARTICLE_SPAWN_SIZE_MAX,
    MAIN_MENU_PARTICLE_SPAWN_ALPHA_MIN,
    MAIN_MENU_PARTICLE_SPAWN_ALPHA_MAX,
)

class MainMenu:
    def __init__(self):
        self.next_scene = None
        self.next_scene_kwargs = {}
        self.selected_index = 0  # keyboard nav: 0=NEW RUN, 1=STATS, 2=SETTINGS, 3=QUIT
        self.keyboard_active = False
        self.particles = []

        self.font_title = pygame.font.SysFont("serif", TITLE_FONT_SIZE)
        self.font_sub = pygame.font.SysFont("serif", 24)

        # Initialize particles
        for _ in range(MAIN_MENU_PARTICLE_INITIAL_COUNT):
            self.particles.append({
                "pos": pygame.Vector2(random.randint(0, SCREEN_WIDTH), random.randint(-SCREEN_HEIGHT, 0)),
                "vel": pygame.Vector2(random.uniform(-10, 10), random.uniform(50, 100)),
                "size": random.randint(MAIN_MENU_PARTICLE_SPAWN_SIZE_MIN, MAIN_MENU_PARTICLE_SPAWN_SIZE_MAX),
                "alpha": random.randint(50, 255),
                "color": (random.randint(200, 255), random.randint(50, 150), random.randint(0, 50))  # Ember colors
            })

    def _spawn_particle(self, from_top: bool) -> None:
        if from_top:
            self.particles.append({
                "pos": pygame.Vector2(random.randint(0, SCREEN_WIDTH), -10),
                "vel": pygame.Vector2(random.uniform(-10, 10), random.uniform(50, 200)),
                "size": random.randint(MAIN_MENU_PARTICLE_SPAWN_SIZE_MIN, MAIN_MENU_PARTICLE_SPAWN_SIZE_MAX),
                "alpha": random.randint(MAIN_MENU_PARTICLE_SPAWN_ALPHA_MIN, MAIN_MENU_PARTICLE_SPAWN_ALPHA_MAX),
                "color": (random.randint(200, 255), random.randint(50, 150), random.randint(0, 50)),
            })
            return

        self.particles.append({
            "pos": pygame.Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 10),
            "vel": pygame.Vector2(random.uniform(-10, 10), random.uniform(-50, -200)),
            "size": random.randint(MAIN_MENU_PARTICLE_SPAWN_SIZE_MIN, MAIN_MENU_PARTICLE_SPAWN_SIZE_MAX),
            "alpha": random.randint(MAIN_MENU_PARTICLE_SPAWN_ALPHA_MIN, MAIN_MENU_PARTICLE_SPAWN_ALPHA_MAX),
            "color": (random.randint(0, 50), random.randint(50, 150), random.randint(200, 255)),
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
                        self.next_scene = STATE_LOBBY
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
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        return

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
                    actions = [STATE_LOBBY, "stats", "settings", None]
                    action = actions[self.selected_index]
                    if action:
                        self.next_scene = action
                    else:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                        return

            elif event.type == pygame.QUIT:
                return

    def update(self, dt):
        """Update the main menu state."""
        # Update particles
        for particle in self.particles:
            # Drift downward + slight random x drift
            particle["pos"] += particle["vel"] * dt

            # Fade out (alpha decreases)
            particle["alpha"] = max(0, particle["alpha"] - MAIN_MENU_PARTICLE_FADE_RATE * dt)

        self._spawn_particle(from_top=True)
        self._spawn_particle(from_top=False)

        # Remove particles that are off-screen or have alpha <= 0
        self.particles = [
            p for p in self.particles
            if -20 < p["pos"].y < SCREEN_HEIGHT + 20 and p["alpha"] > 0
        ]

    def draw(self, screen):
        """Draw the main menu."""
        # 1. Fill screen with very dark color (15, 10, 25)
        screen.fill((15, 10, 25))

        # 2. Draw particles as small colored circles, faded by alpha ratio
        for particle in self.particles:
            ratio = max(0.0, particle["alpha"] / 255.0)
            draw_color = tuple(int(c * ratio) for c in particle["color"])
            pygame.draw.circle(screen, draw_color, (int(particle["pos"].x), int(particle["pos"].y)), particle["size"])

        # 3. Title "MYSTIC SIEGE" centered at y=160, large font, GOLD color
        #    with dark glow/shadow offset by 3px
        title = "MYSTIC SIEGE"
        title_surface = self.font_title.render(title, True, GOLD)
        title_shadow = self.font_title.render(title, True, (0, 0, 0))
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2 + 3, 160))
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 160))

        # 4. Buttons centered horizontally:
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
            text_surf = self.font_sub.render(label, True, (255, 255, 255))
            screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y + 15))
