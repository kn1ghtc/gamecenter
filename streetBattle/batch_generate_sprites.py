#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量检查并生成缺失的精灵动画"""

import os
import json
from pathlib import Path

# 导入精灵动画生成器
from sprite_animation_generator import SpriteAnimationGenerator

def main():
    print("=" * 80)
    print("批量生成精灵动画 - 检查缺失资源")
    print("=" * 80)
    
    # 加载角色列表
    assets_dir = Path("assets")
    unified_roster = Path("config/characters/unified_roster.json")
    
    if not unified_roster.exists():
        print(f"错误: 未找到 {unified_roster}")
        return
    
    with open(unified_roster, 'r', encoding='utf-8') as f:
        roster_data = json.load(f)
    
    # 获取所有非disabled的角色
    valid_characters = []
    for char_id, char_data in roster_data.items():
        if not char_data.get('disabled', False):
            valid_characters.append({
                'id': char_id,
                'name': char_data.get('display_name', char_id),
                'data': char_data
            })
    
    print(f"\n找到 {len(valid_characters)} 个有效角色")
    print("-" * 80)
    
    # 检查每个角色的精灵资源
    missing_sprites = []
    incomplete_sprites = []
    complete_sprites = []
    
    for char in valid_characters:
        char_id = char['id']
        char_dir = assets_dir / "sprites" / char_id
        spritesheet = char_dir / f"{char_id}_spritesheet.png"
        manifest = char_dir / "manifest.json"
        
        # 检查精灵目录
        anim_dirs = ["idle", "walk", "attack", "hit", "jump", "victory", "block"]
        has_frames = all((char_dir / anim).exists() and 
                        len(list((char_dir / anim).glob("*.png"))) > 0 
                        for anim in anim_dirs)
        
        if not spritesheet.exists() and not has_frames:
            missing_sprites.append(char)
        elif not spritesheet.exists() or not manifest.exists():
            incomplete_sprites.append(char)
        else:
            complete_sprites.append(char)
    
    print(f"\n资源状态:")
    print(f"  - 完整: {len(complete_sprites)} 个")
    print(f"  - 不完整: {len(incomplete_sprites)} 个")
    print(f"  - 缺失: {len(missing_sprites)} 个")
    
    # 列出需要生成的角色
    needs_generation = missing_sprites + incomplete_sprites
    
    if not needs_generation:
        print("\n所有角色的精灵资源都已完整！")
        return
    
    print(f"\n需要生成精灵动画的角色 ({len(needs_generation)} 个):")
    for char in needs_generation:
        status = "缺失" if char in missing_sprites else "不完整"
        print(f"  [{status}] {char['name']} ({char['id']})")
    
    # 询问是否生成
    print("\n" + "=" * 80)
    response = input("是否开始批量生成精灵动画？(y/n): ").strip().lower()
    
    if response != 'y':
        print("已取消生成")
        return
    
    # 初始化生成器
    generator = SpriteAnimationGenerator(assets_dir="assets")
    
    print("\n开始批量生成...")
    print("=" * 80)
    
    success_count = 0
    failed_count = 0
    
    for idx, char in enumerate(needs_generation, 1):
        char_id = char['id']
        char_name = char['name']
        
        print(f"\n[{idx}/{len(needs_generation)}] 生成: {char_name} ({char_id})")
        print("-" * 80)
        
        try:
            # 生成精灵动画
            success = generator.generate_character_sprites(char_id)
            
            if success:
                print(f"  ✓ 成功生成 {char_name} 的精灵动画")
                success_count += 1
            else:
                print(f"  ✗ 生成失败: {char_name}")
                failed_count += 1
                
        except Exception as e:
            print(f"  ✗ 生成异常: {e}")
            failed_count += 1
    
    print("\n" + "=" * 80)
    print(f"批量生成完成！")
    print(f"  - 成功: {success_count} 个")
    print(f"  - 失败: {failed_count} 个")
    print(f"  - 总计: {len(needs_generation)} 个")
    print("=" * 80)


if __name__ == '__main__':
    main()
