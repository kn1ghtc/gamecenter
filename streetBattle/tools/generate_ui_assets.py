"""Generate UI asset textures for StreetBattle.

This script creates high quality procedural textures so the game can run
fully offline without having to download CC0 artwork at runtime.  It can be
extended with additional assets if needed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from panda3d.core import Filename, PNMImage


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_png(image: PNMImage, destination: Path) -> None:
    ensure_dir(destination.parent)
    if not image.write(Filename.fromOsSpecific(str(destination))):
        raise RuntimeError(f"Failed to write {destination}")


def make_card_panel(width: int = 384, height: int = 256) -> PNMImage:
    """Create a beveled panel with subtle radial lighting."""
    img = PNMImage(width, height, 4)
    radius = min(width, height) // 6

    for y in range(height):
        v = y / max(1, height - 1)
        vertical_tint = 0.24 + 0.18 * (1.0 - v)
        for x in range(width):
            u = x / max(1, width - 1)
            center_bias = (abs(u - 0.5) * 2.0)
            edge_mix = 0.12 * center_bias
            r = 0.18 + vertical_tint + edge_mix * 0.6
            g = 0.20 + vertical_tint * 0.8
            b = 0.28 + vertical_tint * 0.5
            alpha = 0.9

            dx = min(x, width - 1 - x)
            dy = min(y, height - 1 - y)
            if dx < radius and dy < radius:
                dist = ((radius - dx) ** 2 + (radius - dy) ** 2) ** 0.5
                if dist >= radius:
                    alpha = 0.0
                else:
                    blend = max(0.0, min(1.0, 1.0 - dist / radius))
                    alpha *= blend

            img.setXelA(x, y, min(1.0, r), min(1.0, g), min(1.0, b), alpha)
    img.gaussianFilter(1)
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate UI textures")
    parser.add_argument(
        "--output",
        default=Path(__file__).resolve().parent.parent / "assets" / "images" / "ui",
        type=Path,
        help="Directory to store generated textures",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate textures even if they already exist",
    )
    args = parser.parse_args()

    output_dir = args.output
    ensure_dir(output_dir)

    card_panel_path = output_dir / "card_panel.png"
    if args.overwrite or not card_panel_path.exists():
        print(f"Generating {card_panel_path} ...")
        image = make_card_panel()
        write_png(image, card_panel_path)
    else:
        print(f"Skipping {card_panel_path}, already exists (use --overwrite to regenerate)")


if __name__ == "__main__":
    main()
