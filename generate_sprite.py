"""
Generate transparent PNG sprite assets with OpenAI's Images API.

Usage:
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category enemies \
        --name skeleton_warrior \
        --subject "skeletal warrior with rusty sword and round shield"

Examples:
    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category heroes \
        --name mage \
        --subject "battle mage holding a glowing staff"

    OPENAI_API_KEY=your_key_here python generate_sprite.py \
        --category projectiles \
        --name fireball \
        --subject "glowing ember fireball projectile"

Requirements:
    pip install -U openai
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    sys.exit("Missing dependency: run: pip install -U openai")


VALID_CATEGORIES = {"heroes", "enemies", "projectiles", "effects", "ui"}
DEFAULT_MODEL = "gpt-image-1"
DEFAULT_SIZE = "1024x1024"
DEFAULT_QUALITY = "medium"


def build_prompt(category: str, subject: str, style: str | None) -> str:
    category_guidance = {
        "heroes": (
            "single playable character sprite, centered, full body, readable silhouette, "
            "front-facing or slight 3/4 view, fantasy action game style"
        ),
        "enemies": (
            "single enemy sprite, centered, full body, readable silhouette, "
            "fantasy action game style"
        ),
        "projectiles": (
            "single projectile sprite, centered, clean silhouette, compact composition, "
            "fantasy action game style"
        ),
        "effects": (
            "single visual effect sprite, centered, isolated effect only, "
            "fantasy action game style"
        ),
        "ui": (
            "single UI icon, centered, isolated symbol, highly readable at small size, "
            "fantasy action game style"
        ),
    }[category]

    style_text = style.strip() if style else "stylized 2D painted game art"

    return (
        f"Create one {category_guidance} of {subject}. "
        f"Style: {style_text}. "
        "Transparent background. "
        "No background scene, no floor, no platform, no environment, no shadows outside the subject, "
        "no text, no letters, no numbers, no watermark, no border, no frame, no UI mockup, no multiple subjects. "
        "Keep the subject fully inside the canvas with some padding. "
        "The result must look like a clean standalone game sprite asset."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate transparent sprite PNGs for Mystic Siege.")
    parser.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    parser.add_argument("--name", required=True, help="Output filename without extension, e.g. skeleton_warrior")
    parser.add_argument("--subject", required=True, help="Short description of the sprite subject")
    parser.add_argument(
        "--style",
        default="stylized 2D painted game art",
        help="Visual style guidance for the sprite",
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
        help=f"Image size (default: {DEFAULT_SIZE})",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of candidates to generate (1-10, default: 1)",
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

    prompt = build_prompt(args.category, args.subject, args.style)

    project_root = Path(args.project_root).expanduser().resolve()
    output_dir = project_root / "assets" / "sprites" / args.category
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = args.name.strip().lower().replace(" ", "_")
    prompt_log_path = output_dir / f"{safe_name}_prompt.txt"
    prompt_log_path.write_text(prompt + "\n", encoding="utf-8")

    client = OpenAI()

    print(f"Generating {args.n} transparent sprite candidate(s) with {args.model}...")
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

    saved_paths: list[Path] = []
    for idx, item in enumerate(response.data, start=1):
        if not getattr(item, "b64_json", None):
            print(f"Skipping image {idx}: no base64 image data returned.")
            continue

        image_bytes = base64.b64decode(item.b64_json)
        suffix = f"_{idx}" if args.n > 1 else ""
        output_path = output_dir / f"{safe_name}{suffix}.png"
        output_path.write_bytes(image_bytes)
        saved_paths.append(output_path)

    if not saved_paths:
        sys.exit("The API response did not contain any decodable image payloads.")

    print("Saved files:")
    for path in saved_paths:
        print(f"- {path}")
    print(f"Prompt log: {prompt_log_path}")


if __name__ == "__main__":
    main()
