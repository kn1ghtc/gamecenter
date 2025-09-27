"""Generate character portraits declared in assets/portrait_sources.json.

The generator procedurally builds stylised portraits so that the StreetBattle
character selector ships with high-quality, fully offline artwork without any
copyright entanglements.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import random
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
PORTRAIT_DIR = ASSETS_DIR / "images" / "portraits"
SOURCES_FILE = ASSETS_DIR / "portrait_sources.json"

WIDTH = 768
HEIGHT = 960

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("portrait-generator")


def iter_sources() -> Iterable[tuple[str, dict]]:
    if not SOURCES_FILE.exists():
        logger.error("portrait_sources.json not found at %s", SOURCES_FILE)
        return []
    try:
        with SOURCES_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse %s: %s", SOURCES_FILE, exc)
        return []

    if not isinstance(data, dict):
        logger.error("portrait_sources.json must contain an object map")
        return []
    return data.items()


def sanitize_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name.lower())


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) not in {6, 3}:
        raise ValueError(f"Unsupported colour value: {value}")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def build_gradient(palette: list[str]) -> Image.Image:
    colours = [hex_to_rgb(col) for col in palette]
    if len(colours) == 1:
        solid = Image.new("RGBA", (WIDTH, HEIGHT), (*colours[0], 255))
        return solid

    gradient = Image.new("RGBA", (1, HEIGHT))
    draw = ImageDraw.Draw(gradient)
    segments = len(colours) - 1
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        seg = min(int(t * segments), segments - 1)
        seg_t = t * segments - seg
        start = colours[seg]
        end = colours[seg + 1]
        colour = tuple(int(lerp(start[idx], end[idx], seg_t)) for idx in range(3))
        draw.point((0, y), fill=colour + (255,))
    return gradient.resize((WIDTH, HEIGHT), resample=Image.BICUBIC)


def apply_pattern(base: Image.Image, pattern: str, accent: str, secondary: str, rng: random.Random) -> None:
    accent_rgb = hex_to_rgb(accent)
    secondary_rgb = hex_to_rgb(secondary)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if pattern == "flames":
        mask = Image.new("L", base.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        for _ in range(16):
            width = rng.uniform(WIDTH * 0.18, WIDTH * 0.32)
            height = rng.uniform(HEIGHT * 0.32, HEIGHT * 0.48)
            left = rng.uniform(-WIDTH * 0.1, WIDTH * 0.9)
            bottom = HEIGHT - rng.uniform(HEIGHT * 0.04, HEIGHT * 0.2)
            bbox = [left, bottom - height, left + width, bottom]
            mask_draw.ellipse(bbox, fill=rng.randint(120, 200))
        mask = mask.filter(ImageFilter.GaussianBlur(48))
        flame_layer = Image.new("RGBA", base.size, accent_rgb + (0,))
        flame_layer.putalpha(mask)
        base.alpha_composite(flame_layer)
    elif pattern == "crescent":
        thickness = int(WIDTH * 0.06)
        bbox = [WIDTH * 0.15, HEIGHT * 0.05, WIDTH * 0.85, HEIGHT * 0.75]
        draw.arc(bbox, start=120, end=330, fill=accent_rgb + (190,), width=thickness)
        inner_bbox = [bbox[0] + thickness, bbox[1] + thickness, bbox[2] - thickness, bbox[3] - thickness]
        draw.arc(inner_bbox, start=135, end=315, fill=secondary_rgb + (160,), width=max(2, thickness // 2))
    elif pattern == "fan":
        center = (WIDTH / 2, HEIGHT * 0.1)
        radius = HEIGHT * 1.1
        spokes = 18
        for idx in range(spokes):
            angle_a = math.radians(70 + idx * 4)
            angle_b = math.radians(70 + (idx + 1) * 4.6)
            points = [
                center,
                (center[0] + radius * math.cos(angle_a), center[1] + radius * math.sin(angle_a)),
                (center[0] + radius * math.cos(angle_b), center[1] + radius * math.sin(angle_b)),
            ]
            colour = accent_rgb if idx % 2 == 0 else secondary_rgb
            draw.polygon(points, fill=colour + (90,))
    elif pattern == "star":
        points = []
        spikes = 5
        outer = WIDTH * 0.36
        inner = WIDTH * 0.16
        center = (WIDTH * 0.5, HEIGHT * 0.32)
        for i in range(spikes * 2):
            radius = outer if i % 2 == 0 else inner
            angle = math.pi / 2 + i * math.pi / spikes
            points.append((center[0] + radius * math.cos(angle), center[1] - radius * math.sin(angle)))
        draw.polygon(points, fill=accent_rgb + (170,))
        outline_width = max(4, int(WIDTH * 0.006))
        draw.line(points + [points[0]], fill=secondary_rgb + (220,), width=outline_width, joint="curve")

    if pattern not in {"flames", "crescent", "fan", "star"}:
        opacity = 60
        for diag in range(-WIDTH, WIDTH, int(WIDTH * 0.08)):
            draw.line([(diag, 0), (diag + WIDTH, HEIGHT)], fill=accent_rgb + (opacity,), width=3)

    base.alpha_composite(layer)


def add_silhouette(base: Image.Image, colour: str, rng: random.Random) -> None:
    rgb = hex_to_rgb(colour)
    mask = Image.new("L", base.size, 0)
    mask_draw = ImageDraw.Draw(mask)

    torso_top = HEIGHT * 0.22
    torso_bottom = HEIGHT * 0.78
    shoulder_width = WIDTH * 0.62
    waist_width = WIDTH * 0.34
    hip_width = WIDTH * 0.44
    leg_width = WIDTH * 0.24

    polygon = [
        (WIDTH * 0.5 - shoulder_width / 2, torso_top),
        (WIDTH * 0.5 + shoulder_width / 2, torso_top),
        (WIDTH * 0.5 + waist_width / 2, torso_top + (torso_bottom - torso_top) * 0.36),
        (WIDTH * 0.5 + hip_width / 2, torso_top + (torso_bottom - torso_top) * 0.62),
        (WIDTH * 0.5 + leg_width / 2, torso_bottom),
        (WIDTH * 0.5 - leg_width / 2, torso_bottom),
        (WIDTH * 0.5 - hip_width / 2, torso_top + (torso_bottom - torso_top) * 0.62),
        (WIDTH * 0.5 - waist_width / 2, torso_top + (torso_bottom - torso_top) * 0.36),
    ]
    mask_draw.polygon(polygon, fill=210)

    head_radius = WIDTH * 0.15
    mask_draw.ellipse(
        [
            WIDTH * 0.5 - head_radius,
            torso_top - head_radius * 0.9,
            WIDTH * 0.5 + head_radius,
            torso_top + head_radius * 0.9,
        ],
        fill=220,
    )

    accent_offset = WIDTH * 0.05
    mask_draw.polygon(
        [
            (WIDTH * 0.5 - shoulder_width / 2 - accent_offset, torso_top + HEIGHT * 0.05),
            (WIDTH * 0.5 - waist_width / 2 - accent_offset * 1.2, torso_bottom - HEIGHT * 0.12),
            (WIDTH * 0.5 - shoulder_width / 2, torso_bottom - HEIGHT * 0.08),
        ],
        fill=160,
    )

    silhouette = Image.new("RGBA", base.size, rgb + (0,))
    silhouette.putalpha(mask)
    blur_radius = WIDTH * 0.02
    silhouette = silhouette.filter(ImageFilter.GaussianBlur(blur_radius))
    base.alpha_composite(silhouette)


def draw_emblem(base: Image.Image, text: str, colour: str, rng: random.Random, size: int | None = None) -> None:
    if not text:
        return
    font_size = size or int(HEIGHT * 0.3)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(base)
    fill = hex_to_rgb(colour)
    stroke = tuple(min(255, int(c * 0.5)) for c in fill)
    draw.text(
        (WIDTH * 0.5, HEIGHT * 0.42),
        text,
        fill=fill,
        font=font,
        anchor="mm",
        stroke_width=max(2, font_size // 18),
        stroke_fill=stroke,
    )


def draw_nameplate(base: Image.Image, display_name: str, accent: str) -> None:
    if not display_name:
        return
    banner_height = int(HEIGHT * 0.16)
    banner = Image.new("RGBA", (WIDTH, banner_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(banner)
    draw.rectangle([0, 0, WIDTH, banner_height], fill=(12, 12, 18, 210))
    draw.rectangle([0, banner_height - 8, WIDTH, banner_height], fill=hex_to_rgb(accent) + (255,))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(banner_height * 0.42))
    except OSError:
        font = ImageFont.load_default()
    draw.text(
        (WIDTH * 0.5, banner_height * 0.46),
        display_name,
        font=font,
        fill=(242, 242, 242, 255),
        anchor="mm",
    )
    base.alpha_composite(banner, dest=(0, HEIGHT - banner_height))


def add_surface_texture(base: Image.Image) -> None:
    noise = Image.effect_noise((WIDTH, HEIGHT), 48).convert("L")
    noise = noise.point(lambda v: int(v * 0.4))
    alpha = noise.point(lambda v: int(40 + v * 0.25))
    texture = Image.merge("RGBA", (noise, noise, noise, alpha))
    base.alpha_composite(texture)


def generate_portrait(identifier: str, spec: dict, destination: Path, overwrite: bool = False) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not overwrite:
        logger.info("Skipping existing %s", destination.name)
        return True

    palette = spec.get("palette") or ["#1c1c1c", "#3a3a3a", "#5a5a5a"]
    if not isinstance(palette, list) or not palette:
        logger.error("Portrait spec %s has invalid palette", identifier)
        return False

    accent = spec.get("accent_color", palette[-1])
    secondary = spec.get("secondary_color", palette[0])
    silhouette_colour = spec.get("silhouette_color", accent)
    emblem_text = spec.get("emblem_text", "")
    emblem_color = spec.get("emblem_color", accent)
    emblem_size = spec.get("emblem_size")
    pattern = spec.get("pattern", "diagonal")
    display_name = spec.get("display_name", identifier.replace("_", " ").title())

    rng = random.Random(identifier)

    try:
        canvas = build_gradient(palette).convert("RGBA")
        apply_pattern(canvas, pattern, accent, secondary, rng)
        add_silhouette(canvas, silhouette_colour, rng)
        draw_emblem(canvas, emblem_text, emblem_color, rng, size=emblem_size)
        draw_nameplate(canvas, display_name, accent)
        add_surface_texture(canvas)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to generate portrait %s: %s", identifier, exc)
        return False

    try:
        canvas.save(destination, format="PNG", optimize=True)
    except OSError as exc:
        logger.error("Failed to write %s: %s", destination, exc)
        return False

    logger.info("Generated %s", destination.name)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate StreetBattle portrait assets")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate even if cached")
    args = parser.parse_args()

    PORTRAIT_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    total = 0
    for key, spec in iter_sources():
        if not isinstance(spec, dict):
            logger.error("Portrait spec for %s must be an object", key)
            continue
        total += 1
        filename = sanitize_filename(key) + ".png"
        dest = PORTRAIT_DIR / filename
        if generate_portrait(key, spec, dest, overwrite=args.overwrite):
            success += 1
    logger.info("Generated %s/%s portraits", success, total)


if __name__ == "__main__":
    main()
