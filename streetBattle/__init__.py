"""StreetBattle 包初始化配置。

此模块负责：

1. 暴露核心入口（`GameLauncher`、`launch`、`StreetBattleGame`、`SettingsManager`）。
2. 在脚本以 `python streetBattle/<script>.py` 方式运行时，自动修正 `sys.path`
   以避免 ``ModuleNotFoundError: No module named 'gamecenter'``。
3. 维护 `gamecenter` 命名空间映射，使得 `gamecenter.streetBattle` 与 `streetBattle`
   可以互通使用，满足仓库“使用绝对导入”的规范。
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


def _ensure_project_on_path() -> None:
	"""Ensure the repository project root is present on ``sys.path``.

	当直接运行 ``python streetBattle/main.py`` 时，Python 只会把 ``streetBattle``
	目录加入 ``sys.path``，导致无法解析 ``gamecenter`` 绝对导入。本函数确保
	``gamecenter`` 上级目录被纳入模块搜索路径。
	"""

	project_path = str(PROJECT_ROOT)
	if project_path not in sys.path:
		sys.path.insert(0, project_path)


def _ensure_namespace_bridge() -> None:
	"""Bridge ``streetBattle`` 与 ``gamecenter.streetBattle`` 的命名空间。"""

	# 构造 gamecenter 模块壳，提供 __path__ 以支持下级包发现
	if "gamecenter" not in sys.modules:
		gamecenter_module = ModuleType("gamecenter")
		gamecenter_module.__path__ = [str(PROJECT_ROOT)]
		sys.modules["gamecenter"] = gamecenter_module

	# 将 gamecenter.streetBattle 指向当前包，保持双向兼容
	sys.modules.setdefault("gamecenter.streetBattle", sys.modules[__name__])


_ensure_project_on_path()
_ensure_namespace_bridge()


from .launcher import GameLauncher, launch  # noqa: E402  pylint: disable=wrong-import-position
from .main import StreetBattleGame  # noqa: E402  pylint: disable=wrong-import-position
from .config import SettingsManager  # noqa: E402  pylint: disable=wrong-import-position


__all__ = [
	"GameLauncher",
	"StreetBattleGame",
	"SettingsManager",
	"launch",
]



