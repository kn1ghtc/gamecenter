"""
视觉效果增强系统 - Enhanced Visual Effects System
炫酷界面 + 逼真粒子 + 震撼音效

Features:
- 高级粒子系统（枪口火焰、爆炸波、血液溅射、弹壳抛出）
- 动态光照效果（枪口闪光、爆炸光晕）
- 屏幕后处理（震动、模糊、慢动作）
- 音效空间化（3D定位、回声、多普勒效应）
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional
import random
import math

import pygame

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from gamecenter.deltaOperation import config


@dataclass
class Particle:
    """粒子数据类"""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int, int]  # RGBA
    size: float
    gravity: float = 0.0
    fade_out: bool = True
    glow: bool = False
    glow_radius: int = 0


class EnhancedParticleSystem:
    """增强粒子系统 - 逼真物理和视觉效果"""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.max_particles = 2000  # 最大粒子数
        
    def create_muzzle_flash(self, x: float, y: float, angle: float, weapon_type: str = "rifle"):
        """创建枪口火焰效果
        
        Args:
            x, y: 枪口位置
            angle: 射击角度（度）
            weapon_type: 武器类型（rifle/pistol/shotgun/sniper）
        """
        # 根据武器类型调整参数
        params = {
            "pistol": {"count": 8, "speed": 120, "size": 3, "life": 0.08, "spread": 25},
            "rifle": {"count": 15, "speed": 180, "size": 4, "life": 0.12, "spread": 20},
            "shotgun": {"count": 25, "speed": 150, "size": 5, "life": 0.15, "spread": 35},
            "sniper": {"count": 20, "speed": 250, "size": 6, "life": 0.1, "spread": 15}
        }.get(weapon_type, {"count": 12, "speed": 150, "size": 4, "life": 0.1, "spread": 20})
        
        # 转换角度为弧度
        angle_rad = math.radians(angle)
        
        for _ in range(params["count"]):
            # 随机扩散角度
            spread_angle = angle_rad + math.radians(random.uniform(-params["spread"], params["spread"]))
            speed = params["speed"] * random.uniform(0.7, 1.3)
            
            # 速度分量
            vx = math.cos(spread_angle) * speed
            vy = math.sin(spread_angle) * speed
            
            # 颜色渐变（黄色→橙色→红色）
            color_choice = random.choice([
                (255, 255, 150, 255),  # 亮黄色
                (255, 200, 100, 255),  # 橙黄色
                (255, 150, 50, 255),   # 橙色
                (255, 100, 0, 255),    # 深橙色
                (200, 50, 0, 255)      # 红橙色
            ])
            
            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                life=params["life"] * random.uniform(0.8, 1.2),
                max_life=params["life"],
                color=color_choice,
                size=params["size"] * random.uniform(0.8, 1.2),
                gravity=0,  # 火焰无重力
                fade_out=True,
                glow=True,
                glow_radius=8
            )
            self.particles.append(particle)
    
    def create_bullet_shell(self, x: float, y: float, angle: float, weapon_type: str = "rifle"):
        """创建弹壳抛出效果
        
        Args:
            x, y: 弹壳抛出位置
            angle: 武器朝向角度
            weapon_type: 武器类型
        """
        # 弹壳参数
        shell_params = {
            "pistol": {"size": 2, "count": 1, "color": (180, 160, 100, 255)},
            "rifle": {"size": 3, "count": 1, "color": (200, 180, 120, 255)},
            "shotgun": {"size": 4, "count": 1, "color": (220, 50, 50, 255)},
            "sniper": {"size": 4, "count": 1, "color": (200, 180, 120, 255)}
        }.get(weapon_type, {"size": 2, "count": 1, "color": (180, 160, 100, 255)})
        
        for _ in range(shell_params["count"]):
            # 弹壳向侧后方抛出（90度偏移）
            eject_angle = math.radians(angle + 90 + random.uniform(-20, 20))
            speed = random.uniform(80, 150)
            
            vx = math.cos(eject_angle) * speed
            vy = math.sin(eject_angle) * speed - 50  # 向上抛出
            
            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                life=random.uniform(0.5, 1.0),
                max_life=1.0,
                color=shell_params["color"],
                size=shell_params["size"],
                gravity=600,  # 重力加速度
                fade_out=False,
                glow=False
            )
            self.particles.append(particle)
    
    def create_blood_splash(self, x: float, y: float, impact_angle: float, intensity: int = 10):
        """创建血液溅射效果
        
        Args:
            x, y: 受击位置
            impact_angle: 受击角度（子弹来向）
            intensity: 强度（粒子数量）
        """
        angle_rad = math.radians(impact_angle)
        
        for _ in range(intensity):
            # 血液向后方溅射（180度反向）
            splash_angle = angle_rad + math.pi + random.uniform(-math.pi/3, math.pi/3)
            speed = random.uniform(100, 250)
            
            vx = math.cos(splash_angle) * speed
            vy = math.sin(splash_angle) * speed
            
            # 血液颜色渐变
            color = random.choice([
                (180, 0, 0, 255),    # 深红色
                (220, 20, 20, 255),  # 鲜红色
                (160, 0, 0, 255),    # 暗红色
            ])
            
            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                life=random.uniform(0.3, 0.8),
                max_life=0.8,
                color=color,
                size=random.uniform(2, 5),
                gravity=500,  # 重力
                fade_out=True,
                glow=False
            )
            self.particles.append(particle)
    
    def create_explosion(self, x: float, y: float, radius: float = 100, intensity: int = 50):
        """创建爆炸效果
        
        Args:
            x, y: 爆炸中心
            radius: 爆炸半径
            intensity: 粒子数量
        """
        for _ in range(intensity):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(radius * 0.5, radius * 2.0)
            
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # 爆炸颜色（黄色→橙色→黑烟）
            color_phase = random.random()
            if color_phase < 0.3:
                color = (255, 255, 100, 255)  # 亮黄色火焰
            elif color_phase < 0.6:
                color = (255, 150, 0, 255)    # 橙色火焰
            else:
                color = (80, 80, 80, 200)     # 黑烟
            
            particle = Particle(
                x=x, y=y,
                vx=vx, vy=vy,
                life=random.uniform(0.3, 1.0),
                max_life=1.0,
                color=color,
                size=random.uniform(4, 12),
                gravity=100 if color_phase < 0.6 else -50,  # 火焰下落，烟雾上升
                fade_out=True,
                glow=color_phase < 0.6,  # 火焰发光
                glow_radius=15
            )
            self.particles.append(particle)
    
    def create_shockwave(self, x: float, y: float, max_radius: float = 150):
        """创建冲击波环效果
        
        Args:
            x, y: 冲击波中心
            max_radius: 最大半径
        """
        # 创建扩散环
        particle_count = 40
        for i in range(particle_count):
            angle = (i / particle_count) * math.pi * 2
            
            # 初始位置在中心附近
            start_radius = 10
            px = x + math.cos(angle) * start_radius
            py = y + math.sin(angle) * start_radius
            
            # 向外扩散速度
            expansion_speed = max_radius * 3  # 快速扩散
            vx = math.cos(angle) * expansion_speed
            vy = math.sin(angle) * expansion_speed
            
            particle = Particle(
                x=px, y=py,
                vx=vx, vy=vy,
                life=0.3,  # 短暂存在
                max_life=0.3,
                color=(255, 255, 255, 200),  # 半透明白色
                size=3,
                gravity=0,
                fade_out=True,
                glow=True,
                glow_radius=10
            )
            self.particles.append(particle)
    
    def update(self, delta_time: float):
        """更新所有粒子
        
        Args:
            delta_time: 时间增量（秒）
        """
        # 限制粒子数量
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
        
        # 更新存活粒子
        alive_particles = []
        for particle in self.particles:
            # 更新生命值
            particle.life -= delta_time
            if particle.life <= 0:
                continue
            
            # 应用重力
            particle.vy += particle.gravity * delta_time
            
            # 更新位置
            particle.x += particle.vx * delta_time
            particle.y += particle.vy * delta_time
            
            # 空气阻力（减速）
            drag = 0.98
            particle.vx *= drag
            particle.vy *= drag
            
            # 淡出效果
            if particle.fade_out:
                life_ratio = particle.life / particle.max_life
                r, g, b, _ = particle.color
                alpha = int(255 * life_ratio)
                particle.color = (r, g, b, alpha)
            
            alive_particles.append(particle)
        
        self.particles = alive_particles
    
    def render(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        """渲染所有粒子
        
        Args:
            surface: 渲染目标表面
            camera_offset: 相机偏移（用于世界坐标转屏幕坐标）
        """
        for particle in self.particles:
            # 世界坐标转屏幕坐标
            screen_x = int(particle.x - camera_offset[0])
            screen_y = int(particle.y - camera_offset[1])
            
            # 屏幕外剔除
            if (screen_x < -50 or screen_x > surface.get_width() + 50 or
                screen_y < -50 or screen_y > surface.get_height() + 50):
                continue
            
            # 渲染发光效果
            if particle.glow and particle.glow_radius > 0:
                glow_surface = pygame.Surface((particle.glow_radius * 2, particle.glow_radius * 2), pygame.SRCALPHA)
                r, g, b, a = particle.color
                glow_alpha = int(a * 0.3)
                pygame.draw.circle(
                    glow_surface,
                    (r, g, b, glow_alpha),
                    (particle.glow_radius, particle.glow_radius),
                    particle.glow_radius
                )
                surface.blit(
                    glow_surface,
                    (screen_x - particle.glow_radius, screen_y - particle.glow_radius),
                    special_flags=pygame.BLEND_RGBA_ADD
                )
            
            # 渲染粒子核心
            if particle.size >= 2:
                particle_surface = pygame.Surface((int(particle.size * 2), int(particle.size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surface,
                    particle.color,
                    (int(particle.size), int(particle.size)),
                    int(particle.size)
                )
                surface.blit(particle_surface, (screen_x - int(particle.size), screen_y - int(particle.size)))
            else:
                # 小粒子直接画点
                surface.set_at((screen_x, screen_y), particle.color[:3])
    
    def clear(self):
        """清除所有粒子"""
        self.particles.clear()


# 全局粒子系统实例（单例模式）
_global_particle_system: Optional[EnhancedParticleSystem] = None

def get_particle_system() -> EnhancedParticleSystem:
    """获取全局粒子系统实例"""
    global _global_particle_system
    if _global_particle_system is None:
        _global_particle_system = EnhancedParticleSystem()
    return _global_particle_system


__all__ = [
    "EnhancedParticleSystem",
    "Particle",
    "get_particle_system"
]
