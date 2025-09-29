#!/usr/bin/env python3
"""
统一角色配置脚本
将3D模型、2.5D图片和精灵动画的角色配置统一到unified_roster.json
"""

import json
import os
from pathlib import Path

def get_3d_characters():
    """获取3D角色模型目录中的角色列表"""
    assets_dir = Path("assets/characters")
    characters = []
    
    if assets_dir.exists():
        for item in assets_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 处理特殊目录名称
                char_name = item.name
                if char_name == "geese-xiv-fok-all-stars":
                    char_name = "geese_howard"
                elif char_name == "shingo-classic-kof-all-stars":
                    char_name = "shingo_yabuki"
                elif char_name == "terry_bogard_-_kof_all_stars":
                    char_name = "terry_bogard"
                elif char_name == "wolfgang":
                    char_name = "wolfgang_krauser"
                
                characters.append(char_name)
    
    return sorted(characters)

def get_2d5_characters():
    """获取2.5D角色图片中的角色列表"""
    portraits_dir = Path("assets/images/portraits")
    characters = []
    
    if portraits_dir.exists():
        for item in portraits_dir.iterdir():
            if item.is_file() and item.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                char_name = item.stem
                characters.append(char_name)
    
    return sorted(characters)

def get_sprite_characters():
    """获取精灵动画目录中的角色列表"""
    sprites_dir = Path("assets/sprites")
    characters = []
    
    if sprites_dir.exists():
        for item in sprites_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                characters.append(item.name)
    
    return sorted(characters)

def create_unified_roster():
    """创建统一的角色配置"""
    
    # 获取所有角色
    characters_3d = get_3d_characters()
    characters_2d5 = get_2d5_characters()
    characters_sprites = get_sprite_characters()
    
    print(f"3D角色: {len(characters_3d)}个")
    print(f"2.5D角色: {len(characters_2d5)}个")
    print(f"精灵角色: {len(characters_sprites)}个")
    
    # 合并所有角色（去重）
    all_characters = set(characters_3d + characters_2d5 + characters_sprites)
    print(f"总角色数: {len(all_characters)}个")
    
    # 创建统一的角色配置
    unified_roster = {}
    
    for char_id in sorted(all_characters):
        # 检查资源可用性
        has_3d = char_id in characters_3d
        has_2d5 = char_id in characters_2d5
        has_sprites = char_id in characters_sprites
        
        # 获取显示名称（将下划线转换为空格并首字母大写）
        display_name = char_id.replace('_', ' ').title()
        
        # 特殊名称处理
        if char_id == "k_dash":
            display_name = "K Dash"
        elif char_id == "b_jenet":
            display_name = "B Jenet"
        
        # 创建角色配置
        char_config = {
            "id": char_id,
            "display_name": display_name,
            "portrait_path": f"assets/images/portraits/{char_id}.png",
            "sprite_path": f"assets/sprites/{char_id}",
            "model_path": f"assets/characters/{char_id}",
            "has_portrait": has_2d5,
            "has_sprite": has_sprites,
            "has_3d_model": has_3d
        }
        
        unified_roster[char_id] = char_config
    
    return unified_roster

def main():
    """主函数"""
    print("开始统一角色配置...")
    
    # 创建统一配置
    unified_roster = create_unified_roster()
    
    # 保存到文件
    output_path = Path("config/characters/unified_roster.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unified_roster, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 统一角色配置已保存到: {output_path}")
    print(f"✅ 共配置了 {len(unified_roster)} 个角色")
    
    # 显示角色统计
    has_all_resources = sum(1 for char in unified_roster.values() 
                           if char['has_portrait'] and char['has_sprite'] and char['has_3d_model'])
    print(f"✅ 拥有完整资源的角色: {has_all_resources}个")

if __name__ == "__main__":
    main()