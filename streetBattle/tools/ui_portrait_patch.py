#!/usr/bin/env python3
"""
Character Selection UI Portrait Loading Patch
角色选择界面头像加载修复补丁
"""

import os
from pathlib import Path

def patch_character_selector_portrait_loading():
    """修复角色选择器的头像加载方法"""
    
    def enhanced_get_portrait_texture(self, character_name):
        """增强的头像纹理获取方法"""
        key = self._canonical_key(character_name)
        if key in self.portrait_cache:
            return self.portrait_cache[key]
        
        # 尝试多种头像文件格式
        portraits_dir = Path(self.assets_root) / 'images' / 'portraits'
        
        # 优先级顺序的头像文件路径
        portrait_candidates = [
            portraits_dir / f'{key}_official.png',
            portraits_dir / f'{key}.png', 
            portraits_dir / f'{key}_portrait.png',
            portraits_dir / f'{key}_thumb.png'
        ]
        
        texture = None
        for portrait_path in portrait_candidates:
            if portrait_path.exists():
                try:
                    texture = self.base_app.loader.loadTexture(str(portrait_path))
                    if texture:
                        print(f"🎨 加载头像成功: {character_name} -> {portrait_path.name}")
                        break
                except Exception as e:
                    print(f"头像加载失败 {portrait_path}: {e}")
                    continue
        
        # 如果没有找到头像文件，使用原始回退逻辑
        if not texture:
            profile = self._get_profile(character_name).copy() if character_name else {}
            char_record = self.char_manager.get_character_by_name(character_name) if character_name else None
            if char_record and 'id' not in profile:
                profile['id'] = char_record.get('id')

            if not character_name:
                texture = self._generate_portrait_texture(profile)
            else:
                texture = self.portrait_manager.get_texture(
                    key,
                    profile,
                    fallback_factory=lambda: self._generate_portrait_texture(profile)
                )
        
        self.portrait_cache[key] = texture
        return texture
    
    # 应用补丁
    try:
        from character_selector import CharacterSelector
        CharacterSelector._get_portrait_texture = enhanced_get_portrait_texture
        print("✓ 角色选择器头像加载补丁已应用")
        return True
    except ImportError as e:
        print(f"❌ 无法导入角色选择器: {e}")
        return False

if __name__ == "__main__":
    patch_character_selector_portrait_loading()
