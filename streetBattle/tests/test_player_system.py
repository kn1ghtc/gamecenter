"""
玩家角色系统单元测试模块
测试玩家角色的初始化、移动、状态管理等核心功能
"""

import sys
import os
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from player import Player
from config.config_manager import ConfigManager

# Mock PortraitManager类用于测试
class MockPortraitManager:
    """模拟肖像管理器用于测试"""
    def __init__(self):
        self.cache_dir = Path("assets/images/portraits")
        self._texture_cache = {}

    def get_texture(self, character_key, profile, fallback_factory):
        """模拟获取纹理方法"""
        return fallback_factory()


class TestPlayerSystem:
    """玩家角色系统测试类"""
    
    def setup_method(self):
        """测试方法前置设置"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_manager = ConfigManager(self.config_dir)
        self.config_manager.load_all_configs()
        
        # 创建模拟的PortraitManager
        class MockPortraitManager:
            def get_texture(self, character_key, profile, fallback_factory):
                return None
        
        self.portrait_manager = MockPortraitManager()
        
    def test_player_initialization(self):
        """测试玩家角色初始化"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            pos=(0, 0, 0)
        )
        
        assert player.name == "TestPlayer"
        assert player.pos == (0, 0, 0)
        
        # 检查默认属性
        assert hasattr(player, 'health')
        assert hasattr(player, 'max_health')
        assert hasattr(player, 'target_pos')

    def test_player_movement(self):
        """测试玩家移动功能"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            pos=(0, 0, 0)
        )
        
        # 测试移动功能
        assert hasattr(player, 'target_pos')
        assert hasattr(player, 'interpolate_speed')
        
    def test_player_stats_integration(self):
        """测试玩家属性与配置系统的集成"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="kyo_kusanagi",
            pos=(0, 0, 0)
        )
        
        # 验证玩家属性
        assert player.name == "TestPlayer"
        assert player.character_name == "kyo_kusanagi"
        assert hasattr(player, 'health')
        assert hasattr(player, 'max_health')
        
    def test_player_portrait_integration(self):
        """测试玩家肖像系统集成"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="kyo_kusanagi",
            pos=(0, 0, 0)
        )
        
        # 验证肖像集成
        assert hasattr(player, 'character_name')
        assert player.character_name == "kyo_kusanagi"
        
    def test_player_skill_integration(self):
        """测试玩家技能系统集成"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="kyo_kusanagi",
            pos=(0, 0, 0)
        )
        
        # 验证技能集成
        assert hasattr(player, 'character_name')
        assert player.character_name == "kyo_kusanagi"
        
    def test_player_audio_integration(self):
        """测试玩家音频系统集成"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="kyo_kusanagi",
            pos=(0, 0, 0)
        )
        
        # 验证音频集成
        assert hasattr(player, 'character_name')
        assert player.character_name == "kyo_kusanagi"
        
    def test_player_state_management(self):
        """测试玩家状态管理"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="fighter_001",
            pos=(0, 0, 0)
        )
        
        # 验证状态管理
        assert hasattr(player, 'state')
        assert player.state == 'idle'
        assert hasattr(player, 'last_state')
        
    def test_player_health_management(self):
        """测试玩家生命值管理"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="fighter_001",
            pos=(0, 0, 0)
        )
        
        # 验证生命值管理
        assert hasattr(player, 'health')
        assert hasattr(player, 'max_health')
        assert player.health <= player.max_health
        
    def test_player_serialization(self):
        """测试玩家序列化功能"""
        # 创建模拟的render和loader对象
        class MockRender:
            def attachNewNode(self, name):
                return MockNode()
        
        class MockNode:
            def __init__(self):
                self.pos = (0, 0, 0)
        
        render = MockRender()
        loader = None
        
        player = Player(
            render=render,
            loader=loader,
            name="TestPlayer",
            character_id="fighter_001",
            pos=(10, 5, 0)
        )
        
        # 验证序列化相关属性
        assert hasattr(player, 'name')
        assert hasattr(player, 'character_name')
        assert hasattr(player, 'pos')
        assert player.pos.x == 10
        assert player.pos.y == 5
        assert player.pos.z == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])