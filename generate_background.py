"""
Generate a seamless flat gameplay floor tile with Google Imagen via the Gemini Developer API.

This version is tuned to reduce the chance of the model rendering prompt text,
labels, UI overlays, posters, or concept-sheet style output.

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
    from PIL import Image as PILImage
except ImportError:
    sys.exit("Missing dependency: run: pip install pillow")


API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("Set the GEMINI_API_KEY environment variable before running this script.")

MODEL_NAME = "imagen-4.0-generate-001"
OUTPUT_DIR = "assets/backgrounds"
BASE_NAME = "game_bg"
NUM_IMAGES = 1

# Keep the prompt short and explicit. Long prompts sometimes increase the chance
# of unexpected text or layout-like generations.
PROMPT = (
    "Single square image of a seamless tileable top-down orthographic flat worn ground pattern for a "
    "Vampire Survivors style arena floor. Dark muted gray-brown ground with subtle dust, faint cracks, and very sparse moss. "
    "Perfectly flat 2D surface, zero elevation, zero perspective, zero depth. Repeat cleanly on all four edges. "
    "Texture only, full frame, edge to edge. No text, no letters, no words, no numbers, no symbols, no runes, "
    "no captions, no labels, no watermark, no logo, no UI, no poster, no diagram, no mockup, no concept sheet, "
    "no border, no frame, no corners, no shadows, no objects, no rocks, no characters, no buildings."
)


def save_and_report(generated, path: str) -> None:
    generated.save(path)
    with PILImage.open(path) as img:
        width, height = img.size
    print(f"Saved: {path} ({width}x{height} px)")


def main() -> None:
    client = genai.Client(api_key=API_KEY)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating {NUM_IMAGES} background floor tile candidate(s) with {MODEL_NAME}...")
    response = client.models.generate_images(
        model=MODEL_NAME,
        prompt=PROMPT,
        config=types.GenerateImagesConfig(
            number_of_images=NUM_IMAGES,
            aspect_ratio="1:1",
            person_generation="dont_allow",
        ),
    )

    generated_images = response.generated_images or []
    if not generated_images:
        sys.exit("No images were returned by the API.")

    for index, item in enumerate(generated_images, start=1):
        generated = item.image
        if generated is None:
            print(f"Skipping candidate {index}: no image data.")
            continue
        output_path = os.path.join(OUTPUT_DIR, f"{BASE_NAME}_{index}.png")
        save_and_report(generated, output_path)

    print("Done. Pick the cleanest candidate and test it tiled in-game.")


if __name__ == "__main__":
    main()
