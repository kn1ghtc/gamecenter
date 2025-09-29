#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprite System Tests
测试2.5D精灵系统功能
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from sprite_system import SpriteSystem, SpriteCharacter
    from sprite_animation_generator import SpriteAnimationGenerator
    from panda3d.core import Vec3
    from direct.showbase.ShowBase import ShowBase
    from direct.task.TaskManagerGlobal import taskMgr
    from direct.showbase.Loader import Loader
    from panda3d.core import NodePath
    
    # 创建模拟的base_app对象
    class MockBaseApp:
        def __init__(self):
            self.render = NodePath("render")
            self.taskMgr = taskMgr
            self.loader = Loader(self)
            
            # 设置必要的属性
            self.render.setPythonTag("taskMgr", taskMgr)
            
    mock_app = MockBaseApp()
    
except ImportError as e:
    print(f"⚠️ 导入模块失败: {e}")
    SpriteSystem = None
    SpriteCharacter = None 
    SpriteAnimationGenerator = None
    mock_app = None


class TestSpriteSystem:
    """测试精灵系统核心功能"""
    
    def test_sprite_system_creation(self):
        """测试精灵系统创建"""
        if SpriteSystem is None or mock_app is None:
            pytest.skip("模块导入失败，跳过测试")
            
        try:
            sprite_system = SpriteSystem(mock_app)
            assert sprite_system is not None
            assert hasattr(sprite_system, 'characters')
            assert isinstance(sprite_system.characters, dict)
            print("✅ 精灵系统创建成功")
        except Exception as e:
            pytest.fail(f"精灵系统创建失败: {e}")
    
    def test_character_loading(self):
        """测试角色精灵加载"""
        if SpriteSystem is None or mock_app is None:
            pytest.skip("模块导入失败，跳过测试")
            
        sprite_system = SpriteSystem(mock_app)
        test_character = "ryu"  # 使用一个应该存在的角色
        
        try:
            # 检查角色精灵目录是否存在
            sprites_dir = Path("assets/sprites")
            char_dir = sprites_dir / test_character
            
            if char_dir.exists():
                # 创建SpriteCharacter需要正确的参数
                pos = Vec3(0, 0, 0)
                sprite_char = sprite_system.create_sprite_character(test_character, test_character, pos)
                assert sprite_char is not None
                assert isinstance(sprite_char, SpriteCharacter)
                print(f"✅ 角色 {test_character} 加载成功")
            else:
                print(f"⚠️ 角色 {test_character} 精灵目录不存在，跳过测试")
                
        except Exception as e:
            pytest.fail(f"角色加载失败: {e}")
    
    def test_animation_manifest_loading(self):
        """测试动画清单加载"""
        if SpriteCharacter is None or mock_app is None:
            pytest.skip("模块导入失败，跳过测试")
            
        sprites_dir = Path("assets/sprites")
        if not sprites_dir.exists():
            pytest.skip("精灵目录不存在")
        
        # 检查至少一个角色的manifest文件
        for char_dir in sprites_dir.iterdir():
            if char_dir.is_dir():
                manifest_file = char_dir / "manifest.json"
                if manifest_file.exists():
                    # 创建SpriteCharacter需要正确的参数
                    pos = Vec3(0, 0, 0)
                    sprite_char = SpriteCharacter(char_dir.name, str(char_dir), pos, mock_app.render, mock_app.loader)
                    assert hasattr(sprite_char, 'animations')
                    print(f"✅ 角色 {char_dir.name} 动画清单加载成功")
                    return
        
        pytest.skip("没有找到有效的角色动画清单")


class TestSpriteAnimationGenerator:
    """测试精灵动画生成器"""
    
    def test_generator_creation(self):
        """测试生成器创建"""
        if SpriteAnimationGenerator is None:
            pytest.skip("模块导入失败，跳过测试")
            
        try:
            generator = SpriteAnimationGenerator()
            assert generator is not None
            assert hasattr(generator, 'portraits_dir')  # 修复：portrait_dir -> portraits_dir
            assert hasattr(generator, 'sprites_dir')    # 修复：output_dir -> sprites_dir
            print("✅ 精灵动画生成器创建成功")
        except Exception as e:
            pytest.fail(f"生成器创建失败: {e}")
    
    def test_character_list_loading(self):
        """测试角色列表加载"""
        if SpriteAnimationGenerator is None:
            pytest.skip("模块导入失败，跳过测试")
            
        generator = SpriteAnimationGenerator()
        portraits_dir = generator.portraits_dir  # 修复：直接使用属性
        
        if portraits_dir.exists():
            characters = generator.characters  # 修复：使用characters属性而不是get_character_list方法
            assert isinstance(characters, list)
            assert len(characters) > 0
            print(f"✅ 加载了 {len(characters)} 个角色")
        else:
            pytest.skip("头像目录不存在")


class TestIntegration:
    """集成测试"""
    
    def test_sprite_generation_and_loading(self):
        """测试精灵生成和加载集成"""
        if SpriteSystem is None or mock_app is None:
            pytest.skip("模块导入失败，跳过测试")
            
        # 检查是否有生成的精灵文件
        sprites_dir = Path("assets/sprites")
        if not sprites_dir.exists():
            pytest.skip("精灵目录不存在")
        
        sprite_system = SpriteSystem(mock_app)
        loaded_count = 0
        
        for char_dir in sprites_dir.iterdir():
            if char_dir.is_dir():
                try:
                    pos = Vec3(0, 0, 0)
                    sprite_char = sprite_system.create_sprite_character(char_dir.name, char_dir.name, pos)
                    if sprite_char:
                        loaded_count += 1
                except Exception as e:
                    print(f"⚠️ 角色 {char_dir.name} 加载失败: {e}")
        
        print(f"✅ 成功加载 {loaded_count} 个角色精灵")
        assert loaded_count > 0, "至少应该加载一个角色精灵"


def test_file_structure():
    """测试文件结构完整性"""
    required_files = [
        "sprite_system.py",
        "sprite_animation_generator.py",
        "assets/images/portraits",
        "assets/sprites"
    ]
    
    project_root = Path(__file__).resolve().parent.parent

    for file_path in required_files:
        candidate_path = project_root / file_path
        expected_directory = Path(file_path).suffix == ""

        if expected_directory:
            assert candidate_path.is_dir(), f"目录不存在: {file_path}"
        else:
            assert candidate_path.exists(), f"文件不存在: {file_path}"
    
    print("✅ 所有必需的文件和目录都存在")


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])