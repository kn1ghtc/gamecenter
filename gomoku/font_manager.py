"""跨平台中文字体管理器
Cross-platform Chinese font manager for Gomoku.

自动检测并加载系统中文字体，提供字体缓存机制。
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Dict, Optional, Tuple

import pygame


class FontManager:
    """跨平台中文字体管理器
    
    自动探测并加载最佳中文字体，支持字体缓存。
    """
    
    # 各平台的中文字体优先级列表
    FONT_PRIORITIES = {
        'Darwin': [  # macOS
            'PingFang SC',
            'Hiragino Sans GB',
            'STHeiti',
            'Songti SC',
        ],
        'Windows': [  # Windows
            'Microsoft YaHei',
            'SimHei',
            'SimSun',
            'KaiTi',
        ],
        'Linux': [  # Linux
            'Noto Sans CJK SC',
            'WenQuanYi Zen Hei',
            'WenQuanYi Micro Hei',
            'Droid Sans Fallback',
        ],
    }
    
    def __init__(self):
        """初始化字体管理器"""
        if not pygame.font.get_init():
            pygame.font.init()
        
        self.system = platform.system()
        self.font_cache: Dict[Tuple[int, bool], pygame.font.Font] = {}
        self.font_name = self._detect_best_font()
        self.debug_mode = False
    
    def _detect_best_font(self) -> str:
        """检测系统最佳中文字体
        
        Returns:
            字体名称（pygame格式）
        """
        priorities = self.FONT_PRIORITIES.get(self.system, [])
        available_fonts = pygame.font.get_fonts()
        
        # 尝试优先级列表中的字体
        for font_name in priorities:
            # 转换为pygame格式（小写，无空格）
            pygame_name = font_name.lower().replace(' ', '')
            if pygame_name in available_fonts:
                return pygame_name
        
        # 回退：查找包含'cjk'或'chinese'的字体
        for font in available_fonts:
            if 'cjk' in font or 'chinese' in font or 'han' in font:
                return font
        
        # 最后回退到默认字体
        return pygame.font.get_default_font()
    
    def get_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        """获取指定大小和样式的字体
        
        Args:
            size: 字体大小
            bold: 是否加粗
        
        Returns:
            pygame字体对象
        """
        key = (size, bold)
        
        if key in self.font_cache:
            return self.font_cache[key]
        
        # 创建新字体
        try:
            font = pygame.font.SysFont(self.font_name, size, bold=bold)
        except Exception:
            # 如果系统字体失败，使用默认字体
            font = pygame.font.Font(None, size)
        
        self.font_cache[key] = font
        return font
    
    def toggle_debug(self) -> None:
        """切换调试模式"""
        self.debug_mode = not self.debug_mode
    
    def get_debug_info(self) -> str:
        """获取调试信息
        
        Returns:
            调试信息字符串
        """
        return (f"System: {self.system}\n"
                f"Font: {self.font_name}\n"
                f"Cached: {len(self.font_cache)} sizes")
    
    def clear_cache(self) -> None:
        """清空字体缓存"""
        self.font_cache.clear()
    
    def render_text(self, text: str, size: int, color: Tuple[int, int, int],
                   bold: bool = False, antialias: bool = True) -> pygame.Surface:
        """渲染文本
        
        Args:
            text: 文本内容
            size: 字体大小
            color: 颜色RGB元组
            bold: 是否加粗
            antialias: 是否抗锯齿
        
        Returns:
            渲染后的Surface
        """
        font = self.get_font(size, bold)
        return font.render(text, antialias, color)
    
    def get_text_size(self, text: str, size: int, bold: bool = False) -> Tuple[int, int]:
        """获取文本渲染后的大小
        
        Args:
            text: 文本内容
            size: 字体大小
            bold: 是否加粗
        
        Returns:
            (宽度, 高度)
        """
        font = self.get_font(size, bold)
        return font.size(text)


# 全局字体管理器实例（单例模式）
_font_manager: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """获取全局字体管理器实例
    
    Returns:
        FontManager实例
    """
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def render_text(text: str, size: int, color: Tuple[int, int, int],
               bold: bool = False) -> pygame.Surface:
    """便捷函数：渲染文本
    
    Args:
        text: 文本内容
        size: 字体大小
        color: 颜色RGB元组
        bold: 是否加粗
    
    Returns:
        渲染后的Surface
    """
    return get_font_manager().render_text(text, size, color, bold)


def get_text_size(text: str, size: int, bold: bool = False) -> Tuple[int, int]:
    """便捷函数：获取文本大小
    
    Args:
        text: 文本内容
        size: 字体大小
        bold: 是否加粗
    
    Returns:
        (宽度, 高度)
    """
    return get_font_manager().get_text_size(text, size, bold)
