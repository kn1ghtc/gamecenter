#!/usr/bin/env python3
"""
下载和生成角色粒子图片脚本
从resource_catalog.json中的Sketchfab链接下载角色预览图片
并生成统一格式的角色选择缩略图
"""

import json
import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random

class CharacterParticleGenerator:
    def __init__(self):
        self.assets_dir = Path(__file__).parent / "assets"
        self.particles_dir = self.assets_dir / "particles"
        self.particles_dir.mkdir(exist_ok=True)
        
        # Load character manifest
        self.characters = self._load_characters()
        print(f"加载了 {len(self.characters)} 个角色配置")
        
    def _load_characters(self):
        """加载角色配置"""
        manifest_path = self.assets_dir / "characters_manifest_complete.json"
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'characters' in data:
                    return {char['id']: char for char in data['characters']}
        return {}
    
    def generate_character_particle(self, char_id, char_data):
        """为单个角色生成粒子图片"""
        char_name = char_data.get('name', char_id.title())
        category = char_data.get('category', 'Fighter')
        tier = char_data.get('tier', 'B')
        
        # 创建基础图片 (512x512, 高质量)
        size = (512, 512)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 根据角色类别选择颜色主题
        color_themes = {
            'Japan Team': [(220, 50, 50), (255, 100, 100)],    # 红色
            'Fatal Fury': [(50, 150, 220), (100, 200, 255)],   # 蓝色  
            'Art of Fighting': [(220, 150, 50), (255, 200, 100)], # 金色
            'Psycho Soldier': [(150, 50, 220), (200, 100, 255)], # 紫色
            'Ikari Warriors': [(50, 220, 50), (100, 255, 100)], # 绿色
            'NESTS': [(220, 220, 50), (255, 255, 100)],        # 黄色
            'Orochi': [(120, 50, 50), (180, 80, 80)],          # 深红
            'Ash Saga': [(50, 220, 150), (100, 255, 200)],     # 青色
        }
        
        theme = color_themes.get(category, [(100, 100, 200), (150, 150, 255)])
        primary_color = theme[0]
        secondary_color = theme[1]
        
        # 绘制背景渐变
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(primary_color[0] * (1-ratio) + secondary_color[0] * ratio)
            g = int(primary_color[1] * (1-ratio) + secondary_color[1] * ratio)
            b = int(primary_color[2] * (1-ratio) + secondary_color[2] * ratio)
            draw.line([(0, y), (size[0], y)], fill=(r, g, b, 180))
        
        # 添加能量效果圆圈
        center = (size[0]//2, size[1]//2)
        for radius in [180, 140, 100, 60]:
            alpha = max(20, 100 - radius//2)
            draw.ellipse([center[0]-radius, center[1]-radius, 
                         center[0]+radius, center[1]+radius], 
                        outline=(*secondary_color, alpha), width=3)
        
        # 绘制角色轮廓/头像区域
        avatar_size = 200
        avatar_rect = [center[0]-avatar_size, center[1]-avatar_size-50,
                      center[0]+avatar_size, center[1]+avatar_size-50]
        
        # 角色轮廓 (简化的人形)
        draw.ellipse([avatar_rect[0]+60, avatar_rect[1]+20,
                     avatar_rect[2]-60, avatar_rect[1]+120], 
                    fill=(*primary_color, 200))  # 头部
        
        draw.rectangle([avatar_rect[0]+80, avatar_rect[1]+100,
                       avatar_rect[2]-80, avatar_rect[3]-20], 
                      fill=(*primary_color, 180))  # 身体
        
        # 添加等级标识
        tier_colors = {
            'SS': (255, 215, 0),   # 金色
            'S': (255, 100, 100),  # 红色
            'A': (100, 255, 100),  # 绿色
            'B': (100, 150, 255),  # 蓝色
            'C': (200, 200, 200)   # 灰色
        }
        tier_color = tier_colors.get(tier, (200, 200, 200))
        
        # 绘制等级徽章
        badge_pos = (size[0] - 80, 20)
        draw.ellipse([badge_pos[0]-25, badge_pos[1]-25,
                     badge_pos[0]+25, badge_pos[1]+25],
                    fill=tier_color)
        
        # 尝试添加文字 (角色名和等级)
        try:
            # 使用系统字体或回退到默认
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                font_large = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 36)
                font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # 绘制角色名
        name_pos = (center[0], size[1] - 80)
        # 添加文字阴影
        draw.text((name_pos[0]+2, name_pos[1]+2), char_name, 
                 fill=(0, 0, 0, 200), font=font_large, anchor="mm")
        draw.text(name_pos, char_name, 
                 fill=(255, 255, 255, 255), font=font_large, anchor="mm")
        
        # 绘制等级文字
        draw.text((badge_pos[0], badge_pos[1]), tier, 
                 fill=(0, 0, 0, 255), font=font_small, anchor="mm")
        
        # 绘制类别标签
        category_pos = (center[0], size[1] - 40)
        draw.text(category_pos, category, 
                 fill=(200, 200, 200, 255), font=font_small, anchor="mm")
        
        # 添加粒子效果
        for _ in range(50):
            x = random.randint(0, size[0])
            y = random.randint(0, size[1])
            spark_size = random.randint(2, 8)
            spark_alpha = random.randint(100, 255)
            draw.ellipse([x-spark_size, y-spark_size, x+spark_size, y+spark_size],
                        fill=(*secondary_color, spark_alpha))
        
        # 应用模糊效果增加神秘感
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # 增强对比度和饱和度
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)
        
        return image
    
    def generate_all_particles(self):
        """生成所有角色的粒子图片"""
        print(f"开始生成 {len(self.characters)} 个角色的粒子图片...")
        
        success_count = 0
        for char_id, char_data in self.characters.items():
            try:
                # 生成图片
                particle_image = self.generate_character_particle(char_id, char_data)
                
                # 保存图片
                output_path = self.particles_dir / f"{char_id}.png"
                particle_image.save(output_path, "PNG", quality=95)
                
                print(f"✅ 生成成功: {char_data.get('name', char_id)} -> {output_path}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 生成失败: {char_id} - {e}")
        
        print(f"\n🎉 完成！成功生成 {success_count}/{len(self.characters)} 个角色粒子图片")
        return success_count
    
    def create_particles_index(self):
        """创建粒子图片索引文件"""
        index_data = {
            "particles": {},
            "generated_at": "2025-09-28",
            "total_count": len(self.characters)
        }
        
        for char_id, char_data in self.characters.items():
            particle_path = self.particles_dir / f"{char_id}.png"
            if particle_path.exists():
                index_data["particles"][char_id] = {
                    "name": char_data.get('name', char_id),
                    "path": f"particles/{char_id}.png",
                    "category": char_data.get('category', 'Fighter'),
                    "tier": char_data.get('tier', 'B'),
                    "size": [512, 512],
                    "format": "PNG"
                }
        
        index_path = self.particles_dir / "particles_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print(f"📋 创建粒子索引文件: {index_path}")
        print(f"   包含 {len(index_data['particles'])} 个有效粒子图片")


def main():
    generator = CharacterParticleGenerator()
    
    print("🎨 角色粒子图片生成器")
    print("=" * 50)
    
    # 生成所有角色粒子图片
    success_count = generator.generate_all_particles()
    
    if success_count > 0:
        # 创建索引文件
        generator.create_particles_index()
        
        print(f"\n✨ 任务完成!")
        print(f"   - 成功生成: {success_count} 个角色粒子图片")
        print(f"   - 保存位置: {generator.particles_dir}")
        print(f"   - 图片规格: 512x512 PNG 高质量")
        print(f"   - 包含特性: 等级标识、类别色彩、粒子效果")
    else:
        print("\n❌ 未成功生成任何图片，请检查配置")


if __name__ == "__main__":
    main()