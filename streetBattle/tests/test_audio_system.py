"""
音频系统单元测试
测试音频配置和音频系统的功能
"""

import pytest
import json
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


class TestAudioSystem:
    """音频系统测试类"""

    def setup_method(self):
        """测试方法前置设置"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_manager = ConfigManager(self.config_dir)
        self.config_manager.load_all_configs()

    def test_audio_config_structure(self):
        """测试音频配置结构完整性"""
        audio_config = self.config_manager.get_audio_config()

        # 检查基本音量控制
        assert 'master_volume' in audio_config
        assert 'bgm_volume' in audio_config
        assert 'sfx_volume' in audio_config
        assert 'voice_volume' in audio_config
        assert 'ui_volume' in audio_config

        # 检查音量值范围
        assert 0 <= audio_config['master_volume'] <= 1.0
        assert 0 <= audio_config['bgm_volume'] <= 1.0
        assert 0 <= audio_config['sfx_volume'] <= 1.0

    def test_character_voices_config(self):
        """测试角色语音配置"""
        audio_config = self.config_manager.get_audio_config()

        assert 'character_voices' in audio_config
        # 检查至少有一个角色语音配置存在
        assert len(audio_config['character_voices']) > 0
        
        # 使用实际存在的角色（如'kyo'）进行测试
        kyo_voice = audio_config['character_voices'].get('kyo')
        assert kyo_voice is not None
        assert 'attack_1' in kyo_voice
        assert 'attack_2' in kyo_voice
        assert 'special_move' in kyo_voice

    def test_combat_sfx_config(self):
        """测试战斗音效配置"""
        audio_config = self.config_manager.get_audio_config()

        assert 'combat_sfx' in audio_config
        
        combat_sfx = audio_config['combat_sfx']
        assert 'light_punch' in combat_sfx
        assert 'heavy_punch' in combat_sfx
        assert 'special_hit' in combat_sfx

    def test_ui_sfx_config(self):
        """测试UI音效配置"""
        audio_config = self.config_manager.get_audio_config()

        assert 'ui_sfx' in audio_config
        
        ui_sfx = audio_config['ui_sfx']
        assert 'menu_select' in ui_sfx
        assert 'menu_confirm' in ui_sfx
        assert 'game_start' in ui_sfx

    def test_bgm_tracks_config(self):
        """测试背景音乐配置"""
        audio_config = self.config_manager.get_audio_config()

        assert 'bgm_tracks' in audio_config
        
        bgm_tracks = audio_config['bgm_tracks']
        assert 'main_menu' in bgm_tracks
        assert 'character_select' in bgm_tracks
        assert 'battle_stage_1' in bgm_tracks

    def test_audio_file_paths(self):
        """测试音频文件路径有效性"""
        audio_config = self.config_manager.get_audio_config()

        # 检查默认角色语音路径 - 使用实际存在的角色
        kyo_voice = audio_config['character_voices']['kyo']
        assert kyo_voice is not None
        for key, path in kyo_voice.items():
            assert isinstance(path, str)
            assert path.endswith(('.wav', '.ogg', '.mp3'))

        # 检查战斗音效路径
        combat_sfx = audio_config['combat_sfx']
        assert 'light_punch' in combat_sfx
        assert 'heavy_punch' in combat_sfx
        for key, path in combat_sfx.items():
            assert isinstance(path, str)
            assert path.endswith(('.wav', '.ogg', '.mp3'))

    def test_audio_mixing_config(self):
        """测试音频混音配置"""
        audio_config = self.config_manager.get_audio_config()

        # 检查音量层级关系
        assert audio_config['master_volume'] >= audio_config['bgm_volume']
        assert audio_config['master_volume'] >= audio_config['sfx_volume']
        assert audio_config['master_volume'] >= audio_config['voice_volume']
        assert audio_config['master_volume'] >= audio_config['ui_volume']

        # 检查音量值合理性
        assert audio_config['bgm_volume'] > 0
        assert audio_config['sfx_volume'] > 0

    def test_audio_config_consistency(self):
        """测试音频配置一致性"""
        audio_config = self.config_manager.get_audio_config()

        # 检查所有音量值都在合理范围内
        for key, value in audio_config.items():
            if key.endswith('_volume'):
                assert 0 <= value <= 1.0, f"音量值 {key} 超出范围: {value}"

        # 检查音频文件路径格式
        for category in ['character_voices', 'combat_sfx', 'ui_sfx', 'bgm_tracks']:
            if category in audio_config:
                category_data = audio_config[category]
                if isinstance(category_data, dict):
                    for key, path in category_data.items():
                        if isinstance(path, str):
                            assert path.startswith('assets/audio/'), f"音频路径格式错误: {path}"