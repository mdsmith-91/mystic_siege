import math

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HP_COLOR, HP_MED_COLOR, HP_LOW_COLOR, XP_COLOR,
    MAX_WEAPON_SLOTS, WEAPON_SLOT_PIP_COUNT, WEAPON_SLOT_PIP_RADIUS, WEAPON_SLOT_PIP_SPACING,
    WEAPON_SLOT_PIP_Y_OFFSET, WEAPON_SLOT_PIP_FILLED_COLOR, WEAPON_SLOT_PIP_EMPTY_COLOR,
    CRIT_CHANCE_BASE, PICKUP_RADIUS, THREAT_ARROW_COLOR,
    HUD_SAFE_TOP, HUD_SAFE_BOTTOM, HUD_SAFE_LEFT, HUD_SAFE_RIGHT,
    WHITE, BLACK, GOLD, UI_BG, REVIVE_DURATION,
    HUD_PANEL_PADDING, HUD_PANEL_BAR_HEIGHT, HUD_PANEL_WEAPON_SLOT_SIZE, HUD_PANEL_WEAPON_SLOT_WIDTH,
    HUD_PANEL_WEAPON_SLOT_GAP, HUD_REVIVE_RING_RADIUS, HUD_REVIVE_RING_WIDTH,
    HUD_PANEL_TUPLES,
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
        self._text_cache: dict[tuple[int, str, tuple[int, int, int]], pygame.Surface] = {}

    def _render_text(
        self,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        key = (id(font), text, color)
        cached = self._text_cache.get(key)
        if cached is None:
            cached = font.render(text, True, color)
            self._text_cache[key] = cached
        return cached

    def _build_edge_arrow(self, view_rect: pygame.Rect, screen_pos: pygame.Vector2):
        screen_left = view_rect.left
        screen_right = view_rect.right
        screen_top = view_rect.top
        screen_bottom = view_rect.bottom
        # Sliding-axis clamps — keep arrow body inside safe zones on each edge
        clamp_x_min = HUD_SAFE_LEFT   + _ARROW_TIP + _ARROW_HALF
        clamp_x_max = SCREEN_WIDTH  - HUD_SAFE_RIGHT  - _ARROW_TIP - _ARROW_HALF
        clamp_y_min = HUD_SAFE_TOP    + _ARROW_TIP + _ARROW_HALF
        clamp_y_max = SCREEN_HEIGHT - HUD_SAFE_BOTTOM - _ARROW_TIP - _ARROW_HALF
        cx = screen_pos.x
        cy = screen_pos.y

        offscreen_left = cx < 0
        offscreen_right = cx > SCREEN_WIDTH
        offscreen_top = cy < 0
        offscreen_bottom = cy > SCREEN_HEIGHT

        if not (offscreen_left or offscreen_right or offscreen_top or offscreen_bottom):
            return None, None

        if offscreen_left:
            ay = max(clamp_y_min, min(clamp_y_max, cy))
            tip = (HUD_SAFE_LEFT + _ARROW_TIP, ay)
            poly = [
                tip,
                (HUD_SAFE_LEFT + _ARROW_TIP + _ARROW_DEPTH, ay - _ARROW_HALF),
                (HUD_SAFE_LEFT + _ARROW_TIP + _ARROW_DEPTH, ay + _ARROW_HALF),
            ]
        elif offscreen_right:
            ay = max(clamp_y_min, min(clamp_y_max, cy))
            tip = (SCREEN_WIDTH - HUD_SAFE_RIGHT - _ARROW_TIP, ay)
            poly = [
                tip,
                (SCREEN_WIDTH - HUD_SAFE_RIGHT - _ARROW_TIP - _ARROW_DEPTH, ay - _ARROW_HALF),
                (SCREEN_WIDTH - HUD_SAFE_RIGHT - _ARROW_TIP - _ARROW_DEPTH, ay + _ARROW_HALF),
            ]
        elif offscreen_top:
            ax = max(clamp_x_min, min(clamp_x_max, cx))
            tip = (ax, HUD_SAFE_TOP + _ARROW_TIP)
            poly = [
                tip,
                (ax - _ARROW_HALF, HUD_SAFE_TOP + _ARROW_TIP + _ARROW_DEPTH),
                (ax + _ARROW_HALF, HUD_SAFE_TOP + _ARROW_TIP + _ARROW_DEPTH),
            ]
        else:
            ax = max(clamp_x_min, min(clamp_x_max, cx))
            tip = (ax, SCREEN_HEIGHT - HUD_SAFE_BOTTOM - _ARROW_TIP)
            poly = [
                tip,
                (ax - _ARROW_HALF, SCREEN_HEIGHT - HUD_SAFE_BOTTOM - _ARROW_TIP - _ARROW_DEPTH),
                (ax + _ARROW_HALF, SCREEN_HEIGHT - HUD_SAFE_BOTTOM - _ARROW_TIP - _ARROW_DEPTH),
            ]

        return poly, tip

    def draw_threat_arrows(self, screen, enemy_group, camera, players=None):
        """Draw arrows at screen edges pointing toward offscreen enemies and downed teammates."""
        view_rect = camera.get_view_rect()

        arrows_drawn = 0
        for enemy in enemy_group:
            if arrows_drawn >= 8:
                break
            if (
                enemy.rect.right >= view_rect.left
                and enemy.rect.left <= view_rect.right
                and enemy.rect.bottom >= view_rect.top
                and enemy.rect.top <= view_rect.bottom
            ):
                continue

            poly, _tip = self._build_edge_arrow(view_rect, camera.world_to_screen(enemy.pos))
            if poly is None:
                continue

            pygame.draw.polygon(screen, THREAT_ARROW_COLOR, poly)
            arrows_drawn += 1

        if not players or len(players) <= 1:
            return

        for player in players:
            if not player.is_downed:
                continue

            poly, tip = self._build_edge_arrow(view_rect, camera.world_to_screen(player.pos))
            if poly is None or tip is None:
                continue

            slot = getattr(player, "slot", None)
            slot_color = getattr(slot, "color", GOLD)
            pygame.draw.polygon(screen, slot_color, poly)
            pygame.draw.polygon(screen, WHITE, poly, 2)

            label = self.font_14.render(f"P{slot.index + 1}" if slot is not None else "REV", True, WHITE)
            label_rect = label.get_rect()
            label_rect.center = (int(tip[0]), int(tip[1]))
            if tip[0] <= HUD_SAFE_LEFT + _ARROW_TIP + 1:
                label_rect.midleft = (int(poly[1][0] + 4), int(tip[1]))
            elif tip[0] >= SCREEN_WIDTH - HUD_SAFE_RIGHT - _ARROW_TIP - 1:
                label_rect.midright = (int(poly[1][0] - 4), int(tip[1]))
            elif tip[1] <= HUD_SAFE_TOP + _ARROW_TIP + 1:
                label_rect.midtop = (int(tip[0]), int(poly[1][1] + 2))
            else:
                label_rect.midbottom = (int(tip[0]), int(poly[1][1] - 2))
            screen.blit(label, label_rect)

    def _draw_bar(
        self,
        screen,
        rect: pygame.Rect,
        ratio: float,
        fill_color: tuple[int, int, int],
        background_color: tuple[int, int, int] = (30, 30, 30),
    ) -> None:
        pygame.draw.rect(screen, background_color, rect, border_radius=4)
        ratio = max(0.0, min(1.0, ratio))
        fill_width = int(rect.width * ratio)
        if fill_width > 0:
            fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=4)

    def _draw_shared_info(self, screen, wave_manager, show_fps: bool, fps: float) -> None:
        timer_text = wave_manager.get_elapsed_str()
        timer_surface = self._render_text(self.font_32, timer_text, WHITE)
        timer_shadow = self._render_text(self.font_32, timer_text, BLACK)
        tx = SCREEN_WIDTH // 2 - timer_surface.get_width() // 2
        screen.blit(timer_shadow, (tx + 2, 12))
        screen.blit(timer_surface, (tx, 10))

        warning = wave_manager.get_warning()
        if warning:
            warning_surface = self._render_text(self.font_48, warning, (255, 100, 0))
            warning_shadow = self._render_text(self.font_48, warning, BLACK)
            wx = SCREEN_WIDTH // 2 - warning_surface.get_width() // 2
            screen.blit(warning_shadow, (wx + 3, 203))
            screen.blit(warning_surface, (wx, 200))

        if show_fps:
            fps_text = self._render_text(self.font_16, f"FPS {fps:.0f}", WHITE)
            fps_rect = fps_text.get_rect(midtop=(SCREEN_WIDTH // 2, 50))
            screen.blit(fps_text, fps_rect)

    def _draw_weapon_slots(
        self,
        screen,
        player,
        left: int,
        top: int,
        slot_size: int,
    ) -> None:
        slot_width = max(slot_size, HUD_PANEL_WEAPON_SLOT_WIDTH)
        for i in range(MAX_WEAPON_SLOTS):
            slot_x = left + i * (slot_width + HUD_PANEL_WEAPON_SLOT_GAP)
            slot_rect = pygame.Rect(slot_x, top, slot_width, slot_size)
            pygame.draw.rect(screen, (40, 40, 40), slot_rect, border_radius=4)

            if i >= len(player.weapons):
                pygame.draw.rect(screen, (80, 80, 80), slot_rect, 1, border_radius=4)
                continue

            pygame.draw.rect(screen, (255, 215, 0), slot_rect, 2, border_radius=4)
            weapon = player.weapons[i]
            letter = weapon.name[0] if weapon.name else "?"
            letter_font = self.font_16 if slot_size >= 36 else self.font_14
            text = self._render_text(letter_font, letter, WHITE)
            screen.blit(text, text.get_rect(center=slot_rect.center))

            pip_radius = min(WEAPON_SLOT_PIP_RADIUS, max(2, slot_size // 10))
            pip_spacing = max((pip_radius * 2) + 1, min(WEAPON_SLOT_PIP_SPACING, slot_rect.width // 6))
            pip_y_offset = max(4, min(WEAPON_SLOT_PIP_Y_OFFSET, slot_size // 5))
            total_pip_width = (WEAPON_SLOT_PIP_COUNT - 1) * pip_spacing
            pip_start_x = slot_rect.centerx - total_pip_width // 2
            pip_y = slot_rect.bottom - pip_y_offset - pip_radius
            for p in range(WEAPON_SLOT_PIP_COUNT):
                pip_x = pip_start_x + p * pip_spacing
                color = WEAPON_SLOT_PIP_FILLED_COLOR if p < weapon.level else WEAPON_SLOT_PIP_EMPTY_COLOR
                pygame.draw.circle(screen, color, (pip_x, pip_y), pip_radius)

    def _draw_revive_indicator(self, screen, player, slot_color, camera) -> None:
        if not player.is_downed:
            return

        center = camera.world_to_screen(player.pos)
        ring_rect = pygame.Rect(0, 0, HUD_REVIVE_RING_RADIUS * 2, HUD_REVIVE_RING_RADIUS * 2)
        ring_rect.center = (int(center.x), int(center.y))
        pygame.draw.circle(screen, (50, 50, 50), ring_rect.center, HUD_REVIVE_RING_RADIUS, HUD_REVIVE_RING_WIDTH)

        if REVIVE_DURATION > 0 and player.revive_timer > 0:
            progress = max(0.0, min(1.0, player.revive_timer / REVIVE_DURATION))
            pygame.draw.arc(
                screen,
                slot_color,
                ring_rect,
                -math.pi / 2,
                (-math.pi / 2) + (2 * math.pi * progress),
                HUD_REVIVE_RING_WIDTH,
            )

    def _draw_single_player(self, screen, player, xp_system, wave_manager, show_fps=False, fps=0):
        """Preserve the familiar 1P HUD layout."""

        hp_bar_rect = pygame.Rect(20, 20, 200, 20)
        hp_ratio = max(0.0, player.hp / player.max_hp)
        if hp_ratio > 0.5:
            fill_color = HP_COLOR
        elif hp_ratio > 0.25:
            fill_color = HP_MED_COLOR
        else:
            fill_color = HP_LOW_COLOR
        self._draw_bar(screen, hp_bar_rect, hp_ratio, fill_color)

        hp_display = max(0, int(player.hp))
        text = self._render_text(self.font_16, f"HP  {hp_display} / {int(player.max_hp)}", WHITE)
        screen.blit(text, (230, 20))

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
            stat_lines.append((f"CRIT  {round(player.crit_chance * 100)}%", (255, 230, 80)))
        if player.regen_rate > 0:
            stat_lines.append((f"REGEN  {player.regen_rate:.1f}/s", (120, 255, 160)))
        if player.spell_damage_multiplier > 1.0:
            spell_pct = round((player.spell_damage_multiplier - 1.0) * 100)
            stat_lines.append((f"SPELL  +{spell_pct}%", (180, 140, 255)))
        if player.xp_multiplier > 1.0:
            xp_pct = round((player.xp_multiplier - 1.0) * 100)
            stat_lines.append((f"XP  +{xp_pct}%", (200, 255, 200)))
        if player.pickup_radius > PICKUP_RADIUS:
            stat_lines.append((f"RAD  {int(player.pickup_radius)}", (200, 200, 255)))

        stat_y = 48
        for label, color in stat_lines:
            surf = self._render_text(self.font_14, label, color)
            screen.blit(surf, (20, stat_y))
            stat_y += 16

        xp_bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20)
        xp_progress = xp_system.xp_progress()
        self._draw_bar(screen, xp_bar_rect, xp_progress, XP_COLOR)

        lvl_text = self._render_text(self.font_16, f"LVL {xp_system.current_level}", WHITE)
        lvl_rect = lvl_text.get_rect(midleft=(10, xp_bar_rect.centery))
        screen.blit(lvl_text, lvl_rect)

        kill_text = self._render_text(self.font_16, f"KILLS  {player.kill_count}", WHITE)
        screen.blit(kill_text, (SCREEN_WIDTH - kill_text.get_width() - 10, 20))
        class_text = self._render_text(self.font_14, player.hero_class.upper(), (180, 160, 120))
        screen.blit(class_text, (SCREEN_WIDTH - class_text.get_width() - 10, 40))

        weapon_slot_width = max(40, HUD_PANEL_WEAPON_SLOT_WIDTH)
        total_weapon_width = (MAX_WEAPON_SLOTS * weapon_slot_width) + ((MAX_WEAPON_SLOTS - 1) * HUD_PANEL_WEAPON_SLOT_GAP)
        weapon_slots_x = SCREEN_WIDTH - total_weapon_width - 5
        weapon_slots_y = SCREEN_HEIGHT - 65
        self._draw_weapon_slots(screen, player, weapon_slots_x, weapon_slots_y, 40)

        self._draw_shared_info(screen, wave_manager, show_fps, fps)

    def _draw_player_panel(self, screen, player, xp_system, rect: pygame.Rect, slot, camera) -> None:
        panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel_surface.fill(UI_BG)
        screen.blit(panel_surface, rect.topleft)
        pygame.draw.rect(screen, slot.color, rect, 2, border_radius=6)

        inner_x = rect.x + HUD_PANEL_PADDING
        inner_y = rect.y + HUD_PANEL_PADDING
        inner_width = rect.width - HUD_PANEL_PADDING * 2

        title = self._render_text(self.font_16, f"P{slot.index + 1}  {player.hero_class.upper()}", WHITE)
        kills = self._render_text(self.font_14, f"KILLS {player.kill_count}", GOLD)
        screen.blit(title, (inner_x + 20, inner_y))
        screen.blit(kills, (rect.right - HUD_PANEL_PADDING - kills.get_width(), inner_y + 2))
        pygame.draw.circle(screen, slot.color, (inner_x + 8, inner_y + 10), 6)

        hp_y = inner_y + 24
        hp_rect = pygame.Rect(inner_x, hp_y, inner_width, HUD_PANEL_BAR_HEIGHT)
        hp_ratio = max(0.0, player.hp / player.max_hp) if player.max_hp else 0.0
        if player.is_downed:
            hp_color = (110, 110, 110)
        elif hp_ratio > 0.5:
            hp_color = HP_COLOR
        elif hp_ratio > 0.25:
            hp_color = HP_MED_COLOR
        else:
            hp_color = HP_LOW_COLOR
        self._draw_bar(screen, hp_rect, hp_ratio, hp_color)
        hp_label = "DOWNED" if player.is_downed else f"HP  {max(0, int(player.hp))} / {int(player.max_hp)}"
        screen.blit(self._render_text(self.font_14, hp_label, WHITE), (inner_x, hp_rect.bottom + 1))

        xp_rect = pygame.Rect(inner_x, hp_rect.bottom + 18, inner_width, HUD_PANEL_BAR_HEIGHT)
        self._draw_bar(screen, xp_rect, xp_system.xp_progress(), XP_COLOR)
        lvl_text = self._render_text(self.font_14, f"LVL {xp_system.current_level}", WHITE)
        status_y = xp_rect.bottom + 1
        screen.blit(lvl_text, (inner_x, status_y))

        if player.is_downed:
            progress = 0
            if REVIVE_DURATION > 0:
                progress = int((player.revive_timer / REVIVE_DURATION) * 100)
            revive_text = self._render_text(
                self.font_14,
                f"REVIVE {max(0, min(100, progress))}%",
                slot.color,
            )
            screen.blit(revive_text, (rect.right - HUD_PANEL_PADDING - revive_text.get_width(), xp_rect.bottom + 2))

        slot_size = HUD_PANEL_WEAPON_SLOT_SIZE
        slot_width = max(slot_size, HUD_PANEL_WEAPON_SLOT_WIDTH)
        total_slots_width = (MAX_WEAPON_SLOTS * slot_width) + ((MAX_WEAPON_SLOTS - 1) * HUD_PANEL_WEAPON_SLOT_GAP)
        weapon_left = rect.centerx - total_slots_width // 2
        weapon_top = status_y + self.font_14.get_height() + 4
        self._draw_weapon_slots(screen, player, weapon_left, weapon_top, slot_size)
        self._draw_revive_indicator(screen, player, slot.color, camera)

    def draw(self, screen, players, xp_systems, wave_manager, show_fps=False, fps=0, camera=None):
        """Draw all in-game overlay UI in screen space (no camera offset)."""
        if not players or not xp_systems:
            return

        if len(players) == 1:
            self._draw_single_player(screen, players[0], xp_systems[0], wave_manager, show_fps, fps)
            return

        layout = HUD_PANEL_TUPLES[len(players)]
        for player, xp_system in zip(players, xp_systems):
            slot = player.slot
            if slot is None:
                continue
            rect = pygame.Rect(layout[slot.index])
            self._draw_player_panel(screen, player, xp_system, rect, slot, camera)

        self._draw_shared_info(screen, wave_manager, show_fps, fps)
