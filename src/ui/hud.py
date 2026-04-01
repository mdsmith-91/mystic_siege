import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, HP_COLOR, HP_LOW_COLOR, XP_COLOR

class HUD:
    def __init__(self):
        pass

    def draw(self, screen, player, xp_system, wave_manager, show_fps=False, fps=0):
        """Draw all in-game overlay UI in screen space (no camera offset)."""

        # 1. HP Bar (top-left, x=20, y=20):
        #    Background rect 200x20, dark
        #    Fill rect scaled to hp/max_hp ratio
        #    Color: HP_COLOR if >50%, yellow if >25%, HP_LOW_COLOR otherwise
        #    Text: "HP  85 / 150" to the right of bar
        hp_bar_rect = pygame.Rect(20, 20, 200, 20)
        pygame.draw.rect(screen, (30, 30, 30), hp_bar_rect)  # Dark background

        # Fill rect scaled to hp/max_hp ratio
        hp_ratio = player.hp / player.max_hp
        fill_width = int(200 * hp_ratio)

        # Color: HP_COLOR if >50%, yellow if >25%, HP_LOW_COLOR otherwise
        if hp_ratio > 0.5:
            fill_color = HP_COLOR
        elif hp_ratio > 0.25:
            fill_color = (255, 255, 0)  # Yellow
        else:
            fill_color = HP_LOW_COLOR

        fill_rect = pygame.Rect(20, 20, fill_width, 20)
        pygame.draw.rect(screen, fill_color, fill_rect)

        # Text: "HP  85 / 150" to the right of bar
        font = pygame.font.SysFont("serif", 16)
        text = font.render(f"HP  {int(player.hp)} / {int(player.max_hp)}", True, (255, 255, 255))
        screen.blit(text, (230, 20))

        # 2. XP Bar (bottom of screen, full width, y=SCREEN_HEIGHT-30, height=20):
        #    Background full-width dark rect
        #    Fill rect scaled to xp_system.xp_progress()
        #    Color: XP_COLOR with glow (draw twice, outer with alpha 80)
        #    Text: "LVL 7" on left side of bar
        xp_bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 20)
        pygame.draw.rect(screen, (30, 30, 30), xp_bar_rect)  # Dark background

        # Fill rect scaled to xp_system.xp_progress()
        xp_progress = xp_system.xp_progress()
        fill_width = int(SCREEN_WIDTH * xp_progress)

        # Draw twice for glow effect (outer with alpha 80)
        glow_rect = pygame.Rect(0, SCREEN_HEIGHT - 30, fill_width, 20)
        pygame.draw.rect(screen, XP_COLOR, glow_rect)

        # Draw the inner bar with full opacity
        inner_rect = pygame.Rect(0, SCREEN_HEIGHT - 30, fill_width, 20)
        pygame.draw.rect(screen, XP_COLOR, inner_rect)

        # Text: "LVL 7" on left side of bar
        font = pygame.font.SysFont("serif", 16)
        text = font.render(f"LVL {xp_system.current_level}", True, (255, 255, 255))
        screen.blit(text, (10, SCREEN_HEIGHT - 25))

        # 3. Timer (top-center):
        #    wave_manager.get_elapsed_str() in large font, white with dark shadow
        font = pygame.font.SysFont("serif", 32)
        timer_text = wave_manager.get_elapsed_str()
        timer_surface = font.render(timer_text, True, (255, 255, 255))
        timer_shadow = font.render(timer_text, True, (0, 0, 0))
        screen.blit(timer_shadow, (SCREEN_WIDTH // 2 - timer_surface.get_width() // 2 + 2, 10))
        screen.blit(timer_surface, (SCREEN_WIDTH // 2 - timer_surface.get_width() // 2, 10))

        # 4. Kill counter (top-right):
        #    "✦ {player.kill_count}" right-aligned
        font = pygame.font.SysFont("serif", 16)
        kill_text = f"✦ {player.kill_count}"
        text = font.render(kill_text, True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH - text.get_width() - 10, 20))

        # 5. Weapon slots (bottom-right, 6 slots of 40x40):
        #    Dark background per slot
        #    Gold border on occupied slots
        #    First letter of weapon name centered in slot
        #    Slot color = weapon's projectile_color or a default per weapon type
        weapon_slots_x = SCREEN_WIDTH - 250
        weapon_slots_y = SCREEN_HEIGHT - 60

        for i, weapon in enumerate(player.weapons):
            slot_rect = pygame.Rect(weapon_slots_x + i * 45, weapon_slots_y, 40, 40)

            # Dark background per slot
            pygame.draw.rect(screen, (40, 40, 40), slot_rect)

            # Gold border on occupied slots
            pygame.draw.rect(screen, (255, 215, 0), slot_rect, 2)

            # First letter of weapon name centered in slot
            weapon_name = weapon.name
            letter = weapon_name[0] if weapon_name else "?"
            font = pygame.font.SysFont("serif", 20)
            text = font.render(letter, True, (255, 255, 255))
            text_rect = text.get_rect(center=slot_rect.center)
            screen.blit(text, text_rect)

        # 6. Wave warning (center screen, fades out):
        #    wave_manager.get_warning() if non-empty
        #    Large red/orange text centered horizontally at y=200
        warning = wave_manager.get_warning()
        if warning:
            font = pygame.font.SysFont("serif", 48)
            warning_surface = font.render(warning, True, (255, 100, 0))  # Red/orange
            warning_shadow = font.render(warning, True, (0, 0, 0))
            screen.blit(warning_shadow, (SCREEN_WIDTH // 2 - warning_surface.get_width() // 2 + 3, 200))
            screen.blit(warning_surface, (SCREEN_WIDTH // 2 - warning_surface.get_width() // 2, 200))

        # 7. FPS counter (top-left corner, small, if show_fps): f"FPS: {fps:.0f}"
        if show_fps:
            font = pygame.font.SysFont("serif", 16)
            fps_text = f"FPS: {fps:.0f}"
            text = font.render(fps_text, True, (255, 255, 255))
            screen.blit(text, (10, SCREEN_HEIGHT - 30))