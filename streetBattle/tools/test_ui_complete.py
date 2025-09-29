#!/usr/bin/env python3
"""
StreetBattle Character Selection UI Test
验证角色选择界面的完整性测试
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_unified_character_list():
    """测试统一角色列表"""
    print("📋 测试统一角色列表")
    print("=" * 30)
    
    unified_list_path = project_root / "assets" / "unified_character_list.json"
    
    if not unified_list_path.exists():
        print(f"❌ 统一角色列表不存在: {unified_list_path}")
        return False
    
    try:
        with open(unified_list_path, 'r', encoding='utf-8') as f:
            unified_characters = json.load(f)
        
        print(f"✓ 统一角色列表加载成功，包含 {len(unified_characters)} 个角色")
        
        # 验证数据结构
        required_fields = ['display_name', 'portrait_path', 'has_portrait', 'sprite_path', 'has_sprite']
        issues = []
        
        for char_id, char_info in unified_characters.items():
            for field in required_fields:
                if field not in char_info:
                    issues.append(f"角色 {char_id} 缺少字段: {field}")
            
            # 验证头像文件存在性
            if char_info.get('has_portrait') and char_info.get('portrait_path'):
                portrait_path = project_root / char_info['portrait_path']
                if not portrait_path.exists():
                    issues.append(f"角色 {char_id} 头像文件不存在: {portrait_path}")
        
        if issues:
            print(f"⚠️ 发现 {len(issues)} 个问题:")
            for issue in issues[:10]:  # 只显示前10个问题
                print(f"  - {issue}")
            if len(issues) > 10:
                print(f"  ... 还有 {len(issues) - 10} 个问题")
        else:
            print("✓ 统一角色列表验证通过")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ 统一角色列表测试失败: {e}")
        return False

def test_portrait_resources():
    """测试头像资源"""
    print("\n🎨 测试头像资源")
    print("=" * 30)
    
    # 实际的头像在assets目录下
    portraits_dir = project_root / "assets" / "images" / "portraits"
    
    if not portraits_dir.exists():
        print(f"❌ 头像目录不存在: {portraits_dir}")
        return False
    
    # 统计头像文件
    portrait_files = list(portraits_dir.glob("*_portrait.png"))
    
    print(f"✓ 头像目录存在，包含 {len(portrait_files)} 个头像文件")
    
    # 验证文件大小
    size_issues = []
    for portrait_file in portrait_files:
        size = portrait_file.stat().st_size
        if size < 1000:  # 小于1KB可能有问题
            size_issues.append(f"{portrait_file.name}: {size} bytes")
    
    if size_issues:
        print(f"⚠️ 发现 {len(size_issues)} 个异常小的头像文件:")
        for issue in size_issues[:5]:
            print(f"  - {issue}")
    else:
        print("✓ 头像文件大小验证通过")
    
    return len(size_issues) == 0

def test_path_format_fixer():
    """测试路径格式修复器"""
    print("\n🛤️ 测试路径格式修复器")
    print("=" * 30)
    
    path_fixer_file = project_root / "tools" / "panda3d_path_fixer.py"
    
    if not path_fixer_file.exists():
        print(f"❌ 路径修复器不存在: {path_fixer_file}")
        return False
    
    try:
        # 导入路径修复模块
        sys.path.insert(0, str(project_root / "tools"))
        from panda3d_path_fixer import normalize_path_for_panda3d
        
        # 测试路径标准化
        test_paths = [
            "D:\\pyproject\\gamecenter\\streetBattle\\portraits\\ryu_portrait.png",
            "portraits/ryu_portrait.png",
            "./assets/sprites/ryu.png",
            "C:/Windows/System32/test.dll"
        ]
        
        print("✓ 路径标准化测试:")
        for path in test_paths:
            normalized = normalize_path_for_panda3d(path)
            print(f"  {path} -> {normalized}")
        
        print("✓ 路径格式修复器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 路径格式修复器测试失败: {e}")
        return False

def test_character_selector_imports():
    """测试角色选择器导入"""
    print("\n🎭 测试角色选择器导入")
    print("=" * 30)
    
    selector_file = project_root / "character_selector.py"
    
    if not selector_file.exists():
        print(f"❌ 角色选择器文件不存在: {selector_file}")
        return False
    
    try:
        with open(selector_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键导入
        required_imports = [
            'safe_load_texture',
            'normalize_path_for_panda3d',
            'unified_character_list.json'
        ]
        
        issues = []
        for import_item in required_imports:
            if import_item not in content:
                issues.append(f"缺少导入或引用: {import_item}")
        
        if issues:
            print(f"⚠️ 发现 {len(issues)} 个导入问题:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ 角色选择器导入验证通过")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ 角色选择器导入测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告")
    print("=" * 30)
    
    report = {
        "test_time": str(Path().resolve()),
        "results": {}
    }
    
    # 运行所有测试
    tests = [
        ("unified_character_list", test_unified_character_list),
        ("portrait_resources", test_portrait_resources),
        ("path_format_fixer", test_path_format_fixer),
        ("character_selector_imports", test_character_selector_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            report["results"][test_name] = {
                "passed": result,
                "error": None
            }
            if result:
                passed += 1
        except Exception as e:
            report["results"][test_name] = {
                "passed": False,
                "error": str(e)
            }
    
    # 保存报告
    report_file = project_root / "tools" / "ui_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 测试报告已保存: {report_file}")
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    return passed == total

def main():
    """主函数"""
    print("🧪 StreetBattle角色选择UI测试")
    print("=" * 50)
    
    try:
        success = generate_test_report()
        
        if success:
            print("\n🎉 所有测试通过!")
            print("\n✅ UI系统准备就绪:")
            print("  ✓ 统一角色列表正常")
            print("  ✓ 头像资源完整")
            print("  ✓ 路径格式修复器工作正常")
            print("  ✓ 角色选择器导入正确")
        else:
            print("\n⚠️ 部分测试未通过，请检查问题并修复")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
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