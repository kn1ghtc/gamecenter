#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple save system using JSON in assets/savegame.json"""

import json
from pathlib import Path


def _save_path(assets_dir: str | Path) -> Path:
    return Path(assets_dir) / "savegame.json"


def has_save(assets_dir: str | Path) -> bool:
    return _save_path(assets_dir).exists()


def load_game(assets_dir: str | Path) -> dict | None:
    path = _save_path(assets_dir)
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Failed to load savegame: {e}")
    return None


def save_game(assets_dir: str | Path, data: dict) -> None:
    path = _save_path(assets_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save savegame: {e}")
