"""Generate flat 2D placeholder portraits for the two roomie models.

Run from the repo root:  python tools/make_portraits.py
Outputs girl/boy portraits in four moods to client/assets/portraits/.
Replace these with real art later; the file names are the contract.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

SIZE = 256
OUT_DIR = os.path.join("client", "assets", "portraits")

SKIN = (255, 224, 196)
BLUSH = (255, 170, 170)
GIRL_HAIR = (150, 95, 200)
BOY_HAIR = (90, 120, 200)
SICK_TINT = (190, 225, 185)

MOODS = ("happy", "neutral", "sad", "sick")
BACKDROPS = {
    "happy": (255, 244, 214),
    "neutral": (228, 236, 246),
    "sad": (210, 218, 232),
    "sick": (214, 232, 214),
}


def rounded_background(draw: ImageDraw.ImageDraw, color: tuple) -> None:
    draw.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=36, fill=color)


def draw_hair(draw: ImageDraw.ImageDraw, gender: str, color: tuple) -> None:
    if gender == "girl":
        draw.ellipse([60, 36, 196, 150], fill=color)            # full head of hair
        draw.rectangle([60, 90, 196, 210], fill=color)          # long hair down the sides
        draw.ellipse([72, 60, 184, 170], fill=SKIN)             # face cut-out
    else:
        draw.ellipse([66, 40, 190, 150], fill=color)            # short hair cap
        draw.ellipse([78, 66, 178, 170], fill=SKIN)             # face cut-out


def draw_face(draw: ImageDraw.ImageDraw, mood: str) -> None:
    left_eye = [104, 104, 120, 122]
    right_eye = [136, 104, 152, 122]
    if mood == "sick":
        draw.line([104, 113, 120, 113], fill=(40, 40, 40), width=4)
        draw.line([136, 113, 152, 113], fill=(40, 40, 40), width=4)
        draw.ellipse([158, 96, 170, 116], fill=(140, 200, 230))  # sweat drop
    else:
        draw.ellipse(left_eye, fill=(40, 40, 40))
        draw.ellipse(right_eye, fill=(40, 40, 40))

    draw.ellipse([96, 128, 112, 142], fill=BLUSH)
    draw.ellipse([144, 128, 160, 142], fill=BLUSH)

    if mood == "happy":
        draw.arc([112, 130, 144, 158], start=0, end=180, fill=(120, 60, 60), width=5)
    elif mood == "neutral":
        draw.line([116, 148, 140, 148], fill=(120, 60, 60), width=5)
    else:  # sad and sick share a downturned mouth
        draw.arc([112, 150, 144, 178], start=180, end=360, fill=(120, 60, 60), width=5)


def tint(image: Image.Image, color: tuple, amount: float) -> Image.Image:
    overlay = Image.new("RGB", image.size, color)
    return Image.blend(image, overlay, amount)


def render(gender: str, mood: str) -> Image.Image:
    image = Image.new("RGB", (SIZE, SIZE), BACKDROPS[mood])
    draw = ImageDraw.Draw(image)
    rounded_background(draw, BACKDROPS[mood])
    hair_color = GIRL_HAIR if gender == "girl" else BOY_HAIR
    draw_hair(draw, gender, hair_color)
    draw_face(draw, mood)
    if mood == "sick":
        image = tint(image, SICK_TINT, 0.18)
    return image


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for gender in ("girl", "boy"):
        for mood in MOODS:
            path = os.path.join(OUT_DIR, f"{gender}_{mood}.png")
            render(gender, mood).save(path)
            print("wrote", path)


if __name__ == "__main__":
    main()
