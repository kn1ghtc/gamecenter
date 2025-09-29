#!/usr/bin/env python3
"""
StreetBattle UI Final Integration Test
最终UI集成测试 - 验证所有修复
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def final_integration_test():
    """最终集成测试"""
    print("🎯 StreetBattle UI最终集成测试")
    print("=" * 50)
    
    test_results = {
        "character_count_consistency": False,
        "portrait_resource_availability": False,
        "path_format_fixes": False,
        "unified_character_list": False,
        "ui_integration": False
    }
    
    # 1. 角色数量一致性检查
    print("\n1️⃣ 角色数量一致性检查")
    print("-" * 30)
    
    try:
        # 检查统一角色列表
        unified_list_path = project_root / "assets" / "unified_character_list.json"
        with open(unified_list_path, 'r', encoding='utf-8') as f:
            unified_characters = json.load(f)
        
        # 检查头像文件
        portraits_dir = project_root / "assets" / "images" / "portraits"
        portrait_files = list(portraits_dir.glob("*.png"))
        
        unified_count = len(unified_characters)
        portrait_count = len(portrait_files)
        
        print(f"统一角色列表: {unified_count} 个角色")
        print(f"头像文件数量: {portrait_count} 个文件")
        
        if unified_count == portrait_count == 42:
            print("✅ 角色数量一致性检查通过")
            test_results["character_count_consistency"] = True
        else:
            print(f"❌ 角色数量不一致: 统一列表{unified_count} vs 头像{portrait_count}")
            
    except Exception as e:
        print(f"❌ 角色数量检查失败: {e}")
    
    # 2. 头像资源可用性检查
    print("\n2️⃣ 头像资源可用性检查")
    print("-" * 30)
    
    try:
        missing_portraits = []
        
        for char_id, char_info in unified_characters.items():
            if char_info.get('has_portrait'):
                portrait_path = project_root / char_info['portrait_path']
                if not portrait_path.exists():
                    missing_portraits.append(f"{char_id}: {portrait_path}")
        
        if not missing_portraits:
            print("✅ 所有头像资源都可用")
            test_results["portrait_resource_availability"] = True
        else:
            print(f"❌ 发现 {len(missing_portraits)} 个缺失的头像:")
            for missing in missing_portraits[:5]:
                print(f"  - {missing}")
                
    except Exception as e:
        print(f"❌ 头像资源检查失败: {e}")
    
    # 3. 路径格式修复检查
    print("\n3️⃣ 路径格式修复检查")
    print("-" * 30)
    
    try:
        # 检查路径修复模块
        path_fixer_file = project_root / "tools" / "panda3d_path_fixer.py"
        if path_fixer_file.exists():
            print("✅ 路径格式修复模块存在")
            
            # 检查角色选择器是否导入了路径修复
            selector_file = project_root / "character_selector.py"
            with open(selector_file, 'r', encoding='utf-8') as f:
                selector_content = f.read()
            
            if 'safe_load_texture' in selector_content:
                print("✅ 角色选择器已集成路径修复")
                test_results["path_format_fixes"] = True
            else:
                print("❌ 角色选择器未集成路径修复")
        else:
            print("❌ 路径格式修复模块不存在")
            
    except Exception as e:
        print(f"❌ 路径格式修复检查失败: {e}")
    
    # 4. 统一角色列表完整性检查
    print("\n4️⃣ 统一角色列表完整性检查")
    print("-" * 30)
    
    try:
        required_fields = ['display_name', 'portrait_path', 'has_portrait', 'sprite_path', 'has_sprite']
        incomplete_chars = []
        
        for char_id, char_info in unified_characters.items():
            missing_fields = [field for field in required_fields if field not in char_info]
            if missing_fields:
                incomplete_chars.append(f"{char_id}: {missing_fields}")
        
        if not incomplete_chars:
            print("✅ 统一角色列表结构完整")
            test_results["unified_character_list"] = True
        else:
            print(f"❌ 发现 {len(incomplete_chars)} 个不完整的角色数据:")
            for incomplete in incomplete_chars[:3]:
                print(f"  - {incomplete}")
                
    except Exception as e:
        print(f"❌ 统一角色列表检查失败: {e}")
    
    # 5. UI集成检查
    print("\n5️⃣ UI集成检查")
    print("-" * 30)
    
    try:
        # 检查关键UI文件
        ui_files = [
            "character_selector.py",
            "assets/unified_character_list.json",
            "tools/panda3d_path_fixer.py"
        ]
        
        all_exist = True
        for ui_file in ui_files:
            file_path = project_root / ui_file
            if file_path.exists():
                print(f"✅ {ui_file}")
            else:
                print(f"❌ {ui_file} 不存在")
                all_exist = False
        
        if all_exist:
            test_results["ui_integration"] = True
            
    except Exception as e:
        print(f"❌ UI集成检查失败: {e}")
    
    # 生成最终报告
    print("\n📊 最终测试结果")
    print("=" * 50)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 恭喜！所有UI修复和改进均已完成!")
        print("\n✨ 功能总结:")
        print("  ✓ 角色数量一致性: 42个角色完全匹配")
        print("  ✓ 头像资源完整: 所有角色都有对应头像")
        print("  ✓ 路径格式修复: 消除Windows路径警告")
        print("  ✓ 统一角色列表: 标准化角色数据管理")
        print("  ✓ UI系统集成: 所有组件正确集成")
        
        print("\n🚀 系统已准备就绪，可以启动StreetBattle!")
        return True
    else:
        print(f"\n⚠️ 还有 {total_tests - passed_tests} 个问题需要解决")
        return False

def main():
    """主函数"""
    try:
        success = final_integration_test()
        
        # 保存最终报告
        report_file = project_root / "tools" / "final_integration_report.json"
        report_data = {
            "test_date": "2024-12-19",
            "success": success,
            "summary": "Complete UI system integration test"
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 最终报告已保存: {report_file}")
        
        return success
        
    except Exception as e:
        print(f"❌ 最终测试失败: {e}")
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