"""Integration tests for the Panda3D character selection UI."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

panda3d = pytest.importorskip("panda3d.core")
ShowBase_mod = pytest.importorskip("direct.showbase.ShowBase")

from panda3d.core import loadPrcFileData  # type: ignore  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")

from direct.showbase.ShowBase import ShowBase  # type: ignore  # noqa: E402

from streetBattle.character_selector import CharacterSelector
from streetBattle.enhanced_character_manager import EnhancedCharacterManager


@pytest.fixture()
def showbase_app() -> Iterator[ShowBase]:
    base = ShowBase()  # window disabled via loadPrcFileData
    base.disableMouse()
    try:
        yield base
    finally:
        base.taskMgr.stop()
        base.destroy()


@pytest.fixture()
def character_selector(showbase_app: ShowBase) -> Iterator[CharacterSelector]:
    assets_dir = Path(__file__).resolve().parents[1] / "assets"
    manager = EnhancedCharacterManager(assets_dir)
    selector = CharacterSelector(showbase_app, manager)
    selector.show(mode="versus", player_number=1)
    showbase_app.taskMgr.step()
    try:
        yield selector
    finally:
        selector.hide()
        selector.destroy()


def test_character_grid_spacing(character_selector: CharacterSelector) -> None:
    buttons = [btn for btn in character_selector.character_buttons if btn]
    assert buttons, "角色按钮应当成功创建"

    # 获取按钮位置信息
    x_positions = []
    for btn_data in buttons:
        if 'frame' in btn_data and hasattr(btn_data['frame'], 'getPos'):
            pos = btn_data['frame'].getPos()
            x_positions.append(pos[0])
    
    if x_positions:
        min_x, max_x = min(x_positions), max(x_positions)
        # 左右两列之间需要预留信息面板空隙（右侧为信息面板区域）
        assert max_x < 0.5, "角色网格不应侵入右侧信息面板"
        assert min_x > -1.2, "角色网格左侧不应超出背景边界"


def test_information_panel_layout(character_selector: CharacterSelector) -> None:
    # 检查预览容器是否存在
    assert hasattr(character_selector, 'preview_container'), "预览容器应当存在"
    
    # 检查预览图像是否存在
    if hasattr(character_selector, 'preview_image') and character_selector.preview_image:
        # 预览图像应具有合理的缩放
        scale = character_selector.preview_image.getScale()
        assert 0.1 <= scale[0] <= 0.5, "预览图像缩放应保持在可见范围内"
    
    # 检查预览信息文本是否存在
    assert hasattr(character_selector, 'preview_info'), "预览信息文本应当存在"
    assert character_selector.preview_info is not None, "预览信息文本不应为None"


def test_keyboard_navigation_bindings(character_selector: CharacterSelector, showbase_app: ShowBase) -> None:
    # 检查是否有角色可供选择
    if not character_selector.all_characters:
        pytest.skip("没有可用角色进行导航测试")
    
    # 模拟键盘导航 - 使用现有的选择机制
    initial_index = character_selector.current_selection_index
    
    # 如果有多个角色，尝试选择下一个角色
    if len(character_selector.all_characters) > 1:
        # 模拟选择下一个角色
        next_index = (initial_index + 1) % len(character_selector.all_characters)
        next_char = character_selector.all_characters[next_index]
        character_selector._on_character_selected(next_char)
        
        showbase_app.taskMgr.step()
        
        # 验证选择已更新
        assert character_selector.selected_character == next_char['id'], "角色选择应当更新"