#!/usr/bin/env python3
"""
为KOF角色生成精灵图动画资源
"""
import os
import json
from pathlib import Path
from PIL import Image, ImageDraw
import random

class KOFSpriteAnimationGenerator:
    def __init__(self):
        self.sprites_dir = Path("assets/sprites")
        self.portraits_dir = Path("assets/images/portraits")
        
        # 动画状态配置
        self.animation_states = {
            'idle': {'frames': 4, 'duration': 2.0, 'loop': True},
            'walk': {'frames': 6, 'duration': 1.2, 'loop': True},
            'attack': {'frames': 8, 'duration': 0.8, 'loop': False},
            'hurt': {'frames': 3, 'duration': 0.6, 'loop': False},
            'victory': {'frames': 6, 'duration': 2.4, 'loop': False},
            'defeat': {'frames': 4, 'duration': 1.6, 'loop': False},
            'jump': {'frames': 5, 'duration': 1.0, 'loop': False},
            'block': {'frames': 2, 'duration': 0.8, 'loop': True},
            'special': {'frames': 10, 'duration': 1.5, 'loop': False}
        }
        
        # 角色配色方案（从portraits生成器继承）
        self.character_colors = {
            'kyo_kusanagi': {'primary': '#ff4444', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'iori_yagami': {'primary': '#aa44ff', 'secondary': '#ffffff', 'accent': '#ff0000'},
            'terry_bogard': {'primary': '#4444ff', 'secondary': '#ffff44', 'accent': '#ffffff'},
            'andy_bogard': {'primary': '#ffffff', 'secondary': '#4444ff', 'accent': '#ffaa00'},
            'joe_higashi': {'primary': '#ffaa00', 'secondary': '#ffffff', 'accent': '#ff4444'},
            'mai_shiranui': {'primary': '#ff4444', 'secondary': '#ffff44', 'accent': '#ffffff'},
            'ryo_sakazaki': {'primary': '#ffaa00', 'secondary': '#ffffff', 'accent': '#ff4444'},
            'robert_garcia': {'primary': '#ffff44', 'secondary': '#aa44ff', 'accent': '#ffffff'},
            'yuri_sakazaki': {'primary': '#ffaa00', 'secondary': '#ffffff', 'accent': '#44ff44'},
            'leona_heidern': {'primary': '#44ff44', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'athena_asamiya': {'primary': '#aa44ff', 'secondary': '#ffff44', 'accent': '#ffffff'},
            'sie_kensou': {'primary': '#ffff44', 'secondary': '#aa44ff', 'accent': '#ffffff'},
            'goro_daimon': {'primary': '#ffffff', 'secondary': '#4444ff', 'accent': '#ffaa00'},
            'chizuru_kagura': {'primary': '#aa44ff', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'kula_diamond': {'primary': '#44ffff', 'secondary': '#ffffff', 'accent': '#aa44ff'},
            'k_dash': {'primary': '#000000', 'secondary': '#ffaa00', 'accent': '#ff4444'},
            'maxima': {'primary': '#ffaa00', 'secondary': '#000000', 'accent': '#ff4444'},
            'whip': {'primary': '#44ff44', 'secondary': '#000000', 'accent': '#ffffff'},
            'vanessa': {'primary': '#ff4444', 'secondary': '#ffffff', 'accent': '#000000'},
            'mature': {'primary': '#aa44ff', 'secondary': '#000000', 'accent': '#ff4444'},
            'vice': {'primary': '#ff4444', 'secondary': '#aa44ff', 'accent': '#ffffff'},
            'shermie': {'primary': '#ffff44', 'secondary': '#aa44ff', 'accent': '#ffffff'},
            'chris': {'primary': '#ffaa00', 'secondary': '#ffffff', 'accent': '#ff4444'},
            'ash_crimson': {'primary': '#44ff44', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'geese_howard': {'primary': '#ffaa00', 'secondary': '#000000', 'accent': '#ffffff'},
            'b_jenet': {'primary': '#4444ff', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'gato': {'primary': '#ffffff', 'secondary': '#000000', 'accent': '#ff4444'},
            'nakoruru': {'primary': '#44ff44', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'shunei': {'primary': '#aa44ff', 'secondary': '#ffaa00', 'accent': '#ffffff'},
            'isla': {'primary': '#ff4444', 'secondary': '#44ff44', 'accent': '#ffffff'},
            'dolores': {'primary': '#ffaa00', 'secondary': '#aa44ff', 'accent': '#ffffff'},
            'shingo_yabuki': {'primary': '#ffaa00', 'secondary': '#ffffff', 'accent': '#ff4444'},
            # 新增的12个角色
            'angel': {'primary': '#44ffff', 'secondary': '#ffffff', 'accent': '#aa44ff'},
            'choi_bounge': {'primary': '#44ff44', 'secondary': '#ffaa00', 'accent': '#ff4444'},
            'goro_daimon': {'primary': '#4444ff', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'igniz': {'primary': '#aa44ff', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'lin': {'primary': '#ff4444', 'secondary': '#000000', 'accent': '#ffffff'},
            'magaki': {'primary': '#000000', 'secondary': '#aa44ff', 'accent': '#ffaa00'},
            'mr_big': {'primary': '#ffaa00', 'secondary': '#000000', 'accent': '#ffffff'},
            'orochi': {'primary': '#000000', 'secondary': '#aa44ff', 'accent': '#ff4444'},
            'ramon': {'primary': '#ffaa00', 'secondary': '#ff4444', 'accent': '#ffffff'},
            'saisyu_kusanagi': {'primary': '#ff4444', 'secondary': '#ffffff', 'accent': '#ffaa00'},
            'wolfgang_krauser': {'primary': '#4444ff', 'secondary': '#ffaa00', 'accent': '#ffffff'}
        }
    
    def hex_to_rgb(self, hex_color):
        """将hex颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def load_valid_characters(self):
        """从resource_catalog.json加载有效角色列表"""
        catalog_path = Path("assets/resource_catalog.json")
        if not catalog_path.exists():
            print(f"Error: {catalog_path} not found!")
            return set()
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return set(data.keys())
    
    def create_sprite_animation(self, character_name, animation_name, config):
        """为指定角色和动画创建精灵图序列"""
        frames = config['frames']
        
        # 获取角色配色
        colors = self.character_colors.get(character_name, {
            'primary': '#4444ff', 
            'secondary': '#ffffff', 
            'accent': '#ffaa00'
        })
        
        primary_rgb = self.hex_to_rgb(colors['primary'])
        secondary_rgb = self.hex_to_rgb(colors['secondary'])
        accent_rgb = self.hex_to_rgb(colors['accent'])
        
        sprites = []
        
        for frame_idx in range(frames):
            # 创建64x64的精灵图
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 计算动画进度
            progress = frame_idx / max(1, frames - 1)
            
            # 根据动画类型绘制不同的形状
            if animation_name == 'idle':
                # 空闲动画：轻微摆动
                offset_y = int(2 * abs(progress - 0.5))
                self._draw_character_base(draw, 32, 32 - offset_y, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'walk':
                # 行走动画：左右移动
                offset_x = int(4 * (progress - 0.5))
                leg_offset = int(3 * abs(progress - 0.5))
                self._draw_character_walking(draw, 32 + offset_x, 32, leg_offset, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'attack':
                # 攻击动画：向前伸展
                extend = int(8 * progress) if progress < 0.5 else int(8 * (1 - progress))
                self._draw_character_attacking(draw, 32, 32, extend, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'hurt':
                # 受伤动画：后退和闪烁
                offset_x = -int(6 * progress)
                alpha = 128 if frame_idx % 2 else 255
                hurt_color = (min(255, primary_rgb[0] + 50), primary_rgb[1], primary_rgb[2], alpha)
                self._draw_character_base(draw, 32 + offset_x, 32, hurt_color[:3], secondary_rgb, accent_rgb)
                
            elif animation_name == 'victory':
                # 胜利动画：举手庆祝
                arm_height = int(8 * min(progress * 2, 1))
                self._draw_character_victory(draw, 32, 32, arm_height, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'defeat':
                # 失败动画：倒下
                fall_offset = int(16 * progress)
                self._draw_character_defeated(draw, 32, 32 + fall_offset, progress, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'jump':
                # 跳跃动画：上下移动
                jump_height = int(12 * (1 - 4 * (progress - 0.5) ** 2))  # 抛物线
                self._draw_character_base(draw, 32, 32 - jump_height, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'block':
                # 格挡动画：防御姿态
                block_offset = 2 if frame_idx % 2 else 0
                self._draw_character_blocking(draw, 32 - block_offset, 32, primary_rgb, secondary_rgb, accent_rgb)
                
            elif animation_name == 'special':
                # 特殊技能动画：能量效果
                energy_intensity = int(100 * abs(progress - 0.5))
                self._draw_character_special(draw, 32, 32, energy_intensity, primary_rgb, secondary_rgb, accent_rgb)
            
            else:
                # 默认：基础形状
                self._draw_character_base(draw, 32, 32, primary_rgb, secondary_rgb, accent_rgb)
            
            sprites.append(img)
        
        return sprites
    
    def _draw_character_base(self, draw, x, y, primary, secondary, accent):
        """绘制角色基础形状"""
        # 头部
        draw.ellipse([x-6, y-20, x+6, y-8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 身体
        draw.rectangle([x-4, y-8, x+4, y+8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 手臂
        draw.rectangle([x-8, y-4, x-4, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+4, y-4, x+8, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
        # 腿部
        draw.rectangle([x-3, y+8, x-1, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+1, y+8, x+3, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
    
    def _draw_character_walking(self, draw, x, y, leg_offset, primary, secondary, accent):
        """绘制行走动画"""
        # 头部
        draw.ellipse([x-6, y-20, x+6, y-8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 身体
        draw.rectangle([x-4, y-8, x+4, y+8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 摆动的手臂
        draw.rectangle([x-8-leg_offset, y-4, x-4, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+4, y-4, x+8+leg_offset, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
        # 交替的腿部
        draw.rectangle([x-3+leg_offset, y+8, x-1, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+1-leg_offset, y+8, x+3, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
    
    def _draw_character_attacking(self, draw, x, y, extend, primary, secondary, accent):
        """绘制攻击动画"""
        # 头部
        draw.ellipse([x-6, y-20, x+6, y-8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 身体
        draw.rectangle([x-4, y-8, x+4, y+8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 攻击手臂（延伸）
        draw.rectangle([x+4, y-4, x+8+extend, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
        # 另一只手臂
        draw.rectangle([x-8, y-4, x-4, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
        # 腿部
        draw.rectangle([x-3, y+8, x-1, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+1, y+8, x+3, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
        
        # 攻击特效
        if extend > 0:
            draw.ellipse([x+8+extend-3, y-6, x+8+extend+3, y+6], fill=accent + (128,))
    
    def _draw_character_victory(self, draw, x, y, arm_height, primary, secondary, accent):
        """绘制胜利动画"""
        # 头部
        draw.ellipse([x-6, y-20, x+6, y-8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 身体
        draw.rectangle([x-4, y-8, x+4, y+8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 举起的手臂
        draw.rectangle([x-8, y-4-arm_height, x-4, y+4-arm_height], fill=accent + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+4, y-4-arm_height, x+8, y+4-arm_height], fill=accent + (255,), outline=secondary + (255,), width=1)
        # 腿部
        draw.rectangle([x-3, y+8, x-1, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+1, y+8, x+3, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
    
    def _draw_character_defeated(self, draw, x, y, progress, primary, secondary, accent):
        """绘制失败动画"""
        # 倒下的角色（旋转效果模拟）
        if progress < 1.0:
            # 头部
            draw.ellipse([x-6, y-20, x+6, y-8], fill=primary + (255,), outline=secondary + (255,), width=1)
            # 身体（倾斜）
            offset = int(8 * progress)
            draw.rectangle([x-4+offset, y-8, x+4+offset, y+8], fill=primary + (255,), outline=secondary + (255,), width=1)
            # 手臂
            draw.rectangle([x-8+offset, y-4, x-4+offset, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
            draw.rectangle([x+4+offset, y-4, x+8+offset, y+4], fill=accent + (255,), outline=secondary + (255,), width=1)
            # 腿部
            draw.rectangle([x-3+offset, y+8, x-1+offset, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
            draw.rectangle([x+1+offset, y+8, x+3+offset, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
    
    def _draw_character_blocking(self, draw, x, y, primary, secondary, accent):
        """绘制格挡动画"""
        # 头部
        draw.ellipse([x-6, y-20, x+6, y-8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 身体
        draw.rectangle([x-4, y-8, x+4, y+8], fill=primary + (255,), outline=secondary + (255,), width=1)
        # 防御手臂（交叉）
        draw.rectangle([x-2, y-6, x+2, y+2], fill=accent + (255,), outline=secondary + (255,), width=1)
        # 腿部（稳固姿态）
        draw.rectangle([x-4, y+8, x-2, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
        draw.rectangle([x+2, y+8, x+4, y+16], fill=primary + (255,), outline=secondary + (255,), width=1)
    
    def _draw_character_special(self, draw, x, y, energy, primary, secondary, accent):
        """绘制特殊技能动画"""
        # 角色本体
        self._draw_character_base(draw, x, y, primary, secondary, accent)
        
        # 能量光环
        if energy > 0:
            for i in range(3):
                radius = 15 + i * 5 + energy // (10 + i * 2)
                alpha = max(50, 200 - energy + i * 20)
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                           outline=accent + (alpha,), width=2)
    
    def create_character_animations(self, character_name):
        """为指定角色创建所有动画"""
        print(f"为角色 {character_name} 生成精灵动画...")
        
        character_dir = self.sprites_dir / character_name
        character_dir.mkdir(exist_ok=True)
        
        manifest_data = {
            'character': character_name,
            'animations': {},
            'format': 'png',
            'frame_size': [64, 64]
        }
        
        for anim_name, config in self.animation_states.items():
            print(f"  生成 {anim_name} 动画 ({config['frames']} 帧)")
            
            # 生成动画帧
            sprites = self.create_sprite_animation(character_name, anim_name, config)
            
            # 保存每一帧
            frame_files = []
            for i, sprite in enumerate(sprites):
                frame_filename = f"{anim_name}_{i:03d}.png"
                frame_path = character_dir / frame_filename
                sprite.save(frame_path, "PNG")
                frame_files.append(frame_filename)
            
            # 更新manifest
            manifest_data['animations'][anim_name] = {
                'frames': frame_files,
                'duration': config['duration'],
                'loop': config['loop'],
                'fps': config['frames'] / config['duration']
            }
        
        # 保存manifest文件
        manifest_path = character_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ {character_name} 动画生成完成")
        return True
    
    def generate_all_character_animations(self):
        """为所有角色生成精灵动画"""
        print("=== KOF精灵动画生成器 ===")
        print(f"输出目录: {self.sprites_dir.absolute()}")
        
        valid_characters = self.load_valid_characters()
        
        if not valid_characters:
            print("未找到有效角色列表")
            return False
        
        print(f"发现 {len(valid_characters)} 个角色，开始生成精灵动画...")
        
        success_count = 0
        total_count = len(valid_characters)
        
        for i, character in enumerate(sorted(valid_characters), 1):
            print(f"\n[{i}/{total_count}] 处理角色: {character}")
            
            try:
                if self.create_character_animations(character):
                    success_count += 1
            except Exception as e:
                print(f"  ✗ 生成失败: {e}")
        
        print(f"\n=== 生成完成 ===")
        print(f"成功生成: {success_count}/{total_count} 个角色的精灵动画")
        
        return success_count == total_count

def main():
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"工作目录: {os.getcwd()}")
    
    generator = KOFSpriteAnimationGenerator()
    success = generator.generate_all_character_animations()
    
    if success:
        print("\n🎉 所有角色精灵动画生成完成!")
    else:
        print("\n⚠️  部分角色动画生成失败，请检查错误信息")

if __name__ == "__main__":
    main()