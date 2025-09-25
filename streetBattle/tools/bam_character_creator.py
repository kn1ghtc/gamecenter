#!/usr/bin/env python3
"""
BAM文件复制器 - 为每个角色创建独立的.bam文件副本
使用已知有效的npc_1.bam作为基础，创建20个不同的角色模型文件
"""

import os
import shutil
from pathlib import Path
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BAMCharacterCreator:
    """BAM文件角色创建器"""
    
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = Path(assets_path)
        self.characters_path = self.assets_path / "characters"
        self.models_path = self.assets_path / "models"
        
        # 源模型文件
        self.source_model = self.models_path / "npc_1.bam"
        self.source_animations = [
            self.models_path / "npc_1_ArmatureAction.bam",
            self.models_path / "npc_1_death.bam",
            self.models_path / "npc_1_head.bam"
        ]
        
        # KOF97角色列表
        self.characters = [
            "kyo_kusanagi", "iori_yagami", "mai_shiranui", "terry_bogard",
            "andy_bogard", "joe_higashi", "ryo_sakazaki", "robert_garcia", 
            "athena_asamiya", "sie_kensou", "chin_gentsai", "leona_heidern",
            "ralf_jones", "clark_still", "yuri_sakazaki", "king",
            "blue_mary", "geese_howard", "chizuru_kagura", "orochi"
        ]
    
    def create_character_models(self) -> Dict[str, bool]:
        """为所有角色创建独立的模型文件"""
        results = {}
        
        if not self.source_model.exists():
            logger.error(f"Source model not found: {self.source_model}")
            return results
        
        logger.info(f"Creating character models from source: {self.source_model}")
        
        for char_name in self.characters:
            logger.info(f"Creating character: {char_name}")
            success = self.create_single_character(char_name)
            results[char_name] = success
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Character creation completed: {successful}/{total} successful")
        
        return results
    
    def create_single_character(self, character_name: str) -> bool:
        """创建单个角色的模型文件"""
        try:
            # 创建角色目录
            char_dir = self.characters_path / character_name
            char_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制主模型文件
            dest_model = char_dir / f"{character_name}.bam"
            shutil.copy2(self.source_model, dest_model)
            logger.debug(f"Copied model: {dest_model}")
            
            # 创建动画目录
            animations_dir = char_dir / "animations"
            animations_dir.mkdir(exist_ok=True)
            
            # 定义动画映射
            animation_mapping = {
                "idle": "npc_1_ArmatureAction.bam",
                "walk": "npc_1_ArmatureAction.bam", 
                "punch": "npc_1_ArmatureAction.bam",
                "kick": "npc_1_ArmatureAction.bam",
                "block": "npc_1_ArmatureAction.bam",
                "hurt": "npc_1_ArmatureAction.bam",
                "victory": "npc_1_ArmatureAction.bam",
                "defeat": "npc_1_death.bam"
            }
            
            # 复制动画文件
            for anim_name, source_file in animation_mapping.items():
                source_path = self.models_path / source_file
                if source_path.exists():
                    dest_anim = animations_dir / f"{anim_name}.bam"
                    shutil.copy2(source_path, dest_anim)
                else:
                    # 如果源动画文件不存在，使用主模型文件
                    dest_anim = animations_dir / f"{anim_name}.bam"
                    shutil.copy2(self.source_model, dest_anim)
            
            logger.info(f"Character created: {character_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating character {character_name}: {e}")
            return False
    
    def validate_characters(self) -> Dict[str, bool]:
        """验证创建的角色文件"""
        results = {}
        
        for char_name in self.characters:
            char_dir = self.characters_path / char_name
            model_file = char_dir / f"{char_name}.bam"
            animations_dir = char_dir / "animations"
            
            # 检查主模型
            model_valid = model_file.exists() and model_file.stat().st_size > 1000
            
            # 检查动画文件
            expected_anims = ["idle", "walk", "punch", "kick", "block", "hurt", "victory", "defeat"]
            animations_valid = True
            
            for anim_name in expected_anims:
                anim_file = animations_dir / f"{anim_name}.bam"
                if not anim_file.exists() or anim_file.stat().st_size < 1000:
                    animations_valid = False
                    break
            
            results[char_name] = model_valid and animations_valid
            
            if results[char_name]:
                logger.debug(f"Character validation passed: {char_name}")
            else:
                logger.warning(f"Character validation failed: {char_name}")
        
        return results
    
    def cleanup_egg_files(self):
        """清理无效的.egg文件"""
        for char_name in self.characters:
            char_dir = self.characters_path / char_name
            if char_dir.exists():
                # 删除.egg文件
                for egg_file in char_dir.rglob("*.egg"):
                    try:
                        egg_file.unlink()
                        logger.debug(f"Removed invalid egg file: {egg_file}")
                    except Exception as e:
                        logger.warning(f"Could not remove {egg_file}: {e}")


def main():
    import argparse
    from typing import Dict
    
    parser = argparse.ArgumentParser(description='BAM Character Creator')
    parser.add_argument('--create-all', action='store_true', help='Create all character models')
    parser.add_argument('--validate', action='store_true', help='Validate created characters')
    parser.add_argument('--cleanup-egg', action='store_true', help='Remove invalid .egg files')
    parser.add_argument('--assets-path', default='assets', help='Assets directory path')
    
    args = parser.parse_args()
    
    creator = BAMCharacterCreator(args.assets_path)
    
    if args.cleanup_egg:
        logger.info("Cleaning up invalid .egg files...")
        creator.cleanup_egg_files()
        print("Cleaned up invalid .egg files")
    
    if args.create_all:
        results = creator.create_character_models()
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"Created {successful}/{total} character models successfully")
        
        if args.validate:
            print("\nValidating created characters...")
            validation_results = creator.validate_characters()
            valid_count = sum(1 for valid in validation_results.values() if valid)
            print(f"Validation: {valid_count}/{total} characters are valid")
            
            for char_name, valid in validation_results.items():
                status = "✓" if valid else "✗"
                print(f"  {status} {char_name}")
    
    elif args.validate:
        results = creator.validate_characters()
        valid_count = sum(1 for valid in results.values() if valid)
        total = len(results)
        print(f"Validation: {valid_count}/{total} characters are valid")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()