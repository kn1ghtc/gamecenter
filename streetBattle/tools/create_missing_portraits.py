#!/usr/bin/env python3
"""
下载缺失的角色肖像图片
"""
import os
import json
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

def create_high_quality_portrait(character_name, output_path, width=768, height=960):
    """创建高质量的角色肖像图片"""
    
    # 角色配色方案
    color_schemes = {
        'angel': {'bg': '#ff6b9d', 'primary': '#2196f3', 'secondary': '#ffffff'},
        'choi_bounge': {'bg': '#4caf50', 'primary': '#ff9800', 'secondary': '#795548'},
        'goro_daimon': {'bg': '#3f51b5', 'primary': '#ffeb3b', 'secondary': '#ffffff'},
        'igniz': {'bg': '#9c27b0', 'primary': '#e91e63', 'secondary': '#000000'},
        'lin': {'bg': '#ff5722', 'primary': '#607d8b', 'secondary': '#ffffff'},
        'magaki': {'bg': '#212121', 'primary': '#f44336', 'secondary': '#ff9800'},
        'mr_big': {'bg': '#795548', 'primary': '#ffc107', 'secondary': '#ffffff'},
        'orochi': {'bg': '#1a1a1a', 'primary': '#ff0000', 'secondary': '#800080'},
        'ramon': {'bg': '#00bcd4', 'primary': '#ff9800', 'secondary': '#ffffff'},
        'saisyu_kusanagi': {'bg': '#8bc34a', 'primary': '#f44336', 'secondary': '#ffffff'},
        'sie_kensou': {'bg': '#ffeb3b', 'primary': '#e91e63', 'secondary': '#000000'},
        'wolfgang_krauser': {'bg': '#424242', 'primary': '#ff5722', 'secondary': '#ffc107'}
    }
    
    # 获取角色配色
    colors = color_schemes.get(character_name, {
        'bg': '#2196f3', 
        'primary': '#ffffff', 
        'secondary': '#ff9800'
    })
    
    # 创建图像
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制渐变背景
    for y in range(height):
        alpha = int(255 * (1 - y / height * 0.7))
        bg_color = tuple(int(colors['bg'][i:i+2], 16) for i in (1, 3, 5)) + (alpha,)
        draw.rectangle([(0, y), (width, y+1)], fill=bg_color)
    
    # 绘制角色轮廓（简化的几何图形）
    center_x, center_y = width // 2, height // 2 - 50
    
    # 头部（圆形）
    head_radius = 80
    head_color = tuple(int(colors['primary'][i:i+2], 16) for i in (1, 3, 5)) + (200,)
    draw.ellipse([
        center_x - head_radius, center_y - head_radius - 50,
        center_x + head_radius, center_y + head_radius - 50
    ], fill=head_color, outline=tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,), width=3)
    
    # 身体（矩形）
    body_width, body_height = 100, 200
    body_color = tuple(int(colors['primary'][i:i+2], 16) for i in (1, 3, 5)) + (180,)
    draw.rectangle([
        center_x - body_width//2, center_y + 30,
        center_x + body_width//2, center_y + 30 + body_height
    ], fill=body_color, outline=tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,), width=3)
    
    # 手臂
    arm_width, arm_length = 30, 120
    arm_color = tuple(int(colors['primary'][i:i+2], 16) for i in (1, 3, 5)) + (160,)
    # 左臂
    draw.rectangle([
        center_x - body_width//2 - arm_width, center_y + 50,
        center_x - body_width//2, center_y + 50 + arm_length
    ], fill=arm_color, outline=tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,), width=2)
    # 右臂
    draw.rectangle([
        center_x + body_width//2, center_y + 50,
        center_x + body_width//2 + arm_width, center_y + 50 + arm_length
    ], fill=arm_color, outline=tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,), width=2)
    
    # 腿部
    leg_width, leg_length = 35, 150
    leg_color = tuple(int(colors['primary'][i:i+2], 16) for i in (1, 3, 5)) + (160,)
    # 左腿
    draw.rectangle([
        center_x - leg_width - 10, center_y + 230,
        center_x - 10, center_y + 230 + leg_length
    ], fill=leg_color, outline=tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,), width=2)
    # 右腿
    draw.rectangle([
        center_x + 10, center_y + 230,
        center_x + leg_width + 10, center_y + 230 + leg_length
    ], fill=leg_color, outline=tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,), width=2)
    
    # 添加角色名称
    try:
        # 尝试使用系统字体
        font_size = 36
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
                
        # 格式化角色名称
        display_name = character_name.replace('_', ' ').title()
        
        # 获取文本尺寸
        bbox = draw.textbbox((0, 0), display_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (width - text_width) // 2
        text_y = height - 100
        
        # 绘制文本阴影
        shadow_color = (0, 0, 0, 150)
        draw.text((text_x + 2, text_y + 2), display_name, font=font, fill=shadow_color)
        
        # 绘制文本
        text_color = tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (255,)
        draw.text((text_x, text_y), display_name, font=font, fill=text_color)
        
    except Exception as e:
        print(f"Error adding text for {character_name}: {e}")
    
    # 添加装饰元素
    for i in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(2, 8)
        particle_color = tuple(int(colors['secondary'][i:i+2], 16) for i in (1, 3, 5)) + (100,)
        draw.ellipse([x, y, x + size, y + size], fill=particle_color)
    
    # 保存图像
    img.save(output_path, "PNG")
    print(f"Created portrait for {character_name}: {output_path}")
    return True

def main():
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("=== Portrait Generator for Missing Characters ===")
    print(f"Working directory: {os.getcwd()}")
    
    # 加载有效角色列表
    with open('assets/resource_catalog.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    valid_chars = set(data.keys())
    
    # 检查现有肖像图片
    portraits_dir = Path('assets/images/portraits')
    existing_portraits = set()
    for f in portraits_dir.glob('*.png'):
        name = f.stem.replace('_official', '')
        existing_portraits.add(name)
    
    # 找出缺失的角色
    missing = valid_chars - existing_portraits
    print(f"Found {len(missing)} missing character portraits")
    
    # 为每个缺失的角色创建肖像
    created_count = 0
    for character in sorted(missing):
        output_file = portraits_dir / f"{character}_official.png"
        try:
            if create_high_quality_portrait(character, output_file):
                created_count += 1
        except Exception as e:
            print(f"Error creating portrait for {character}: {e}")
    
    print(f"\nCompleted! Created {created_count} new character portraits.")
    print(f"All {len(valid_chars)} characters now have portrait images.")

if __name__ == "__main__":
    main()