"""
游戏设置系统单元测试
测试游戏设置、图形配置、控制映射等功能
"""

import pytest
import json
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from streetBattle.config.config_manager import ConfigManager


class TestGameSettings:
    """游戏设置测试类"""

    def setup_method(self):
        """测试方法前置设置"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_manager = ConfigManager(self.config_dir)
        self.config_manager.load_all_configs()

    def test_settings_structure(self):
        """测试设置结构完整性"""
        settings = self.config_manager.get_game_settings()

        # 检查主要设置类别
        assert "audio" in settings
        assert "controls" in settings
        assert "gameplay" in settings
        assert "graphics" in settings
        assert "preferred_version" in settings
        assert "remember_last_version" in settings

    def test_audio_settings(self):
        """测试音频设置"""
        settings = self.config_manager.get_game_settings()
        audio_settings = settings["audio"]

        # 检查音频设置字段
        assert "effects_volume" in audio_settings
        assert "music_volume" in audio_settings
        assert "muted" in audio_settings

        # 验证音频设置值
        assert 0 <= audio_settings["effects_volume"] <= 1.0
        assert 0 <= audio_settings["music_volume"] <= 1.0
        assert isinstance(audio_settings["muted"], bool)

        # 检查音量关系
        assert audio_settings["effects_volume"] > 0, "音效音量不应为0"
        assert audio_settings["music_volume"] > 0, "音乐音量不应为0"

    def test_controls_settings(self):
        """测试控制设置"""
        settings = self.config_manager.get_game_settings()
        controls = settings["controls"]

        # 检查键盘控制映射
        assert "keyboard" in controls
        keyboard = controls["keyboard"]

        # 检查必需的控制键
        required_keys = ["attack", "down", "jump", "left", "right", "special", "up"]
        for key in required_keys:
            assert key in keyboard, f"缺少键盘控制键: {key}"
            assert keyboard[key], f"键盘控制键 {key} 为空"

        # 验证控制键唯一性
        key_values = list(keyboard.values())
        assert len(key_values) == len(set(key_values)), "控制键映射存在重复"

    def test_gameplay_settings(self):
        """测试游戏玩法设置"""
        settings = self.config_manager.get_game_settings()
        gameplay = settings["gameplay"]

        # 检查游戏玩法字段
        assert "cpu_character" in gameplay
        assert "difficulty" in gameplay
        assert "player_character" in gameplay
        assert "rounds_to_win" in gameplay

        # 验证游戏玩法值
        assert gameplay["rounds_to_win"] > 0
        assert gameplay["rounds_to_win"] <= 5, "回合数设置过高"

        # 检查难度级别
        valid_difficulties = ["easy", "normal", "hard", "expert"]
        assert gameplay["difficulty"] in valid_difficulties, f"无效的难度设置: {gameplay['difficulty']}" 

        # 检查角色存在性
        roster = self.config_manager.get_roster()
        fighters = roster["fighters"]
        
        # 检查默认角色是否在花名册中
        assert gameplay["player_character"] in fighters, f"玩家角色不存在于花名册中: {gameplay['player_character']}"
        assert gameplay["cpu_character"] in fighters, f"CPU角色不存在于花名册中: {gameplay['cpu_character']}"

    def test_graphics_settings(self):
        """测试图形设置"""
        settings = self.config_manager.get_game_settings()
        graphics = settings["graphics"]

        # 检查图形设置字段
        assert "fullscreen" in graphics
        assert "resolution" in graphics
        assert "vsync" in graphics
        assert "texture_quality" in graphics
        assert "shadow_quality" in graphics
        assert "anti_aliasing" in graphics
        assert "anisotropic_filtering" in graphics
        assert "particle_effects" in graphics
        assert "post_processing" in graphics

        # 验证图形设置值
        assert isinstance(graphics["fullscreen"], bool)
        assert isinstance(graphics["vsync"], bool)
        assert isinstance(graphics["particle_effects"], bool)
        assert isinstance(graphics["post_processing"], bool)

        # 检查分辨率
        resolution = graphics["resolution"]
        assert isinstance(resolution, list)
        assert len(resolution) == 2
        assert resolution[0] > 0 and resolution[1] > 0
        assert resolution[0] >= 800 and resolution[1] >= 600, "分辨率设置过低"

        # 检查图形质量设置
        valid_qualities = ["low", "medium", "high", "ultra"]
        assert graphics["texture_quality"] in valid_qualities
        assert graphics["shadow_quality"] in valid_qualities

        # 检查抗锯齿设置
        valid_aa = ["none", "fxaa", "msaa2x", "msaa4x", "msaa8x"]
        assert graphics["anti_aliasing"] in valid_aa

        # 检查各向异性过滤
        assert graphics["anisotropic_filtering"] in [0, 2, 4, 8, 16]

    def test_version_settings(self):
        """测试版本设置"""
        settings = self.config_manager.get_game_settings()

        # 检查版本偏好
        assert "preferred_version" in settings
        assert "remember_last_version" in settings

        # 验证版本设置
        valid_versions = ["2d", "3d"]
        assert settings["preferred_version"] in valid_versions
        assert isinstance(settings["remember_last_version"], bool)

    def test_settings_validation(self):
        """测试设置验证"""
        settings = self.config_manager.get_game_settings()

        # 验证设置键的唯一性
        all_keys = set()

        def collect_keys(config_dict, prefix=""):
            for key, value in config_dict.items():
                full_key = f"{prefix}.{key}" if prefix else key
                assert full_key not in all_keys, f"重复的设置键: {full_key}"
                all_keys.add(full_key)
                if isinstance(value, dict):
                    collect_keys(value, full_key)

        collect_keys(settings)

    def test_settings_default_values(self):
        """测试设置默认值"""
        settings = self.config_manager.get_game_settings()

        # 检查合理的默认值
        assert settings["audio"]["effects_volume"] >= 0.5, "音效音量默认值过低"
        assert settings["audio"]["music_volume"] >= 0.5, "音乐音量默认值过低"
        assert settings["gameplay"]["rounds_to_win"] >= 2, "回合数默认值过低"
        assert settings["graphics"]["resolution"][0] >= 1024, "分辨率默认值过低"
        assert settings["graphics"]["resolution"][1] >= 768, "分辨率默认值过低"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])