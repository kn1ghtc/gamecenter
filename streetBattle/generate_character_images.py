#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色图像生成器 - 使用Flux AI生成高质量格斗游戏角色图像
Character Image Generator - Generate high-quality fighting game character images with Flux AI
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List
import time


class CharacterImageGenerator:
    """专业格斗游戏角色图像生成器"""
    
    def __init__(self):
        self.output_dir = Path("assets/characters")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 角色定义和专业提示词
        self.characters = {
            "mr_big": {
                "display_name": "Mr. Big",
                "description": "Elegant crime boss from Fatal Fury",
                "signature_moves": ["Ground Blaster", "Tornado Upper", "California Romance"],
                "appearance": "tall gentleman in expensive business suit, slicked back dark hair, confident stance with arms crossed",
                "fighting_style": "street fighting with cane techniques",
                "colors": "dark navy suit, white shirt, red tie"
            },
            "ramon": {
                "display_name": "Ramon",
                "description": "Lucha libre wrestler from King of Fighters",
                "signature_moves": ["Tiger Road", "Feint Step", "Rolling Sobat"],
                "appearance": "muscular luchador with colorful mask, athletic build in wrestling attire",
                "fighting_style": "lucha libre wrestling and acrobatic moves",
                "colors": "bright blue and yellow mask, green wrestling outfit"
            },
            "wolfgang": {
                "display_name": "Wolfgang Krauser",
                "description": "German nobleman from Fatal Fury",
                "signature_moves": ["Kaiser Wave", "Leg Tomahawk", "Phoenix Throw"],
                "appearance": "imposing tall nobleman with long blonde hair, aristocratic uniform with cape",
                "fighting_style": "brutal power attacks and royal combat techniques",
                "colors": "dark blue military uniform, golden details, white cape"
            }
        }
    
    def generate_professional_prompt(self, char_id: str, pose_type: str = "stance") -> str:
        """生成专业的AI图像提示词"""
        char = self.characters[char_id]
        
        base_prompt = f"""Professional full-body portrait of {char['display_name']}, {char['description']}, 
{char['appearance']}, performing signature {pose_type} pose, {char['fighting_style']} style,
high-quality detailed anime fighting game art style, {char['colors']}, 
clean white background, perfect lighting, 1024x1024 resolution, 
only one person in image, full body visible from head to toe, 
no other characters, solo character art, fighting game character design,
detailed shading, vibrant colors, professional game art quality"""
        
        # 清理提示词
        return " ".join(base_prompt.split())
    
    def generate_multiple_poses(self, char_id: str) -> List[str]:
        """为每个角色生成多个姿势的提示词"""
        poses = [
            "combat stance",
            "signature attack pose", 
            "victory celebration",
            "defensive guard position",
            "special move preparation",
            "jumping attack pose"
        ]
        
        prompts = []
        for pose in poses:
            prompt = self.generate_professional_prompt(char_id, pose)
            prompts.append((pose, prompt))
        
        return prompts
    
    def call_flux_api(self, prompt: str, filename: str) -> bool:
        """调用Flux API生成图像（需要实际的API配置）"""
        print(f"🎨 生成图像: {filename}")
        print(f"📝 提示词: {prompt[:100]}...")
        
        # 这里需要配置实际的Flux API调用
        # 由于没有实际的API密钥，我们创建占位符
        
        try:
            # 示例API调用结构（需要根据实际API调整）
            """
            api_url = "https://fal.ai/models/fal-ai/flux/schnell"
            headers = {
                "Authorization": "Bearer YOUR_API_KEY",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 4,
                "guidance_scale": 3.5
            }
            
            response = requests.post(api_url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                image_url = result.get("image_url")
                
                # 下载图像
                img_response = requests.get(image_url)
                with open(self.output_dir / filename, 'wb') as f:
                    f.write(img_response.content)
                
                return True
            """
            
            # 暂时创建占位符文件，显示应该生成的内容
            placeholder_info = {
                "character": filename.split('_')[0],
                "prompt": prompt,
                "resolution": "1024x1024",
                "status": "ready_for_generation"
            }
            
            with open(self.output_dir / f"{filename}.json", 'w', encoding='utf-8') as f:
                json.dump(placeholder_info, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 提示词已准备: {filename}.json")
            return True
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return False
    
    def generate_character_images(self, char_id: str):
        """为指定角色生成所有图像"""
        if char_id not in self.characters:
            print(f"❌ 未知角色: {char_id}")
            return
        
        char = self.characters[char_id]
        print(f"\n🎭 开始生成 {char['display_name']} 的角色图像...")
        
        # 生成主肖像
        main_prompt = self.generate_professional_prompt(char_id, "signature combat stance")
        main_filename = f"{char_id}_portrait.png"
        self.call_flux_api(main_prompt, main_filename)
        
        # 生成多个动作姿势
        poses = self.generate_multiple_poses(char_id)
        for i, (pose_name, prompt) in enumerate(poses):
            filename = f"{char_id}_pose_{i+1}_{pose_name.replace(' ', '_')}.png"
            self.call_flux_api(prompt, filename)
            time.sleep(1)  # 避免API限制
        
        print(f"✅ {char['display_name']} 图像生成完成")
    
    def generate_sprite_animation_frames(self, char_id: str):
        """生成精灵动画帧"""
        char = self.characters[char_id]
        sprite_dir = Path(f"assets/sprites/{char_id}")
        sprite_dir.mkdir(parents=True, exist_ok=True)
        
        # 动画状态定义
        animation_states = {
            "idle": ["neutral stance", "breathing animation", "ready position"],
            "walk": ["step forward", "mid stride", "step back", "weight shift"],
            "attack": ["wind up", "strike", "follow through", "recovery"],
            "hit": ["impact reaction", "stagger back", "recovery stance"],
            "jump": ["crouch", "leap", "peak", "landing"],
            "block": ["guard up", "blocking stance", "deflection"],
            "victory": ["arms raised", "celebration pose", "triumphant stance"]
        }
        
        print(f"\n🎬 生成 {char['display_name']} 精灵动画帧...")
        
        for state, frames in animation_states.items():
            for i, frame_desc in enumerate(frames):
                prompt = f"""Professional fighting game sprite frame of {char['display_name']}, 
{char['appearance']}, {frame_desc} animation frame, 
pixel art style, clean background, 128x128 resolution,
side view, detailed sprite animation, {char['colors']},
only one character, clear silhouette, game sprite quality"""
                
                filename = f"{char_id}_{state}_frame_{i+1}.png"
                
                # 创建精灵动画配置
                sprite_info = {
                    "character": char_id,
                    "animation": state,
                    "frame": i + 1,
                    "description": frame_desc,
                    "prompt": " ".join(prompt.split()),
                    "resolution": "128x128",
                    "style": "pixel_art_sprite"
                }
                
                with open(sprite_dir / f"{filename}.json", 'w', encoding='utf-8') as f:
                    json.dump(sprite_info, f, indent=2, ensure_ascii=False)
        
        # 创建精灵动画清单
        manifest = {
            "character_id": char_id,
            "display_name": char['display_name'],
            "description": char['description'],
            "states": {}
        }
        
        for state, frames in animation_states.items():
            manifest["states"][state] = {
                "sequence": list(range(len(frames))),
                "fps": 12 if state in ["walk", "attack"] else 8,
                "loop": state in ["idle", "walk", "block"],
                "frames": len(frames),
                "durations": [0.1] * len(frames)
            }
        
        with open(sprite_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {char['display_name']} 精灵动画配置完成")
    
    def generate_all_missing_characters(self):
        """生成所有缺失角色的图像"""
        print("🚀 开始生成缺失角色图像...")
        print("=" * 60)
        
        for char_id in self.characters.keys():
            print(f"\n⭐ 处理角色: {self.characters[char_id]['display_name']}")
            
            # 生成角色肖像
            self.generate_character_images(char_id)
            
            # 生成精灵动画
            self.generate_sprite_animation_frames(char_id)
            
            print(f"🎉 {self.characters[char_id]['display_name']} 处理完成!")
        
        print("\n" + "=" * 60)
        print("✨ 所有角色图像生成任务完成!")
        print("\n📋 生成内容:")
        print("   • 每个角色的主肖像 (1024x1024)")
        print("   • 6种不同战斗姿势")
        print("   • 7种动画状态的精灵帧")
        print("   • 完整的动画配置清单")
        print("\n💡 下一步:")
        print("   1. 使用生成的JSON提示词配合Flux AI API")
        print("   2. 将生成的PNG图像放入对应目录")
        print("   3. 运行游戏测试新角色")


def main():
    """主函数"""
    generator = CharacterImageGenerator()
    
    print("🎮 Street Battle 角色图像生成器")
    print("🎨 为 Mr. Big, Ramon, Wolfgang 生成专业图像")
    print()
    
    # 生成所有缺失角色
    generator.generate_all_missing_characters()
    
    # 显示生成的文件
    output_files = list(generator.output_dir.rglob("*.json"))
    print(f"\n📁 生成了 {len(output_files)} 个配置文件:")
    for file in output_files[:10]:  # 只显示前10个
        print(f"   {file}")
    if len(output_files) > 10:
        print(f"   ... 和其他 {len(output_files) - 10} 个文件")


if __name__ == "__main__":
    main()