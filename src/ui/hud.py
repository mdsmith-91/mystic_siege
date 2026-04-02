import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HP_COLOR, HP_LOW_COLOR, XP_COLOR, MAX_WEAPON_SLOTS,
    WEAPON_SLOT_PIP_COUNT, WEAPON_SLOT_PIP_RADIUS, WEAPON_SLOT_PIP_SPACING,
    WEAPON_SLOT_PIP_Y_OFFSET, WEAPON_SLOT_PIP_FILLED_COLOR, WEAPON_SLOT_PIP_EMPTY_COLOR,
)

class HUD:
    def __init__(self):
        pass

    def draw_threat_arrows(self, screen, player, enemy_group, camera):
        """Draw arrows pointing to enemies that are offscreen."""
        # Get screen boundaries
        screen_left = camera.offset.x
        screen_right = camera.offset.x + SCREEN_WIDTH
        screen_top = camera.offset.y
        screen_bottom = camera.offset.y + SCREEN_HEIGHT

        # Track how many arrows we've drawn
        arrows_drawn = 0

        # For each enemy, check if it's offscreen
        for enemy in enemy_group:
            if arrows_drawn >= 8:  # Max 8 arrows
                break

            # Get enemy position relative to screen
            enemy_left = enemy.rect.left
            enemy_right = enemy.rect.right
            enemy_top = enemy.rect.top
            enemy_bottom = enemy.rect.bottom

            # Check if enemy is offscreen
            offscreen_left = enemy_right < screen_left
            offscreen_right = enemy_left > screen_right
            offscreen_top = enemy_bottom < screen_top
            offscreen_bottom = enemy_top > screen_bottom

            # Only draw arrow if enemy is more than 400px offscreen
            if (offscreen_left or offscreen_right or offscreen_top or offscreen_bottom):
                # Calculate center of enemy
                enemy_center_x = (enemy_left + enemy_right) / 2
                enemy_center_y = (enemy_top + enemy_bottom) / 2

                # Calculate screen edge where arrow should point
                arrow_x, arrow_y = 0, 0
                arrow_color = (255, 0, 0)  # Default to red

                # Determine which edge the arrow should point to
                if offscreen_left:
                    arrow_x = 0
                    arrow_y = enemy_center_y - camera.offset.y
                    # Adjust to screen edge
                    if arrow_y < 0:
                        arrow_y = 0
                    elif arrow_y > SCREEN_HEIGHT:
                        arrow_y = SCREEN_HEIGHT
                elif offscreen_right:
                    arrow_x = SCREEN_WIDTH
                    arrow_y = enemy_center_y - camera.offset.y
                    # Adjust to screen edge
                    if arrow_y < 0:
                        arrow_y = 0
                    elif arrow_y > SCREEN_HEIGHT:
                        arrow_y = SCREEN_HEIGHT
                elif offscreen_top:
                    arrow_x = enemy_center_x - camera.offset.x
                    arrow_y = 0
                    # Adjust to screen edge
                    if arrow_x < 0:
                        arrow_x = 0
                    elif arrow_x > SCREEN_WIDTH:
                        arrow_x = SCREEN_WIDTH
                elif offscreen_bottom:
                    arrow_x = enemy_center_x - camera.offset.x
                    arrow_y = SCREEN_HEIGHT
                    # Adjust to screen edge
                    if arrow_x < 0:
                        arrow_x = 0
                    elif arrow_x > SCREEN_WIDTH:
                        arrow_x = SCREEN_WIDTH

                # Draw arrow
                pygame.draw.polygon(screen, arrow_color, [
                    (arrow_x, arrow_y),
                    (arrow_x - 10, arrow_y - 5),
                    (arrow_x - 10, arrow_y + 5)
                ])
                arrows_drawn += 1

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

        # 1b. Player stat block (top-left, below HP bar)
        #     Always show Speed and Armor; show others only when non-default
        stat_font = pygame.font.SysFont("serif", 14)
        stat_lines = [
            (f"SPD  {int(player.speed / player.base_speed * 100)}%", (200, 200, 200)),
            (f"ARM  {int(player.armor)}%", (200, 200, 200)),
        ]
        if player.cooldown_reduction > 0:
            stat_lines.append((f"CDR  {int(player.cooldown_reduction * 100)}%", (180, 220, 255)))
        if player.damage_multiplier > 1.0:
            stat_lines.append((f"DMG  {player.damage_multiplier:.1f}x", (255, 200, 120)))
        if player.crit_chance > 0:
            stat_lines.append((f"CRIT  {int(player.crit_chance * 100)}%", (255, 230, 80)))
        if player.regen_rate > 0:
            stat_lines.append((f"REGEN  {player.regen_rate:.1f}/s", (120, 255, 160)))

        stat_y = 48
        for label, color in stat_lines:
            surf = stat_font.render(label, True, color)
            screen.blit(surf, (20, stat_y))
            stat_y += 16

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

        # Text: "LVL 7" on left side of bar, vertically centered
        font = pygame.font.SysFont("serif", 16)
        text = font.render(f"LVL {xp_system.current_level}", True, (255, 255, 255))
        screen.blit(text, (10, xp_bar_rect.centery - text.get_height() // 2))

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
        kill_text = f"KILLS  {player.kill_count}"
        text = font.render(kill_text, True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH - text.get_width() - 10, 20))

        # 5. Weapon slots (bottom-right, MAX_WEAPON_SLOTS slots of 40x40):
        #    All slots always drawn — empty slots show a dim border, occupied slots gold
        weapon_slots_x = SCREEN_WIDTH - (MAX_WEAPON_SLOTS * 45 + 5)
        weapon_slots_y = SCREEN_HEIGHT - 75
        font = pygame.font.SysFont("serif", 20)

        for i in range(MAX_WEAPON_SLOTS):
            slot_rect = pygame.Rect(weapon_slots_x + i * 45, weapon_slots_y, 40, 40)
            pygame.draw.rect(screen, (40, 40, 40), slot_rect)

            if i < len(player.weapons):
                # Occupied slot: gold border + weapon initial
                pygame.draw.rect(screen, (255, 215, 0), slot_rect, 2)
                weapon_name = player.weapons[i].name
                letter = weapon_name[0] if weapon_name else "?"
                text = font.render(letter, True, (255, 255, 255))
                screen.blit(text, text.get_rect(center=slot_rect.center))
                # Level pip dots: filled pips up to weapon.level, empty pips beyond
                weapon_level = player.weapons[i].level
                total_pip_width = (WEAPON_SLOT_PIP_COUNT - 1) * WEAPON_SLOT_PIP_SPACING
                pip_start_x = slot_rect.centerx - total_pip_width // 2
                pip_y = slot_rect.bottom - WEAPON_SLOT_PIP_Y_OFFSET - WEAPON_SLOT_PIP_RADIUS
                for p in range(WEAPON_SLOT_PIP_COUNT):
                    pip_x = pip_start_x + p * WEAPON_SLOT_PIP_SPACING
                    color = WEAPON_SLOT_PIP_FILLED_COLOR if p < weapon_level else WEAPON_SLOT_PIP_EMPTY_COLOR
                    pygame.draw.circle(screen, color, (pip_x, pip_y), WEAPON_SLOT_PIP_RADIUS)
            else:
                # Empty slot: dim border only
                pygame.draw.rect(screen, (80, 80, 80), slot_rect, 1)

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

        # 7. FPS counter (bottom-left, above LVL field, if show_fps): f"FPS: {fps:.0f}"
        if show_fps:
            font = pygame.font.SysFont("serif", 16)
            fps_text = f"FPS: {fps:.0f}"
            text = font.render(fps_text, True, (255, 255, 255))
            screen.blit(text, (10, SCREEN_HEIGHT - 55))

