"""
Generate transparent PNG sprite assets with OpenAI's Images API.

Usage:
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category enemies \
        --name skeleton_warrior \
        --subject "skeletal warrior with rusty sword and round shield"

    # 4-direction spritesheet (cols: down, left, right, up) at 32x32 per frame (128x32 output):
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category enemies \
        --name skeleton \
        --subject "skeletal warrior with rusty sword and round shield" \
        --directions

    # 4-frame walk animation spritesheet at 32x32 per frame (128x32 output):
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category heroes \
        --name knight_walk \
        --subject "armored knight with burning sword" \
        --frames 4 \
        --frame-size 32

    # 16x16 projectile sprite:
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category projectiles \
        --name fireball \
        --subject "glowing ember fireball projectile" \
        --frame-size 16

    # 3 candidates to pick from (single image mode only):
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category heroes \
        --name mage \
        --subject "battle mage holding a glowing staff" \
        --n 3

Requirements:
    pip install -U openai pillow
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

import numpy as np

try:
    from openai import OpenAI
except ImportError:
    sys.exit("Missing dependency: run: pip install -U openai")

try:
    from PIL import Image as PILImage
except ImportError:
    sys.exit("Missing dependency: run: pip install pillow")


VALID_CATEGORIES = {"heroes", "enemies", "projectiles", "effects", "ui"}
DEFAULT_MODEL = "gpt-image-1"
DEFAULT_SIZE = "1024x1024"
DEFAULT_QUALITY = "high"
DEFAULT_FRAME_SIZE = 32
DEFAULT_FRAMES = 1

# Ordered columns in a 4-direction spritesheet: col 0=down, 1=left, 2=right, 3=up
DIRECTION_ORDER = ["down", "left", "right", "up"]

_DIRECTION_FACING: dict[str, str] = {
    "down":  (
        "facing directly toward the viewer, full front view, "
        "weapon and shield visible on correct sides, neutral stance"
    ),
    "left":  (
        "facing directly to the left, strict side profile, "
        "character walking left, weapon arm leading"
    ),
    "right": (
        "facing directly to the right, strict side profile, "
        "character walking right, weapon arm leading"
    ),
    "up":    (
        "facing directly away from the viewer, full back view, "
        "back of armor/cape visible, no face shown"
    ),
}

_GAME_CONTEXT = (
    "top-down medieval fantasy survivor game in the style of Vampire Survivors and Brotato, "
    "stylized 2D painted game art, chunky pixel-art influenced. "
    "The game background is a dark stone dungeon floor, so sprites must use bright, "
    "saturated, high-contrast colors to stand out clearly — no dark or muddy tones"
)

_NEGATIVE = (
    "No background scene, no floor, no platform, no environment, "
    "no shadows outside the subject, no cast shadows, no drop shadows, "
    "no ambient occlusion on floor, no perspective ground plane, "
    "no text, no letters, no numbers, no watermark, no border, no frame, "
    "no UI mockup, no multiple subjects, "
    "no dark color palette, no muddy browns or blacks as dominant colors, "
    "no underexposed or shadowy rendering."
)


def build_prompt(
    category: str,
    subject: str,
    style: str | None,
    frame_idx: int = 0,
    total_frames: int = 1,
    direction: str | None = None,
) -> str:
    category_guidance: dict[str, str] = {
        "heroes": (
            "single playable character sprite, centered, full body, "
            "chunky readable silhouette, front-facing or slight 3/4 overhead view, "
            "neutral idle stance, fully inside canvas with clear padding"
        ),
        "enemies": (
            "single enemy sprite, centered, full body, "
            "chunky readable silhouette, front-facing or slight 3/4 overhead view, "
            "clearly identifiable enemy type, fully inside canvas with clear padding"
        ),
        "projectiles": (
            "single compact glowing projectile sprite, centered, small tight silhouette, "
            "floating in air, no ground shadow, no cast shadow, no floor, isolated in space"
        ),
        "effects": (
            "single visual effect frame, centered, isolated magical particle or explosion element, "
            "no ground contact, no floor, no environment"
        ),
        "ui": (
            "single UI icon, centered, isolated symbol or item, "
            "highly readable at small size, clean flat graphic, no scene or environment"
        ),
    }[category]

    style_text = style.strip() if style else (
        "stylized 2D painted game art, chunky pixel-art influenced, "
        "bright vivid colors, well-lit, high contrast"
    )

    direction_suffix = ""
    if direction is not None:
        facing = _DIRECTION_FACING[direction]
        direction_suffix = (
            f" The character must be {facing}. "
            "This is one frame of a 4-direction sheet; keep the style, color palette, "
            "and character design identical across all directions."
        )

    frame_suffix = ""
    if total_frames > 1:
        frame_suffix = (
            f" This is frame {frame_idx + 1} of {total_frames} of a smooth looping animation. "
            "Match the previous frames' style, color palette, and character design exactly. "
            "Show a slightly different pose in the animation cycle — subtle motion only, keep the character centered."
        )

    return (
        f"Create one {category_guidance} of {subject}. "
        f"Game context: {_GAME_CONTEXT}. "
        f"Visual style: {style_text}. "
        f"Transparent background. {_NEGATIVE} "
        "Keep the subject fully inside the canvas with some padding. "
        f"The result must look like a clean standalone game sprite asset.{direction_suffix}{frame_suffix}"
    )


def build_directions_prompt(category: str, subject: str, style: str | None) -> str:
    """Build a single prompt that requests all 4 directions in a 2x2 grid image.

    Grid layout (matches slice_2x2_into_frames extraction order):
        top-left  = front (down)  |  top-right = left profile
        bot-left  = right profile |  bot-right = back (up)
    """
    style_text = style.strip() if style else (
        "stylized 2D painted game art, chunky pixel-art influenced, "
        "bright vivid colors, well-lit, high contrast"
    )
    return (
        f"Create a 2x2 character reference sheet showing a {subject} "
        f"for a {_GAME_CONTEXT}. "
        "The canvas is split into exactly 4 equal square panels arranged in a 2-column by 2-row grid "
        "with NO borders, gaps, labels, or dividers between panels. "
        "Panel positions: "
        "TOP-LEFT panel: character facing directly toward the viewer, full front view, "
        "weapon held visibly in hand in front of the body; "
        "TOP-RIGHT panel: character facing directly to their left, strict side profile facing left, "
        "weapon extended forward; "
        "BOTTOM-LEFT panel: character facing directly to their right, strict side profile facing right, "
        "weapon extended forward; "
        "BOTTOM-RIGHT panel: character facing directly away from the viewer, full back view, "
        "weapon visible held at side or over shoulder. "
        "All 4 panels show the EXACT SAME character design — identical weapon, colors, proportions, and style. "
        "The weapon must appear in ALL 4 panels. "
        "Each character is fully inside its panel, centered, with padding on all sides — "
        "no limbs or weapons clipped by panel edges. "
        f"Visual style: {style_text}. "
        "Completely transparent background — no ground, no floor, no environment, no color fill behind the character. "
        f"{_NEGATIVE} "
        "No dividers, no labels, no text, no grid lines between panels."
    )


def remove_background(img: PILImage.Image, tolerance: int = 40) -> PILImage.Image:
    """Flood-fill from all 4 corners to erase the solid background color.

    Uses PIL floodfill (C-speed) to mark background pixels, then numpy to
    replace them with full transparency. Safe for sprites because it only
    removes pixels connected to the image edges.
    """
    from PIL import ImageDraw
    img = img.convert("RGBA")
    marker = (1, 2, 3, 255)  # sentinel value unlikely to appear in sprite art
    for seed in [(0, 0), (img.width - 1, 0), (0, img.height - 1), (img.width - 1, img.height - 1)]:
        ImageDraw.floodfill(img, seed, marker, thresh=tolerance)
    arr = np.array(img)
    mask = np.all(arr == [1, 2, 3, 255], axis=2)
    arr[mask] = [0, 0, 0, 0]
    return PILImage.fromarray(arr)


def resize_frame(image_bytes: bytes, size: int) -> PILImage.Image:
    """Decode PNG bytes, convert to RGBA, resize to size×size with LANCZOS."""
    img = PILImage.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")
    return img.resize((size, size), PILImage.Resampling.LANCZOS)


def slice_into_frames(sheet: PILImage.Image, n_cols: int, frame_size: int) -> list[PILImage.Image]:
    """Slice a wide image into n_cols equal columns and resize each to frame_size×frame_size.

    Crops to the content bounding box first to remove transparent padding the model
    adds around the full image, which would otherwise shift the slice boundaries.
    """
    bbox = sheet.getbbox()
    if bbox:
        sheet = sheet.crop(bbox)
    col_w = sheet.width // n_cols
    frames = []
    for i in range(n_cols):
        box = (i * col_w, 0, (i + 1) * col_w, sheet.height)
        col = sheet.crop(box).convert("RGBA")
        frames.append(col.resize((frame_size, frame_size), PILImage.Resampling.LANCZOS))
    return frames


def slice_2x2_into_frames(sheet: PILImage.Image, frame_size: int) -> list[PILImage.Image]:
    """Slice a 2x2 grid image into 4 frames in [down, left, right, up] order.

    Expected grid layout from build_directions_prompt:
        top-left  = front/down   |  top-right = left profile
        bot-left  = right profile|  bot-right = back/up

    Crops to content bounding box first to strip any outer transparent padding.
    """
    bbox = sheet.getbbox()
    if bbox:
        sheet = sheet.crop(bbox)
    half_w = sheet.width // 2
    half_h = sheet.height // 2
    quadrants = [
        (0,      0,      half_w,       half_h),        # top-left  → down
        (half_w, 0,      sheet.width,  half_h),        # top-right → left
        (0,      half_h, half_w,       sheet.height),  # bot-left  → right
        (half_w, half_h, sheet.width,  sheet.height),  # bot-right → up
    ]
    frames = []
    for box in quadrants:
        frame = sheet.crop(box).convert("RGBA")
        frames.append(frame.resize((frame_size, frame_size), PILImage.Resampling.LANCZOS))
    return frames


def composite_spritesheet(frames: list[PILImage.Image], frame_size: int) -> PILImage.Image:
    """Paste N frames side-by-side into a horizontal strip PNG."""
    strip = PILImage.new("RGBA", (frame_size * len(frames), frame_size), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        strip.paste(frame, (i * frame_size, 0))
    return strip


def pil_to_png_bytes(img: PILImage.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate transparent sprite PNGs for Mystic Siege.")
    parser.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    parser.add_argument("--name", required=True, help="Output filename without extension, e.g. skeleton_warrior")
    parser.add_argument("--subject", required=True, help="Short description of the sprite subject")
    parser.add_argument(
        "--style",
        default="stylized 2D painted game art, chunky pixel-art influenced",
        help="Visual style guidance for the sprite",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=DEFAULT_FRAMES,
        metavar="N",
        help=(
            "Number of animation frames to generate as a horizontal spritesheet "
            f"(default: {DEFAULT_FRAMES} = single image). Each frame is a separate API call. "
            "Mutually exclusive with --n > 1."
        ),
    )
    parser.add_argument(
        "--frame-size",
        type=int,
        default=DEFAULT_FRAME_SIZE,
        metavar="SIZE",
        help=(
            f"Output pixel size per frame after downscaling (default: {DEFAULT_FRAME_SIZE}). "
            "Use 32 for heroes/enemies/ui, 16 for projectiles, 12 for effects."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI image model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--quality",
        default=DEFAULT_QUALITY,
        choices=["low", "medium", "high", "auto"],
        help=f"Generation quality (default: {DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "--size",
        default=DEFAULT_SIZE,
        choices=["1024x1024", "1536x1024", "1024x1536", "auto"],
        help=f"Image size sent to the API (default: {DEFAULT_SIZE})",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of candidates to generate (1-10, default: 1). Cannot be > 1 with --frames > 1.",
    )
    parser.add_argument(
        "--directions",
        action="store_true",
        default=False,
        help=(
            "Generate a 4-direction spritesheet with frames for down, left, right, up "
            "(cols 0-3). Each direction gets a tailored prompt. "
            "Mutually exclusive with --frames > 1 and --n > 1."
        ),
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to your mystic_siege project root (default: current directory)",
    )
    return parser.parse_args()


def ensure_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Set the OPENAI_API_KEY environment variable before running this script.")
    return api_key


def main() -> None:
    args = parse_args()
    ensure_api_key()

    if not (1 <= args.n <= 10):
        sys.exit("--n must be between 1 and 10")
    if not (1 <= args.frames <= 24):
        sys.exit("--frames must be between 1 and 24")
    if not (4 <= args.frame_size <= 256):
        sys.exit("--frame-size must be between 4 and 256")
    if args.frames > 1 and args.n > 1:
        sys.exit("--frames and --n > 1 are mutually exclusive; use --n 1 when generating spritesheets")
    if args.directions and args.frames > 1:
        sys.exit("--directions and --frames > 1 are mutually exclusive")
    if args.directions and args.n > 1:
        sys.exit("--directions and --n > 1 are mutually exclusive")

    is_spritesheet = args.frames > 1

    project_root = Path(args.project_root).expanduser().resolve()
    output_dir = project_root / "assets" / "sprites" / args.category
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = args.name.strip().lower().replace(" ", "_")

    # Log the prompt that will be used
    if args.directions:
        prompt = build_directions_prompt(args.category, args.subject, args.style)
    else:
        prompt = build_prompt(args.category, args.subject, args.style, frame_idx=0, total_frames=args.frames)
    prompt_log_path = output_dir / f"{safe_name}_prompt.txt"
    prompt_log_path.write_text(prompt + "\n", encoding="utf-8")

    client = OpenAI()
    saved_paths: list[Path] = []

    if args.directions:
        # Single API call: all 4 directions in one image, then slice for style consistency
        dir_prompt = build_directions_prompt(args.category, args.subject, args.style)
        print(f"Generating 4-direction sheet in one call with {args.model}...")
        response = client.images.generate(
            model=args.model,
            prompt=dir_prompt,
            size="1024x1024",
            quality=args.quality,
            background="transparent",
            output_format="png",
            n=1,
        )
        if not getattr(response, "data", None) or not getattr(response.data[0], "b64_json", None):
            sys.exit("No image data returned for directions sheet.")
        raw_bytes = base64.b64decode(response.data[0].b64_json)
        full_sheet = remove_background(PILImage.open(io.BytesIO(raw_bytes)))

        # Save the raw unsliced (but background-removed) sheet for inspection
        raw_path = output_dir / f"{safe_name}_raw.png"
        raw_path.write_bytes(pil_to_png_bytes(full_sheet))
        print(f"Raw unsliced sheet: {raw_path}")

        frames = slice_2x2_into_frames(full_sheet, args.frame_size)

        strip = composite_spritesheet(frames, args.frame_size)
        output_path = output_dir / f"{safe_name}.png"
        output_path.write_bytes(pil_to_png_bytes(strip))
        saved_paths.append(output_path)

        meta = {
            "frame_w": args.frame_size,
            "frame_h": args.frame_size,
            "frame_count": len(DIRECTION_ORDER),
            "cols": len(DIRECTION_ORDER),
            "rows": 1,
            "directions": DIRECTION_ORDER,
        }
        meta_path = output_dir / f"{safe_name}_meta.json"
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"Spritesheet metadata: {meta_path}")

    elif is_spritesheet:
        # Generate N frames individually and composite into a horizontal strip
        frames: list[PILImage.Image] = []
        for frame_idx in range(args.frames):
            frame_prompt = build_prompt(
                args.category, args.subject, args.style,
                frame_idx=frame_idx, total_frames=args.frames,
            )
            print(f"Generating frame {frame_idx + 1}/{args.frames} with {args.model}...")
            response = client.images.generate(
                model=args.model,
                prompt=frame_prompt,
                size=args.size,
                quality=args.quality,
                background="transparent",
                output_format="png",
                n=1,
            )
            if not getattr(response, "data", None) or not getattr(response.data[0], "b64_json", None):
                sys.exit(f"No image data returned for frame {frame_idx + 1}.")
            raw_bytes = base64.b64decode(response.data[0].b64_json)
            frames.append(resize_frame(raw_bytes, args.frame_size))

        strip = composite_spritesheet(frames, args.frame_size)
        output_path = output_dir / f"{safe_name}.png"
        output_path.write_bytes(pil_to_png_bytes(strip))
        saved_paths.append(output_path)

        meta = {
            "frame_w": args.frame_size,
            "frame_h": args.frame_size,
            "frame_count": args.frames,
            "cols": args.frames,
            "rows": 1,
        }
        meta_path = output_dir / f"{safe_name}_meta.json"
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"Spritesheet metadata: {meta_path}")

    else:
        # Generate one or more single-image candidates
        print(f"Generating {args.n} sprite candidate(s) with {args.model}...")
        response = client.images.generate(
            model=args.model,
            prompt=prompt,
            size=args.size,
            quality=args.quality,
            background="transparent",
            output_format="png",
            n=args.n,
        )
        if not getattr(response, "data", None):
            sys.exit("No image data was returned by the API.")

        for idx, item in enumerate(response.data, start=1):
            if not getattr(item, "b64_json", None):
                print(f"Skipping image {idx}: no base64 image data returned.")
                continue
            raw_bytes = base64.b64decode(item.b64_json)
            resized = resize_frame(raw_bytes, args.frame_size)
            suffix = f"_{idx}" if args.n > 1 else ""
            output_path = output_dir / f"{safe_name}{suffix}.png"
            output_path.write_bytes(pil_to_png_bytes(resized))
            saved_paths.append(output_path)

            meta = {
                "frame_w": args.frame_size,
                "frame_h": args.frame_size,
                "frame_count": 1,
                "cols": 1,
                "rows": 1,
            }
            meta_path = output_dir / f"{safe_name}{suffix}_meta.json"
            meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    if not saved_paths:
        sys.exit("The API response did not contain any decodable image payloads.")

    print("Saved files:")
    for path in saved_paths:
        print(f"  {path}")
    print(f"Prompt log: {prompt_log_path}")


if __name__ == "__main__":
    main()
