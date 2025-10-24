"""相机系统 - 跟随玩家、平滑移动、屏幕震动"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT.parent))

import pygame
from typing import Optional, Tuple
import math
import random

from gamecenter.deltaOperation import config


class Camera:
    """游戏相机系统
    
    功能:
    - 跟随目标(玩家)
    - 平滑移动(lerp插值)
    - 屏幕震动效果
    - 缩放功能
    - 边界限制
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 相机位置(世界坐标中心)
        self.x = 0.0
        self.y = 0.0
        
        # 目标位置
        self.target_x = 0.0
        self.target_y = 0.0
        
        # 平滑跟随参数
        self.smooth_speed = 0.1  # 0-1之间,越大越快
        
        # 缩放
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.zoom_speed = 0.05
        
        # 屏幕震动
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0
        
        # 边界限制
        self.bounds_enabled = True
        self.min_x = 0.0
        self.min_y = 0.0
        self.max_x = float('inf')
        self.max_y = float('inf')
        
        # 前瞻(look ahead) - 相机会稍微偏向玩家移动方向
        self.look_ahead_enabled = True
        self.look_ahead_distance = 100.0
        self.look_ahead_speed = 0.05
        self.look_ahead_x = 0.0
        self.look_ahead_y = 0.0
        
    def set_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float):
        """设置相机边界
        
        Args:
            min_x, min_y: 左上角坐标
            max_x, max_y: 右下角坐标
        """
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        
    def follow(self, target_x: float, target_y: float, velocity_x: float = 0, velocity_y: float = 0):
        """设置跟随目标
        
        Args:
            target_x, target_y: 目标位置
            velocity_x, velocity_y: 目标速度(用于前瞻)
        """
        self.target_x = target_x
        self.target_y = target_y
        
        # 前瞻计算
        if self.look_ahead_enabled:
            look_ahead_target_x = velocity_x * self.look_ahead_distance
            look_ahead_target_y = velocity_y * self.look_ahead_distance
            
            # 平滑过渡前瞻偏移
            self.look_ahead_x += (look_ahead_target_x - self.look_ahead_x) * self.look_ahead_speed
            self.look_ahead_y += (look_ahead_target_y - self.look_ahead_y) * self.look_ahead_speed
            
    def update(self, delta_time: float):
        """更新相机状态
        
        Args:
            delta_time: 时间步长
        """
        # 平滑跟随目标
        target_with_look_ahead_x = self.target_x + self.look_ahead_x
        target_with_look_ahead_y = self.target_y + self.look_ahead_y
        
        self.x += (target_with_look_ahead_x - self.x) * self.smooth_speed
        self.y += (target_with_look_ahead_y - self.y) * self.smooth_speed
        
        # 平滑缩放
        self.zoom += (self.target_zoom - self.zoom) * self.zoom_speed
        
        # 边界限制
        if self.bounds_enabled:
            half_width = (self.screen_width / 2) / self.zoom
            half_height = (self.screen_height / 2) / self.zoom
            
            self.x = max(self.min_x + half_width, min(self.x, self.max_x - half_width))
            self.y = max(self.min_y + half_height, min(self.y, self.max_y - half_height))
            
        # 更新屏幕震动
        if self.shake_duration > 0:
            self.shake_duration -= delta_time
            
            # 随机震动偏移
            angle = random.uniform(0, math.pi * 2)
            self.shake_offset_x = math.cos(angle) * self.shake_intensity
            self.shake_offset_y = math.sin(angle) * self.shake_intensity
            
            # 震动衰减
            self.shake_intensity *= 0.9
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0
            
    def shake(self, intensity: float, duration: float = 0.3):
        """触发屏幕震动
        
        Args:
            intensity: 震动强度(像素)
            duration: 持续时间(秒)
        """
        self.shake_intensity = intensity
        self.shake_duration = duration
        
    def set_zoom(self, zoom: float):
        """设置目标缩放级别
        
        Args:
            zoom: 缩放倍数(1.0=正常,>1放大,<1缩小)
        """
        self.target_zoom = max(0.5, min(zoom, 3.0))  # 限制在0.5-3.0之间
        
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """世界坐标转屏幕坐标
        
        Args:
            world_x, world_y: 世界坐标
            
        Returns:
            (screen_x, screen_y): 屏幕坐标
        """
        screen_x = (world_x - self.x) * self.zoom + self.screen_width / 2 + self.shake_offset_x
        screen_y = (world_y - self.y) * self.zoom + self.screen_height / 2 + self.shake_offset_y
        
        return (int(screen_x), int(screen_y))
        
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """屏幕坐标转世界坐标
        
        Args:
            screen_x, screen_y: 屏幕坐标
            
        Returns:
            (world_x, world_y): 世界坐标
        """
        world_x = (screen_x - self.screen_width / 2 - self.shake_offset_x) / self.zoom + self.x
        world_y = (screen_y - self.screen_height / 2 - self.shake_offset_y) / self.zoom + self.y
        
        return (world_x, world_y)
        
    def get_viewport_rect(self) -> Tuple[float, float, float, float]:
        """获取相机视口在世界坐标中的矩形区域
        
        Returns:
            (x, y, width, height): 视口矩形
        """
        width = self.screen_width / self.zoom
        height = self.screen_height / self.zoom
        
        x = self.x - width / 2
        y = self.y - height / 2
        
        return (x, y, width, height)
        
    def is_visible(self, world_x: float, world_y: float, obj_width: float = 0, obj_height: float = 0) -> bool:
        """检测对象是否在相机视野内
        
        Args:
            world_x, world_y: 对象世界坐标
            obj_width, obj_height: 对象尺寸
            
        Returns:
            True如果在视野内
        """
        vp_x, vp_y, vp_width, vp_height = self.get_viewport_rect()
        
        return (world_x + obj_width >= vp_x and
                world_x <= vp_x + vp_width and
                world_y + obj_height >= vp_y and
                world_y <= vp_y + vp_height)
                
    def apply_transform(self, surface: pygame.Surface) -> pygame.Surface:
        """应用相机变换到Surface
        
        Args:
            surface: 世界渲染Surface
            
        Returns:
            变换后的Surface
        """
        if self.zoom != 1.0:
            scaled_width = int(surface.get_width() * self.zoom)
            scaled_height = int(surface.get_height() * self.zoom)
            surface = pygame.transform.scale(surface, (scaled_width, scaled_height))
            
        return surface
        
    def reset(self):
        """重置相机到默认状态"""
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.shake_intensity = 0
        self.shake_duration = 0
        self.look_ahead_x = 0
        self.look_ahead_y = 0
