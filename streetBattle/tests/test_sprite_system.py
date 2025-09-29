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
except ImportError as e:
    print(f"⚠️ 导入模块失败: {e}")
    SpriteSystem = None
    SpriteCharacter = None 
    SpriteAnimationGenerator = None


class TestSpriteSystem:
    """测试精灵系统核心功能"""
    
    def test_sprite_system_creation(self):
        """测试精灵系统创建"""
        try:
            sprite_system = SpriteSystem()
            assert sprite_system is not None
            assert hasattr(sprite_system, 'characters')
            assert isinstance(sprite_system.characters, dict)
            print("✅ 精灵系统创建成功")
        except Exception as e:
            pytest.fail(f"精灵系统创建失败: {e}")
    
    def test_character_loading(self):
        """测试角色精灵加载"""
        sprite_system = SpriteSystem()
        test_character = "ryu"  # 使用一个应该存在的角色
        
        try:
            # 检查角色精灵目录是否存在
            sprites_dir = Path("assets/sprites")
            char_dir = sprites_dir / test_character
            
            if char_dir.exists():
                sprite_char = sprite_system.create_character(test_character)
                assert sprite_char is not None
                assert isinstance(sprite_char, SpriteCharacter)
                print(f"✅ 角色 {test_character} 加载成功")
            else:
                print(f"⚠️ 角色 {test_character} 精灵目录不存在，跳过测试")
                
        except Exception as e:
            pytest.fail(f"角色加载失败: {e}")
    
    def test_animation_manifest_loading(self):
        """测试动画清单加载"""
        sprites_dir = Path("assets/sprites")
        if not sprites_dir.exists():
            pytest.skip("精灵目录不存在")
        
        # 检查至少一个角色的manifest文件
        for char_dir in sprites_dir.iterdir():
            if char_dir.is_dir():
                manifest_file = char_dir / "manifest.json"
                if manifest_file.exists():
                    sprite_char = SpriteCharacter(char_dir.name, str(char_dir))
                    assert hasattr(sprite_char, 'animations')
                    print(f"✅ 角色 {char_dir.name} 动画清单加载成功")
                    return
        
        pytest.skip("没有找到有效的角色动画清单")


class TestSpriteAnimationGenerator:
    """测试精灵动画生成器"""
    
    def test_generator_creation(self):
        """测试生成器创建"""
        try:
            generator = SpriteAnimationGenerator()
            assert generator is not None
            assert hasattr(generator, 'portrait_dir')
            assert hasattr(generator, 'output_dir')
            print("✅ 精灵动画生成器创建成功")
        except Exception as e:
            pytest.fail(f"生成器创建失败: {e}")
    
    def test_character_list_loading(self):
        """测试角色列表加载"""
        generator = SpriteAnimationGenerator()
        portraits_dir = Path(generator.portrait_dir)
        
        if portraits_dir.exists():
            characters = generator.get_character_list()
            assert isinstance(characters, list)
            assert len(characters) > 0
            print(f"✅ 加载了 {len(characters)} 个角色")
        else:
            pytest.skip("头像目录不存在")


class TestIntegration:
    """集成测试"""
    
    def test_sprite_generation_and_loading(self):
        """测试精灵生成和加载集成"""
        # 检查是否有生成的精灵文件
        sprites_dir = Path("assets/sprites")
        if not sprites_dir.exists():
            pytest.skip("精灵目录不存在")
        
        sprite_system = SpriteSystem()
        loaded_count = 0
        
        for char_dir in sprites_dir.iterdir():
            if char_dir.is_dir():
                try:
                    sprite_char = sprite_system.create_character(char_dir.name)
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
    
    for file_path in required_files:
        path = Path(file_path)
        if file_path.endswith('/'):
            assert path.is_dir(), f"目录不存在: {file_path}"
        else:
            assert path.exists(), f"文件不存在: {file_path}"
    
    print("✅ 所有必需的文件和目录都存在")


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v"])