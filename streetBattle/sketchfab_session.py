"""Lightweight Sketchfab API session manager used by StreetBattle.

The original tooling expected a private helper that handled authenticated
Sketchfab downloads.  This implementation focuses on the features that
StreetBattle actually relies on:

* discovering an API token from environment variables or local credentials
* validating the token (optionally probing a model UID)
* downloading GLTF/GLB archives using the official Sketchfab REST endpoints
* providing clear diagnostics when authentication fails so the runtime can
  gracefully fall back to procedural placeholders

The implementation avoids hard failures – missing credentials simply mean that
premium assets cannot be downloaded, but the game keeps running.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Sequence
from urllib.parse import urlparse

import requests

__all__ = ["SketchfabSessionManager", "SketchfabAuthError", "SketchfabDownloadError"]

logger = logging.getLogger("streetbattle.sketchfab")


class SketchfabAuthError(RuntimeError):
    """Raised when a Sketchfab authentication workflow fails."""


class SketchfabDownloadError(RuntimeError):
    """Raised when downloading a Sketchfab resource fails."""


@dataclass
class _DownloadCandidate:
    format: str
    url: str
    filename: Optional[str]


class SketchfabSessionManager:
    """Minimal session manager for the Sketchfab REST API.

    Parameters
    ----------
    project_root:
        Path to the repository root – used to discover credential files and to
        persist refreshed access tokens when needed.
    session:
        Optional requests session for dependency injection/testing.
    """

    def __init__(self, project_root: Path | str, session: Optional[requests.Session] = None) -> None:
        self.project_root = Path(project_root)
        self.assets_dir = self.project_root / "gamecenter" / "streetBattle" / "assets"
        self._session = session or requests.Session()
        self._token = self._load_token()
        self._ensure_requests_headers()

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------
    def ensure_authenticated(self, test_uid: Optional[str] = None) -> bool:
        """Return ``True`` when an API token is available and looks valid.

        If ``test_uid`` is provided we perform a cheap HEAD probe to confirm the
        token can access the download endpoint.  Any network failure is treated
        as a soft warning – the game will still fall back to placeholders.
        """

        if not self._token:
            logger.warning("Sketchfab token is not configured. Premium assets will be skipped.")
            return False

        if not test_uid:
            return True

        probe_url = f"https://api.sketchfab.com/v3/models/{test_uid}"
        try:
            response = self._session.head(probe_url, timeout=10)
            if response.status_code == 401:
                logger.error("Sketchfab authentication failed (401). Check API token.")
                return False
            if response.status_code == 404:
                # UID might not exist, but token still valid.
                return True
            return response.ok
        except requests.RequestException as exc:
            logger.warning("Sketchfab auth probe failed: %s", exc)
            # Treat transient network issues as non-fatal.
            return True

    def download_model(self, model_uid: str, output_dir: Path | str, preferred_formats: Sequence[str]) -> Path:
        """Download the model archive for ``model_uid``.

        Parameters
        ----------
        model_uid:
            Sketchfab model UID.
        output_dir:
            Directory where the downloaded archive should be stored.
        preferred_formats:
            Priority-ordered list of formats to try (e.g. ("gltf", "glb")).

        Returns
        -------
        pathlib.Path
            Path to the downloaded archive or GLTF/GLB file.
        """

        if not self.ensure_authenticated(test_uid=model_uid):
            raise SketchfabAuthError("Sketchfab token unavailable or invalid – cannot download model")

        payload = self._fetch_download_manifest(model_uid)
        candidates = self._extract_candidates(payload, preferred_formats)
        if not candidates:
            raise SketchfabDownloadError(f"No downloadable formats available for model {model_uid}")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for candidate in candidates:
            try:
                return self._stream_candidate(candidate, output_dir, model_uid)
            except requests.RequestException as exc:
                logger.error("Failed to download %s for %s: %s", candidate.format, model_uid, exc)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Unexpected failure downloading %s for %s: %s", candidate.format, model_uid, exc)

        raise SketchfabDownloadError(f"Unable to download model {model_uid} in any preferred format")

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _load_token(self) -> Optional[str]:
        """Discover an API token from environment variables or credential files."""

        env_token = os.getenv("SKETCHFAB_API_TOKEN") or os.getenv("SKETCHFAB_TOKEN")
        if env_token:
            return env_token.strip()

        cred_paths = [
            self.assets_dir / "sketchfab_credentials.json",
            self.project_root / "sketchfab_credentials.json",
        ]
        for path in cred_paths:
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - log and continue
                logger.warning("Failed to parse %s: %s", path, exc)
                continue
            token = data.get("token") or data.get("api_token")
            if token:
                return str(token).strip()

        return None

    def _ensure_requests_headers(self) -> None:
        if self._token:
            self._session.headers.update({
                "Authorization": f"Token {self._token}",
                "User-Agent": "StreetBattle/1.0 (+https://github.com/kn1ghtc/gamecenter)",
            })

    def _fetch_download_manifest(self, model_uid: str) -> Dict[str, Dict[str, str]]:
        url = f"https://api.sketchfab.com/v3/models/{model_uid}/download"
        try:
            response = self._session.get(url, timeout=30)
        except requests.RequestException as exc:
            raise SketchfabDownloadError(f"Sketchfab download manifest request failed: {exc}") from exc

        if response.status_code == 401:
            raise SketchfabAuthError("Sketchfab rejected the API token (401 Unauthorized)")
        if response.status_code == 404:
            raise SketchfabDownloadError(f"Sketchfab model {model_uid} not found (404)")
        if not response.ok:
            raise SketchfabDownloadError(f"Failed to fetch download manifest: HTTP {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - unexpected response
            raise SketchfabDownloadError("Sketchfab returned invalid JSON") from exc

    def _extract_candidates(self, manifest: Dict[str, Dict[str, str]], preferred_formats: Sequence[str]) -> Sequence[_DownloadCandidate]:
        candidates: list[_DownloadCandidate] = []
        for fmt in preferred_formats:
            entry = manifest.get(fmt)
            if not entry:
                continue
            url = entry.get("url")
            if not url:
                continue
            filename = entry.get("filename") or entry.get("name")
            candidates.append(_DownloadCandidate(format=fmt, url=url, filename=filename))
        # Fallback: manifest may include "archives" dict keyed by format
        archives = manifest.get("archives") or {}
        for fmt in preferred_formats:
            entry = archives.get(fmt)
            if not entry or not entry.get("url"):
                continue
            filename = entry.get("filename") or f"{fmt}.zip"
            candidates.append(_DownloadCandidate(format=fmt, url=entry["url"], filename=filename))
        return candidates

    def _stream_candidate(self, candidate: _DownloadCandidate, output_dir: Path, model_uid: str) -> Path:
        logger.info("Downloading Sketchfab asset %s (%s)", model_uid, candidate.format)
        with self._session.get(candidate.url, timeout=180, stream=True) as response:
            response.raise_for_status()
            filename = candidate.filename or self._build_filename(candidate, model_uid)
            destination = output_dir / filename
            with destination.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
        return destination

    @staticmethod
    def _build_filename(candidate: _DownloadCandidate, model_uid: str) -> str:
        parsed = urlparse(candidate.url)
        name = Path(parsed.path).name
        if name:
            return name
        suffix = candidate.format.lower()
        if suffix not in {"gltf", "glb", "zip"}:
            suffix = "bin"
        return f"{model_uid}.{suffix}"
