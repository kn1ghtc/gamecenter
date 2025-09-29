"""Sequential Sketchfab downloader using credential/cookie authentication."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .cookie_session import (
    SketchfabAuthError,
    SketchfabCookieError,
    SketchfabCookieSession,
    SketchfabRateLimitError,
)

__all__ = [
    "SketchfabSequentialDownloader",
    "SketchfabDownloadSummary",
]

logger = logging.getLogger("streetbattle.sketchfab.downloader")

DEFAULT_RATE_LIMIT_SECONDS = 4.5
DEFAULT_RETRY_AFTER = 30.0


@dataclass
class SketchfabDownloadSummary:
    """Metadata describing a successful download operation."""

    character_id: str
    model_uid: str
    archive_path: Path
    gltf_url: str
    status_code: int


class SketchfabSequentialDownloader:
    """Coordinate sequential Sketchfab downloads based on the resource catalog."""

    def __init__(
        self,
        *,
        catalog_path: Path | str,
        download_root: Path | str,
        cookie_session: SketchfabCookieSession,
        presigned_map_path: Optional[Path | str] = None,
        rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
        cookie_refresh_timeout: float = 600.0,
    ) -> None:
        self.catalog_path = Path(catalog_path)
        self.download_root = Path(download_root)
        self.cookie_session = cookie_session
        self.rate_limit_seconds = max(rate_limit_seconds, 1.0)
        self.cookie_refresh_timeout = cookie_refresh_timeout
        self.presigned_map_path = (
            Path(presigned_map_path) if presigned_map_path else self.catalog_path.parent / "presigned_urls.json"
        )

        self.download_root.mkdir(parents=True, exist_ok=True)
        self.catalog = self._load_catalog()
        self.presigned_map = self._load_presigned_map()
        self.cookie_session.ensure_logged_in()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def run(
        self,
        characters: Optional[Iterable[str]] = None,
        *,
        keep_archives: bool = True,
        update_presigned: bool = True,
    ) -> List[SketchfabDownloadSummary]:
        """Download GLTF archives sequentially for ``characters``.

        When ``characters`` is ``None`` every entry in the catalog is processed.
    The downloader respects rate limits and handles authentication refresh
    and retry logic for Sketchfab throttling.
        """

        targets = self._resolve_characters(characters)
        logger.info("Starting sequential Sketchfab download for %d characters", len(targets))
        summaries: List[SketchfabDownloadSummary] = []

        for index, char_id in enumerate(targets, start=1):
            info = self.catalog.get(char_id, {})
            model_uid = (info.get("sketchfab") or {}).get("uid")
            if not model_uid:
                logger.warning("Skipping %s – no sketchfab.uid in catalog", char_id)
                continue

            logger.info("[%d/%d] Fetching manifest for %s (%s)", index, len(targets), char_id, model_uid)
            summary = self._download_single(char_id, model_uid, keep_archives=keep_archives)
            if summary:
                summaries.append(summary)
                if update_presigned:
                    self._update_presigned_map(char_id, summary.gltf_url)

        if update_presigned:
            self._save_presigned_map()

        logger.info("Completed sequential download – %d success, %d skipped", len(summaries), len(targets) - len(summaries))
        return summaries

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _download_single(
        self,
        char_id: str,
        model_uid: str,
        *,
        keep_archives: bool,
        max_attempts: int = 5,
    ) -> Optional[SketchfabDownloadSummary]:
        attempts = 0
        backoff = self.rate_limit_seconds
        while attempts < max_attempts:
            attempts += 1
            try:
                gltf_url = self.cookie_session.get_presigned_url(model_uid)
            except SketchfabRateLimitError as exc:
                retry_after = exc.retry_after or backoff
                logger.warning("Rate limited fetching manifest for %s – sleeping %.1f seconds", model_uid, retry_after)
                self._delay(retry_after)
                backoff = min(backoff * 1.5, 120)
                continue
            except SketchfabAuthError:
                logger.warning("Authentication expired for %s – waiting for refresh", model_uid)
                refresh = self.cookie_session.wait_for_refresh(timeout=self.cookie_refresh_timeout)
                if not refresh.refreshed:
                    logger.error("Authentication refresh timed out – aborting %s", char_id)
                    return None
                backoff = min(backoff * 1.2, 60)
                continue
            except SketchfabCookieError as exc:
                logger.error("Failed to get manifest for %s: %s", model_uid, exc)
                self._delay(backoff)
                backoff = min(backoff * 1.5, 120)
                continue

            if not gltf_url:
                logger.error("Manifest for %s did not provide a GLTF archive", model_uid)
                return None

            archive_path = self._download_archive(char_id, model_uid, gltf_url, keep_archives=keep_archives)
            if archive_path is None:
                self._delay(backoff)
                backoff = min(backoff * 1.5, 60)
                continue

            logger.info("Downloaded %s -> %s", char_id, archive_path)
            return SketchfabDownloadSummary(
                character_id=char_id,
                model_uid=model_uid,
                archive_path=archive_path,
                gltf_url=gltf_url,
                status_code=200,
            )

        logger.error("Reached maximum retries for %s", char_id)
        return None

    def _download_archive(
        self,
        char_id: str,
        model_uid: str,
        url: str,
        *,
        keep_archives: bool,
    ) -> Optional[Path]:
        filename = f"{char_id}.zip"
        target_path = self.download_root / filename
        temp_path = target_path.with_suffix(".tmp")

        try:
            self.cookie_session.download_file(url, temp_path)
        except SketchfabRateLimitError as exc:
            retry_after = exc.retry_after or DEFAULT_RETRY_AFTER
            logger.warning("Rate limited while downloading %s – sleeping %.1f seconds", model_uid, retry_after)
            self._delay(retry_after)
            temp_path.unlink(missing_ok=True)
            return None
        except SketchfabCookieError as exc:
            logger.error("Failed to download archive for %s: %s", char_id, exc)
            temp_path.unlink(missing_ok=True)
            return None

        temp_path.replace(target_path)
        if not keep_archives:
            try:
                target_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to remove archive for %s after extraction", char_id)
                return target_path
        return target_path

    def _resolve_characters(self, subset: Optional[Iterable[str]]) -> List[str]:
        if not subset:
            return sorted(self.catalog.keys())
        result: List[str] = []
        for char in subset:
            char_id = char.strip()
            if not char_id:
                continue
            if char_id not in self.catalog:
                logger.warning("Character %s not in catalog", char_id)
                continue
            result.append(char_id)
        return sorted(result)

    def _load_catalog(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        try:
            data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive logging
            raise RuntimeError(f"Failed to read resource catalog: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("resource_catalog.json must be a JSON object")
        return data

    def _load_presigned_map(self) -> Dict[str, str]:
        if not self.presigned_map_path.exists():
            return {}
        try:
            data = json.loads(self.presigned_map_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to parse presigned URLs map: %s", exc)
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _update_presigned_map(self, key: str, url: str) -> None:
        self.presigned_map[key] = url

    def _save_presigned_map(self) -> None:
        try:
            payload = json.dumps(self.presigned_map, indent=2, ensure_ascii=False, sort_keys=True)
            self.presigned_map_path.write_text(payload, encoding="utf-8")
            logger.info("Updated %s with %d entries", self.presigned_map_path, len(self.presigned_map))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to write presigned URL map: %s", exc)

    @staticmethod
    def _delay(seconds: float) -> None:
        if seconds <= 0:
            return
        import time

        time.sleep(seconds)


def main() -> None:  # pragma: no cover - CLI utility
    import argparse

    parser = argparse.ArgumentParser(description="Sequential Sketchfab downloader")
    parser.add_argument("--catalog", default=Path(__file__).parents[1] / "assets" / "resource_catalog.json")
    parser.add_argument("--download-root", default=Path(__file__).parents[1] / "assets" / "downloads")
    parser.add_argument("--cookies", default=None, help="Optional path to exported cookies JSON")
    parser.add_argument("--env", default=Path(__file__).parents[1] / ".env.local", help="Path to .env.local file")
    parser.add_argument("--email", help="Sketchfab login email (overrides .env)")
    parser.add_argument("--password", help="Sketchfab login password (overrides .env)")
    parser.add_argument("--characters", nargs="*", help="Optional list of character IDs to download")
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE_LIMIT_SECONDS, help="Delay between manifest requests")
    parser.add_argument("--keep-archives", action="store_true", help="Keep downloaded ZIP archives on disk")
    parser.add_argument("--no-update-presigned", action="store_true", help="Skip updating presigned_urls.json")
    args = parser.parse_args()

    cookie_kwargs = {
        "cookie_path": args.cookies,
        "env_path": args.env,
        "email": args.email,
        "password": args.password,
        "rate_limit_seconds": args.rate,
    }

    try:
        cookie_session = SketchfabCookieSession(**cookie_kwargs)
    except SketchfabCookieError as exc:
        parser.error(str(exc))
        return

    downloader = SketchfabSequentialDownloader(
        catalog_path=args.catalog,
        download_root=args.download_root,
        cookie_session=cookie_session,
        rate_limit_seconds=args.rate,
    )

    downloader.run(
        characters=args.characters,
        keep_archives=args.keep_archives,
        update_presigned=not args.no_update_presigned,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
