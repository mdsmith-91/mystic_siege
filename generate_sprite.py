"""
Generate transparent PNG sprite assets with OpenAI's Images API.

Usage:
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category enemies \
        --name skeleton_warrior \
        --subject "skeletal warrior with rusty sword and round shield"

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
DEFAULT_QUALITY = "medium"
DEFAULT_FRAME_SIZE = 32
DEFAULT_FRAMES = 1

_GAME_CONTEXT = (
    "top-down medieval fantasy survivor game in the style of Vampire Survivors and Brotato, "
    "stylized 2D painted game art, chunky pixel-art influenced"
)

_NEGATIVE = (
    "No background scene, no floor, no platform, no environment, "
    "no shadows outside the subject, no cast shadows, no drop shadows, "
    "no ambient occlusion on floor, no perspective ground plane, "
    "no text, no letters, no numbers, no watermark, no border, no frame, "
    "no UI mockup, no multiple subjects."
)


def build_prompt(
    category: str,
    subject: str,
    style: str | None,
    frame_idx: int = 0,
    total_frames: int = 1,
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

    style_text = style.strip() if style else "stylized 2D painted game art, chunky pixel-art influenced"

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
        f"The result must look like a clean standalone game sprite asset.{frame_suffix}"
    )


def resize_frame(image_bytes: bytes, size: int) -> PILImage.Image:
    """Decode PNG bytes, convert to RGBA, resize to size×size with LANCZOS."""
    img = PILImage.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")
    return img.resize((size, size), PILImage.Resampling.LANCZOS)


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

    is_spritesheet = args.frames > 1

    project_root = Path(args.project_root).expanduser().resolve()
    output_dir = project_root / "assets" / "sprites" / args.category
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = args.name.strip().lower().replace(" ", "_")

    # Log the base prompt (frame 0)
    prompt = build_prompt(args.category, args.subject, args.style, frame_idx=0, total_frames=args.frames)
    prompt_log_path = output_dir / f"{safe_name}_prompt.txt"
    prompt_log_path.write_text(prompt + "\n", encoding="utf-8")

    client = OpenAI()
    saved_paths: list[Path] = []

    if is_spritesheet:
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
