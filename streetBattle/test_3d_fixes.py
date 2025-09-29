#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试3D模式修复功能
Test 3D Mode Fixes
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_audio_bgm_loading():
    """测试BGM加载与播放修复"""
    from enhanced_audio_system import EnhancedAudioSystem
    
    # 模拟Panda3D环境
    mock_base = Mock()
    mock_base.loader.loadMusic = Mock(return_value=Mock())
    
    audio_system = EnhancedAudioSystem()
    audio_system.base = mock_base
    
    # 测试BGM加载
    result = audio_system.load_bgm("assets/audio/bgm_loop.wav", name="test_bgm")
    assert result == True
    
    # 测试BGM播放
    result = audio_system.play_bgm("test_bgm", loop=True)
    assert result == True
    
    print("✅ BGM loading and playing test passed")

def test_audio_sfx_loading():
    """测试SFX加载修复"""
    from enhanced_audio_system import EnhancedAudioSystem
    
    # 模拟Panda3D环境
    mock_base = Mock()
    mock_base.loader.loadSfx = Mock(return_value=Mock())
    
    audio_system = EnhancedAudioSystem()
    audio_system.base = mock_base
    
    # 测试SFX加载
    result = audio_system.load_sfx("assets/audio/hit.wav", name="hit")
    assert result == True
    
    print("✅ SFX loading test passed")

def test_3d_character_scaling():
    """测试3D角色缩放修复"""
    from enhanced_character_manager import EnhancedCharacterManager
    from panda3d.core import Vec3
    
    # 模拟应用
    mock_app = Mock()
    mock_app.render = Mock()
    mock_app.loader = Mock()
    
    char_manager = EnhancedCharacterManager(mock_app)
    
    # 模拟角色数据
    char_data = {
        'id': 'kyo_kusanagi',
        'name': 'Kyo Kusanagi',
        'stats': {'speed': 7, 'power': 8}
    }
    
    # 模拟Actor
    mock_actor = Mock()
    mock_actor.isEmpty.return_value = False
    mock_actor.getActorInfo.return_value = {}
    mock_actor.getTightBounds.return_value = (Mock(getZ=lambda: -1.0), Mock(getZ=lambda: 2.0))
    mock_actor.getPos.return_value = Vec3(0, 0, 0)
    
    # 测试角色增强功能（包括缩放）
    char_manager._apply_character_enhancements(mock_actor, char_data)
    
    # 验证缩放被调用
    mock_actor.setScale.assert_called()
    scale_args = mock_actor.setScale.call_args[0]
    assert len(scale_args) == 1  # 单一缩放因子
    assert 0.1 < scale_args[0] < 1.0  # 确保缩放在合理范围内
    
    print("✅ 3D character scaling test passed")

def test_3d_character_ground_positioning():
    """测试3D角色地面定位修复"""
    from player import Player
    from panda3d.core import Vec3
    
    # 模拟render和loader
    mock_render = Mock()
    mock_loader = Mock()
    
    # 模拟Actor实例 - 修复mock配置
    mock_actor = Mock()
    # 正确设置bounds mock
    mock_min_point = Mock()
    mock_min_point.getZ.return_value = -0.5  # 模型底部在地面下
    mock_max_point = Mock()
    mock_max_point.getZ.return_value = 2.0
    mock_actor.getTightBounds.return_value = (mock_min_point, mock_max_point)
    mock_actor.getPos.return_value = Vec3(0, 0, 1.0)
    
    # 创建Player
    player = Player(mock_render, mock_loader, name="Test Player", 
                   actor_instance=mock_actor, pos=Vec3(0, 0, 0))
    
    # 确保node被正确设置
    player.node = mock_actor
    
    # 测试地面接触调整
    player._ensure_ground_contact()
    
    # 验证位置调整被调用（由于模型底部在-0.5，地面在0，应该调整）
    mock_actor.setPos.assert_called()
    
    print("✅ 3D character ground positioning test passed")

def test_keyboard_input_handling():
    """测试键盘输入处理"""
    from player import Player
    from panda3d.core import Vec3
    
    # 模拟render和loader
    mock_render = Mock()
    mock_loader = Mock()
    
    # 模拟3D模型节点
    mock_node = Mock()
    mock_node.setPos = Mock()
    
    # 创建Player
    player = Player(mock_render, mock_loader, name="Test Player", pos=Vec3(0, 0, 0))
    player.node = mock_node
    
    # 测试输入应用
    inputs = {
        'left': True,
        'right': False,
        'up': False,
        'down': False,
        'light': False,
        'heavy': False,
        'jump': False
    }
    
    initial_pos = Vec3(player.pos)
    player.apply_input(inputs, 0.016)  # 60fps 时间步长
    
    # 验证位置改变
    assert player.pos.x < initial_pos.x  # 向左移动
    
    # 调用update确保3D模型位置同步
    player.update(0.016)
    
    # 验证3D模型位置更新
    mock_node.setPos.assert_called()
    
    print("✅ Keyboard input handling test passed")

def test_create_character_model_method():
    """测试create_character_model方法存在"""
    from enhanced_character_manager import EnhancedCharacterManager
    
    # 模拟应用
    mock_app = Mock()
    mock_app.render = Mock()
    mock_app.loader = Mock()
    
    char_manager = EnhancedCharacterManager(mock_app)
    
    # 验证方法存在
    assert hasattr(char_manager, 'create_character_model')
    assert callable(char_manager.create_character_model)
    
    print("✅ create_character_model method test passed")

def run_all_tests():
    """运行所有测试"""
    print("🧪 Running 3D Mode Fixes Tests...")
    print("=" * 50)
    
    try:
        test_audio_bgm_loading()
        test_audio_sfx_loading()
        test_3d_character_scaling()
        test_3d_character_ground_positioning()
        test_keyboard_input_handling()
        test_create_character_model_method()
        
        print("=" * 50)
        print("🎉 All 3D mode fixes tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)