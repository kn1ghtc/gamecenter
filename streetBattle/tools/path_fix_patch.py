#!/usr/bin/env python3
"""
Path Compatibility Fix Patch
路径兼容性修复补丁
"""

import os
from pathlib import Path

def fix_panda3d_paths():
    """修复Panda3D路径兼容性问题"""
    
    def normalize_path_for_panda3d(path_str):
        """将路径标准化为Panda3D兼容格式"""
        if not path_str:
            return path_str
        
        # 转换为Path对象
        path_obj = Path(path_str)
        
        # 转换为POSIX风格路径（Unix风格，使用/）
        posix_path = path_obj.as_posix()
        
        # 如果是绝对路径，确保格式正确
        if path_obj.is_absolute():
            # Windows绝对路径转换
            if os.name == 'nt' and ':' in posix_path:
                # C:/path/to/file 格式
                posix_path = posix_path.replace('\\', '/')
        
        print(f"🛤️ 路径转换: {path_str} -> {posix_path}")
        return posix_path
    
    def patch_loader_methods():
        """修补加载器方法以使用正确的路径格式"""
        
        def enhanced_load_model(self, path, *args, **kwargs):
            """增强的模型加载方法"""
            normalized_path = normalize_path_for_panda3d(str(path))
            print(f"🎮 加载模型: {normalized_path}")
            
            try:
                return self._original_load_model(normalized_path, *args, **kwargs)
            except Exception as e:
                print(f"❌ 模型加载失败: {e}")
                # 尝试备用路径
                backup_path = normalized_path.replace('.bam', '.egg')
                if os.path.exists(backup_path):
                    print(f"🔄 尝试备用路径: {backup_path}")
                    return self._original_load_model(backup_path, *args, **kwargs)
                raise
        
        def enhanced_load_texture(self, path, *args, **kwargs):
            """增强的纹理加载方法"""
            normalized_path = normalize_path_for_panda3d(str(path))
            print(f"🎨 加载纹理: {normalized_path}")
            
            try:
                return self._original_load_texture(normalized_path, *args, **kwargs)
            except Exception as e:
                print(f"❌ 纹理加载失败: {e}")
                raise
        
        # 应用补丁
        try:
            from direct.showbase.ShowBase import ShowBase
            from direct.showbase.Loader import Loader
            
            # 保存原始方法
            if not hasattr(Loader, '_original_load_model'):
                Loader._original_load_model = Loader.loadModel
                Loader.loadModel = enhanced_load_model
                print("✅ 模型加载器已补丁")
            
            if not hasattr(Loader, '_original_load_texture'):
                Loader._original_load_texture = Loader.loadTexture  
                Loader.loadTexture = enhanced_load_texture
                print("✅ 纹理加载器已补丁")
                
        except ImportError as e:
            print(f"⚠️ 无法导入Panda3D模块: {e}")
    
    return {
        'normalize_path': normalize_path_for_panda3d,
        'patch_loaders': patch_loader_methods
    }

if __name__ == "__main__":
    path_fixes = fix_panda3d_paths()
    path_fixes['patch_loaders']()
    print("路径兼容性补丁已准备就绪")
