import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, STATE_MENU
from src.systems.save_system import SaveSystem


class StatsMenu:
    def __init__(self):
        self.next_scene = None
        self.next_scene_kwargs = {}

        self.font_title = pygame.font.SysFont("serif", 64)
        self.font_label = pygame.font.SysFont("serif", 28)
        self.font_small = pygame.font.SysFont("serif", 20)

        data = SaveSystem().data
        total_time = int(data.get("total_time_played", 0))
        best_time = int(data.get("best_time_survived", 0))
        self.rows = [
            ("Total Runs",          str(data.get("total_runs", 0))),
            ("Total Kills",         str(data.get("total_kills", 0))),
            ("Total Time Played",   self._fmt_hms(total_time)),
            ("Highest Level",       str(data.get("highest_level", 1))),
            ("Best Time Survived",  self._fmt_ms(best_time)),
        ]

    def _fmt_hms(self, seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _fmt_ms(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.next_scene = STATE_MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(mouse_pos):
                    self.next_scene = STATE_MENU
            elif event.type == pygame.QUIT:
                return

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((15, 10, 25))

        # Title
        title_surf = self.font_title.render("STATS", True, GOLD)
        title_shadow = self.font_title.render("STATS", True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        screen.blit(title_shadow, (cx - title_surf.get_width() // 2 + 3, 103))
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, 100))

        # Stat rows
        row_y = 230
        row_gap = 60
        col_label_x = cx - 220
        col_value_x = cx + 220

        for label, value in self.rows:
            label_surf = self.font_label.render(label, True, (160, 150, 140))
            value_surf = self.font_label.render(value, True, (255, 240, 180))
            screen.blit(label_surf, (col_label_x, row_y))
            screen.blit(value_surf, (col_value_x - value_surf.get_width(), row_y))
            # Divider line
            pygame.draw.line(screen, (50, 40, 30),
                             (col_label_x, row_y + label_surf.get_height() + 6),
                             (col_value_x, row_y + label_surf.get_height() + 6), 1)
            row_y += row_gap

        # BACK button
        back_rect = pygame.Rect(20, SCREEN_HEIGHT - 60, 100, 40)
        mouse_pos = pygame.mouse.get_pos()
        back_color = (80, 60, 30) if back_rect.collidepoint(mouse_pos) else (40, 30, 20)
        pygame.draw.rect(screen, back_color, back_rect)
        pygame.draw.rect(screen, GOLD, back_rect, 2)
        back_text = self.font_small.render("BACK", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2,
                                back_rect.centery - back_text.get_height() // 2))
