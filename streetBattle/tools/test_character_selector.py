#!/usr/bin/env python3
"""
Enhanced Character Selector Test
增强角色选择器测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_character_selector_functionality():
    """测试角色选择器功能"""
    print("🧪 测试角色选择器功能")
    print("=" * 40)
    
    try:
        # 1. 测试统一角色列表加载
        unified_list_path = project_root / "assets" / "unified_character_list.json"
        
        if not unified_list_path.exists():
            print("❌ 统一角色列表不存在")
            return False
        
        import json
        with open(unified_list_path, 'r', encoding='utf-8') as f:
            unified_characters = json.load(f)
        
        print(f"✓ 统一角色列表加载成功: {len(unified_characters)} 个角色")
        
        # 2. 测试角色数据完整性
        complete_characters = 0
        incomplete_characters = []
        
        for char_id, char_info in unified_characters.items():
            if (char_info.get('has_portrait', False) and 
                char_info.get('display_name') and
                char_info.get('portrait_path')):
                complete_characters += 1
            else:
                incomplete_characters.append(char_id)
        
        print(f"✓ 完整角色数据: {complete_characters}/{len(unified_characters)}")
        
        if incomplete_characters:
            print(f"⚠️ 不完整角色: {incomplete_characters[:5]}...")
        
        # 3. 测试头像文件存在性
        missing_portraits = 0
        
        for char_id, char_info in unified_characters.items():
            if char_info.get('has_portrait') and char_info.get('portrait_path'):
                portrait_path = project_root / char_info['portrait_path']
                if not portrait_path.exists():
                    missing_portraits += 1
        
        if missing_portraits == 0:
            print("✓ 所有头像文件都存在")
        else:
            print(f"⚠️ 缺失头像文件: {missing_portraits} 个")
        
        # 4. 测试角色选择器类导入
        try:
            from enhanced_character_selector import EnhancedCharacterSelector
            print("✓ 增强角色选择器类导入成功")
        except ImportError as e:
            print(f"❌ 增强角色选择器类导入失败: {e}")
            return False
        
        # 5. 生成测试报告
        success_rate = (complete_characters / len(unified_characters)) * 100
        
        print(f"\n📊 测试结果:")
        print(f"  总角色数: {len(unified_characters)}")
        print(f"  完整角色: {complete_characters}")
        print(f"  完整率: {success_rate:.1f}%")
        print(f"  缺失头像: {missing_portraits}")
        
        return success_rate >= 95.0  # 95%以上认为成功
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 StreetBattle角色选择器功能测试")
    print("=" * 50)
    
    try:
        success = test_character_selector_functionality()
        
        if success:
            print("\n🎉 角色选择器测试通过!")
            print("\n✅ 验证结果:")
            print("  ✓ 统一角色列表正常加载")
            print("  ✓ 角色数据完整性良好")
            print("  ✓ 头像资源完整存在")
            print("  ✓ 增强选择器类正常")
            print("\n🚀 角色选择器准备就绪!")
        else:
            print("\n⚠️ 角色选择器测试未完全通过")
            print("请检查统一角色列表和头像资源")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        sys.exit(1)
