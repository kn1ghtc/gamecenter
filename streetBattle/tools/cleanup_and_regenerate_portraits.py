#!/usr/bin/env python3
"""
Character Portraits Cleanup and Regeneration Tool
角色头像清理和重新生成工具
"""

import os
import sys
import json
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def cleanup_portraits_directory():
    """清理portraits目录，每个角色只保留一张高质量图片"""
    print("🧹 清理角色头像目录")
    print("=" * 40)
    
    portraits_dir = project_root / "assets" / "images" / "portraits"
    
    if not portraits_dir.exists():
        print(f"❌ 头像目录不存在: {portraits_dir}")
        return False
    
    # 获取所有角色ID
    resource_catalog_path = project_root / "assets" / "resource_catalog.json"
    with open(resource_catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    character_ids = list(catalog.keys())
    print(f"✓ 找到 {len(character_ids)} 个角色")
    
    cleaned_count = 0
    kept_files = []
    
    for char_id in character_ids:
        # 每个角色的头像文件
        portrait_files = [
            f"{char_id}.png",
            f"{char_id}_official.png", 
            f"{char_id}_portrait.png",
            f"{char_id}_thumb.png"
        ]
        
        # 查找存在的文件
        existing_files = []
        for filename in portrait_files:
            file_path = portraits_dir / filename
            if file_path.exists():
                existing_files.append((filename, file_path))
        
        if not existing_files:
            print(f"  ⚠️ {char_id}: 没有找到头像文件")
            continue
        
        # 优先级: _official.png > .png > _portrait.png > _thumb.png
        priority_order = [f"{char_id}_official.png", f"{char_id}.png", f"{char_id}_portrait.png", f"{char_id}_thumb.png"]
        
        # 选择最高优先级的文件作为保留文件
        kept_file = None
        for priority_name in priority_order:
            for filename, file_path in existing_files:
                if filename == priority_name:
                    kept_file = (filename, file_path)
                    break
            if kept_file:
                break
        
        if not kept_file:
            kept_file = existing_files[0]  # 回退到第一个找到的文件
        
        # 重命名为标准格式 char_id.png
        standard_name = f"{char_id}.png"
        standard_path = portraits_dir / standard_name
        
        if kept_file[0] != standard_name:
            shutil.copy2(kept_file[1], standard_path)
            print(f"  ✓ {char_id}: {kept_file[0]} -> {standard_name}")
        else:
            print(f"  ✓ {char_id}: 保持 {standard_name}")
        
        kept_files.append(standard_path)
        
        # 删除其他文件
        for filename, file_path in existing_files:
            if file_path != standard_path and file_path.exists():
                try:
                    file_path.unlink()
                    cleaned_count += 1
                    print(f"    🗑️ 删除: {filename}")
                except Exception as e:
                    print(f"    ❌ 删除失败 {filename}: {e}")
    
    print(f"\n📊 清理统计:")
    print(f"  保留文件: {len(kept_files)} 个")
    print(f"  删除文件: {cleaned_count} 个")
    
    return True

def regenerate_specified_characters():
    """重新生成指定角色的完整全身动作图片"""
    print("\n🎨 重新生成指定角色图片")
    print("=" * 40)
    
    # 需要重新生成的角色
    characters_to_regenerate = [
        'wolfgang_krauser',
        'lin', 
        'goro_daimon',
        'igniz',
        'saisyu_kusanagi'
    ]
    
    # 改进的角色描述，专门用于制作精灵图的完整全身动作图片
    character_descriptions = {
        'wolfgang_krauser': {
            'name': 'Wolfgang Krauser',
            'prompt': 'A powerful German nobleman fighter with blonde slicked-back hair and intimidating presence, wearing a dark blue military-style uniform with gold trim and high boots, standing in a commanding pose with arms crossed, full body view, single character only, martial arts stance, King of Fighters style, detailed artwork for sprite animation'
        },
        'lin': {
            'name': 'Lin',
            'prompt': 'A skilled Chinese female assassin with short dark hair, wearing a tight-fitting dark blue qipao dress with gold accents, holding throwing knives, in a dynamic ready-to-strike pose, full body view, single character only, martial arts stance, King of Fighters style, detailed artwork for sprite animation'
        },
        'goro_daimon': {
            'name': 'Goro Daimon',
            'prompt': 'A massive Japanese judoka with a thick beard and imposing build, wearing a white judo gi with red belt, in a classic judo throwing stance with arms positioned for a grapple, full body view, single character only, martial arts pose, King of Fighters style, detailed artwork for sprite animation'
        },
        'igniz': {
            'name': 'Igniz',
            'prompt': 'An elegant silver-haired antagonist with pale skin wearing a flowing white coat with metallic accents, floating slightly above ground with energy emanating from his hands, in a supernatural commanding pose, full body view, single character only, boss character stance, King of Fighters style, detailed artwork for sprite animation'
        },
        'saisyu_kusanagi': {
            'name': 'Saisyu Kusanagi',
            'prompt': 'An older Japanese martial artist with grey hair and beard, wearing a traditional dark hakama and white gi, in a powerful flame-summoning pose with fire energy around his hands, full body view, single character only, traditional martial arts stance, King of Fighters style, detailed artwork for sprite animation'
        }
    }
    
    try:
        import openai
        
        # 检查API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ 未找到OPENAI_API_KEY环境变量")
            return False
        
        client = openai.OpenAI(api_key=api_key)
        portraits_dir = project_root / "assets" / "images" / "portraits"
        
        success_count = 0
        
        for char_id in characters_to_regenerate:
            if char_id not in character_descriptions:
                print(f"⚠️ 跳过未知角色: {char_id}")
                continue
            
            char_info = character_descriptions[char_id]
            print(f"\n🎭 正在生成 {char_info['name']} 的完整全身动作图片...")
            
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=char_info['prompt'],
                    size="1024x1024",
                    quality="hd",
                    style="vivid",
                    n=1
                )
                
                if response.data:
                    image_url = response.data[0].url
                    print(f"  ✓ 图像生成成功: {char_info['name']}")
                    
                    # 下载图像
                    import requests
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    
                    # 保存图像
                    output_path = portraits_dir / f"{char_id}.png"
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"  ✅ 保存成功: {output_path}")
                    success_count += 1
                else:
                    print(f"  ❌ 图像生成失败: {char_info['name']}")
                    
            except Exception as e:
                print(f"  ❌ 生成异常 {char_info['name']}: {e}")
        
        print(f"\n📊 重新生成统计:")
        print(f"  成功生成: {success_count}/{len(characters_to_regenerate)} 个角色")
        
        return success_count > 0
        
    except ImportError:
        print("❌ 未安装openai库，跳过图片重新生成")
        return False
    except Exception as e:
        print(f"❌ 重新生成失败: {e}")
        return False

def create_unified_character_list():
    """创建统一的角色列表文件"""
    print("\n📋 创建统一角色列表")
    print("=" * 40)
    
    # 从resource_catalog.json获取角色列表
    resource_catalog_path = project_root / "assets" / "resource_catalog.json"
    with open(resource_catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    character_ids = list(catalog.keys())
    portraits_dir = project_root / "assets" / "images" / "portraits"
    sprites_dir = project_root / "assets" / "sprites"
    
    # 创建统一角色数据
    unified_characters = {}
    
    for char_id in character_ids:
        # 生成显示名称
        display_name = char_id.replace('_', ' ').title()
        
        # 检查资源存在性
        portrait_exists = (portraits_dir / f"{char_id}.png").exists()
        sprite_exists = (sprites_dir / char_id).exists()
        
        unified_characters[char_id] = {
            'id': char_id,
            'display_name': display_name,
            'portrait_path': f"assets/images/portraits/{char_id}.png" if portrait_exists else None,
            'sprite_path': f"assets/sprites/{char_id}" if sprite_exists else None,
            'has_portrait': portrait_exists,
            'has_sprite': sprite_exists
        }
        
        status = []
        if portrait_exists:
            status.append("Portrait✓")
        if sprite_exists:
            status.append("Sprite✓")
        
        print(f"  {char_id}: {display_name} ({', '.join(status) if status else 'No Resources'})")
    
    # 保存统一角色列表
    unified_list_path = project_root / "assets" / "unified_character_list.json"
    with open(unified_list_path, 'w', encoding='utf-8') as f:
        json.dump(unified_characters, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 统一角色列表已保存: {unified_list_path}")
    print(f"  包含 {len(unified_characters)} 个角色")
    
    return True

def main():
    """主函数"""
    print("🎮 StreetBattle 角色头像清理和重新生成工具")
    print("=" * 50)
    
    try:
        # 1. 清理portraits目录
        if not cleanup_portraits_directory():
            print("❌ 头像目录清理失败")
            return False
        
        # 2. 重新生成指定角色图片
        regenerate_specified_characters()
        
        # 3. 创建统一角色列表
        if not create_unified_character_list():
            print("❌ 统一角色列表创建失败")
            return False
        
        print("\n🎉 角色头像清理和重新生成完成!")
        print("\n📋 完成总结:")
        print("  ✓ portraits目录已清理，每个角色只保留一张高质量图片")
        print("  ✓ 指定角色的完整全身动作图片已重新生成")
        print("  ✓ 统一角色列表已创建")
        
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