#!/usr/bin/env python3
"""Generate placeholder assets for Mystic Siege."""

import os
import wave
import math
import pygame


def _require_numpy():
    """Import numpy only when audio placeholder generation is actually used."""
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "placeholder audio generation requires numpy. Install project dependencies "
            "before running src/utils/placeholder_assets.py."
        ) from exc
    return np

def create_asset_directories():
    """Create all required asset directories."""
    directories = [
        "assets/sprites/heroes/",
        "assets/sprites/enemies/",
        "assets/sprites/projectiles/",
        "assets/sprites/effects/",
        "assets/sprites/ui/",
        "assets/audio/sfx/",
        "assets/audio/music/",
        "assets/fonts/"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def _shade(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    """Return a color shifted brighter/darker by delta."""
    return tuple(max(0, min(255, channel + delta)) for channel in color)


def _hero_palettes() -> dict[str, dict[str, tuple[int, int, int]]]:
    return {
        "knight": {
            "primary": (70, 145, 200),
            "secondary": (205, 120, 55),
            "accent": (235, 195, 70),
            "skin": (235, 200, 165),
        },
        "wizard": {
            "primary": (225, 120, 35),
            "secondary": (75, 120, 215),
            "accent": (245, 205, 90),
            "skin": (235, 205, 170),
        },
        "friar": {
            "primary": (198, 124, 52),
            "secondary": (135, 82, 34),
            "accent": (242, 210, 120),
            "skin": (229, 190, 150),
        },
        "ranger": {
            "primary": (85, 152, 102),
            "secondary": (128, 88, 52),
            "accent": (224, 210, 156),
            "skin": (225, 192, 150),
        },
        "druid": {
            "primary": (76, 140, 72),
            "secondary": (86, 74, 46),
            "accent": (176, 220, 110),
            "skin": (218, 184, 140),
        },
    }


def _draw_outline_rect(surface: pygame.Surface, color: tuple[int, int, int], rect: pygame.Rect, radius: int = 2) -> None:
    pygame.draw.rect(surface, color, rect, 1, border_radius=radius)


def _weapon_points(direction: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if direction == "left":
        return (9, 14), (2, 20)
    if direction == "right":
        return (23, 14), (30, 20)
    if direction == "up":
        return (17, 9), (24, 3)
    return (15, 20), (22, 28)


def _draw_knight_weapon(surface: pygame.Surface, direction: str, palette: dict[str, tuple[int, int, int]]) -> None:
    start, end = _weapon_points(direction)
    blade_color = _shade(palette["accent"], 10)
    guard_color = _shade(palette["secondary"], -15)
    pygame.draw.line(surface, blade_color, start, end, 2)
    if direction in {"left", "right"}:
        guard_x = start[0]
        pygame.draw.line(surface, guard_color, (guard_x, start[1] - 2), (guard_x, start[1] + 2), 2)
    else:
        guard_y = start[1]
        pygame.draw.line(surface, guard_color, (start[0] - 2, guard_y), (start[0] + 2, guard_y), 2)


def _draw_staff(surface: pygame.Surface, direction: str, palette: dict[str, tuple[int, int, int]]) -> None:
    wood = _shade(palette["secondary"], -20)
    orb = palette["accent"]
    start, end = _weapon_points(direction)
    pygame.draw.line(surface, wood, start, end, 2)
    pygame.draw.circle(surface, orb, end, 2)


def _draw_book(surface: pygame.Surface, direction: str, palette: dict[str, tuple[int, int, int]]) -> None:
    book = pygame.Rect(20, 15, 7, 6)
    if direction == "left":
        book = pygame.Rect(5, 15, 7, 6)
    elif direction == "up":
        book = pygame.Rect(18, 8, 7, 6)
    elif direction == "down":
        book = pygame.Rect(18, 20, 7, 6)
    pygame.draw.rect(surface, palette["accent"], book, border_radius=1)
    pygame.draw.line(surface, _shade(palette["secondary"], -25), (book.centerx, book.top + 1), (book.centerx, book.bottom - 1), 1)


def _draw_bow(surface: pygame.Surface, direction: str, palette: dict[str, tuple[int, int, int]]) -> None:
    bow = _shade(palette["secondary"], -25)
    string = _shade(palette["accent"], 20)
    if direction == "left":
        pygame.draw.arc(surface, bow, (3, 10, 9, 14), 1.3, 5.0, 2)
        pygame.draw.line(surface, string, (9, 11), (9, 23), 1)
        pygame.draw.line(surface, string, (9, 17), (15, 17), 1)
        pygame.draw.polygon(surface, string, [(15, 17), (12, 15), (12, 19)])
    elif direction == "right":
        pygame.draw.arc(surface, bow, (20, 10, 9, 14), 4.4, 1.9, 2)
        pygame.draw.line(surface, string, (23, 11), (23, 23), 1)
        pygame.draw.line(surface, string, (17, 17), (23, 17), 1)
        pygame.draw.polygon(surface, string, [(17, 17), (20, 15), (20, 19)])
    elif direction == "up":
        pygame.draw.arc(surface, bow, (16, 2, 10, 16), 2.7, 0.5, 2)
        pygame.draw.line(surface, string, (20, 4), (20, 16), 1)
        pygame.draw.line(surface, string, (14, 10), (20, 10), 1)
        pygame.draw.polygon(surface, string, [(14, 10), (17, 8), (17, 12)])
    else:
        pygame.draw.arc(surface, bow, (6, 15, 10, 16), 5.8, 3.7, 2)
        pygame.draw.line(surface, string, (10, 17), (10, 29), 1)
        pygame.draw.line(surface, string, (10, 23), (16, 23), 1)
        pygame.draw.polygon(surface, string, [(16, 23), (13, 21), (13, 25)])


def _draw_hero_frame(hero_key: str, direction: str, palette: dict[str, tuple[int, int, int]]) -> pygame.Surface:
    frame = pygame.Surface((32, 32), pygame.SRCALPHA)
    primary = palette["primary"]
    secondary = palette["secondary"]
    accent = palette["accent"]
    skin = palette["skin"]
    outline = _shade(primary, -55)

    head_rect = pygame.Rect(10, 5, 12, 9)
    torso_rect = pygame.Rect(9, 12, 14, 12)
    leg_left = pygame.Rect(10, 22, 4, 6)
    leg_right = pygame.Rect(18, 22, 4, 6)

    if hero_key == "wizard":
        pygame.draw.polygon(frame, secondary, [(9, 11), (16, 3), (23, 11)])
        pygame.draw.ellipse(frame, accent, (8, 10, 16, 4))
    elif hero_key == "friar":
        pygame.draw.ellipse(frame, secondary, (10, 5, 12, 10))
    elif hero_key == "druid":
        pygame.draw.polygon(frame, secondary, [(9, 13), (16, 5), (23, 13)])
        pygame.draw.ellipse(frame, skin, head_rect)
    else:
        pygame.draw.ellipse(frame, skin if hero_key == "knight" else secondary, head_rect)

    if hero_key == "knight":
        pygame.draw.rect(frame, _shade(primary, 35), (12, 6, 8, 5), border_radius=2)
        pygame.draw.rect(frame, primary, torso_rect, border_radius=3)
        pygame.draw.rect(frame, accent, (13, 15, 6, 7), border_radius=1)
        pygame.draw.rect(frame, secondary, (9, 12, 3, 9), border_radius=1)
        pygame.draw.rect(frame, secondary, (20, 12, 3, 9), border_radius=1)
    elif hero_key == "wizard":
        pygame.draw.polygon(frame, primary, [(9, 24), (16, 11), (23, 24)])
        pygame.draw.rect(frame, primary, (12, 12, 8, 8), border_radius=2)
        pygame.draw.rect(frame, accent, (13, 14, 6, 3), border_radius=1)
    elif hero_key == "friar":
        pygame.draw.polygon(frame, primary, [(9, 24), (16, 10), (23, 24)])
        pygame.draw.rect(frame, accent, (14, 13, 4, 6), border_radius=1)
        pygame.draw.line(frame, accent, (16, 12), (16, 20), 1)
        pygame.draw.line(frame, accent, (13, 16), (19, 16), 1)
    elif hero_key == "druid":
        pygame.draw.polygon(frame, primary, [(8, 24), (12, 11), (20, 11), (24, 24)])
        pygame.draw.rect(frame, secondary, (11, 8, 10, 6), border_radius=2)
        pygame.draw.line(frame, accent, (11, 16), (21, 20), 1)
        pygame.draw.line(frame, accent, (12, 20), (22, 15), 1)
    else:
        pygame.draw.polygon(frame, primary, [(8, 24), (12, 11), (20, 11), (24, 24)])
        pygame.draw.rect(frame, secondary, (11, 8, 10, 6), border_radius=2)
        pygame.draw.rect(frame, accent, (13, 15, 6, 3), border_radius=1)

    pygame.draw.rect(frame, _shade(secondary, 20), leg_left, border_radius=1)
    pygame.draw.rect(frame, _shade(secondary, 20), leg_right, border_radius=1)
    pygame.draw.rect(frame, outline, leg_left, 1, border_radius=1)
    pygame.draw.rect(frame, outline, leg_right, 1, border_radius=1)

    if hero_key == "knight":
        _draw_knight_weapon(frame, direction, palette)
    elif hero_key == "wizard":
        _draw_staff(frame, direction, palette)
    elif hero_key == "friar":
        _draw_book(frame, direction, palette)
    elif hero_key == "druid":
        _draw_staff(frame, direction, palette)
    else:
        _draw_bow(frame, direction, palette)

    _draw_outline_rect(frame, outline, torso_rect)
    if hero_key != "wizard":
        pygame.draw.ellipse(frame, outline, head_rect, 1)

    return frame


def _weapon_bg(surface: pygame.Surface, color: tuple[int, int, int]) -> None:
    bg = _shade(color, -30)
    border = _shade(color, 35)
    pygame.draw.rect(surface, bg, (0, 0, 32, 32), border_radius=6)
    pygame.draw.rect(surface, border, (1, 1, 30, 30), 2, border_radius=6)


def _draw_throwing_hatchet_icon(surface: pygame.Surface) -> None:
    """Draw a compact competition-style throwing hatchet readable at 32x32."""
    handle_shadow = (64, 38, 12)
    handle_color = (176, 132, 74)
    handle_highlight = (214, 172, 110)
    steel_outline = (42, 46, 54)
    steel_fill = (190, 192, 196)
    steel_shadow = (132, 136, 144)
    steel_highlight = (232, 234, 238)

    # Straight haft with slight taper so the silhouette reads as wood instead of a line.
    pygame.draw.polygon(surface, handle_shadow, [(9, 26), (12, 27), (20, 12), (17, 11)])
    pygame.draw.polygon(surface, handle_color, [(10, 25), (12, 26), (19, 12), (17, 12)])
    pygame.draw.line(surface, handle_highlight, (11, 24), (18, 13), 1)

    # Small eye/socket where the steel wraps the haft. This creates clear wood/metal separation.
    pygame.draw.polygon(surface, steel_outline, [(14, 11), (18, 9), (21, 11), (19, 15), (16, 14), (14, 13)])
    pygame.draw.polygon(surface, steel_shadow, [(15, 11), (18, 10), (20, 11), (18, 14), (16, 13), (15, 12)])

    # Competition-style hatchet head: mostly trapezoidal with the narrow mounted side at the shaft.
    head_outline = [(6, 9), (17, 6), (21, 9), (19, 15), (16, 16), (8, 15), (4, 12)]
    head_fill = [(7, 9), (17, 7), (20, 9), (18, 14), (16, 15), (8, 14), (5, 12)]
    pygame.draw.polygon(surface, steel_outline, head_outline)
    pygame.draw.polygon(surface, steel_fill, head_fill)

    # Subtle darker underside keeps the rectangular head readable at icon size.
    pygame.draw.polygon(surface, steel_shadow, [(9, 14), (16, 15), (18, 14), (16, 13), (10, 13)])

    # Keep the bevel subtle and inside the blade face.
    pygame.draw.lines(surface, steel_highlight, False, [(7, 9), (5, 12), (8, 14)], 1)
    pygame.draw.line(surface, steel_highlight, (9, 9), (17, 7), 1)

    # Re-assert the silhouette edges after the highlight so the dark border stays crisp.
    pygame.draw.lines(surface, steel_outline, False, [(6, 9), (17, 6), (21, 9), (19, 15), (16, 16), (8, 15), (4, 12)], 1)


def _draw_weapon_icon(surface: pygame.Surface, weapon_key: str, color: tuple[int, int, int]) -> None:
    detail = _shade(color, 55)
    shadow = _shade(color, -70)
    if weapon_key == "arcane":
        pygame.draw.circle(surface, detail, (16, 16), 7)
        pygame.draw.circle(surface, shadow, (16, 16), 7, 2)
        pygame.draw.line(surface, detail, (21, 11), (26, 6), 2)
    elif weapon_key == "caltrops":
        outline = (44, 46, 54)
        spike = (192, 196, 205)
        highlight = (235, 238, 244)
        pygame.draw.line(surface, outline, (8, 16), (24, 16), 4)
        pygame.draw.line(surface, outline, (16, 8), (16, 24), 4)
        pygame.draw.line(surface, outline, (10, 10), (22, 22), 4)
        pygame.draw.line(surface, outline, (22, 10), (10, 22), 4)
        pygame.draw.line(surface, spike, (8, 16), (24, 16), 2)
        pygame.draw.line(surface, spike, (16, 8), (16, 24), 2)
        pygame.draw.line(surface, spike, (10, 10), (22, 22), 2)
        pygame.draw.line(surface, spike, (22, 10), (10, 22), 2)
        pygame.draw.circle(surface, highlight, (16, 16), 2)
    elif weapon_key == "flail":
        chain_color = (86, 88, 96)
        chain_highlight = (138, 140, 148)
        head_outline = (46, 48, 56)
        head_fill = (155, 158, 168)
        head_highlight = (230, 232, 238)
        pygame.draw.line(surface, chain_color, (11, 22), (20, 11), 3)
        pygame.draw.line(surface, chain_highlight, (11, 22), (20, 11), 1)
        for link_center in ((13, 20), (15, 17), (17, 14)):
            pygame.draw.circle(surface, chain_color, link_center, 2, 1)
        pygame.draw.circle(surface, head_outline, (22, 10), 6)
        pygame.draw.circle(surface, head_fill, (22, 10), 5)
        pygame.draw.circle(surface, head_highlight, (20, 8), 2)
        pygame.draw.line(surface, head_outline, (10, 23), (7, 26), 2)
    elif weapon_key == "nova":
        pygame.draw.circle(surface, detail, (16, 16), 8, 3)
        pygame.draw.circle(surface, detail, (16, 16), 3)
    elif weapon_key == "fire":
        pygame.draw.polygon(surface, detail, [(16, 6), (21, 14), (18, 25), (12, 22), (10, 14)])
        pygame.draw.polygon(surface, shadow, [(16, 11), (18, 16), (16, 22), (13, 18)])
    elif weapon_key == "hex":
        core = (150, 255, 120)
        outline = (24, 8, 46)
        highlight = _shade(color, 85)
        pygame.draw.circle(surface, outline, (16, 16), 10)
        pygame.draw.circle(surface, shadow, (16, 16), 9)
        pygame.draw.circle(surface, color, (16, 16), 7)
        pygame.draw.circle(surface, highlight, (13, 12), 2)
        pygame.draw.circle(surface, core, (16, 16), 4)
        pygame.draw.circle(surface, (55, 120, 70), (16, 16), 4, 1)
        rune_color = (115, 235, 105)
        pygame.draw.line(surface, rune_color, (8, 11), (11, 9), 2)
        pygame.draw.line(surface, rune_color, (8, 11), (10, 14), 2)
        pygame.draw.line(surface, rune_color, (21, 8), (24, 11), 2)
        pygame.draw.line(surface, rune_color, (24, 11), (21, 13), 2)
        pygame.draw.line(surface, rune_color, (11, 23), (16, 25), 2)
        pygame.draw.line(surface, rune_color, (16, 25), (21, 23), 2)
    elif weapon_key == "bramble":
        pygame.draw.circle(surface, shadow, (16, 16), 10)
        pygame.draw.circle(surface, color, (16, 16), 8)
        pygame.draw.circle(surface, detail, (16, 16), 4)
        for angle_deg in range(0, 360, 60):
            angle = math.radians(angle_deg)
            x0 = int(16 + math.cos(angle) * 7)
            y0 = int(16 + math.sin(angle) * 7)
            x1 = int(16 + math.cos(angle) * 13)
            y1 = int(16 + math.sin(angle) * 13)
            pygame.draw.line(surface, detail, (x0, y0), (x1, y1), 2)
    elif weapon_key == "frost":
        pygame.draw.line(surface, detail, (16, 7), (16, 25), 2)
        pygame.draw.line(surface, detail, (8, 16), (24, 16), 2)
        pygame.draw.line(surface, detail, (10, 10), (22, 22), 2)
        pygame.draw.line(surface, detail, (22, 10), (10, 22), 2)
    elif weapon_key == "lightning":
        pygame.draw.polygon(surface, detail, [(18, 6), (10, 17), (15, 17), (12, 26), (22, 14), (17, 14)])
    elif weapon_key == "blade":
        pygame.draw.line(surface, detail, (11, 23), (22, 10), 3)
        pygame.draw.line(surface, shadow, (9, 24), (13, 24), 2)
        pygame.draw.line(surface, shadow, (12, 21), (16, 25), 2)
    elif weapon_key == "longbow":
        pygame.draw.arc(surface, shadow, (8, 5, 12, 22), 1.2, 5.1, 3)
        pygame.draw.line(surface, detail, (18, 7), (18, 25), 1)
        pygame.draw.line(surface, detail, (11, 16), (25, 16), 2)
        pygame.draw.polygon(surface, detail, [(25, 16), (21, 13), (21, 19)])
    elif weapon_key == "axe":
        _draw_throwing_hatchet_icon(surface)
    elif weapon_key == "knife":
        blade_outline = (42, 40, 52)
        blade_fill = (188, 192, 205)
        blade_highlight = (238, 240, 248)
        guard = _shade(color, 35)
        handle = shadow
        pommel = _shade(color, -35)

        # Slim, pointy blade and compact grip stay clear of the rounded icon border.
        pygame.draw.polygon(surface, blade_outline, [(16, 5), (20, 15), (18, 21), (14, 21), (12, 15)])
        pygame.draw.polygon(surface, blade_fill, [(16, 7), (18, 15), (17, 19), (15, 19), (14, 15)])
        pygame.draw.line(surface, blade_highlight, (16, 8), (17, 17), 1)

        pygame.draw.line(surface, guard, (12, 22), (20, 22), 3)
        pygame.draw.rect(surface, handle, pygame.Rect(14, 23, 4, 4), border_radius=1)
        pygame.draw.circle(surface, pommel, (16, 27), 2)


def _draw_pickup_icon(surface: pygame.Surface, pickup_key: str, color: tuple[int, int, int]) -> None:
    _weapon_bg(surface, color)
    white = (245, 245, 245)
    if pickup_key == "magnet":
        pygame.draw.arc(surface, white, (8, 7, 16, 16), 0.1, 3.04, 3)
        pygame.draw.line(surface, white, (10, 16), (10, 24), 3)
        pygame.draw.line(surface, white, (22, 16), (22, 24), 3)
    elif pickup_key == "health_potion":
        pygame.draw.rect(surface, white, (11, 8, 10, 13), border_radius=3)
        pygame.draw.rect(surface, (200, 230, 255), (13, 5, 6, 4), border_radius=1)
        pygame.draw.rect(surface, color, (12, 14, 8, 5), border_radius=2)
    elif pickup_key == "battle_rage":
        pygame.draw.polygon(surface, white, [(15, 5), (22, 14), (17, 14), (22, 23), (10, 13), (15, 13)])
    elif pickup_key == "iron_skin":
        pygame.draw.polygon(surface, white, [(16, 5), (23, 8), (23, 17), (16, 24), (9, 17), (9, 8)])
        pygame.draw.line(surface, color, (16, 7), (16, 21), 2)
    elif pickup_key == "haste":
        pygame.draw.polygon(surface, white, [(11, 9), (19, 9), (15, 15), (22, 15), (11, 26), (15, 18), (9, 18)])


def _draw_projectile(surface: pygame.Surface, weapon_key: str, color: tuple[int, int, int]) -> None:
    detail = _shade(color, 45)
    shadow = _shade(color, -60)
    if weapon_key == "arcane":
        pygame.draw.circle(surface, detail, (8, 8), 5)
        pygame.draw.circle(surface, shadow, (8, 8), 5, 1)
        pygame.draw.line(surface, detail, (11, 5), (14, 2), 1)
    elif weapon_key == "nova":
        pygame.draw.circle(surface, detail, (8, 8), 5, 2)
        pygame.draw.circle(surface, detail, (8, 8), 2)
    elif weapon_key == "fire":
        pygame.draw.polygon(surface, detail, [(8, 2), (12, 7), (10, 14), (5, 12), (4, 7)])
    elif weapon_key == "frost":
        pygame.draw.line(surface, detail, (8, 3), (8, 13), 1)
        pygame.draw.line(surface, detail, (3, 8), (13, 8), 1)
        pygame.draw.line(surface, detail, (4, 4), (12, 12), 1)
        pygame.draw.line(surface, detail, (12, 4), (4, 12), 1)
    elif weapon_key == "lightning":
        pygame.draw.polygon(surface, detail, [(9, 2), (5, 8), (8, 8), (6, 14), (12, 7), (9, 7)])
    elif weapon_key == "longbow":
        pygame.draw.rect(surface, shadow, (1, 6, 9, 4), border_radius=1)
        pygame.draw.polygon(surface, detail, [(15, 8), (9, 3), (9, 13)])
        pygame.draw.polygon(surface, (240, 230, 210), [(0, 8), (3, 4), (3, 12)])
    elif weapon_key == "bramble":
        pygame.draw.circle(surface, shadow, (8, 8), 5)
        pygame.draw.circle(surface, detail, (8, 8), 3)
        pygame.draw.line(surface, detail, (8, 8), (13, 5), 1)
        pygame.draw.line(surface, detail, (8, 8), (12, 12), 1)

def generate_hero_assets():
    """Generate hero placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    for hero_key, palette in _hero_palettes().items():
        filename = f"{hero_key}.png"
        surface = pygame.Surface((128, 32), pygame.SRCALPHA)
        for index, direction in enumerate(("down", "left", "right", "up")):
            frame = _draw_hero_frame(hero_key, direction, palette)
            surface.blit(frame, (index * 32, 0))

        # Only write if no real asset exists
        filepath = f"assets/sprites/heroes/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def generate_enemy_assets():
    """Generate enemy placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Enemy assets
    enemies = [
        ("skeleton.png", (200, 200, 200), "S"),
        ("goblin.png", (60, 160, 60), "G"),
        ("wraith.png", (100, 100, 180), "W"),
        ("bat.png", (80, 40, 80), "B"),
        ("golem.png", (120, 100, 80), "G"),
        ("knight_enemy.png", (100, 100, 140), "K"),
        ("lich.png", (140, 60, 160), "L")
    ]

    for filename, color, label in enemies:
        # Create surface
        if filename == "golem.png":
            # Larger 48x48 surface for golem
            surface = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, 48, 48))
        else:
            surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, 32, 32))

        # Special handling for wraith (with alpha)
        if filename == "wraith.png":
            # Set alpha to 180 for wraith
            for x in range(surface.get_width()):
                for y in range(surface.get_height()):
                    r, g, b, a = surface.get_at((x, y))
                    surface.set_at((x, y), (r, g, b, 180))

        # Draw label
        font = pygame.font.SysFont(None, 24)
        text = font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(text, text_rect)

        # Only write if no real asset exists
        filepath = f"assets/sprites/enemies/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def generate_projectile_assets():
    """Generate projectile placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Projectile assets
    projectiles = [
        ("arcane.png", (160, 80, 255)),
        ("nova.png", (212, 175, 55)),
        ("fire.png", (255, 100, 20)),
        ("bramble.png", (82, 190, 95)),
        ("frost.png", (80, 200, 255)),
        ("lightning.png", (255, 240, 60)),
        ("longbow.png", (170, 120, 60)),
    ]

    for filename, color in projectiles:
        surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        _draw_projectile(surface, filename.split(".")[0], color)

        # Only write if no real asset exists
        filepath = f"assets/sprites/projectiles/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def generate_xp_orb_asset():
    """Generate XP orb placeholder asset."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Create 12x12 surface
    surface = pygame.Surface((12, 12), pygame.SRCALPHA)

    # Draw gold circle
    pygame.draw.circle(surface, (212, 175, 55), (6, 6), 6)

    # Only write if no real asset exists
    filepath = "assets/sprites/effects/xp_orb.png"
    if not os.path.exists(filepath):
        pygame.image.save(surface, filepath)

def generate_weapon_icon_assets():
    """Generate weapon icon placeholder assets."""
    # Initialize pygame headlessly
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    # Weapon colors matching projectiles
    weapons = [
        ("arcane.png", (160, 80, 255)),
        ("caltrops.png", (150, 150, 160)),
        ("nova.png", (212, 175, 55)),
        ("fire.png", (255, 100, 20)),
        ("flail.png", (150, 150, 160)),
        ("hex.png", (95, 35, 145)),
        ("bramble.png", (82, 190, 95)),
        ("frost.png", (80, 200, 255)),
        ("lightning.png", (255, 240, 60)),
        ("blade.png", (100, 150, 255)),  # Spectral blade color
        ("longbow.png", (170, 120, 60)),
        ("knife.png", (105, 105, 135)),   # Shadow knives — muted rogue steel
        ("axe.png", (160, 160, 170)),    # Throwing axes — steel-gray
    ]

    for filename, color in weapons:
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        _weapon_bg(surface, color)
        _draw_weapon_icon(surface, filename.split(".")[0], color)

        # Only write if no real asset exists
        filepath = f"assets/sprites/ui/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)


def generate_pickup_icon_assets():
    """Generate pickup placeholder assets."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    pickups = [
        ("magnet.png", (120, 220, 255)),
        ("health_potion.png", (220, 70, 90)),
        ("battle_rage.png", (255, 145, 60)),
        ("iron_skin.png", (160, 170, 190)),
        ("haste.png", (120, 255, 160)),
    ]

    for filename, color in pickups:
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        _draw_pickup_icon(surface, filename.split(".")[0], color)
        filepath = f"assets/sprites/ui/{filename}"
        if not os.path.exists(filepath):
            pygame.image.save(surface, filepath)

def _write_sine_wav(path: str, freq_hz: float, duration_s: float, volume: float = 0.25, sample_rate: int = 44100):
    """Write a mono sine-wave WAV file."""
    np = _require_numpy()
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    # Apply a short fade-out envelope to avoid clicks
    envelope = np.minimum(1.0, np.linspace(1.0, 0.0, n) * (n / max(1, int(sample_rate * 0.01))))
    samples = (np.sin(2 * np.pi * freq_hz * t) * envelope * volume * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def _write_sweep_wav(path: str, freq_start: float, freq_end: float, duration_s: float, volume: float = 0.25, sample_rate: int = 44100):
    """Write a mono frequency-sweep (chirp) WAV file."""
    np = _require_numpy()
    n = int(sample_rate * duration_s)
    freq = np.linspace(freq_start, freq_end, n)
    phase = np.cumsum(2 * np.pi * freq / sample_rate)
    envelope = np.linspace(1.0, 0.0, n)
    samples = (np.sin(phase) * envelope * volume * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def _write_chord_wav(path: str, freqs: list, duration_s: float, volume: float = 0.2, sample_rate: int = 44100):
    """Write a mono chord WAV file by mixing multiple sine frequencies."""
    np = _require_numpy()
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    envelope = np.linspace(1.0, 0.0, n)
    mixed = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    samples = (mixed * envelope * volume * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def generate_audio_placeholders():
    """Generate placeholder SFX WAV files using simple sine waves."""
    sfx_dir = "assets/audio/sfx/"

    # Only write each file if no real asset exists
    def maybe_write_sine(name, **kw):
        p = f"{sfx_dir}{name}"
        if not os.path.exists(p):
            _write_sine_wav(p, **kw)

    def maybe_write_sweep(name, **kw):
        p = f"{sfx_dir}{name}"
        if not os.path.exists(p):
            _write_sweep_wav(p, **kw)

    def maybe_write_chord(name, **kw):
        p = f"{sfx_dir}{name}"
        if not os.path.exists(p):
            _write_chord_wav(p, **kw)

    maybe_write_sine("player_hit.wav",      freq_hz=220,  duration_s=0.10)
    maybe_write_sweep("player_death.wav",   freq_start=440, freq_end=110, duration_s=0.40)
    maybe_write_sine("enemy_death.wav",     freq_hz=660,  duration_s=0.06)
    maybe_write_sine("xp_pickup.wav",       freq_hz=1320, duration_s=0.05)
    maybe_write_chord("level_up.wav",       freqs=[330, 440, 550], duration_s=0.35)
    maybe_write_sine("arcane_bolt.wav",     freq_hz=880,  duration_s=0.07)
    maybe_write_sweep("bramble_seeds.wav",  freq_start=540, freq_end=180, duration_s=0.16)
    maybe_write_sweep("hex_orb.wav",        freq_start=260, freq_end=90, duration_s=0.18)
    maybe_write_sine("holy_nova.wav",       freq_hz=110,  duration_s=0.25)
    maybe_write_sine("flame_blast.wav",     freq_hz=330,  duration_s=0.10)
    maybe_write_sine("spectral_blade.wav",  freq_hz=550,  duration_s=0.06)
    maybe_write_sine("lightning_chain.wav", freq_hz=1760, duration_s=0.08)
    maybe_write_sine("frost_ring.wav",      freq_hz=220,  duration_s=0.20)
    maybe_write_sine("longbow.wav",         freq_hz=440,  duration_s=0.10)
    maybe_write_sine("shadow_knives.wav",   freq_hz=660,  duration_s=0.07)
    maybe_write_sine("throwing_axes.wav",   freq_hz=330,  duration_s=0.08)
    maybe_write_chord("pickup_collect.wav", freqs=[520, 780, 1040], duration_s=0.18)


def main():
    """Generate all placeholder assets."""
    print("Generating placeholder assets...")

    # Create directories
    create_asset_directories()

    # Generate assets
    generate_hero_assets()
    generate_enemy_assets()
    generate_projectile_assets()
    generate_xp_orb_asset()
    generate_weapon_icon_assets()
    generate_pickup_icon_assets()
    generate_audio_placeholders()

    print("Generated placeholder assets to assets/")
    print("Run 'python main.py' to start the game")

if __name__ == "__main__":
    main()
