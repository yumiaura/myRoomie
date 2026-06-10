"""Generate flat 2D placeholder scenes for the point-and-click web client.

Run from the repo root:  python tools/make_scenes.py
Writes scene PNGs + manifest.json to client/assets/scenes/.

Every labeled box is also a clickable hotspot region. manifest.json records
those regions as percentages — that is the contract, so real art can be
painted to the same layout and dropped in with no code change.
"""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw

OUT_DIR = os.path.join("client", "assets", "scenes")
CANVAS = (960, 640)

# scene -> {bg, floor (optional band color), regions: [(id, x%, y%, w%, h%, fill, label)]}
SCENES = {
    "apartment": {
        "bg": (250, 238, 222),
        "floor": (224, 201, 175),
        "regions": [
            ("bed", 4, 22, 26, 30, (180, 150, 205), "BED"),
            ("kitchen", 33, 15, 24, 25, (205, 180, 150), "KITCHEN"),
            ("wardrobe", 61, 24, 14, 46, (170, 140, 110), "WARDROBE"),
            ("shower", 80, 24, 16, 50, (150, 200, 222), "SHOWER"),
            ("roomie", 40, 36, 20, 42, (255, 224, 196), "ROOMIE"),
            ("mailbox", 21, 60, 9, 18, (200, 120, 120), "MAIL"),
            ("notebook", 40, 64, 11, 13, (150, 180, 150), "NOTES"),
            ("broom", 52, 70, 10, 18, (210, 200, 120), "CLEAN"),
            ("door", 4, 56, 15, 40, (120, 90, 70), "DOOR"),
        ],
    },
    "street": {
        "bg": (190, 214, 235),
        "floor": (150, 150, 158),
        "regions": [
            ("grocery", 5, 28, 26, 48, (120, 190, 130), "GROCERY"),
            ("mall", 37, 22, 26, 54, (235, 160, 195), "MALL"),
            ("work", 69, 18, 26, 60, (130, 160, 220), "WORK"),
            ("home", 3, 72, 15, 26, (150, 110, 85), "HOME"),
        ],
    },
    "grocery": {
        "bg": (236, 247, 236),
        "floor": (210, 224, 210),
        "regions": [
            ("shelf", 14, 24, 72, 54, (150, 200, 160), "FOOD SHELF"),
            ("back", 2, 4, 13, 13, (200, 200, 200), "BACK"),
        ],
    },
    "mall": {
        "bg": (250, 235, 244),
        "floor": (224, 206, 218),
        "regions": [
            ("gifts", 9, 26, 37, 52, (240, 180, 120), "GIFTS"),
            ("clothes", 54, 26, 37, 52, (170, 160, 230), "CLOTHES"),
            ("back", 2, 4, 13, 13, (200, 200, 200), "BACK"),
        ],
    },
    "work": {
        "bg": (224, 232, 248),
        "floor": (198, 206, 224),
        "regions": [
            ("desk", 20, 30, 60, 46, (150, 175, 225), "WORK DESK"),
            ("back", 2, 4, 13, 13, (200, 200, 200), "BACK"),
        ],
    },
}


def pixels(region: tuple) -> tuple:
    code, xp, yp, wp, hp, fill, label = region
    x = xp / 100.0 * CANVAS[0]
    y = yp / 100.0 * CANVAS[1]
    w = wp / 100.0 * CANVAS[0]
    h = hp / 100.0 * CANVAS[1]
    return x, y, w, h, fill, label


def render(name: str, spec: dict) -> Image.Image:
    image = Image.new("RGB", CANVAS, spec["bg"])
    draw = ImageDraw.Draw(image)
    if spec.get("floor"):
        draw.rectangle([0, int(CANVAS[1] * 0.62), CANVAS[0], CANVAS[1]], fill=spec["floor"])
    for region in spec["regions"]:
        x, y, w, h, fill, label = pixels(region)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=fill, outline=(60, 50, 50), width=3)
        text_width = draw.textlength(label)
        draw.text((x + w / 2 - text_width / 2, y + h / 2 - 6), label, fill=(40, 35, 35))
    return image


def manifest() -> dict:
    scenes = {}
    for name, spec in SCENES.items():
        scenes[name] = {
            "bg": f"scene_{name}.png",
            "hotspots": [
                {"id": code, "x": xp, "y": yp, "w": wp, "h": hp}
                for (code, xp, yp, wp, hp, fill, label) in spec["regions"]
            ],
        }
    return {
        "canvas": {"width": CANVAS[0], "height": CANVAS[1]},
        "coordinates": "percent",
        "scenes": scenes,
        "guidelines": (
            "Each hotspot is a clickable region in percent of the canvas. Real art "
            "must keep the same canvas aspect and place interactive objects within "
            "these regions (or update both this manifest and web/scenes.js together). "
            "Backgrounds are opaque PNGs named scene_<name>.png; the roomie avatar in "
            "the apartment is drawn by the client over the 'roomie' region using the "
            "portrait art under /assets/portraits."
        ),
    }


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, spec in SCENES.items():
        path = os.path.join(OUT_DIR, f"scene_{name}.png")
        render(name, spec).save(path)
        print("wrote", path)
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest(), handle, indent=2)
    print("wrote", manifest_path)


if __name__ == "__main__":
    main()
