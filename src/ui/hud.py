import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HP_COLOR, HP_MED_COLOR, HP_LOW_COLOR, XP_COLOR,
    MAX_WEAPON_SLOTS, WEAPON_SLOT_PIP_COUNT, WEAPON_SLOT_PIP_RADIUS, WEAPON_SLOT_PIP_SPACING,
    WEAPON_SLOT_PIP_Y_OFFSET, WEAPON_SLOT_PIP_FILLED_COLOR, WEAPON_SLOT_PIP_EMPTY_COLOR,
    CRIT_CHANCE_BASE, PICKUP_RADIUS, THREAT_ARROW_COLOR,
)

# Arrow geometry: tip distance from edge, half-width of arrow base
_ARROW_TIP = 15
_ARROW_DEPTH = 14
_ARROW_HALF = 8


class HUD:
    def __init__(self):
        self.font_16 = pygame.font.SysFont("serif", 16)
        self.font_14 = pygame.font.SysFont("serif", 14)
        self.font_32 = pygame.font.SysFont("serif", 32)
        self.font_20 = pygame.font.SysFont("serif", 20)
        self.font_48 = pygame.font.SysFont("serif", 48)

    def draw_threat_arrows(self, screen, player, enemy_group, camera):
        """Draw arrows at screen edges pointing toward offscreen enemies."""
        screen_left = camera.offset.x
        screen_right = camera.offset.x + SCREEN_WIDTH
        screen_top = camera.offset.y
        screen_bottom = camera.offset.y + SCREEN_HEIGHT

        # Safe range for the sliding axis so the arrow body stays on-screen
        clamp_min = _ARROW_TIP + _ARROW_HALF
        clamp_x_max = SCREEN_WIDTH - clamp_min
        clamp_y_max = SCREEN_HEIGHT - clamp_min

        arrows_drawn = 0
        for enemy in enemy_group:
            if arrows_drawn >= 8:
                break

            offscreen_left = enemy.rect.right < screen_left
            offscreen_right = enemy.rect.left > screen_right
            offscreen_top = enemy.rect.bottom < screen_top
            offscreen_bottom = enemy.rect.top > screen_bottom

            if not (offscreen_left or offscreen_right or offscreen_top or offscreen_bottom):
                continue

            cx = (enemy.rect.left + enemy.rect.right) / 2 - camera.offset.x
            cy = (enemy.rect.top + enemy.rect.bottom) / 2 - camera.offset.y

            if offscreen_left:
                # Arrow on left edge, tip points left
                ay = max(clamp_min, min(clamp_y_max, cy))
                tip = (_ARROW_TIP, ay)
                poly = [tip, (_ARROW_TIP + _ARROW_DEPTH, ay - _ARROW_HALF),
                              (_ARROW_TIP + _ARROW_DEPTH, ay + _ARROW_HALF)]
            elif offscreen_right:
                # Arrow on right edge, tip points right
                ay = max(clamp_min, min(clamp_y_max, cy))
                tip = (SCREEN_WIDTH - _ARROW_TIP, ay)
                poly = [tip, (SCREEN_WIDTH - _ARROW_TIP - _ARROW_DEPTH, ay - _ARROW_HALF),
                              (SCREEN_WIDTH - _ARROW_TIP - _ARROW_DEPTH, ay + _ARROW_HALF)]
            elif offscreen_top:
                # Arrow on top edge, tip points up
                ax = max(clamp_min, min(clamp_x_max, cx))
                tip = (ax, _ARROW_TIP)
                poly = [tip, (ax - _ARROW_HALF, _ARROW_TIP + _ARROW_DEPTH),
                              (ax + _ARROW_HALF, _ARROW_TIP + _ARROW_DEPTH)]
            else:
                # Arrow on bottom edge, tip points down
                ax = max(clamp_min, min(clamp_x_max, cx))
                tip = (ax, SCREEN_HEIGHT - _ARROW_TIP)
                poly = [tip, (ax - _ARROW_HALF, SCREEN_HEIGHT - _ARROW_TIP - _ARROW_DEPTH),
                              (ax + _ARROW_HALF, SCREEN_HEIGHT - _ARROW_TIP - _ARROW_DEPTH)]

            pygame.draw.polygon(screen, THREAT_ARROW_COLOR, poly)
            arrows_drawn += 1

    def draw(self, screen, player, xp_system, wave_manager, show_fps=False, fps=0):
        """Draw all in-game overlay UI in screen space (no camera offset)."""

        # 1. HP Bar (top-left, x=20, y=20)
        hp_bar_rect = pygame.Rect(20, 20, 200, 20)
        pygame.draw.rect(screen, (30, 30, 30), hp_bar_rect)

        hp_ratio = max(0.0, player.hp / player.max_hp)
        fill_width = int(200 * hp_ratio)

        if hp_ratio > 0.5:
            fill_color = HP_COLOR
        elif hp_ratio > 0.25:
            fill_color = HP_MED_COLOR
        else:
            fill_color = HP_LOW_COLOR

        pygame.draw.rect(screen, fill_color, pygame.Rect(20, 20, fill_width, 20))

        hp_display = max(0, int(player.hp))
        text = self.font_16.render(f"HP  {hp_display} / {int(player.max_hp)}", True, (255, 255, 255))
        screen.blit(text, (230, 20))

        # 1b. Player stat block (top-left, below HP bar)
        #     Always show Speed; show others only when non-default
        stat_lines = []
        if player.speed > player.base_speed:
            spd_pct = int(player.speed / player.base_speed * 100) if player.base_speed else 100
            stat_lines.append((f"SPD  {spd_pct}%", (200, 200, 200)))
        if player.armor > 0:
            stat_lines.append((f"ARM  {int(player.armor)}%", (192, 200, 215)))
        if player.cooldown_reduction > 0:
            stat_lines.append((f"CDR  {int(player.cooldown_reduction * 100)}%", (180, 220, 255)))
        if player.damage_multiplier > 1.0:
            stat_lines.append((f"DMG  {player.damage_multiplier:.1f}x", (255, 200, 120)))
        if player.crit_chance > CRIT_CHANCE_BASE:
            stat_lines.append((f"CRIT  {int(player.crit_chance * 100)}%", (255, 230, 80)))
        if player.regen_rate > 0:
            stat_lines.append((f"REGEN  {player.regen_rate:.1f}/s", (120, 255, 160)))
        if player.spell_damage_multiplier > 1.0:
            stat_lines.append((f"SPELL  {player.spell_damage_multiplier:.2f}x", (180, 140, 255)))
        if player.xp_multiplier > 1.0:
            stat_lines.append((f"XP  {player.xp_multiplier:.2f}x", (200, 255, 200)))
        if player.pickup_radius > PICKUP_RADIUS:
            stat_lines.append((f"RAD  {int(player.pickup_radius)}", (200, 200, 255)))

        stat_y = 48
        for label, color in stat_lines:
            surf = self.font_14.render(label, True, color)
            screen.blit(surf, (20, stat_y))
            stat_y += 16

        # 2. XP Bar (flush with screen bottom, full width)
        xp_bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20)
        pygame.draw.rect(screen, (30, 30, 30), xp_bar_rect)

        xp_progress = xp_system.xp_progress()
        fill_width = int(SCREEN_WIDTH * xp_progress)

        if fill_width > 0:
            # Glow: semi-transparent wider bar drawn underneath the main bar
            glow_surf = pygame.Surface((fill_width, 24), pygame.SRCALPHA)
            glow_surf.fill((*XP_COLOR, 80))
            screen.blit(glow_surf, (0, SCREEN_HEIGHT - 22))
            pygame.draw.rect(screen, XP_COLOR, pygame.Rect(0, SCREEN_HEIGHT - 20, fill_width, 20))

        text = self.font_16.render(f"LVL {xp_system.current_level}", True, (255, 255, 255))
        screen.blit(text, (10, xp_bar_rect.centery - text.get_height() // 2))

        # 3. Timer (top-center)
        timer_text = wave_manager.get_elapsed_str()
        timer_surface = self.font_32.render(timer_text, True, (255, 255, 255))
        timer_shadow = self.font_32.render(timer_text, True, (0, 0, 0))
        tx = SCREEN_WIDTH // 2 - timer_surface.get_width() // 2
        screen.blit(timer_shadow, (tx + 2, 12))
        screen.blit(timer_surface, (tx, 10))

        # 4. Kill counter and hero class (top-right)
        kill_text = self.font_16.render(f"KILLS  {player.kill_count}", True, (255, 255, 255))
        screen.blit(kill_text, (SCREEN_WIDTH - kill_text.get_width() - 10, 20))
        class_text = self.font_14.render(player.hero_class.upper(), True, (180, 160, 120))
        screen.blit(class_text, (SCREEN_WIDTH - class_text.get_width() - 10, 40))

        # 5. Weapon slots (bottom-right)
        weapon_slots_x = SCREEN_WIDTH - (MAX_WEAPON_SLOTS * 45 + 5)
        weapon_slots_y = SCREEN_HEIGHT - 65

        for i in range(MAX_WEAPON_SLOTS):
            slot_rect = pygame.Rect(weapon_slots_x + i * 45, weapon_slots_y, 40, 40)
            pygame.draw.rect(screen, (40, 40, 40), slot_rect)

            if i < len(player.weapons):
                pygame.draw.rect(screen, (255, 215, 0), slot_rect, 2)
                weapon_name = player.weapons[i].name
                letter = weapon_name[0] if weapon_name else "?"
                text = self.font_20.render(letter, True, (255, 255, 255))
                screen.blit(text, text.get_rect(center=slot_rect.center))
                weapon_level = player.weapons[i].level
                total_pip_width = (WEAPON_SLOT_PIP_COUNT - 1) * WEAPON_SLOT_PIP_SPACING
                pip_start_x = slot_rect.centerx - total_pip_width // 2
                pip_y = slot_rect.bottom - WEAPON_SLOT_PIP_Y_OFFSET - WEAPON_SLOT_PIP_RADIUS
                for p in range(WEAPON_SLOT_PIP_COUNT):
                    pip_x = pip_start_x + p * WEAPON_SLOT_PIP_SPACING
                    color = WEAPON_SLOT_PIP_FILLED_COLOR if p < weapon_level else WEAPON_SLOT_PIP_EMPTY_COLOR
                    pygame.draw.circle(screen, color, (pip_x, pip_y), WEAPON_SLOT_PIP_RADIUS)
            else:
                pygame.draw.rect(screen, (80, 80, 80), slot_rect, 1)

        # 6. Wave warning (center screen, fades out)
        warning = wave_manager.get_warning()
        if warning:
            warning_surface = self.font_48.render(warning, True, (255, 100, 0))
            warning_shadow = self.font_48.render(warning, True, (0, 0, 0))
            wx = SCREEN_WIDTH // 2 - warning_surface.get_width() // 2
            screen.blit(warning_shadow, (wx + 3, 203))
            screen.blit(warning_surface, (wx, 200))

        # 7. FPS counter (inside XP bar, right of LVL)
        if show_fps:
            fps_text = self.font_16.render(f"FPS: {fps:.0f}", True, (255, 255, 255))
            screen.blit(fps_text, (90, xp_bar_rect.centery - fps_text.get_height() // 2))
