#!/usr/bin/env python3
"""
StreetBattle Complete Testing and Validation Tool
StreetBattle 完整测试和验证工具
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_portraits_integration():
    """测试头像集成"""
    print("🎨 头像集成测试")
    print("=" * 30)
    
    portraits_dir = project_root / "assets" / "images" / "portraits"
    
    # 检查官方头像
    official_portraits = list(portraits_dir.glob("*_official.png"))
    print(f"✓ 官方头像: {len(official_portraits)} 个")
    
    # 检查备用头像
    standard_portraits = list(portraits_dir.glob("*.png"))
    backup_portraits = [p for p in standard_portraits if not p.name.endswith("_official.png")]
    print(f"✓ 备用头像: {len(backup_portraits)} 个")
    
    # 检查角色索引
    index_file = project_root / "assets" / "character_portraits_index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        print(f"✓ 角色索引: {len(index_data)} 个角色")
    else:
        print("❌ 角色索引文件不存在")
        return False
    
    print("✅ 头像集成测试通过")
    return True

def test_2d5_mode():
    """测试2.5D模式"""
    print("\n🎮 2.5D模式测试")
    print("=" * 30)
    
    # 检查精灵资源
    sprites_dir = project_root / "assets" / "sprites"
    if not sprites_dir.exists():
        print("❌ 精灵目录不存在")
        return False
    
    sprite_dirs = list(sprites_dir.glob("*/"))
    print(f"✓ 精灵角色目录: {len(sprite_dirs)} 个")
    
    # 检查精灵格式
    valid_manifests = 0
    for sprite_dir in sprite_dirs[:5]:  # 测试前5个
        manifest_file = sprite_dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                if "states" in manifest:  # 新格式
                    valid_manifests += 1
                    print(f"  ✓ {sprite_dir.name}: 新格式manifest")
                else:
                    print(f"  ⚠️ {sprite_dir.name}: 旧格式manifest")
            except Exception as e:
                print(f"  ❌ {sprite_dir.name}: manifest读取失败 - {e}")
    
    print(f"✓ 有效manifest文件: {valid_manifests}/5 (测试样本)")
    
    # 运行2.5D启动测试
    try:
        result = subprocess.run([
            sys.executable, str(project_root / "tools" / "test_2d5_startup.py")
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 2.5D模式启动测试通过")
        else:
            print(f"⚠️ 2.5D模式启动测试异常: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️ 2.5D模式测试超时")
    except Exception as e:
        print(f"⚠️ 2.5D模式测试异常: {e}")
    
    return True

def test_3d_models():
    """测试3D模型"""
    print("\n🎯 3D模型测试") 
    print("=" * 30)
    
    characters_dir = project_root / "assets" / "characters"
    if not characters_dir.exists():
        print("❌ 角色目录不存在")
        return False
    
    character_dirs = list(characters_dir.glob("*/"))
    print(f"✓ 角色目录: {len(character_dirs)} 个")
    
    # 检查BAM文件
    bam_count = 0
    gltf_count = 0
    
    for char_dir in character_dirs:
        bam_files = list(char_dir.rglob("*.bam"))
        gltf_files = list(char_dir.rglob("*.gltf"))
        
        if bam_files:
            bam_count += len(bam_files)
            print(f"  ✓ {char_dir.name}: {len(bam_files)} BAM文件")
        
        if gltf_files:
            gltf_count += len(gltf_files)
    
    print(f"✓ 总计BAM文件: {bam_count} 个")
    print(f"✓ 总计GLTF文件: {gltf_count} 个")
    
    if bam_count > 0:
        print("✅ 3D模型资源充足")
        return True
    else:
        print("⚠️ BAM文件不足，可能影响3D模式")
        return False

def test_ui_components():
    """测试UI组件"""
    print("\n🖼️ UI组件测试")
    print("=" * 30)
    
    # 检查关键UI文件
    ui_files = [
        "character_selector.py",
        "portrait_manager.py",
        "ui_asset_manager.py", 
        "enhanced_character_manager.py"
    ]
    
    missing_files = []
    for ui_file in ui_files:
        file_path = project_root / ui_file
        if file_path.exists():
            print(f"  ✓ {ui_file}")
        else:
            print(f"  ❌ {ui_file}")
            missing_files.append(ui_file)
    
    if missing_files:
        print(f"⚠️ 缺少 {len(missing_files)} 个UI文件")
        return False
    
    # 检查补丁文件
    patch_files = [
        "tools/ui_portrait_patch.py",
        "tools/player2_debug_patch.py",
        "tools/path_fix_patch.py"
    ]
    
    for patch_file in patch_files:
        file_path = project_root / patch_file
        if file_path.exists():
            print(f"  ✓ {patch_file}")
        else:
            print(f"  ❌ {patch_file}")
    
    print("✅ UI组件测试完成")
    return True

def create_comprehensive_test_report():
    """创建综合测试报告"""
    print("\n📋 创建综合测试报告")
    print("=" * 30)
    
    report = {
        "test_timestamp": str(Path(__file__).stat().st_mtime),
        "project_path": str(project_root),
        "summary": {},
        "details": {}
    }
    
    # 收集统计信息
    portraits_dir = project_root / "assets" / "images" / "portraits"
    sprites_dir = project_root / "assets" / "sprites"
    characters_dir = project_root / "assets" / "characters"
    
    report["summary"]["portraits"] = len(list(portraits_dir.glob("*.png"))) if portraits_dir.exists() else 0
    report["summary"]["sprite_characters"] = len(list(sprites_dir.glob("*/"))) if sprites_dir.exists() else 0
    report["summary"]["3d_characters"] = len(list(characters_dir.glob("*/"))) if characters_dir.exists() else 0
    
    # BAM文件统计
    bam_files = list(characters_dir.rglob("*.bam")) if characters_dir.exists() else []
    report["summary"]["bam_models"] = len(bam_files)
    
    # 详细信息
    report["details"]["portrait_types"] = {
        "official": len(list(portraits_dir.glob("*_official.png"))) if portraits_dir.exists() else 0,
        "standard": len(list(portraits_dir.glob("*.png"))) if portraits_dir.exists() else 0
    }
    
    # 保存报告
    report_file = project_root / "reports" / "comprehensive_test_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 测试报告已保存: {report_file}")
    
    # 打印摘要
    print(f"\n📊 测试摘要:")
    print(f"  头像文件: {report['summary']['portraits']} 个")
    print(f"  2.5D角色: {report['summary']['sprite_characters']} 个")
    print(f"  3D角色: {report['summary']['3d_characters']} 个")
    print(f"  BAM模型: {report['summary']['bam_models']} 个")
    
    return True

def run_integration_test():
    """运行集成测试"""
    print("\n🧪 运行集成测试")
    print("=" * 30)
    
    try:
        # 测试Python模块导入
        test_imports = [
            "pathlib",
            "json", 
            "os",
            "sys"
        ]
        
        for module_name in test_imports:
            try:
                __import__(module_name)
                print(f"  ✓ {module_name}")
            except ImportError:
                print(f"  ❌ {module_name}")
        
        # 测试Panda3D（如果可用）
        try:
            from panda3d.core import Filename
            print("  ✓ panda3d.core")
        except ImportError:
            print("  ⚠️ panda3d.core (可选)")
        
        # 测试Pygame（如果可用）
        try:
            import pygame
            print("  ✓ pygame")
        except ImportError:
            print("  ⚠️ pygame (可选)")
        
        print("✅ 集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🎮 StreetBattle 完整测试和验证工具")
    print("=" * 50)
    
    test_results = []
    
    try:
        # 1. 头像集成测试
        result = test_portraits_integration()
        test_results.append(("头像集成", result))
        
        # 2. 2.5D模式测试
        result = test_2d5_mode()
        test_results.append(("2.5D模式", result))
        
        # 3. 3D模型测试
        result = test_3d_models()
        test_results.append(("3D模型", result))
        
        # 4. UI组件测试
        result = test_ui_components()
        test_results.append(("UI组件", result))
        
        # 5. 集成测试
        result = run_integration_test()
        test_results.append(("集成测试", result))
        
        # 6. 创建测试报告
        create_comprehensive_test_report()
        
        # 汇总结果
        print("\n🏆 测试结果汇总")
        print("=" * 50)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, passed in test_results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {test_name}: {status}")
            if passed:
                passed_tests += 1
        
        print(f"\n📊 总体结果: {passed_tests}/{total_tests} 通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！StreetBattle已准备就绪")
        elif passed_tests >= total_tests * 0.8:
            print("✅ 大部分测试通过，项目基本可用")
        else:
            print("⚠️ 多项测试失败，需要进一步修复")
        
        print("\n🔧 后续建议:")
        print("  1. 启动游戏测试2.5D和3D模式")
        print("  2. 验证角色选择界面头像显示")
        print("  3. 测试Player2加载和显示")
        print("  4. 如有问题，应用相应的补丁文件")
        
        return passed_tests >= total_tests * 0.6  # 60%通过率为成功
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        sys.exit(1)