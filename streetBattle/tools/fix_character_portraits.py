#!/usr/bin/env python3
"""
Character Selection UI Portrait Fix
简化版角色选择界面头像修复工具
"""

import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def fix_character_portraits():
    """修复角色头像显示问题"""
    print("🎨 角色头像修复工具")
    print("=" * 40)
    
    portraits_dir = project_root / "assets" / "images" / "portraits"
    
    if not portraits_dir.exists():
        print(f"❌ 头像目录不存在: {portraits_dir}")
        return False
    
    # 列出所有头像文件
    portrait_files = list(portraits_dir.glob("*_official.png"))
    print(f"✓ 找到 {len(portrait_files)} 个官方头像文件")
    
    # 为每个官方头像创建备用文件名
    fixed_count = 0
    for portrait_file in portrait_files:
        char_id = portrait_file.stem.replace("_official", "")
        
        # 创建多种文件名格式以确保兼容性
        backup_formats = [
            f"{char_id}.png",
            f"{char_id}_portrait.png",
            f"{char_id}_thumb.png"
        ]
        
        for backup_name in backup_formats:
            backup_path = portraits_dir / backup_name
            if not backup_path.exists():
                try:
                    shutil.copy2(portrait_file, backup_path)
                    print(f"  ✓ 创建备用头像: {backup_name}")
                    fixed_count += 1
                except Exception as e:
                    print(f"  ❌ 创建失败 {backup_name}: {e}")
    
    print(f"\n📊 修复统计: 创建了 {fixed_count} 个备用头像文件")
    
    # 验证头像文件完整性
    print("\n🔍 验证头像文件...")
    for portrait_file in portrait_files:
        try:
            # 检查文件大小
            file_size = portrait_file.stat().st_size
            if file_size > 1000:  # 至少1KB
                print(f"  ✓ {portrait_file.name} ({file_size} bytes)")
            else:
                print(f"  ⚠️ {portrait_file.name} 文件过小 ({file_size} bytes)")
        except Exception as e:
            print(f"  ❌ {portrait_file.name} 访问失败: {e}")
    
    return True

def create_character_index():
    """创建角色索引文件以便UI使用"""
    print("\n📋 创建角色索引...")
    
    portraits_dir = project_root / "assets" / "images" / "portraits"
    portrait_files = list(portraits_dir.glob("*_official.png"))
    
    # 生成角色索引
    character_index = {}
    for portrait_file in portrait_files:
        char_id = portrait_file.stem.replace("_official", "")
        character_index[char_id] = {
            "portrait_official": str(portrait_file.relative_to(project_root)),
            "portrait_standard": str((portraits_dir / f"{char_id}.png").relative_to(project_root)),
            "display_name": char_id.replace("_", " ").title()
        }
    
    # 保存索引文件
    index_file = project_root / "assets" / "character_portraits_index.json"
    import json
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(character_index, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 角色索引已保存: {index_file}")
    print(f"  包含 {len(character_index)} 个角色")
    
    return True

def test_ui_portrait_loading():
    """测试UI头像加载"""
    print("\n🧪 测试头像加载...")
    
    # 测试几个示例角色
    test_characters = ['kyo_kusanagi', 'terry_bogard', 'mai_shiranui', 'iori_yagami']
    
    portraits_dir = project_root / "assets" / "images" / "portraits"
    
    all_passed = True
    for char_id in test_characters:
        official_path = portraits_dir / f"{char_id}_official.png"
        standard_path = portraits_dir / f"{char_id}.png"
        
        if official_path.exists():
            print(f"  ✓ {char_id}: 官方头像可用")
        elif standard_path.exists():
            print(f"  ✓ {char_id}: 标准头像可用")
        else:
            print(f"  ❌ {char_id}: 无头像文件")
            all_passed = False
    
    return all_passed

def create_ui_patch():
    """创建UI修复补丁"""
    print("\n🔧 创建UI修复补丁...")
    
    patch_content = '''#!/usr/bin/env python3
"""
Character Selection UI Portrait Loading Patch
角色选择界面头像加载修复补丁
"""

import os
from pathlib import Path

def patch_character_selector_portrait_loading():
    """修复角色选择器的头像加载方法"""
    
    def enhanced_get_portrait_texture(self, character_name):
        """增强的头像纹理获取方法"""
        key = self._canonical_key(character_name)
        if key in self.portrait_cache:
            return self.portrait_cache[key]
        
        # 尝试多种头像文件格式
        portraits_dir = Path(self.assets_root) / 'images' / 'portraits'
        
        # 优先级顺序的头像文件路径
        portrait_candidates = [
            portraits_dir / f'{key}_official.png',
            portraits_dir / f'{key}.png', 
            portraits_dir / f'{key}_portrait.png',
            portraits_dir / f'{key}_thumb.png'
        ]
        
        texture = None
        for portrait_path in portrait_candidates:
            if portrait_path.exists():
                try:
                    texture = self.base_app.loader.loadTexture(str(portrait_path))
                    if texture:
                        print(f"🎨 加载头像成功: {character_name} -> {portrait_path.name}")
                        break
                except Exception as e:
                    print(f"头像加载失败 {portrait_path}: {e}")
                    continue
        
        # 如果没有找到头像文件，使用原始回退逻辑
        if not texture:
            profile = self._get_profile(character_name).copy() if character_name else {}
            char_record = self.char_manager.get_character_by_name(character_name) if character_name else None
            if char_record and 'id' not in profile:
                profile['id'] = char_record.get('id')

            if not character_name:
                texture = self._generate_portrait_texture(profile)
            else:
                texture = self.portrait_manager.get_texture(
                    key,
                    profile,
                    fallback_factory=lambda: self._generate_portrait_texture(profile)
                )
        
        self.portrait_cache[key] = texture
        return texture
    
    # 应用补丁
    try:
        from character_selector import CharacterSelector
        CharacterSelector._get_portrait_texture = enhanced_get_portrait_texture
        print("✓ 角色选择器头像加载补丁已应用")
        return True
    except ImportError as e:
        print(f"❌ 无法导入角色选择器: {e}")
        return False

if __name__ == "__main__":
    patch_character_selector_portrait_loading()
'''
    
    patch_file = project_root / "tools" / "ui_portrait_patch.py"
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print(f"✓ UI修复补丁已创建: {patch_file}")
    return True

def main():
    """主函数"""
    print("🎮 StreetBattle角色选择界面头像修复工具")
    print("=" * 50)
    
    try:
        # 1. 修复头像文件
        if not fix_character_portraits():
            print("❌ 头像文件修复失败")
            return False
        
        # 2. 创建角色索引
        if not create_character_index():
            print("❌ 角色索引创建失败")
            return False
        
        # 3. 测试头像加载
        if not test_ui_portrait_loading():
            print("⚠️ 部分头像加载测试失败")
        
        # 4. 创建UI补丁
        if not create_ui_patch():
            print("❌ UI补丁创建失败")
            return False
        
        print("\n🎉 角色选择界面头像修复完成!")
        print("\n📋 修复总结:")
        print("  ✓ 头像文件备份和格式规范化")
        print("  ✓ 角色索引文件创建")
        print("  ✓ 头像加载测试")
        print("  ✓ UI修复补丁创建")
        
        print("\n🔧 使用说明:")
        print("  1. 启动游戏测试角色选择界面")
        print("  2. 如有头像显示问题，运行补丁文件")
        print("  3. 所有角色现在都有多种格式的头像备份")
        
        return True
        
    except Exception as e:
        print(f"❌ 执行过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)