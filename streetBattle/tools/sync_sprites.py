#!/usr/bin/env python3
"""Synchronise 2.5D sprite sheets for the StreetBattle pygame mode.

The pipeline fetches curated open-source sprite sheets, slices them according to
predefined metadata, and emits ``manifest.json`` files that the runtime loader
consumes (see ``twod5/game.py``).  Each manifest describes the frame layout,
looping behaviour, and attack frame timing so the game can mix procedural and
hand-drawn assets seamlessly.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

try:  # Optional dependency used to auto-detect frame dimensions
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None  # type: ignore

SPRITE_ROOT = Path(__file__).resolve().parents[1] / "assets" / "sprites"
SPRITE_ROOT.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("streetbattle.sprite_sync")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@dataclass
class StateConfig:
    name: str
    url: str
    grid: Iterable[int]
    fps: int
    loop: bool
    filename: str
    frame_size: Optional[List[int]] = None
    sequence: Optional[List[int]] = None
    hit_frames: Optional[List[int]] = None


SPRITE_SOURCES: Dict[str, Dict[str, Any]] = {
    # Only characters with high-quality portraits are supported
}


def download_file(url: str, destination: Path, skip_existing: bool) -> bool:
    if destination.exists() and skip_existing:
        logger.info("Using cached %s", destination.name)
        return True
    logger.info("Fetching %s", url)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network failure is expected sometimes
        logger.warning("Download failed for %s: %s", url, exc)
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return True


def _palette_for_character(key: str) -> Dict[str, tuple[int, int, int]]:
    # Default palette for all characters
    return {
        "base": (160, 160, 160),
        "accent": (220, 220, 220),
        "shadow": (96, 96, 96),
    }


def _procedural_draw_frame(draw: "ImageDraw.ImageDraw", bbox: tuple[int, int, int, int], colors: Dict[str, tuple[int, int, int]], anim_phase: float, variant: str) -> None:
    x0, y0, x1, y1 = bbox
    width = x1 - x0
    height = y1 - y0
    torso_width = int(width * 0.28)
    torso_height = int(height * 0.45)
    hip_y = y0 + int(height * 0.35)
    offset = int(math.sin(anim_phase) * width * 0.08)
    draw.rectangle((x0 + width // 2 - torso_width // 2 + offset, hip_y, x0 + width // 2 + torso_width // 2 + offset, hip_y + torso_height), fill=colors["base"])
    leg_height = int(height * 0.35)
    leg_width = int(width * 0.18)
    stride = int(math.sin(anim_phase * 2.0) * width * 0.12)
    draw.rectangle((x0 + width // 2 - leg_width - stride, hip_y + torso_height, x0 + width // 2 - stride, hip_y + torso_height + leg_height), fill=colors["shadow"])
    draw.rectangle((x0 + width // 2 + stride, hip_y + torso_height, x0 + width // 2 + leg_width + stride, hip_y + torso_height + leg_height), fill=colors["shadow"])
    arm_width = int(width * 0.12)
    arm_height = int(height * 0.28)
    punch = int(math.sin(anim_phase * 1.4 + (0 if variant == "idle" else math.pi / 2)) * width * 0.18)
    draw.rectangle((x0 + width // 2 - torso_width // 2 - arm_width, hip_y + int(height * 0.08), x0 + width // 2 - torso_width // 2, hip_y + int(height * 0.08) + arm_height), fill=colors["accent"])
    draw.rectangle((x0 + width // 2 + torso_width // 2, hip_y + int(height * 0.08), x0 + width // 2 + torso_width // 2 + arm_width + punch, hip_y + int(height * 0.08) + arm_height), fill=colors["accent"])
    head_radius = int(width * 0.18)
    draw.ellipse((x0 + width // 2 - head_radius, hip_y - head_radius * 2, x0 + width // 2 + head_radius, hip_y - head_radius), fill=colors["accent"])
    visor_height = int(head_radius * 0.6)
    draw.rectangle((x0 + width // 2 - head_radius, hip_y - head_radius * 2 + visor_height, x0 + width // 2 + head_radius, hip_y - head_radius * 2 + visor_height + int(visor_height * 0.4)), fill=(0, 0, 0, 180))


def generate_placeholder_sheet(character: str, state: StateConfig, output_path: Path) -> bool:
    palette = _palette_for_character(character)
    try:
        cols, rows = map(int, state.grid)
    except Exception:
        cols, rows = 4, 1
    frame_w = int(state.frame_size[0]) if state.frame_size else 64
    frame_h = int(state.frame_size[1]) if state.frame_size else 64
    sheet_width = frame_w * cols
    sheet_height = frame_h * rows
    try:
        if Image is None:
            raise RuntimeError("Pillow is unavailable")
        image = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        total_frames = cols * rows
        for index in range(total_frames):
            col = index % cols
            row = index // cols
            x0 = col * frame_w
            y0 = row * frame_h
            bbox = (x0, y0, x0 + frame_w, y0 + frame_h)
            phase = index / max(1, total_frames - 1)
            variant = state.name
            _procedural_draw_frame(draw, bbox, palette, phase * math.pi * 2.0, variant)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        logger.info("Generated procedural sheet for %s:%s", character, state.name)
        return True
    except Exception as exc:
        try:
            import pygame

            pygame.init()
            surface = pygame.Surface((sheet_width, sheet_height), flags=pygame.SRCALPHA)
            total_frames = cols * rows
            for index in range(total_frames):
                col = index % cols
                row = index // cols
                rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                phase = index / max(1, total_frames - 1)
                base = palette["base"]
                accent = palette["accent"]
                shadow = palette["shadow"]
                pygame.draw.rect(surface, shadow, rect.inflate(-frame_w * 0.4, -frame_h * 0.15))
                pygame.draw.rect(surface, base, rect.inflate(-frame_w * 0.6, -frame_h * 0.45))
                punch_width = int(frame_w * 0.2 + math.sin(phase * math.pi * 2.0) * frame_w * 0.12)
                punch_rect = pygame.Rect(rect.centerx + punch_width // 2, rect.centery - frame_h // 4, punch_width, frame_h // 4)
                pygame.draw.rect(surface, accent, punch_rect)
                head_rect = pygame.Rect(rect.centerx - frame_w // 6, rect.top + frame_h // 6, frame_w // 3, frame_h // 3)
                pygame.draw.ellipse(surface, accent, head_rect)
            pygame.image.save(surface, output_path.as_posix())
            pygame.quit()
            logger.info("Generated pygame procedural sheet for %s:%s (fallback path)", character, state.name)
            return True
        except Exception as fallback_exc:  # pragma: no cover - environment-specific
            logger.warning("Failed to generate placeholder for %s:%s (%s / %s)", character, state.name, exc, fallback_exc)
            return False


def infer_frame_size(state: StateConfig, image_path: Path) -> tuple[int, int]:
    if state.frame_size:
        return int(state.frame_size[0]), int(state.frame_size[1])
    if Image is None:
        raise RuntimeError(
            "Pillow is required to infer frame dimensions automatically. Provide frame_size in the state config."
        )
    with Image.open(image_path) as img:
        width, height = img.size
    cols, rows = state.grid
    return width // int(cols), height // int(rows)


def build_manifest_entry(state: StateConfig, local_filename: str, frame_size: tuple[int, int]) -> Dict[str, Any]:
    sequence = state.sequence
    if not sequence:
        cols, rows = state.grid
        total = int(cols) * int(rows)
        sequence = list(range(total))
    entry = {
        "sheet": local_filename,
        "frame_size": [frame_size[0], frame_size[1]],
        "fps": state.fps,
        "loop": state.loop,
        "sequence": sequence,
    }
    if state.hit_frames:
        entry["hit_frames"] = state.hit_frames
    return entry


def process_character(key: str, cfg: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    char_dir = SPRITE_ROOT / key
    if args.clean and char_dir.exists():
        for item in char_dir.glob("*"):
            if item.is_file():
                item.unlink()
    char_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "name": key,
        "display_name": cfg.get("display_name", key.title()),
        "source": cfg.get("source"),
        "license": cfg.get("license"),
        "states": {},
    }
    downloaded = 0
    available_states = 0
    for state in cfg.get("states", []):
        dest = char_dir / state.filename
        success = True
        if not args.skip_download:
            success = download_file(state.url, dest, skip_existing=not args.force)
            if success:
                downloaded += 1
        if not dest.exists():
            placeholder_ok = generate_placeholder_sheet(key, state, dest)
            if placeholder_ok:
                success = True
            else:
                logger.warning("Missing sprite sheet for %s:%s", key, state.name)
                continue
        if not dest.exists():
            continue
        available_states += 1
        try:
            frame_size = infer_frame_size(state, dest)
        except Exception as exc:
            logger.warning("Unable to determine frame size for %s:%s (%s)", key, state.name, exc)
            continue
        manifest_entry = build_manifest_entry(state, dest.name, frame_size)
        manifest["states"][state.name] = manifest_entry

    if downloaded == 0:
        manifest["source"] = "Procedural offline placeholder"
        manifest["license"] = "Generated"
        for state_name, entry in manifest["states"].items():
            entry["procedural"] = True

    manifest_path = char_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=4, ensure_ascii=False), encoding="utf-8")
    return {
        "character": key,
        "manifest": manifest_path.relative_to(SPRITE_ROOT.parent),
        "downloaded": downloaded,
        "states": available_states,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronise sprite sheets for the StreetBattle 2.5D mode")
    parser.add_argument(
        "--characters",
        nargs="*",
        default=list(SPRITE_SOURCES.keys()),
        help="Subset of characters to process (default: all registered)",
    )
    parser.add_argument("--skip-download", action="store_true", help="Regenerate manifests without downloading")
    parser.add_argument("--force", action="store_true", help="Re-download files even if cached")
    parser.add_argument("--clean", action="store_true", help="Remove cached sprite sheets before syncing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary: List[Dict[str, Any]] = []
    for key in args.characters:
        cfg = SPRITE_SOURCES.get(key)
        if not cfg:
            logger.warning("Unknown sprite pack '%s'", key)
            continue
        summary.append(process_character(key, cfg, args))
    logger.info("Sprite sync complete:")
    for item in summary:
        logger.info(
            "%-8s | states=%d | downloaded=%d | manifest=%s",
            item["character"],
            item["states"],
            item["downloaded"],
            item["manifest"],
        )


if __name__ == "__main__":
    main()
