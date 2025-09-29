"""Portrait management utilities for the StreetBattle UI.

This module centralises logic for retrieving character portrait imagery.  It
supports three tiers of sources, in priority order:

1. Local overrides under ``assets/images/portraits`` (PNG/JPG/WEBP)
2. Portrait URLs declared in ``assets/portrait_sources.json`` or within the
   character profile metadata (``portrait_url`` / ``portrait_urls``)
3. Procedurally generated gradients supplied by the caller

Downloads are cached on disk so we only hit the network once per character.
All network failures degrade gracefully to the procedural fallback texture, so
offline play remains fully supported.
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

logger = logging.getLogger("streetbattle.portraits")

TextureFactory = Callable[[], Texture]


class PortraitManager:
    """Resolve and cache portrait textures for characters."""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    def __init__(self, loader, assets_dir: str | Path) -> None:
        self.loader = loader
        self.assets_dir = Path(assets_dir)
        self.cache_dir = self.assets_dir / "images" / "portraits"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sources = self._load_sources()
        self._texture_cache: Dict[str, Texture] = {}

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def get_texture(self, character_key: str, profile: Dict, fallback_factory: TextureFactory) -> Texture:
        key = character_key
        if key in self._texture_cache:
            return self._texture_cache[key]

        texture: Optional[Texture] = None

        # 1) local overrides (profile hint or cached download)
        for candidate in self._local_candidates(key, profile):
            texture = self._load_texture(candidate)
            if texture:
                break

        # 2) remote fetch when local not available
        if texture is None:
            remote_urls = self._resolve_remote_urls(key, profile)
            for url in remote_urls:
                local_path = self._download_portrait(url, key)
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
        mapping_file = self.assets_dir / "portrait_sources.json"
        if not mapping_file.exists():
            return {}
        try:
            with mapping_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.warning("Failed to load portrait_sources.json: %s", exc)
        return {}

    def _local_candidates(self, key: str, profile: Dict) -> Iterable[Path]:
        hints = []
        manual_path = profile.get('portrait_local') or profile.get('portrait_path')
        if manual_path:
            hints.append(Path(manual_path))
        directory = self.cache_dir
        for ext in self.SUPPORTED_EXTENSIONS:
            hints.append(directory / f"{key}{ext}")
            hints.append(directory / f"{key}_official{ext}")
        # allow nested folders per key
        hints.append(directory / key / "portrait.png")
        hints.append(directory / key / "portrait.jpg")
        for candidate in hints:
            if candidate.exists():
                yield candidate

        # hashed cache entries (key_digest.ext)
        for ext in self.SUPPORTED_EXTENSIONS:
            pattern = f"{key}_*{ext}"
            for candidate in sorted(directory.glob(pattern)):
                if candidate.exists():
                    yield candidate

    def _resolve_remote_urls(self, key: str, profile: Dict) -> list[str]:
        urls: list[str] = []

        def _append(value):
            if isinstance(value, str):
                urls.append(value)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    if isinstance(item, str):
                        urls.append(item)

        # Profile overrides take precedence
        _append(profile.get('portrait_url'))
        _append(profile.get('portrait_urls'))

        entry = self.sources.get(key) or self.sources.get(profile.get('id', key))
        if isinstance(entry, dict):
            _append(entry.get('urls'))
            _append(entry.get('portrait_urls'))
            _append(entry.get('url'))
            _append(entry.get('portrait_url'))
        elif isinstance(entry, str):
            urls.append(entry)

        deduped: list[str] = []
        seen = set()
        for url in urls:
            if not url:
                continue
            clean = url.strip()
            if not clean:
                continue
            if clean in seen:
                continue
            seen.add(clean)
            deduped.append(clean)

        return deduped

    def _download_portrait(self, url: str, key: str) -> Optional[Path]:
        logger.info("Fetching portrait for %s from %s", key, url)
        try:
            headers = {
                "User-Agent": "StreetBattle/1.0 (portrait-loader)",
                "Accept": "image/png,image/jpeg;q=0.9,*/*;q=0.8",
            }
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Portrait download failed for %s: %s", key, exc)
            return None

        extension = self._guess_extension(url, response.headers.get('Content-Type'))
        filename = self._make_filename(key, extension, response.content)
        destination = self.cache_dir / filename
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                return destination
            with destination.open('wb') as fh:
                fh.write(response.content)
        except Exception as exc:
            logger.warning("Failed to persist portrait %s: %s", destination, exc)
            return None
        return destination

    def _load_texture(self, path: Path) -> Optional[Texture]:
        if not path.exists():
            return None
        try:
            # 改进路径处理：使用绝对路径并确保跨平台兼容性
            absolute_path = path.resolve()
            panda_path = Filename.fromOsSpecific(str(absolute_path))
            panda_path.makeCanonical()
            
            # 添加调试信息以帮助诊断路径问题
            logger.debug("Loading texture from path: %s (absolute: %s)", path, absolute_path)
            
            tex = self.loader.loadTexture(panda_path)
            if tex:
                tex.setMinfilter(Texture.FTLinearMipmapLinear)
                tex.setMagfilter(Texture.FTLinear)
            return tex
        except Exception as exc:
            logger.warning("Failed to load portrait texture %s: %s", path, exc)
            return None

    @staticmethod
    def _guess_extension(url: str, content_type: Optional[str]) -> str:
        if content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
            if ext in PortraitManager.SUPPORTED_EXTENSIONS:
                return ext
        parsed = os.path.splitext(url.split('?')[0])[1].lower()
        if parsed in PortraitManager.SUPPORTED_EXTENSIONS:
            return parsed
        return '.png'

    @staticmethod
    def _make_filename(key: str, extension: str, payload: bytes) -> str:
        digest = hashlib.sha1(payload).hexdigest()[:10]
        safe_key = key.replace('/', '_')
        return f"{safe_key}_{digest}{extension}"