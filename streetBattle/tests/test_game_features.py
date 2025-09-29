"""Unit tests covering enhanced 2.5D HUD and camera behaviour."""

from __future__ import annotations

import os
import random
from pathlib import Path

import pygame
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from streetBattle.config import SettingsManager
from streetBattle.twod5 import game as twod5_game

from .test_smoke import pygame_env  # re-export fixture for reuse


@pytest.fixture()
def settings_tmp(tmp_path: Path) -> SettingsManager:
    """Provide an isolated settings manager so tests avoid touching real files."""
    return SettingsManager(project_root=tmp_path)


def test_help_content_reflects_custom_keymap(settings_tmp: SettingsManager, pygame_env: None) -> None:
    """Help overlay should echo bound keys and show translated toggle hint."""
    game = twod5_game.SpriteBattleGame(settings_manager=settings_tmp)
    game.keymap = {
        "left": [pygame.K_a],
        "right": [pygame.K_d],
        "jump": [pygame.K_w],
        "attack": [pygame.K_j],
        "special": [pygame.K_k],
        "help": [pygame.K_F1, pygame.K_h],
    }

    content = game._build_help_content()  # pylint: disable=protected-access
    assert content.overlay, "帮助覆盖文本应生成多行内容"
    assert any("A" in line or "D" in line for line in content.overlay), "左右按键描述应包含映射键"
    assert content.hint.startswith("F1"), "帮助提示应突出显示自定义帮助键"
    assert any("F1" in line for line in content.overlay), "帮助覆盖中应包含帮助键说明"


def test_camera_shake_recovers_to_idle(settings_tmp: SettingsManager, pygame_env: None) -> None:
    """Camera shake should decay back to a neutral offset after impact."""
    random.seed(42)
    game = twod5_game.SpriteBattleGame(settings_manager=settings_tmp)
    game._trigger_camera_shake(28.0)  # pylint: disable=protected-access
    assert game.shake_timer > 0.0

    game._advance_camera_shake(0.0)  # pylint: disable=protected-access
    assert game.shake_offset != (0.0, 0.0), "触发震动后应立即出现偏移"

    total = 0.0
    offsets: list[tuple[float, float]] = []
    while total < game.shake_timer:
        game._advance_camera_shake(0.05)  # pylint: disable=protected-access
        offsets.append(game.shake_offset)
        total += 0.05

    assert any(abs(x) > 0.0 or abs(y) > 0.0 for x, y in offsets), "震动过程中应出现非零偏移"
    game._advance_camera_shake(0.2)  # pylint: disable=protected-access
    assert game.shake_offset == (0.0, 0.0), "震动时间结束后应回归原点"
