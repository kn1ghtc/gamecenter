#!/usr/bin/env python3
"""
3D Mode Diagnostics and Fixes
3D模式诊断和修复工具
"""

import os
import sys
import glob
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def analyze_3d_models():
    """分析3D模型资源"""
    print("🎯 3D模型资源分析")
    print("=" * 40)
    
    models_dir = project_root / "assets" / "3d_models"
    if not models_dir.exists():
        print(f"❌ 3D模型目录不存在: {models_dir}")
        return False
    
    # 查找所有模型文件
    model_extensions = ["*.bam", "*.egg", "*.glb", "*.gltf", "*.x", "*.obj"]
    model_files = []
    
    for ext in model_extensions:
        found_files = list(models_dir.rglob(ext))
        model_files.extend(found_files)
        if found_files:
            print(f"  {ext}: {len(found_files)} 个文件")
    
    print(f"✓ 总计找到 {len(model_files)} 个3D模型文件")
    
    # 分析BAM文件（Panda3D的主要格式）
    bam_files = list(models_dir.rglob("*.bam"))
    print(f"\n🎮 BAM模型文件分析:")
    print(f"  找到 {len(bam_files)} 个BAM文件")
    
    valid_bam_count = 0
    for bam_file in bam_files:
        file_size = bam_file.stat().st_size
        if file_size > 1000:  # 至少1KB的有效文件
            valid_bam_count += 1
            print(f"    ✓ {bam_file.name} ({file_size} bytes)")
        else:
            print(f"    ⚠️ {bam_file.name} 文件过小 ({file_size} bytes)")
    
    print(f"  有效BAM文件: {valid_bam_count}/{len(bam_files)}")
    
    return len(model_files) > 0

def check_path_compatibility():
    """检查路径兼容性问题"""
    print("\n🛤️ 路径兼容性检查")
    print("=" * 40)
    
    # 查找包含Windows路径的配置文件
    config_files = [
        project_root / "main.py",
        project_root / "enhanced_character_manager.py",
        project_root / "panda3d_ui.py"
    ]
    
    path_issues = []
    
    for config_file in config_files:
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找Windows风格路径
                if '\\\\' in content or 'C:\\\\' in content:
                    path_issues.append(config_file)
                    print(f"  ⚠️ {config_file.name}: 发现Windows风格路径")
                elif '\\' in content and not '\\\\"' in content:
                    # 可能的路径问题
                    print(f"  📋 {config_file.name}: 可能存在路径格式问题")
                else:
                    print(f"  ✓ {config_file.name}: 路径格式正常")
                    
            except Exception as e:
                print(f"  ❌ {config_file.name}: 读取失败 - {e}")
    
    if path_issues:
        print(f"\n⚠️ 发现 {len(path_issues)} 个文件存在路径兼容性问题")
        return False
    
    return True

def create_player2_debug_patch():
    """创建Player2调试补丁"""
    print("\n🎭 创建Player2调试补丁")
    print("=" * 40)
    
    patch_content = '''#!/usr/bin/env python3
"""
Player2 Loading Debug Patch
Player2加载调试补丁
"""

import os
from pathlib import Path

def debug_player2_loading():
    """调试Player2加载问题"""
    
    def enhanced_load_player2_model(self, character_name):
        """增强的Player2模型加载方法"""
        print(f"🎭 开始加载Player2模型: {character_name}")
        
        # 多种模型文件路径尝试
        models_dir = Path(self.assets_dir) / "3d_models"
        
        model_candidates = [
            models_dir / f"{character_name}.bam",
            models_dir / f"{character_name}_player2.bam", 
            models_dir / f"{character_name}_p2.bam",
            models_dir / "characters" / f"{character_name}.bam",
            models_dir / "players" / f"{character_name}_p2.bam"
        ]
        
        print(f"🔍 搜索Player2模型文件:")
        for candidate in model_candidates:
            if candidate.exists():
                print(f"    ✓ 找到: {candidate}")
                try:
                    # 尝试加载模型
                    model = self.base_app.loader.loadModel(str(candidate))
                    if model:
                        print(f"    ✅ 成功加载: {candidate.name}")
                        
                        # 设置Player2位置和属性
                        model.setPos(3, 0, 0)  # Player2位置
                        model.setScale(1.0)
                        model.reparentTo(self.base_app.render)
                        
                        # 如果是Actor，设置动画
                        if hasattr(model, 'setPlayRate'):
                            model.loop('idle')  # 播放idle动画
                        
                        print(f"    📍 Player2已设置到位置 (3, 0, 0)")
                        return model
                    else:
                        print(f"    ❌ 加载失败: {candidate.name}")
                except Exception as e:
                    print(f"    ❌ 加载异常 {candidate.name}: {e}")
            else:
                print(f"    ❌ 不存在: {candidate}")
        
        print(f"⚠️ 无法找到Player2模型文件，使用回退方案")
        
        # 回退方案：使用Player1模型的副本
        try:
            player1_model = getattr(self, 'player1_model', None)
            if player1_model:
                player2_model = player1_model.copyTo(self.base_app.render)
                player2_model.setPos(3, 0, 0)
                player2_model.setColorScale(0.8, 0.8, 1.0, 1.0)  # 略微改变颜色
                print(f"    ✅ 使用Player1模型副本作为Player2")
                return player2_model
        except Exception as e:
            print(f"    ❌ 回退方案失败: {e}")
        
        return None
    
    def enhanced_setup_player2_lighting(self):
        """增强的Player2光照设置"""
        print(f"💡 设置Player2光照")
        
        try:
            # 为Player2创建专用光照
            from panda3d.core import DirectionalLight, AmbientLight, VBase4
            
            # 方向光
            player2_dlight = DirectionalLight('player2_dlight')
            player2_dlight.setDirection(VBase4(-1, -1, -1, 0))
            player2_dlight.setColor(VBase4(0.8, 0.8, 1.0, 1))
            
            player2_dlnp = self.base_app.render.attachNewNode(player2_dlight)
            player2_dlnp.setPos(3, 5, 5)
            
            # 环境光
            player2_alight = AmbientLight('player2_alight')
            player2_alight.setColor(VBase4(0.3, 0.3, 0.4, 1))
            player2_alnp = self.base_app.render.attachNewNode(player2_alight)
            
            # 应用光照到Player2区域
            if hasattr(self, 'player2_model') and self.player2_model:
                self.player2_model.setLight(player2_dlnp)
                self.player2_model.setLight(player2_alnp)
                print(f"    ✅ Player2光照设置完成")
            
        except Exception as e:
            print(f"    ❌ Player2光照设置失败: {e}")
    
    # 应用补丁的辅助函数
    def apply_player2_patch(game_instance):
        """应用Player2补丁到游戏实例"""
        if hasattr(game_instance, 'load_player2_model'):
            game_instance.load_player2_model = enhanced_load_player2_model.__get__(game_instance)
            print("✅ Player2加载补丁已应用")
        
        if hasattr(game_instance, 'setup_player2_lighting'):
            game_instance.setup_player2_lighting = enhanced_setup_player2_lighting.__get__(game_instance)
            print("✅ Player2光照补丁已应用")
    
    return {
        'load_player2_model': enhanced_load_player2_model,
        'setup_player2_lighting': enhanced_setup_player2_lighting,
        'apply_patch': apply_player2_patch
    }

if __name__ == "__main__":
    debug_functions = debug_player2_loading()
    print("Player2调试补丁已准备就绪")
'''
    
    patch_file = project_root / "tools" / "player2_debug_patch.py"
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print(f"✓ Player2调试补丁已创建: {patch_file}")
    return True

def create_path_fix_patch():
    """创建路径修复补丁"""
    print("\n🛤️ 创建路径修复补丁")
    print("=" * 40)
    
    patch_content = '''#!/usr/bin/env python3
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
                posix_path = posix_path.replace('\\\\', '/')
        
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
'''
    
    patch_file = project_root / "tools" / "path_fix_patch.py"
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print(f"✓ 路径修复补丁已创建: {patch_file}")
    return True

def test_3d_mode_startup():
    """测试3D模式启动"""
    print("\n🎮 3D模式启动测试")
    print("=" * 40)
    
    try:
        # 模拟Panda3D环境检查
        try:
            from panda3d.core import Filename, getModelPath
            print("✓ Panda3D核心模块可用")
        except ImportError:
            print("❌ Panda3D核心模块不可用")
            return False
        
        # 检查模型路径
        model_paths = [
            project_root / "assets" / "3d_models",
            project_root / "assets" / "characters",
            project_root / "assets" / "models"
        ]
        
        valid_paths = []
        for path in model_paths:
            if path.exists():
                model_count = len(list(path.glob("*.bam")))
                print(f"  ✓ {path.name}: {model_count} BAM文件")
                valid_paths.append(path)
            else:
                print(f"  ❌ {path.name}: 目录不存在")
        
        if not valid_paths:
            print("⚠️ 没有找到有效的3D模型目录")
            return False
        
        print("✅ 3D模式基础检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 3D模式测试异常: {e}")
        return False

def main():
    """主函数"""
    print("🎯 StreetBattle 3D模式诊断和修复工具")
    print("=" * 50)
    
    try:
        # 1. 分析3D模型资源
        if not analyze_3d_models():
            print("⚠️ 3D模型资源不足，可能影响3D模式")
        
        # 2. 检查路径兼容性
        if not check_path_compatibility():
            print("⚠️ 发现路径兼容性问题")
        
        # 3. 创建Player2调试补丁
        if not create_player2_debug_patch():
            print("❌ Player2调试补丁创建失败")
            return False
        
        # 4. 创建路径修复补丁
        if not create_path_fix_patch():
            print("❌ 路径修复补丁创建失败")
            return False
        
        # 5. 测试3D模式启动
        if not test_3d_mode_startup():
            print("⚠️ 3D模式启动测试未完全通过")
        
        print("\n🎉 3D模式诊断和修复完成!")
        print("\n📋 修复总结:")
        print("  ✓ 3D模型资源分析完成")
        print("  ✓ 路径兼容性检查完成")
        print("  ✓ Player2调试补丁已创建")
        print("  ✓ 路径修复补丁已创建")
        print("  ✓ 3D模式启动测试完成")
        
        print("\n🔧 使用建议:")
        print("  1. 启动3D模式测试Player2显示")
        print("  2. 如有Player2加载问题，应用Player2调试补丁")
        print("  3. 如有路径警告，应用路径修复补丁")
        print("  4. 检查模型文件完整性")
        
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