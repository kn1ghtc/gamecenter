#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration system for Super Mario
Loads defaults and optional overrides from assets/config.json
"""

from __future__ import annotations
import json
from pathlib import Path


DEFAULT_CONFIG = {
    "game": {
        "max_levels": 30,
        "initial_lives": 3000,
        "time_per_level": 400,
        "music_enabled": True,
    },
    "player": {
        "speed": 200,
        "jump_force": -600,
        "gravity": 800,
        "max_fall_speed": 400,
        "skills": {
            "double_jump": True,
            "dash": True,
        }
    }
}


def deep_update(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_update(base[k], v)
        else:
            base[k] = v
    return base


def load_config(assets_dir: str | Path) -> dict:
    assets_dir = Path(assets_dir)
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg_path = assets_dir / "config.json"
    try:
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            deep_update(cfg, user_cfg)
    except Exception as e:
        print(f"Failed to load config.json: {e}")
    return cfg
