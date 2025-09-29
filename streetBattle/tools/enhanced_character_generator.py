#!/usr/bin/env python3
"""
Enhanced Character Image Regeneration Tool
优化角色图像重新生成工具 - 针对精灵动画制作需求
"""

import os
import sys
import json
import requests
from pathlib import Path
from openai import OpenAI

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_enhanced_character_prompt(character_name, character_info):
    """创建针对精灵动画的优化提示词"""
    
    # 基础角色描述映射
    character_descriptions = {
        'mr_big': {
            'base': 'Mr. Big from King of Fighters - African American crime boss with distinctive mustache and formal attire',
            'style': 'tall muscular man in a pinstripe suit',
            'pose': 'dynamic fighting stance with both arms and legs clearly visible',
            'details': 'wearing white dress shirt, dark pinstripe vest, formal pants, dress shoes, holding walking cane as weapon'
        },
        'magaki': {
            'base': 'Magaki from King of Fighters - mysterious pale-skinned antagonist with long flowing hair',
            'style': 'ethereal otherworldly figure with supernatural aura',
            'pose': 'dramatic floating combat pose with energy emanating from hands',
            'details': 'long silver/white hair flowing, dark mystical robes with intricate patterns, bare feet, glowing eyes'
        },
        'ramon': {
            'base': 'Ramon from King of Fighters - Mexican luchador wrestler with distinctive mask',
            'style': 'athletic muscular wrestler in colorful lucha libre attire',
            'pose': 'dynamic wrestling stance ready to grapple with arms extended',
            'details': 'wearing colorful luchador mask with geometric patterns, wrestling tights, boots, cape flowing behind'
        },
        'orochi': {
            'base': 'Orochi from King of Fighters - ancient serpent deity in human form with otherworldly presence',
            'style': 'tall imposing figure with supernatural divine aura',
            'pose': 'majestic combat stance with arms spread wide showing divine power',
            'details': 'long flowing dark hair, traditional Japanese divine robes with mystical symbols, bare feet, glowing supernatural energy'
        },
        'wolfgang_krauser': {
            'base': 'Wolfgang Krauser from Fatal Fury/King of Fighters - German nobleman and martial artist',
            'style': 'tall imposing European nobleman with regal bearing',
            'pose': 'commanding martial arts stance with perfect form and balance',
            'details': 'blonde hair slicked back, red military-style jacket with gold trim, white pants, black boots, cape flowing dramatically'
        }
    }
    
    char_desc = character_descriptions.get(character_name, {
        'base': f'{character_name} fighting game character',
        'style': 'athletic martial artist',
        'pose': 'dynamic fighting stance',
        'details': 'wearing martial arts attire'
    })
    
    # 针对精灵动画优化的通用提示词模板
    enhanced_prompt = f"""Create a high-quality full-body character sprite image for 2D fighting game animation:

CHARACTER: {char_desc['base']}
STYLE: {char_desc['style']}
POSE: {char_desc['pose']}
DETAILS: {char_desc['details']}

TECHNICAL REQUIREMENTS FOR SPRITE ANIMATION:
- Full body clearly visible from head to toe
- Standing upright in neutral fighting stance
- Both arms and legs fully visible and well-defined
- Clear muscle definition and body proportions
- Facing slightly forward (3/4 view) for optimal sprite visibility
- Clean background (solid color or minimal)
- Sharp outlines and distinct color separation
- Suitable for frame-by-frame animation extraction
- Professional fighting game art style
- High contrast for easy sprite cutting
- All limbs clearly separated and visible
- Perfect for creating walking, punching, and special move animations

ARTISTIC STYLE:
- 2D fighting game character art style (Street Fighter/King of Fighters quality)
- Vibrant colors with strong contrast
- Detailed shading and highlights
- Professional game sprite artwork
- Clean lineart with cel-shading style
- Suitable for 2D sprite animation and frame extraction"""

    return enhanced_prompt

def regenerate_character_with_enhanced_prompt(character_name):
    """使用优化提示词重新生成角色图像"""
    print(f"🎨 重新生成角色: {character_name}")
    
    try:
        # 获取OpenAI客户端
        client = OpenAI()
        
        # 创建优化的提示词
        enhanced_prompt = create_enhanced_character_prompt(character_name, {})
        
        print(f"📝 使用优化提示词:\n{enhanced_prompt[:200]}...")
        
        # 调用DALL-E 3生成图像
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        print(f"✅ 图像生成成功: {image_url}")
        
        # 下载图像
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            # 保存到portraits目录
            portrait_path = project_root / "assets" / "images" / "portraits" / f"{character_name}.png"
            
            with open(portrait_path, 'wb') as f:
                f.write(image_response.content)
            
            print(f"💾 图像已保存: {portrait_path}")
            return True
        else:
            print(f"❌ 图像下载失败: {image_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def batch_regenerate_characters():
    """批量重新生成需要优化的角色"""
    print("🎨 批量角色图像优化生成")
    print("=" * 50)
    
    # 需要重新生成的角色列表
    characters_to_regenerate = [
        'mr_big',
        'magaki', 
        'ramon',
        'orochi',
        'wolfgang_krauser'
    ]
    
    results = {}
    
    for i, character in enumerate(characters_to_regenerate, 1):
        print(f"\n📍 处理角色 {i}/{len(characters_to_regenerate)}: {character}")
        print("-" * 30)
        
        success = regenerate_character_with_enhanced_prompt(character)
        results[character] = success
        
        if success:
            print(f"✅ {character} 生成成功")
        else:
            print(f"❌ {character} 生成失败")
        
        # 添加延迟避免API限制
        if i < len(characters_to_regenerate):
            import time
            print("⏳ 等待3秒避免API限制...")
            time.sleep(3)
    
    # 生成结果报告
    print("\n📊 批量生成结果报告")
    print("=" * 50)
    
    successful = [char for char, success in results.items() if success]
    failed = [char for char, success in results.items() if not success]
    
    print(f"✅ 成功生成: {len(successful)}/{len(characters_to_regenerate)} 个角色")
    if successful:
        for char in successful:
            print(f"  ✓ {char}")
    
    if failed:
        print(f"❌ 生成失败: {len(failed)} 个角色")
        for char in failed:
            print(f"  ✗ {char}")
    
    # 保存生成报告
    report_data = {
        "generation_date": "2025-09-28",
        "characters_processed": characters_to_regenerate,
        "successful": successful,
        "failed": failed,
        "success_rate": f"{len(successful)}/{len(characters_to_regenerate)}"
    }
    
    report_file = project_root / "tools" / "enhanced_character_generation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 生成报告已保存: {report_file}")
    
    return len(successful) == len(characters_to_regenerate)

def main():
    """主函数"""
    print("🎨 StreetBattle角色图像优化生成工具")
    print("=" * 60)
    print("针对2D精灵动画制作需求优化角色图像生成")
    print("=" * 60)
    
    try:
        success = batch_regenerate_characters()
        
        if success:
            print("\n🎉 所有角色图像优化生成完成!")
            print("\n✨ 优化特点:")
            print("  ✓ 完整全身可见（头到脚）")
            print("  ✓ 清晰的肢体分离")
            print("  ✓ 适合精灵动画制作")
            print("  ✓ 高对比度便于抠图")
            print("  ✓ 专业格斗游戏美术风格")
            
            print("\n🚀 图像已准备就绪，可用于精灵动画制作!")
        else:
            print("\n⚠️ 部分角色生成失败，请检查API配置或网络连接")
        
        return success
        
    except Exception as e:
        print(f"❌ 工具执行失败: {e}")
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