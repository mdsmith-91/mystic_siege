"""
One-off script to regenerate assets/sprites/enemies/golem.png from golem_raw.png.

golem_raw.png is a 2x2 grid of directional frames with a dark non-transparent background.
This script removes the background via BFS flood-fill from all 4 corners of each frame,
then assembles a clean 256x64 RGBA runtime spritesheet.

Run from the project root:
    python src/utils/process_golem_sprite.py
"""

import os
import sys
import collections
import pygame
from settings import STONE_GOLEM_ENEMY_DATA

# Resolve project root regardless of where the script is run from
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PATH = os.path.join(_ROOT, "assets", "sprites", "enemies", "golem_raw.png")
OUT_PATH = os.path.join(_ROOT, "assets", "sprites", "enemies", "golem.png")

# How aggressively to remove background pixels (color distance threshold, 0-441)
# Higher = remove more; lower = remove less (safe range: 40-80 for high-contrast sprites)
BG_THRESHOLD = 60

FRAME_WIDTH, FRAME_HEIGHT = STONE_GOLEM_ENEMY_DATA["spritesheet_frame_size"]


def _require_numpy():
    """Import numpy only when this asset-processing script is executed."""
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "golem sprite processing requires numpy. Install project dependencies "
            "before running src/utils/process_golem_sprite.py."
        ) from exc
    return np


def color_distance(a, b) -> float:
    """Euclidean distance between two RGB triples."""
    np = _require_numpy()
    return float(np.sqrt(np.sum((a.astype(np.float32) - b.astype(np.float32)) ** 2)))


def flood_fill_background(surface: pygame.Surface, threshold: int) -> pygame.Surface:
    """
    Return a copy of surface with background pixels made transparent.
    Seeds from all 4 corners and BFS-expands to neighboring pixels that are
    within `threshold` color distance from the seed color.
    """
    w, h = surface.get_size()
    result = surface.copy()
    np = _require_numpy()

    rgb = pygame.surfarray.pixels3d(result)      # shape (w, h, 3)
    alpha = pygame.surfarray.pixels_alpha(result) # shape (w, h)

    visited = np.zeros((w, h), dtype=bool)
    queue = collections.deque()

    # Seed from all 4 corners
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for cx, cy in corners:
        if not visited[cx, cy]:
            visited[cx, cy] = True
            queue.append((cx, cy))

    # Collect the average background color from the corner pixels to use as reference
    corner_colors = np.array([rgb[cx, cy] for cx, cy in corners], dtype=np.float32)
    bg_color = corner_colors.mean(axis=0)

    while queue:
        x, y = queue.popleft()
        if color_distance(rgb[x, y], bg_color) < threshold:
            alpha[x, y] = 0
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and not visited[nx, ny]:
                    visited[nx, ny] = True
                    queue.append((nx, ny))

    # Release pixel array locks before returning
    del rgb, alpha

    return result


def main() -> None:
    # Minimal pygame init — display surface required for convert_alpha
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.NOFRAME)

    if not os.path.exists(RAW_PATH):
        print(f"ERROR: raw sprite not found at {RAW_PATH}")
        sys.exit(1)

    raw = pygame.image.load(RAW_PATH).convert_alpha()
    raw_w, raw_h = raw.get_size()
    frame_w = raw_w // 2
    frame_h = raw_h // 2

    print(f"Loaded {RAW_PATH}  ({raw_w}x{raw_h})")
    print(f"Detected frame size: {frame_w}x{frame_h} (2x2 grid)")

    # Frame layout in raw: top-left=down, top-right=left, bottom-left=right, bottom-right=up
    frame_origins = [
        (0,       0),       # down  (front)
        (frame_w, 0),       # left
        (0,       frame_h), # right
        (frame_w, frame_h), # up    (back)
    ]

    output = pygame.Surface((FRAME_WIDTH * 4, FRAME_HEIGHT), pygame.SRCALPHA)

    for col_idx, (ox, oy) in enumerate(frame_origins):
        # Extract one frame from the raw sheet
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(raw, (0, 0), pygame.Rect(ox, oy, frame_w, frame_h))

        # Remove dark background via BFS flood-fill from corners
        clean = flood_fill_background(frame, BG_THRESHOLD)

        # Scale to the runtime frame size used by the Stone Golem enemy.
        scaled = pygame.transform.scale(clean, (FRAME_WIDTH, FRAME_HEIGHT))

        output.blit(scaled, (col_idx * FRAME_WIDTH, 0))
        print(f"  Frame {col_idx} processed")

    pygame.image.save(output, OUT_PATH)
    print(f"Saved {OUT_PATH}  ({FRAME_WIDTH * 4}x{FRAME_HEIGHT})")

    pygame.quit()


if __name__ == "__main__":
    main()
