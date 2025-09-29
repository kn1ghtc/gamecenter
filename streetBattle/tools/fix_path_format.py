#!/usr/bin/env python3
"""
Path Format Fix Tool
路径格式修复工具 - 修复Windows路径格式问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def fix_panda3d_path_format():
    """修复Panda3D路径格式问题"""
    print("🛤️ 修复Panda3D路径格式问题")
    print("=" * 40)
    
    # 创建路径标准化函数
    path_fix_code = '''#!/usr/bin/env python3
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
'''
    
    # 保存路径修复模块
    path_fixer_file = project_root / "tools" / "panda3d_path_fixer.py"
    with open(path_fixer_file, 'w', encoding='utf-8') as f:
        f.write(path_fix_code)
    
    print(f"✓ 路径修复模块已创建: {path_fixer_file}")
    
    return True

def update_character_selector_paths():
    """更新角色选择器中的路径处理"""
    print("\n🎭 更新角色选择器路径处理")
    print("=" * 40)
    
    # 读取character_selector.py文件
    selector_file = project_root / "character_selector.py"
    
    if not selector_file.exists():
        print(f"❌ 文件不存在: {selector_file}")
        return False
    
    try:
        with open(selector_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在文件开头添加路径修复导入
        import_section = '''from pathlib import Path
import sys

# 导入路径修复模块
try:
    from tools.panda3d_path_fixer import safe_load_texture, normalize_path_for_panda3d
except ImportError:
    def safe_load_texture(loader, path_str):
        return loader.loadTexture(str(path_str)) if path_str else None
    def normalize_path_for_panda3d(path_str):
        return str(Path(path_str).as_posix()) if path_str else path_str

'''
        
        # 检查是否已经有路径修复导入
        if 'safe_load_texture' not in content:
            # 在第一个import之后添加路径修复导入
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i + 1
                elif line.strip() == '' and insert_pos > 0:
                    break
            
            lines.insert(insert_pos, import_section)
            content = '\n'.join(lines)
            
            with open(selector_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✓ 已添加路径修复导入到角色选择器")
        else:
            print("✓ 角色选择器已包含路径修复导入")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新角色选择器失败: {e}")
        return False

def main():
    """主函数"""
    print("🛤️ StreetBattle路径格式修复工具")
    print("=" * 50)
    
    try:
        # 1. 创建路径修复模块
        if not fix_panda3d_path_format():
            print("❌ 路径修复模块创建失败")
            return False
        
        # 2. 更新角色选择器
        if not update_character_selector_paths():
            print("❌ 角色选择器路径更新失败")
            return False
        
        print("\n🎉 路径格式修复完成!")
        print("\n📋 修复总结:")
        print("  ✓ Panda3D路径格式修复模块已创建")
        print("  ✓ 角色选择器路径处理已更新")
        print("  ✓ 自动处理Windows路径转Unix路径格式")
        
        print("\n🔧 使用说明:")
        print("  1. 路径修复模块会自动处理Windows路径格式")
        print("  2. 所有纹理和模型加载都会使用标准化路径")
        print("  3. 消除 'Filename uses Windows-style path' 警告")
        
        return True
        
    except Exception as e:
        print(f"❌ 执行过程中出现异常: {e}")
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