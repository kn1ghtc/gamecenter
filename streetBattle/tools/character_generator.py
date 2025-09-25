#!/usr/bin/env python3
"""
程序化角色生成器 - 为格斗游戏创建多样化的角色模型
基于基础模型模板生成不同的角色变体，通过材质、颜色、装备等差异化角色外观

Usage:
    python character_generator.py --generate-all
    python character_generator.py --character kyo_kusanagi --variant fire_master
"""

import os
import json
import random
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CharacterGenerator:
    """程序化角色生成器"""
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = Path(assets_path)
        self.characters_path = self.assets_path / "characters"
        self.templates_path = self.assets_path / "templates"
        self.config_file = self.assets_path / "character_profiles.json"
        
        # 确保目录存在
        self.characters_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)
        
        # 加载角色配置
        self.character_profiles = self._load_character_profiles()
        
    def _load_character_profiles(self) -> Dict[str, Any]:
        """加载角色配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading character profiles: {e}")
        
        # 返回默认配置
        return self._create_default_character_profiles()
    
    def _create_default_character_profiles(self) -> Dict[str, Any]:
        """创建默认角色配置"""
        profiles = {
            "base_templates": {
                "male_fighter": {
                    "base_model": "templates/male_base.egg",
                    "animations": ["idle", "walk", "punch", "kick", "block", "hurt", "victory", "defeat"],
                    "body_type": "athletic"
                },
                "female_fighter": {
                    "base_model": "templates/female_base.egg", 
                    "animations": ["idle", "walk", "punch", "kick", "block", "hurt", "victory", "defeat"],
                    "body_type": "athletic"
                }
            },
            "characters": {
                "kyo_kusanagi": {
                    "name": "Kyo Kusanagi",
                    "template": "male_fighter",
                    "variants": {
                        "classic": {
                            "primary_color": [0.8, 0.1, 0.1],  # 红色
                            "secondary_color": [0.9, 0.9, 0.9],  # 白色
                            "material_type": "fabric",
                            "special_effects": ["fire_particles"],
                            "costume_parts": ["school_uniform", "flame_gloves"]
                        },
                        "fire_master": {
                            "primary_color": [1.0, 0.4, 0.0],  # 橙红色
                            "secondary_color": [0.2, 0.2, 0.2],  # 黑色
                            "material_type": "leather",
                            "special_effects": ["fire_aura", "flame_trail"],
                            "costume_parts": ["battle_suit", "flame_emblem"]
                        }
                    }
                },
                "iori_yagami": {
                    "name": "Iori Yagami",
                    "template": "male_fighter",
                    "variants": {
                        "classic": {
                            "primary_color": [0.1, 0.1, 0.8],  # 蓝色
                            "secondary_color": [0.9, 0.9, 0.9],  # 白色
                            "material_type": "fabric",
                            "special_effects": ["purple_flames"],
                            "costume_parts": ["band_outfit", "claw_gloves"]
                        },
                        "orochi_power": {
                            "primary_color": [0.4, 0.0, 0.4],  # 紫色
                            "secondary_color": [0.1, 0.1, 0.1],  # 黑色
                            "material_type": "mystical",
                            "special_effects": ["dark_aura", "orochi_flames"],
                            "costume_parts": ["torn_clothes", "orochi_marks"]
                        }
                    }
                },
                "mai_shiranui": {
                    "name": "Mai Shiranui",
                    "template": "female_fighter",
                    "variants": {
                        "classic": {
                            "primary_color": [0.8, 0.0, 0.0],  # 红色
                            "secondary_color": [0.9, 0.8, 0.6],  # 米色
                            "material_type": "silk",
                            "special_effects": ["fire_fan", "flame_dance"],
                            "costume_parts": ["ninja_outfit", "fire_fan_prop"]
                        },
                        "modern_ninja": {
                            "primary_color": [0.2, 0.2, 0.8],  # 蓝色
                            "secondary_color": [0.8, 0.8, 0.8],  # 银色
                            "material_type": "tech_fabric",
                            "special_effects": ["energy_fan", "tech_flames"],
                            "costume_parts": ["modern_suit", "tech_fan"]
                        }
                    }
                },
                "terry_bogard": {
                    "name": "Terry Bogard",
                    "template": "male_fighter",
                    "variants": {
                        "classic": {
                            "primary_color": [0.0, 0.0, 0.8],  # 蓝色
                            "secondary_color": [0.8, 0.8, 0.0],  # 黄色
                            "material_type": "denim",
                            "special_effects": ["power_wave"],
                            "costume_parts": ["cap", "jacket", "gloves"]
                        },
                        "wild_wolf": {
                            "primary_color": [0.4, 0.2, 0.0],  # 棕色
                            "secondary_color": [0.8, 0.6, 0.4],  # 皮革色
                            "material_type": "leather",
                            "special_effects": ["wolf_aura", "power_geyser"],
                            "costume_parts": ["leather_jacket", "wolf_emblem"]
                        }
                    }
                }
            }
        }
        
        # 为其余16个角色生成简化配置
        remaining_characters = [
            "andy_bogard", "joe_higashi", "ryo_sakazaki", "robert_garcia",
            "athena_asamiya", "sie_kensou", "chin_gentsai", "leona_heidern",
            "ralf_jones", "clark_still", "yuri_sakazaki", "king",
            "blue_mary", "geese_howard", "chizuru_kagura", "orochi"
        ]
        
        for char in remaining_characters:
            template = "female_fighter" if char in ["athena_asamiya", "leona_heidern", "yuri_sakazaki", "king", "blue_mary", "chizuru_kagura"] else "male_fighter"
            
            profiles["characters"][char] = {
                "name": char.replace('_', ' ').title(),
                "template": template,
                "variants": {
                    "classic": {
                        "primary_color": [random.uniform(0.1, 0.9), random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)],
                        "secondary_color": [random.uniform(0.1, 0.9), random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)],
                        "material_type": random.choice(["fabric", "leather", "metal", "tech_fabric"]),
                        "special_effects": [f"{char}_effect"],
                        "costume_parts": [f"{char}_outfit"]
                    }
                }
            }
        
        # 保存默认配置
        self._save_character_profiles(profiles)
        return profiles
    
    def _save_character_profiles(self, profiles: Dict[str, Any]) -> None:
        """保存角色配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            logger.info(f"Character profiles saved to: {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving character profiles: {e}")
    
    def create_base_templates(self) -> bool:
        """创建基础模板文件"""
        male_template = self.templates_path / "male_base.egg"
        female_template = self.templates_path / "female_base.egg"
        
        # 创建简化的基础.egg模板
        male_egg_content = self._generate_base_egg_template("male")
        female_egg_content = self._generate_base_egg_template("female")
        
        try:
            with open(male_template, 'w', encoding='utf-8') as f:
                f.write(male_egg_content)
            logger.info(f"Created male template: {male_template}")
            
            with open(female_template, 'w', encoding='utf-8') as f:
                f.write(female_egg_content)
            logger.info(f"Created female template: {female_template}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating base templates: {e}")
            return False
    
    def _generate_base_egg_template(self, gender: str) -> str:
        """生成基础.egg模板内容"""
        # 根据性别调整基础尺寸
        height_scale = 1.8 if gender == "male" else 1.6
        width_scale = 1.0 if gender == "male" else 0.9
        
        egg_template = f'''<CoordinateSystem> {{ Z-Up }}

<Material> base_material {{
  <Scalar> ambient {{ 0.2 0.2 0.2 1.0 }}
  <Scalar> diffuse {{ 0.8 0.8 0.8 1.0 }}
  <Scalar> specular {{ 0.1 0.1 0.1 1.0 }}
  <Scalar> shininess {{ 50 }}
}}

<Group> "character_root" {{
  <Transform> {{
    <Matrix4> {{
      {width_scale} 0 0 0
      0 {height_scale} 0 0
      0 0 1 0
      0 0 0 1
    }}
  }}
  
  <Group> "body" {{
    <VertexPool> body_vpool {{
      // 简化的人体几何形状
      <Vertex> 0 {{ 0 0 0 }}
      <Vertex> 1 {{ 0.5 0 0 }}
      <Vertex> 2 {{ 0.5 0 {height_scale} }}
      <Vertex> 3 {{ 0 0 {height_scale} }}
      <Vertex> 4 {{ -0.5 0 0 }}
      <Vertex> 5 {{ -0.5 0 {height_scale} }}
      <Vertex> 6 {{ 0 0.2 {height_scale * 0.5} }}
      <Vertex> 7 {{ 0 -0.2 {height_scale * 0.5} }}
    }}
    
    <Polygon> {{
      <MRef> {{ base_material }}
      <VertexRef> {{ 0 1 2 3 <Ref> {{ body_vpool }} }}
    }}
    <Polygon> {{
      <MRef> {{ base_material }}
      <VertexRef> {{ 0 4 5 3 <Ref> {{ body_vpool }} }}
    }}
    <Polygon> {{
      <MRef> {{ base_material }}
      <VertexRef> {{ 1 6 7 2 <Ref> {{ body_vpool }} }}
    }}
  }}
  
  <Group> "head" {{
    <Transform> {{
      <Matrix4> {{
        1 0 0 0
        0 1 0 0
        0 0 1 {height_scale * 0.9}
        0 0 0 1
      }}
    }}
    
    <VertexPool> head_vpool {{
      <Vertex> 0 {{ -0.15 -0.15 0 }}
      <Vertex> 1 {{ 0.15 -0.15 0 }}
      <Vertex> 2 {{ 0.15 0.15 0 }}
      <Vertex> 3 {{ -0.15 0.15 0 }}
      <Vertex> 4 {{ -0.1 -0.1 0.3 }}
      <Vertex> 5 {{ 0.1 -0.1 0.3 }}
      <Vertex> 6 {{ 0.1 0.1 0.3 }}
      <Vertex> 7 {{ -0.1 0.1 0.3 }}
    }}
    
    <Polygon> {{
      <MRef> {{ base_material }}
      <VertexRef> {{ 0 1 2 3 <Ref> {{ head_vpool }} }}
    }}
    <Polygon> {{
      <MRef> {{ base_material }}
      <VertexRef> {{ 4 5 6 7 <Ref> {{ head_vpool }} }}
    }}
  }}
}}

<Group> "animations" {{
  // 动画占位符
  <Scalar> fps {{ 24 }}
  <Char*> animation_type {{ "character" }}
}}'''

        return egg_template
    
    def generate_character_variant(self, character_name: str, variant_name: str = "classic") -> bool:
        """
        生成指定角色的变体
        
        Args:
            character_name: 角色名称
            variant_name: 变体名称
            
        Returns:
            bool: 是否成功生成
        """
        if character_name not in self.character_profiles["characters"]:
            logger.error(f"Unknown character: {character_name}")
            return False
        
        char_config = self.character_profiles["characters"][character_name]
        
        if variant_name not in char_config["variants"]:
            logger.error(f"Unknown variant '{variant_name}' for character '{character_name}'")
            return False
        
        variant_config = char_config["variants"][variant_name]
        template_name = char_config["template"]
        template_config = self.character_profiles["base_templates"][template_name]
        
        # 创建角色目录
        char_dir = self.characters_path / character_name
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成主模型文件
        model_path = char_dir / f"{character_name}.egg"
        success = self._generate_character_model(
            template_config, variant_config, str(model_path)
        )
        
        if not success:
            logger.error(f"Failed to generate model for {character_name}")
            return False
        
        # 生成动画文件
        animations_dir = char_dir / "animations"
        animations_dir.mkdir(exist_ok=True)
        
        for anim_name in template_config["animations"]:
            anim_path = animations_dir / f"{anim_name}.egg"
            self._generate_animation_file(str(model_path), str(anim_path), anim_name)
        
        logger.info(f"Generated character variant: {character_name}/{variant_name}")
        return True
    
    def _generate_character_model(self, template_config: Dict, variant_config: Dict, output_path: str) -> bool:
        """生成角色模型文件"""
        try:
            # 获取基础模板
            template_path = self.templates_path / template_config["base_model"].split('/')[-1]
            
            if not template_path.exists():
                logger.warning(f"Template not found: {template_path}, creating from scratch")
                # 从头创建模板
                template_content = self._generate_base_egg_template("male" if "male" in template_config["base_model"] else "female")
            else:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            
            # 应用变体修改
            modified_content = self._apply_variant_modifications(template_content, variant_config)
            
            # 写入输出文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            logger.debug(f"Character model generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating character model: {e}")
            return False
    
    def _apply_variant_modifications(self, template_content: str, variant_config: Dict) -> str:
        """应用变体修改到模板内容"""
        modified_content = template_content
        
        # 应用颜色修改
        primary_color = variant_config.get("primary_color", [0.8, 0.8, 0.8])
        secondary_color = variant_config.get("secondary_color", [0.2, 0.2, 0.2])
        
        # 创建自定义材质 - 修正.egg格式语法
        material_section = f'''
<Material> primary_material {{
  <Scalar> ambient {{ {primary_color[0] * 0.3:.3f} {primary_color[1] * 0.3:.3f} {primary_color[2] * 0.3:.3f} 1.0 }}
  <Scalar> diffuse {{ {primary_color[0]:.3f} {primary_color[1]:.3f} {primary_color[2]:.3f} 1.0 }}
  <Scalar> specular {{ 0.2 0.2 0.2 1.0 }}
  <Scalar> shininess {{ 64 }}
}}

<Material> secondary_material {{
  <Scalar> ambient {{ {secondary_color[0] * 0.3:.3f} {secondary_color[1] * 0.3:.3f} {secondary_color[2] * 0.3:.3f} 1.0 }}
  <Scalar> diffuse {{ {secondary_color[0]:.3f} {secondary_color[1]:.3f} {secondary_color[2]:.3f} 1.0 }}
  <Scalar> specular {{ 0.1 0.1 0.1 1.0 }}
  <Scalar> shininess {{ 32 }}
}}'''
        
        # 在坐标系统后插入材质定义
        if '<CoordinateSystem>' in modified_content:
            insert_pos = modified_content.find('<CoordinateSystem>')
            end_pos = modified_content.find('\n', insert_pos) + 1
            modified_content = modified_content[:end_pos] + material_section + '\n' + modified_content[end_pos:]
        
        # 替换材质引用
        modified_content = modified_content.replace('<MRef> { base_material }', '<MRef> { primary_material }')
        
        # 添加特殊效果注释
        special_effects = variant_config.get("special_effects", [])
        if special_effects:
            effects_comment = f'\n// Special effects: {", ".join(special_effects)}\n'
            modified_content = effects_comment + modified_content
        
        return modified_content
    
    def _generate_animation_file(self, base_model_path: str, anim_path: str, anim_name: str) -> bool:
        """生成动画文件"""
        try:
            # 读取基础模型
            with open(base_model_path, 'r', encoding='utf-8') as f:
                base_content = f.read()
            
            # 生成简单的动画内容
            anim_content = self._create_simple_animation(base_content, anim_name)
            
            with open(anim_path, 'w', encoding='utf-8') as f:
                f.write(anim_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating animation file {anim_path}: {e}")
            return False
    
    def _create_simple_animation(self, base_content: str, anim_name: str) -> str:
        """创建简单的动画内容"""
        # 定义不同动画的基本参数
        anim_params = {
            "idle": {"duration": 2.0, "loop": True, "keyframes": 2},
            "walk": {"duration": 1.0, "loop": True, "keyframes": 4},
            "punch": {"duration": 0.5, "loop": False, "keyframes": 3},
            "kick": {"duration": 0.6, "loop": False, "keyframes": 3},
            "block": {"duration": 1.0, "loop": True, "keyframes": 1},
            "hurt": {"duration": 0.3, "loop": False, "keyframes": 2},
            "victory": {"duration": 2.0, "loop": False, "keyframes": 3},
            "defeat": {"duration": 1.5, "loop": False, "keyframes": 2}
        }
        
        params = anim_params.get(anim_name, {"duration": 1.0, "loop": True, "keyframes": 2})
        
        # 创建动画表格
        animation_table = f'''
<Table> "{anim_name}_anim" {{
  <Bundle> "bundle" {{
    <Table> "<skeleton>" {{
      <Table> "character_root" {{
        <Scalar> fps {{ 24 }}
        <Char*> order {{ "xyzrhpijs" }}
        <V> contents {{
          <S$> xfm {{'''
        
        # 添加关键帧
        for i in range(params["keyframes"]):
            time = (params["duration"] / max(1, params["keyframes"] - 1)) * i
            # 根据动画类型生成不同的变换
            transform = self._get_animation_transform(anim_name, i, params["keyframes"])
            animation_table += f'\n            <Scalar> {time:.2f} {{ {transform} }}'
        
        animation_table += '''
          }}
        }}
      }}
    }}
  }}
}}'''
        
        # 将动画表格插入到基础内容中
        if '<Group> "animations"' in base_content:
            # 替换动画占位符
            start_pos = base_content.find('<Group> "animations"')
            end_pos = base_content.find('}', start_pos) + 1
            return base_content[:start_pos] + animation_table + base_content[end_pos:]
        else:
            # 在文件末尾添加动画
            return base_content + '\n' + animation_table
    
    def _get_animation_transform(self, anim_name: str, keyframe: int, total_keyframes: int) -> str:
        """获取指定动画和关键帧的变换参数"""
        # 基础变换: x y z rx ry rz sx sy sz
        base_transform = "0 0 0 0 0 0 1 1 1"
        
        if anim_name == "idle":
            # 轻微的上下浮动
            y_offset = 0.05 * (1 if keyframe % 2 == 0 else -1)
            return f"0 {y_offset} 0 0 0 0 1 1 1"
        
        elif anim_name == "walk":
            # 行走动画 - 简单的左右移动
            x_offset = 0.1 * ((keyframe % 4) - 1.5) 
            return f"{x_offset} 0 0 0 0 0 1 1 1"
        
        elif anim_name == "punch":
            # 出拳动画 - 前后移动
            if keyframe == 1:  # 出拳
                return "0 0.3 0 0 0 0 1 1 1"
            else:  # 回收
                return base_transform
        
        elif anim_name == "kick":
            # 踢腿动画 - 旋转和前移
            if keyframe == 1:  # 踢出
                return "0 0.2 0 0 0 15 1 1 1"
            else:
                return base_transform
        
        elif anim_name == "hurt":
            # 受伤动画 - 后退
            if keyframe == 1:
                return "0 -0.2 0 0 0 -10 1 1 1"
            else:
                return base_transform
        
        elif anim_name == "victory":
            # 胜利动画 - 举手
            if keyframe == 1:
                return "0 0.1 0 0 0 0 1.1 1.1 1"
            else:
                return base_transform
        
        elif anim_name == "defeat":
            # 失败动画 - 倒下
            if keyframe == 1:
                return "0 -0.5 -0.3 -30 0 0 1 1 1"
            else:
                return base_transform
        
        return base_transform
    
    def generate_all_characters(self) -> Dict[str, bool]:
        """生成所有角色的默认变体"""
        results = {}
        
        logger.info("Starting generation of all characters...")
        
        # 首先创建基础模板
        if not self.create_base_templates():
            logger.error("Failed to create base templates")
            return results
        
        # 生成每个角色
        for char_name in self.character_profiles["characters"]:
            logger.info(f"Generating character: {char_name}")
            success = self.generate_character_variant(char_name, "classic")
            results[char_name] = success
            
            if not success:
                logger.error(f"Failed to generate character: {char_name}")
        
        # 显示统计
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Character generation completed: {successful}/{total} successful")
        
        return results
    
    def validate_generated_characters(self) -> Dict[str, bool]:
        """验证生成的角色文件"""
        results = {}
        
        for char_name in self.character_profiles["characters"]:
            char_dir = self.characters_path / char_name
            model_file = char_dir / f"{char_name}.egg"
            animations_dir = char_dir / "animations"
            
            # 检查主模型文件
            model_valid = model_file.exists() and model_file.stat().st_size > 500  # 至少500字节
            
            # 检查动画文件
            expected_animations = self.character_profiles["base_templates"][
                self.character_profiles["characters"][char_name]["template"]
            ]["animations"]
            
            animations_valid = True
            for anim_name in expected_animations:
                anim_file = animations_dir / f"{anim_name}.egg"
                if not anim_file.exists() or anim_file.stat().st_size < 200:
                    animations_valid = False
                    break
            
            results[char_name] = model_valid and animations_valid
            
            if results[char_name]:
                logger.debug(f"Character validation passed: {char_name}")
            else:
                logger.warning(f"Character validation failed: {char_name}")
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='程序化角色生成器')
    parser.add_argument('--generate-all', action='store_true', help='生成所有角色')
    parser.add_argument('--character', help='指定角色名称')
    parser.add_argument('--variant', default='classic', help='角色变体名称')
    parser.add_argument('--validate', action='store_true', help='验证生成的角色')
    parser.add_argument('--assets-path', default='assets', help='资源目录路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    generator = CharacterGenerator(args.assets_path)
    
    if args.generate_all:
        results = generator.generate_all_characters()
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"Generated {successful}/{total} characters successfully")
        
        if args.validate:
            print("\nValidating generated characters...")
            validation_results = generator.validate_generated_characters()
            valid_count = sum(1 for valid in validation_results.values() if valid)
            print(f"Validation: {valid_count}/{total} characters are valid")
    
    elif args.character:
        success = generator.generate_character_variant(args.character, args.variant)
        if success:
            print(f"Successfully generated {args.character}/{args.variant}")
        else:
            print(f"Failed to generate {args.character}/{args.variant}")
            return 1
    
    elif args.validate:
        results = generator.validate_generated_characters()
        valid_count = sum(1 for valid in results.values() if valid)
        total = len(results)
        print(f"Validation: {valid_count}/{total} characters are valid")
        
        for char_name, valid in results.items():
            status = "✓" if valid else "✗" 
            print(f"  {status} {char_name}")
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())