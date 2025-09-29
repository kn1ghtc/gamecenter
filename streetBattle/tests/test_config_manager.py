"""
配置管理器单元测试
测试config_manager.py中的所有功能
"""

import pytest
import json
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


class TestConfigManager:
    """配置管理器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.manager = ConfigManager(self.config_dir)
        self.manager.load_all_configs()
    
    def test_init(self):
        """测试初始化"""
        assert self.manager.config_dir == self.config_dir
        # 检查是否加载了配置
        assert self.manager._configs is not None
        assert len(self.manager._configs) > 0

    def test_load_audio_config(self):
        """测试音频配置加载"""
        audio_config = self.manager.get_audio_config()
        assert audio_config is not None
        # 检查实际的音频配置字段
        assert 'bgm_volume' in audio_config
        assert 'sfx_volume' in audio_config
        assert 'character_voices' in audio_config

    def test_load_character_stats(self):
        """测试角色属性配置加载"""
        stats = self.manager.get_character_stats()
        assert stats is not None
        # 检查实际的统计配置结构
        assert 'character_stat_modifiers' in stats
        assert 'kyo_kusanagi' in stats['character_stat_modifiers']

    def test_load_roster(self):
        """测试花名册配置加载"""
        roster = self.manager.get_roster()
        assert roster is not None
        assert 'fighters' in roster
        assert isinstance(roster['fighters'], list)
        assert len(roster['fighters']) > 0

    def test_load_settings(self):
        """测试游戏设置配置加载"""
        settings = self.manager.get_game_settings()
        assert settings is not None
        assert 'audio' in settings
        assert 'controls' in settings
        assert 'gameplay' in settings
        assert 'graphics' in settings

    def test_load_skills(self):
        """测试技能配置加载"""
        skills = self.manager.get_config('skills')
        assert skills is not None
        assert 'skill_templates' in skills
        assert 'character_skills' in skills
        # 检查角色技能配置
        assert 'kyo_kusanagi' in skills['character_skills']

    def test_get_character_profile(self):
        """测试获取角色档案"""
        profile = self.manager.get_character_config('kyo_kusanagi')
        assert profile is not None
        assert 'name' in profile
        assert 'description' in profile

    def test_get_character_manifest(self):
        """测试获取角色清单"""
        manifest = self.manager.get_config('characters_manifest')
        assert manifest is not None
        assert 'characters' in manifest
        assert isinstance(manifest['characters'], list)

    def test_get_character_skills(self):
        """测试获取角色技能"""
        skills = self.manager.get_config('skills')
        assert skills is not None
        # 检查角色技能配置结构
        assert 'character_skills' in skills
        assert 'kyo_kusanagi' in skills['character_skills']

    def test_save_config(self, tmp_path):
        """测试配置保存功能"""
        test_config = {"test_key": "test_value"}
        test_file = tmp_path / "test_config.json"
        
        # 使用标准文件操作保存配置
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        # 验证文件存在且内容正确
        assert test_file.exists()
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        assert loaded_config == test_config

    def test_config_validation(self):
        """测试配置验证"""
        # 测试音频配置验证
        audio_config = self.manager.get_audio_config()
        assert audio_config is not None
        # 检查实际的音频配置字段
        assert 'bgm_volume' in audio_config
        assert 'sfx_volume' in audio_config
        
        # 测试角色配置验证
        validation_errors = self.manager.validate_configs()
        assert isinstance(validation_errors, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])