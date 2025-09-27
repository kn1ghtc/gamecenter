"""StreetBattle smoke tests.

These tests validate that bundled sprite assets and skill configurations are
loadable without launching the interactive game loop. They are intended to run
quickly inside CI to guarantee that resource packaging and metadata stay valid.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
for candidate in (REPO_ROOT, PROJECT_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import pygame
import pytest

from streetBattle.twod5 import game as twod5_game


@pytest.fixture(scope="module")
def pygame_env() -> Iterator[None]:
    """Initialise a headless pygame context for asset loading."""
    if pygame.get_init():
        yield
        return
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))
    try:
        yield
    finally:
        pygame.display.quit()
        pygame.quit()


def _load_manifest(name: str) -> dict[str, object]:
    manifest = twod5_game._load_sprite_manifest(name)  # type: ignore[attr-defined]
    assert manifest is not None, f"Missing manifest for sprite set '{name}'"
    return manifest


def _load_roster_entries() -> list[dict[str, object]]:
    roster_path = PROJECT_ROOT / "config" / "roster.json"
    if not roster_path.exists():
        return []
    payload = json.loads(roster_path.read_text(encoding="utf-8"))
    fighters = payload.get("fighters", []) if isinstance(payload, dict) else []
    return [entry for entry in fighters if isinstance(entry, dict)]


def test_sprite_manifests_exist_and_load(pygame_env: None) -> None:
    """所有 roster 精灵表都应存在且可加载。"""
    roster_entries = _load_roster_entries()
    manifest_names: set[str] = {"hero", "shadow"}
    for entry in roster_entries:
        manifest = entry.get("manifest") or entry.get("key")
        if isinstance(manifest, str) and manifest:
            manifest_names.add(manifest)
    assert manifest_names, "应至少有一个精灵 manifest"

    for manifest_name in sorted(manifest_names):
        pack = twod5_game.load_sprite_animations(manifest_name)
        assert pack is not None, f"Unable to load animations for {manifest_name}"
        states, metadata = pack
        assert states, f"No animation states returned for {manifest_name}"
        assert "idle" in states, f"'{manifest_name}' 缺少 idle 动画"
        assert metadata.get("license"), f"{manifest_name} metadata 缺少授权信息"


def test_skills_align_with_manifest(pygame_env: None) -> None:
    """技能配置引用的动画必须在 manifest 上存在。"""
    skills_path = PROJECT_ROOT / "config" / "skills.json"
    payload = json.loads(skills_path.read_text(encoding="utf-8"))
    assert payload, "skills.json 应包含至少一个角色"

    for roster_id, roster_cfg in payload.items():
        manifest = _load_manifest(roster_id)
        states = manifest.get("states", {}) if isinstance(manifest, dict) else {}
        available = set(states.keys())
        assert available, f"{roster_id} manifest 缺少 states"

        skills = roster_cfg.get("skills", []) if isinstance(roster_cfg, dict) else []
        assert skills, f"{roster_id} 至少需要一个技能定义"
        for skill in skills:
            name = skill.get("name")
            animation = skill.get("animation")
            assert name, f"技能缺少 name 字段: {skill}"
            assert animation, f"技能 {name} 缺少 animation 字段"
            assert animation in available, (
                f"技能 {name} 引用的动画 '{animation}' 在 {roster_id} manifest 中不存在"
            )
            hit_frames = skill.get("hit_frames", [])
            assert isinstance(hit_frames, list), f"技能 {name} 的 hit_frames 必须为列表"


def test_roster_entries_have_skill_profiles() -> None:
    """每个 roster 角色都应映射到有效技能配置。"""
    roster_entries = _load_roster_entries()
    skills_path = PROJECT_ROOT / "config" / "skills.json"
    skills_payload = json.loads(skills_path.read_text(encoding="utf-8"))
    assert skills_payload, "技能配置不可为空"

    for entry in roster_entries:
        key = entry.get("key")
        assert isinstance(key, str) and key, f"roster entry 缺少有效 key: {entry}"
        skill_profile = entry.get("skill_profile") or key
        assert skill_profile in skills_payload, f"{key} 未在 skills.json 中定义 skill_profile"
        manifest_name = entry.get("manifest") or key
        manifest = _load_manifest(str(manifest_name))
        assert manifest is not None, f"{key} 指向的 manifest {manifest_name} 不存在"


def test_settings_manager_roundtrip(tmp_path: Path) -> None:
    """配置写入和重新加载应保持字段完整。"""
    manager = twod5_game.SettingsManager(project_root=tmp_path)
    manager.set("controls.keyboard.attack", "l", persist=True)
    manager_refreshed = twod5_game.SettingsManager(project_root=tmp_path)
    assert (
        manager_refreshed.get("controls.keyboard.attack") == "l"
    ), "配置在磁盘往返后应保持变更"
