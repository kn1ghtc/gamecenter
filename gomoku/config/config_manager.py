"""统一配置管理器
Unified configuration manager for the Gomoku project.

单一入口加载所有JSON配置，提供类型安全的访问方法。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional


class DifficultyConfig:
    """AI难度配置"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.name: str = config_dict['name']
        self.display_name: str = config_dict['display_name']
        self.search_depth: int = config_dict['search_depth']
        self.time_limit: float = config_dict['time_limit']
        self.use_iterative_deepening: bool = config_dict.get('use_iterative_deepening', False)
        self.use_killer_moves: bool = config_dict.get('use_killer_moves', True)
        self.use_history_table: bool = config_dict.get('use_history_table', True)
        self.transposition_table_size: int = config_dict.get('transposition_table_size', 500_000)
        self.candidate_moves_count: int = config_dict.get('candidate_moves_count', 12)
        self.description: str = config_dict.get('description', '')

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典（用于调试/记录）"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'search_depth': self.search_depth,
            'time_limit': self.time_limit,
            'use_iterative_deepening': self.use_iterative_deepening,
            'use_killer_moves': self.use_killer_moves,
            'use_history_table': self.use_history_table,
            'transposition_table_size': self.transposition_table_size,
            'candidate_moves_count': self.candidate_moves_count,
            'description': self.description,
        }


class ConfigManager:
    """配置管理器（单例）"""

    _instance: Optional['ConfigManager'] = None

    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_is_initialized') and self._is_initialized:  # 避免重复加载
            return
        self._config_path = Path(__file__).parent / 'game_config.json'
        self._data: Dict[str, Any] = {}
        self._load()
        self._is_initialized = True

    # ------------------------------------------------------------------
    # 基础加载
    # ------------------------------------------------------------------
    def _load(self) -> None:
        try:
            with open(self._config_path, 'r', encoding='utf-8') as fp:
                self._data = json.load(fp)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"无法加载配置文件: {self._config_path}") from exc

    def reload(self) -> None:
        """重新加载配置"""
        self._load()

    # ------------------------------------------------------------------
    # 通用访问
    # ------------------------------------------------------------------
    def get_raw(self) -> Dict[str, Any]:
        """返回底层配置数据的深拷贝"""
        return copy.deepcopy(self._data)

    def get_path(self, name: str, default: Optional[str] = None) -> str:
        return self._data.get('paths', {}).get(name, default or '')

    def get_window_config(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data.get('window', {}))

    def get_gameplay_config(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data.get('gameplay', {}))

    def get_engine_defaults(self) -> Dict[str, Any]:
        engine = self._data.get('engine', {})
        return copy.deepcopy(engine.get('defaults', {}))

    def get_engine_metadata(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data.get('engine', {}))

    def get_colors(self) -> Dict[str, tuple]:
        colors = {}
        for key, value in self._data.get('colors', {}).items():
            colors[key] = tuple(value)
        return colors

    def get_ui_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        ui = self._data.get('ui', {})
        if section:
            return copy.deepcopy(ui.get(section, {}))
        return copy.deepcopy(ui)

    def get_pattern_scores(self) -> Dict[str, int]:
        return copy.deepcopy(self._data.get('pattern_scores', {}))

    def get_default_settings(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data.get('default_settings', {}))

    def get_audio_config(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data.get('audio', {}))

    # ------------------------------------------------------------------
    # AI难度配置
    # ------------------------------------------------------------------
    def get_difficulty_config(self, difficulty_name: str) -> DifficultyConfig:
        engine_data = self._data.get('engine', {})
        difficulties = engine_data.get('difficulties', {})
        defaults = engine_data.get('defaults', {})
        fallback = defaults.get('difficulty', 'medium')

        config_dict = difficulties.get(difficulty_name, difficulties.get(fallback))
        if config_dict is None:
            raise KeyError(f"未找到难度配置: {difficulty_name}")
        return DifficultyConfig(config_dict)

    def get_difficulty_names(self) -> Dict[str, DifficultyConfig]:
        engine_data = self._data.get('engine', {})
        difficulties = engine_data.get('difficulties', {})
        return {
            name: DifficultyConfig(data)
            for name, data in difficulties.items()
        }


def get_config_manager() -> ConfigManager:
    """快捷函数：获取配置管理器实例"""
    return ConfigManager()


def get_difficulty_config(difficulty_name: str) -> DifficultyConfig:
    """快捷函数：返回难度配置"""
    return get_config_manager().get_difficulty_config(difficulty_name)
