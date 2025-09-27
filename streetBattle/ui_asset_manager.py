"""UI asset management for StreetBattle character selection.

This helper mirrors the portrait manager but focuses on decorative UI
textures (panels, banners, etc.).  Assets are cached under
``assets/images/ui`` after the first download so the game can run fully
offline thereafter.
"""
from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

import requests
from panda3d.core import Texture, Filename

logger = logging.getLogger("streetbattle.ui_assets")

TextureFactory = Callable[[], Texture]


class UIAssetManager:
    """Resolve and cache decorative UI textures."""

    SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

    def __init__(self, loader, assets_dir: str | Path) -> None:
        self.loader = loader
        self.assets_dir = Path(assets_dir)
        self.cache_dir = self.assets_dir / "images" / "ui"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sources = self._load_sources()
        self._texture_cache: Dict[str, Texture] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def get_texture(self, key: str, fallback_factory: TextureFactory) -> Texture:
        if key in self._texture_cache:
            return self._texture_cache[key]

        texture: Optional[Texture] = None

        for candidate in self._local_candidates(key):
            texture = self._load_texture(candidate)
            if texture:
                break

        if texture is None:
            urls = self._resolve_urls(key)
            for url in urls:
                local_path = self._download_asset(url, key)
                if local_path:
                    texture = self._load_texture(local_path)
                if texture:
                    break

        if texture is None:
            texture = fallback_factory()

        self._texture_cache[key] = texture
        return texture

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _load_sources(self) -> Dict[str, Dict[str, str]]:
        mapping_file = self.assets_dir / "ui_sources.json"
        if not mapping_file.exists():
            return {}
        try:
            with mapping_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.warning("Failed to load ui_sources.json: %s", exc)
        return {}

    def _local_candidates(self, key: str) -> Iterable[Path]:
        directory = self.cache_dir
        manual = directory / f"{key}.png"
        if manual.exists():
            yield manual
        for ext in self.SUPPORTED_EXTENSIONS:
            candidate = directory / f"{key}{ext}"
            if candidate.exists():
                yield candidate
        pattern = f"{key}_*"
        for candidate in sorted(directory.glob(pattern)):
            if candidate.exists():
                yield candidate

    def _resolve_urls(self, key: str) -> list[str]:
        urls: list[str] = []

        entry = self.sources.get(key)
        if isinstance(entry, dict):
            possible = [entry.get("urls"), entry.get("url"), entry.get("fallbacks")]
            for item in possible:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, (list, tuple, set)):
                    for value in item:
                        if isinstance(value, str):
                            urls.append(value)
        elif isinstance(entry, str):
            urls.append(entry)

        deduped: list[str] = []
        seen = set()
        for url in urls:
            clean = (url or "").strip()
            if not clean:
                continue
            if clean in seen:
                continue
            seen.add(clean)
            deduped.append(clean)
        return deduped

    def _download_asset(self, url: str, key: str) -> Optional[Path]:
        logger.info("Fetching UI asset %s from %s", key, url)
        try:
            headers = {
                "User-Agent": "StreetBattle/1.0 (ui-asset-loader)",
                "Accept": "image/png,image/jpeg,image/webp;q=0.9,*/*;q=0.8",
            }
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("UI asset download failed for %s: %s", key, exc)
            return None

        extension = self._guess_extension(url, response.headers.get("Content-Type"))
        filename = self._make_filename(key, extension, response.content)
        destination = self.cache_dir / filename
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                return destination
            with destination.open("wb") as fh:
                fh.write(response.content)
        except Exception as exc:
            logger.warning("Failed to persist UI asset %s: %s", destination, exc)
            return None
        return destination

    def _load_texture(self, path: Path) -> Optional[Texture]:
        if not path.exists():
            return None
        try:
            panda_path = Filename.fromOsSpecific(str(path))
            panda_path.makeCanonical()
            tex = self.loader.loadTexture(panda_path)
            if tex:
                tex.setMinfilter(Texture.FTLinearMipmapLinear)
                tex.setMagfilter(Texture.FTLinear)
            return tex
        except Exception as exc:
            logger.warning("Failed to load UI texture %s: %s", path, exc)
            return None

    @staticmethod
    def _guess_extension(url: str, content_type: Optional[str]) -> str:
        if content_type:
            ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
            if ext in UIAssetManager.SUPPORTED_EXTENSIONS:
                return ext
        parsed = os.path.splitext(url.split("?")[0])[1].lower()
        if parsed in UIAssetManager.SUPPORTED_EXTENSIONS:
            return parsed
        return ".png"

    @staticmethod
    def _make_filename(key: str, extension: str, payload: bytes) -> str:
        digest = hashlib.sha1(payload).hexdigest()[:10]
        safe_key = key.replace('/', '_')
        return f"{safe_key}_{digest}{extension}"
