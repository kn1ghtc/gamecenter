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

    x_positions = [btn.getPos()[0] for btn in buttons]
    min_x, max_x = min(x_positions), max(x_positions)
    # 左右两列之间需要预留信息面板空隙（右侧为信息面板区域）
    assert max_x < 0.5, "角色网格不应侵入右侧信息面板"
    assert min_x > -1.2, "角色网格左侧不应超出背景边界"


def test_information_panel_layout(character_selector: CharacterSelector) -> None:
    info_frame = character_selector.info_frame
    assert info_frame is not None
    frame_size = info_frame['frameSize']
    left, right, bottom, top = frame_size
    # 信息面板应位于背景右侧且拥有合理宽度
    assert right - left > 0.6
    assert top - bottom > 1.0

    portrait_scale = character_selector.char_portrait_image.getScale()[0]
    assert 0.1 <= portrait_scale <= 0.3, "角色肖像缩放应保持在可见范围内"


def test_keyboard_navigation_bindings(character_selector: CharacterSelector, showbase_app: ShowBase) -> None:
    # 模拟一次导航，验证不会抛出异常并且索引发生变化
    initial_index = character_selector.current_selection_index
    character_selector._navigate_right()  # pylint: disable=protected-access
    showbase_app.taskMgr.step()
    assert character_selector.current_selection_index != initial_index