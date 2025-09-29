from __future__ import annotations

"""Sprite loading utilities for the 2.5D StreetBattle mode."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - pygame is optional when running without 2.5D mode
    import pygame
except ImportError:  # pragma: no cover - handled at runtime via launcher
    pygame = None  # type: ignore


SPRITE_ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets" / "sprites"


@dataclass
class SpriteFrame:
    surface: Any
    duration: float  # seconds


class SpriteAnimation:
    """Simple frame-based animation compatible with sprite sheets or procedural art."""

    def __init__(self, name: str, frames: List[SpriteFrame], loop: bool = True) -> None:
        if pygame is None:
            raise RuntimeError("Pygame must be available to create animations")
        self.name = name
        self.frames = frames
        self.loop = loop
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def reset(self) -> None:
        self.index = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt: float) -> None:
        if not self.frames:
            return
        if self.finished and not self.loop:
            return
        self.timer += dt
        while self.timer >= self.frames[self.index].duration:
            self.timer -= self.frames[self.index].duration
            if self.index + 1 < len(self.frames):
                self.index += 1
            elif self.loop:
                self.index = 0
            else:
                self.finished = True
                self.index = len(self.frames) - 1
                self.timer = 0.0
                break

    @property
    def current_surface(self) -> Any:
        return self.frames[self.index].surface

    @property
    def current_index(self) -> int:
        return self.index

    @property
    def total_duration(self) -> float:
        return sum(frame.duration for frame in self.frames)


def _load_sprite_manifest(name: str) -> Optional[Dict[str, Any]]:
    manifest_path = SPRITE_ASSET_ROOT / name / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with manifest_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                data["__manifest_path__"] = manifest_path  # type: ignore[index]
                return data
    except Exception:
        return None
    return None


def _apply_color_mod(surface: Any, color_mod: Optional[Dict[str, Any]]) -> Any:
    if not color_mod:
        return surface
    result = surface.copy()
    multiply = color_mod.get("multiply") if isinstance(color_mod, dict) else None
    if multiply:
        mul = [max(0.0, float(value)) for value in multiply[:3]]
        multiplier = pygame.Surface(result.get_size(), pygame.SRCALPHA)
        multiplier.fill(
            (
                min(255, int(mul[0] * 255)),
                min(255, int((mul[1] if len(mul) > 1 else mul[0]) * 255)),
                min(255, int((mul[2] if len(mul) > 2 else mul[0]) * 255)),
                255,
            )
        )
        result.blit(multiplier, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    add = color_mod.get("add") if isinstance(color_mod, dict) else None
    if add:
        add_values = [max(0.0, float(value)) for value in add[:3]]
        additive = pygame.Surface(result.get_size(), pygame.SRCALPHA)
        additive.fill(
            (
                min(255, int(add_values[0])),
                min(255, int((add_values[1] if len(add_values) > 1 else add_values[0]))),
                min(255, int((add_values[2] if len(add_values) > 2 else add_values[0]))),
                0,
            )
        )
        result.blit(additive, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return result


def _slice_sheet(
    image: Any,
    frame_size: Tuple[int, int],
    sequence: List[int],
    duration: float,
    durations: Optional[List[float]] = None,
    color_mod: Optional[Dict[str, Any]] = None,
) -> List[SpriteFrame]:
    frames: List[SpriteFrame] = []
    width, height = image.get_size()
    frame_w, frame_h = frame_size
    columns = max(1, width // frame_w)
    for idx, frame_index in enumerate(sequence):
        row = frame_index // columns
        col = frame_index % columns
        rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
        surface = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        surface.blit(image, (0, 0), rect)
        if color_mod:
            surface = _apply_color_mod(surface, color_mod)
        frame_duration = durations[idx] if durations and idx < len(durations) else duration
        frames.append(SpriteFrame(surface, frame_duration))
    return frames


def load_sprite_animations(name: str) -> Optional[Tuple[Dict[str, SpriteAnimation], Dict[str, Any]]]:
    if pygame is None:
        return None
    manifest = _load_sprite_manifest(name)
    if not manifest:
        return None
    manifest_dir = manifest["__manifest_path__"].parent  # type: ignore[index]
    states = manifest.get("states", {})
    animations: Dict[str, SpriteAnimation] = {}
    metadata: Dict[str, Any] = {}
    top_color_mod = manifest.get("color_mod") if isinstance(manifest, dict) else None
    hit_frame_map: Dict[str, Iterable[int]] = {}
    for state, cfg in states.items():
        sheet_name = cfg.get("sheet")
        if not sheet_name:
            continue
        sheet_path = manifest_dir / sheet_name
        if not sheet_path.exists():
            continue
        try:
            surface = pygame.image.load(sheet_path.as_posix()).convert_alpha()
        except Exception:
            continue
        frame_size = cfg.get("frame_size") or [surface.get_width(), surface.get_height()]
        if not isinstance(frame_size, (list, tuple)) or len(frame_size) != 2:
            frame_size = [surface.get_width(), surface.get_height()]
        frame_size_tuple = (int(frame_size[0]), int(frame_size[1]))
        sequence = cfg.get("sequence") or list(range(cfg.get("frames", 1)))
        if not sequence:
            total_frames = (surface.get_width() // frame_size_tuple[0]) * (surface.get_height() // frame_size_tuple[1])
            sequence = list(range(total_frames))
        fps = cfg.get("fps", 8)
        base_duration = 1.0 / max(1, fps)
        durations = cfg.get("durations")
        state_color_mod = cfg.get("color_mod") if isinstance(cfg, dict) else None
        frames = _slice_sheet(
            surface,
            frame_size_tuple,
            sequence,
            base_duration,
            durations,
            color_mod=state_color_mod or top_color_mod,
        )
        loop = bool(cfg.get("loop", True))
        animations[state] = SpriteAnimation(state, frames, loop=loop)
        if "hit_frames" in cfg:
            frames_value = cfg["hit_frames"]
            if isinstance(frames_value, (list, tuple)):
                hit_frame_map[state] = tuple(int(i) for i in frames_value)
    metadata["source"] = manifest.get("source")
    license_value = manifest.get("license")
    if license_value:
        metadata["license"] = license_value
    if hit_frame_map:
        metadata["hit_frames"] = hit_frame_map
        if "attack" not in metadata and "attack_light" in hit_frame_map:
            metadata["attack_frames"] = tuple(hit_frame_map["attack_light"])
    if "attack" not in animations and "attack_light" in animations:
        animations["attack"] = animations["attack_light"]
    return animations, metadata


def clone_animations_with_color(
    animations: Dict[str, SpriteAnimation],
    color_mod: Optional[Dict[str, Any]],
) -> Dict[str, SpriteAnimation]:
    """Return a tinted clone of the provided animations."""

    if pygame is None or not color_mod:
        return animations
    tinted: Dict[str, SpriteAnimation] = {}
    for name, animation in animations.items():
        frames = [SpriteFrame(_apply_color_mod(frame.surface, color_mod), frame.duration) for frame in animation.frames]
        tinted[name] = SpriteAnimation(animation.name, frames, loop=animation.loop)
    return tinted


__all__ = [
    "SpriteFrame",
    "SpriteAnimation",
    "SPRITE_ASSET_ROOT",
    "clone_animations_with_color",
    "load_sprite_animations",
]
