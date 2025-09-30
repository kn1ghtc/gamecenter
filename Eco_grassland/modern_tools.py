#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化工具模块 - 统一的配置和资源管理
解决 pkg_resources 弃用警告，提供现代化的资源管理方案
"""

import sys
import os
from pathlib import Path
from typing import Union, Optional

# =============================================================================
# 游戏常量配置
# =============================================================================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
MAP_WIDTH = 2000
MAP_HEIGHT = 1500

# =============================================================================
# 现代化环境设置
# =============================================================================

def patch_pygame_pkgdata():
    """
    修补 pygame 的 pkgdata 模块，避免使用已弃用的 pkg_resources
    """
    class MockPkgResources:
        @staticmethod
        def resource_exists(package, resource):
            return False

        @staticmethod
        def resource_stream(package, resource):
            raise NotImplementedError("使用现代资源管理")

    # 在 pygame 导入前注入虚假的 pkg_resources 模块
    if 'pkg_resources' not in sys.modules:
        sys.modules['pkg_resources'] = MockPkgResources()

def setup_modern_environment():
    """
    设置现代化的 Python 环境配置
    """
    # 1. 禁用 pygame 的支持提示和警告
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

    # 2. 应用 pkg_resources 补丁
    patch_pygame_pkgdata()

    # 3. 设置现代包管理环境
    os.environ['SETUPTOOLS_USE_DISTUTILS'] = 'stdlib'

    # 4. 预加载现代资源管理模块
    try:
        if sys.version_info >= (3, 8):
            import importlib.metadata
            # 预加载避免后续 pkg_resources 调用
            try:
                _ = importlib.metadata.version('pygame')
            except Exception:
                pass
    except ImportError:
        pass

# =============================================================================
# 现代资源管理器
# =============================================================================

class ModernResourceManager:
    """
    现代资源管理器，使用 importlib.resources 替代已弃用的 pkg_resources
    """

    @staticmethod
    def get_resource_path(package: str, resource: str) -> Path:
        """
        获取资源文件路径

        Args:
            package: 包名
            resource: 资源名称

        Returns:
            Path: 资源文件路径
        """
        try:
            # Python 3.9+ 现代方式
            if sys.version_info >= (3, 9):
                from importlib.resources import files, as_file
                package_files = files(package)
                resource_file = package_files / resource

                if resource_file.is_file():
                    with as_file(resource_file) as resource_path:
                        return resource_path
                else:
                    raise FileNotFoundError(f"Resource {resource} not found in package {package}")
            else:
                # Python 3.7-3.8 兼容方式
                try:
                    import importlib_resources
                    with importlib_resources.path(package, resource) as resource_path:
                        return resource_path
                except ImportError:
                    # 回退到传统方式
                    import importlib
                    module = importlib.import_module(package)
                    package_path = Path(module.__file__).parent
                    resource_path = package_path / resource

                    if resource_path.exists():
                        return resource_path
                    else:
                        raise FileNotFoundError(f"Resource {resource} not found")

        except Exception as e:
            raise FileNotFoundError(f"无法找到资源 {resource} 在包 {package} 中: {e}")

    @staticmethod
    def resource_exists(package: str, resource: str) -> bool:
        """
        检查资源是否存在
        """
        try:
            ModernResourceManager.get_resource_path(package, resource)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def load_resource_bytes(package: str, resource: str) -> bytes:
        """
        加载资源文件为字节数据
        """
        resource_path = ModernResourceManager.get_resource_path(package, resource)
        return resource_path.read_bytes()

    @staticmethod
    def load_resource_text(package: str, resource: str, encoding: str = 'utf-8') -> str:
        """
        加载资源文件为文本数据
        """
        resource_path = ModernResourceManager.get_resource_path(package, resource)
        return resource_path.read_text(encoding=encoding)

    @staticmethod
    def get_package_version(package: str) -> str:
        """
        使用现代 API 获取包版本
        """
        try:
            if sys.version_info >= (3, 8):
                from importlib.metadata import version
                return version(package)
            else:
                try:
                    import importlib_metadata
                    return importlib_metadata.version(package)
                except ImportError:
                    import importlib
                    module = importlib.import_module(package)
                    return getattr(module, '__version__', 'unknown')
        except Exception:
            return 'unknown'

# =============================================================================
# 初始化函数
# =============================================================================

def initialize_modern_environment():
    """
    初始化现代化环境 - 在导入 pygame 之前调用
    """
    setup_modern_environment()
    print("🚀 现代化环境已初始化，pkg_resources 警告已消除")

# 全局资源管理器实例
resource_manager = ModernResourceManager()

# 自动初始化
initialize_modern_environment()
