"""Sketchfab session handling using credential-based login or stored cookies."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from requests.cookies import RequestsCookieJar

__all__ = [
    "SketchfabCookieSession",
    "SketchfabCookieError",
    "SketchfabAuthError",
    "SketchfabRateLimitError",
    "CookieRefreshResult",
]

logger = logging.getLogger("streetbattle.sketchfab.cookies")


class SketchfabCookieError(RuntimeError):
    """Raised when Sketchfab authentication or cookie handling fails."""


class SketchfabAuthError(SketchfabCookieError):
    """Raised when the Sketchfab session is no longer authenticated."""


class SketchfabRateLimitError(SketchfabCookieError):
    """Raised when Sketchfab signals rate limiting (HTTP 429)."""

    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class CookieRefreshResult:
    """Result metadata for cookie refresh attempts."""

    refreshed: bool
    attempts: int
    wait_seconds: float


class SketchfabCookieSession:
    """Manage a Sketchfab session using stored cookies or credential-based login."""

    LOGIN_URL = "https://sketchfab.com/login"
    DOWNLOAD_ENDPOINTS = (
        "https://sketchfab.com/i/archives/latest?archiveType={archive}&model={uid}",
        "https://sketchfab.com/i/archives/download?archiveType={archive}&model={uid}",
    )

    def __init__(
        self,
        cookie_path: Optional[Path | str] = None,
        *,
        session: Optional[requests.Session] = None,
        auto_reload: bool = True,
        email: Optional[str] = None,
        password: Optional[str] = None,
        env_path: Optional[Path | str] = None,
        rate_limit_seconds: float = 4.5,
    ) -> None:
        self.cookie_path = Path(cookie_path) if cookie_path else None
        self.auto_reload = auto_reload
        self._last_mtime: Optional[float] = None
        self._rate_limit_seconds = max(rate_limit_seconds, 1.0)
        self._last_request_ts = 0.0
        self._logged_in = False
        self._env_loaded = False

        self.session = session or requests.Session()
        self._ensure_headers()

        self.env_path = Path(env_path) if env_path else Path(__file__).resolve().parents[1] / ".env.local"
        self.email = self._clean_env_value(email)
        self.password = self._clean_env_value(password)

        if self.cookie_path:
            self.reload()
            self._logged_in = True
        else:
            self._load_env()
            if not self.email:
                self.email = self._clean_env_value(os.getenv("SKETCHFAB_EMAIL") or os.getenv("SKETCHFAB_email"))
            if not self.password:
                self.password = self._clean_env_value(os.getenv("SKETCHFAB_PASSWORD") or os.getenv("SKETCHFAB_password"))
            if not self.email or not self.password:
                raise SketchfabCookieError(
                    "Sketchfab credentials are required. Ensure SKETCHFAB_EMAIL and SKETCHFAB_PASSWORD are set."
                )
            self.ensure_logged_in(force=True)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def prepare(self) -> requests.Session:
        """Return an authenticated :class:`requests.Session`."""

        if self.cookie_path and self.auto_reload:
            self._reload_if_stale()
        else:
            self.ensure_logged_in()
        return self.session

    def ensure_logged_in(self, *, force: bool = False) -> bool:
        """Ensure the Sketchfab session is authenticated."""

        if self.cookie_path:
            if force:
                self.reload()
            return True

        if self._logged_in and not force:
            return True

        self._perform_login()
        self._logged_in = True
        return True

    def reload(self) -> None:
        """Load cookies from ``self.cookie_path`` into the session."""

        if not self.cookie_path or not self.cookie_path.exists():
            raise SketchfabCookieError(f"Cookie file not found: {self.cookie_path}")

        try:
            data = json.loads(self.cookie_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive logging
            raise SketchfabCookieError(f"Failed to read cookie file: {exc}") from exc

        jar = RequestsCookieJar()
        cookie_iterable: Iterable[dict]
        if isinstance(data, dict):
            cookie_iterable = data.get("cookies", [])
        else:
            cookie_iterable = data

        loaded = 0
        for item in cookie_iterable:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            value = item.get("value")
            if not name or value is None:
                continue
            domain = item.get("domain")
            path = item.get("path", "/")
            jar.set(name, value, domain=domain, path=path)
            loaded += 1

        if loaded == 0:
            raise SketchfabCookieError("Cookie file did not contain any usable entries")

        self.session.cookies.clear()  # type: ignore[call-arg]
        self.session.cookies.update(jar)  # type: ignore[attr-defined]
        self._last_mtime = self._current_mtime()
        logger.info("Loaded %d Sketchfab cookies from %s", loaded, self.cookie_path)

    def wait_for_refresh(self, *, timeout: float = 300.0, poll_interval: float = 5.0) -> CookieRefreshResult:
        """Attempt to refresh authentication state."""

        start = time.monotonic()
        attempts = 0

        if self.cookie_path:
            baseline_mtime = self._last_mtime or self._current_mtime()
            while time.monotonic() - start < timeout:
                attempts += 1
                current_mtime = self._current_mtime()
                if current_mtime and baseline_mtime and current_mtime > baseline_mtime:
                    self.reload()
                    elapsed = time.monotonic() - start
                    return CookieRefreshResult(refreshed=True, attempts=attempts, wait_seconds=elapsed)
                time.sleep(poll_interval)
            elapsed = time.monotonic() - start
            return CookieRefreshResult(refreshed=False, attempts=attempts, wait_seconds=elapsed)

        # Credential-based session: attempt to re-login until success or timeout
        while time.monotonic() - start < timeout:
            attempts += 1
            try:
                self.ensure_logged_in(force=True)
                elapsed = time.monotonic() - start
                return CookieRefreshResult(refreshed=True, attempts=attempts, wait_seconds=elapsed)
            except SketchfabCookieError as exc:
                logger.warning("Retrying Sketchfab login: %s", exc)
                time.sleep(poll_interval)
        elapsed = time.monotonic() - start
        return CookieRefreshResult(refreshed=False, attempts=attempts, wait_seconds=elapsed)

    def get_presigned_url(self, model_uid: str, *, archive_type: str = "gltf") -> Optional[str]:
        """Return a presigned S3 URL for the given model UID."""

        self.ensure_logged_in()
        headers = {
            "Referer": "https://sketchfab.com/",
            "Accept": "application/json, text/javascript, */*;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
        }

        for endpoint in self.DOWNLOAD_ENDPOINTS:
            url = endpoint.format(archive=archive_type, uid=model_uid)
            response = self._get_with_rate_limit(url, headers=headers, allow_redirects=False)

            if response.status_code in (401, 403):
                self._logged_in = False
                raise SketchfabAuthError(f"Sketchfab rejected credentials with HTTP {response.status_code}")

            if response.status_code == 429:
                retry_after = self._parse_retry_after(response.headers)
                raise SketchfabRateLimitError("Sketchfab rate limit encountered", retry_after)

            if response.status_code in (302, 303):
                location = response.headers.get("Location")
                if location:
                    return location

            if response.ok:
                download_url = self._extract_download_url(response)
                if download_url:
                    return download_url

        return None

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _perform_login(self) -> None:
        self._load_env()
        if not self.email or not self.password:
            raise SketchfabCookieError("Sketchfab credentials missing; cannot login")

        self.session.cookies.clear()  # reset previous attempts
        self._ensure_headers()

        try:
            page = self.session.get(self.LOGIN_URL, timeout=30)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise SketchfabCookieError(f"Failed to reach Sketchfab login page: {exc}") from exc

        if page.status_code != 200:
            raise SketchfabCookieError(f"Sketchfab login page returned HTTP {page.status_code}")

        csrf_token = self._extract_csrf(page.text) or self.session.cookies.get("csrftoken")
        if not csrf_token:
            raise SketchfabCookieError("Unable to locate Sketchfab CSRF token")

        payload = {
            "csrfmiddlewaretoken": csrf_token,
            "email": self.email,
            "password": self.password,
            "remember": "on",
        }
        headers = {
            "Referer": self.LOGIN_URL,
            "Origin": "https://sketchfab.com",
            "User-Agent": self.session.headers["User-Agent"],
        }

        try:
            response = self.session.post(
                self.LOGIN_URL,
                data=payload,
                headers=headers,
                timeout=30,
                allow_redirects=False,
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise SketchfabCookieError(f"Sketchfab login request failed: {exc}") from exc

        if response.status_code not in (302, 303):
            if response.status_code >= 500:
                raise SketchfabCookieError(f"Sketchfab login service error: HTTP {response.status_code}")
            raise SketchfabCookieError("Sketchfab login rejected credentials")

        self._logged_in = True
        logger.info("Authenticated with Sketchfab as %s", self.email)

    def _get_with_rate_limit(self, url: str, *, headers: Optional[dict[str, str]] = None, **kwargs) -> requests.Response:
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        if elapsed < self._rate_limit_seconds:
            time.sleep(self._rate_limit_seconds - elapsed)
        self._last_request_ts = time.monotonic()

        try:
            return self.session.get(url, headers=headers, timeout=45, **kwargs)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise SketchfabCookieError(f"Sketchfab request failed: {exc}") from exc

    def download_file(self, download_url: str, target_path: Path) -> Path:
        """Download the file at ``download_url`` to ``target_path``."""

        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.session.get(download_url, timeout=300, stream=True) as response:
                if response.status_code == 429:
                    retry_after = self._parse_retry_after(response.headers)
                    raise SketchfabRateLimitError("Rate limited while downloading archive", retry_after)
                response.raise_for_status()
                with target_path.open("wb") as fh:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            fh.write(chunk)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise SketchfabCookieError(f"Downloading Sketchfab archive failed: {exc}") from exc
        return target_path

    def _ensure_headers(self) -> None:
        self.session.headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) StreetBattle/1.0",
        )
        self.session.headers.setdefault("Accept", "application/json, */*;q=0.8")
        self.session.headers.setdefault("Connection", "keep-alive")

    def _reload_if_stale(self) -> None:
        current = self._current_mtime()
        if current and self._last_mtime and current <= self._last_mtime:
            return
        if current and (self._last_mtime is None or current > self._last_mtime):
            logger.info("Cookie file changed on disk; reloading")
            self.reload()

    def _current_mtime(self) -> Optional[float]:
        if not self.cookie_path:
            return None
        try:
            return self.cookie_path.stat().st_mtime
        except FileNotFoundError:
            return None

    def _load_env(self) -> None:
        if self._env_loaded:
            return
        try:
            load_dotenv(dotenv_path=self.env_path, override=False)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to load .env file %s: %s", self.env_path, exc)
        self._env_loaded = True

    @staticmethod
    def _clean_env_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(('"', "'")) and len(value) >= 2:
            value = value[1:-1]
        return value.strip()

    @staticmethod
    def _extract_csrf(html: str) -> Optional[str]:
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
        return match.group(1) if match else None

    def _extract_download_url(self, response: requests.Response) -> Optional[str]:
        content_type = response.headers.get("Content-Type", "")
        text = response.text
        data = None
        if "json" in content_type.lower() or (text and text.strip().startswith("{")):
            try:
                data = response.json()
            except ValueError:
                data = None

        if isinstance(data, dict):
            for key in ("url", "downloadUrl", "href"):
                if key in data and isinstance(data[key], str):
                    return data[key]
            for bucket in ("gltf", "glb", "archives"):
                entry = data.get(bucket)
                if isinstance(entry, dict):
                    for key in ("url", "downloadUrl", "href"):
                        if key in entry and isinstance(entry[key], str):
                            return entry[key]
            # archives may be nested (archives -> gltf -> url)
            archives = data.get("archives")
            if isinstance(archives, dict):
                for fmt_entry in archives.values():
                    if isinstance(fmt_entry, dict):
                        for key in ("url", "downloadUrl", "href"):
                            value = fmt_entry.get(key)
                            if isinstance(value, str):
                                return value

        # Fallback: look for a URL in the body
        match = re.search(r'https://[^"]+amazonaws.com[^"]+', text)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def _parse_retry_after(headers: dict[str, str]) -> float:
        retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return 30.0

    @staticmethod
    def derive_filename(url: str, *, fallback: str) -> str:
        parsed = urlparse(url)
        name = Path(parsed.path).name
        return name or fallback
