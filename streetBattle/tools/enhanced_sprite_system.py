#!/usr/bin/env python3
"""
Enhanced 2.5D Sprite System
增强2.5D精灵系统 - 修复精灵生成和特效问题
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def enhance_sprite_manifest_generation():
    """增强精灵manifest生成系统"""
    print("🎭 增强精灵manifest生成系统")
    print("=" * 40)
    
    # 读取统一角色列表
    unified_list_path = project_root / "assets" / "unified_character_list.json"
    
    if not unified_list_path.exists():
        print(f"❌ 统一角色列表不存在: {unified_list_path}")
        return False
    
    with open(unified_list_path, 'r', encoding='utf-8') as f:
        unified_characters = json.load(f)
    
    # 为每个角色创建增强的manifest
    manifests_created = 0
    
    for char_id, char_info in unified_characters.items():
        if not char_info.get('has_portrait'):
            continue
            
        # 创建角色精灵目录
        sprite_dir = project_root / "assets" / "sprites" / char_id
        sprite_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成增强的manifest.json
        manifest_data = create_enhanced_manifest(char_id, char_info)
        
        manifest_path = sprite_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 创建增强manifest: {char_id}")
        manifests_created += 1
    
    print(f"✅ 成功创建 {manifests_created} 个增强manifest文件")
    return True

def create_enhanced_manifest(char_id, char_info):
    """创建增强的角色manifest配置"""
    
    # 基础动画状态配置
    base_states = {
        "idle": {
            "sheet": f"{char_id}_spritesheet.png",
            "frame_size": [128, 128],
            "sequence": [0, 1, 2, 3],
            "fps": 8,
            "loop": True,
            "durations": [0.15, 0.15, 0.15, 0.15]
        },
        "walk": {
            "sheet": f"{char_id}_spritesheet.png", 
            "frame_size": [128, 128],
            "sequence": [4, 5, 6, 7],
            "fps": 12,
            "loop": True,
            "durations": [0.1, 0.08, 0.1, 0.08]
        },
        "attack_light": {
            "sheet": f"{char_id}_spritesheet.png",
            "frame_size": [128, 128], 
            "sequence": [8, 9, 10, 11],
            "fps": 16,
            "loop": False,
            "hit_frames": [2, 3],
            "durations": [0.06, 0.04, 0.08, 0.12]
        },
        "attack_heavy": {
            "sheet": f"{char_id}_spritesheet.png",
            "frame_size": [128, 128],
            "sequence": [12, 13, 14, 15],
            "fps": 14,
            "loop": False,
            "hit_frames": [2, 3],
            "durations": [0.08, 0.06, 0.1, 0.16]
        },
        "special_move": {
            "sheet": f"{char_id}_spritesheet.png",
            "frame_size": [128, 128],
            "sequence": [16, 17, 18, 19, 20, 21],
            "fps": 12,
            "loop": False,
            "hit_frames": [3, 4, 5],
            "durations": [0.1, 0.08, 0.06, 0.08, 0.1, 0.18]
        },
        "hurt": {
            "sheet": f"{char_id}_spritesheet.png",
            "frame_size": [128, 128],
            "sequence": [22, 23],
            "fps": 8,
            "loop": False,
            "durations": [0.15, 0.2]
        },
        "victory": {
            "sheet": f"{char_id}_spritesheet.png",
            "frame_size": [128, 128],
            "sequence": [24, 25, 26, 27],
            "fps": 6,
            "loop": True,
            "durations": [0.2, 0.15, 0.15, 0.2]
        }
    }
    
    # 角色特定颜色调整
    character_colors = {
        'ryu': {'multiply': [1.0, 1.0, 1.0], 'add': [0, 0, 0]},
        'kyo_kusanagi': {'multiply': [1.1, 0.9, 0.8], 'add': [10, 0, 0]},  # 火焰色调
        'iori_yagami': {'multiply': [0.9, 0.8, 1.1], 'add': [0, 0, 15]},  # 紫色调
        'terry_bogard': {'multiply': [1.0, 1.0, 0.9], 'add': [5, 5, 0]},  # 温暖色调
        'mai_shiranui': {'multiply': [1.1, 0.95, 0.9], 'add': [15, 5, 0]}, # 红色调
    }
    
    color_mod = character_colors.get(char_id, {'multiply': [1.0, 1.0, 1.0], 'add': [0, 0, 0]})
    
    # 完整manifest数据
    manifest = {
        "source": f"Generated from enhanced portrait: {char_info.get('display_name', char_id)}",
        "license": "Educational/Research Use",
        "character_id": char_id,
        "display_name": char_info.get('display_name', char_id.title()),
        "sprite_version": "2.0_enhanced",
        "color_mod": color_mod,
        "states": base_states,
        "metadata": {
            "hit_multiplier": 1.0,
            "speed_multiplier": 1.0,
            "special_effects": True,
            "enhanced_particles": True
        }
    }
    
    return manifest

def generate_enhanced_spritesheet(char_id):
    """从肖像生成增强的精灵图集"""
    print(f"🎨 生成增强精灵图集: {char_id}")
    
    # 获取角色肖像
    portrait_path = project_root / "assets" / "images" / "portraits" / f"{char_id}.png"
    
    if not portrait_path.exists():
        print(f"❌ 肖像不存在: {portrait_path}")
        return False
    
    try:
        # 加载肖像
        portrait = Image.open(portrait_path).convert("RGBA")
        
        # 创建128x128的精灵帧
        sprite_size = (128, 128)
        
        # 创建8x4的精灵图集 (32帧)
        sheet_width = 8 * sprite_size[0]  # 1024px
        sheet_height = 4 * sprite_size[1]  # 512px
        
        spritesheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
        
        # 生成不同动画帧
        for row in range(4):
            for col in range(8):
                frame_index = row * 8 + col
                
                # 创建帧变化
                frame = create_enhanced_sprite_frame(portrait, sprite_size, frame_index)
                
                # 粘贴到精灵图集
                x = col * sprite_size[0]
                y = row * sprite_size[1]
                spritesheet.paste(frame, (x, y))
        
        # 保存精灵图集
        sprite_dir = project_root / "assets" / "sprites" / char_id
        sprite_dir.mkdir(parents=True, exist_ok=True)
        
        spritesheet_path = sprite_dir / f"{char_id}_spritesheet.png"
        spritesheet.save(spritesheet_path, "PNG", optimize=True)
        
        print(f"✓ 精灵图集已保存: {spritesheet_path}")
        return True
        
    except Exception as e:
        print(f"❌ 精灵图集生成失败: {e}")
        return False

def create_enhanced_sprite_frame(portrait, target_size, frame_index):
    """创建增强的精灵帧，包含动画变化"""
    
    # 调整肖像到目标尺寸
    sprite_frame = portrait.copy()
    sprite_frame = sprite_frame.resize(target_size, Image.Resampling.LANCZOS)
    
    # 根据帧索引应用不同的变换
    animation_type = frame_index // 4  # 每4帧一个动画
    frame_in_anim = frame_index % 4
    
    if animation_type == 0:  # idle (0-3)
        # 轻微呼吸动画
        if frame_in_anim in [1, 2]:
            sprite_frame = sprite_frame.resize((target_size[0], target_size[1] + 2), Image.Resampling.LANCZOS)
            sprite_frame = sprite_frame.resize(target_size, Image.Resampling.LANCZOS)
    
    elif animation_type == 1:  # walk (4-7)
        # 左右轻微移动
        offset = [-2, 0, 2, 0][frame_in_anim]
        if offset != 0:
            new_frame = Image.new("RGBA", target_size, (0, 0, 0, 0))
            new_frame.paste(sprite_frame, (offset, 0))
            sprite_frame = new_frame
    
    elif animation_type == 2:  # attack_light (8-11)
        # 攻击闪光效果
        if frame_in_anim in [1, 2]:
            enhancer = ImageEnhance.Brightness(sprite_frame)
            sprite_frame = enhancer.enhance(1.3)
            
            # 添加红色色调
            overlay = Image.new("RGBA", target_size, (255, 100, 100, 30))
            sprite_frame = Image.alpha_composite(sprite_frame, overlay)
    
    elif animation_type == 3:  # attack_heavy (12-15)
        # 重击蓝色闪光
        if frame_in_anim in [1, 2]:
            enhancer = ImageEnhance.Brightness(sprite_frame)
            sprite_frame = enhancer.enhance(1.4)
            
            # 添加蓝色色调
            overlay = Image.new("RGBA", target_size, (100, 100, 255, 40))
            sprite_frame = Image.alpha_composite(sprite_frame, overlay)
    
    elif animation_type == 4:  # special_move (16-21)
        # 特殊技能能量效果
        if frame_in_anim >= 2:
            enhancer = ImageEnhance.Brightness(sprite_frame)
            sprite_frame = enhancer.enhance(1.5)
            
            # 添加金色能量效果
            overlay = Image.new("RGBA", target_size, (255, 215, 0, 50))
            sprite_frame = Image.alpha_composite(sprite_frame, overlay)
    
    elif animation_type == 5:  # hurt (22-23)
        # 受伤红闪
        overlay = Image.new("RGBA", target_size, (255, 0, 0, 60))
        sprite_frame = Image.alpha_composite(sprite_frame, overlay)
    
    elif animation_type == 6:  # victory (24-27)
        # 胜利金光
        enhancer = ImageEnhance.Brightness(sprite_frame)
        sprite_frame = enhancer.enhance(1.2)
        
        overlay = Image.new("RGBA", target_size, (255, 255, 100, 20))
        sprite_frame = Image.alpha_composite(sprite_frame, overlay)
    
    return sprite_frame

def create_enhanced_vfx_system():
    """创建增强的VFX特效系统"""
    print("💥 创建增强VFX特效系统")
    print("=" * 40)
    
    vfx_code = '''#!/usr/bin/env python3
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
        particle_count = {"light": 15, "heavy": 25, "special": 40}[effect_type]
        colors = {
            "light": [(255, 200, 100, 255), (255, 150, 50, 255)],
            "heavy": [(100, 150, 255, 255), (150, 200, 255, 255)],
            "special": [(255, 100, 255, 255), (200, 50, 255, 255)]
        }
        
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            color = random.choice(colors[effect_type])
            size = random.uniform(3, 8)
            lifetime = random.uniform(0.5, 1.2)
            
            particle = EnhancedParticle(x, y, vx, vy, color, size, lifetime, "spark")
            self.particles.append(particle)
        
        # 屏幕震动
        shake_intensity = {"light": 3.0, "heavy": 6.0, "special": 10.0}[effect_type]
        self.screen_shake = max(self.screen_shake, shake_intensity)
    
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
    
    def render(self, screen: Surface, camera_offset: Tuple[float, float] = (0, 0)):
        """渲染VFX特效"""
        # 应用屏幕震动
        shake_x = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
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
'''
    
    # 保存增强VFX系统
    vfx_file = project_root / "twod5" / "enhanced_vfx.py"
    with open(vfx_file, 'w', encoding='utf-8') as f:
        f.write(vfx_code)
    
    print(f"✓ 增强VFX系统已创建: {vfx_file}")
    return True

def batch_generate_enhanced_sprites():
    """批量生成增强精灵系统"""
    print("🎭 批量生成增强精灵系统")
    print("=" * 50)
    
    try:
        # 1. 增强manifest生成
        if not enhance_sprite_manifest_generation():
            print("❌ Manifest生成失败")
            return False
        
        # 2. 读取角色列表
        unified_list_path = project_root / "assets" / "unified_character_list.json"
        with open(unified_list_path, 'r', encoding='utf-8') as f:
            unified_characters = json.load(f)
        
        # 3. 批量生成精灵图集
        successful_sprites = 0
        total_characters = sum(1 for char_info in unified_characters.values() if char_info.get('has_portrait'))
        
        for char_id, char_info in unified_characters.items():
            if not char_info.get('has_portrait'):
                continue
                
            print(f"\n📍 生成精灵图集: {char_id} ({char_info.get('display_name', char_id)})")
            
            if generate_enhanced_spritesheet(char_id):
                successful_sprites += 1
                print(f"✅ {char_id} 精灵图集生成成功")
            else:
                print(f"❌ {char_id} 精灵图集生成失败")
        
        # 4. 创建增强VFX系统
        if not create_enhanced_vfx_system():
            print("❌ VFX系统创建失败")
            return False
        
        # 5. 生成结果报告
        print(f"\n📊 批量生成结果:")
        print(f"✅ 成功生成精灵图集: {successful_sprites}/{total_characters}")
        print(f"✅ 增强manifest系统: 已完成")
        print(f"✅ 增强VFX系统: 已创建")
        
        success_rate = successful_sprites / total_characters if total_characters > 0 else 0
        
        return success_rate >= 0.8  # 80%以上成功率认为成功
        
    except Exception as e:
        print(f"❌ 批量生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🎭 StreetBattle 2.5D精灵系统增强工具")
    print("=" * 60)
    print("修复精灵生成问题，增强战斗特效系统")
    print("=" * 60)
    
    try:
        success = batch_generate_enhanced_sprites()
        
        if success:
            print("\n🎉 2.5D精灵系统增强完成!")
            print("\n✨ 增强功能:")
            print("  ✓ 高质量精灵图集生成")
            print("  ✓ 增强动画帧差异化")
            print("  ✓ 改进的manifest配置")
            print("  ✓ 增强粒子特效系统")
            print("  ✓ 屏幕震动和视觉冲击")
            print("  ✓ 角色专属气场特效")
            
            print("\n🚀 2.5D模式已准备就绪，战斗特效大幅提升!")
        else:
            print("\n⚠️ 部分功能生成失败，请检查错误信息")
        
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