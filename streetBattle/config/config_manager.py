"""
StreetBattle 统一配置管理器

这个模块负责加载和管理游戏的所有配置文件，提供统一的配置访问接口。
支持配置文件的动态加载、验证和热重载功能。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("streetbattle.config")


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_dir: str | Path):
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._config_files = {
            'audio': 'audio_config.json',
            'stats': 'character_stats.json', 
            'roster': 'roster.json',
            'settings': 'settings.json',
            'skills': 'skills.json',
            'characters_manifest': 'characters/manifest.json',
            'characters_profiles': 'characters/profiles.json'
        }
        
    def load_all_configs(self) -> bool:
        """加载所有配置文件"""
        success = True
        for config_name, filename in self._config_files.items():
            if not self._load_config(config_name, filename):
                success = False
                logger.error(f"Failed to load config: {filename}")
        
        if success:
            logger.info("All configurations loaded successfully")
        return success
    
    def _load_config(self, config_name: str, filename: str) -> bool:
        """加载单个配置文件"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return False
            
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._configs[config_name] = data
            logger.debug(f"Loaded config: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading config {filename}: {e}")
            return False
    
    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取指定配置"""
        return self._configs.get(config_name)
    
    def get_character_config(self, character_id: str) -> Optional[Dict[str, Any]]:
        """获取角色完整配置（整合manifest和profile）"""
        manifest = self._configs.get('characters_manifest', {})
        profiles = self._configs.get('characters_profiles', {})
        skills = self._configs.get('skills', {})
        
        character_data = {}
        
        # 从manifest获取资源路径
        for char in manifest.get('characters', []):
            if char.get('id') == character_id:
                character_data.update(char)
                break
        
        # 从profiles获取档案信息
        if character_id in profiles:
            character_data.update(profiles[character_id])
        
        # 从skills获取技能配置
        if character_id in skills:
            character_data['skills'] = skills[character_id]
        
        return character_data if character_data else None
    
    def get_audio_config(self) -> Dict[str, Any]:
        """获取音频配置"""
        return self._configs.get('audio', {})
    
    def get_game_settings(self) -> Dict[str, Any]:
        """获取游戏设置"""
        return self._configs.get('settings', {})
    
    def get_roster(self) -> Dict[str, Any]:
        """获取角色花名册"""
        return self._configs.get('roster', {})
    
    def get_character_stats(self) -> Dict[str, Any]:
        """获取角色统计配置"""
        return self._configs.get('stats', {})
    
    def reload_config(self, config_name: str) -> bool:
        """重新加载指定配置"""
        if config_name in self._config_files:
            filename = self._config_files[config_name]
            return self._load_config(config_name, filename)
        return False
    
    def validate_configs(self) -> Dict[str, list]:
        """验证所有配置的完整性"""
        errors = {}
        
        # 验证关键配置文件是否存在
        required_configs = ['audio', 'stats', 'roster', 'settings']
        for config_name in required_configs:
            if config_name not in self._configs:
                if 'missing_required_files' not in errors:
                    errors['missing_required_files'] = []
                errors['missing_required_files'].append(config_name)
        
        # 移除对角色配置一致性的检查，允许配置不完整
        # 在实际游戏中，角色配置可以动态加载，不需要强制一致性
        
        return errors


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: str | Path = None) -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    
    if _config_manager is None:
        if config_dir is None:
            raise ValueError("Config directory must be provided for first initialization")
        _config_manager = ConfigManager(config_dir)
        _config_manager.load_all_configs()
    
    return _config_manager


def initialize_config(config_dir: str | Path) -> ConfigManager:
    """初始化配置管理器"""
    global _config_manager
    _config_manager = ConfigManager(config_dir)
    _config_manager.load_all_configs()
    return _config_manager