#!/usr/bin/env python3
"""
Enhanced VFX System for 2.5D Mode
增强版2.5D模式特效系统
"""

try:
    import pygame
    from pygame import Surface, Rect
    import math
    import random
    from typing import List, Tuple, Dict, Optional
except ImportError:
    pygame = None

class EnhancedParticle:
    """增强粒子类"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 color: Tuple[int, int, int, int], size: float, 
                 lifetime: float, particle_type: str = "spark"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.particle_type = particle_type
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-180, 180)
        
    def update(self, dt: float) -> bool:
        """更新粒子，返回是否还活着"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # 重力影响
        if self.particle_type in ["spark", "debris"]:
            self.vy += 300 * dt  # 重力加速度
        
        # 空气阻力
        friction = 0.98
        self.vx *= friction
        self.vy *= friction
        
        # 旋转
        self.rotation += self.rotation_speed * dt
        
        # 生命周期
        self.lifetime -= dt
        
        # 尺寸衰减
        life_ratio = self.lifetime / self.max_lifetime
        self.size *= 0.995
        
        # 颜色alpha衰减
        alpha = int(self.color[3] * life_ratio)
        self.color = (self.color[0], self.color[1], self.color[2], max(0, alpha))
        
        return self.lifetime > 0 and self.size > 0.5

class EnhancedVFXSystem:
    """增强VFX系统"""
    
    def __init__(self, screen_width: int = 1280, screen_height: int = 720):
        if pygame is None:
            raise RuntimeError("Pygame is required for Enhanced VFX System")
            
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles: List[EnhancedParticle] = []
        self.screen_shake = 0.0
        self.screen_shake_decay = 8.0
        
        # 预创建粒子纹理
        self._create_particle_textures()
        
        # 攻击轨迹线条
        self.attack_trails: List[Dict] = []
        
    def _create_particle_textures(self):
        """创建粒子纹理"""
        self.textures: Dict[str, Surface] = {}
        
        # 火花纹理
        spark_size = 16
        spark_surface = Surface((spark_size, spark_size), pygame.SRCALPHA)
        for i in range(spark_size):
            for j in range(spark_size):
                distance = math.sqrt((i - spark_size//2)**2 + (j - spark_size//2)**2)
                if distance <= spark_size//2:
                    alpha = int(255 * (1 - distance / (spark_size//2)))
                    spark_surface.set_at((i, j), (255, 255, 100, alpha))
        self.textures["spark"] = spark_surface
        
        # 能量球纹理
        energy_size = 24
        energy_surface = Surface((energy_size, energy_size), pygame.SRCALPHA)
        center = energy_size // 2
        for i in range(energy_size):
            for j in range(energy_size):
                distance = math.sqrt((i - center)**2 + (j - center)**2)
                if distance <= center:
                    alpha = int(255 * (1 - distance / center) ** 0.5)
                    intensity = int(200 * (1 - distance / center))
                    energy_surface.set_at((i, j), (100, 150, 255, alpha))
        self.textures["energy"] = energy_surface
        
        # 爆炸纹理
        explosion_size = 32
        explosion_surface = Surface((explosion_size, explosion_size), pygame.SRCALPHA)
        center = explosion_size // 2
        for i in range(explosion_size):
            for j in range(explosion_size):
                distance = math.sqrt((i - center)**2 + (j - center)**2)
                if distance <= center:
                    alpha = int(255 * (1 - distance / center) ** 2)
                    red = int(255 * (1 - distance / center))
                    explosion_surface.set_at((i, j), (red, 100, 50, alpha))
        self.textures["explosion"] = explosion_surface
    
    def create_hit_effect(self, x: float, y: float, effect_type: str = "light"):
        """创建打击特效"""
        particle_count = {
            "light": 15, 
            "medium": 20,
            "heavy": 25, 
            "special": 40
        }.get(effect_type, 15)
        
        colors = {
            "light": [(255, 200, 100, 255), (255, 150, 50, 255)],
            "medium": [(255, 180, 120, 255), (200, 120, 80, 255)],
            "heavy": [(100, 150, 255, 255), (150, 200, 255, 255)],
            "special": [(255, 100, 255, 255), (200, 50, 255, 255)]
        }
        
        effect_colors = colors.get(effect_type, colors["light"])
        
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = random.choice(effect_colors)
            size = random.uniform(3, 8)
            lifetime = random.uniform(0.5, 1.2)
            
            particle = EnhancedParticle(x, y, vx, vy, color, size, lifetime, "spark")
            self.particles.append(particle)
        
        # 屏幕震动
        shake_intensity = {
            "light": 3.0, 
            "medium": 4.5,
            "heavy": 6.0, 
            "special": 10.0
        }.get(effect_type, 3.0)
        
        self.screen_shake = max(self.screen_shake, shake_intensity)
    
    def create_punch_trail(self, start_x: float, start_y: float, 
                          end_x: float, end_y: float, 
                          color: Tuple[int, int, int] = (255, 200, 100)):
        """创建出拳轨迹特效"""
        trail_data = {
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'color': color,
            'alpha': 220,
            'lifetime': 0.12,
            'max_lifetime': 0.12,
            'width': 8
        }
        self.attack_trails.append(trail_data)
        
        # 沿轨迹创建粒子
        steps = 5
        for i in range(steps):
            t = i / steps
            px = start_x + (end_x - start_x) * t
            py = start_y + (end_y - start_y) * t
            
            # 添加轨迹粒子
            offset_x = random.uniform(-5, 5)
            offset_y = random.uniform(-5, 5)
            
            vx = random.uniform(-50, 50)
            vy = random.uniform(-50, 50)
            
            particle_color = (*color, 200)
            size = random.uniform(2, 4)
            lifetime = random.uniform(0.2, 0.4)
            
            particle = EnhancedParticle(
                px + offset_x, py + offset_y, 
                vx, vy, 
                particle_color, size, lifetime, "spark"
            )
            self.particles.append(particle)
    
    def create_kick_trail(self, center_x: float, center_y: float,
                         direction: float, radius: float = 80):
        """创建出腿轨迹特效（弧形）"""
        # 创建弧形轨迹粒子
        arc_steps = 8
        start_angle = direction - math.pi / 4
        end_angle = direction + math.pi / 4
        
        for i in range(arc_steps):
            t = i / arc_steps
            angle = start_angle + (end_angle - start_angle) * t
            
            px = center_x + math.cos(angle) * radius
            py = center_y + math.sin(angle) * radius
            
            # 速度沿切线方向
            tangent_angle = angle + math.pi / 2
            speed = random.uniform(100, 200)
            vx = math.cos(tangent_angle) * speed
            vy = math.sin(tangent_angle) * speed
            
            color = (150, 200, 255, 220)
            size = random.uniform(3, 6)
            lifetime = random.uniform(0.3, 0.5)
            
            particle = EnhancedParticle(px, py, vx, vy, color, size, lifetime, "spark")
            self.particles.append(particle)
    
    def create_impact_ring(self, x: float, y: float, max_radius: float = 60):
        """创建冲击波环特效"""
        ring_particles = 20
        for i in range(ring_particles):
            angle = (2 * math.pi * i) / ring_particles
            
            # 环形扩散
            speed = random.uniform(200, 350)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = (255, 255, 200, 255)
            size = random.uniform(4, 7)
            lifetime = random.uniform(0.4, 0.7)
            
            particle = EnhancedParticle(x, y, vx, vy, color, size, lifetime, "spark")
            self.particles.append(particle)
    
    def create_projectile_trail(self, x: float, y: float, direction: Tuple[float, float]):
        """创建投射物轨迹特效"""
        for _ in range(8):
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            
            vx = -direction[0] * random.uniform(50, 150) + random.uniform(-50, 50)
            vy = -direction[1] * random.uniform(50, 150) + random.uniform(-50, 50)
            
            color = (100, 200, 255, 200)
            size = random.uniform(2, 5)
            lifetime = random.uniform(0.3, 0.8)
            
            particle = EnhancedParticle(x + offset_x, y + offset_y, vx, vy, 
                                      color, size, lifetime, "energy")
            self.particles.append(particle)
    
    def create_special_aura(self, x: float, y: float, character_name: str = "default"):
        """创建角色特殊气场特效"""
        aura_colors = {
            "ryu": [(255, 255, 255, 150), (200, 200, 255, 100)],
            "kyo_kusanagi": [(255, 100, 0, 150), (255, 200, 100, 100)],
            "iori_yagami": [(150, 0, 255, 150), (100, 50, 200, 100)],
            "default": [(255, 215, 0, 150), (255, 255, 100, 100)]
        }
        
        colors = aura_colors.get(character_name, aura_colors["default"])
        
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(30, 80)
            orbit_speed = random.uniform(60, 120)
            
            orbit_x = x + math.cos(angle) * radius
            orbit_y = y + math.sin(angle) * radius
            
            vx = math.cos(angle + math.pi/2) * orbit_speed
            vy = math.sin(angle + math.pi/2) * orbit_speed
            
            color = random.choice(colors)
            size = random.uniform(4, 10)
            lifetime = random.uniform(1.0, 2.0)
            
            particle = EnhancedParticle(orbit_x, orbit_y, vx, vy, 
                                      color, size, lifetime, "energy")
            self.particles.append(particle)
    
    def update(self, dt: float):
        """更新VFX系统"""
        # 更新粒子
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # 更新屏幕震动
        if self.screen_shake > 0:
            self.screen_shake -= self.screen_shake_decay * dt
            self.screen_shake = max(0, self.screen_shake)
        
        # 更新攻击轨迹
        for trail in list(self.attack_trails):
            trail['lifetime'] -= dt
            if trail['lifetime'] > 0:
                # 更新透明度
                life_ratio = trail['lifetime'] / trail['max_lifetime']
                trail['alpha'] = int(220 * life_ratio)
                trail['width'] = int(8 * life_ratio)
            else:
                self.attack_trails.remove(trail)
    
    def render(self, screen: Surface, camera_offset: Tuple[float, float] = (0, 0)):
        """渲染VFX特效"""
        # 应用屏幕震动
        shake_x = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
        # 渲染攻击轨迹线条
        for trail in self.attack_trails:
            if trail['alpha'] > 0 and trail['width'] > 0:
                start_pos = (
                    int(trail['start'][0] - camera_offset[0] + shake_x),
                    int(trail['start'][1] - camera_offset[1] + shake_y)
                )
                end_pos = (
                    int(trail['end'][0] - camera_offset[0] + shake_x),
                    int(trail['end'][1] - camera_offset[1] + shake_y)
                )
                
                # 创建带透明度的线条
                temp_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                pygame.draw.line(
                    temp_surface,
                    (*trail['color'], trail['alpha']),
                    start_pos,
                    end_pos,
                    trail['width']
                )
                screen.blit(temp_surface, (0, 0))
        
        # 渲染粒子
        for particle in self.particles:
            # 计算屏幕位置
            screen_x = int(particle.x - camera_offset[0] + shake_x)
            screen_y = int(particle.y - camera_offset[1] + shake_y)
            
            # 检查是否在屏幕内
            if (-50 <= screen_x <= self.screen_width + 50 and 
                -50 <= screen_y <= self.screen_height + 50):
                
                # 获取合适的纹理
                texture = self.textures.get(particle.particle_type, self.textures["spark"])
                
                # 缩放纹理
                scaled_size = max(1, int(particle.size))
                if scaled_size != texture.get_width():
                    scaled_texture = pygame.transform.scale(texture, (scaled_size, scaled_size))
                else:
                    scaled_texture = texture
                
                # 应用颜色调制
                colored_texture = scaled_texture.copy()
                colored_texture.fill(particle.color[:3], special_flags=pygame.BLEND_MULT)
                
                # 应用旋转
                if particle.rotation != 0:
                    colored_texture = pygame.transform.rotate(colored_texture, particle.rotation)
                
                # 设置alpha
                colored_texture.set_alpha(particle.color[3])
                
                # 绘制到屏幕
                rect = colored_texture.get_rect(center=(screen_x, screen_y))
                screen.blit(colored_texture, rect)
    
    def get_screen_shake_offset(self) -> Tuple[float, float]:
        """获取屏幕震动偏移"""
        if self.screen_shake <= 0:
            return (0, 0)
        
        shake_x = random.uniform(-self.screen_shake, self.screen_shake)
        shake_y = random.uniform(-self.screen_shake, self.screen_shake)
        return (shake_x, shake_y)

# 全局VFX实例
_vfx_system: Optional[EnhancedVFXSystem] = None

def get_vfx_system() -> EnhancedVFXSystem:
    """获取全局VFX系统实例"""
    global _vfx_system
    if _vfx_system is None:
        _vfx_system = EnhancedVFXSystem()
    return _vfx_system

def create_enhanced_hit_effect(x: float, y: float, effect_type: str = "light"):
    """创建增强打击特效"""
    vfx = get_vfx_system()
    vfx.create_hit_effect(x, y, effect_type)

def create_projectile_trail(x: float, y: float, direction: Tuple[float, float]):
    """创建投射物轨迹"""
    vfx = get_vfx_system()
    vfx.create_projectile_trail(x, y, direction)

def create_character_aura(x: float, y: float, character_name: str = "default"):
    """创建角色气场特效"""
    vfx = get_vfx_system()
    vfx.create_special_aura(x, y, character_name)

def create_punch_trail_effect(start_x: float, start_y: float, end_x: float, end_y: float):
    """创建出拳轨迹效果"""
    vfx = get_vfx_system()
    vfx.create_punch_trail(start_x, start_y, end_x, end_y)

def create_kick_trail_effect(center_x: float, center_y: float, direction: float):
    """创建出腿轨迹效果"""
    vfx = get_vfx_system()
    vfx.create_kick_trail(center_x, center_y, direction)

def create_impact_ring_effect(x: float, y: float):
    """创建冲击波环效果"""
    vfx = get_vfx_system()
    vfx.create_impact_ring(x, y)
