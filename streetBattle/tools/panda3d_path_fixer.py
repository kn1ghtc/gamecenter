#!/usr/bin/env python3
"""
Panda3D Path Format Fixer
Panda3D路径格式修复器
"""

import os
from pathlib import Path

def normalize_path_for_panda3d(path_str):
    """将路径标准化为Panda3D兼容格式（Unix风格）"""
    if not path_str:
        return path_str
    
    # 转换为Path对象
    path_obj = Path(path_str)
    
    # 转换为POSIX风格路径（Unix风格，使用/）
    posix_path = path_obj.as_posix()
    
    # 如果是绝对路径，确保格式正确
    if path_obj.is_absolute():
        # Windows绝对路径转换为Panda3D兼容格式
        if os.name == 'nt' and ':' in posix_path:
            # 将 C:/path 转换为 /c/path 格式
            drive, rest = posix_path.split(':', 1)
            posix_path = f"/{drive.lower()}{rest}"
    
    return posix_path

def safe_load_texture(loader, path_str):
    """安全加载纹理，自动处理路径格式"""
    if not path_str:
        return None
    
    # 标准化路径
    normalized_path = normalize_path_for_panda3d(str(path_str))
    
    try:
        return loader.loadTexture(normalized_path)
    except Exception as e:
        print(f"Failed to load texture with normalized path {normalized_path}: {e}")
        
        # 尝试原始路径
        try:
            return loader.loadTexture(str(path_str))
        except Exception as e2:
            print(f"Failed to load texture with original path {path_str}: {e2}")
            return None

def safe_load_model(loader, path_str):
    """安全加载模型，自动处理路径格式"""
    if not path_str:
        return None
    
    # 标准化路径
    normalized_path = normalize_path_for_panda3d(str(path_str))
    
    try:
        return loader.loadModel(normalized_path)
    except Exception as e:
        print(f"Failed to load model with normalized path {normalized_path}: {e}")
        
        # 尝试原始路径
        try:
            return loader.loadModel(str(path_str))
        except Exception as e2:
            print(f"Failed to load model with original path {path_str}: {e2}")
            return None

# 应用到全局loader
def patch_loader_methods():
    """为全局loader方法打补丁"""
    try:
        from direct.showbase import ShowBase
        from panda3d.core import Loader
        
        # 保存原始方法
        if not hasattr(Loader, '_original_loadTexture'):
            Loader._original_loadTexture = Loader.loadTexture
            
            def enhanced_loadTexture(self, path, *args, **kwargs):
                normalized_path = normalize_path_for_panda3d(str(path))
                return self._original_loadTexture(normalized_path, *args, **kwargs)
            
            Loader.loadTexture = enhanced_loadTexture
            print("✅ Loader.loadTexture已修补路径格式")
        
        if not hasattr(Loader, '_original_loadModel'):
            Loader._original_loadModel = Loader.loadModel
            
            def enhanced_loadModel(self, path, *args, **kwargs):
                normalized_path = normalize_path_for_panda3d(str(path))
                return self._original_loadModel(normalized_path, *args, **kwargs)
            
            Loader.loadModel = enhanced_loadModel
            print("✅ Loader.loadModel已修补路径格式")
            
    except ImportError as e:
        print(f"⚠️ 无法导入Panda3D模块: {e}")
    except Exception as e:
        print(f"❌ 路径修补失败: {e}")

if __name__ == "__main__":
    patch_loader_methods()
    print("Panda3D路径格式修复器已激活")
