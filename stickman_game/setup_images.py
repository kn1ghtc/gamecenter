#!/usr/bin/env python3
"""
游戏图片资源下载器
从开源站点下载免费图片文件并生成备用图片
"""

import os
import urllib.request
import pygame
from PIL import Image, ImageDraw, ImageFont
import io

# 确保图片目录存在
def ensure_images_directory():
    images_dir = os.path.join("assets", "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    return images_dir

# 免费开源图片文件URL (使用免费资源)
IMAGE_URLS = {
    # 注意：这些是示例URL，实际使用时需要替换为真实的免费资源链接
    'player_sprite': 'https://opengameart.org/sites/default/files/stickman.png',
    'enemy_sprite': 'https://opengameart.org/sites/default/files/enemy.png',
    'background_forest': 'https://opengameart.org/sites/default/files/forest_bg.png',
    'background_desert': 'https://opengameart.org/sites/default/files/desert_bg.png',
    'background_snow': 'https://opengameart.org/sites/default/files/snow_bg.png',
    'platform_sprite': 'https://opengameart.org/sites/default/files/platform.png',
    'weapon_knife': 'https://opengameart.org/sites/default/files/knife.png',
    'weapon_gun': 'https://opengameart.org/sites/default/files/gun.png',
    'weapon_bomb': 'https://opengameart.org/sites/default/files/bomb.png'
}

def download_image_file(url, filename):
    """下载图片文件"""
    try:
        print(f"正在下载: {filename}")
        urllib.request.urlretrieve(url, filename)
        print(f"✅ 下载成功: {filename}")
        return True
    except Exception as e:
        print(f"❌ 下载失败 {filename}: {e}")
        return False

def create_stickman_sprite(width=40, height=40):
    """创建火柴人精灵"""
    # 创建透明背景的图片
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 火柴人颜色
    stick_color = (255, 255, 255, 255)  # 白色
    
    # 头部 (圆形)
    head_radius = width // 8
    head_x = width // 2
    head_y = height // 4
    draw.ellipse([head_x - head_radius, head_y - head_radius, 
                  head_x + head_radius, head_y + head_radius], 
                 outline=stick_color, width=2)
    
    # 身体 (竖线)
    body_start_y = head_y + head_radius
    body_end_y = height * 3 // 4
    draw.line([head_x, body_start_y, head_x, body_end_y], fill=stick_color, width=2)
    
    # 手臂 (横线)
    arm_y = height // 2
    arm_length = width // 3
    draw.line([head_x - arm_length, arm_y, head_x + arm_length, arm_y], 
              fill=stick_color, width=2)
    
    # 腿部 (V形)
    leg_length = height // 4
    draw.line([head_x, body_end_y, head_x - leg_length, height - 2], 
              fill=stick_color, width=2)
    draw.line([head_x, body_end_y, head_x + leg_length, height - 2], 
              fill=stick_color, width=2)
    
    return image

def create_enemy_sprite(width=35, height=35):
    """创建敌人精灵"""
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 敌人颜色 (红色)
    enemy_color = (255, 0, 0, 255)
    
    # 头部 (方形)
    head_size = width // 4
    head_x = width // 2
    head_y = height // 4
    draw.rectangle([head_x - head_size, head_y - head_size,
                    head_x + head_size, head_y + head_size],
                   outline=enemy_color, width=2)
    
    # 身体
    body_start_y = head_y + head_size
    body_end_y = height * 3 // 4
    draw.line([head_x, body_start_y, head_x, body_end_y], fill=enemy_color, width=3)
    
    # 手臂
    arm_y = height // 2
    arm_length = width // 3
    draw.line([head_x - arm_length, arm_y, head_x + arm_length, arm_y], 
              fill=enemy_color, width=2)
    
    # 腿部
    leg_length = height // 4
    draw.line([head_x, body_end_y, head_x - leg_length, height - 2], 
              fill=enemy_color, width=2)
    draw.line([head_x, body_end_y, head_x + leg_length, height - 2], 
              fill=enemy_color, width=2)
    
    return image

def create_background_gradient(width=1000, height=700, theme='forest'):
    """创建渐变背景"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    if theme == 'forest':
        # 森林主题：绿色渐变
        top_color = (50, 100, 50)
        bottom_color = (20, 60, 20)
    elif theme == 'desert':
        # 沙漠主题：黄色渐变
        top_color = (255, 200, 100)
        bottom_color = (200, 150, 50)
    elif theme == 'snow':
        # 雪地主题：蓝白渐变
        top_color = (200, 220, 255)
        bottom_color = (150, 180, 220)
    else:
        # 默认：蓝色渐变
        top_color = (100, 150, 255)
        bottom_color = (50, 100, 200)
    
    # 创建垂直渐变
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return image

def create_platform_sprite(width=100, height=20):
    """创建平台精灵"""
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 平台颜色 (棕色)
    platform_color = (139, 69, 19, 255)
    
    # 绘制平台矩形
    draw.rectangle([0, 0, width-1, height-1], fill=platform_color, outline=(100, 50, 10))
    
    # 添加纹理线条
    for i in range(3):
        y = height // 4 * (i + 1)
        draw.line([5, y, width-5, y], fill=(100, 50, 10), width=1)
    
    return image

def create_weapon_sprite(weapon_type, width=20, height=20):
    """创建武器精灵"""
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    if weapon_type == 'knife':
        # 匕首：银色三角形
        points = [(width//4, height-2), (width//2, 2), (width*3//4, height-2)]
        draw.polygon(points, fill=(192, 192, 192, 255), outline=(128, 128, 128))
        
    elif weapon_type == 'gun':
        # 枪：黑色矩形
        draw.rectangle([2, height//3, width-2, height*2//3], fill=(64, 64, 64, 255))
        draw.rectangle([width-6, height//4, width-2, height*3//4], fill=(32, 32, 32, 255))
        
    elif weapon_type == 'bomb':
        # 炸弹：黑色圆形
        center_x, center_y = width//2, height//2
        radius = min(width, height) // 3
        draw.ellipse([center_x-radius, center_y-radius, 
                      center_x+radius, center_y+radius], 
                     fill=(32, 32, 32, 255))
        # 引线
        draw.line([center_x, center_y-radius, center_x, 2], fill=(255, 255, 0), width=2)
    
    return image

def create_fallback_images():
    """创建备用的程序生成图片"""
    print("🎨 生成程序化图片资源...")
    
    images = {}
    
    # 创建角色精灵
    images['player_sprite'] = create_stickman_sprite(40, 40)
    images['enemy_sprite'] = create_enemy_sprite(35, 35)
    
    # 创建背景图片
    images['background_forest'] = create_background_gradient(1000, 700, 'forest')
    images['background_desert'] = create_background_gradient(1000, 700, 'desert')
    images['background_snow'] = create_background_gradient(1000, 700, 'snow')
    
    # 创建平台精灵
    images['platform_sprite'] = create_platform_sprite(100, 20)
    
    # 创建武器精灵
    images['weapon_knife'] = create_weapon_sprite('knife', 20, 20)
    images['weapon_gun'] = create_weapon_sprite('gun', 20, 20)
    images['weapon_bomb'] = create_weapon_sprite('bomb', 20, 20)
    
    return images

def save_image_to_file(image, filename):
    """保存PIL图片到文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # 保存图片
        if filename.endswith('.png'):
            image.save(filename, 'PNG')
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            # 对于JPEG，需要转换为RGB
            if image.mode == 'RGBA':
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1])
                rgb_image.save(filename, 'JPEG')
            else:
                image.save(filename, 'JPEG')
        else:
            image.save(filename)
        
        return True
    except Exception as e:
        print(f"❌ 保存图片文件失败: {e}")
        return False

def setup_game_images():
    """设置游戏图片系统"""
    images_dir = ensure_images_directory()
    
    print("🎨 设置游戏图片系统...")
    
    # 首先尝试从免费资源下载（这些URL通常需要特殊处理）
    print("🎨 尝试下载图片文件...")
    downloaded_count = 0
    
    # 由于大部分免费图片站点不允许直接下载，我们直接生成程序化图片
    print("🎨 生成程序化图片资源...")
    fallback_images = create_fallback_images()
    
    # 保存图片文件到磁盘
    saved_count = 0
    for image_name, image in fallback_images.items():
        filename = os.path.join(images_dir, f"{image_name}.png")
        if save_image_to_file(image, filename):
            print(f"✅ 保存图片文件: {image_name}.png")
            saved_count += 1
        else:
            print(f"❌ 保存失败: {image_name}.png")
    
    print(f"🎨 图片系统设置完成！保存了 {saved_count} 个图片文件")
    return fallback_images

if __name__ == "__main__":
    setup_game_images()
