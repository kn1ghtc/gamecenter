#!/usr/bin/env python3
"""
路径兼容性工具 - 解决Windows/Unix路径格式兼容性问题
"""

import os
from pathlib import Path
import platform


def normalize_path(path):
    """
    标准化路径格式，确保跨平台兼容性
    
    Args:
        path: 原始路径字符串或Path对象
        
    Returns:
        标准化后的路径字符串
    """
    if isinstance(path, str):
        # 处理Windows路径格式
        if path.startswith('D:/'):
            # 转换为Unix格式
            path = path.replace('D:/', '/d/')
        elif ':' in path and path[1] == ':':
            # Windows绝对路径转换为Unix格式
            drive_letter = path[0].lower()
            path = path[2:].replace('\\', '/')
            path = f'/{drive_letter}{path}'
    
    # 转换为Path对象并返回字符串
    return str(Path(path))


def get_asset_path(relative_path):
    """
    获取资源文件的跨平台路径
    
    Args:
        relative_path: 相对于assets目录的相对路径
        
    Returns:
        完整的跨平台路径
    """
    base_dir = Path(__file__).parent.parent / "assets"
    full_path = base_dir / relative_path
    return normalize_path(full_path)


def ensure_unix_path(path):
    """
    确保路径使用Unix格式（Panda3D期望的格式）
    
    Args:
        path: 原始路径
        
    Returns:
        Unix格式的路径
    """
    path_str = str(path)
    
    # 如果是Windows绝对路径，转换为Unix格式
    if ':' in path_str and path_str[1] == ':':
        drive_letter = path_str[0].lower()
        path_str = path_str[2:].replace('\\', '/')
        path_str = f'/{drive_letter}{path_str}'
    
    return path_str.replace('\\', '/')


def is_windows():
    """检查当前是否为Windows系统"""
    return platform.system().lower() == 'windows'


def is_unix():
    """检查当前是否为Unix系统"""
    return platform.system().lower() in ['linux', 'darwin']


def get_compatible_path(path):
    """
    获取与当前系统兼容的路径
    
    Args:
        path: 原始路径
        
    Returns:
        与当前系统兼容的路径
    """
    if is_windows():
        # Windows系统：确保使用正斜杠
        return str(path).replace('\\', '/')
    else:
        # Unix系统：确保使用Unix格式
        return ensure_unix_path(path)