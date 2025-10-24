"""粒子效果系统 - 视觉特效"""
import pygame
import random
import math
from typing import List, Tuple

from gamecenter.deltaOperation.core.physics import Vector2D


class Particle:
    """单个粒子"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float,
                 lifetime: float, color: Tuple[int, int, int, int],
                 size: float = 3.0):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(vx, vy)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.gravity = 0.2
        
    def update(self, delta_time: float) -> bool:
        """更新粒子
        
        Returns:
            粒子是否存活
        """
        self.lifetime -= delta_time
        
        if self.lifetime <= 0:
            return False
            
        # 更新位置
        self.position.x += self.velocity.x * delta_time * 60
        self.position.y += self.velocity.y * delta_time * 60
        
        # 重力
        self.velocity.y += self.gravity
        
        # 摩擦
        self.velocity.x *= 0.98
        self.velocity.y *= 0.98
        
        return True
        
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """渲染粒子"""
        # 计算alpha(根据生命值衰减)
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color[:3], alpha)
        
        # 计算大小(根据生命值缩小)
        size = self.size * (self.lifetime / self.max_lifetime)
        
        # 屏幕坐标
        screen_x = int(self.position.x - camera_x)
        screen_y = int(self.position.y - camera_y)
        
        # 渲染圆形粒子
        if size >= 1.0:
            try:
                pygame.draw.circle(screen, color, (screen_x, screen_y), int(size))
            except:
                pass  # 超出屏幕范围


class ParticleSystem:
    """粒子系统管理器"""
    
    def __init__(self):
        self.particles: List[Particle] = []
        
    def emit_muzzle_flash(self, x: float, y: float, angle: float):
        """枪口火光"""
        for _ in range(10):
            # 在枪口方向喷射粒子
            spread = random.uniform(-0.3, 0.3)
            speed = random.uniform(2, 5)
            
            vx = math.cos(angle + spread) * speed
            vy = math.sin(angle + spread) * speed
            
            color = random.choice([
                (255, 200, 0),   # 黄色
                (255, 150, 0),   # 橙色
                (255, 100, 0)    # 橙红色
            ])
            
            lifetime = random.uniform(0.1, 0.3)
            size = random.uniform(2, 4)
            
            particle = Particle(x, y, vx, vy, lifetime, color, size)
            self.particles.append(particle)
            
    def emit_shell_casing(self, x: float, y: float, facing_right: bool):
        """弹壳抛出"""
        for _ in range(1):
            # 向侧后方抛出
            vx = random.uniform(2, 4) * (-1 if facing_right else 1)
            vy = random.uniform(-3, -1)
            
            color = (200, 180, 100)
            lifetime = random.uniform(0.5, 1.0)
            size = 2.0
            
            particle = Particle(x, y, vx, vy, lifetime, color, size)
            particle.gravity = 0.5  # 弹壳重力更大
            self.particles.append(particle)
            
    def emit_blood_splat(self, x: float, y: float, direction: float):
        """血液溅射"""
        for _ in range(15):
            spread = random.uniform(-0.5, 0.5)
            speed = random.uniform(3, 8)
            
            vx = math.cos(direction + spread) * speed
            vy = math.sin(direction + spread) * speed
            
            color = (180, 0, 0)  # 深红色
            lifetime = random.uniform(0.3, 0.6)
            size = random.uniform(1, 3)
            
            particle = Particle(x, y, vx, vy, lifetime, color, size)
            particle.gravity = 0.3
            self.particles.append(particle)
            
    def emit_explosion(self, x: float, y: float, intensity: float = 1.0):
        """爆炸效果"""
        num_particles = int(30 * intensity)
        
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 15) * intensity
            
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = random.choice([
                (255, 100, 0),   # 橙色
                (255, 200, 0),   # 黄色
                (100, 100, 100), # 灰色(烟雾)
                (50, 50, 50)     # 黑色(烟雾)
            ])
            
            lifetime = random.uniform(0.3, 1.0)
            size = random.uniform(3, 8) * intensity
            
            particle = Particle(x, y, vx, vy, lifetime, color, size)
            particle.gravity = random.uniform(-0.1, 0.3)  # 烟雾上升
            self.particles.append(particle)
            
    def emit_dust(self, x: float, y: float, amount: int = 5):
        """灰尘/脚步"""
        for _ in range(amount):
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, 0)
            
            color = (150, 150, 150)
            lifetime = random.uniform(0.2, 0.5)
            size = random.uniform(1, 2)
            
            particle = Particle(x, y, vx, vy, lifetime, color, size)
            particle.gravity = 0.1
            self.particles.append(particle)
            
    def update(self, delta_time: float):
        """更新所有粒子"""
        # 更新并移除死亡粒子
        self.particles = [p for p in self.particles if p.update(delta_time)]
        
    def render(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """渲染所有粒子"""
        for particle in self.particles:
            particle.render(screen, camera_x, camera_y)
            
    def clear(self):
        """清空所有粒子"""
        self.particles.clear()
        
    def get_particle_count(self) -> int:
        """获取粒子数量"""
        return len(self.particles)
