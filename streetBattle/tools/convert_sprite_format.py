#!/usr/bin/env python3
"""
转换精灵图动画格式以兼容2.5D模式
将当前的animations格式转换为2.5D模式期望的states格式
"""
import os
import json
from pathlib import Path
from PIL import Image
import math

class SpriteFormatConverter:
    def __init__(self):
        self.sprites_dir = Path("assets/sprites")
        
    def convert_character_manifest(self, character_name):
        """转换单个角色的manifest格式"""
        character_dir = self.sprites_dir / character_name
        manifest_file = character_dir / "manifest.json"
        
        if not manifest_file.exists():
            print(f"✗ {character_name}: manifest.json 不存在")
            return False
        
        try:
            # 读取当前的manifest
            with open(manifest_file, 'r', encoding='utf-8') as f:
                current_manifest = json.load(f)
            
            if "states" in current_manifest:
                # 已经是正确格式
                print(f"✓ {character_name}: 已经是正确的states格式")
                return True
            
            animations = current_manifest.get("animations", {})
            if not animations:
                print(f"✗ {character_name}: 没有animations数据")
                return False
            
            # 创建合成的精灵表单
            created_sheets = {}
            states = {}
            
            for anim_name, anim_data in animations.items():
                frame_files = anim_data.get("frames", [])
                if not frame_files:
                    continue
                
                # 检查帧文件是否存在
                valid_frames = []
                for frame_file in frame_files:
                    frame_path = character_dir / frame_file
                    if frame_path.exists():
                        valid_frames.append(frame_path)
                
                if not valid_frames:
                    print(f"  ⚠️ {anim_name}: 没有有效的帧文件")
                    continue
                
                # 创建精灵表单
                sheet_name = f"{anim_name}_sheet.png"
                sheet_success = self.create_sprite_sheet(valid_frames, character_dir / sheet_name)
                
                if sheet_success:
                    created_sheets[anim_name] = sheet_name
                    
                    # 添加到states配置
                    states[anim_name] = {
                        "sheet": sheet_name,
                        "frame_size": [64, 64],  # 我们生成的精灵图大小
                        "frames": len(valid_frames),
                        "sequence": list(range(len(valid_frames))),
                        "fps": anim_data.get("fps", 8),
                        "loop": anim_data.get("loop", True)
                    }
                    
                    # 添加攻击帧信息
                    if anim_name in ["attack", "special"]:
                        # 攻击动画的命中帧通常在中后段
                        total_frames = len(valid_frames)
                        hit_start = max(1, total_frames // 3)
                        hit_end = min(total_frames - 1, (total_frames * 2) // 3)
                        states[anim_name]["hit_frames"] = list(range(hit_start, hit_end + 1))
            
            if not states:
                print(f"✗ {character_name}: 无法创建任何状态")
                return False
            
            # 创建新的manifest
            new_manifest = {
                "character": character_name,
                "format": "states",
                "states": states,
                "source": f"Generated from individual frames for {character_name}",
                "license": "CC0 - Generated content"
            }
            
            # 保存新的manifest
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(new_manifest, f, indent=2, ensure_ascii=False)
            
            print(f"✓ {character_name}: 转换成功 ({len(states)} 个状态)")
            return True
            
        except Exception as e:
            print(f"✗ {character_name}: 转换失败 - {e}")
            return False
    
    def create_sprite_sheet(self, frame_paths, output_path):
        """将多个帧图片合成为一个精灵表单"""
        try:
            if not frame_paths:
                return False
            
            # 加载第一个帧来获取尺寸
            first_frame = Image.open(frame_paths[0])
            frame_width, frame_height = first_frame.size
            
            # 计算表单布局
            num_frames = len(frame_paths)
            cols = min(8, num_frames)  # 最多8列
            rows = math.ceil(num_frames / cols)
            
            sheet_width = cols * frame_width
            sheet_height = rows * frame_height
            
            # 创建空白表单
            sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
            
            # 将各帧放置到表单中
            for i, frame_path in enumerate(frame_paths):
                frame = Image.open(frame_path).convert('RGBA')
                
                col = i % cols
                row = i // cols
                
                x = col * frame_width
                y = row * frame_height
                
                sheet.paste(frame, (x, y))
            
            # 保存表单
            sheet.save(output_path, 'PNG')
            first_frame.close()
            
            return True
            
        except Exception as e:
            print(f"  创建精灵表单失败: {e}")
            return False
    
    def convert_all_characters(self):
        """转换所有角色的manifest格式"""
        print("=== 精灵图格式转换器 ===")
        print(f"处理目录: {self.sprites_dir.absolute()}")
        
        if not self.sprites_dir.exists():
            print("✗ sprites目录不存在")
            return False
        
        character_dirs = [d for d in self.sprites_dir.iterdir() 
                         if d.is_dir() and not d.name.startswith('.') 
                         and d.name not in ['hero', 'shadow']]
        
        if not character_dirs:
            print("✗ 没有找到角色目录")
            return False
        
        print(f"发现 {len(character_dirs)} 个角色目录")
        
        success_count = 0
        for char_dir in sorted(character_dirs):
            character_name = char_dir.name
            if self.convert_character_manifest(character_name):
                success_count += 1
        
        print(f"\n=== 转换完成 ===")
        print(f"成功转换: {success_count}/{len(character_dirs)} 个角色")
        
        return success_count == len(character_dirs)

def main():
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"工作目录: {os.getcwd()}")
    
    converter = SpriteFormatConverter()
    success = converter.convert_all_characters()
    
    if success:
        print("\n🎉 所有角色manifest格式转换完成!")
        print("现在可以尝试启动2.5D模式了")
    else:
        print("\n⚠️  部分角色转换失败，请检查错误信息")

if __name__ == "__main__":
    main()