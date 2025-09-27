"""Simple texture manager for Kyo Kusanagi assets.

This module keeps the enhanced character manager happy even when high end
texture remapping is unavailable.  The implementation focuses on a pragmatic
workflow: reuse the baked textures that ship with the Sketchfab download and
apply them uniformly across the model.  It ensures the loader never raises a
`ModuleNotFoundError` and avoids noisy fallback warnings during runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from panda3d.core import Texture, Filename


class KyoTextureManager:
    """Minimal texture helper used by :mod:`enhanced_character_manager`."""

    def __init__(self, loader, assets_dir: Optional[Path] = None) -> None:
        self.loader = loader
        script_dir = Path(__file__).parent
        if assets_dir is None:
            assets_dir = script_dir / "assets" / "characters" / "kyo_kusanagi" / "sketchfab" / "textures"
        self.textures_dir = Path(assets_dir)

    def apply_kyo_textures(self, model) -> bool:
        """Apply a best-effort albedo texture to the supplied model.

        Returns ``True`` when a texture was applied successfully, otherwise
        ``False`` so the caller can fall back to basic material adjustments.
        """

        if model is None or model.isEmpty():
            return False

        albedo_candidates = [
            self.textures_dir / "albedo.png",
            self.textures_dir / "albedo.jpg",
            self.textures_dir / "24_face_0.2_0_0_baseColor.png",
        ]

        texture: Optional[Texture] = None
        for candidate in albedo_candidates:
            if not candidate.exists():
                continue
            try:
                panda_path = Filename.fromOsSpecific(str(candidate))
                panda_path.makeCanonical()
                texture = self.loader.loadTexture(panda_path)
            except Exception:
                texture = None
            if texture:
                break

        if not texture:
            return False

        try:
            texture.setMinfilter(Texture.FTLinearMipmapLinear)
            texture.setMagfilter(Texture.FTLinear)
            model.clearTexture()
            model.setTexture(texture, 1)
            return True
        except Exception:
            return False
