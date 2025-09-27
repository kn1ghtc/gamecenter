from __future__ import annotations

"""Configuration management for StreetBattle.

This module provides a simple yet extensible configuration system with a JSON
backing store that lives inside the repository (``config/settings.json``).  The
configuration can be tweaked from the launcher UI or edited manually with any
text editor.  Nested keys use dotted accessors (e.g. ``graphics.resolution``).
"""

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping, Optional

_SETTINGS_FILE = "settings.json"

_DEFAULT_SETTINGS: Dict[str, Any] = {
    "preferred_version": "3d",  # either "3d" (Panda3D) or "2.5d" (pygame)
    "remember_last_version": True,
    "graphics": {
        "resolution": [1024, 768],
        "fullscreen": False,
        "vsync": True,
    },
    "audio": {
        "music_volume": 0.75,
        "effects_volume": 0.8,
        "muted": False,
    },
    "gameplay": {
        "difficulty": "normal",
        "rounds_to_win": 2,
        "player_character": "kyo_kusanagi",
        "cpu_character": "iori_yagami",
    },
    "controls": {
        "keyboard": {
            "left": "a",
            "right": "d",
            "up": "w",
            "down": "s",
            "attack": "j",
            "special": "k",
            "jump": "space",
        }
    },
}


def _deep_merge(target: MutableMapping[str, Any], incoming: MutableMapping[str, Any]) -> None:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def _resolve_dotted(mapping: MutableMapping[str, Any], dotted: Iterable[str]) -> MutableMapping[str, Any]:
    current = mapping
    for segment in dotted:
        if segment not in current or not isinstance(current[segment], dict):
            current[segment] = {}
        current = current[segment]
    return current


@dataclass
class Settings:
    """Wrapper around the underlying settings dictionary."""

    data: Dict[str, Any]
    path: Path

    def get(self, key: str, default: Any | None = None) -> Any:
        if not key:
            return self.data
        segments = key.split(".")
        current: Any = self.data
        for segment in segments:
            if not isinstance(current, dict) or segment not in current:
                return default
            current = current[segment]
        return current

    def set(self, key: str, value: Any) -> None:
        segments = key.split(".")
        if not segments:
            raise ValueError("Key must not be empty")
        *parents, last = segments
        target = self.data
        if parents:
            target = _resolve_dotted(target, parents)
        target[last] = value

    def to_dict(self) -> Dict[str, Any]:
        return deepcopy(self.data)


class SettingsManager:
    """Load/save helper for the StreetBattle configuration."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        if project_root is None:
            project_root = Path(__file__).resolve().parents[1]
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.config_dir / _SETTINGS_FILE
        self._settings = Settings(deepcopy(_DEFAULT_SETTINGS), self.path)
        self._load_from_disk()

    @property
    def settings(self) -> Settings:
        return self._settings

    def _load_from_disk(self) -> None:
        if not self.path.exists():
            self.save()  # persist defaults for manual editing
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            if isinstance(payload, dict):
                merged = deepcopy(_DEFAULT_SETTINGS)
                _deep_merge(merged, payload)
                self._settings = Settings(merged, self.path)
        except Exception as exc:
            backup_path = self.path.with_suffix(".invalid.json")
            backup_path.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
            raise RuntimeError(
                f"Failed to parse configuration file {self.path}. A copy was written to {backup_path}."
            ) from exc

    def save(self) -> None:
        payload = self._settings.to_dict()
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=4, ensure_ascii=False, sort_keys=True)

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        self._settings.set(key, value)
        if persist:
            self.save()

    def toggle(self, key: str, persist: bool = True) -> Any:
        current = bool(self.get(key, False))
        self.set(key, not current, persist=persist)
        return not current

    def refresh(self) -> None:
        """Reload configuration from disk, discarding unsaved changes."""
        self._settings = Settings(deepcopy(_DEFAULT_SETTINGS), self.path)
        self._load_from_disk()


__all__ = ["SettingsManager", "Settings"]
