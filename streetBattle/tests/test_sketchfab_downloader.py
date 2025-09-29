from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, List

import pytest

from gamecenter.streetBattle.sketchfab_tools.cookie_session import (
    CookieRefreshResult,
    SketchfabAuthError,
    SketchfabCookieError,
    SketchfabCookieSession,
    SketchfabRateLimitError,
)
from gamecenter.streetBattle.sketchfab_tools.downloader import SketchfabSequentialDownloader
class DummyCookieSession:
    def __init__(
        self,
        manifest_queue: List[Any],
        download_queue: List[bytes],
        *,
        refresh_result: CookieRefreshResult | None = None,
    ) -> None:
        self.manifest_queue = manifest_queue
        self.download_queue = download_queue
        self.refresh_calls = 0
        self.refresh_result = refresh_result or CookieRefreshResult(refreshed=True, attempts=1, wait_seconds=0.1)
        self.logged_in = False

    def ensure_logged_in(self, force: bool = False):
        self.logged_in = True
        return True

    def get_presigned_url(self, uid: str, *, archive_type: str = "gltf") -> str:
        if not self.manifest_queue:
            raise AssertionError("No more manifest results queued")
        result = self.manifest_queue.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def download_file(self, url: str, target_path: Path) -> Path:
        if not self.download_queue:
            raise AssertionError("No more downloads queued")
        payload = self.download_queue.pop(0)
        target_path.write_bytes(payload)
        return target_path

    def wait_for_refresh(self, *, timeout: float = 300.0, poll_interval: float = 5.0):
        self.refresh_calls += 1
        return self.refresh_result


def write_cookie_file(path: Path, value: str) -> None:
    payload = [{"name": "sessionid", "value": value, "domain": ".sketchfab.com", "path": "/"}]
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_cookie_session_loads_and_reloads(tmp_path: Path) -> None:
    cookie_path = tmp_path / "cookies.json"
    write_cookie_file(cookie_path, "alpha")
    session = SketchfabCookieSession(cookie_path, auto_reload=False)
    assert session.prepare().cookies.get("sessionid") == "alpha"

    # Rewrite cookie file and trigger reload
    write_cookie_file(cookie_path, "beta")
    session.reload()
    assert session.prepare().cookies.get("sessionid") == "beta"


def test_cookie_session_wait_for_refresh(tmp_path: Path) -> None:
    cookie_path = tmp_path / "cookies.json"
    write_cookie_file(cookie_path, "alpha")
    session = SketchfabCookieSession(cookie_path, auto_reload=False)

    def updater():
        time.sleep(0.2)
        write_cookie_file(cookie_path, "beta")

    thread = threading.Thread(target=updater)
    thread.start()
    result = session.wait_for_refresh(timeout=2.0, poll_interval=0.05)
    thread.join()

    assert result.refreshed is True
    assert session.prepare().cookies.get("sessionid") == "beta"


def test_sequential_downloader_happy_path(tmp_path: Path) -> None:
    catalog_path = tmp_path / "resource_catalog.json"
    catalog_path.write_text(
        json.dumps({"kyo_kusanagi": {"sketchfab": {"uid": "demo123"}}}),
        encoding="utf-8",
    )
    download_root = tmp_path / "downloads"
    presigned_path = tmp_path / "presigned_urls.json"

    manifest_url = "https://example.com/kyo.zip"
    archive_content = b"demo"

    cookie_session = DummyCookieSession([manifest_url], [archive_content])

    downloader = SketchfabSequentialDownloader(
        catalog_path=catalog_path,
        download_root=download_root,
        cookie_session=cookie_session,  # type: ignore[arg-type]
        presigned_map_path=presigned_path,
        rate_limit_seconds=0.1,
    )

    summaries = downloader.run(update_presigned=True)
    assert len(summaries) == 1
    assert summaries[0].character_id == "kyo_kusanagi"
    assert (download_root / "kyo_kusanagi.zip").exists()
    presigned_map = json.loads(presigned_path.read_text(encoding="utf-8"))
    assert presigned_map["kyo_kusanagi"] == manifest_url


def test_sequential_downloader_handles_403(tmp_path: Path) -> None:
    catalog_path = tmp_path / "resource_catalog.json"
    catalog_path.write_text(
        json.dumps({"iori_yagami": {"sketchfab": {"uid": "demo456"}}}),
        encoding="utf-8",
    )
    download_root = tmp_path / "downloads"

    manifest_url = "https://example.com/iori.zip"
    cookie_session = DummyCookieSession(
        [
            SketchfabAuthError("expired"),
            manifest_url,
        ],
        [b"demo"],
    )

    downloader = SketchfabSequentialDownloader(
        catalog_path=catalog_path,
        download_root=download_root,
        cookie_session=cookie_session,  # type: ignore[arg-type]
        rate_limit_seconds=0.1,
    )

    summaries = downloader.run(update_presigned=False)
    assert len(summaries) == 1
    assert cookie_session.refresh_calls == 1


def test_sequential_downloader_handles_rate_limit(tmp_path: Path) -> None:
    catalog_path = tmp_path / "resource_catalog.json"
    catalog_path.write_text(
        json.dumps({"athena": {"sketchfab": {"uid": "demo789"}}}),
        encoding="utf-8",
    )
    download_root = tmp_path / "downloads"

    manifest_url = "https://example.com/athena.zip"
    cookie_session = DummyCookieSession(
        [
            SketchfabRateLimitError("busy", retry_after=0.01),
            manifest_url,
        ],
        [b"athena"],
    )

    downloader = SketchfabSequentialDownloader(
        catalog_path=catalog_path,
        download_root=download_root,
        cookie_session=cookie_session,  # type: ignore[arg-type]
        rate_limit_seconds=0.01,
    )

    summaries = downloader.run(update_presigned=False)
    assert len(summaries) == 1


def test_cookie_session_requires_entries(tmp_path: Path) -> None:
    cookie_path = tmp_path / "cookies.json"
    cookie_path.write_text("[]", encoding="utf-8")
    with pytest.raises(SketchfabCookieError):
        SketchfabCookieSession(cookie_path)
