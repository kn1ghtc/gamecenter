"""跨平台字体管理"""
import pygame
import sys
from pathlib import Path
from typing import Optional


class FontManager:
    """字体管理器 - 跨平台中文字体支持
    
    字体回退链:
    1. PingFang SC (macOS)
    2. Microsoft YaHei (Windows)
    3. Noto Sans CJK (Linux)
    4. System Default
    
    使用单例模式以避免重复初始化
    """
    
    _instance = None  # 单例实例
    _initialized = False  # 初始化标志
    
    FONT_FALLBACK_CHAIN = [
        "PingFang SC",      # macOS
        "Microsoft YaHei",  # Windows
        "微软雅黑",          # Windows (中文名)
        "Noto Sans CJK SC", # Linux
        "WenQuanYi Micro Hei",  # Linux
        "SimHei",           # Windows备选
        "Arial Unicode MS", # 通用Unicode
    ]
    
    def __new__(cls):
        """单例模式 - 确保只有一个FontManager实例"""
        if cls._instance is None:
            cls._instance = super(FontManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化字体管理器 - 只初始化一次"""
        # 避免重复初始化
        if FontManager._initialized:
            return
            
        self.fonts = {}
        self.default_font_name = None
        self._detect_system_fonts()
        
        # 标记已初始化
        FontManager._initialized = True
        
    def _detect_system_fonts(self):
        """检测系统可用字体"""
        print("[FontManager] 检测系统字体...")
        
        available_fonts = pygame.font.get_fonts()
        
        # 查找回退链中第一个可用字体
        for font_name in self.FONT_FALLBACK_CHAIN:
            # 规范化字体名(小写,去空格)
            normalized = font_name.lower().replace(' ', '')
            
            if normalized in available_fonts:
                self.default_font_name = font_name
                print(f"  [+] 使用字体: {font_name}")
                break
                
        if not self.default_font_name:
            print("  [!] 未找到中文字体,使用系统默认")
            self.default_font_name = None
            
    def get_font(self, size: int, bold: bool = False, italic: bool = False) -> pygame.font.Font:
        """获取字体对象
        
        Args:
            size: 字体大小
            bold: 是否粗体
            italic: 是否斜体
            
        Returns:
            pygame.font.Font对象
        """
        # 缓存键
        key = (size, bold, italic)
        
        if key in self.fonts:
            return self.fonts[key]
            
        # 创建字体
        try:
            if self.default_font_name:
                # 尝试使用系统字体
                font = pygame.font.SysFont(self.default_font_name, size, bold, italic)
            else:
                # 使用pygame默认字体
                font = pygame.font.Font(None, size)
                
            self.fonts[key] = font
            return font
            
        except Exception as e:
            print(f"[FontManager] 字体创建失败: {e}")
            # 回退到None(pygame默认)
            font = pygame.font.Font(None, size)
            self.fonts[key] = font
            return font
            
    def load_custom_font(self, name: str, filepath: Path, size: int) -> Optional[pygame.font.Font]:
        """加载自定义字体文件
        
        Args:
            name: 字体名称
            filepath: 字体文件路径
            size: 字体大小
            
        Returns:
            字体对象或None
        """
        try:
            if not filepath.exists():
                print(f"[FontManager] 字体文件不存在: {filepath}")
                return None
                
            font = pygame.font.Font(str(filepath), size)
            self.fonts[name] = font
            print(f"[FontManager] 加载自定义字体: {name}")
            return font
            
        except Exception as e:
            print(f"[FontManager] 加载字体失败 {filepath}: {e}")
            return None
            
    def render_text(self, text: str, size: int, color: tuple,
                   bold: bool = False, italic: bool = False) -> pygame.Surface:
        """渲染文本
        
        Args:
            text: 文本内容
            size: 字体大小
            color: 文本颜色 (R,G,B)
            bold: 是否粗体
            italic: 是否斜体
            
        Returns:
            渲染后的Surface
        """
        font = self.get_font(size, bold, italic)
        return font.render(text, True, color)
        
    def render_text_multiline(self, text: str, size: int, color: tuple,
                             max_width: int, line_spacing: int = 5) -> pygame.Surface:
        """渲染多行文本
        
        Args:
            text: 文本内容(可包含\\n)
            size: 字体大小
            color: 文本颜色
            max_width: 最大宽度
            line_spacing: 行间距
            
        Returns:
            渲染后的Surface
        """
        font = self.get_font(size)
        lines = []
        
        # 按换行符分割
        for line in text.split('\n'):
            # 按空格分割单词
            words = line.split(' ')
            current_line = ""
            
            for word in words:
                test_line = current_line + word + " "
                test_surf = font.render(test_line, True, color)
                
                if test_surf.get_width() > max_width:
                    if current_line:
                        lines.append(current_line)
                    current_line = word + " "
                else:
                    current_line = test_line
                    
            if current_line:
                lines.append(current_line)
                
        # 计算总高度
        line_height = font.get_height()
        total_height = len(lines) * (line_height + line_spacing)
        
        # 创建Surface
        surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # 透明背景
        
        # 渲染每一行
        y = 0
        for line in lines:
            line_surf = font.render(line, True, color)
            surface.blit(line_surf, (0, y))
            y += line_height + line_spacing
            
        return surface
        
    def get_text_size(self, text: str, size: int) -> tuple:
        """获取文本渲染尺寸
        
        Args:
            text: 文本内容
            size: 字体大小
            
        Returns:
            (width, height)
        """
        font = self.get_font(size)
        return font.size(text)
