#!/usr/bin/env python3
"""
2.5D模式启动测试脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
streetbattle_root = Path(__file__).resolve().parent.parent  # streetBattle目录
project_root = streetbattle_root.parent  # gamecenter目录
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(streetbattle_root))

# 切换到正确的工作目录
os.chdir(streetbattle_root)

def test_2d5_mode():
    """测试2.5D模式启动"""
    print("=== 2.5D模式启动测试 ===")
    print(f"工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")
    
    try:
        # 导入pygame检查
        import pygame
        print(f"✓ Pygame版本: {pygame.version.ver}")
        
        # 导入配置管理器
        from gamecenter.streetBattle.config import SettingsManager
        print("✓ 配置管理器导入成功")
        
        # 导入2.5D游戏类
        from gamecenter.streetBattle.twod5.game import SpriteBattleGame
        print("✓ 2.5D游戏类导入成功")
        
        # 创建游戏实例
        settings_manager = SettingsManager()
        game = SpriteBattleGame(settings_manager)
        print("✓ 游戏实例创建成功")
        
        # 检查角色配置
        print(f"✓ 角色列表: {len(game.roster_order)} 个角色")
        if game.roster_order:
            print(f"  前5个角色: {game.roster_order[:5]}")
        
        # 检查精灵资源
        sprites_dir = Path("assets/sprites")
        if sprites_dir.exists():
            sprite_chars = [d.name for d in sprites_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            print(f"✓ 精灵资源: {len(sprite_chars)} 个角色目录")
            if sprite_chars:
                print(f"  前5个: {sprite_chars[:5]}")
        else:
            print("✗ 精灵资源目录不存在")
        
        print("\n🎉 2.5D模式基础检查通过!")
        return True
        
    except ImportError as e:
        print(f"✗ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sprite_loading():
    """测试精灵资源加载"""
    print("\n=== 精灵资源加载测试 ===")
    
    try:
        from gamecenter.streetBattle.twod5.sprites import load_sprite_animations, SPRITE_ASSET_ROOT
        print(f"✓ 精灵加载模块导入成功")
        print(f"✓ 精灵资源根目录: {SPRITE_ASSET_ROOT}")
        
        # 尝试加载一个角色的精灵动画
        test_chars = ['kyo_kusanagi', 'terry_bogard', 'hero', 'shadow']
        loaded_char = None
        
        for char in test_chars:
            char_dir = SPRITE_ASSET_ROOT / char
            if char_dir.exists():
                manifest_file = char_dir / "manifest.json"
                if manifest_file.exists():
                    print(f"✓ 找到角色 {char} 的manifest文件")
                    
                    # 尝试加载动画
                    result = load_sprite_animations(char)
                    if result:
                        animations, metadata = result
                        print(f"✓ 成功加载 {char} 的动画: {list(animations.keys())}")
                        loaded_char = char
                        break
                    else:
                        print(f"✗ 加载 {char} 的动画失败")
                else:
                    print(f"✗ {char} 缺少manifest.json文件")
            else:
                print(f"✗ {char} 目录不存在")
        
        if loaded_char:
            print(f"🎉 精灵资源加载测试通过! (测试角色: {loaded_char})")
            return True
        else:
            print("⚠️  未找到可用的精灵资源")
            return False
            
    except Exception as e:
        print(f"✗ 精灵加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """测试UI组件"""
    print("\n=== UI组件测试 ===")
    
    try:
        from gamecenter.streetBattle.twod5.ui import HudRenderer, MatchSetupScreen
        print("✓ UI组件导入成功")
        
        # 测试HUD渲染器
        hud = HudRenderer(1280, 720, 600)
        print("✓ HUD渲染器创建成功")
        
        print("🎉 UI组件测试通过!")
        return True
        
    except Exception as e:
        print(f"✗ UI组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始2.5D模式诊断测试...\n")
    
    success_count = 0
    total_tests = 3
    
    if test_2d5_mode():
        success_count += 1
    
    if test_sprite_loading():
        success_count += 1
        
    if test_ui_components():
        success_count += 1
    
    print(f"\n=== 测试完成 ===")
    print(f"通过: {success_count}/{total_tests} 项测试")
    
    if success_count == total_tests:
        print("🎉 所有测试通过! 2.5D模式应该可以正常启动")
        
        # 尝试实际启动游戏（但不进入主循环）
        try:
            print("\n尝试启动2.5D模式...")
            from gamecenter.streetBattle.config import SettingsManager
            from gamecenter.streetBattle.twod5.game import SpriteBattleGame
            
            settings_manager = SettingsManager()
            game = SpriteBattleGame(settings_manager)
            game._boot_display()
            
            if game.screen is not None:
                print("✓ 显示初始化成功")
                # 立即退出，不进入游戏循环
                import pygame
                pygame.quit()
                print("✓ 2.5D模式启动测试完全成功!")
            else:
                print("✗ 显示初始化失败")
                
        except Exception as e:
            print(f"✗ 实际启动测试失败: {e}")
    else:
        print("⚠️  存在问题，需要进一步修复")

if __name__ == "__main__":
    main()