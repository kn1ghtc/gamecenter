#!/usr/bin/env python3
"""
图片资源管理器
加载和管理游戏中的所有图片资源
"""

import pygame
import os

class ImageManager:
    """图片资源管理器"""
    
    def __init__(self):
        self.images = {}
        self.backgrounds = {}
        self.sprites = {}
        self.weapons = {}
        self._load_images()
    
    def _load_images(self):
        """加载所有图片资源"""
        # 获取游戏根目录
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        images_dir = os.path.join(current_dir, "assets", "images")
        
        # 图片文件映射
        image_files = {
            'player_sprite': 'player_sprite.png',
            'enemy_sprite': 'enemy_sprite.png',
            'background_forest': 'background_forest.png',
            'background_desert': 'background_desert.png',
            'background_snow': 'background_snow.png',
            'platform_sprite': 'platform_sprite.png',
            'weapon_knife': 'weapon_knife.png',
            'weapon_gun': 'weapon_gun.png',
            'weapon_bomb': 'weapon_bomb.png'
        }
        
        loaded_count = 0
        
        # 加载图片文件
        for image_name, filename in image_files.items():
            # 使用原始路径（Windows兼容）
            original_path = os.path.join(images_dir, filename)
            
            if os.path.exists(original_path):
                try:
                    image = pygame.image.load(original_path).convert_alpha()
                    self.images[image_name] = image
                    
                    # 分类存储
                    if 'background' in image_name:
                        self.backgrounds[image_name] = image
                    elif 'sprite' in image_name:
                        self.sprites[image_name] = image
                    elif 'weapon' in image_name:
                        self.weapons[image_name] = image
                    
                    loaded_count += 1
                except Exception as e:
                    pass  # 静默处理加载失败
        
        print(f"图片系统就绪 ({loaded_count} 个资源)")
    
    def get_image(self, name):
        """获取图片"""
        return self.images.get(name)
    
    def get_background(self, theme):
        """根据主题获取背景"""
        bg_name = f"background_{theme}"
        return self.backgrounds.get(bg_name)
    
    def get_sprite(self, sprite_type):
        """获取精灵图片"""
        return self.sprites.get(f"{sprite_type}_sprite")
    
    def get_weapon_icon(self, weapon_type):
        """获取武器图标"""
        return self.weapons.get(f"weapon_{weapon_type.lower()}")
    
    def get_scaled_image(self, name, width, height):
        """获取缩放后的图片"""
        image = self.get_image(name)
        if image:
            return pygame.transform.scale(image, (width, height))
        return None
    
    def get_scaled_background(self, theme, width, height):
        """获取缩放后的背景"""
        image = self.get_background(theme)
        if image:
            return pygame.transform.scale(image, (width, height))
        return None
