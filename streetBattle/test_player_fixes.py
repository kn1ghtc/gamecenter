#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Player创建修复
Test Player Creation Fixes
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_player_creation_fallback():
    """测试Player创建的fallback机制"""
    try:
        from player import Player
        from panda3d.core import Vec3
        
        # 模拟render和loader
        mock_render = Mock()
        mock_loader = Mock()
        
        # 测试基础Player创建（不使用3D模型）
        player = Player(mock_render, mock_loader, name="Test Player", pos=Vec3(0, 0, 0))
        
        # 验证基本属性
        assert player.name == "Test Player"
        assert player.pos.x == 0
        assert player.pos.y == 0
        assert player.pos.z == 0
        assert player.health > 0
        assert player.max_health > 0
        
        print("✅ Player creation fallback test passed")
        return True
        
    except Exception as e:
        print(f"❌ Player creation test failed: {e}")
        return False

def test_ground_contact_method():
    """测试地面接触方法不会引起错误"""
    try:
        from player import Player
        from panda3d.core import Vec3
        
        # 模拟render和loader
        mock_render = Mock()
        mock_loader = Mock()
        
        # 创建Player
        player = Player(mock_render, mock_loader, name="Test Player", pos=Vec3(0, 0, 0))
        
        # 测试地面接触方法（即使没有真实的3D模型也不应该崩溃）
        player._ensure_ground_contact()
        
        print("✅ Ground contact method test passed")
        return True
        
    except Exception as e:
        print(f"❌ Ground contact test failed: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🧪 Running Player Creation Fix Tests...")
    print("=" * 50)
    
    success = True
    
    success &= test_player_creation_fallback()
    success &= test_ground_contact_method()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed successfully!")
    else:
        print("❌ Some tests failed!")
    
    return success

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)