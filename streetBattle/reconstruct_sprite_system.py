#!/usr/bin/env python3
"""
精灵图系统重构工具
基于particles目录的真实角色图片，为每个角色生成专属的精灵动画序列
替换通用的hero精灵图系统
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import math
import random

class SpriteSystemReconstructor:
    def __init__(self):
        self.assets_dir = Path(__file__).parent / "assets"
        self.sprites_dir = self.assets_dir / "sprites"
        self.particles_dir = self.assets_dir / "particles"
        
        # Load character data
        self.characters = self._load_characters()
        
        # Sprite animation configurations
        self.sprite_configs = {
            'idle': {'frames': 4, 'duration': 0.8, 'description': '待机动画'},
            'walk': {'frames': 6, 'duration': 0.6, 'description': '行走动画'},
            'attack': {'frames': 4, 'duration': 0.4, 'description': '攻击动画'},
            'jump': {'frames': 3, 'duration': 0.3, 'description': '跳跃动画'},
            'hit': {'frames': 2, 'duration': 0.2, 'description': '受击动画'},
            'victory': {'frames': 3, 'duration': 1.0, 'description': '胜利动画'}
        }
        
        print(f"精灵图系统重构器初始化完成")
        print(f"- 角色数量: {len(self.characters)}")
        print(f"- 动画类型: {len(self.sprite_configs)}")
        
    def _load_characters(self):
        """加载角色配置"""
        manifest_path = self.assets_dir / "characters_manifest_complete.json"
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'characters' in data:
                    return {char['id']: char for char in data['characters']}
        return {}
    
    def create_sprite_animation(self, char_id, char_data, animation_type, config):
        """为角色创建特定类型的精灵动画"""
        # 检查particles图片是否存在
        particle_path = self.particles_dir / f"{char_id}.png"
        if not particle_path.exists():
            print(f"⚠️  粒子图片不存在: {char_id}")
            return None
            
        try:
            # 加载基础粒子图片
            base_image = Image.open(particle_path)
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            # 创建动画帧
            frames = []
            frame_count = config['frames']
            
            for frame_idx in range(frame_count):
                # 基于动画类型创建变换
                frame = self._create_animation_frame(
                    base_image.copy(), 
                    animation_type, 
                    frame_idx, 
                    frame_count
                )
                frames.append(frame)
            
            return frames
            
        except Exception as e:
            print(f"❌ 创建精灵动画失败 {char_id}:{animation_type} - {e}")
            return None
    
    def _create_animation_frame(self, base_image, animation_type, frame_idx, total_frames):
        """创建单个动画帧"""
        size = base_image.size
        frame = base_image.copy()
        
        # 计算动画进度 (0.0 到 1.0)
        progress = frame_idx / max(1, total_frames - 1)
        
        if animation_type == 'idle':
            # 待机动画：轻微的呼吸效果和位置摆动
            breath_offset = int(math.sin(progress * 2 * math.pi) * 3)
            sway_offset = int(math.cos(progress * 2 * math.pi) * 2)
            
            # 创建新图片，稍微调整位置
            new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
            new_frame.paste(frame, (sway_offset, breath_offset), frame)
            frame = new_frame
            
        elif animation_type == 'walk':
            # 行走动画：上下摆动和轻微的倾斜
            bob_offset = int(math.sin(progress * 2 * math.pi) * 8)
            lean_angle = int(math.sin(progress * 2 * math.pi) * 3)
            
            # 应用上下摆动
            new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
            new_frame.paste(frame, (0, bob_offset), frame)
            
            # 轻微旋转（模拟倾斜）
            if lean_angle != 0:
                new_frame = new_frame.rotate(lean_angle, expand=False, fillcolor=(0, 0, 0, 0))
            
            frame = new_frame
            
        elif animation_type == 'attack':
            # 攻击动画：前冲和缩放效果
            if frame_idx == 0:
                # 准备阶段：缩小
                frame = frame.resize((int(size[0] * 0.9), int(size[1] * 0.9)), Image.Resampling.LANCZOS)
                # 居中
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                offset = ((size[0] - frame.width) // 2, (size[1] - frame.height) // 2)
                new_frame.paste(frame, offset, frame)
                frame = new_frame
            elif frame_idx == 1 or frame_idx == 2:
                # 攻击阶段：放大和前移
                scale = 1.1 if frame_idx == 1 else 1.05
                frame = frame.resize((int(size[0] * scale), int(size[1] * scale)), Image.Resampling.LANCZOS)
                # 前移
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                forward_offset = 15 if frame_idx == 1 else 10
                offset = (forward_offset, (size[1] - frame.height) // 2)
                new_frame.paste(frame, offset, frame)
                frame = new_frame
            # frame_idx == 3: 恢复阶段，使用原图
            
        elif animation_type == 'jump':
            # 跳跃动画：垂直位移和拉伸
            if frame_idx == 0:
                # 蹲下准备
                frame = frame.resize((int(size[0] * 1.1), int(size[1] * 0.8)), Image.Resampling.LANCZOS)
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                offset = ((size[0] - frame.width) // 2, size[1] - frame.height)
                new_frame.paste(frame, offset, frame)
                frame = new_frame
            elif frame_idx == 1:
                # 空中拉伸
                frame = frame.resize((int(size[0] * 0.9), int(size[1] * 1.2)), Image.Resampling.LANCZOS)
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                offset = ((size[0] - frame.width) // 2, -20)  # 向上偏移
                new_frame.paste(frame, offset, frame)
                frame = new_frame
            # frame_idx == 2: 落地，使用原图
            
        elif animation_type == 'hit':
            # 受击动画：后退和闪烁效果
            if frame_idx == 0:
                # 受击瞬间：后退和变红
                enhancer = ImageEnhance.Color(frame)
                frame = enhancer.enhance(0.5)  # 降低饱和度
                # 添加红色叠加
                red_overlay = Image.new('RGBA', size, (255, 100, 100, 100))
                frame = Image.alpha_composite(frame, red_overlay)
                # 后退
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                new_frame.paste(frame, (-20, 0), frame)
                frame = new_frame
            # frame_idx == 1: 恢复，使用原图
            
        elif animation_type == 'victory':
            # 胜利动画：放大和发光效果
            if frame_idx == 0:
                # 第一帧：轻微放大
                frame = frame.resize((int(size[0] * 1.05), int(size[1] * 1.05)), Image.Resampling.LANCZOS)
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                offset = ((size[0] - frame.width) // 2, (size[1] - frame.height) // 2)
                new_frame.paste(frame, offset, frame)
                frame = new_frame
            elif frame_idx == 1:
                # 第二帧：最大放大和发光
                frame = frame.resize((int(size[0] * 1.1), int(size[1] * 1.1)), Image.Resampling.LANCZOS)
                # 添加发光效果
                enhancer = ImageEnhance.Brightness(frame)
                frame = enhancer.enhance(1.2)
                new_frame = Image.new('RGBA', size, (0, 0, 0, 0))
                offset = ((size[0] - frame.width) // 2, (size[1] - frame.height) // 2)
                new_frame.paste(frame, offset, frame)
                frame = new_frame
            # frame_idx == 2: 恢复到稍微放大的状态，类似frame_idx == 0
        
        return frame
    
    def create_character_sprite_set(self, char_id, char_data):
        """为单个角色创建完整的精灵图集"""
        char_name = char_data.get('name', char_id)
        print(f"🎨 创建精灵图集: {char_name} ({char_id})")
        
        # 创建角色专属目录
        char_sprite_dir = self.sprites_dir / char_id
        char_sprite_dir.mkdir(exist_ok=True)
        
        # 生成每种动画的精灵图
        sprite_manifest = {
            'character_id': char_id,
            'character_name': char_name,
            'category': char_data.get('category', 'Fighter'),
            'tier': char_data.get('tier', 'B'),
            'animations': {},
            'generated_at': '2025-09-28'
        }
        
        success_count = 0
        for anim_type, config in self.sprite_configs.items():
            frames = self.create_sprite_animation(char_id, char_data, anim_type, config)
            if frames:
                # 保存动画帧
                anim_dir = char_sprite_dir / anim_type
                anim_dir.mkdir(exist_ok=True)
                
                frame_paths = []
                for i, frame in enumerate(frames):
                    frame_path = anim_dir / f"frame_{i:02d}.png"
                    frame.save(frame_path, "PNG")
                    frame_paths.append(f"{anim_type}/frame_{i:02d}.png")
                
                # 记录到manifest
                sprite_manifest['animations'][anim_type] = {
                    'frames': len(frames),
                    'duration': config['duration'],
                    'description': config['description'],
                    'frame_paths': frame_paths
                }
                
                success_count += 1
                print(f"   ✅ {anim_type}: {len(frames)} 帧")
            else:
                print(f"   ❌ {anim_type}: 创建失败")
        
        # 保存角色精灵图manifest
        manifest_path = char_sprite_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(sprite_manifest, f, indent=2, ensure_ascii=False)
        
        print(f"   📋 Manifest: {manifest_path}")
        print(f"   ✨ 完成 {success_count}/{len(self.sprite_configs)} 个动画")
        
        return success_count > 0
    
    def reconstruct_all_sprites(self):
        """重构所有角色的精灵图系统"""
        print(f"🔧 开始重构精灵图系统...")
        print(f"=" * 60)
        
        success_count = 0
        total_characters = len(self.characters)
        
        for char_id, char_data in self.characters.items():
            try:
                if self.create_character_sprite_set(char_id, char_data):
                    success_count += 1
            except Exception as e:
                print(f"❌ 角色 {char_id} 精灵图创建失败: {e}")
        
        # 创建全局精灵图索引
        self._create_global_sprite_index()
        
        print(f"\n🎉 精灵图系统重构完成!")
        print(f"   成功: {success_count}/{total_characters} 个角色")
        print(f"   动画类型: {len(self.sprite_configs)} 种")
        print(f"   总精灵图: ~{success_count * len(self.sprite_configs) * 4} 个")
        
        return success_count
    
    def _create_global_sprite_index(self):
        """创建全局精灵图索引"""
        global_index = {
            'sprite_system_version': '2.0',
            'generated_at': '2025-09-28',
            'animation_types': list(self.sprite_configs.keys()),
            'characters': {},
            'total_characters': len(self.characters)
        }
        
        for char_id, char_data in self.characters.items():
            manifest_path = self.sprites_dir / char_id / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        char_manifest = json.load(f)
                    
                    global_index['characters'][char_id] = {
                        'name': char_data.get('name', char_id),
                        'category': char_data.get('category', 'Fighter'),
                        'tier': char_data.get('tier', 'B'),
                        'sprite_directory': char_id,
                        'available_animations': list(char_manifest.get('animations', {}).keys()),
                        'total_frames': sum(anim.get('frames', 0) for anim in char_manifest.get('animations', {}).values())
                    }
                except Exception as e:
                    print(f"⚠️  无法读取 {char_id} 的manifest: {e}")
        
        # 保存全局索引
        index_path = self.sprites_dir / "sprites_global_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(global_index, f, indent=2, ensure_ascii=False)
        
        print(f"📋 创建全局精灵图索引: {index_path}")
        print(f"   包含 {len(global_index['characters'])} 个角色的精灵图数据")


def main():
    reconstructor = SpriteSystemReconstructor()
    
    print("🎮 精灵图系统重构工具")
    print("将particles真实图片转换为角色专属精灵动画")
    print("=" * 60)
    
    # 重构所有精灵图
    success_count = reconstructor.reconstruct_all_sprites()
    
    if success_count > 0:
        print(f"\n✨ 重构任务完成!")
        print(f"   - 生成角色精灵图: {success_count} 个")
        print(f"   - 动画类型覆盖: idle, walk, attack, jump, hit, victory")
        print(f"   - 每个角色包含: ~24个精灵帧")
        print(f"   - 存储位置: {reconstructor.sprites_dir}")
        
        print(f"\n📝 后续任务:")
        print(f"   1. 更新游戏代码以使用新的精灵图系统")
        print(f"   2. 移除旧的hero通用精灵图依赖")
        print(f"   3. 测试所有角色的动画显示效果")
    else:
        print(f"\n❌ 重构任务失败，未成功生成任何精灵图")


if __name__ == "__main__":
    main()