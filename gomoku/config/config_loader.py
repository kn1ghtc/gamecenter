"""难度配置加载器
Difficulty Configuration Loader

统一管理所有AI难度级别的配置参数。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class DifficultyConfig:
    """难度配置类"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """初始化难度配置
        
        Args:
            config_dict: 配置字典
        """
        self.name = config_dict['name']
        self.display_name = config_dict['display_name']
        self.search_depth = config_dict['search_depth']
        self.time_limit = config_dict['time_limit']
        self.use_iterative_deepening = config_dict.get('use_iterative_deepening', False)
        self.use_killer_moves = config_dict.get('use_killer_moves', True)
        self.use_history_table = config_dict.get('use_history_table', True)
        self.transposition_table_size = config_dict.get('transposition_table_size', 500000)
        self.candidate_moves_count = config_dict.get('candidate_moves_count', 12)
        self.description = config_dict.get('description', '')
    
    def get_depth(self) -> int:
        """获取搜索深度"""
        return self.search_depth
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
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
            'description': self.description
        }


class ConfigManager:
    """配置管理器（单例）"""
    
    _instance = None
    _config_data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._config_data is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        config_path = Path(__file__).parent / 'difficulty_config.json'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
            # 使用默认配置
            self._config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "difficulties": {
                "easy": {
                    "name": "简单",
                    "display_name": "简单 (D3)",
                    "search_depth": 3,
                    "time_limit": 5.0,
                    "use_iterative_deepening": False,
                    "use_killer_moves": True,
                    "use_history_table": False,
                    "transposition_table_size": 100000,
                    "candidate_moves_count": 10
                },
                "medium": {
                    "name": "中等",
                    "display_name": "中等 (D5)",
                    "search_depth": 5,
                    "time_limit": 5.0,
                    "use_iterative_deepening": False,
                    "use_killer_moves": True,
                    "use_history_table": True,
                    "transposition_table_size": 500000,
                    "candidate_moves_count": 12
                },
                "hard": {
                    "name": "困难",
                    "display_name": "困难 (D7+)",
                    "search_depth": 7,
                    "time_limit": 10.0,
                    "use_iterative_deepening": True,
                    "use_killer_moves": True,
                    "use_history_table": True,
                    "transposition_table_size": 1000000,
                    "candidate_moves_count": 15
                }
            },
            "default_difficulty": "medium",
            "default_engine_type": "auto"
        }
    
    def get_difficulty_config(self, difficulty_name: str) -> DifficultyConfig:
        """获取难度配置
        
        Args:
            difficulty_name: 难度名称 (easy/medium/hard/expert)
        
        Returns:
            DifficultyConfig对象
        """
        difficulties = self._config_data.get('difficulties', {})
        
        if difficulty_name not in difficulties:
            # 默认使用中等难度
            difficulty_name = self._config_data.get('default_difficulty', 'medium')
        
        config_dict = difficulties[difficulty_name]
        return DifficultyConfig(config_dict)
    
    def get_all_difficulties(self) -> Dict[str, DifficultyConfig]:
        """获取所有难度配置
        
        Returns:
            难度名称到配置对象的映射
        """
        difficulties = self._config_data.get('difficulties', {})
        return {
            name: DifficultyConfig(config)
            for name, config in difficulties.items()
        }
    
    def get_difficulty_names(self) -> list:
        """获取所有难度名称"""
        return list(self._config_data.get('difficulties', {}).keys())
    
    def get_phase2_config(self) -> Dict[str, Any]:
        """获取Phase 2优化配置"""
        return self._config_data.get('phase2_optimizations', {})
    
    def get_cpp_config(self) -> Dict[str, Any]:
        """获取C++引擎配置"""
        return self._config_data.get('cpp_engine', {})
    
    def get_default_difficulty(self) -> str:
        """获取默认难度"""
        return self._config_data.get('default_difficulty', 'medium')
    
    def get_default_engine_type(self) -> str:
        """获取默认引擎类型"""
        return self._config_data.get('default_engine_type', 'auto')
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._config_data = None
        self._load_config()


# 全局函数
def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    return ConfigManager()


def get_difficulty_config(difficulty_name: str) -> DifficultyConfig:
    """快捷函数：获取难度配置"""
    return get_config_manager().get_difficulty_config(difficulty_name)
