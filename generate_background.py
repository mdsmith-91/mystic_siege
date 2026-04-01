"""
Run this script once to generate a seamless background tile using Google Imagen.

Usage:
    GEMINI_API_KEY=your_key_here python generate_background.py

Requirements:
    pip install -U google-genai pillow
"""

import os
import sys

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("Missing dependency: run: pip install -U google-genai")

try:
    from PIL import Image
except ImportError:
    sys.exit("Missing dependency: run: pip install pillow")


API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("Set the GEMINI_API_KEY environment variable before running this script.")

OUTPUT_PATH = "assets/backgrounds/game_bg.png"

PROMPT = (
    "Top-down medieval fantasy ground texture, dark stone cobblestones "
    "with moss and dirt patches, seamless tileable, dark muted greens and grays, "
    "no characters, no shadows, 2D game asset"
)


def main():
    client = genai.Client(api_key=API_KEY)

    print("Generating background tile with Imagen 4...")
    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=PROMPT,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_low_and_above",
            person_generation="dont_allow",
        ),
    )

    if not response.generated_images:
        sys.exit("No image was returned by the API.")

    img: Image.Image = response.generated_images[0].image

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    img.save(OUTPUT_PATH)

    print(f"Saved: {OUTPUT_PATH} ({img.size[0]}x{img.size[1]} px)")
    print("Launch the game to see it in action.")


if __name__ == "__main__":
    main()
