#!/usr/bin/env python3
"""验证2.5D街机模式的花名册加载逻辑。"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

# 将项目根路径加入sys.path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pytestmark = [
    pytest.mark.filterwarnings("ignore:pkg_resources is deprecated as an API.:UserWarning"),
    pytest.mark.filterwarnings("ignore:Deprecated call to `pkg_resources.declare_namespace:DeprecationWarning"),
]


@pytest.fixture()
def patched_pygame(monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    """提供一个最小化的pygame桩，避免测试依赖真实的SDL环境。"""

    stub = types.SimpleNamespace(
        get_init=lambda: False,
        init=lambda: None,
        quit=lambda: None,
        display=types.SimpleNamespace(gl_set_swap_interval=lambda *_: None),
        key=types.SimpleNamespace(name=lambda code: f"key-{code}"),
    )
    from gamecenter.streetBattle.twod5 import game as twod5_game

    monkeypatch.setattr(twod5_game, "pygame", stub)
    return stub


def test_roster_loader_accepts_string_entries(patched_pygame: types.SimpleNamespace) -> None:
    """确保字符串形式的fighters列表能够被正确解析并生成花名册。"""

    from gamecenter.streetBattle.twod5.game import SpriteBattleGame

    game = SpriteBattleGame()

    assert game.roster_map, "roster_map 不应为空"
    assert game.roster_order, "roster_order 不应为空"
    assert "kyo_kusanagi" in game.roster_map, "Kyo 应该出现在花名册中"
    assert len(game.roster_order) >= 2, "花名册应至少包含玩家与CPU两个角色"

    kyo_entry = game.roster_map["kyo_kusanagi"]
    assert kyo_entry["manifest"] == "kyo_kusanagi"
    assert kyo_entry["display_name"].lower().startswith("kyo"), "显示名称应与角色对应"


def test_roster_loader_ensures_default_entries(patched_pygame: types.SimpleNamespace) -> None:
    """验证默认玩家与CPU角色始终存在，避免初始化时索引越界。"""

    from gamecenter.streetBattle.twod5.game import SpriteBattleGame

    game = SpriteBattleGame()

    assert "kyo_kusanagi" == game.roster_order[0], "默认玩家应为 config/roster.json 中的配置"
    assert game.roster_order[1] != "", "CPU 角色不应为空字符串"
    assert game.roster_order[1] in game.roster_map, "CPU 角色必须在花名册映射中"
